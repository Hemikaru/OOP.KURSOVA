from abc import ABC, abstractmethod
import time


class TestRunner(ABC):
    def run(self, questions):
        start_time = time.time()

        score = 0
        for question in questions:
            answer = self.ask(question)
            if self.check(question, answer):
                score += 1

        duration = int(time.time() - start_time)
        self.finish(score, len(questions), duration)

    @abstractmethod
    def ask(self, question):
        pass

    def check(self, question, answer):
        return question.check_answer(answer)

    @abstractmethod
    def finish(self, score, total, duration):
        pass