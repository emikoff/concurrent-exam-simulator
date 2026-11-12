from models import ExamAttempt, ExaminerStatus, ExaminerSummary
import curses


class TablePrinter:
    """Формирует и печатает таблицу.

    Raises:
        ValueError: Инициирует ошибку в случе неверных входящих данных.
    """

    STATUS = {
        "start_exam": "Очередь",
        "end_exam": "Свободен",
        "free": "Свободен",
        "start_lunch": "Обед",
        "end_lunch": "Свободен",
        "end_work": "Закончил",
        "passed": "Сдал",
        "failed": "Провалил",
        "queue": "Очередь",
    }

    STATUS_PRIORITY = {
        "queue": 0,
        "start_exam": 0,
        "passed": 2,
        "failed": 3,
    }

    def _row_table(
        self,
        data: list[str],
        max_len_column: list[int],
        frame: str = "|",
        symbol: str = " ",
    ) -> str:
        """Формирует строку таблицы

        Args:
            data (list[str]): Список данных для вывода в таблицу
            max_len_column (list[int]): Список максимальных длин колонок
            frame (str, optional): Разделитель таблицы. Defaults to "|".
            symbol (str, optional): Символ заполнения ячейки пустого места. Defaults to " ".

        Returns:
            str: _description_
        """
        result = [frame]

        for i in range(len(data)):
            result.append(self._column(data[i], frame, max_len_column[i], symbol))
        return "".join(result)

    def _column(self, data: str, frame: str, max_len: int, symbol: str) -> str:
        """Заполненяет одну ячейку таблицы

        Args:
            data (str): Даанные для вставки в ячейку
            frame (str): Разделитель таблицы.
            max_len (int): Максимальная ширина ячейки.
            symbol (str): Символ заполнения ячейки пустого места.

        Returns:
            str: Сформированная ячейка табличной строки.
        """
        if len(data) > max_len:
            data = data[: max_len - 3] + "..."

        return f"{symbol}{data}{symbol * (max_len - len(data) + 1)}{frame}"

    def _print_table(self, data: list[list[str]], header: dict[str, int]) -> str:
        """Провереяет корректнось количества строк, отправляет данные
        для печати шапки и тела таблицы.

        Args:
            data (list[list[str]]): Данные для печати в таблице
            header (dict[str, int]): Заголовочная информация для шапки таблицы

        Raises:
            ValueError: Ошибка в количестве переданных аргументом

        Returns:
            str: Собранную таблицу из шапки и тела.
        """

        for row in data:
            if len(row) != len(header):
                raise ValueError(
                    f"Неверное количество\n\tожидается {len(header)} получили {len(row)} столбца\n\t{row}"
                )

        max_len_column, line, text = self._print_header(header)
        text += self._print_body(data, max_len_column) + line + "\n"

        return text

    def _print_body(self, data: list[list[str]], max_len_column: list[int]) -> str:
        """Печатает тело таблицы.

        Args:
            data (list[list[str]]): Данные для печати таблицы.
            max_len_column (list[int]): Максимальная ширина ячеек таблицы.

        Returns:
            str: Тело таблицы.
        """
        result = ""

        for row in data:
            result += self._row_table(row, max_len_column) + "\n"

        return result

    def _print_header(self, header: dict[str, int]) -> tuple[list[int], str, str]:
        """Печатает шапку таблицы.

        Args:
            header (dict[str, int]): Заголовочная информация таблицы

        Returns:
            tuple[list[int], str]: Максимальная длинна ячеек таблицы,
                строка разделителя таблицы и шапка таблицы.
        """
        max_len_column: list[int] = []
        header_cells: list[str] = []

        for txt, len_col in header.items():
            max_len_column.append(len_col)
            header_cells.append(txt)

        line_symbol = "-"
        line_frame = "+"
        line_data = [""] * len(header_cells)

        line = self._row_table(line_data, max_len_column, line_frame, line_symbol)
        header_row = self._row_table(header_cells, max_len_column)

        text = line + "\n" + header_row + "\n" + line + "\n"

        return max_len_column, line, text


class LiveReport(TablePrinter):
    """
    Выводит статус проведения экзамена в реальном времени.
    """

    def print_report(
        self,
        stdscr,
        examiner_status: dict[str, ExaminerStatus],
        student_status: dict[str, str],
        global_time: float,
        cnt_student_queue: int,
    ) -> None:
        """
        Получает текущие данные о статусе проведения экзамена,
        о студентах и экзаменаторах и печатает их в терминал.

        Args:
            stdscr: Экран отчета.
            examiner_status (dict[str, dict[str, str | int | float]]): статус экзаменаторов
            student_status (dict[str, str]): статус студентов
            global_time (float): Время, прошедшее с начала работы программы
        """

        sorted_students = sorted(
            student_status.items(),
            key=lambda item: self.STATUS_PRIORITY.get(item[1], 99),
        )

        header1 = {"Студент": 10, "Статус": 8}
        body1 = [[name, self.STATUS[status]] for name, status in sorted_students]

        header2 = {
            "Экзаменатор": 11,
            "Текущий студент": 15,
            "Всего студентов": 15,
            "Завалил": 7,
            "Время работы": 12,
            # "Статус": 8,
            # "кол-во обедов": 13,
            # "Время обеда": 11,
        }
        body2 = [
            [
                examiner_name,
                data["student_name"],
                str(data["total_student"]),
                str(data["failed_student"]),
                (
                    f"{data['time_work_all'] + (global_time - data["start_exam_time"]):.2f}"
                    if data["status"] == "start_exam"
                    else f"{data['time_work_all']:.2f}"
                ),
                # self.STATUS[data["status"]],
                # str(data["cnt_lunch"]),
                # str(data["time_lunch"]),
            ]
            for examiner_name, data in examiner_status.items()
        ]

        table1 = self._print_table(body1, header1)
        table2 = self._print_table(body2, header2)

        info = [
            f"Осталось в очереди: {cnt_student_queue} из {len(student_status)}",
            f"Время с момента начала экзамена: {global_time:.2f}",
        ]

        self.text = table1 + table2 + "\n".join(info)

        stdscr.erase()
        stdscr.addstr(0, 0, self.text)
        stdscr.refresh()


class FinishReport(TablePrinter):
    """
    Выводит результаты проведенных экзаменов.
    """

    def __init__(self, exam_attempts: list[ExamAttempt], end_time: float) -> None:
        self.exam_attempts = exam_attempts
        self.examiners_summary = self._examiners_summary()

        self.best_student = self._best_student()
        self.best_examiner = self._best_examiner()
        self.expelled_student = self._expelled_student()

        self.result_exams = self._result_exams()

        self.statistics_questions = self._statistics_questions()
        self.best_question = self._best_question()
        self.end_time = end_time

    def print_report(self, stdscr) -> None:
        """
        Печатает результаты проведеных экзаменов в терминал.

        Args:
            stdscr: Экран отчета.
        """

        student_status = {
            exam_attempt.student.name: exam_attempt.student.status
            for exam_attempt in self.exam_attempts
        }

        sorted_students = sorted(
            student_status.items(),
            key=lambda item: self.STATUS_PRIORITY.get(item[1], 99),
        )

        header1 = {"Студент": 10, "Статус": 8}
        body1 = [[name, self.STATUS[status]] for name, status in sorted_students]

        header2 = {
            "Экзаменатор": 11,
            "Всего студентов": 15,
            "Завалил": 7,
            "Время работы": 12,
            # "кол-во обедов": 13,
            # "Время обеда": 11,
        }
        body2 = [
            [
                examiner_name,
                str(data["total_student"]),
                str(data["failed_student"]),
                "{:.2f}".format(data["time_work_all"]),
                # str(data["cnt_lunch"]),
                # "{:.2f}".format(data["time_lunch"]),
            ]
            for examiner_name, data in self.examiners_summary.items()
        ]

        table1 = self._print_table(body1, header1)
        table2 = self._print_table(body2, header2)

        info = [
            f"Время с момента начала экзамена и до момента и его завершения: {self.end_time: .2f}",
            f"Имена лучших студентов: {self.best_student}",
            f"Имена лучших экзаменаторов:  {self.best_examiner}",
            f"Имена студентов, которых после экзамена отчислят: {self.expelled_student}",
            f"Лучшие вопросы: {self.best_question}",
            f"Вывод: {self.result_exams}",
        ]

        self.text = table1 + table2 + "\n".join(info)

        stdscr.erase()
        stdscr.addstr(0, 0, self.text)
        stdscr.refresh()
        stdscr.getch()

    def _best_student(self) -> str:
        """
        Определяет лучших студентов.

        Returns:
            str: Имена студентов, которые сдали экзамен.
            быстрее остальных
        """
        result = []

        durations = [
            exam_attempt.student.duration_exam
            for exam_attempt in self.exam_attempts
            if exam_attempt.student.status == "passed"
        ]

        if not durations:
            return "нет студентов которые сдали"

        min_duration = min(durations)

        for exam_attempt in self.exam_attempts:
            if (
                exam_attempt.student.duration_exam == min_duration
                and exam_attempt.student.status == "passed"
            ):
                result.append(exam_attempt.student.name)

        return ", ".join(result)

    def _best_examiner(self) -> str:
        """
        Определяет лучших экзаменаторов

        Returns:
            str: Имена лучших экзаминаторов, у которые % сдавших
            экзамен студентов выше.
        """

        result: dict[float, list[str]] = {}
        for examiner_name, data in self.examiners_summary.items():
            if data["total_student"] != 0:
                key = data["failed_student"] / data["total_student"]
                if key not in result:
                    result[key] = []
                result[key].append(examiner_name)

        if result:
            return ", ".join(result[min(result)])

        return "нет лучших экзаменаторов"

    def _expelled_student(self) -> str:
        """
        Возвращает имена студентов которые подлежат отчислению.

        Returns:
            str: Имена студентов которые быстрее завалили экзамен.
        """
        result = []

        durations = [
            exam_attempt.student.duration_exam
            for exam_attempt in self.exam_attempts
            if exam_attempt.student.status == "failed"
        ]

        if not durations:
            return "На отчисление студентов нет"

        min_duration = min(durations)

        for exam_attempt in self.exam_attempts:
            if (
                exam_attempt.student.duration_exam == min_duration
                and exam_attempt.student.status == "failed"
            ):
                result.append(exam_attempt.student.name)

        return ", ".join(result)

    def _best_question(self) -> str:
        """
        Определяет лучшие вопросы

        Returns:
            str: Вопросы, на которые студенты дали больше всего правильных ответов.
        """
        result = []
        max_num = 1
        for key, val in self.statistics_questions.items():
            if val == max_num:
                result.append(key)
            elif val > max_num:
                result = [key]
                max_num = val

        if not result:
            return "лучших вопросов нет"

        return ", ".join(result)

    def _result_exams(self) -> str:
        """
        Экзамен удался если больше 85% студентов сдали экзамен положительно.

        Returns:
            str: "экзамен не удался" | "экзамен удался"
        """

        all_attempts = len(self.exam_attempts)
        good_attempts = 0
        for exam_attempt in self.exam_attempts:
            if exam_attempt.result_exam == "passed":
                good_attempts += 1

        return ["экзамен не удался", "экзамен удался"][
            (good_attempts / all_attempts) > 0.85 if all_attempts != 0 else False
        ]

    def _examiners_summary(self) -> dict[str, ExaminerSummary]:
        """Статистика экзаменаторов.

        Returns:
            dict[str, dict[str, int | float]]: total_student, failed_student,
            time_work_all, cnt_lunch, time_lunch
        """
        result: dict[str, ExaminerSummary] = {}

        for exam_attempt in self.exam_attempts:
            if exam_attempt.examiner.name not in result:
                result[exam_attempt.examiner.name] = {
                    "total_student": 0,
                    "failed_student": 0,
                    "time_work_all": 0.0,
                    "cnt_lunch": 0,
                    "time_lunch": 0.0,
                }

            result[exam_attempt.examiner.name]["total_student"] += 1
            if exam_attempt.result_exam == "failed":
                result[exam_attempt.examiner.name]["failed_student"] += 1
            result[exam_attempt.examiner.name][
                "time_work_all"
            ] += exam_attempt.duration_exam

            if exam_attempt.was_lunch:
                result[exam_attempt.examiner.name]["cnt_lunch"] += 1
                result[exam_attempt.examiner.name][
                    "time_lunch"
                ] += exam_attempt.lunch_duration

        return result

    def _statistics_questions(self) -> dict[str, int]:
        """
        Считает количество верных ответов на вопросы.

        Returns:
            dict[str, int]: количество правильных ответов на вопрос.
        """
        result = {}

        for exam_attempt in self.exam_attempts:
            for question, res in exam_attempt.statistics_questions.items():
                if question not in result:
                    result[question] = res
                else:
                    result[question] += res

        return result
