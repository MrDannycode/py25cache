import math
from typing import List, Tuple, Optional, Dict

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.app import App


class CircuitCanvas(Widget):
    """
    Canvas simplu și intuitiv pentru schema electrică: baterie, întrerupător, bec.
    Utilizatorul conectează firele trăgând cu degetul între terminale.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connections: List[Dict] = []
        self._current_line = None
        self._touch_start = None
        self._start_terminal = None
        self.bulb_lit = False
        self.switch_on = False
        self._setup_components()

    def _setup_components(self):
        """Configurează componentele la poziții fixe și mai mari."""
        if not self.width or not self.height:
            return
        
        w, h = self.width, self.height
        comp_size = min(w, h) * 0.25  # Componente mai mari
        
        # Poziții fixe, centrate vertical
        self.battery_pos = (w * 0.2, h * 0.5)
        self.switch_pos = (w * 0.5, h * 0.5)
        self.bulb_pos = (w * 0.8, h * 0.5)
        self.comp_size = comp_size
        
        # Terminale pentru conexiuni
        self.terminals = {
            "battery_positive": (self.battery_pos[0] + comp_size * 0.4, self.battery_pos[1]),
            "battery_negative": (self.battery_pos[0] - comp_size * 0.4, self.battery_pos[1]),
            "switch_in": (self.switch_pos[0] - comp_size * 0.4, self.switch_pos[1]),
            "switch_out": (self.switch_pos[0] + comp_size * 0.4, self.switch_pos[1]),
            "bulb_positive": (self.bulb_pos[0] - comp_size * 0.4, self.bulb_pos[1] + comp_size * 0.2),
            "bulb_negative": (self.bulb_pos[0] - comp_size * 0.4, self.bulb_pos[1] - comp_size * 0.2),
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
            # Fundal
            Color(0.96, 0.96, 0.98, 1)
            Rectangle(pos=self.pos, size=self.size)

        with self.canvas:
            # Desenează conexiunile existente
            for conn in self.connections:
                self._draw_wire(conn["start"], conn["end"])
            
            # Desenează componentele
            self._draw_battery()
            self._draw_switch()
            self._draw_bulb()
            
            # Desenează linia curentă (în timpul trasării)
            if self._current_line:
                pass  # Linia este deja desenată în canvas.after

    def _draw_battery(self):
        """Desenează bateria."""
        x, y = self.battery_pos
        size = self.comp_size
        
        # Umbră
        Color(0, 0, 0, 0.2)
        Rectangle(
            pos=(x - size * 0.4 + 3, y - size * 0.3 - 3),
            size=(size * 0.8, size * 0.6)
        )
        
        # Corp baterie
        Color(0.25, 0.65, 0.25, 1)
        Rectangle(
            pos=(x - size * 0.4, y - size * 0.3),
            size=(size * 0.8, size * 0.6)
        )
        
        # Highlight
        Color(0.35, 0.75, 0.35, 1)
        Rectangle(
            pos=(x - size * 0.4, y + size * 0.1),
            size=(size * 0.8, size * 0.2)
        )
        
        # Terminal pozitiv (+)
        Color(0.9, 0.9, 0.9, 1)
        Rectangle(
            pos=(x + size * 0.4, y - size * 0.05),
            size=(size * 0.2, size * 0.1)
        )
        # Simbol +
        Color(0.2, 0.2, 0.2, 1)
        Line(points=[x + size * 0.5, y - size * 0.05, x + size * 0.5, y + size * 0.05], width=2)
        Line(points=[x + size * 0.45, y, x + size * 0.55, y], width=2)
        
        # Terminal negativ (-)
        Color(0.9, 0.9, 0.9, 1)
        Rectangle(
            pos=(x - size * 0.6, y - size * 0.05),
            size=(size * 0.2, size * 0.1)
        )
        # Simbol -
        Color(0.2, 0.2, 0.2, 1)
        Line(points=[x - size * 0.5, y, x - size * 0.4, y], width=2)
        
        # Etichetă
        Color(0, 0, 0, 1)
        # Vom desena text separat dacă e necesar

    def _draw_switch(self):
        """Desenează întrerupătorul."""
        x, y = self.switch_pos
        size = self.comp_size
        
        # Umbră
        Color(0, 0, 0, 0.2)
        Rectangle(
            pos=(x - size * 0.3 + 2, y - size * 0.15 - 2),
            size=(size * 0.6, size * 0.3)
        )
        
        # Bază întrerupător
        Color(0.4, 0.4, 0.4, 1)
        Rectangle(
            pos=(x - size * 0.3, y - size * 0.15),
            size=(size * 0.6, size * 0.3)
        )
        
        # Highlight
        Color(0.5, 0.5, 0.5, 1)
        Rectangle(
            pos=(x - size * 0.3, y + size * 0.05),
            size=(size * 0.6, size * 0.1)
        )
        
        # Pârghie
        if self.switch_on:
            Color(0.2, 0.8, 0.2, 1)  # Verde când e ON
            # Pârghie în poziție ON (înclinată sus)
            Line(
                points=[
                    x - size * 0.2, y,
                    x + size * 0.2, y + size * 0.15
                ],
                width=5
            )
        else:
            Color(0.8, 0.2, 0.2, 1)  # Roșu când e OFF
            # Pârghie în poziție OFF (înclinată jos)
            Line(
                points=[
                    x - size * 0.2, y,
                    x - size * 0.2, y - size * 0.15
                ],
                width=5
            )
        
        # Terminale (cercuri)
        Color(0.3, 0.3, 0.3, 1)
        Ellipse(
            pos=(x - size * 0.4 - size * 0.08, y - size * 0.08),
            size=(size * 0.16, size * 0.16)
        )
        Ellipse(
            pos=(x + size * 0.4 - size * 0.08, y - size * 0.08),
            size=(size * 0.16, size * 0.16)
        )

    def _draw_bulb(self):
        """Desenează becul."""
        x, y = self.bulb_pos
        size = self.comp_size
        
        if self.bulb_lit:
            # Glow când e aprins (straturi multiple)
            for i in range(4):
                alpha = 0.5 - (i * 0.12)
                Color(1.0, 0.9, 0.2, alpha)
                Ellipse(
                    pos=(x - size * 0.5 - i * size * 0.08, y - size * 0.5 - i * size * 0.08),
                    size=(size + i * size * 0.16, size + i * size * 0.16)
                )
            Color(1.0, 0.95, 0.3, 1)
        else:
            Color(0.75, 0.75, 0.75, 1)
        
        # Umbră
        Color(0, 0, 0, 0.15)
        Ellipse(
            pos=(x - size * 0.5 + 2, y - size * 0.5 - 2),
            size=(size, size)
        )
        
        # Corp bec (bulb)
        Color(1.0, 0.95, 0.3, 1) if self.bulb_lit else Color(0.75, 0.75, 0.75, 1)
        Ellipse(
            pos=(x - size * 0.5, y - size * 0.5),
            size=(size, size)
        )
        
        # Highlight pe bec
        Color(1, 1, 1, 0.4)
        Ellipse(
            pos=(x - size * 0.3, y + size * 0.1),
            size=(size * 0.6, size * 0.4)
        )
        
        # Filament interior
        if self.bulb_lit:
            Color(1.0, 1.0, 0.7, 1)
        else:
            Color(0.3, 0.3, 0.3, 1)
        
        # Filament simplu (linie în zigzag)
        filament_points = [
            x - size * 0.2, y + size * 0.1,
            x, y - size * 0.1,
            x + size * 0.2, y + size * 0.05
        ]
        Line(points=filament_points, width=3)
        
        # Baza becului
        Color(0.25, 0.25, 0.25, 1)
        Rectangle(
            pos=(x - size * 0.3, y - size * 0.65),
            size=(size * 0.6, size * 0.2)
        )
        
        # Terminale
        Color(0.2, 0.2, 0.2, 1)
        Ellipse(
            pos=(x - size * 0.4 - size * 0.08, y + size * 0.2 - size * 0.08),
            size=(size * 0.16, size * 0.16)
        )
        Ellipse(
            pos=(x - size * 0.4 - size * 0.08, y - size * 0.2 - size * 0.08),
            size=(size * 0.16, size * 0.16)
        )

    def _draw_wire(self, start_terminal: str, end_terminal: str):
        """Desenează un fir între două terminale."""
        start_pos = self.terminals.get(start_terminal)
        end_pos = self.terminals.get(end_terminal)
        
        if not start_pos or not end_pos:
            return
        
        # Fir (linie groasă)
        Color(0.15, 0.15, 0.15, 1)
        Line(points=[start_pos[0], start_pos[1], end_pos[0], end_pos[1]], width=6)
        
        # Highlight pe fir
        Color(0.3, 0.3, 0.3, 0.5)
        Line(points=[start_pos[0], start_pos[1], end_pos[0], end_pos[1]], width=3)

    def on_touch_down(self, touch):
        """Începe trasarea unui fir."""
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        
        terminal = self._terminal_at(touch.pos)
        if terminal:
            self._start_terminal = terminal
            self._touch_start = touch.pos
            with self.canvas.after:
                Color(0.2, 0.2, 0.2, 1)
                self._current_line = Line(points=[touch.x, touch.y], width=6)
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
        """Găsește terminalul cel mai apropiat de poziție."""
        x, y = pos
        min_dist = float('inf')
        nearest = None
        
        for term_name, term_pos in self.terminals.items():
            dist = math.sqrt((x - term_pos[0])**2 + (y - term_pos[1])**2)
            # Zonă de captură mai mare pentru ușurință
            if dist < min(self.comp_size * 0.3, 50) and dist < min_dist:
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
