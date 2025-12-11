from typing import Dict


class CircuitGame:
    """
    Joc simplu de completat circuit:
    slot1 -> baterie
    slot2 -> rezistor
    slot3 -> led
    Când toate sunt corecte, LED-ul „se aprinde”.
    """

    def __init__(self):
        self.correct = {"slot1": "baterie", "slot2": "rezistor", "slot3": "led"}
        self.reset()

    def reset(self):
        self.state: Dict[str, str] = {"slot1": "_", "slot2": "_", "slot3": "_"}

    def render(self) -> str:
        return (
            f"[ + ] Slot1: {self.state['slot1']}\n"
            f"[ R ] Slot2: {self.state['slot2']}\n"
            f"[ LED ] Slot3: {self.state['slot3']}"
        )

    def place(self, slot: str, component: str) -> str:
        if slot not in self.state:
            return "invalid"
        if self.state[slot] != "_":
            return "filled"

        if self.correct.get(slot) != component:
            # plasează totuși, ca feedback vizual, dar marchează greșit
            self.state[slot] = component
            return "wrong"

        self.state[slot] = component

        if all(self.state[s] == self.correct[s] for s in self.state):
            return "win"
        return "ok"

