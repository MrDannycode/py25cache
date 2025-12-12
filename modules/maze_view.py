import math
from typing import List, Tuple

from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.properties import ListProperty
from kivy.uix.widget import Widget


class MazeView(Widget):
    """
    Renderer 3D avansat pentru labirint cu efecte de iluminare, umbre și texturi.
    """

    __events__ = ("on_swipe",)

    # 2D list of characters from MazeGame (rows of strings split into chars)
    grid: List[List[str]] = ListProperty([])

    # Culori îmbunătățite cu contrast mai bun
    wall_color = ListProperty([0.15, 0.18, 0.22, 1])
    wall_highlight = ListProperty([0.25, 0.28, 0.32, 1])
    wall_shadow = ListProperty([0.05, 0.08, 0.12, 1])
    floor_color = ListProperty([0.88, 0.85, 0.78, 1])
    floor_shadow = ListProperty([0.75, 0.72, 0.65, 1])
    path_color = ListProperty([0.65, 0.75, 0.70, 1])
    exit_color = ListProperty([1.0, 0.85, 0.15, 1])
    exit_glow = ListProperty([1.0, 0.95, 0.35, 0.8])
    player_color = ListProperty([0.61, 0.16, 0.96, 1])  # Violet pentru creier
    player_glow = ListProperty([0.35, 0.85, 1.0, 0.6])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._touch_start: Tuple[float, float] | None = None
        self.bind(pos=self._redraw, size=self._redraw, grid=self._redraw)

    # --- Drawing ---
    def _redraw(self, *args):
        self.canvas.before.clear()
        self.canvas.after.clear()

        # Fundal întunecat
        with self.canvas.before:
            Color(0.08, 0.10, 0.12, 1)
            Rectangle(pos=self.pos, size=self.size)

        if not self.grid or not self.width or not self.height:
            return

        rows = len(self.grid)
        cols = len(self.grid[0]) if rows else 0
        if cols == 0:
            return

        cw = self.width / cols
        ch = self.height / rows

        with self.canvas:
            for r, row in enumerate(self.grid):
                for c, cell in enumerate(row):
                    x = self.x + c * cw
                    y = self.top - (r + 1) * ch

                    if cell == "#":
                        # Perete 3D cu iluminare și umbră
                        # Umbră (stânga și jos)
                        Color(*self.wall_shadow)
                        Rectangle(pos=(x, y), size=(cw * 0.15, ch))
                        Rectangle(pos=(x, y), size=(cw, ch * 0.15))

                        # Perete principal
                        Color(*self.wall_color)
                        Rectangle(pos=(x, y), size=(cw, ch))

                        # Highlight (dreapta și sus) pentru efect 3D
                        Color(*self.wall_highlight)
                        Rectangle(
                            pos=(x + cw * 0.85, y),
                            size=(cw * 0.15, ch)
                        )
                        Rectangle(
                            pos=(x, y + ch * 0.85),
                            size=(cw, ch * 0.15)
                        )

                        # Contur subtil
                        Color(0, 0, 0, 0.3)
                        Line(
                            rectangle=(x, y, cw, ch),
                            width=1.5
                        )
                        continue

                    # Podea / traseu
                    if cell == ".":
                        # Traseu parcurs - afișează ca podea normală (fără urmă vizuală)
                        Color(*self.floor_shadow)
                        Rectangle(
                            pos=(x + cw * 0.05, y + ch * 0.05),
                            size=(cw * 0.95, ch * 0.95)
                        )
                        Color(*self.floor_color)
                        Rectangle(pos=(x, y), size=(cw, ch))
                    else:
                        # Podea normală
                        # Umbră subtilă pentru adâncime
                        Color(*self.floor_shadow)
                        Rectangle(
                            pos=(x + cw * 0.05, y + ch * 0.05),
                            size=(cw * 0.95, ch * 0.95)
                        )
                        Color(*self.floor_color)
                        Rectangle(pos=(x, y), size=(cw, ch))

                    # Pattern de textură pentru podea (pătrate mici)
                    Color(1, 1, 1, 0.08)
                    for i in range(0, int(cw), max(1, int(cw // 4))):
                        for j in range(0, int(ch), max(1, int(ch // 4))):
                            if (i + j) % 2 == 0:
                                Rectangle(
                                    pos=(x + i, y + j),
                                    size=(cw // 4, ch // 4)
                                )

                    # Ieșire (imagine carte.png)
                    if cell == "E":
                        # Umbră sub imagine
                        Color(0, 0, 0, 0.3)
                        Ellipse(
                            pos=(x + cw * 0.2, y + ch * 0.1),
                            size=(cw * 0.6, ch * 0.2)
                        )

                        # Glow exterior (galben pentru carte)
                        Color(*self.exit_glow)
                        for i in range(2):
                            alpha = 0.4 - (i * 0.2)
                            Color(
                                self.exit_glow[0],
                                self.exit_glow[1],
                                self.exit_glow[2],
                                alpha
                            )
                            Ellipse(
                                pos=(
                                    x + cw * (0.2 - i * 0.05),
                                    y + ch * (0.15 - i * 0.05)
                                ),
                                size=(
                                    cw * (0.6 + i * 0.1),
                                    ch * (0.7 + i * 0.1)
                                )
                            )

                        # Imaginea carte.png
                        Color(1, 1, 1, 1)  # Culoare albă pentru a nu afecta imaginea
                        Rectangle(
                            pos=(x + cw * 0.2, y + ch * 0.2),
                            size=(cw * 0.6, ch * 0.6),
                            source='assets/images/carte.png'
                        )

                    # Jucător (imagine pngegg.png) cu glow și umbră
                    elif cell == "P":
                        # Umbră sub imagine
                        Color(0, 0, 0, 0.3)
                        Ellipse(
                            pos=(x + cw * 0.2, y + ch * 0.1),
                            size=(cw * 0.6, ch * 0.2)
                        )

                        # Glow exterior (violet pentru creier)
                        Color(*self.player_glow)
                        for i in range(2):
                            alpha = 0.4 - (i * 0.2)
                            Color(
                                self.player_glow[0],
                                self.player_glow[1],
                                self.player_glow[2],
                                alpha
                            )
                            Ellipse(
                                pos=(
                                    x + cw * (0.2 - i * 0.05),
                                    y + ch * (0.15 - i * 0.05)
                                ),
                                size=(
                                    cw * (0.6 + i * 0.1),
                                    ch * (0.7 + i * 0.1)
                                )
                            )

                        # Imaginea creierului (creier.png)
                        Color(1, 1, 1, 1)  # Culoare albă pentru a nu afecta imaginea
                        Rectangle(
                            pos=(x + cw * 0.2, y + ch * 0.2),
                            size=(cw * 0.6, ch * 0.6),
                            source='assets/images/creier.png'
                        )

    # --- Gestures ---
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        self._touch_start = touch.pos
        return True

    def on_touch_up(self, touch):
        if self._touch_start is None:
            return super().on_touch_up(touch)
        if not self.collide_point(*touch.pos):
            self._touch_start = None
            return super().on_touch_up(touch)

        sx, sy = self._touch_start
        dx = touch.x - sx
        dy = touch.y - sy
        distance = math.sqrt(dx * dx + dy * dy)
        self._touch_start = None

        # Threshold mai mare pentru a reduce sensibilitatea (0.08 în loc de 0.04)
        # Threshold mai mare pentru a reduce sensibilitatea (0.08 în loc de 0.04)
        threshold = max(self.width, self.height) * 0.08
        if abs(dx) < threshold and abs(dy) < threshold:
            return True

        # Distanță minimă pentru a detecta o glisare (10% din dimensiunea ecranului)
        min_swipe_distance = max(self.width, self.height) * 0.1
        if distance < min_swipe_distance:
            return True  # Glisare prea scurtă, ignoră

        direction = None
        if abs(dx) > abs(dy):
            direction = "right" if dx > 0 else "left"
        else:
            direction = "up" if dy > 0 else "down"
        
        # Calculează numărul de celule pe baza distanței
        # Folosește dimensiunea medie a celulei pentru a determina câte celule
        if not self.grid or not self.width or not self.height:
            cells = 1
        else:
            rows = len(self.grid)
            cols = len(self.grid[0]) if rows else 1
            avg_cell_size = (self.width / cols + self.height / rows) / 2
            # Numărul de celule = distanța / dimensiunea medie a celulei
            # Minimum 1 celulă, maximum 5 celule pentru o glisare foarte lungă
            # Ajustat pentru a necesita o distanță mai mare pentru mai multe celule
            cells = max(1, min(5, int(distance / (avg_cell_size * 1.5)) + 1))

        self.dispatch("on_swipe", direction, cells)
        return True

    def on_swipe(self, direction: str, cells: int):
        """Custom event dispatched when a swipe is detected."""
        pass
