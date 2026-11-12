from data import ExamData
from runner import ExamRunnerMultiprocess
from reports import FinishReport
import curses


def main(stdscr) -> None:
    exam_data = ExamData("./examiners.txt", "./students.txt", "./questions.txt")

    exam = ExamRunnerMultiprocess(exam_data)

    end_time = exam.run(stdscr)

    report_printer = FinishReport(exam.exam_attempts, end_time)
    report_printer.print_report(stdscr)


if __name__ == "__main__":
    curses.wrapper(main)
