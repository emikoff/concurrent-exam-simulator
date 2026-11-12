"""
Содержит логику проведения экзамена, включая работу банка вопросов,
генерацию ответов и выбор слов.
"""

from random import choice, choices, uniform
from models import ExamAttempt, Student, Examiner


class WordSelection:
    """
    Выбирает случайное слово из вопроса по правилу золотого сечения
    """

    def __init__(self) -> None:
        self.golden_ratio = 1.618

    def _index(self, num: int) -> list[float]:
        """Определяет вероятность выбора слова

        Args:
            num (int): Длина списка слов.

        Returns:
            list[float]: Список весов для последующего случайного выбора слова.
        """
        total = 1.0
        result: list[float] = []

        for _ in range(num - 1):
            res = total / self.golden_ratio
            result.append(res)
            total = total - res

        result.append(1 - sum(result))

        return result

    def word(self, words: str, gender: str = "М") -> str:
        """Выбирает случайное слово из текста вопроса.

        Args:
            words (str): Текст вопроса.
            gender (str): Пол М или Ж. Влияет на вероятность выбора слова.
            Defaults to "М".

        Returns:
            str: случайное слово из текста вопроса.
        """
        word_list = words.split()
        idx = self._index(len(word_list))
        if gender == "Ж":
            idx = idx[::-1]

        return choices(word_list, idx)[0]


class BankQuestions:
    """
    Хранит список вопросов
    """

    def __init__(self, questions: dict[str, int]) -> None:
        self.statistics_questions = questions

    def select_question(self, num: int = 3) -> list[str]:
        """
        Выбирает случайные вопросы (по умолчанию 3) для проведения экзамена.

        Args:
            num (int): Нужное количество случайных вопросов. Defaults to 3.

        Raises:
            Exception: Недостаточное колчичество вопросов.

        Returns:
            list[str]: Список вопросов
        """
        if len(self.statistics_questions) < (num):
            raise Exception("Недостатчоное колчичество вопросов")

        list_words = [words for words in self.statistics_questions]

        result: list[str] = []
        while len(result) < num:
            question = choice(list_words)
            if question not in result:
                result.append(question)

        return result


class AnswerGenerator:
    """
    Формирует ответы экзаменатора.
    """

    def __init__(self, word_selector: WordSelection) -> None:
        self.word_selector = word_selector
        self.continue_probability = 1 / 3

    def generate_answer(self, question: str, gender: str) -> set[str]:
        """Формирует ответ экзаменатора как множество слов. С вероятностью 1/3 после выбора слова определяет, продолжать ли добавлять слова.

        Args:
            question (str): Текст вопроса.
            gender (str): Пол экзаменатора, влияет на вероятность выбора слова.

        Returns:
            set[str]: Множество ответов.
        """
        result: set[str] = set()
        len_question = len(set(question.split()))

        add_answer = [True]

        while len(result) < len_question and add_answer[0]:
            word = self.word_selector.word(question, gender)
            if word not in result:
                result.add(word)
                add_answer = choices(
                    (True, False),
                    [self.continue_probability, 1 - self.continue_probability],
                )

        return result


class ExamProcessor:
    """
    Логика проведения экзамена. Получает ответы экзаменатора, студента
    и сверяет их. Определяет результат экзамена, обновляет статистику вопросов.
    """

    def __init__(
        self,
        bank_questions: BankQuestions,
        student: Student,
        examiner: Examiner,
        word_selection: WordSelection,
    ) -> None:

        self.bank_questions = bank_questions
        self.questions = self.bank_questions.select_question()
        self.student = student
        self.examiner = examiner
        self.word_selection = word_selection
        self.answer_generator = AnswerGenerator(self.word_selection)

    def _pull_answer_student(self) -> list[str]:
        result = []

        for el in self.questions:
            result.append(self.word_selection.word(el, self.student.gender))

        return result

    def _pull_answer_examiner(self) -> list[set[str]]:
        result = []
        for el in self.questions:
            result.append(
                self.answer_generator.generate_answer(el, self.examiner.gender)
            )
        return result

    def _check_answer(self) -> list[bool]:
        result = []
        num = len(self.exam_attempt.correct_answer_examiner)
        for i in range(num):
            if (
                self.exam_attempt.student_answers[i]
                in self.exam_attempt.correct_answer_examiner[i]
            ):
                self.exam_attempt.correct_cnt += 1
                result.append(True)
            else:
                self.exam_attempt.wrong_cnt += 1
                result.append(False)

        return result

    def _result_exam(self) -> str:
        mood = self._mood()

        if mood == "Хорошее":
            return "passed"
        elif mood == "Нейтральное":
            if self.exam_attempt.correct_cnt > self.exam_attempt.wrong_cnt:
                return "passed"

        return "failed"

    def _mood(self) -> str:
        return choices(["Плохое", "Хорошее", "Нейтральное"], [1 / 8, 1 / 4, 5 / 8])[0]

    def _update_statistics_questions(self, check_answer: list[bool]) -> None:
        num = len(self.questions)
        for i in range(num):
            if check_answer[i]:
                self.exam_attempt.statistics_questions[self.questions[i]] += 1

    def _start_exam(self) -> None:
        self._start_student_exam()
        self._start_examiner_exam()

    def _start_student_exam(self) -> None:
        self.student.in_exam = True

    def _start_examiner_exam(self) -> None:
        self.examiner.now_student = self.student.name
        self.examiner.total_student = 1
        self.examiner.status = "Экзамен"

    def _end_student_exam(self) -> None:
        self.student.status = self.exam_attempt.result_exam
        self.student.duration_exam = self.exam_attempt.duration_exam
        self.student.in_exam = False
        self.student.cnt_good_answer = self.exam_attempt.correct_cnt
        self.student.cnt_bad_answer = self.exam_attempt.wrong_cnt

    def _end_examiner_exam(self) -> None:
        self.examiner.time_work_all += self.exam_attempt.duration_exam
        self.examiner.time_work += self.exam_attempt.duration_exam

        if self.exam_attempt.result_exam == "failed":
            self.examiner.failed_student = 1
        else:
            self.examiner.failed_student = 0

        self.examiner.now_student = "-"
        self.examiner.status = "Свободен"

    def _end_exam(self, check_answer: list[bool]) -> None:

        self.exam_attempt.duration_exam += self._time_process()

        self._end_student_exam()
        self._end_examiner_exam()

        self._update_statistics_questions(check_answer)

    def _time_process(self) -> float:
        len_name_examiner = len(self.examiner.name)

        return round(uniform(len_name_examiner - 1, len_name_examiner + 1), 2)

    def process(self) -> ExamAttempt:
        """
        Проводит экзамен и возвращает его результат.

        Returns:
            ExamAttempt: Результат одной попытки сдачи экзамена.
        """
        self.exam_attempt = ExamAttempt(self.student, self.examiner, self.questions)

        # запустить экзамен
        self._start_exam()

        # получить ответы
        self.exam_attempt.student_answers = self._pull_answer_student()
        self.exam_attempt.correct_answer_examiner = self._pull_answer_examiner()

        # проверить ответы
        check_answer = self._check_answer()

        # определить результат
        self.exam_attempt.result_exam = self._result_exam()

        # завершить экзамен
        self._end_exam(check_answer)

        # вернуть ExamAttempt
        return self.exam_attempt
