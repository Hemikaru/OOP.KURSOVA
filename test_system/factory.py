from models import SingleChoiceQuestion, TextQuestion


class QuestionFactory:
    @staticmethod
    def create_question(
        question_id,
        test_id,
        text,
        q_type,
        options,
        correct,
        points=1,
        difficulty="medium",
        explanation=""
    ):
        if q_type == "single":
            return SingleChoiceQuestion(
                question_id=question_id,
                test_id=test_id,
                text=text,
                options=options,
                correct=correct,
                points=points,
                difficulty=difficulty,
                explanation=explanation
            )

        if q_type == "text":
            return TextQuestion(
                question_id=question_id,
                test_id=test_id,
                text=text,
                correct=correct,
                points=points,
                difficulty=difficulty,
                explanation=explanation
            )

        raise ValueError(f"Невідомий тип питання: {q_type}")