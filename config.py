# config.py
from dataclasses import dataclass

@dataclass
class ZMQConfig:
    video_port: int = 5555
    ctrl_port: int = 5556
    rcv_timeout_ms: int = 2000

@dataclass
class VideoConfig:
    width: int = 640
    height: int = 480
    conf_draw_th: float = 0.7
    conf_detect_th: float = 0.5

@dataclass
class ControlConfig:
    max_angular: float = 0.17
    kp_ang: float = 0.3
    kp_lin: float = 8.0
    desired_area: float = 0.2
    area_deadband: float = 0.05
    smoothing: float = 0.6
    search_linear: float = 0.0
    search_angular: float = 0.0
    max_linear_local: float = 0.25
    min_move_linear: float = 0.06
    angular_deadzone: float = 0.15

@dataclass
class HandConfig:
    enabled: bool = True
    hand_every_n: int = 3
    hand_conf_th: float = 0.65
    emergency_hold_s: float = 5.0
    person_class_name: str = "person"
    hand_class_name: str = "Hand raise"
