"""Тесты для модуля записи в Excel"""

import os
import tempfile
from pathlib import Path
from src.excel_writer import ExcelWriter, write_courses_to_excel
from openpyxl import load_workbook


class TestExcelWriter:
    """Тесты для класса ExcelWriter"""

    def test_init(self):
        """Тест инициализации writer"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            writer = ExcelWriter(tmp.name)
            assert writer.output_path == tmp.name
            assert writer.workbook is not None
            assert writer.worksheet is not None
            writer.workbook.close()
            os.unlink(tmp.name)

    def test_write_headers(self):
        """Тест записи заголовков"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            writer = ExcelWriter(tmp.name)
            writer._write_headers()

            # Проверяем заголовки
            assert writer.worksheet.cell(row=1, column=1).value == "course_uid"
            assert writer.worksheet.cell(row=1, column=2).value == "title"
            assert writer.worksheet.cell(row=1, column=1).font.bold is True
            writer.workbook.close()
            os.unlink(tmp.name)

    def test_format_bool(self):
        """Тест форматирования булевых значений"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            writer = ExcelWriter(tmp.name)
            assert writer._format_bool(True) == "true"
            assert writer._format_bool(False) == "false"
            assert writer._format_bool("true") == "true"
            assert writer._format_bool("false") == "false"
            assert writer._format_bool("1") == "true"
            assert writer._format_bool("0") == "false"
            assert writer._format_bool("yes") == "true"
            assert writer._format_bool("no") == "false"
            assert writer._format_bool("да") == "true"
            assert writer._format_bool("нет") == "false"
            assert writer._format_bool(None) == "false"
            writer.workbook.close()
            os.unlink(tmp.name)

    def test_write_course(self):
        """Тест записи курса"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            writer = ExcelWriter(tmp.name)
            writer._write_headers()

            course = {
                "course_uid": "TEST-001",
                "title": "Тестовый курс",
                "description": "Описание",
                "access_level": "manual_check",
                "parent_course_uid": "",
                "order_number": "",
                "required_courses_uid": "",
                "is_required": "false",
            }

            writer._write_course(course)

            # Проверяем данные
            assert writer.worksheet.cell(row=2, column=1).value == "TEST-001"
            assert writer.worksheet.cell(row=2, column=2).value == "Тестовый курс"
            assert writer.worksheet.cell(row=2, column=4).value == "manual_check"
            writer.workbook.close()
            os.unlink(tmp.name)

    def test_write_courses(self):
        """Тест записи списка курсов"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            courses = [
                {
                    "course_uid": "TEST-001",
                    "title": "Курс 1",
                    "description": "",
                    "access_level": "manual_check",
                    "parent_course_uid": "",
                    "order_number": "",
                    "required_courses_uid": "",
                    "is_required": "false",
                },
                {
                    "course_uid": "TEST-002",
                    "title": "Курс 2",
                    "description": "",
                    "access_level": "manual_check",
                    "parent_course_uid": "TEST-001",
                    "order_number": 1,
                    "required_courses_uid": "",
                    "is_required": "false",
                },
            ]

            writer = ExcelWriter(tmp.name)
            writer.write_courses(courses)

            # Проверяем, что файл создан
            assert os.path.exists(tmp.name)

            # Загружаем и проверяем содержимое
            wb = load_workbook(tmp.name)
            ws = wb.active

            assert ws.cell(row=1, column=1).value == "course_uid"
            assert ws.cell(row=2, column=1).value == "TEST-001"
            assert ws.cell(row=3, column=1).value == "TEST-002"
            assert ws.cell(row=3, column=5).value == "TEST-001"  # parent_course_uid
            assert ws.cell(row=3, column=6).value == 1  # order_number
            wb.close()
            os.unlink(tmp.name)


class TestWriteCoursesToExcelFunction:
    """Тесты для функции write_courses_to_excel"""

    def test_write_courses_to_excel(self):
        """Тест функции write_courses_to_excel"""
        courses = [
            {
                "course_uid": "TEST-001",
                "title": "Курс 1",
                "description": "",
                "access_level": "manual_check",
                "parent_course_uid": "",
                "order_number": "",
                "required_courses_uid": "",
                "is_required": "false",
            },
        ]

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            output_path = write_courses_to_excel(courses, tmp.name)
            assert output_path == tmp.name
            assert os.path.exists(output_path)
            # Файл уже закрыт функцией write_courses_to_excel
            os.unlink(tmp.name)
