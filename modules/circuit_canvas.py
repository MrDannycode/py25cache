import math
from typing import List, Tuple, Optional, Dict

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.app import App


class CircuitCanvas(Widget):
    """
    Canvas simplu și intuitiv pentru touchscreen: baterie, întrerupător, bec.
    Componente mari, poziționate bine, ușor de atins cu imagini clare.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connections: List[Dict] = []
        self._current_line = None
        self._touch_start = None
        self._start_terminal = None
        self.bulb_lit = False
        self.switch_on = False
        self.bind(size=self._setup_components)
        Clock.schedule_once(lambda dt: self._setup_components(), 0.1)

    def _setup_components(self, *args):
        """Configurează componentele la poziții fixe, mari și centrate."""
        if not self.width or not self.height:
            return
        
        w, h = self.width, self.height
        # Componente mult mai mari pentru touchscreen
        comp_size = min(w, h) * 0.4
        
        # Poziții fixe, mutate foarte sus pentru display touch de 7 inchi
        # Bateria rotită la 90 de grade, întrerupătorul puțin mai jos
        self.battery_pos = (w * 0.15, h * 0.9)
        self.switch_pos = (w * 0.5, h * 0.85)  # Mutat mai jos pentru a evita suprapunerea
        self.bulb_pos = (w * 0.85, h * 0.9)
        self.comp_size = comp_size
        
        # Terminale mari pentru conexiuni (zone de touch mari)
        # Bateria rotită la 90 de grade: terminal pozitiv sus, negativ jos
        terminal_size = comp_size * 0.3
        self.terminals = {
            "battery_positive": {
                "pos": (self.battery_pos[0], self.battery_pos[1] + comp_size * 0.4),  # Sus
                "size": terminal_size
            },
            "battery_negative": {
                "pos": (self.battery_pos[0], self.battery_pos[1] - comp_size * 0.4),  # Jos
                "size": terminal_size
            },
            "switch_in": {
                "pos": (self.switch_pos[0] - comp_size * 0.4, self.switch_pos[1]),
                "size": terminal_size
            },
            "switch_out": {
                "pos": (self.switch_pos[0] + comp_size * 0.4, self.switch_pos[1]),
                "size": terminal_size
            },
            "bulb_positive": {
                "pos": (self.bulb_pos[0] - comp_size * 0.4, self.bulb_pos[1] + comp_size * 0.3),
                "size": terminal_size
            },
            "bulb_negative": {
                "pos": (self.bulb_pos[0] - comp_size * 0.4, self.bulb_pos[1] - comp_size * 0.3),
                "size": terminal_size
            },
        }
        
        self._redraw()

    def on_size(self, *args):
        """Reconfigurează componentele când se schimbă dimensiunea."""
        if self.width and self.height:
            self._setup_components()

    def reset_components(self):
        """Resetează circuitul."""
        self.connections = []
        self.bulb_lit = False
        self.switch_on = False
        self._redraw()

    def clear_lines(self):
        """Șterge toate conexiunile."""
        self.connections = []
        self.bulb_lit = False
        self._redraw()

    def toggle_switch(self):
        """Comută întrerupătorul."""
        self.switch_on = not self.switch_on
        self._redraw()
        self._check_circuit()

    def _redraw(self):
        """Redesenează toate componentele și conexiunile."""
        self.canvas.before.clear()
        self.canvas.clear()
        self.canvas.after.clear()
        
        if not self.width or not self.height:
            return

        with self.canvas.before:
            # Fundal transparent (fără chenar alb)
            pass

        with self.canvas:
            # Desenează conexiunile existente
            for conn in self.connections:
                self._draw_wire(conn["start"], conn["end"])
            
            # Desenează componentele
            self._draw_battery()
            self._draw_switch()
            self._draw_bulb()
            
            # Desenează terminalele (zone de touch vizibile)
            self._draw_terminals()

    def _draw_battery(self):
        """Desenează bateria rotită la 90 de grade (verticală)."""
        x, y = self.battery_pos
        size = self.comp_size
        
        # Umbră (rotită vertical)
        Color(0, 0, 0, 0.3)
        Rectangle(
            pos=(x - size * 0.4 + 5, y - size * 0.45 - 5),
            size=(size * 0.8, size * 0.9)
        )
        
        # Corp baterie principal (vertical)
        Color(0.15, 0.55, 0.15, 1)
        Rectangle(
            pos=(x - size * 0.4, y - size * 0.45),
            size=(size * 0.8, size * 0.9)
        )
        
        # Banda verde deschis (orizontală acum, verticală în baterie rotită)
        Color(0.25, 0.7, 0.25, 1)
        Rectangle(
            pos=(x - size * 0.4, y + size * 0.15),
            size=(size * 0.8, size * 0.25)
        )
        
        # Liniile orizontale (simbol baterie rotit) - acum verticale
        Color(0.1, 0.4, 0.1, 1)
        for i in range(3):
            Line(
                points=[
                    x - size * 0.35, y - size * 0.3 + i * size * 0.3,
                    x + size * 0.35, y - size * 0.3 + i * size * 0.3
                ],
                width=4
            )
        
        # Terminal pozitiv (+) - sus (mare și clar)
        Color(0.9, 0.9, 0.9, 1)
        Rectangle(
            pos=(x - size * 0.1, y + size * 0.45),
            size=(size * 0.2, size * 0.3)
        )
        # Simbol + mare
        Color(0.1, 0.1, 0.1, 1)
        Line(points=[x - size * 0.1, y + size * 0.6, x + size * 0.1, y + size * 0.6], width=5)
        Line(points=[x, y + size * 0.5, x, y + size * 0.7], width=5)
        
        # Terminal negativ (-) - jos (mare și clar)
        Color(0.9, 0.9, 0.9, 1)
        Rectangle(
            pos=(x - size * 0.1, y - size * 0.75),
            size=(size * 0.2, size * 0.3)
        )
        # Simbol - mare
        Color(0.1, 0.1, 0.1, 1)
        Line(points=[x - size * 0.1, y - size * 0.6, x + size * 0.1, y - size * 0.6], width=5)

    def _draw_switch(self):
        """Desenează întrerupătorul cu imagini clare."""
        x, y = self.switch_pos
        size = self.comp_size
        
        # Umbră
        Color(0, 0, 0, 0.3)
        Rectangle(
            pos=(x - size * 0.4 + 4, y - size * 0.25 - 4),
            size=(size * 0.8, size * 0.5)
        )
        
        # Bază întrerupător
        Color(0.3, 0.3, 0.3, 1)
        Rectangle(
            pos=(x - size * 0.4, y - size * 0.25),
            size=(size * 0.8, size * 0.5)
        )
        
        # Highlight
        Color(0.4, 0.4, 0.4, 1)
        Rectangle(
            pos=(x - size * 0.4, y + size * 0.15),
            size=(size * 0.8, size * 0.1)
        )
        
        # Pârghie mare și clară
        if self.switch_on:
            Color(0.1, 0.9, 0.1, 1)  # Verde strălucitor când e ON
            # Pârghie în poziție ON (înclinată sus)
            Line(
                points=[
                    x - size * 0.3, y,
                    x + size * 0.3, y + size * 0.25
                ],
                width=10
            )
            # Indicător ON
            Color(0.1, 0.9, 0.1, 0.5)
            Ellipse(
                pos=(x - size * 0.15, y - size * 0.15),
                size=(size * 0.3, size * 0.3)
            )
        else:
            Color(0.9, 0.1, 0.1, 1)  # Roșu strălucitor când e OFF
            # Pârghie în poziție OFF (înclinată jos)
            Line(
                points=[
                    x - size * 0.3, y,
                    x - size * 0.3, y - size * 0.25
                ],
                width=10
            )
            # Indicător OFF
            Color(0.9, 0.1, 0.1, 0.5)
            Ellipse(
                pos=(x - size * 0.15, y - size * 0.15),
                size=(size * 0.3, size * 0.3)
            )
        
        # Terminale (cercuri mari și clare)
        Color(0.2, 0.2, 0.2, 1)
        Ellipse(
            pos=(x - size * 0.4 - size * 0.15, y - size * 0.15),
            size=(size * 0.3, size * 0.3)
        )
        Ellipse(
            pos=(x + size * 0.4 - size * 0.15, y - size * 0.15),
            size=(size * 0.3, size * 0.3)
        )

    def _draw_bulb(self):
        """Desenează becul cu imagini clare."""
        x, y = self.bulb_pos
        size = self.comp_size
        
        if self.bulb_lit:
            # Glow când e aprins (straturi multiple, mai strălucitor)
            for i in range(6):
                alpha = 0.7 - (i * 0.12)
                Color(1.0, 0.95, 0.3, alpha)
                Ellipse(
                    pos=(x - size * 0.5 - i * size * 0.12, y - size * 0.5 - i * size * 0.12),
                    size=(size + i * size * 0.24, size + i * size * 0.24)
                )
            Color(1.0, 0.98, 0.4, 1)
        else:
            Color(0.65, 0.65, 0.65, 1)
        
        # Umbră
        Color(0, 0, 0, 0.25)
        Ellipse(
            pos=(x - size * 0.5 + 4, y - size * 0.5 - 4),
            size=(size, size)
        )
        
        # Corp bec (bulb) - mare și clar
        Color(1.0, 0.98, 0.4, 1) if self.bulb_lit else Color(0.65, 0.65, 0.65, 1)
        Ellipse(
            pos=(x - size * 0.5, y - size * 0.5),
            size=(size, size)
        )
        
        # Highlight pe bec
        Color(1, 1, 1, 0.6)
        Ellipse(
            pos=(x - size * 0.3, y + size * 0.2),
            size=(size * 0.6, size * 0.6)
        )
        
        # Filament interior - mare și clar
        if self.bulb_lit:
            Color(1.0, 1.0, 0.8, 1)
        else:
            Color(0.2, 0.2, 0.2, 1)
        
        # Filament simplu (linie în zigzag) - mai gros
        filament_points = [
            x - size * 0.3, y + size * 0.2,
            x, y - size * 0.2,
            x + size * 0.3, y + size * 0.15
        ]
        Line(points=filament_points, width=6)
        
        # Baza becului - mare și clară
        Color(0.15, 0.15, 0.15, 1)
        Rectangle(
            pos=(x - size * 0.4, y - size * 0.75),
            size=(size * 0.8, size * 0.3)
        )
        
        # Terminale (cercuri mari și clare)
        Color(0.1, 0.1, 0.1, 1)
        Ellipse(
            pos=(x - size * 0.4 - size * 0.15, y + size * 0.3 - size * 0.15),
            size=(size * 0.3, size * 0.3)
        )
        Ellipse(
            pos=(x - size * 0.4 - size * 0.15, y - size * 0.3 - size * 0.15),
            size=(size * 0.3, size * 0.3)
        )

    def _draw_terminals(self):
        """Desenează terminalele ca zone de touch vizibile și clare."""
        for term_name, term_info in self.terminals.items():
            pos = term_info["pos"]
            size = term_info["size"]
            
            # Cerc pentru terminal (zone de touch) - mai vizibil
            Color(0.05, 0.78, 1, 0.5)  # Albastru neon transparent
            Ellipse(
                pos=(pos[0] - size * 0.5, pos[1] - size * 0.5),
                size=(size, size)
            )
            # Contur groasă
            Color(0.05, 0.78, 1, 1)  # Albastru neon
            Line(
                ellipse=(pos[0] - size * 0.5, pos[1] - size * 0.5, size, size),
                width=5
            )
            # Centru indicător
            Color(1, 1, 1, 0.8)
            Ellipse(
                pos=(pos[0] - size * 0.15, pos[1] - size * 0.15),
                size=(size * 0.3, size * 0.3)
            )

    def _draw_wire(self, start_terminal: str, end_terminal: str):
        """Desenează un fir între două terminale."""
        start_info = self.terminals.get(start_terminal)
        end_info = self.terminals.get(end_terminal)
        
        if not start_info or not end_info:
            return
        
        start_pos = start_info["pos"]
        end_pos = end_info["pos"]
        
        # Fir (linie foarte groasă pentru claritate)
        Color(0.05, 0.05, 0.05, 1)
        Line(points=[start_pos[0], start_pos[1], end_pos[0], end_pos[1]], width=12)
        
        # Highlight pe fir
        Color(0.3, 0.3, 0.3, 0.7)
        Line(points=[start_pos[0], start_pos[1], end_pos[0], end_pos[1]], width=6)

    def on_touch_down(self, touch):
        """Începe trasarea unui fir."""
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        
        terminal = self._terminal_at(touch.pos)
        if terminal:
            self._start_terminal = terminal
            self._touch_start = touch.pos
            with self.canvas.after:
                Color(0.1, 0.1, 0.1, 1)
                self._current_line = Line(points=[touch.x, touch.y], width=12)
        return True

    def on_touch_move(self, touch):
        """Continuă trasarea firului."""
        if self._current_line is not None:
            self._current_line.points += [touch.x, touch.y]
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        """Finalizează trasarea firului."""
        if self._current_line is None:
            return super().on_touch_up(touch)
        
        end_terminal = self._terminal_at(touch.pos)
        
        self._current_line = None
        
        if self._start_terminal and end_terminal and self._start_terminal != end_terminal:
            # Adaugă conexiunea
            connection = {
                "start": self._start_terminal,
                "end": end_terminal
            }
            # Evită duplicatele
            reverse_conn = {"start": end_terminal, "end": self._start_terminal}
            if connection not in self.connections and reverse_conn not in self.connections:
                self.connections.append(connection)
                self._redraw()
                self._check_circuit()
        
        self._start_terminal = None
        self._touch_start = None
        return super().on_touch_up(touch)

    def _terminal_at(self, pos: Tuple[float, float]) -> Optional[str]:
        """Găsește terminalul cel mai apropiat de poziție (zona de touch foarte mare)."""
        x, y = pos
        min_dist = float('inf')
        nearest = None
        
        for term_name, term_info in self.terminals.items():
            term_pos = term_info["pos"]
            term_size = term_info["size"]
            dist = math.sqrt((x - term_pos[0])**2 + (y - term_pos[1])**2)
            # Zonă de captură foarte mare pentru touchscreen
            if dist < term_size * 1.0 and dist < min_dist:
                min_dist = dist
                nearest = term_name
        
        return nearest

    def _check_circuit(self):
        """Verifică dacă circuitul este complet."""
        # Verifică conexiuni
        has_battery_switch = False
        has_switch_bulb = False
        
        for conn in self.connections:
            start = conn["start"]
            end = conn["end"]
            
            # Baterie -> Întrerupător
            if (("battery" in start and "switch" in end) or
                ("battery" in end and "switch" in start)):
                has_battery_switch = True
            
            # Întrerupător -> Bec
            if (("switch" in start and "bulb" in end) or
                ("switch" in end and "bulb" in start)):
                has_switch_bulb = True
        
        # Circuit complet dacă: baterie->switch->bec și switch e ON
        if has_battery_switch and has_switch_bulb and self.switch_on:
            self.bulb_lit = True
            self._redraw()
            # Notifică aplicația
            app = App.get_running_app()
            if hasattr(app, "on_circuit_complete"):
                Clock.schedule_once(lambda dt: app.on_circuit_complete(), 2.0)
        else:
            self.bulb_lit = False
            self._redraw()
