import os
import random
import webbrowser

from kivy.config import Config

# Setări de fereastră pentru kiosk (fullscreen, fără bordură)
Config.set("graphics", "fullscreen", "auto")
Config.set("graphics", "borderless", "1")
Config.set("graphics", "resizable", "0")

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen

from modules.personality_test import PersonalityTest
from modules.scientist_matcher import ScientistMatcher
from modules.rps_camera_game import RPSCameraGame


# --- Screen-uri de bază ---

class HomeScreen(Screen):
    """Ecranul principal, cu butoanele pentru toate modulele."""
    pass


class InfoScreen(Screen):
    """Ecran cu informații despre universitate și buton către site."""
    pass


class PersonalityTestScreen(Screen):
    """Ecran pentru testul de personalitate."""
    pass


class ScientistMatcherScreen(Screen):
    """Ecran pentru modulul care găsește oameni de știință care seamănă cu elevul."""
    pass


class RPSCameraGameScreen(Screen):
    """Ecran pentru jocul piatră-foarfecă-hârtie la cameră."""
    pass


class KioskApp(App):
    # True dacă a fost detectată o persoană în fața camerei
    person_present = BooleanProperty(False)

    # Proprietăți pentru testul de personalitate
    personality_question_text = StringProperty("")
    personality_options = ListProperty([])
    personality_progress = StringProperty("")
    personality_result_text = StringProperty("")

    # Proprietăți pentru scientist matcher
    scientist_status_text = StringProperty("Atinge butonul pentru a face o poză și a găsi un om de știință.")

    # Proprietăți pentru RPS
    rps_status_text = StringProperty("Atinge «Joacă o rundă» și arată un gest către cameră.")

    def build(self):
        self.title = "Universitate - Kiosk"
        kv_path = os.path.join(os.path.dirname(__file__), "kv", "main.kv")
        # Permite schimbarea camerei din variabilă de mediu (ex: CAMERA_INDEX=1)
        self.camera_index = int(os.environ.get("CAMERA_INDEX", "0"))
        self.personality_engine = PersonalityTest()
        self.scientist_matcher = ScientistMatcher()
        self.rps_game = RPSCameraGame()
        self._reset_personality_test()
        return Builder.load_file(kv_path)

    def on_start(self):
        """
        Pornește aplicația în mod kiosk fără detectare de mișcare.
        Setăm person_present=True ca să nu blocăm butoanele.
        """
        self.person_present = True

    # Detectorul este dezactivat; metodele rămân ca no-op pentru compatibilitate
    def _setup_presence_detector(self):
        self.presence_detector = None

    def _update_presence(self, dt):
        return

    # --- Info screen ---
    def open_university_website(self):
        """Deschide site-ul universității în browser."""
        # Înlocuiește cu link-ul real al universității tale
        url = "https://www.exemplu-universitate.ro"
        try:
            webbrowser.open(url)
        except Exception as exc:
            print(f"[KIOSK] Nu pot deschide browser-ul: {exc}")

    def go_home(self):
        """Revine la ecranul principal."""
        if self.root:
            self.root.current = "home"

    # --- Personalitate ---
    def _reset_personality_test(self):
        self.personality_engine.reset()
        question = self.personality_engine.current_question()
        self._apply_personality_question(question)
        self.personality_result_text = ""

    def _apply_personality_question(self, question):
        if not question:
            self.personality_question_text = "Test finalizat."
            self.personality_options = []
            self.personality_progress = ""
            return
        self.personality_question_text = question["text"]
        self.personality_options = question["options"]
        self.personality_progress = self.personality_engine.progress_label()

    def select_personality_answer(self, option_index: int):
        if not self.personality_engine.has_next():
            return
        try:
            self.personality_engine.answer(option_index)
        except Exception as exc:
            print(f"[KIOSK] Eroare la răspuns: {exc}")
            return

        if self.personality_engine.has_next():
            question = self.personality_engine.current_question()
            self._apply_personality_question(question)
        else:
            result = self.personality_engine.result()
            self.personality_result_text = (
                f"Recomandare: {result['faculty']}\\n{result['reason']}"
            )
            self.personality_question_text = "Gata! Vezi recomandarea de mai jos."
            self.personality_options = []
            self.personality_progress = ""

    # --- Scientist matcher ---
    def capture_scientist_match(self):
        self.scientist_status_text = "Capturez... te rog stai nemișcat(ă)."
        try:
            match = self.scientist_matcher.capture_and_match(camera_index=self.camera_index)
        except Exception as exc:
            self.scientist_status_text = f"Eroare cameră: {exc}"
            return

        if not match:
            self.scientist_status_text = "Nu am putut detecta o față. Încearcă din nou."
            return

        name = match.get("name", "Om de știință misterios")
        desc = match.get("description", "")
        self.scientist_status_text = f"Semeni cu {name}!\\n{desc}"

    # --- RPS ---
    def play_rps_round(self):
        self.rps_status_text = "Capturez gestul... 3, 2, 1!"
        try:
            outcome = self.rps_game.play_round(camera_index=self.camera_index)
        except Exception as exc:
            self.rps_status_text = f"Eroare cameră: {exc}"
            return

        player = outcome.get("player_move", "necunoscut")
        ai = outcome.get("ai_move", "necunoscut")
        result = outcome.get("result", "egal")
        self.rps_status_text = f"Tu: {player} | AI: {ai} -> {result}"

    def on_stop(self):
        """Oprește detectorul (nefolosit acum) la ieșirea din aplicație."""
        detector = getattr(self, "presence_detector", None)
        if detector is not None:
            try:
                detector.stop()
            except Exception as exc:
                print(f"[KIOSK] Eroare la oprirea PresenceDetector: {exc}")


if __name__ == "__main__":
    KioskApp().run()

