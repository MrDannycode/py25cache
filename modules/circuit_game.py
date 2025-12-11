class CircuitGame:
    """
    Circuit 2D simplu:
    - Baterie pe stânga (fixă)
    - Două fire (sus/jos) ce trebuie plasate pentru a închide circuitul
    - Întrerupător pe ramura de sus
    - Bec pe dreapta
    Circuitul se aprinde când: fir sus + fir jos sunt puse și întrerupătorul e ON.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.wire_top = False
        self.wire_bottom = False
        self.switch_on = False

    def toggle_switch(self):
        self.switch_on = not self.switch_on
        return self._status()

    def place_wire(self, where: str):
        if where == "top":
            self.wire_top = True
        elif where == "bottom":
            self.wire_bottom = True
        return self._status()

    def _is_complete(self) -> bool:
        return self.wire_top and self.wire_bottom and self.switch_on

    def _status(self) -> str:
        if self._is_complete():
            return "win"
        if not (self.wire_top and self.wire_bottom):
            return "need_wires"
        if not self.switch_on:
            return "need_switch"
        return "ok"

    def render(self) -> str:
        """
        Randare 2D simplă cu markup Kivy pentru culori.
        B = baterie, S = întrerupător, L = bec, — = fir.
        """
        bat = "[color=#4CAF50]Baterie[/color]"
        sw_on = "[color=#FFC107]S(ON)[/color]" if self.switch_on else "S(off)"
        bulb_on = "[color=#FFEB3B]💡[/color]" if self._is_complete() else "💡"
        wire_h = "────"  # fir orizontal
        wire_top = wire_h if self.wire_top else "    "
        wire_bot = wire_h if self.wire_bottom else "    "

        line1 = f"{bat} {wire_top} {sw_on} {wire_top} {bulb_on}"
        line2 = " " * len(bat) + " " * 1 + "    " + " " * len(sw_on) + "    " + "    "
        line3 = f"{' ' * len(bat)} {wire_bot} {' ' * len(sw_on)} {wire_bot}    "

        return "\n".join([line1, line2, line3])

