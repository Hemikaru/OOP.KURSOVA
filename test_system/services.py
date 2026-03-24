import json
from database import get_conn
from models import Test
from factory import QuestionFactory


def create_test(title: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("INSERT INTO tests(title) VALUES(?)", (title,))

    conn.commit()
    conn.close()


def get_tests():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, title FROM tests ORDER BY id DESC")
    rows = cur.fetchall()

    conn.close()
    return [Test(test_id=row[0], title=row[1]) for row in rows]


def add_question(
    test_id: int,
    text: str,
    q_type: str,
    options: list[str],
    correct: str,
    points: int = 1,
    difficulty: str = "medium",
    explanation: str = ""
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO questions(test_id, text, type, options, correct, points, difficulty, explanation)
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            test_id,
            text,
            q_type,
            json.dumps(options, ensure_ascii=False),
            correct,
            points,
            difficulty,
            explanation
        )
    )

    conn.commit()
    conn.close()


def get_questions(test_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, test_id, text, type, options, correct, points, difficulty, explanation
        FROM questions
        WHERE test_id=?
        ORDER BY id
        """,
        (test_id,)
    )

    rows = cur.fetchall()
    conn.close()

    questions = []
    for row in rows:
        options = json.loads(row[4]) if row[4] else []
        questions.append(
            QuestionFactory.create_question(
                question_id=row[0],
                test_id=row[1],
                text=row[2],
                q_type=row[3],
                options=options,
                correct=row[5],
                points=row[6],
                difficulty=row[7],
                explanation=row[8]
            )
        )

    return questions


def get_question_count(test_id: int) -> int:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM questions WHERE test_id=?", (test_id,))
    count = cur.fetchone()[0]

    conn.close()
    return count


def save_result(username: str, test_id: int, score: int, total: int, duration: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO results(username, test_id, score, total, duration) VALUES(?,?,?,?,?)",
        (username, test_id, score, total, duration)
    )

    conn.commit()
    conn.close()


def get_results():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT r.id, r.username, r.test_id, t.title, r.score, r.total, r.duration, r.created_at
        FROM results r
        LEFT JOIN tests t ON r.test_id = t.id
        ORDER BY r.id DESC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


def update_question(
    question_id: int,
    text: str,
    q_type: str,
    options: list[str],
    correct: str,
    points: int,
    difficulty: str,
    explanation: str
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE questions
        SET text=?, type=?, options=?, correct=?, points=?, difficulty=?, explanation=?
        WHERE id=?
        """,
        (
            text,
            q_type,
            json.dumps(options, ensure_ascii=False),
            correct,
            points,
            difficulty,
            explanation,
            question_id
        )
    )

    conn.commit()
    conn.close()


def delete_question(question_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM questions WHERE id=?", (question_id,))

    conn.commit()
    conn.close()