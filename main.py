# main.py
import time
import cv2

from config import ZMQConfig, VideoConfig, ControlConfig, HandConfig
from comms.zmq_io import ZMQVideoSubscriber, ZMQControlPublisher
from comms.tts import AsyncTTS
from comms.sms import TwilioSMS
from vision.yolo_detectors import YOLODetector, pick_best_target, detect_hand_raise_in_roi
from control.follower import FollowerController

def main():
    zmq_cfg = ZMQConfig()
    vid_cfg = VideoConfig()
    ctrl_cfg = ControlConfig()
    hand_cfg = HandConfig()

    font = cv2.FONT_HERSHEY_SIMPLEX

    # ---- comms ----
    video_sub = ZMQVideoSubscriber(zmq_cfg.video_port, timeout_ms=zmq_cfg.rcv_timeout_ms)
    ctrl_pub  = ZMQControlPublisher(zmq_cfg.ctrl_port)

    # ---- speech + sms ----
    tts = AsyncTTS(rate=175)
    sms = TwilioSMS()

    tts.say("Follow robot targeting", cooldown_s=0.1)
    print("Windows bound, waiting for frames...")

    # ---- models ----
    detector = YOLODetector("yolov8n.pt")
    hand_detector = YOLODetector("best.pt")
    print("Hand model classes:", hand_detector.model.names)

    # ---- controller ----
    follower = FollowerController(vid_cfg.width, vid_cfg.height, ctrl_cfg)

    # ---- UI state ----
    target_class = None
    locked_target = None
    seen_classes = []
    selected_candidate = None
    selected_index = 0

    frame_i = 0
    emergency_until = 0.0
    fpsFilt = 0.0
    t_prev = time.time()

    print("Running... Press:")
    print("  c = cycle seen objects")
    print("  1..9 = select seen object by number")
    print("  l = lock selected as TARGET")
    print("  x = clear target (SEARCH)")
    print("  q = quit")

    try:
        while True:
            img = video_sub.recv_frame_bgr()
            if img is None:
                print("No frames received (timeout). Check publisher / Windows firewall / IP.")
                continue

            frame = cv2.resize(img, (vid_cfg.width, vid_cfg.height))

            # detect
            r = detector.infer(frame, conf=vid_cfg.conf_detect_th, verbose=False)

            # seen classes
            seen_set = set()
            for b in r.boxes:
                conf = float(b.conf.item())
                if conf < vid_cfg.conf_draw_th:
                    continue
                cls_id = int(b.cls.item())
                seen_set.add(r.names[cls_id])
            seen_classes = sorted(list(seen_set))

            # draw detections
            for b in r.boxes:
                conf = float(b.conf.item())
                if conf < vid_cfg.conf_draw_th:
                    continue
                cls_id = int(b.cls.item())
                name = r.names[cls_id]
                x1, y1, x2, y2 = map(float, b.xyxy[0].tolist())
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.putText(frame, f"{name} {conf:.2f}", (int(x1), max(20, int(y1) - 6)),
                            font, 0.6, (0, 255, 0), 2)

            # keys
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

            if key == ord('c'):
                if len(seen_classes) > 0:
                    selected_index = (selected_index + 1) % len(seen_classes)
                    selected_candidate = seen_classes[selected_index]
                else:
                    selected_candidate = None

            if ord('1') <= key <= ord('9'):
                idx = key - ord('1')
                if idx < len(seen_classes):
                    selected_index = idx
                    selected_candidate = seen_classes[selected_index]
                    print("Selected candidate:", selected_candidate)

            if key == ord('l'):
                if selected_candidate is not None:
                    target_class = selected_candidate
                    if target_class != locked_target:
                        locked_target = target_class
                        phrase = f"Target locked is {target_class}"
                        print("SPEAK:", phrase)
                        tts.say(phrase, cooldown_s=0.1)

            if key == ord('x'):
                target_class = None
                locked_target = None
                tts.say("Target cleared", cooldown_s=0.5)

            # pick target
            target = pick_best_target(r.boxes, target_class, r.names)

            now = time.time()

            # compute motion (base)
            linear, angular, status, extra = follower.compute(target, target_class, now)

            # emergency pipeline (only when following person)
            hand_hits = []
            if target is not None and hand_cfg.enabled and target_class == hand_cfg.person_class_name:
                frame_i += 1
                if frame_i % hand_cfg.hand_every_n == 0:
                    x1, y1, x2, y2, conf, _ = target
                    hand_emergency, hand_hits = detect_hand_raise_in_roi(
                        frame, (x1, y1, x2, y2),
                        hand_detector=hand_detector,
                        width=vid_cfg.width, height=vid_cfg.height,
                        hand_class_name=hand_cfg.hand_class_name,
                        conf_th=hand_cfg.hand_conf_th
                    )
                    if hand_emergency:
                        emergency_until = max(emergency_until, now + hand_cfg.emergency_hold_s)

            if now < emergency_until:
                linear = 0.0
                angular = 0.0
                status = "EMERGENCY: HAND RAISE"
                tts.say("Emergency signal detected", cooldown_s=3.0)
                sms.send("Emergency: Hand raise detected from followed person.", cooldown_s=30.0)

                for hx1, hy1, hx2, hy2, hconf in hand_hits:
                    cv2.rectangle(frame, (int(hx1), int(hy1)), (int(hx2), int(hy2)), (0, 0, 255), 2)
                    cv2.putText(frame, f"Hand raise {hconf:.2f}", (int(hx1), max(20, int(hy1) - 6)),
                                font, 0.6, (0, 0, 255), 2)

            # smoothing + send
            linear_s, angular_s = follower.smooth(linear, angular)
            ctrl_pub.send_cmd(linear_s, angular_s, status)

            # fps
            dt = time.time() - t_prev
            t_prev = time.time()
            fps = 1.0 / dt if dt > 0 else 0.0
            fpsFilt = 0.9 * fpsFilt + 0.1 * fps

            # HUD
            center_x = vid_cfg.width // 2
            cv2.line(frame, (center_x, 0), (center_x, vid_cfg.height), (255, 0, 0), 2)
            cv2.putText(frame, status, (10, 25), font, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, f"linear={linear_s:.2f} angular={angular_s:.2f}", (10, vid_cfg.height - 15),
                        font, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, f"{fpsFilt:.1f} fps", (vid_cfg.width - 140, 30),
                        font, 0.8, (0, 0, 255), 2)

            hud_seen = "Seen: " + (", ".join([f"{i+1}:{n}" for i, n in enumerate(seen_classes[:9])]) if seen_classes else "(none)")
            cv2.putText(frame, hud_seen, (10, vid_cfg.height - 45), font, 0.55, (0, 255, 0), 2)

            cand = selected_candidate if selected_candidate else "(press c / 1..9)"
            cv2.putText(frame, f"Candidate: {cand} | lock=l | clear=x", (10, vid_cfg.height - 25),
                        font, 0.55, (255, 255, 0), 2)

            # highlight target
            if target is not None:
                x1, y1, x2, y2, conf, _ = target
                cx = (x1 + x2) / 2.0
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 255), 2)
                cv2.circle(frame, (int(cx), int((y1 + y2) / 2)), 4, (255, 255, 255), -1)
                if "area_frac" in extra:
                    cv2.putText(frame, f"area={extra['area_frac']:.3f}", (10, 55), font, 0.7, (255, 255, 255), 2)

            cv2.imshow("Object Follow", frame)

    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        video_sub.close()
        ctrl_pub.close()
        cv2.destroyAllWindows()
        tts.close()

if __name__ == "__main__":
    main()
