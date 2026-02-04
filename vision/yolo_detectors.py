# vision/yolo_detectors.py
from ultralytics import YOLO

class YOLODetector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)

    def infer(self, frame_bgr, conf: float = 0.5, verbose: bool = False):
        return self.model(frame_bgr, conf=conf, verbose=verbose)[0]  # first result


# def pick_best_target(boxes, target_name: str | None, names: dict):
from typing import Optional, Dict

def pick_best_target(boxes, target_name: Optional[str], names: Dict):

    if target_name is None or boxes is None or len(boxes) == 0:
        return None

    best = None
    best_area = 0.0

    for b in boxes:
        cls_id = int(b.cls.item())
        cls_name = names.get(cls_id, str(cls_id))
        if cls_name != target_name:
            continue

        x1, y1, x2, y2 = b.xyxy[0].cpu().numpy()
        area = float((x2 - x1) * (y2 - y1))
        if area > best_area:
            best_area = area
            best = (float(x1), float(y1), float(x2), float(y2), float(b.conf.item()), cls_id)

    return best


def detect_hand_raise_in_roi(frame_bgr, roi_xyxy, hand_detector: YOLODetector,
                             width: int, height: int,
                             hand_class_name: str, conf_th: float):
    x1, y1, x2, y2 = roi_xyxy
    x1i, y1i, x2i, y2i = map(int, [x1, y1, x2, y2])

    # clamp
    x1i = max(0, min(width - 1, x1i))
    x2i = max(0, min(width - 1, x2i))
    y1i = max(0, min(height - 1, y1i))
    y2i = max(0, min(height - 1, y2i))

    if x2i <= x1i or y2i <= y1i:
        return False, []

    roi = frame_bgr[y1i:y2i, x1i:x2i]
    res = hand_detector.infer(roi, conf=conf_th, verbose=False)

    hits = []
    for b in res.boxes:
        cls_id = int(b.cls.item())
        name = res.names.get(cls_id, str(cls_id))
        conf = float(b.conf.item())
        if name == hand_class_name and conf >= conf_th:
            rx1, ry1, rx2, ry2 = map(float, b.xyxy[0].tolist())
            hits.append((x1 + rx1, y1 + ry1, x1 + rx2, y1 + ry2, conf))

    return (len(hits) > 0), hits
#