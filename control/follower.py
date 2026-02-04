# control/follower.py
import time
import numpy as np
from typing import Optional

def clamp(x, lo, hi):
    return float(np.clip(x, lo, hi))

class FollowerController:
    def __init__(self, width: int, height: int, cfg):
        self.WIDTH = width
        self.HEIGHT = height
        self.CENTER_X = width // 2
        self.cfg = cfg

        self.linear_s = 0.0
        self.angular_s = 0.0

        self.frame_i = 0
        self.emergency_until = 0.0

    # def compute(self, target_xyxyconf, target_class: str | None, now: float):
    def compute(self, target_xyxyconf, target_class: Optional[str], now: float):

        """
        Returns:
          linear, angular, status, extra(dict)
        """
        extra = {}
        linear = self.cfg.search_linear
        angular = self.cfg.search_angular
        status = "SEARCH" if target_class is None else f"FOLLOW ROBOT TARGETING {target_class.upper()}"

        if target_xyxyconf is None:
            return linear, angular, status, extra

        x1, y1, x2, y2, conf, cls_id = target_xyxyconf

        cx = (x1 + x2) / 2.0
        err_x = (self.CENTER_X - cx) / self.CENTER_X

        # angular
        if abs(err_x) < self.cfg.angular_deadzone:
            angular = 0.0
        else:
            angular = clamp(self.cfg.kp_ang * err_x, -self.cfg.max_angular, self.cfg.max_angular)

        # linear from area
        box_area = (x2 - x1) * (y2 - y1)
        frame_area = self.WIDTH * self.HEIGHT
        area_frac = box_area / frame_area
        area_error = self.cfg.desired_area - area_frac

        if abs(area_error) < self.cfg.area_deadband:
            linear = 0.0
        else:
            linear = clamp(self.cfg.kp_lin * area_error, -self.cfg.max_linear_local, self.cfg.max_linear_local)
            if 0 < abs(linear) < self.cfg.min_move_linear:
                linear = self.cfg.min_move_linear if linear > 0 else -self.cfg.min_move_linear

        status = f"TRACK '{target_class}' ({conf:.2f})"
        extra.update({"cx": cx, "area_frac": area_frac})
        return linear, angular, status, extra

    def smooth(self, linear, angular):
        s = self.cfg.smoothing
        self.linear_s = s * self.linear_s + (1 - s) * linear
        self.angular_s = s * self.angular_s + (1 - s) * angular
        return self.linear_s, self.angular_s
