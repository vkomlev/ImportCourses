"""Тесты для главного модуля"""

import pytest
from unittest.mock import Mock, patch
from src.main import extract_main_course_title, parse_courses


class TestExtractMainCourseTitle:
    """Тесты для функции extract_main_course_title"""

    @patch("src.main.CourseParser")
    def test_extract_title_from_title_tag(self, mock_parser_class):
        """Тест извлечения названия из тега title"""
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser

        html = '<html><head><title>Python для ЕГЭ - Школа Виктора Комлева</title></head></html>'
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        mock_parser._fetch_page.return_value = soup

        title = extract_main_course_title(mock_parser, "http://example.com")
        assert "Python для ЕГЭ" in title or title == "Python для ЕГЭ"

    @patch("src.main.CourseParser")
    def test_extract_title_from_h1(self, mock_parser_class):
        """Тест извлечения названия из h1"""
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser

        html = '<html><body><h1>Python для ЕГЭ</h1></body></html>'
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        mock_parser._fetch_page.return_value = soup

        title = extract_main_course_title(mock_parser, "http://example.com")
        assert title == "Python для ЕГЭ"


class TestParseCourses:
    """Тесты для функции parse_courses"""

    @patch("src.main.CourseParser")
    @patch("src.main.generate_uid")
    @patch("src.main.reset_uid_generator")
    def test_parse_courses_basic(self, mock_reset, mock_generate_uid, mock_parser_class):
        """Базовый тест парсинга курсов"""
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser

        # Мокируем данные
        from src.parser import Subcourse
        mock_subcourse = Subcourse(
            title="Основы Python",
            url="http://example.com/basics",
            level=1,
        )

        mock_parser.parse_main_page.return_value = [mock_subcourse]
        mock_parser.parse_subcourse_page.return_value = []
        mock_parser._fetch_page.return_value = None
        mock_parser.extract_description.return_value = None

        mock_generate_uid.side_effect = lambda title, parent: f"{parent}-{title.lower().replace(' ', '-')}"

        courses = parse_courses("http://example.com", "MAIN-UID")

        assert len(courses) == 1
        assert courses[0]["title"] == "Основы Python"
        assert courses[0]["parent_course_uid"] == "MAIN-UID"
