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
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from modules.personality_test import PersonalityTest
from modules.scientist_matcher import ScientistMatcher
from modules.rps_camera_game import RPSCameraGame
from modules.maze_game import MazeGame
from modules.circuit_game import CircuitGame
from modules.circuit_canvas import CircuitCanvas


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


class MazeGameScreen(Screen):
    """Ecran pentru jocul de labirint controlat prin touchscreen."""
    pass


class CircuitGameScreen(Screen):
    """Ecran pentru jocul „Circuitul Magic”."""
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
    scientist_photo_path = StringProperty("")

    # Proprietăți pentru RPS
    rps_status_text = StringProperty("Atinge «Joacă o rundă» și arată un gest către cameră.")
    rps_timer_text = StringProperty("")

    # Proprietăți pentru Labirint
    maze_display_text = StringProperty("")
    maze_status_text = StringProperty("Găsește ieșirea!")
    maze_grid = ListProperty([])

    # Proprietăți pentru Circuit
    circuit_board_text = StringProperty("")
    circuit_status_text = StringProperty("Plasează firele și pornește întrerupătorul.")

    def build(self):
        self.title = "Universitatea Dunărea de Jos Galați"
        kv_path = os.path.join(os.path.dirname(__file__), "kv", "main.kv")
        # Permite schimbarea camerei din variabilă de mediu (ex: CAMERA_INDEX=1)
        self.camera_index = int(os.environ.get("CAMERA_INDEX", "0"))
        self.personality_engine = PersonalityTest()
        self.scientist_matcher = ScientistMatcher()
        self.rps_game = RPSCameraGame()
        self.maze_game = MazeGame()
        self.circuit_game = CircuitGame()
        self._reset_personality_test()
        self._reset_maze()
        self._reset_circuit()
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
        url = "https://www.ugal.ro/"
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
            self._show_personality_popup(result)

    # --- Scientist matcher ---
    def capture_scientist_match(self):
        self.scientist_status_text = "Capturez... te rog stai nemișcat(ă)."
        self.scientist_photo_path = ""
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
        photo_path = match.get("edited_photo_path", "")
        
        self.scientist_photo_path = photo_path
        self.scientist_status_text = f"Semeni cu {name}!\\n{desc}\\n\\nPoza ta cu casca este gata! Poți o descărca mai jos."

    def download_scientist_photo(self):
        """Deschide poza în aplicația default sau copiază în clipboard."""
        if not self.scientist_photo_path or not os.path.exists(self.scientist_photo_path):
            self.scientist_status_text = "Nu există poză de descărcat. Fă mai întâi o poză."
            return
        
        try:
            # Deschide poza cu aplicația default
            webbrowser.open(f"file://{os.path.abspath(self.scientist_photo_path)}")
            self.scientist_status_text = f"Poza a fost deschisă!\\nCalea: {self.scientist_photo_path}"
        except Exception as exc:
            self.scientist_status_text = f"Eroare la deschiderea pozei: {exc}"

    # --- RPS ---
    def play_rps_round(self):
        """Joacă o rundă cu timer de 3 secunde și mesaje personalizate."""
        self.rps_status_text = "Pregătește-te! Timer-ul începe..."
        self.rps_timer_text = "3"
        
        # Timer de 3 secunde cu countdown
        def update_timer(dt):
            timer_value = int(self.rps_timer_text)
            if timer_value > 1:
                self.rps_timer_text = str(timer_value - 1)
                self.rps_status_text = f"Pregătește-te! {timer_value - 1}..."
            else:
                self.rps_timer_text = "0"
                self.rps_status_text = "Capturez gestul... Arată semnul!"
                Clock.schedule_once(self._capture_rps_move, 0.5)
        
        # Anulează orice timer anterior
        if hasattr(self, '_rps_timer'):
            self._rps_timer.cancel()
        
        # Pornește timer-ul
        self._rps_timer = Clock.schedule_interval(update_timer, 1.0)
        Clock.schedule_once(lambda dt: self._rps_timer.cancel(), 3.5)
    
    def _capture_rps_move(self, dt):
        """Capturează mutarea după timer."""
        try:
            outcome = self.rps_game.play_round(camera_index=self.camera_index)
        except Exception as exc:
            self.rps_status_text = f"Eroare cameră: {exc}"
            self.rps_timer_text = ""
            return

        player = outcome.get("player_move", "necunoscut")
        ai = outcome.get("ai_move", "necunoscut")
        result = outcome.get("result", "egal")
        
        # Mesaje personalizate
        if result == "player_wins":
            self.rps_status_text = f"Felicitări, ești mai bun decât un Intel i5!\\n\\nTu: {player} | AI: {ai}"
        elif result == "ai_wins":
            self.rps_status_text = f"Haha, până și un Pentium e mai bun ca tine!\\n\\nTu: {player} | AI: {ai}"
        else:
            self.rps_status_text = f"Egal!\\n\\nTu: {player} | AI: {ai}"
        
        self.rps_timer_text = ""

    # --- Labirint ---
    def _reset_maze(self):
        self.maze_game.reset()
        self.maze_display_text = self.maze_game.render()
        self.maze_grid = [row[:] for row in self.maze_game.grid]
        self.maze_status_text = "Găsește ieșirea!"

    def move_maze(self, direction: str):
        status = self.maze_game.move(direction)
        self.maze_display_text = self.maze_game.render()
        self.maze_grid = [row[:] for row in self.maze_game.grid]
        if status == "win":
            self.maze_status_text = "Bravo! Ai găsit ieșirea. Apasă «Repornește»."
            self._show_maze_win_popup()
        elif status == "block":
            self.maze_status_text = "Perete! Încearcă altă direcție."
        else:
            self.maze_status_text = "Găsește ieșirea!"

    def _show_maze_win_popup(self):
        content = BoxLayout(orientation="vertical", padding=16, spacing=12)
        message = Label(
            text="Felicitări! Ai găsit ieșirea din labirint!",
            font_size="24sp",
            bold=True,
            halign="center",
            valign="middle",
            text_size=(400, None),
        )
        ok_btn = Button(
            text="OK",
            size_hint_y=None,
            height=48,
        )
        content.add_widget(message)
        content.add_widget(ok_btn)
        popup = Popup(
            title="Ai câștigat!",
            content=content,
            size_hint=(0.65, 0.45),
            auto_dismiss=True,
        )
        ok_btn.bind(on_press=popup.dismiss)
        popup.open()

    # --- Popup Personalitate ---
    def _show_personality_popup(self, result: dict):
        faculty = result.get("faculty", "Facultate")
        reason = result.get("reason", "")
        # Mesaje fără emoji (pentru fonturi care nu afișează corect)
        messages = [
            "Bravo!",
            "Felicitări!",
            "Super alegere!",
            "Excelent!",
            "Wow, bine făcut!",
        ]
        btn_text = random.choice(messages)

        content = BoxLayout(orientation="vertical", padding=16, spacing=12)
        msg = Label(
            text=f"{btn_text}\n\nRecomandare: {faculty}\n{reason}",
            font_size="26sp",
            bold=True,
            halign="center",
            valign="middle",
            text_size=(420, None),
        )
        ok_btn = Button(
            text=btn_text,
            size_hint_y=None,
            height=56,
            font_size="20sp",
            bold=True,
        )
        content.add_widget(msg)
        content.add_widget(ok_btn)
        popup = Popup(
            title="Rezultatul tău",
            content=content,
            size_hint=(0.7, 0.5),
            auto_dismiss=True,
        )
        ok_btn.bind(on_press=popup.dismiss)
        popup.open()

    # --- Circuit Magic ---
    def _reset_circuit(self):
        self.circuit_status_text = "Trage cu degetul de la terminalele componentei pentru a conecta firele. Apoi apasă pe întrerupător."
        canvas = None
        if self.root:
            try:
                screen = self.root.get_screen("circuit")
                canvas = screen.ids.get("circuit_canvas")
            except Exception:
                canvas = None
        if canvas:
            canvas.reset_components()
            canvas.clear_lines()

    def circuit_toggle_switch(self):
        """Comută primul întrerupător."""
        canvas = None
        if self.root:
            try:
                screen = self.root.get_screen("circuit")
                canvas = screen.ids.get("circuit_canvas")
            except Exception:
                canvas = None
        
        if canvas:
            canvas.toggle_switch()
            if canvas.bulb_lit or canvas.bulb2_lit:
                self.circuit_status_text = "Circuit complet! Becul s-a aprins!"
            else:
                self.circuit_status_text = "Conectează toate firele și pornește întrerupătoarele."
    
    def circuit_toggle_switch2(self):
        """Comută al doilea întrerupător."""
        canvas = None
        if self.root:
            try:
                screen = self.root.get_screen("circuit")
                canvas = screen.ids.get("circuit_canvas")
            except Exception:
                canvas = None
        
        if canvas:
            canvas.toggle_switch2()
            if canvas.bulb_lit or canvas.bulb2_lit:
                self.circuit_status_text = "Circuit complet! Becul s-a aprins!"
            else:
                self.circuit_status_text = "Conectează toate firele și pornește întrerupătoarele."

    def on_circuit_complete(self):
        """Callback când circuitul este complet."""
        self.circuit_status_text = "Felicitări! Circuitul funcționează perfect!"
    
    def on_circuit_explosion(self):
        """Callback când circuitul are conexiuni greșite."""
        self.circuit_status_text = "AI LUAT FOC! Conexiunile sunt greșite!"
        self._show_circuit_win_popup()

    def _show_circuit_win_popup(self):
        """Afișează popup cu felicitări când circuitul este complet."""
        content = BoxLayout(orientation="vertical", padding=16, spacing=12)
        message = Label(
            text="Felicitări! Ai conectat corect circuitul!\n\nBecul s-a aprins și circuitul funcționează perfect!",
            font_size="24sp",
            bold=True,
            halign="center",
            valign="middle",
            text_size=(400, None),
        )
        ok_btn = Button(
            text="Excelent!",
            size_hint_y=None,
            height=48,
        )
        content.add_widget(message)
        content.add_widget(ok_btn)
        popup = Popup(
            title="Circuit complet!",
            content=content,
            size_hint=(0.7, 0.5),
            auto_dismiss=True,
        )
        ok_btn.bind(on_press=popup.dismiss)
        popup.open()

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

