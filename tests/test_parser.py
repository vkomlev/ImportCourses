"""Тесты для модуля парсера"""

import pytest
from bs4 import BeautifulSoup
from src.parser import CourseParser, RawMaterial, Subcourse


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

    def test_find_section_by_header(self):
        """Поиск секции по заголовку (Текстовые уроки / Видеоуроки)"""
        parser = CourseParser()
        html = """
        <div>
            <h2>Текстовые уроки</h2>
            <p><a href="/lesson1">Урок 1</a></p>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        section = parser._find_section_by_header(soup, "Текстовые уроки")
        assert section is not None
        assert section.get_text(strip=True) == "Текстовые уроки"

    def test_parse_materials_sections(self):
        """Извлечение материалов из секций Текстовые уроки и Видеоуроки"""
        parser = CourseParser()
        html = """
        <div>
            <h2>Текстовые уроки</h2>
            <p><a href="https://example.com/lesson1">Урок 1</a></p>
            <h2>Видеоуроки</h2>
            <p><a href="https://example.com/video1">Видео 1</a></p>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        base = "https://example.com/page"
        materials = parser.parse_materials_sections(soup, base)
        assert len(materials) >= 1
        text_mats = [m for m in materials if m.material_type == "text"]
        video_mats = [m for m in materials if m.material_type == "video"]
        assert any(m.title == "Урок 1" and m.url for m in text_mats)
        assert any(m.title == "Видео 1" and m.url for m in video_mats)


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


class TestRawMaterial:
    """Тесты для структуры RawMaterial"""

    def test_raw_material_creation(self):
        """Создание RawMaterial"""
        m = RawMaterial(title="Урок", url="https://example.com/1", material_type="text")
        assert m.title == "Урок"
        assert m.url == "https://example.com/1"
        assert m.material_type == "text"
