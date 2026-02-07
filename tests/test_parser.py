"""Тесты для модуля парсера"""

import pytest
from bs4 import BeautifulSoup
from src.parser import CourseParser, Subcourse


class TestCourseParser:
    """Тесты для класса CourseParser"""

    def test_init(self):
        """Тест инициализации парсера"""
        parser = CourseParser()
        assert parser.session is not None
        assert "User-Agent" in parser.session.headers

    def test_clean_list_item_title(self):
        """Тест очистки названия элемента списка"""
        parser = CourseParser()
        assert parser._clean_list_item_title("1. Название") == "Название"
        assert parser._clean_list_item_title("1) Название") == "Название"
        assert parser._clean_list_item_title("1.1. Название") == "Название"
        assert parser._clean_list_item_title("Название") == "Название"

    def test_find_go_link(self):
        """Тест поиска ссылки 'Перейти'"""
        parser = CourseParser()
        html = """
        <div>
            <h3>Заголовок</h3>
            <p><a href="/link">Перейти</a></p>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        h3 = soup.find("h3")
        link = parser._find_go_link(h3)
        assert link == "/link"

    def test_find_plan_section(self):
        """Тест поиска раздела плана"""
        parser = CourseParser()
        html = """
        <div>
            <h2>Краткий план раздела</h2>
            <ol>
                <li>Пункт 1</li>
                <li>Пункт 2</li>
            </ol>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        section = parser._find_plan_section(soup)
        assert section is not None

    def test_find_ordered_list(self):
        """Тест поиска нумерованного списка"""
        parser = CourseParser()
        html = """
        <div>
            <h2>Краткий план раздела</h2>
            <ol>
                <li>Пункт 1</li>
                <li>Пункт 2</li>
            </ol>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        section = parser._find_plan_section(soup)
        ol = parser._find_ordered_list(section)
        assert ol is not None
        assert ol.name == "ol"


class TestSubcourse:
    """Тесты для структуры Subcourse"""

    def test_subcourse_creation(self):
        """Тест создания Subcourse"""
        subcourse = Subcourse(
            title="Тест",
            url="http://example.com",
            level=1,
        )
        assert subcourse.title == "Тест"
        assert subcourse.url == "http://example.com"
        assert subcourse.level == 1
