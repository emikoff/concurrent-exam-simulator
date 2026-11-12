from random import uniform
import time

import multiprocessing as mp
import queue

from exam import WordSelection, ExamProcessor
from reports import LiveReport
from models import ExamAttempt, ExamEvent, ExaminerStatus, Student, Examiner
from data import ExamData
from exam import BankQuestions


class EventHandler:
    """
    Обновляет состояние экзамена.
    """

    def update_status(
        self,
        event: ExamEvent,
        examiner_status: dict[str, ExaminerStatus],
        student_status: dict[str, str],
        current_elapsed: float,
    ) -> tuple[dict[str, ExaminerStatus], dict[str, str]]:
        """
        Обновляет статус студента и экзаменатора во время экзамена.

        Args:
            event (dict[str, str | float]): Событие с информацией о текущем состоянии.
            examiner_status (dict[str, dict[str, str | int | float]]): Состояние экзаменаторов.
            student_status (dict[str, str]): Состояние студентов.
            current_elapsed (float): Текущее время с начала экзамена

        Returns:
            tuple(dict[str, dict[str, str | int | float]], dict[str, str]): Состояние экзаменаторов и студентов.
        """
        examiner_name = event["examiner_name"]

        if "status" in event:
            examiner_status[examiner_name]["status"] = event["status"]
            if event["status"] == "start_exam":
                examiner_status[examiner_name]["total_student"] += 1
                examiner_status[examiner_name]["start_exam_time"] = current_elapsed
            elif event["status"] == "start_lunch":
                examiner_status[examiner_name]["cnt_lunch"] += 1

        if "student_name" in event:
            examiner_status[examiner_name]["student_name"] = event["student_name"]
            if event["student_name"] != "-":
                if "result_exam" in event:
                    student_status[event["student_name"]] = event["result_exam"]
                elif "status" in event:
                    student_status[event["student_name"]] = event["status"]

        if "result_exam" in event and event["result_exam"] == "failed":
            examiner_status[examiner_name]["failed_student"] += 1

        if "time_work_all" in event:
            examiner_status[examiner_name]["time_work_all"] += event["time_work_all"]

        if "time_lunch" in event:
            examiner_status[examiner_name]["time_lunch"] += event["time_lunch"]

        return examiner_status, student_status


class ExaminerWorker:
    """
    Worker одного экзаменатора.
    """

    def __init__(
        self,
        bank_questions: BankQuestions,
        examiner: Examiner,
        word_selection: WordSelection,
    ) -> None:

        self.bank_questions = bank_questions
        self.examiner = examiner
        self.word_selection = word_selection

    def _lunch(self) -> None:
        """
        Cбрасывает накопленное время до следующего обеда, определяет
        продолжительность обеда и ждет это время
        """
        self.examiner.time_work = 0
        self.time_for_lunch = uniform(12, 18)

        time.sleep(self.time_for_lunch)
        self.exam_attempt.lunch_duration = self.time_for_lunch

    def run(
        self,
        student_queue: mp.Queue,
        result_queue: mp.Queue,
        event_queue: mp.Queue,
        cnt_student_queue: mp.Value,
    ) -> None:
        """
        Из очереди студентов берет студента, проводит экзамен
        и помещает данныесобытий и результатов в соответствующие очереди.

        Args:
            student_queue (mp.Queue()): Очередь, в которой находятся объекты
                Student, а также специальный None, который сообщает worker-у о
                завершении работы.
            result_queue (mp.Queue()): Очередь, куда worker кладет объекты
                ExamAttempt (результат текущей попытки).
            event_queue (mp.Queue()): Очередь, куда worker кладет словари
                текущего события.
        """
        while True:
            student = student_queue.get()
            if student is None:
                break

            with cnt_student_queue.get_lock():
                cnt_student_queue.value -= 1

            event_queue.put(
                {
                    "examiner_name": self.examiner.name,
                    "student_name": student.name,
                    "status": "start_exam",
                }
            )

            exam_processor = ExamProcessor(
                self.bank_questions,
                student,
                self.examiner,
                self.word_selection,
            )

            self.exam_attempt = exam_processor.process()
            time.sleep(self.exam_attempt.duration_exam)

            event_queue.put(
                {
                    "examiner_name": self.examiner.name,
                    "student_name": student.name,
                    "status": "end_exam",
                    "time_work_all": self.exam_attempt.duration_exam,
                    "result_exam": self.exam_attempt.result_exam,
                }
            )

            event_queue.put(
                {
                    "examiner_name": self.examiner.name,
                    "student_name": "-",
                    "status": "free",
                }
            )

            if (
                self.examiner.time_work >= self.examiner.time_work_max
                and cnt_student_queue.value > 0
            ):
                self.exam_attempt.was_lunch = True
                event_queue.put(
                    {
                        "examiner_name": self.examiner.name,
                        "status": "start_lunch",
                    }
                )
                self._lunch()
                event_queue.put(
                    {
                        "examiner_name": self.examiner.name,
                        "status": "end_lunch",
                        "time_lunch": self.time_for_lunch,
                    }
                )

            result_queue.put(self.exam_attempt)

        event_queue.put({"examiner_name": self.examiner.name, "status": "end_work"})


class ExamRunnerMultiprocess:
    """
    Управляет многопроцессным проведением экзамена.
    Для каждого экзаменатора создается свой отдельный процесс,
    контроль за текущим состоянием выполняется через очереди.
    """

    def __init__(self, exam_data: ExamData) -> None:
        self.exam_data = exam_data
        self.word_selection = WordSelection()
        self.exam_attempts: list[ExamAttempt] = []
        self.live_report = LiveReport()
        self.event_handler = EventHandler()
        self.student_queue: mp.Queue[Student | None] = mp.Queue()
        self.result_queue: mp.Queue[ExamAttempt] = mp.Queue()
        self.event_queue: mp.Queue[ExamEvent] = mp.Queue()
        self.procs: list[mp.Process] = []
        self.examiners = [examiner for examiner in self.exam_data.examiners]
        self.examiner_status: dict[str, ExaminerStatus] = {}
        self.students_status: dict[str, str] = {}
        self.finished_worker = 0
        self.cnt_student_queue = mp.Value("i", len(self.exam_data.students))

    def _student_queue_put(self, list_student_queue: list[Student]) -> None:
        for student in list_student_queue:
            self.student_queue.put(student)

    def run(self, stdscr) -> float:
        """Подготавливает начальные состояния участников экзамена,
            запускает процессы экзаменаторов и обрабатывает их события,
            передавая данные в отчет.

        Returns:
            float: Время с начала и до окончания экзамена.
        """
        start_time = time.time()

        self._student_queue_put(self.exam_data.student_queue)

        for student in self.exam_data.students:
            self.students_status[student.name] = "queue"

        for examiner in self.exam_data.examiners:
            self.examiner_status[examiner.name] = {
                "student_name": "-",
                "status": "free",
                "time_lunch": 0.0,
                "total_student": 0,
                "failed_student": 0,
                "cnt_lunch": 0,
                "time_work_all": 0.0,
                "start_exam_time": 0.0,
            }

            examiner_worker = ExaminerWorker(
                self.exam_data.bank_questions,
                examiner,
                self.word_selection,
            )

            p = mp.Process(
                target=examiner_worker.run,
                args=(
                    self.student_queue,
                    self.result_queue,
                    self.event_queue,
                    self.cnt_student_queue,
                ),
            )
            p.start()
            self.procs.append(p)

        for _ in self.procs:
            self.student_queue.put(None)

        while self.finished_worker < len(self.procs):
            # 1. Вычисляем текущее астрономическое время экзамена
            current_elapsed = time.time() - start_time

            # 2. Вычитываем все накопившиеся события БЕЗ БЛОКИРОВКИ
            while True:
                try:
                    event = self.event_queue.get_nowait()
                    self.examiner_status, self.students_status = (
                        self.event_handler.update_status(
                            event,
                            self.examiner_status,
                            self.students_status,
                            current_elapsed,
                        )
                    )
                    if "status" in event and event["status"] == "end_work":
                        self.finished_worker += 1
                except queue.Empty:
                    # Если новых событий в очереди нет выходим из цикла чтения
                    break

            # 3. Печатаем кадр и передаем текущее время
            self.live_report.print_report(
                stdscr,
                self.examiner_status,
                self.students_status,
                current_elapsed,
                self.cnt_student_queue.value,
            )

            # 4. Задержка 0.01 секунды для создания плавного 100 FPS "кадра"
            time.sleep(0.01)

        for _ in range(len(self.exam_data.students)):
            self.exam_attempts.append(self.result_queue.get())

        for p in self.procs:
            p.join()

        return current_elapsed
