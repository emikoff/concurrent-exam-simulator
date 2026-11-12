"""
Модуль содержит классы, описывающие студента, экзаменатора
и попытку сдачи экзамена.
"""

from typing import NotRequired, TypedDict


class ExamEvent(TypedDict):
    examiner_name: str
    student_name: NotRequired[str]
    status: NotRequired[str]
    result_exam: NotRequired[str]
    time_work_all: NotRequired[float]
    time_lunch: NotRequired[float]


class ExaminerStatus(TypedDict):
    student_name: str
    status: str
    time_lunch: float
    total_student: int
    failed_student: int
    cnt_lunch: int
    time_work_all: float
    start_exam_time: float


class ExaminerSummary(TypedDict):
    total_student: int
    failed_student: int
    time_work_all: float
    cnt_lunch: int
    time_lunch: float


class Student:
    """Хранит данные студента, статус и результаты сдачи экзамена."""

    def __init__(self, name: str, gender: str) -> None:

        self.name = name
        self.gender = gender
        self.status = "queue"
        self.in_exam = False
        self.duration_exam: float = 0.0
        self.cnt_good_answer = 0
        self.cnt_bad_answer = 0


class Examiner:
    """
    Хранит данные экзаменатора, статистику, время работы и его текущий статус.
    """

    def __init__(self, name: str, gender: str) -> None:

        self.name = name
        self.gender = gender
        self.now_student = "-"
        self.total_student = 0
        self.failed_student = 0
        self.time_work_all: float = 0.0
        self.time_work: float = 0.0
        self.time_work_max: float = 30.0
        self.time_lunch: float = 0.0
        self.cnt_lunch = 0
        self.is_finished = False
        self.status = "free"


class ExamAttempt:
    """
    Хранит данные одной попытки сдачи экзамена, включая ответы студента
    и экзаменатора и результат экзамена.
    """

    def __init__(
        self, student: Student, examiner: Examiner, questions: list[str]
    ) -> None:

        self.student = student
        self.examiner = examiner
        self.questions = questions
        self.student_answers: list[str] = []
        self.correct_answer_examiner: list[set[str]] = []
        self.correct_cnt = 0
        self.wrong_cnt = 0
        self.result_exam = ""
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.duration_exam: float = 0.0
        self.lunch_duration: float = 0.0
        self.was_lunch = False
        self.statistics_questions = {question: 0 for question in self.questions}
