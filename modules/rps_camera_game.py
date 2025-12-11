import random
import time
import subprocess
import os
import tempfile
from typing import Dict

import cv2
import numpy as np


class RPSCameraGame:
    """
    Joc piatră-foarfecă-hârtie folosind recunoașterea semnelor:
    - Piatra = pumn închis
    - Foarfecă = două degete ridicate
    - Hârtie = palmă ridicată
    """

    MOVES = ["piatră", "foarfecă", "hârtie"]

    def _capture_frame_rpicam(self) -> np.ndarray:
        """
        Capturează un frame folosind rpicam-hello --timeout 0.
        Returnează imaginea ca numpy array (BGR pentru OpenCV).
        """
        # Creează un fișier temporar pentru imagine
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Rulează rpicam-hello pentru a captura o imagine
            cmd = [
                "rpicam-hello",
                "--timeout", "0",
                "--output", temp_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"rpicam-hello a eșuat: {result.stderr}")
            
            # Citește imaginea capturată
            frame = cv2.imread(temp_path)
            if frame is None:
                raise RuntimeError("Nu am putut citi imaginea capturată.")
            
            return frame
            
        finally:
            # Șterge fișierul temporar
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass

    def _count_fingers(self, frame) -> int:
        """
        Numără degetele ridicate din mână.
        Returnează numărul de degete detectate.
        """
        # Focus pe centrul imaginii
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
            return 0

        max_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(max_contour) < 1000:
            return 0

        hull = cv2.convexHull(max_contour, returnPoints=False)
        if hull is None or len(hull) < 3:
            return 0

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
                angle = np.arccos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c + 1e-6))
                if angle <= np.pi / 2 and d > 1000:
                    finger_count += 1

        # Numărul de degete = finger_count + 1 (degetul mare nu e detectat de convexity defects)
        return finger_count + 1

    def _detect_move(self, frame) -> str:
        """
        Detectează mutarea jucătorului:
        - Piatra = pumn închis (0-1 degete)
        - Foarfecă = două degete ridicate (2 degete)
        - Hârtie = palmă ridicată (4-5 degete)
        """
        finger_count = self._count_fingers(frame)
        
        if finger_count <= 1:
            return "piatră"  # Pumn închis
        elif finger_count == 2:
            return "foarfecă"  # Două degete
        elif finger_count >= 4:
            return "hârtie"  # Palmă ridicată
        else:
            # Caz intermediar (3 degete) - alegem cea mai probabilă
            return "foarfecă"

    def _warm_capture(self, attempts: int = 2, delay: float = 0.5):
        """Face mai multe încercări de captură pentru a se asigura că primește un frame valid."""
        for attempt in range(attempts):
            try:
                frame = self._capture_frame_rpicam()
                if frame is not None and frame.size > 0:
                    return frame
            except subprocess.TimeoutExpired:
                if attempt == attempts - 1:
                    raise RuntimeError("Timeout la capturarea imaginii. Verifică dacă camera funcționează.")
                time.sleep(delay)
            except Exception as e:
                if attempt == attempts - 1:
                    raise
                time.sleep(delay)
        return None

    def play_round(self, camera_index: int = 0) -> Dict:
        """
        Joacă o rundă. Sistemul alege aleator, jucătorul alege prin recunoașterea semnului.
        Timer-ul este gestionat în UI, nu aici.
        """
        try:
            # Capturează frame folosind rpicam-hello
            frame = self._warm_capture()
            if frame is None:
                raise RuntimeError("Nu am putut citi un frame de la cameră.")

            # Sistemul alege aleator
            ai_move = random.choice(self.MOVES)
            
            # Jucătorul alege prin recunoașterea semnului
            player_move = self._detect_move(frame)
            
            # Determină câștigătorul
            result = self._winner(player_move, ai_move)
            
            return {
                "player_move": player_move,
                "ai_move": ai_move,
                "result": result
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Eroare la rularea rpicam-hello: {e}")
        except FileNotFoundError:
            raise RuntimeError("rpicam-hello nu este instalat sau nu este în PATH.")
        except Exception as e:
            raise RuntimeError(f"Eroare cameră: {e}")

    def _winner(self, player: str, ai: str) -> str:
        """Determină câștigătorul și returnează mesajul corespunzător."""
        if player == ai:
            return "Egal"
        if (
            (player == "piatră" and ai == "foarfecă")
            or (player == "foarfecă" and ai == "hârtie")
            or (player == "hârtie" and ai == "piatră")
        ):
            return "player_wins"  # Jucătorul câștigă
        return "ai_wins"  # AI câștigă


if __name__ == "__main__":
    game = RPSCameraGame()
    print(game.play_round(camera_index=0))
