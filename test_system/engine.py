from abc import ABC, abstractmethod
import time


class TestRunner(ABC):
    def run(self, questions):
        start_time = time.time()

        score = 0
        total = 0

        for question in questions:
            total += question.points
            answer = self.ask(question)

            if self.check(question, answer):
                score += question.points

        duration = int(time.time() - start_time)
        self.finish(score, total, duration)

    @abstractmethod
    def ask(self, question):
        pass

    def check(self, question, answer):
        return question.check_answer(answer)

    @abstractmethod
    def finish(self, score, total, duration):
        pass