import random
from typing import List, Tuple, Optional

from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Rectangle
from kivy.app import App


class CircuitCanvas(Widget):
    """
    Zonă de desen pentru circuit: componente emoji plasate aleator,
    utilizatorul trage linii cu degetul pentru a conecta baterie -> bec.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.components: List[dict] = []
        self._current_line = None
        self._touch_start = None
        self._component_size = (64, 64)
        self.reset_components()

    def reset_components(self):
        self.clear_lines()
        self.clear_widgets()
        spots = [
            (0.1, 0.5),
            (0.35, 0.75),
            (0.35, 0.25),
            (0.65, 0.75),
            (0.65, 0.25),
            (0.85, 0.5),
        ]
        random.shuffle(spots)
        comp_defs = [
            ("battery", "🔋"),
            ("led", "💡"),
            ("transistor", "⚡"),
            ("diode", "⇉"),
        ]
        self.components = []
        for comp, spot in zip(comp_defs, spots):
            name, icon = comp
            self._add_component(name, icon, spot)

    def _add_component(self, name: str, icon: str, spot: Tuple[float, float]):
        colors = {
            "battery": (0.2, 0.7, 0.2, 1),
            "led": (0.95, 0.8, 0.2, 1),
            "transistor": (0.4, 0.6, 0.9, 1),
            "diode": (0.9, 0.4, 0.4, 1),
        }
        label_map = {
            "battery": "BAT",
            "led": "BEC",
            "transistor": "TR",
            "diode": "DIO",
        }
        w, h = self._component_size
        x = self.x + spot[0] * (self.width or 1) - w / 2
        y = self.y + spot[1] * (self.height or 1) - h / 2
        lbl = Label(
            text=label_map.get(name, icon),
            font_size="18sp",
            bold=True,
            color=(0, 0, 0, 1),
            size_hint=(None, None),
            size=(w, h),
            pos=(x, y),
        )
        with lbl.canvas.before:
            Color(*colors.get(name, (0.8, 0.8, 0.8, 1)))
            Rectangle(pos=lbl.pos, size=lbl.size)
        self.add_widget(lbl)
        self.components.append({"name": name, "icon": icon, "pos": (x, y), "size": (w, h), "widget": lbl})

    def on_size(self, *args):
        # Repoziționează componentele la resize
        self.reset_components()

    def clear_lines(self):
        self.canvas.after.clear()

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        with self.canvas.after:
            Color(1, 0.8, 0.2, 1)
            self._current_line = Line(points=[touch.x, touch.y], width=4)
        self._touch_start = touch.pos
        return True

    def on_touch_move(self, touch):
        if self._current_line is not None:
            self._current_line.points += [touch.x, touch.y]
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        start_comp = self._component_at(self._touch_start) if self._touch_start else None
        end_comp = self._component_at(touch.pos)
        self._current_line = None
        self._touch_start = None
        app = App.get_running_app()
        if hasattr(app, "on_circuit_line_drawn"):
            app.on_circuit_line_drawn(start_comp, end_comp)
        return super().on_touch_up(touch)

    def _component_at(self, pos: Tuple[float, float]) -> Optional[str]:
        x, y = pos
        for comp in self.components:
            cx, cy = comp["pos"]
            w, h = comp["size"]
            if cx <= x <= cx + w and cy <= y <= cy + h:
                return comp["name"]
        return None

