import os
import webbrowser

from kivy.config import Config

# Setări de fereastră pentru kiosk (fullscreen, fără bordură)
Config.set("graphics", "fullscreen", "auto")
Config.set("graphics", "borderless", "1")
Config.set("graphics", "resizable", "0")

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import BooleanProperty
from kivy.uix.screenmanager import ScreenManager, Screen


# --- Screen-uri de bază ---

class HomeScreen(Screen):
    """Ecranul principal, cu butoanele pentru toate modulele."""
    pass


class InfoScreen(Screen):
    """Ecran cu informații despre universitate și buton către site."""
    pass


class PersonalityTestScreen(Screen):
    """Ecran pentru testul de personalitate (UI-ul detaliat îl vei adăuga ulterior)."""
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

    def build(self):
        self.title = "Universitate - Kiosk"
        kv_path = os.path.join(os.path.dirname(__file__), "kv", "main.kv")
        return Builder.load_file(kv_path)

    def on_start(self):
        """Pornește detectorul de prezență (dacă modulul există)."""
        self._setup_presence_detector()

    def _setup_presence_detector(self):
        """Inițializează și pornește detectorul de prezență."""
        try:
            from modules.presence_detector import PresenceDetector
        except ImportError:
            # Aplicația merge și fără detector, dar nu va bloca butoanele.
            print(
                "[KIOSK] AVERTISMENT: modules/presence_detector.py nu a fost găsit.\n"
                "         Prezența nu va fi detectată automat."
            )
            self.presence_detector = None
            # Dacă vrei să testezi fără detector, setează person_present = True
            # self.person_present = True
            return

        # Creezi instanța (adaptează parametrii la implementarea ta reală)
        self.presence_detector = PresenceDetector(camera_index=0)

        try:
            self.presence_detector.start()
        except Exception as exc:
            print(f"[KIOSK] Eroare la pornirea PresenceDetector: {exc}")
            self.presence_detector = None
            return

        # Interoghează periodic detectorul
        Clock.schedule_interval(self._update_presence, 0.5)

    def _update_presence(self, dt):
        """Actualizează proprietatea person_present pe baza detectorului."""
        if not getattr(self, "presence_detector", None):
            return

        try:
            present = self.presence_detector.is_person_present()
            self.person_present = bool(present)
        except Exception as exc:
            print(f"[KIOSK] Eroare în is_person_present(): {exc}")

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

    def on_stop(self):
        """Oprește detectorul de prezență la ieșirea din aplicație."""
        detector = getattr(self, "presence_detector", None)
        if detector is not None:
            try:
                detector.stop()
            except Exception as exc:
                print(f"[KIOSK] Eroare la oprirea PresenceDetector: {exc}")


if __name__ == "__main__":
    KioskApp().run()

