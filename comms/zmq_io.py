# comms/zmq_io.py
import json, time
import zmq
import numpy as np
import cv2

class ZMQVideoSubscriber:
    def __init__(self, port: int, timeout_ms: int = 2000):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE, b"")
        self.socket.setsockopt(zmq.RCVTIMEO, timeout_ms)
        self.socket.setsockopt(zmq.CONFLATE, 1)
        self.socket.setsockopt(zmq.RCVHWM, 1)
        self.socket.bind(f"tcp://*:{port}")

    def recv_frame_bgr(self):
        try:
            msg = self.socket.recv()
        except zmq.Again:
            return None

        arr = np.frombuffer(msg, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img

    def close(self):
        self.socket.close()
        self.context.term()


class ZMQControlPublisher:
    def __init__(self, port: int):
        self.ctx = zmq.Context()
        self.pub = self.ctx.socket(zmq.PUB)
        self.pub.bind(f"tcp://*:{port}")

    def send_cmd(self, linear: float, angular: float, status: str = ""):
        msg = {
            "linear": float(linear),
            "angular": float(angular),
            "status": str(status),
            "ts": time.time(),
        }
        self.pub.send_string(json.dumps(msg))

    def close(self):
        self.pub.close()
        self.ctx.term()
