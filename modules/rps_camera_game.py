#!/usr/bin/python3
import random
import time
import subprocess
from typing import Dict

import cv2
import numpy as np


class RPSCameraGame:
    """
    Joc piatră-foarfecă-hârtie folosind conturul mâinii.
    Heuristică simplă: număr degete ridicate -> hârtie (>=4), foarfecă (≈2), altfel piatră.
    """

    MOVES = ["piatră", "foarfecă", "hârtie"]

    def __init__(self):
        # rezoluția la care cerem poza de la libcamera
        self.width = 640
        self.height = 480

    # ---------- camera ----------

    def _capture_frame(self) -> np.ndarray:
        """
        Face o fotografie cu libcamera-still și o întoarce ca imagine OpenCV (BGR).
        NU avem nevoie de video continuu pentru acest joc, doar de cadre individuale.
        """
        tmp_path = "/tmp/rps_frame.jpg"
        cmd = [
            "libcamera-still",
            "-n",              # no preview
            "-t", "1",         # 1 ms "shutter time" – practic instant
            "--width", str(self.width),
            "--height", str(self.height),
            "-o", tmp_path,
        ]
        # Dacă apar erori la cameră, va arunca excepție
        subprocess.run(cmd, check=True)
        frame = cv2.imread(tmp_path)
        if frame is None:
            raise RuntimeError("Nu am reușit să citesc cadrul capturat.")
        return frame

    # ---------- analiză imagine ----------

    def _detect_move(self) -> str:
        """
        Capturează un cadru și încearcă să determine mutarea jucătorului.
        """
        frame = self._capture_frame()

        # Oglindim ca să pară comportament "selfie"
        frame = cv2.flip(frame, 1)

        # Focus pe centrul imaginii – zona în care presupunem că e mâna
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2
        size = min(h, w) // 2
        x1, y1 = cx - size // 2, cy - size // 2
        x2, y2 = cx + size // 2, cy + size // 2
        roi = frame[y1:y2, x1:x2]

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Prag automat (Otsu)
        _, thresh = cv2.threshold(
            blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # inversăm: mână = alb, fundal = negru (dacă e nevoie)
        # thresh = cv2.bitwise_not(thresh)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return random.choice(self.MOVES)  # ceva fallback

        # cel mai mare contur = probabil mâna
        cnt = max(contours, key=cv2.contourArea)

        # Convex hull & defects pentru a număra "degete"
        hull = cv2.convexHull(cnt, returnPoints=False)
        if hull is None or len(hull) < 3:
            return "piatră"

        defects = cv2.convexityDefects(cnt, hull)
        if defects is None:
            return "piatră"

        finger_gaps = 0
        for i in range(defects.shape[0]):
            s, e, f, depth = defects[i, 0]
            # filtrăm defectele "mici" – adică zgomot, nu spații între degete
            if depth > 1000:  # prag empiric, poți ajusta
                finger_gaps += 1

        # aproximăm numărul degete = finger_gaps + 1
        fingers = finger_gaps + 1

        if fingers >= 4:
            return "hârtie"
        elif fingers >= 2:
            return "foarfecă"
        else:
            return "piatră"

    # ---------- logică joc ----------

    def _decide_winner(self, player: str, computer: str) -> str:
        if player == computer:
            return "egal"
        if (
            (player == "piatră" and computer == "foarfecă")
            or (player == "foarfecă" and computer == "hârtie")
            or (player == "hârtie" and computer == "piatră")
        ):
            return "tu"
        return "calculatorul"

    def play_round(self):
        input("Ridică mâna în fața camerei și apasă Enter când ești gata...")
        player_move = self._detect_move()
        computer_move = random.choice(self.MOVES)
        winner = self._decide_winner(player_move, computer_move)

        print(f"Tu: {player_move} | Calculator: {computer_move}")
        if winner == "egal":
            print("Rezultat: egal!")
        elif winner == "tu":
            print("Rezultat: ai câștigat! 🎉")
        else:
            print("Rezultat: a câștigat calculatorul 😅")


if __name__ == "__main__":
    game = RPSCameraGame()
    while True:
        game.play_round()
        again = input("Mai joci o rundă? (d/N) ").strip().lower()
        if again != "d":
            break
