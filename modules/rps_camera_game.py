import random
import time
import subprocess
import os
import tempfile
from typing import Dict, List, Tuple, Optional
from pathlib import Path

import cv2
import numpy as np

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("MediaPipe nu este instalat. Folosind metoda alternativă.")


class RPSCameraGame:
    """
    Joc piatră-foarfecă-hârtie folosind AI pentru recunoașterea semnelor:
    - Piatra = pumn închis
    - Foarfecă = două degete ridicate
    - Hârtie = palmă ridicată
    
    Detectează 2 mâini simultan și compară cu pozele salvate.
    """

    MOVES = ["piatră", "foarfecă", "hârtie"]
    
    def __init__(self):
        self.reference_images_dir = Path("assets/rps_references")
        self.reference_images_dir.mkdir(parents=True, exist_ok=True)
        
        # Inițializează MediaPipe dacă e disponibil
        if MEDIAPIPE_AVAILABLE:
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            )
            self.mp_drawing = mp.solutions.drawing_utils
        else:
            self.hands = None
        
        # Încarcă pozele de referință dacă există
        self._load_reference_images()

    def _load_reference_images(self):
        """Încarcă pozele de referință pentru fiecare semn."""
        self.reference_images = {
            "piatră": [],
            "foarfecă": [],
            "hârtie": []
        }
        
        for move in self.MOVES:
            ref_dir = self.reference_images_dir / move
            if ref_dir.exists():
                for img_path in ref_dir.glob("*.jpg"):
                    img = cv2.imread(str(img_path))
                    if img is not None:
                        self.reference_images[move].append(img)

    def _capture_frame_rpicam(self) -> np.ndarray:
        """
        Capturează un frame folosind rpicam-hello --timeout 0.
        Returnează imaginea ca numpy array (BGR pentru OpenCV).
        """
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        try:
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
            
            frame = cv2.imread(temp_path)
            if frame is None:
                raise RuntimeError("Nu am putut citi imaginea capturată.")
            
            return frame
            
        finally:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass

    def _extract_hand_roi(self, frame: np.ndarray, landmarks, h: int, w: int) -> Optional[np.ndarray]:
        """Extrage regiunea de interes (ROI) pentru o mână."""
        if not landmarks:
            return None
        
        # Calculează bounding box pentru mână
        x_coords = [lm.x * w for lm in landmarks.landmark]
        y_coords = [lm.y * h for lm in landmarks.landmark]
        
        x_min, x_max = int(min(x_coords)), int(max(x_coords))
        y_min, y_max = int(min(y_coords)), int(max(y_coords))
        
        # Adaugă padding
        padding = 30
        x_min = max(0, x_min - padding)
        y_min = max(0, y_min - padding)
        x_max = min(w, x_max + padding)
        y_max = min(h, y_max + padding)
        
        roi = frame[y_min:y_max, x_min:x_max]
        if roi.size == 0:
            return None
        
        # Redimensionează pentru comparare
        roi = cv2.resize(roi, (224, 224))
        return roi

    def _compare_with_references(self, hand_roi: np.ndarray, move: str) -> float:
        """Compară ROI-ul mâinii cu pozele de referință pentru un semn."""
        if not self.reference_images[move]:
            return 0.0
        
        best_match = 0.0
        
        for ref_img in self.reference_images[move]:
            # Redimensionează imaginea de referință
            ref_resized = cv2.resize(ref_img, (224, 224))
            
            # Compară folosind histogramă de culori
            hand_hist = cv2.calcHist([hand_roi], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
            ref_hist = cv2.calcHist([ref_resized], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
            
            # Corelație între histograme
            correlation = cv2.compareHist(hand_hist, ref_hist, cv2.HISTCMP_CORREL)
            best_match = max(best_match, correlation)
        
        return best_match

    def _detect_gesture_mediapipe(self, frame: np.ndarray) -> List[Tuple[str, float]]:
        """Detectează gesturile folosind MediaPipe și compară cu referințele."""
        if not MEDIAPIPE_AVAILABLE or not self.hands:
            return []
        
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        detected_gestures = []
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Extrage ROI pentru mână
                hand_roi = self._extract_hand_roi(frame, hand_landmarks, h, w)
                if hand_roi is None:
                    continue
                
                # Numără degetele ridicate
                finger_count = self._count_fingers_from_landmarks(hand_landmarks, h, w)
                
                # Compară cu pozele de referință
                best_move = None
                best_score = 0.0
                
                for move in self.MOVES:
                    score = self._compare_with_references(hand_roi, move)
                    if score > best_score:
                        best_score = score
                        best_move = move
                
                # Verifică și cu numărul de degete
                if finger_count == 0 or finger_count == 1:
                    if best_move != "piatră" or best_score < 0.3:
                        best_move = "piatră"
                        best_score = 0.5
                elif finger_count == 2:
                    if best_move != "foarfecă" or best_score < 0.3:
                        best_move = "foarfecă"
                        best_score = 0.5
                elif finger_count >= 4:
                    if best_move != "hârtie" or best_score < 0.3:
                        best_move = "hârtie"
                        best_score = 0.5
                
                if best_move and best_score > 0.2:
                    detected_gestures.append((best_move, best_score))
        
        return detected_gestures

    def _count_fingers_from_landmarks(self, landmarks, h: int, w: int) -> int:
        """Numără degetele ridicate folosind landmark-urile MediaPipe."""
        # Puncte cheie pentru degete
        finger_tips = [4, 8, 12, 16, 20]  # Deget mare, arătător, mijlociu, inelar, mic
        finger_pips = [3, 6, 10, 14, 18]  # Articulații pentru degete
        
        fingers_up = 0
        
        # Deget mare (verificare specială - stânga/dreapta)
        if landmarks.landmark[4].x > landmarks.landmark[3].x:
            fingers_up += 1
        
        # Celelalte 4 degete (verificare sus/jos)
        for i in range(1, 5):
            if landmarks.landmark[finger_tips[i]].y < landmarks.landmark[finger_pips[i]].y:
                fingers_up += 1
        
        return fingers_up

    def _detect_gesture_fallback(self, frame: np.ndarray) -> List[Tuple[str, float]]:
        """Metodă alternativă de detectare când MediaPipe nu e disponibil."""
        # Folosește metoda veche de numărare degete
        finger_count = self._count_fingers_advanced(frame)
        
        if finger_count == 0 or finger_count == 1:
            return [("piatră", 0.6)]
        elif finger_count == 2:
            return [("foarfecă", 0.6)]
        elif finger_count >= 4:
            return [("hârtie", 0.6)]
        else:
            return [("piatră", 0.4)]  # Default

    def _count_fingers_advanced(self, frame) -> int:
        """Numără degetele folosind metoda veche (fallback)."""
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2
        size = min(h, w) // 3
        roi = frame[max(0, cy - size):min(h, cy + size), 
                    max(0, cx - size):min(w, cx + size)]
        
        if roi.size == 0:
            return 0

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        thresh = cv2.bitwise_not(thresh)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return 0

        max_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(max_contour) < 3000:
            return 0

        hull = cv2.convexHull(max_contour, returnPoints=False)
        if hull is None or len(hull) < 3:
            return 0

        defects = cv2.convexityDefects(max_contour, hull)
        if defects is None:
            return 0

        finger_count = 0
        for i in range(defects.shape[0]):
            s, e, f, d = defects[i, 0]
            start = tuple(max_contour[s][0])
            end = tuple(max_contour[e][0])
            far = tuple(max_contour[f][0])
            
            a = np.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
            b = np.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
            c = np.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)
            
            angle = np.arccos((b**2 + c**2 - a**2) / (2 * b * c + 1e-6))
            
            if angle <= np.pi / 2 and d > 15000:
                finger_count += 1

        return finger_count

    def _warm_capture(self, attempts: int = 2, delay: float = 0.5):
        """Face mai multe încercări de captură."""
        for attempt in range(attempts):
            try:
                frame = self._capture_frame_rpicam()
                if frame is not None and frame.size > 0:
                    return frame
            except subprocess.TimeoutExpired:
                if attempt == attempts - 1:
                    raise RuntimeError("Timeout la capturarea imaginii.")
                time.sleep(delay)
            except Exception as e:
                if attempt == attempts - 1:
                    raise
                time.sleep(delay)
        return None

    def play_round_two_players(self, camera_index: int = 0) -> Dict:
        """
        Joacă o rundă între 2 jucători.
        Detectează 2 mâini simultan și compară semnele.
        """
        try:
            # Capturează frame
            frame = self._warm_capture()
            if frame is None:
                raise RuntimeError("Nu am putut citi un frame de la cameră.")

            # Detectează gesturile
            if MEDIAPIPE_AVAILABLE and self.hands:
                gestures = self._detect_gesture_mediapipe(frame)
            else:
                gestures = self._detect_gesture_fallback(frame)

            # Trebuie să detectăm exact 2 mâini
            if len(gestures) < 2:
                # Dacă detectăm doar o mână, o folosim pentru ambele (test)
                if len(gestures) == 1:
                    player1_move = gestures[0][0]
                    player2_move = random.choice(self.MOVES)  # Fallback
                else:
                    player1_move = random.choice(self.MOVES)
                    player2_move = random.choice(self.MOVES)
            else:
                # Avem 2 mâini detectate
                player1_move = gestures[0][0]
                player2_move = gestures[1][0]

            # Determină câștigătorul
            result = self._winner(player1_move, player2_move)
            
            return {
                "player1_move": player1_move,
                "player2_move": player2_move,
                "result": result
            }
        except Exception as e:
            raise RuntimeError(f"Eroare cameră: {e}")

    def _winner(self, player1: str, player2: str) -> str:
        """Determină câștigătorul între 2 jucători."""
        if player1 == player2:
            return "Egal"
        if (
            (player1 == "piatră" and player2 == "foarfecă")
            or (player1 == "foarfecă" and player2 == "hârtie")
            or (player1 == "hârtie" and player2 == "piatră")
        ):
            return "player1_wins"  # Jucătorul 1 câștigă
        return "player2_wins"  # Jucătorul 2 câștigă

    # Metodă pentru compatibilitate cu codul vechi
    def play_round(self, camera_index: int = 0) -> Dict:
        """Metodă de compatibilitate - joacă între jucător și AI."""
        result = self.play_round_two_players(camera_index)
        # Convertim pentru compatibilitate
        ai_move = random.choice(self.MOVES)
        return {
            "player_move": result["player1_move"],
            "ai_move": ai_move,
            "result": self._winner(result["player1_move"], ai_move)
        }


if __name__ == "__main__":
    game = RPSCameraGame()
    print(game.play_round_two_players(camera_index=0))
