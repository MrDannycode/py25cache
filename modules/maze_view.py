from typing import List, Tuple

from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.properties import ListProperty
from kivy.uix.widget import Widget


class MazeView(Widget):
    """
    A simple canvas-based renderer for the maze.

    Draws walls, floor, player, and exit with subtle shading and supports swipe
    gestures to move the player.
    """

    __events__ = ("on_swipe",)

    # 2D list of characters from MazeGame (rows of strings split into chars)
    grid: List[List[str]] = ListProperty([])

    wall_color = ListProperty([0.06, 0.12, 0.16, 1])
    floor_color = ListProperty([0.12, 0.20, 0.22, 1])
    path_color = ListProperty([0.18, 0.30, 0.34, 1])
    exit_color = ListProperty([0.97, 0.72, 0.23, 1])
    player_color = ListProperty([0.25, 0.82, 0.48, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._touch_start: Tuple[float, float] | None = None
        self.bind(pos=self._redraw, size=self._redraw, grid=self._redraw)

    # --- Drawing ---
    def _redraw(self, *args):
        self.canvas.before.clear()
        self.canvas.after.clear()

        with self.canvas.before:
            Color(0.05, 0.10, 0.12, 1)
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
                        Color(*self.wall_color)
                        Rectangle(pos=(x, y), size=(cw, ch))
                        Color(1, 1, 1, 0.03)
                        Line(rectangle=(x, y, cw, ch), width=1)
                        continue

                    # Base floor / path
                    if cell == ".":
                        Color(*self.path_color)
                    else:
                        Color(*self.floor_color)
                    Rectangle(pos=(x, y), size=(cw, ch))

                    if cell == "E":
                        # Exit tile glow
                        Color(*self.exit_color)
                        Rectangle(pos=(x + cw * 0.12, y + ch * 0.12), size=(cw * 0.76, ch * 0.76))
                        Color(1, 1, 1, 0.18)
                        Line(ellipse=(x + cw * 0.08, y + ch * 0.08, cw * 0.84, ch * 0.84), width=2)
                    elif cell == "P":
                        # Player marker with halo
                        Color(*self.player_color)
                        Ellipse(pos=(x + cw * 0.25, y + ch * 0.18), size=(cw * 0.5, ch * 0.64))
                        Color(1, 1, 1, 0.18)
                        Line(ellipse=(x + cw * 0.2, y + ch * 0.12, cw * 0.6, ch * 0.76), width=2)

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
        self._touch_start = None

        threshold = max(self.width, self.height) * 0.04
        if abs(dx) < threshold and abs(dy) < threshold:
            return True

        direction = None
        if abs(dx) > abs(dy):
            direction = "right" if dx > 0 else "left"
        else:
            direction = "up" if dy > 0 else "down"

        self.dispatch("on_swipe", direction)
        return True

    def on_swipe(self, direction: str):
        """Custom event dispatched when a swipe is detected."""
        pass

