"""
Загружает данные из файлов, создает объекты студентов,экзаменаторов,
объект банка вопросов и формирует очередь студентов.

Returns:
    _type_: _description_
"""

from models import Student, Examiner
from exam import BankQuestions


class ExamData:
    """
    Хранит объекты экзаменаторов, студентов, банк вопросов и очередь студентов.
    """

    def __init__(
        self, examiners_file: str, students_file: str, questions_file: str
    ) -> None:

        self.examiners = self._init_class_people(Examiner, examiners_file)
        self.students = self._init_class_people(Student, students_file)
        self.bank_questions = self._init_class_questions(questions_file)
        self.student_queue = [student for student in self.students]

    def _load_data(self, file: str) -> list[str]:
        """
        Читает данные из файла и возвращает их списком.

        Args:
            file (str): путь к файлу.

        Returns:
            list[str]: строки, прочитанные из файла.
        """
        result = []

        with open(file, "r", encoding="utf-8") as file_input:
            for line in file_input:
                if line:
                    result.append(line.strip())

        return result

    def _parse_person(self, file_input: list[str]) -> list[list[str]]:
        """
        Преобразует список строк во вложенные списки [Имя, пол].

        Args:
            file_input (list[str]): Список строк исходных данных.

        Returns:
            list[list[str]]: Вложенные списки [Имя, пол].
        """
        result = []

        for el in file_input:
            if el:
                name, gender = el.split()
                if gender == "М" or gender == "Ж":
                    result.append([name, gender])

        return result

    def _init_class_people(
        self, target_class: type[Student] | type[Examiner], file: str
    ) -> list[Student | Examiner]:
        """
        Создает объекты студентов или экзаменаторов.

        Args:
            target_class (Student | Examiner):
                Класс студента или экзаменатора.
            file (str): Путь к файлу с данными.

        Returns:
            list[Student | Examiner]: Cписок объектов класса.
        """
        file_input = self._load_data(file)

        data = self._parse_person(file_input)
        result = []
        for el in data:
            result.append(target_class(el[0], el[1]))

        return result

    def _init_class_questions(self, file: str) -> BankQuestions:
        """
        Создает объект банка вопросов

        Args:
            file (str): Путь к файлу с данными.

        Returns:
            BankQuestions: Объект класса BankQuestions.
        """
        file_input = {line: 0 for line in self._load_data(file)}
        if len(file_input) < 3:
            raise ValueError("Недостаточное количество вопросов")

        return BankQuestions(file_input)
