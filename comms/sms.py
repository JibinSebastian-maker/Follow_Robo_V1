# comms/sms.py
import os, time

try:
    from twilio.rest import Client
except Exception:
    Client = None

class TwilioSMS:
    def __init__(self):
        self.sid   = os.getenv("TWILIO_SID", "")
        self.token = os.getenv("TWILIO_TOKEN", "")
        self.from_ = os.getenv("TWILIO_FROM", "")
        self.to    = os.getenv("ALERT_TO", "")

        self.client = None
        if Client and self.sid and self.token:
            self.client = Client(self.sid, self.token)

        self._last_sms_t = 0.0

        print("TWILIO_SID:", (self.sid[:6] + "...") if self.sid else "MISSING")
        print("TWILIO_TOKEN set:", bool(self.token))
        print("TWILIO_FROM:", self.from_)
        print("ALERT_TO:", self.to)

    def send(self, text: str, cooldown_s: float = 30.0):
        now = time.time()
        if now - self._last_sms_t < cooldown_s:
            return

        if self.client is None or not self.from_ or not self.to:
            print("[SMS NOT SENT] Configure TWILIO_SID/TWILIO_TOKEN/TWILIO_FROM/ALERT_TO env vars.")
            print("Message:", text)
            self._last_sms_t = now
            return

        try:
            self.client.messages.create(body=text, from_=self.from_, to=self.to)
            print("[SMS SENT]", text)
            self._last_sms_t = now
        except Exception as e:
            print("[SMS ERROR]", e)
