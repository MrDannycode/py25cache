import os
import random
import time
from dataclasses import dataclass
from typing import List, Dict, Optional

import cv2


@dataclass
class Scientist:
    name: str
    description: str
    image_path: Optional[str] = None


class ScientistMatcher:
    """
    Captură un frame, detectează fața și întoarce un om de știință „asemănător”.
    Pentru simplitate pe Raspberry Pi alegem un profil random dintr-o listă.
    """

    def __init__(self, scientists: Optional[List[Scientist]] = None):
        self.scientists = scientists or self._default_scientists()
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def _default_scientists(self) -> List[Scientist]:
        return [
            Scientist("Albert Einstein", "Pionier în fizica teoretică și relativitate."),
            Scientist("Marie Curie", "Cercetătoare în radioactivitate, dublu Nobel."),
            Scientist("Nikola Tesla", "Inventator și vizionar al curentului alternativ."),
            Scientist("Ada Lovelace", "Prima programatoare, a imaginat mașini computaționale."),
            Scientist("Rosalind Franklin", "A elucidat structura ADN prin difracție cu raze X."),
            Scientist("Katherine Johnson", "Matematiciană NASA, calcule critice pentru zboruri spațiale."),
        ]

    def _detect_face(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
        return faces

    def _warm_capture(self, cap, attempts: int = 5, delay: float = 0.1):
        """Încercă să citești câteva cadre pentru a încălzi camera."""
        frame = None
        for _ in range(attempts):
            ret, frame = cap.read()
            if ret and frame is not None:
                return frame
            time.sleep(delay)
        return None

    def capture_and_match(self, camera_index: int = 0) -> Optional[Dict]:
        cap = cv2.VideoCapture(camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not cap.isOpened():
            raise RuntimeError(f"Nu pot deschide camera {camera_index}")

        try:
            frame = self._warm_capture(cap)
            if frame is None:
                raise RuntimeError("Nu am putut citi un frame de la cameră.")

            faces = self._detect_face(frame)
            if len(faces) == 0:
                return None

            # Alege un om de știință random (în loc de heavy ML)
            scientist = random.choice(self.scientists)
            return {
                "name": scientist.name,
                "description": scientist.description,
                "image_path": scientist.image_path,
                "faces_detected": len(faces),
            }
        finally:
            cap.release()


if __name__ == "__main__":
    matcher = ScientistMatcher()
    result = matcher.capture_and_match(camera_index=0)
    print(result)
