import os
import random
import webbrowser
import tempfile
import cv2

from kivy.config import Config

# Setări de fereastră pentru kiosk (fullscreen, fără bordură)
Config.set("graphics", "fullscreen", "auto")
Config.set("graphics", "borderless", "1")
Config.set("graphics", "resizable", "0")

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.animation import Animation
from pathlib import Path
import re

from modules.personality_test import PersonalityTest
from modules.scientist_matcher import ScientistMatcher
from modules.rps_camera_game import RPSCameraGame
from modules.maze_game import MazeGame
from modules.circuit_game import CircuitGame
from modules.circuit_canvas import CircuitCanvas


# --- Screen-uri de bază ---

class ScreensaverScreen(Screen):
    """Ecran de screensaver cu prezentarea."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_paths = []
        self.current_image_index = 0
        self.slide_timer = None
        self._touch_start = None
        self._load_images()
    
    def _load_images(self):
        """Încarcă imaginile din folderul prezentare și le sortează după număr."""
        prezentare_dir = Path("assets/images/prezentare")
        if prezentare_dir.exists():
            # Colectează toate imaginile
            all_images = list(prezentare_dir.glob("*.png"))
            all_images.extend(prezentare_dir.glob("*.jpg"))
            all_images.extend(prezentare_dir.glob("*.jpeg"))
            
            # Sortează după numărul din numele fișierului
            def extract_number(path):
                """Extrage numărul din numele fișierului."""
                match = re.search(r'(\d+)', path.name)
                if match:
                    return int(match.group(1))
                return 0
            
            self.image_paths = sorted(all_images, key=extract_number)
    
    def on_enter(self):
        """Când intră pe ecran, pornește slideshow-ul."""
        if self.image_paths:
            # Așteaptă puțin pentru ca widget-ul să fie complet inițializat
            Clock.schedule_once(lambda dt: self._show_current_image(fade_in=False), 0.1)
            # Schimbă imaginea la fiecare 9 secunde (5 + 4)
            self.slide_timer = Clock.schedule_interval(self._next_image, 9.0)
    
    def on_leave(self):
        """Când părăsește ecranul, oprește timer-ul."""
        if self.slide_timer:
            self.slide_timer.cancel()
            self.slide_timer = None
    
    def _show_current_image(self, fade_in=True):
        """Afișează imaginea curentă cu efect de fade."""
        if not self.image_paths:
            return
        
        image_path = self.image_paths[self.current_image_index]
        # Actualizează imaginea în widget
        if hasattr(self, 'ids') and 'screensaver_image' in self.ids:
            img_widget = self.ids.screensaver_image
            
            if fade_in:
                # Efect de fade: opacitate de la 0 la 1
                img_widget.opacity = 0
                img_widget.source = str(image_path)
                # Forțează reîncărcarea
                try:
                    img_widget.reload()
                except:
                    pass
                
                # Animație fade in
                anim = Animation(opacity=1, duration=1.0)
                anim.start(img_widget)
            else:
                # Fără fade pentru prima imagine - asigură-te că se vede
                img_widget.source = str(image_path)
                img_widget.opacity = 1
                # Forțează reîncărcarea
                try:
                    img_widget.reload()
                except:
                    pass
                # Așteaptă puțin și verifică din nou
                Clock.schedule_once(lambda dt: self._ensure_image_visible(), 0.2)
    
    def _ensure_image_visible(self):
        """Asigură-te că imaginea este vizibilă."""
        if hasattr(self, 'ids') and 'screensaver_image' in self.ids:
            img_widget = self.ids.screensaver_image
            if img_widget.opacity < 1:
                img_widget.opacity = 1
            if not img_widget.source:
                # Reîncarcă dacă sursa lipsește
                if self.image_paths:
                    img_widget.source = str(self.image_paths[self.current_image_index])
                    try:
                        img_widget.reload()
                    except:
                        pass
    
    def _next_image(self, dt):
        """Trece la următoarea imagine cu efect de fade."""
        if not self.image_paths:
            return
        
        # Fade out imaginea curentă
        if hasattr(self, 'ids') and 'screensaver_image' in self.ids:
            img_widget = self.ids.screensaver_image
            anim_out = Animation(opacity=0, duration=0.5)
            
            def on_complete(anim, widget):
                # După fade out, schimbă imaginea și face fade in
                self.current_image_index = (self.current_image_index + 1) % len(self.image_paths)
                self._show_current_image(fade_in=True)
            
            anim_out.bind(on_complete=on_complete)
            anim_out.start(img_widget)
    
    def on_touch_down(self, touch):
        """Detectează începutul unui swipe sau click."""
        if self.collide_point(*touch.pos):
            self._touch_start = touch.pos
            return True
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        """Detectează mișcarea pentru swipe."""
        if self._touch_start is None:
            return super().on_touch_move(touch)
        return True
    
    def on_touch_up(self, touch):
        """Detectează finalul swipe-ului sau click-ul."""
        if self._touch_start is None:
            return super().on_touch_up(touch)
        
        if not self.collide_point(*touch.pos):
            self._touch_start = None
            return super().on_touch_up(touch)
        
        # Calculează distanța și direcția swipe-ului
        dx = touch.x - self._touch_start[0]
        dy = touch.y - self._touch_start[1]
        
        # Threshold pentru a distinge între swipe și click
        swipe_threshold = 50
        
        if abs(dx) > swipe_threshold or abs(dy) > swipe_threshold:
            # Este un swipe
            if abs(dx) > abs(dy):
                # Swipe orizontal
                if dx > 0:
                    # Swipe la dreapta - imaginea anterioară
                    self._previous_image()
                else:
                    # Swipe la stânga - imaginea următoare
                    self._next_image_manual()
            # Dacă e swipe vertical, nu facem nimic (sau poți adăuga funcționalitate)
        else:
            # Este un click - trece la ecranul principal
            app = App.get_running_app()
            if app and app.root:
                app.root.current = "home"
        
        self._touch_start = None
        return True
    
    def _previous_image(self):
        """Trece la imaginea anterioară."""
        if not self.image_paths:
            return
        
        # Oprește timer-ul temporar
        if self.slide_timer:
            self.slide_timer.cancel()
        
        # Fade out imaginea curentă
        if hasattr(self, 'ids') and 'screensaver_image' in self.ids:
            img_widget = self.ids.screensaver_image
            anim_out = Animation(opacity=0, duration=0.5)
            
            def on_complete(anim, widget):
                # După fade out, schimbă la imaginea anterioară
                self.current_image_index = (self.current_image_index - 1) % len(self.image_paths)
                self._show_current_image(fade_in=True)
                # Repornește timer-ul
                if self.image_paths:
                    self.slide_timer = Clock.schedule_interval(self._next_image, 9.0)
            
            anim_out.bind(on_complete=on_complete)
            anim_out.start(img_widget)
    
    def _next_image_manual(self):
        """Trece manual la imaginea următoare (folosit pentru swipe)."""
        if not self.image_paths:
            return
        
        # Oprește timer-ul temporar
        if self.slide_timer:
            self.slide_timer.cancel()
        
        # Fade out imaginea curentă
        if hasattr(self, 'ids') and 'screensaver_image' in self.ids:
            img_widget = self.ids.screensaver_image
            anim_out = Animation(opacity=0, duration=0.5)
            
            def on_complete(anim, widget):
                # După fade out, schimbă la imaginea următoare
                self.current_image_index = (self.current_image_index + 1) % len(self.image_paths)
                self._show_current_image(fade_in=True)
                # Repornește timer-ul
                if self.image_paths:
                    self.slide_timer = Clock.schedule_interval(self._next_image, 9.0)
            
            anim_out.bind(on_complete=on_complete)
            anim_out.start(img_widget)

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
    
    def on_enter(self):
        """Pornește feed-ul camerei când se intră pe ecran."""
        app = App.get_running_app()
        if app:
            app._start_scientist_camera_feed()
    
    def on_leave(self):
        """Oprește feed-ul camerei când se părăsește ecranul."""
        app = App.get_running_app()
        if app:
            app._stop_scientist_camera_feed()


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
    scientist_camera_feed = StringProperty("")  # Calea către feed-ul live al camerei

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
    
    def _start_scientist_camera_feed(self):
        """Pornește feed-ul live al camerei pentru ecranul scientist într-un popup."""
        if hasattr(self, '_scientist_camera_popup') and self._scientist_camera_popup:
            return  # Deja pornit
        
        # Creează un fișier temporar pentru feed
        self._scientist_camera_temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        self._scientist_camera_temp_path = self._scientist_camera_temp_file.name
        self._scientist_camera_temp_file.close()
        
        # Face o captură inițială pentru a avea ceva de afișat
        try:
            initial_frame = self.scientist_matcher._capture_frame_rpicam()
            if initial_frame is not None:
                cv2.imwrite(self._scientist_camera_temp_path, initial_frame)
        except:
            pass
        
        self.scientist_camera_feed = self._scientist_camera_temp_path
        
        # Creează popup-ul cu feed-ul camerei
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        
        # Imaginea feed-ului camerei
        camera_image = Image(
            source=self._scientist_camera_temp_path,
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(1, 0.9)
        )
        content.add_widget(camera_image)
        
        # Buton de închidere
        close_btn = Button(
            text="Închide camera",
            size_hint_y=None,
            height=48,
            font_size="18sp"
        )
        content.add_widget(close_btn)
        
        # Creează popup-ul
        popup = Popup(
            title="Camera live",
            content=content,
            size_hint=(0.7, 0.6),
            auto_dismiss=False,
        )
        
        # Funcție pentru a închide popup-ul și a opri feed-ul
        def close_camera_feed(instance):
            popup.dismiss()
            self._stop_scientist_camera_feed()
        
        # Butonul de închidere închide popup-ul și oprește feed-ul
        close_btn.bind(on_press=close_camera_feed)
        
        # Când popup-ul este închis, oprește feed-ul
        popup.bind(on_dismiss=lambda instance: self._stop_scientist_camera_feed())
        
        # Salvează referințele
        self._scientist_camera_popup = popup
        self._scientist_camera_image = camera_image
        
        # Deschide popup-ul
        popup.open()
        
        # Face o captură inițială după ce popup-ul este deschis
        Clock.schedule_once(lambda dt: self._update_scientist_camera_feed(0), 0.2)
        
        # Pornește actualizarea feed-ului
        self._scientist_camera_timer = Clock.schedule_interval(self._update_scientist_camera_feed, 0.1)  # 10 FPS
    
    def _stop_scientist_camera_feed(self):
        """Oprește feed-ul live al camerei și închide popup-ul."""
        # Oprește timer-ul
        if hasattr(self, '_scientist_camera_timer') and self._scientist_camera_timer:
            self._scientist_camera_timer.cancel()
            self._scientist_camera_timer = None
        
        # Închide popup-ul
        if hasattr(self, '_scientist_camera_popup') and self._scientist_camera_popup:
            try:
                self._scientist_camera_popup.dismiss()
            except:
                pass
            self._scientist_camera_popup = None
        
        # Șterge referințele
        if hasattr(self, '_scientist_camera_image'):
            self._scientist_camera_image = None
        
        # Șterge fișierul temporar
        if hasattr(self, '_scientist_camera_temp_path') and os.path.exists(self._scientist_camera_temp_path):
            try:
                os.unlink(self._scientist_camera_temp_path)
            except:
                pass
        
        self.scientist_camera_feed = ""
    
    def _update_scientist_camera_feed(self, dt):
        """Actualizează feed-ul camerei capturând un nou frame."""
        try:
            # Verifică dacă popup-ul este încă deschis
            if not hasattr(self, '_scientist_camera_popup') or not self._scientist_camera_popup:
                return
            
            if not hasattr(self, '_scientist_camera_image') or not self._scientist_camera_image:
                return
            
            frame = self.scientist_matcher._capture_frame_rpicam()
            if frame is not None and hasattr(self, '_scientist_camera_temp_path'):
                # Salvează frame-ul ca imagine
                cv2.imwrite(self._scientist_camera_temp_path, frame)
                # Actualizează imaginea în popup folosind un timestamp pentru a forța reîncărcarea
                import time
                timestamp = int(time.time() * 1000)  # Milisecunde pentru timestamp unic
                # Setează sursa cu timestamp pentru a forța reîncărcarea
                self._scientist_camera_image.source = f"{self._scientist_camera_temp_path}?t={timestamp}"
                # Forțează reîncărcarea
                try:
                    self._scientist_camera_image.reload()
                except:
                    # Dacă reload nu funcționează, setează din nou sursa fără timestamp
                    self._scientist_camera_image.source = self._scientist_camera_temp_path
        except Exception as e:
            # Ignoră erorile pentru a nu întrerupe feed-ul
            pass

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
        """Capturează mutarea după timer pentru 2 jucători."""
        try:
            outcome = self.rps_game.play_round_two_players(camera_index=self.camera_index)
        except Exception as exc:
            self.rps_status_text = f"Eroare cameră: {exc}"
            self.rps_timer_text = ""
            return

        player1 = outcome.get("player1_move", "necunoscut")
        player2 = outcome.get("player2_move", "necunoscut")
        result = outcome.get("result", "egal")
        
        # Mesaje personalizate pentru 2 jucători
        if result == "player1_wins":
            self.rps_status_text = f"Felicitări, ești mai bun decât un Intel i5!\\n\\nJucător 1: {player1} | Jucător 2: {player2}\\nJucătorul 1 câștigă!"
        elif result == "player2_wins":
            self.rps_status_text = f"Haha, până și un Pentium e mai bun ca tine!\\n\\nJucător 1: {player1} | Jucător 2: {player2}\\nJucătorul 2 câștigă!"
        else:
            self.rps_status_text = f"Egal!\\n\\nJucător 1: {player1} | Jucător 2: {player2}"
        
        self.rps_timer_text = ""

    # --- Labirint ---
    def _reset_maze(self):
        self.maze_game.reset()
        self.maze_display_text = self.maze_game.render()
        self.maze_grid = [row[:] for row in self.maze_game.grid]
        self.maze_status_text = "Găsește ieșirea!"

    def move_maze(self, direction: str, cells: int = 1):
        """
        Mișcă creierul în labirint.
        Dacă glisarea este mai lungă, se mișcă mai multe celule.
        """
        # Încearcă să se miște de câte ori este necesar (până la numărul de celule)
        for _ in range(cells):
            status = self.maze_game.move(direction)
            self.maze_display_text = self.maze_game.render()
            self.maze_grid = [row[:] for row in self.maze_game.grid]
            
            if status == "win":
                self.maze_status_text = "Bravo! Ai găsit ieșirea. Apasă «Repornește»."
                self._show_maze_win_popup()
                break  # Oprește mișcarea dacă a câștigat
            elif status == "block":
                self.maze_status_text = "Perete! Încearcă altă direcție."
                self._show_maze_wall_popup()
                break  # Oprește mișcarea dacă s-a lovit de perete
            else:
                self.maze_status_text = "Găsește ieșirea!"

    def _show_maze_win_popup(self):
        # Listă de curiozități despre lume
        curiosities = [
            "Știai că o meduză este compusă din 95% apă?",
            "Știai că melcii pot dormi până la 3 ani consecutiv?",
            "Știai că inima unei balene albastre este atât de mare încât un om ar putea înota prin arterele sale?",
            "Știai că există mai multe stele în univers decât granule de nisip pe toate plajele Pământului?",
            "Știai că bananele sunt în realitate bace și nu fructe?",
            "Știai că un fulg de zăpadă poate avea până la 200 de fețe diferite?",
            "Știai că păianjenii pot mânca mai mult decât toate oamenii de pe Pământ combinat?",
            "Știai că există mai multe tipuri de bacterii în corpul tău decât celule umane?",
            "Știai că un cub de gheață de 1 metru cub cântărește aproape o tonă?",
            "Știai că lumina de la Soare călătorește 8 minute până la Pământ?",
            "Știai că există mai multe combinații posibile de șah decât atomi în universul observabil?",
            "Știai că o albină trebuie să viziteze 2 milioane de flori pentru a produce 500g de miere?",
            "Știai că un crocodil nu poate scoate limba din gură?",
            "Știai că există mai mult aur în oceane decât a fost extras vreodată de pe uscat?",
            "Știai că un păianjen poate trăi până la 2 ani fără mâncare?",
            "Știai că oamenii au mai multe bacterii în gură decât oameni pe Pământ?",
            "Știai că un fulger este de 5 ori mai fierbinte decât suprafața Soarelui?",
            "Știai că există mai multe copaci pe Pământ decât stele în galaxia noastră?",
            "Știai că o meduză nu are creier, inimă sau oase?",
        ]
        
        # Alege o curiozitate random
        curiosity = random.choice(curiosities)
        
        content = BoxLayout(orientation="vertical", padding=16, spacing=12)
        message = Label(
            text=curiosity,
            font_size="22sp",
            bold=True,
            halign="center",
            valign="middle",
            text_size=(450, None),
        )
        ok_btn = Button(
            text="OK",
            size_hint_y=None,
            height=48,
        )
        content.add_widget(message)
        content.add_widget(ok_btn)
        popup = Popup(
            title="Curiozitate despre lume",
            content=content,
            size_hint=(0.7, 0.5),
            auto_dismiss=True,
        )
        ok_btn.bind(on_press=popup.dismiss)
        popup.open()

    def _show_maze_wall_popup(self):
        """Afișează popup cu imaginea lui Einstein când jucătorul se lovește de perete."""
        content = BoxLayout(orientation="vertical", padding=16, spacing=12)
        
        # Imaginea lui Einstein
        einstein_img = Image(
            source='assets/images/Albert_Einstein_sticks_his_tongue.jpg',
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(1, 0.8)
        )
        content.add_widget(einstein_img)
        
        popup = Popup(
            title="",
            content=content,
            size_hint=(0.6, 0.6),
            auto_dismiss=True,
        )
        popup.open()
        
        # Închide popup-ul automat după 1 secundă
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.0)

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
            # Nu afișa mesaje de felicitări dacă există explozie
            if canvas.explosion_active:
                self.circuit_status_text = "AI LUAT FOC! Conexiunile sunt greșite!"
            elif canvas.bulb_lit:
                self.circuit_status_text = "Circuit complet! Becul s-a aprins!"
            else:
                self.circuit_status_text = "Conectează toate firele și pornește întrerupătorul."

    def on_circuit_complete(self):
        """Callback când circuitul este complet."""
        # Verifică dacă nu există explozie înainte de a afișa mesajul de felicitări
        canvas = None
        if self.root:
            try:
                screen = self.root.get_screen("circuit")
                canvas = screen.ids.get("circuit_canvas")
            except Exception:
                canvas = None
        
        if canvas and not canvas.explosion_active:
            self.circuit_status_text = "Felicitări! Circuitul funcționează perfect!"
    
    def on_circuit_explosion(self):
        """Callback când circuitul are conexiuni greșite."""
        self.circuit_status_text = "AI LUAT FOC! Conexiunile sunt greșite!"
        # Nu afișa popup-ul de felicitări la explozie

    def _show_circuit_win_popup(self):
        """Afișează popup cu felicitări când circuitul este complet."""
        # Verifică dacă există explozie înainte de a afișa popup-ul
        canvas = None
        if self.root:
            try:
                screen = self.root.get_screen("circuit")
                canvas = screen.ids.get("circuit_canvas")
            except Exception:
                canvas = None
        
        if canvas and canvas.explosion_active:
            # Nu afișa popup dacă există explozie
            return
        
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

