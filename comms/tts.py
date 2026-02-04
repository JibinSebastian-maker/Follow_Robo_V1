# comms/tts.py
import queue, threading, time
import pyttsx3

class AsyncTTS:
    def __init__(self, rate: int = 175):
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", rate)

        self._q = queue.Queue()
        self._last_spoken = ""
        self._last_spoken_t = 0.0

        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        while True:
            text = self._q.get()
            if text is None:
                break
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print("[TTS ERROR]", e)

    def say(self, text: str, cooldown_s: float = 2.0):
        now = time.time()
        if text == self._last_spoken and (now - self._last_spoken_t) < cooldown_s:
            return
        self._last_spoken = text
        self._last_spoken_t = now
        self._q.put(text)

    def close(self):
        self._q.put(None)
