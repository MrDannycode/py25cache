from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Question:
    text: str
    options: List[str]
    scores: List[Dict[str, int]]


class PersonalityTest:
    """
    Mini test de personalitate. Scorurile cresc pe 4 axe:
    - analitic
    - creativ
    - social
    - practic
    """

    def __init__(self):
        self.questions: List[Question] = self._default_questions()
        self.reset()

    def _default_questions(self) -> List[Question]:
        return [
            Question(
                text="Ce tip de proiect te entuziasmează cel mai mult?",
                options=["Construiesc ceva cu mâinile", "Rezolv puzzle-uri logice", "Fac un design/video", "Coordonez o echipă"],
                scores=[
                    {"practic": 2},
                    {"analitic": 2},
                    {"creativ": 2},
                    {"social": 2},
                ],
            ),
            Question(
                text="Cum preferi să înveți?",
                options=["Prin experimente și prototipuri", "Citind și analizând date", "Creând povești sau imagini", "Discutând cu alții"],
                scores=[
                    {"practic": 2},
                    {"analitic": 2},
                    {"creativ": 2},
                    {"social": 2},
                ],
            ),
            Question(
                text="Ce te motivează într-un proiect?",
                options=["Impact vizibil și rapid", "Soluția elegantă și optimă", "Mesajul și emoția transmisă", "Lucrul cu oamenii"],
                scores=[
                    {"practic": 2},
                    {"analitic": 2},
                    {"creativ": 2},
                    {"social": 2},
                ],
            ),
            Question(
                text="Dacă ai o zi liberă, ce ai face?",
                options=["Tinkering / DIY", "Hackathon sau probleme logice", "Artă, muzică, video", "Voluntariat / eveniment social"],
                scores=[
                    {"practic": 2},
                    {"analitic": 2},
                    {"creativ": 2},
                    {"social": 2},
                ],
            ),
        ]

    def reset(self):
        self.index = 0
        self.scores = {"analitic": 0, "creativ": 0, "social": 0, "practic": 0}

    def current_question(self):
        if self.index >= len(self.questions):
            return None
        q = self.questions[self.index]
        return {"text": q.text, "options": q.options}

    def has_next(self) -> bool:
        return self.index < len(self.questions)

    def progress_label(self) -> str:
        return f"Întrebarea {self.index + 1} din {len(self.questions)}"

    def answer(self, option_index: int):
        if not self.has_next():
            raise RuntimeError("Testul s-a terminat.")
        question = self.questions[self.index]
        if option_index < 0 or option_index >= len(question.options):
            raise ValueError("Index invalid pentru răspuns.")
        # aplică scor
        for axis, val in question.scores[option_index].items():
            self.scores[axis] = self.scores.get(axis, 0) + val
        self.index += 1

    def result(self) -> Dict[str, str]:
        if self.has_next():
            raise RuntimeError("Testul nu este complet.")
        axis = max(self.scores, key=self.scores.get)
        mapping = {
            "analitic": ("Informatică / Inginerie", "Îți plac structurile logice și rezolvarea problemelor."),
            "creativ": ("Design / Arte / Media", "Îți place să creezi, să transmiți emoție și să găsești idei noi."),
            "social": ("Științe economice / Comunicare", "Te motivează munca cu oamenii și coordonarea echipelor."),
            "practic": ("Automatică / Construcții / Mecatronică", "Îți place să vezi rezultate concrete și să construiești lucruri."),
        }
        faculty, reason = mapping.get(axis, ("Facultate mixtă", "Ai interese variate."))  # type: ignore
        return {"faculty": faculty, "reason": reason}


if __name__ == "__main__":
    # Mic demo CLI
    test = PersonalityTest()
    while test.has_next():
        q = test.current_question()
        print(q["text"])
        for idx, opt in enumerate(q["options"]):
            print(f"  {idx + 1}. {opt}")
        test.answer(0)
    print(test.result())
