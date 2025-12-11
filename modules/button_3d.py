from kivy.animation import Animation
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.button import Button


class Button3D(Button):
    """
    Buton 3D cu efecte avansate: gradient, umbre multiple, iluminare neon,
    animații la hover și press.
    """

    # Culori personalizabile
    base_color = ListProperty([1.0, 0.95, 0.85, 1])
    neon_color = ListProperty([0.05, 0.78, 1, 1])
    shadow_intensity = NumericProperty(0.35)
    glow_intensity = NumericProperty(0.6)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = [0, 0, 0, 0]  # Transparent pentru canvas
        self._anim_press = None
        self._anim_release = None
        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _update_canvas(self, *args):
        """Actualizează canvas-ul când se schimbă poziția sau dimensiunea."""
        self.canvas.before.clear()
        self.canvas.after.clear()
        self._draw_button()

    def _draw_button(self):
        """Desenează butonul cu efecte 3D avansate."""
        if not self.width or not self.height:
            return

        import kivy.metrics as metrics
        dp = metrics.dp

        # Umbră principală (jos)
        with self.canvas.before:
            Color(0, 0, 0, self.shadow_intensity)
            RoundedRectangle(
                pos=(self.x + dp(2), self.y - dp(4)),
                size=(self.width - dp(4), self.height),
                radius=[dp(12), dp(12), dp(12), dp(12)]
            )

            # Umbră secundară (mai subtilă)
            Color(0, 0, 0, self.shadow_intensity * 0.5)
            RoundedRectangle(
                pos=(self.x + dp(1), self.y - dp(2)),
                size=(self.width - dp(2), self.height + dp(1)),
                radius=[dp(12), dp(12), dp(12), dp(12)]
            )

            # Gradient base (simulat cu două straturi)
            # Strat inferior (mai închis)
            Color(
                self.base_color[0] * 0.85,
                self.base_color[1] * 0.85,
                self.base_color[2] * 0.85,
                self.base_color[3]
            )
            RoundedRectangle(
                pos=(self.x + dp(1), self.y + dp(1)),
                size=(self.width - dp(2), self.height - dp(2)),
                radius=[dp(12), dp(12), dp(12), dp(12)]
            )

            # Strat superior (mai deschis - efect gradient)
            Color(*self.base_color)
            RoundedRectangle(
                pos=(self.x + dp(2), self.y + dp(3)),
                size=(self.width - dp(4), self.height - dp(4)),
                radius=[dp(12), dp(12), dp(12), dp(12)]
            )

            # Highlight (iluminare de sus)
            Color(1, 1, 1, 0.25)
            RoundedRectangle(
                pos=(self.x + dp(2), self.y + self.height * 0.6),
                size=(self.width - dp(4), self.height * 0.4),
                radius=[dp(12), dp(12), 0, 0]
            )

        # Contur neon cu glow
        with self.canvas.after:
            # Glow exterior (mai slab)
            Color(
                self.neon_color[0],
                self.neon_color[1],
                self.neon_color[2],
                self.glow_intensity * 0.3
            )
            Line(
                width=dp(5),
                rounded_rectangle=(
                    self.x - dp(1), self.y - dp(1),
                    self.width + dp(2), self.height + dp(2),
                    dp(12), dp(12), dp(12), dp(12)
                )
            )

            # Contur neon principal
            Color(*self.neon_color)
            Line(
                width=dp(3),
                rounded_rectangle=(
                    self.x, self.y, self.width, self.height,
                    dp(12), dp(12), dp(12), dp(12)
                )
            )

            # Glow interior (highlight)
            Color(
                self.neon_color[0] * 1.5,
                self.neon_color[1] * 1.5,
                self.neon_color[2] * 1.5,
                self.glow_intensity * 0.5
            )
            Line(
                width=dp(1.5),
                rounded_rectangle=(
                    self.x + dp(2), self.y + dp(2),
                    self.width - dp(4), self.height - dp(4),
                    dp(10), dp(10), dp(10), dp(10)
                )
            )

    def on_touch_down(self, touch):
        """Animație la apăsare."""
        if self.collide_point(*touch.pos) and not self.disabled:
            self._anim_press = Animation(
                glow_intensity=1.0,
                shadow_intensity=0.5,
                duration=0.1
            )
            self._anim_press.start(self)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        """Animație la eliberare."""
        if self._anim_press:
            self._anim_press.cancel(self)
        if self.collide_point(*touch.pos) and not self.disabled:
            self._anim_release = Animation(
                glow_intensity=0.6,
                shadow_intensity=0.35,
                duration=0.15
            )
            self._anim_release.start(self)
        return super().on_touch_up(touch)

