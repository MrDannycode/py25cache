import cv2
import threading
import time


class PresenceDetector:
    def __init__(
        self,
        camera_index: int = 0,
        motion_threshold: float = 15.0,      # mai sensibil
        min_changed_pixels: int = 1000,     # mai puțini pixeli
        presence_timeout: float = 3.0,
    ):
        self.camera_index = camera_index
        self.motion_threshold = motion_threshold
        self.min_changed_pixels = min_changed_pixels
        self.presence_timeout = presence_timeout

        self._capture = None
        self._thread = None
        self._running = False

        self._person_present = False
        self._last_motion_time = 0.0
        self._lock = threading.Lock()

    def start(self):
        if self._running:
            return

        self._capture = cv2.VideoCapture(self.camera_index)
        if not self._capture.isOpened():
            raise RuntimeError(f"Nu pot deschide camera cu index {self.camera_index}")

        print("[PresenceDetector] Camera deschisă OK")

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def is_person_present(self) -> bool:
        with self._lock:
            if time.time() - self._last_motion_time > self.presence_timeout:
                self._person_present = False
            return self._person_present

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

        if self._capture is not None:
            try:
                self._capture.release()
            except Exception:
                pass
            self._capture = None

        print("[PresenceDetector] Oprit.")

    def _run_loop(self):
        prev_gray = None

        while self._running:
            ret, frame = self._capture.read()
            if not ret or frame is None:
                print("[PresenceDetector] Frame invalid, aștept...")
                time.sleep(0.1)
                continue

            frame_small = cv2.resize(frame, (320, 240))
            gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)

            if prev_gray is not None:
                diff = cv2.absdiff(gray, prev_gray)
                _, thresh = cv2.threshold(diff, self.motion_threshold, 255, cv2.THRESH_BINARY)
                changed_pixels = cv2.countNonZero(thresh)

                # DEBUG: vezi câți pixeli se schimbă
                # (comentat dacă te deranjează spam-ul)
                # print("[PresenceDetector] changed_pixels =", changed_pixels)

                if changed_pixels > self.min_changed_pixels:
                    with self._lock:
                        self._last_motion_time = time.time()
                        if not self._person_present:
                            print("[PresenceDetector] Mișcare detectată -> persoană PREZENTĂ")
                        self._person_present = True

            prev_gray = gray
            time.sleep(0.05)


if __name__ == "__main__":
    detector = PresenceDetector(camera_index=0)
    try:
        print("Pornez detectorul de prezență... (Ctrl+C pentru ieșire)")
        detector.start()
        while True:
            present = detector.is_person_present()
            print("Persoană prezentă:", present)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Oprire...")
    finally:
        detector.stop()

