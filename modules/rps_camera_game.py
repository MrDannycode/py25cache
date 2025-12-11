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

    def _detect_skin(self, frame):
        """Detectează pielea din imagine folosind HSV."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Range pentru culoarea pielii în HSV
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Morfologie pentru a elimina zgomotul
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        return mask

    def _count_fingers_advanced(self, frame) -> int:
        """
        Numără degetele folosind o metodă îmbunătățită.
        Returnează numărul de degete detectate.
        """
        # Focus pe centrul imaginii
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2
        size = min(h, w) // 3  # ROI mai mare pentru a captura întreaga mână
        roi = frame[max(0, cy - size):min(h, cy + size), 
                    max(0, cx - size):min(w, cx + size)]
        
        if roi.size == 0:
            return 0

        # Detectează pielea
        skin_mask = self._detect_skin(roi)
        
        # Găsește contururi
        contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return 0

        # Găsește cel mai mare contur (probabil mâna)
        max_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(max_contour)
        
        if area < 3000:  # Arie minimă pentru mână
            return 0

        # Calculează hull și defects
        hull = cv2.convexHull(max_contour, returnPoints=False)
        if hull is None or len(hull) < 3:
            return 0

        defects = cv2.convexityDefects(max_contour, hull)
        if defects is None:
            return 0

        # Numără degetele folosind defects
        finger_count = 0
        for i in range(defects.shape[0]):
            s, e, f, d = defects[i, 0]
            start = tuple(max_contour[s][0])
            end = tuple(max_contour[e][0])
            far = tuple(max_contour[f][0])
            
            # Calculează distanțele
            a = np.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
            b = np.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
            c = np.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)
            
            # Calculează unghiul
            angle = np.arccos((b**2 + c**2 - a**2) / (2 * b * c + 1e-6))
            
            # Un defect valid este unul cu unghi < 90 grade și distanță suficientă
            if angle <= np.pi / 2 and d > 15000:  # Threshold mai mare pentru mai multă precizie
                finger_count += 1

        # Numărul de degete = finger_count (fără +1, deoarece numărăm corect)
        return finger_count

    def _detect_move(self, frame) -> str:
        """
        Detectează mutarea jucătorului folosind mai multe metode:
        - Piatra = pumn închis (0-1 degete, arie mică, aspect ratio compact)
        - Foarfecă = două degete ridicate (2 degete, aspect ratio vertical)
        - Hârtie = palmă ridicată (4-5 degete, arie mare)
        """
        # Focus pe centrul imaginii
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2
        size = min(h, w) // 3
        roi = frame[max(0, cy - size):min(h, cy + size), 
                    max(0, cx - size):min(w, cx + size)]
        
        if roi.size == 0:
            return random.choice(self.MOVES)

        # Detectează pielea
        skin_mask = self._detect_skin(roi)
        
        # Găsește contururi
        contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return random.choice(self.MOVES)

        max_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(max_contour)
        
        if area < 3000:
            return random.choice(self.MOVES)

        # Calculează aspect ratio
        x, y, w_rect, h_rect = cv2.boundingRect(max_contour)
        aspect_ratio = float(w_rect) / h_rect if h_rect > 0 else 0

        # Numără degetele
        finger_count = self._count_fingers_advanced(frame)
        
        # Logica de decizie îmbunătățită
        if finger_count == 0 or finger_count == 1:
            # Pumn închis: 0-1 degete sau arie mică cu aspect ratio compact
            if area < 15000 or (aspect_ratio > 0.7 and aspect_ratio < 1.3):
                return "piatră"
        
        if finger_count == 2:
            # Două degete: exact 2 degete sau aspect ratio vertical
            if aspect_ratio < 0.8 or finger_count == 2:
                return "foarfecă"
        
        if finger_count >= 4:
            # Palmă: 4-5 degete sau arie mare
            return "hârtie"
        
        # Cazuri intermediare - folosim heuristica
        if finger_count == 3:
            # 3 degete - probabil foarfecă sau palmă parțială
            if aspect_ratio < 0.9:
                return "foarfecă"
            else:
                return "hârtie"
        
        # Fallback bazat pe arie și aspect ratio
        if area > 20000:
            return "hârtie"  # Arie mare = palmă
        elif aspect_ratio < 0.7:
            return "foarfecă"  # Aspect ratio vertical = degete
        else:
            return "piatră"  # Default = pumn

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
