#!/usr/bin/python3
import random
import time
from typing import Dict

import cv2
import numpy as np
from picamera2 import Picamera2


class RPSCameraGame:
    """
    Joc piatră-foarfecă-hârtie folosind conturul mâinii.
    Heuristic simplu: număr degete ridicate -> hartie (>=4), foarfecă (~2),
    altfel piatră.
    """

    MOVES = ["piatră", "foarfecă", "hârtie"]

    def __init__(self):
        # Inițializare cameră Picamera2 (funcționează cu toate camerele CSI)
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(1.0)  # timp scurt de încălzire

    def _detect_move(self, frame) -> str:
        # Oglindim pentru comportament "selfie"
        frame = cv2.flip(frame, 1)

        # Focus pe centrul imaginii
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2
        size = min(h, w) // 2
        roi = frame[
            cy - size // 2 : cy + size // 2,
            cx - size // 2 : cx + size // 2,
        ]

        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Prag automat (Otsu)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        thresh = cv2.bitwise_not(thresh)  # inversăm: mâna = alb

        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return random.choice(self.MOVES)

        max_contour = max(contours, key=cv2.contourArea)

        if cv2.contourArea(max_contour) < 1000:
            return random.choice(self.MOVES)

        # Convex hull & defects – pentru numărat degete
        hull = cv2.convexHull(max_contour, returnPoints=False)
        if hull is None or len(hull) < 3:
            return "piatră"

        defects = cv2.convexityDefects(max_contour, hull)
        if defects is None:
            return "piatră"

        finger_count = 0
        for i in range(defects.shape[0]):
            s, e, f, d = defects[i, 0]
            start = max_contour[s][0]
            end = max_contour[e][0]
            far = max_contour[f][0]

            a = np.linalg.norm(end - start)
            b = np.linalg.norm(far - start)
            c = np.linalg.norm(end - far)

            if b * c == 0:
                continue

            angle = np.degrees(np.arccos((b**2 + c**2 - a**2) / (2 * b * c)))

            if angle < 90 and d > 1000:
                finger_count += 1

        fingers = finger_count + 1  # aproximare

        if fingers >= 4:
            return "hârtie"
        elif 2 <= fingers <= 3:
            return "foarfecă"
        else:
            return "piatră"

    def _decide_winner(self, player: str, computer: str) -> str:
        if player == computer:
            return "egalitate"

        if (
            (player == "piatră" and computer == "foarfecă")
            or (player == "foarfecă" and computer == "hârtie")
            or (player == "hârtie" and computer == "piatră")
        ):
            return "tu"
        else:
            return "computerul"

    def play_round(self, timeout_seconds: int = 5) -> Dict[str, str]:
        """
        Capturează un frame de la cameră, detectează gestul
        și decide câștigătorul.
        """
        end_time = time.time() + timeout_seconds
        frame = None

        while time.time() < end_time:
            frame = self.picam2.capture_array()
            if frame is not None:
                break

        if frame is None:
            raise RuntimeError("Nu am putut citi un frame de la cameră.")

        player_move = self._detect_move(frame)
        computer_move = random.choice(self.MOVES)
        winner = self._decide_winner(player_move, computer_move)

        return {
            "mutarea_ta": player_move,
            "mutarea_computerului": computer_move,
            "câștigător": winner,
        }


if __name__ == "__main__":
    game = RPSCameraGame()
    try:
        rezultat = game.play_round(timeout_seconds=5)
        print("Mutarea ta:", rezultat["mutarea_ta"])
        print("Mutarea computerului:", rezultat["mutarea_computerului"])
        print("Câștigător:", rezultat["câștigător"])
    finally:
        game.picam2.stop()
