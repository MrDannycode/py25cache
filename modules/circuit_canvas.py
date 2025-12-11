import math
from typing import List, Tuple, Optional, Dict

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.app import App


class CircuitCanvas(Widget):
    """
    Canvas pentru schema electrică simplă: baterie, întrerupător, bec.
    Utilizatorul conectează firele trăgând cu degetul.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.components: List[Dict] = []
        self.connections: List[Dict] = []  # Lista de conexiuni (start, end)
        self._current_line = None
        self._touch_start = None
        self._start_component = None
        self.bulb_lit = False
        self._bulb_glow_anim = None
        self.reset_components()

    def reset_components(self):
        """Resetează componentele la pozițiile inițiale."""
        self.clear_lines()
        self.connections = []
        self.bulb_lit = False
        self._start_component = None
        
        # Poziții fixe pentru componente (baterie stânga, întrerupător mijloc, bec dreapta)
        if self.width and self.height:
            self._setup_components()

    def _setup_components(self):
        """Configurează componentele la poziții fixe."""
        w, h = self.width, self.height
        comp_size = min(w, h) * 0.15
        
        # Baterie - stânga
        battery_pos = (w * 0.15, h * 0.5)
        # Întrerupător - mijloc
        switch_pos = (w * 0.5, h * 0.5)
        # Bec - dreapta
        bulb_pos = (w * 0.85, h * 0.5)
        
        self.components = [
            {
                "name": "battery",
                "pos": battery_pos,
                "size": comp_size,
                "terminals": {
                    "positive": (battery_pos[0] + comp_size * 0.5, battery_pos[1] + comp_size * 0.3),
                    "negative": (battery_pos[0] + comp_size * 0.5, battery_pos[1] - comp_size * 0.3)
                }
            },
            {
                "name": "switch",
                "pos": switch_pos,
                "size": comp_size,
                "on": False,
                "terminals": {
                    "in": (switch_pos[0] - comp_size * 0.4, switch_pos[1]),
                    "out": (switch_pos[0] + comp_size * 0.4, switch_pos[1])
                }
            },
            {
                "name": "bulb",
                "pos": bulb_pos,
                "size": comp_size,
                "terminals": {
                    "positive": (bulb_pos[0] - comp_size * 0.4, bulb_pos[1] + comp_size * 0.3),
                    "negative": (bulb_pos[0] - comp_size * 0.4, bulb_pos[1] - comp_size * 0.3)
                }
            }
        ]
        self._redraw()

    def on_size(self, *args):
        """Reconfigurează componentele când se schimbă dimensiunea."""
        if self.width and self.height:
            self._setup_components()

    def clear_lines(self):
        """Șterge toate conexiunile."""
        self.canvas.after.clear()
        self.connections = []
        self.bulb_lit = False
        if self._bulb_glow_anim:
            self._bulb_glow_anim.cancel(self)
        self._redraw()

    def _redraw(self):
        """Redesenează toate componentele și conexiunile."""
        self.canvas.before.clear()
        self.canvas.clear()
        
        if not self.width or not self.height or not self.components:
            return

        with self.canvas.before:
            # Fundal
            Color(0.95, 0.95, 0.98, 1)
            Rectangle(pos=self.pos, size=self.size)

        with self.canvas:
            # Desenează componentele
            for comp in self.components:
                self._draw_component(comp)
            
            # Desenează conexiunile
            for conn in self.connections:
                self._draw_connection(conn)

    def _draw_component(self, comp: Dict):
        """Desenează o componentă (baterie, întrerupător sau bec)."""
        x, y = comp["pos"]
        size = comp["size"]
        
        if comp["name"] == "battery":
            self._draw_battery(x, y, size)
        elif comp["name"] == "switch":
            self._draw_switch(x, y, size, comp.get("on", False))
        elif comp["name"] == "bulb":
            self._draw_bulb(x, y, size, self.bulb_lit)

    def _draw_battery(self, x: float, y: float, size: float):
        """Desenează bateria."""
        # Corp baterie
        Color(0.3, 0.7, 0.3, 1)
        Rectangle(
            pos=(x - size * 0.4, y - size * 0.3),
            size=(size * 0.8, size * 0.6)
        )
        # Terminal pozitiv (+)
        Color(0.9, 0.9, 0.9, 1)
        Rectangle(
            pos=(x + size * 0.4, y - size * 0.1),
            size=(size * 0.15, size * 0.2)
        )
        # Terminal negativ (-)
        Rectangle(
            pos=(x + size * 0.4, y - size * 0.3),
            size=(size * 0.15, size * 0.2)
        )
        # Simbol +
        Color(0.2, 0.2, 0.2, 1)
        Line(points=[
            x + size * 0.475, y,
            x + size * 0.525, y,
            x + size * 0.5, y - size * 0.05,
            x + size * 0.5, y + size * 0.05
        ], width=2)
        # Simbol -
        Line(points=[
            x + size * 0.475, y - size * 0.2,
            x + size * 0.525, y - size * 0.2
        ], width=2)
        # Etichetă
        Color(0, 0, 0, 1)
        # Label va fi desenat separat dacă e necesar

    def _draw_switch(self, x: float, y: float, size: float, is_on: bool):
        """Desenează întrerupătorul."""
        # Bază întrerupător
        Color(0.5, 0.5, 0.5, 1)
        Rectangle(
            pos=(x - size * 0.3, y - size * 0.1),
            size=(size * 0.6, size * 0.2)
        )
        # Pârghie
        if is_on:
            Color(0.2, 0.8, 0.2, 1)  # Verde când e pornit
            # Pârghie în poziție ON (înclinată)
            Line(
                points=[
                    x - size * 0.25, y,
                    x + size * 0.25, y + size * 0.2
                ],
                width=4
            )
        else:
            Color(0.8, 0.2, 0.2, 1)  # Roșu când e oprit
            # Pârghie în poziție OFF (verticală)
            Line(
                points=[
                    x - size * 0.25, y,
                    x - size * 0.25, y - size * 0.2
                ],
                width=4
            )
        # Terminale
        Color(0.3, 0.3, 0.3, 1)
        Ellipse(
            pos=(x - size * 0.4 - size * 0.05, y - size * 0.05),
            size=(size * 0.1, size * 0.1)
        )
        Ellipse(
            pos=(x + size * 0.4 - size * 0.05, y - size * 0.05),
            size=(size * 0.1, size * 0.1)
        )

    def _draw_bulb(self, x: float, y: float, size: float, lit: bool):
        """Desenează becul."""
        # Filament (interior)
        if lit:
            # Glow când e aprins
            for i in range(3):
                alpha = 0.6 - (i * 0.2)
                Color(1.0, 0.9, 0.3, alpha)
                Ellipse(
                    pos=(x - size * 0.5 - i * size * 0.1, y - size * 0.5 - i * size * 0.1),
                    size=(size + i * size * 0.2, size + i * size * 0.2)
                )
            Color(1.0, 0.95, 0.4, 1)
        else:
            Color(0.7, 0.7, 0.7, 1)
        
        # Corp bec (bulb)
        Ellipse(
            pos=(x - size * 0.5, y - size * 0.5),
            size=(size, size)
        )
        
        # Filament interior
        if lit:
            Color(1.0, 1.0, 0.6, 1)
        else:
            Color(0.4, 0.4, 0.4, 1)
        
        # Filament simplu (linie în zigzag)
        filament_points = []
        for i in range(3):
            px = x - size * 0.15 + i * size * 0.15
            py = y + (size * 0.1 if i % 2 == 0 else -size * 0.1)
            filament_points.extend([px, py])
        if len(filament_points) >= 4:
            Line(points=filament_points, width=3)
        
        # Baza becului
        Color(0.3, 0.3, 0.3, 1)
        Rectangle(
            pos=(x - size * 0.3, y - size * 0.6),
            size=(size * 0.6, size * 0.2)
        )
        # Terminale
        Color(0.2, 0.2, 0.2, 1)
        Ellipse(
            pos=(x - size * 0.4 - size * 0.05, y - size * 0.3 - size * 0.05),
            size=(size * 0.1, size * 0.1)
        )
        Ellipse(
            pos=(x - size * 0.4 - size * 0.05, y - size * 0.5 - size * 0.05),
            size=(size * 0.1, size * 0.1)
        )

    def _draw_connection(self, conn: Dict):
        """Desenează o conexiune (fir) între două componente."""
        start = conn.get("start_terminal")
        end = conn.get("end_terminal")
        if not start or not end:
            return
        
        # Fir (linie)
        Color(0.2, 0.2, 0.2, 1)
        Line(points=[start[0], start[1], end[0], end[1]], width=4)

    def on_touch_down(self, touch):
        """Începe trasarea unui fir."""
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        
        comp = self._component_at(touch.pos)
        if comp:
            self._start_component = comp
            self._touch_start = touch.pos
            with self.canvas.after:
                Color(0.2, 0.2, 0.2, 1)
                self._current_line = Line(points=[touch.x, touch.y], width=4)
        return True

    def on_touch_move(self, touch):
        """Continuă trasarea firului."""
        if self._current_line is not None:
            self._current_line.points += [touch.x, touch.y]
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        """Finalizează trasarea firului și verifică conexiunea."""
        if self._current_line is None:
            return super().on_touch_up(touch)
        
        start_comp = self._start_component
        end_comp = self._component_at(touch.pos)
        
        self._current_line = None
        self._start_component = None
        self._touch_start = None
        
        if start_comp and end_comp and start_comp != end_comp:
            # Adaugă conexiunea
            start_terminal = self._get_nearest_terminal(start_comp, touch.pos)
            end_terminal = self._get_nearest_terminal(end_comp, touch.pos)
            
            connection = {
                "start": start_comp["name"],
                "end": end_comp["name"],
                "start_terminal": start_terminal,
                "end_terminal": end_terminal
            }
            self.connections.append(connection)
            self._redraw()
            
            # Verifică circuitul
            app = App.get_running_app()
            if hasattr(app, "check_circuit"):
                app.check_circuit()
        
        return super().on_touch_up(touch)

    def _component_at(self, pos: Tuple[float, float]) -> Optional[Dict]:
        """Găsește componenta la poziția dată."""
        x, y = pos
        for comp in self.components:
            cx, cy = comp["pos"]
            size = comp["size"]
            if (cx - size * 0.5 <= x <= cx + size * 0.5 and
                cy - size * 0.5 <= y <= cy + size * 0.5):
                return comp
        return None

    def _get_nearest_terminal(self, comp: Dict, pos: Tuple[float, float]) -> Tuple[float, float]:
        """Găsește terminalul cel mai apropiat de poziție."""
        terminals = comp.get("terminals", {})
        if not terminals:
            return comp["pos"]
        
        min_dist = float('inf')
        nearest = comp["pos"]
        
        for term_name, term_pos in terminals.items():
            dist = math.sqrt((pos[0] - term_pos[0])**2 + (pos[1] - term_pos[1])**2)
            if dist < min_dist:
                min_dist = dist
                nearest = term_pos
        
        return nearest

    def set_bulb_lit(self, lit: bool):
        """Setează starea becului (aprins/stins)."""
        self.bulb_lit = lit
        if lit:
            # Animație glow pulsant - redesenăm periodic
            Clock.schedule_interval(self._update_bulb_glow, 0.3)
        else:
            Clock.unschedule(self._update_bulb_glow)
        self._redraw()

    def _update_bulb_glow(self, dt):
        """Actualizează animația glow a becului."""
        if self.bulb_lit:
            self._redraw()
            return True
        else:
            return False
