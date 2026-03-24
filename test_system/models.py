class User:
    def __init__(self, username: str, role: str):
        self.username = username
        self.role = role

    def is_admin(self) -> bool:
        return self.role == "admin"

    def is_student(self) -> bool:
        return self.role == "student"


class Test:
    def __init__(self, test_id: int, title: str):
        self.id = test_id
        self.title = title


class Question:
    def __init__(
        self,
        question_id: int,
        test_id: int,
        text: str,
        q_type: str,
        options: list[str],
        correct: str,
        points: int = 1,
        difficulty: str = "medium",
        explanation: str = ""
    ):
        self.id = question_id
        self.test_id = test_id
        self.text = text
        self.q_type = q_type
        self.options = options
        self.correct = correct
        self.points = points
        self.difficulty = difficulty
        self.explanation = explanation

    def check_answer(self, answer: str) -> bool:
        return answer.strip() == self.correct.strip()