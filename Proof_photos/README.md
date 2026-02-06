


```markdown
# 🤖 Follow Bot – Vision-Based Robot Following System

A real-time robot following system built with **YOLOv8**, **ZeroMQ**, and **Python**, supporting dynamic target selection, smooth motion control, voice feedback, and emergency hand-raise detection with SMS alerts.

---

## ✨ Features

### 🎯 Object Following
- Real-time object detection using YOLOv8
- Dynamically select any detected object class at runtime
- Locks onto the largest visible instance of the target class
- Smooth linear & angular velocity control

### 🧠 Smart Control Logic
- Proportional (P) controller for steering and distance
- Deadzones to prevent jitter
- Motion smoothing for stable robot movement
- Automatic SEARCH mode when no target is selected

### ✋ Emergency Hand-Raise Detection
- Secondary YOLO model for hand-raise gesture detection
- Active only when following a person
- Runs every N frames for performance
- Emergency stop overrides all motion commands
- Emergency state persists for a configurable duration

### 🔊 Voice Feedback (Text-to-Speech)
- Asynchronous, non-blocking TTS
- Announces:
  - Target locked
  - Target cleared
  - Emergency detected
- Cooldown system to avoid repeated speech

### 📱 SMS Alerts (Twilio)
- Sends SMS on emergency hand-raise detection
- Cooldown protection to prevent spam
- Uses environment variables for security
- Optional (system works without SMS)

### 🎮 Keyboard Controls
| Key | Action |
|----|-------|
| `c` | Cycle detected object classes |
| `1–9` | Select object by index |
| `l` | Lock selected object as target |
| `x` | Clear target (SEARCH mode) |
| `q` | Quit application |

---

## 📂 Project Structure

```

follow_bot/
├── main.py
├── config.py
│
├── comms/
│   ├── zmq_io.py
│   ├── tts.py
│   └── sms.py
│
├── vision/
│   └── yolo_detectors.py
│
├── control/
│   └── follower.py
│
├── runs/
│   └── best.pt
│
└── yolov8n.pt

```

---

## 🧠 System Architecture

```

Camera / ZMQ Stream
↓
YOLOv8 Detection
↓
Target Selection
↓
Motion Controller
↓
ZeroMQ Control Output
↓
Robot

```

Emergency pipeline:
```

Person ROI → Hand YOLO → EMERGENCY STOP
↳ Voice Alert
↳ SMS Alert

````

---

## ⚙️ Requirements

### Python
- Python 3.8 or 3.9 recommended
- Python 3.10+ supported

### Dependencies
```bash
pip install ultralytics opencv-python pyttsx3 pyzmq torch torchvision
pip install twilio
````

---

## 🔐 Environment Variables (SMS – Optional)

```bash
TWILIO_SID=ACxxxxxxxxxxxxxxxx
TWILIO_TOKEN=xxxxxxxxxxxxxxxx
TWILIO_FROM=+1234567890
ALERT_TO=+491234567890
```

If not set, the system runs normally without SMS alerts.

---

## ▶️ How to Run

From the project root directory:

```bash
python follow_bot/main.py
```

Ensure:

* Video frames are being published over ZeroMQ
* `best.pt` exists at the configured path
* Robot is subscribed to control messages

---

## 🛠 Configuration

All tunable parameters are located in `config.py`, including:

* Speed limits
* PID gains
* Deadzones
* Detection thresholds
* Emergency timing
* Motion smoothing

---

## 🧪 Tested Use Cases

* Vision-based human-following robot
* PC ↔ Robot communication via ZeroMQ
* Jetson Nano / Xavier pipelines
* Safety-aware robotics demos
* Human–Robot Interaction (HRI)

---

## 🚀 Future Improvements

* ROS2 integration
* Multi-target tracking
* Face recognition
* Web dashboard
* Logging and telemetry
* Unit tests

---

## 📜 License

MIT License

---

## 🙌 Acknowledgements

* Ultralytics YOLOv8
* PyTorch
* OpenCV
* ZeroMQ

```
