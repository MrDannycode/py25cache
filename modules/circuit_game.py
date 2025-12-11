class CircuitGame:
    """
    Circuit simplu: baterie -> întrerupător -> bec
    Utilizatorul conectează firele trăgând cu degetul.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.connections = []  # Lista de conexiuni [(start, end), ...]
        self.switch_on = False

    def add_connection(self, start: str, end: str):
        """Adaugă o conexiune între componente."""
        # Evită duplicatele
        conn = (start, end) if start < end else (end, start)
        if conn not in self.connections:
            self.connections.append(conn)
        return self._check_circuit()

    def toggle_switch(self):
        """Comută întrerupătorul."""
        self.switch_on = not self.switch_on
        return self._check_circuit()

    def _check_circuit(self) -> str:
        """
        Verifică dacă circuitul este complet și corect.
        Returnează: "win" dacă e complet, altfel statusul curent.
        """
        # Verifică dacă există conexiune baterie -> întrerupător
        has_battery_switch = (
            ("battery", "switch") in self.connections or
            ("switch", "battery") in self.connections
        )
        
        # Verifică dacă există conexiune întrerupător -> bec
        has_switch_bulb = (
            ("switch", "bulb") in self.connections or
            ("bulb", "switch") in self.connections
        )
        
        # Verifică dacă există conexiune directă baterie -> bec (bypass)
        has_battery_bulb = (
            ("battery", "bulb") in self.connections or
            ("bulb", "battery") in self.connections
        )
        
        if has_battery_switch and has_switch_bulb and self.switch_on:
            return "win"
        elif has_battery_bulb and self.switch_on:
            # Conexiune directă (fără întrerupător) - tot e valid
            return "win"
        elif not (has_battery_switch or has_battery_bulb):
            return "need_battery"
        elif not (has_switch_bulb or has_battery_bulb):
            return "need_bulb"
        elif not self.switch_on:
            return "need_switch"
        else:
            return "incomplete"

    def render(self) -> str:
        """Randare text simplă pentru compatibilitate."""
        status = self._check_circuit()
        if status == "win":
            return "Circuit complet! Becul s-a aprins 💡"
        return f"Status: {status}"
