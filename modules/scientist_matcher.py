import os
import random
import time
import subprocess
import tempfile
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

import cv2
import numpy as np


@dataclass
class Scientist:
    name: str
    description: str
    image_path: Optional[str] = None


class ScientistMatcher:
    """
    Captură un frame folosind rpicam-hello, detectează fața, adaugă cască de muncitor
    și salvează poza editată.
    """

    def __init__(self, scientists: Optional[List[Scientist]] = None):
        self.scientists = scientists or self._default_scientists()
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        # Director pentru pozele salvate
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output_photos")
        os.makedirs(self.output_dir, exist_ok=True)

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

    def _create_helmet_mask(self, width: int, height: int) -> np.ndarray:
        """Creează o mască pentru cască de muncitor (galbenă cu bandă reflectantă)."""
        mask = np.zeros((height, width, 3), dtype=np.uint8)  # BGR
        
        # Casca principală (galben - BGR format)
        cv2.ellipse(mask, (width // 2, height // 2), (width // 2, height // 2), 0, 0, 360, (0, 200, 255), -1)
        
        # Banda reflectantă (portocaliu)
        cv2.ellipse(mask, (width // 2, height // 3), (width // 2, height // 6), 0, 0, 360, (0, 100, 255), -1)
        
        # Detalii (linii)
        cv2.line(mask, (width // 4, height // 2), (3 * width // 4, height // 2), (0, 150, 255), 2)
        
        # Highlight pentru efect 3D
        cv2.ellipse(mask, (width // 2, height // 3), (width // 3, height // 4), 0, 0, 180, (255, 255, 255), -1)
        
        return mask

    def _add_helmet_to_face(self, frame: np.ndarray, face: tuple) -> np.ndarray:
        """
        Adaugă o cască de muncitor pe capul detectat.
        face = (x, y, w, h) - coordonatele feței
        """
        x, y, w, h = face
        frame_copy = frame.copy()
        
        # Dimensiuni pentru cască (mai mare decât fața)
        helmet_width = int(w * 1.5)
        helmet_height = int(h * 1.3)
        
        # Poziție cască (centrată pe față, puțin mai sus)
        helmet_x = x - int((helmet_width - w) / 2)
        helmet_y = y - int(h * 0.4)
        
        # Asigură-te că casca nu iese din cadru
        helmet_x = max(0, min(helmet_x, frame.shape[1] - helmet_width))
        helmet_y = max(0, min(helmet_y, frame.shape[0] - helmet_height))
        
        # Ajustează dimensiunile dacă ies din cadru
        actual_width = min(helmet_width, frame.shape[1] - helmet_x)
        actual_height = min(helmet_height, frame.shape[0] - helmet_y)
        
        # Creează casca
        helmet_mask = self._create_helmet_mask(actual_width, actual_height)
        
        # Extrage regiunea unde va fi casca
        roi = frame_copy[helmet_y:helmet_y + actual_height, helmet_x:helmet_x + actual_width]
        
        if roi.shape[0] > 0 and roi.shape[1] > 0 and helmet_mask.shape[0] > 0 and helmet_mask.shape[1] > 0:
            # Aplică casca cu blending (70% casca, 30% imaginea originală)
            alpha = 0.7
            roi[:] = cv2.addWeighted(roi, 1 - alpha, helmet_mask, alpha, 0)
        
        return frame_copy

    def _capture_frame_rpicam(self, output_path: Optional[str] = None) -> Optional[np.ndarray]:
        """
        Capturează un frame folosind rpicam-hello cu timeout scurt.
        Returnează imaginea ca numpy array (BGR pentru OpenCV).
        
        Args:
            output_path: Dacă este specificat, salvează direct la acest path (pentru feed live).
                        Dacă este None, creează un fișier temporar care va fi șters.
        """
        # Dacă nu este specificat un output_path, creează un fișier temporar
        if output_path is None:
            temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            should_delete = True
        else:
            temp_path = output_path
            should_delete = False
        
        try:
            # Rulează rpicam-hello cu timeout de 1 secundă pentru captură rapidă
            # Folosim --timeout 1000 (milisecunde) în loc de 0
            cmd = [
                "rpicam-hello",
                "--timeout", "1000",  # 1 secundă în loc de 0
                "--output", temp_path,
                "--width", "640",
                "--height", "480"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3  # Timeout mai scurt pentru subprocess
            )
            
            if result.returncode != 0:
                # Dacă eșuează, încearcă cu rpicam-vid pentru o captură mai rapidă
                try:
                    cmd_vid = [
                        "rpicam-vid",
                        "--frames", "1",
                        "--output", temp_path,
                        "--width", "640",
                        "--height", "480"
                    ]
                    result = subprocess.run(
                        cmd_vid,
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    if result.returncode != 0:
                        return None
                except FileNotFoundError:
                    return None
            
            # Citește imaginea capturată
            if not os.path.exists(temp_path):
                return None
            
            frame = cv2.imread(temp_path)
            if frame is None:
                return None
            
            return frame
            
        except subprocess.TimeoutExpired:
            # Dacă timeout, returnează None în loc să arunce eroare
            return None
        except Exception as e:
            # Pentru feed live, nu aruncăm eroare, doar returnăm None
            return None
        finally:
            # Șterge fișierul temporar doar dacă nu este pentru feed live
            if should_delete and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass

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

    def capture_and_match(self, camera_index: int = 0) -> Optional[Dict]:
        """
        Capturează o imagine folosind rpicam-hello, detectează fața, adaugă cască
        și salvează poza editată.
        """
        try:
            # Capturează frame folosind rpicam-hello
            frame = self._warm_capture()
            if frame is None:
                raise RuntimeError("Nu am putut citi un frame de la cameră.")

            faces = self._detect_face(frame)
            if len(faces) == 0:
                return None

            # Adaugă casca pe prima față detectată
            edited_frame = frame.copy()
            if len(faces) > 0:
                # Folosește cea mai mare față detectată
                largest_face = max(faces, key=lambda f: f[2] * f[3])
                edited_frame = self._add_helmet_to_face(edited_frame, largest_face)

            # Salvează poza editată
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scientist_photo_{timestamp}.jpg"
            output_path = os.path.join(self.output_dir, filename)
            cv2.imwrite(output_path, edited_frame)

            # Alege un om de știință random
            scientist = random.choice(self.scientists)
            return {
                "name": scientist.name,
                "description": scientist.description,
                "image_path": scientist.image_path,
                "faces_detected": len(faces),
                "edited_photo_path": output_path,
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Eroare la rularea rpicam-hello: {e}")
        except FileNotFoundError:
            raise RuntimeError("rpicam-hello nu este instalat sau nu este în PATH.")
        except Exception as e:
            raise RuntimeError(f"Eroare cameră: {e}")


if __name__ == "__main__":
    matcher = ScientistMatcher()
    result = matcher.capture_and_match(camera_index=0)
    print(result)
