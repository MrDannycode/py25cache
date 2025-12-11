import random
import time
from typing import Dict

import cv2t
import numpy as np


class RPSCameraGame:
    """
    Joc piatră-foarfecă-hârtie folosind conturul mâinii.
    Heuristic simplu: număr degete ridicate -> hartie (>=4), foarfecă (~2),
    altfel piatră.
    """

    MOVES = ["piatră", "foarfecă", "hârtie"]

    def _detect_move(self, frame) -> str:
        # Focus pe centrul imaginii pentru a evita zgomot de fundal
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2
        size = min(h, w) // 2
        roi = frame[cy - size // 2 : cy + size // 2, cx - size // 2 : cx + size // 2]

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        thresh = cv2.bitwise_not(thresh)

        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return random.choice(self.MOVES)

        max_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(max_contour) < 1000:
            return random.choice(self.MOVES)

        hull = cv2.convexHull(max_contour, returnPoints=False)
        if hull is None or len(hull) < 3:
            return random.choice(self.MOVES)

        defects = cv2.convexityDefects(max_contour, hull)
        finger_count = 0
        if defects is not None:
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(max_contour[s][0])
                end = tuple(max_contour[e][0])
                far = tuple(max_contour[f][0])
                a = np.linalg.norm(np.array(end) - np.array(start))
                b = np.linalg.norm(np.array(far) - np.array(start))
                c = np.linalg.norm(np.array(end) - np.array(far))
                # Cosinus legea cosinusului
                angle = np.arccos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c + 1e-6))
                if angle <= np.pi / 2 and d > 1000:
                    finger_count += 1

        if finger_count >= 3:
            return "hârtie"
        if finger_count == 1 or finger_count == 2:
            return "foarfecă"
        return "piatră"

    def _warm_capture(self, cap, attempts: int = 5, delay: float = 0.1):
        frame = None
        for _ in range(attempts):
            ret, frame = cap.read()
            if ret and frame is not None:
                return frame
            time.sleep(delay)
        return None

    def play_round(self, camera_index: int = 0) -> Dict:
        cap = cv2.VideoCapture(camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not cap.isOpened():
            raise RuntimeError(f"Nu pot deschide camera {camera_index}")

        try:
            frame = self._warm_capture(cap)
            if frame is None:
                raise RuntimeError("Nu am putut citi un frame de la cameră.")

            player_move = self._detect_move(frame)
            ai_move = random.choice(self.MOVES)
            result = self._winner(player_move, ai_move)
            return {"player_move": player_move, "ai_move": ai_move, "result": result}
        finally:
            cap.release()

    def _winner(self, player: str, ai: str) -> str:
        if player == ai:
            return "Egal"
        if (
            (player == "piatră" and ai == "foarfecă")
            or (player == "foarfecă" and ai == "hârtie")
            or (player == "hârtie" and ai == "piatră")
        ):
            return "Ai câștigat!"
        return "AI a câștigat!"


if __name__ == "__main__":
    game = RPSCameraGame()
    print(game.play_round(camera_index=0))
