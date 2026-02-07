"""Парсинг HTML страниц курсов"""

import logging
import time
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import (
    GO_LINK_TEXT,
    PLAN_SECTION_HEADER,
    REQUEST_TIMEOUT,
    RETRY_ATTEMPTS,
    RETRY_DELAY,
    USER_AGENT,
    H3_TAG,
)

logger = logging.getLogger(__name__)


@dataclass
class Subcourse:
    """Структура данных для подкурса"""

    title: str
    url: Optional[str] = None
    description: Optional[str] = None
    parent_uid: Optional[str] = None
    level: int = 1  # 1 - первый уровень, 2 - второй уровень


class CourseParser:
    """Парсер курсов с сайта"""

    def __init__(self):
        """Инициализация парсера"""
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Загрузка и парсинг HTML страницы

        Args:
            url: URL страницы

        Returns:
            BeautifulSoup объект или None при ошибке
        """
        for attempt in range(RETRY_ATTEMPTS):
            try:
                logger.info(f"Загрузка страницы: {url} (попытка {attempt + 1})")
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or "utf-8"
                return BeautifulSoup(response.text, "html.parser")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Ошибка при загрузке {url}: {e}")
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"Не удалось загрузить {url} после {RETRY_ATTEMPTS} попыток")
                    return None

    def parse_main_page(self, url: str) -> List[Subcourse]:
        """
        Парсинг главной страницы курса

        Извлекает заголовки h3 и ссылки "Перейти" под ними

        Args:
            url: URL главной страницы

        Returns:
            Список подкурсов первого уровня
        """
        soup = self._fetch_page(url)
        if not soup:
            return []

        subcourses = []
        h3_tags = soup.find_all(H3_TAG)

        logger.info(f"Найдено {len(h3_tags)} заголовков {H3_TAG}")

        for h3 in h3_tags:
            try:
                # Извлекаем текст заголовка
                title = h3.get_text(strip=True)
                if not title:
                    continue

                # Ищем ссылку "Перейти" после заголовка
                go_link = self._find_go_link(h3)

                if go_link:
                    # Преобразуем относительную ссылку в абсолютную
                    full_url = urljoin(url, go_link)
                    subcourse = Subcourse(
                        title=title,
                        url=full_url,
                        level=1,
                    )
                    subcourses.append(subcourse)
                    logger.info(f"Найден подкурс: {title} -> {full_url}")
                else:
                    logger.warning(f"Не найдена ссылка 'Перейти' для заголовка: {title}")

            except Exception as e:
                logger.error(f"Ошибка при обработке заголовка: {e}")
                continue

        return subcourses

    def _find_go_link(self, h3_tag) -> Optional[str]:
        """
        Поиск ссылки "Перейти" после заголовка h3

        Args:
            h3_tag: BeautifulSoup тег h3

        Returns:
            URL ссылки или None
        """
        # Ищем в следующих элементах после h3
        current = h3_tag.next_sibling

        # Проверяем следующие элементы (до 10 элементов вперед)
        for _ in range(10):
            if current is None:
                break

            # Если это тег, проверяем его и его содержимое
            if hasattr(current, "find_all"):
                # Ищем все ссылки в этом элементе
                links = current.find_all("a", string=lambda text: text and GO_LINK_TEXT in text)
                if links:
                    return links[0].get("href")

                # Также проверяем вложенные ссылки
                links = current.find_all("a", href=True)
                for link in links:
                    link_text = link.get_text(strip=True)
                    if GO_LINK_TEXT in link_text:
                        return link.get("href")

            current = current.next_sibling

        # Если не нашли в следующих элементах, ищем в родительском контейнере
        parent = h3_tag.parent
        if parent:
            # Ищем ссылку в том же контейнере
            links = parent.find_all("a", string=lambda text: text and GO_LINK_TEXT in text)
            if links:
                return links[0].get("href")

            # Ищем любую ссылку с текстом "Перейти" в родителе
            for link in parent.find_all("a", href=True):
                link_text = link.get_text(strip=True)
                if GO_LINK_TEXT in link_text:
                    return link.get("href")

        return None

    def parse_subcourse_page(self, url: str) -> List[Subcourse]:
        """
        Парсинг страницы подкурса

        Извлекает список (нумерованный или маркированный) под любым заголовком

        Args:
            url: URL страницы подкурса

        Returns:
            Список подкурсов второго уровня
        """
        soup = self._fetch_page(url)
        if not soup:
            return []

        # Сначала пытаемся найти список по стандартному заголовку "Краткий план раздела"
        plan_section = self._find_plan_section(soup)
        if plan_section:
            # Ищем список (ol или ul) после заголовка
            list_element = self._find_list_after_header(plan_section)
            if list_element:
                return self._extract_list_items(list_element, url)

        # Если не нашли по стандартному заголовку, ищем любой заголовок со списком
        list_element = self._find_any_list_with_header(soup)
        if list_element:
            return self._extract_list_items(list_element, url)

        logger.warning(f"Не найден список на странице {url}")
        return []

    def _extract_list_items(self, list_element, url: str) -> List[Subcourse]:
        """
        Извлечение элементов из списка (ol или ul)

        Args:
            list_element: Элемент списка (ol или ul)
            url: URL страницы (для логирования)

        Returns:
            Список подкурсов
        """
        subcourses = []
        list_items = list_element.find_all("li", recursive=False)

        logger.info(f"Найдено {len(list_items)} элементов в списке на странице {url}")

        for item in list_items:
            try:
                # Извлекаем текст элемента
                # Используем separator=' ' чтобы правильно обработать пробелы
                title = item.get_text(separator=' ', strip=True)
                if not title:
                    continue

                # Удаляем нумерацию в начале, если есть
                title = self._clean_list_item_title(title)
                
                # Нормализуем пробелы (множественные пробелы -> один)
                import re
                title = re.sub(r'\s+', ' ', title)
                # Убираем пробелы перед знаками препинания
                title = re.sub(r'\s+([.,:;!?])', r'\1', title)
                title = title.strip()

                if not title:
                    continue

                subcourse = Subcourse(
                    title=title,
                    level=2,
                )
                subcourses.append(subcourse)
                logger.debug(f"Найден подкурс уровня 2: {title}")

            except Exception as e:
                logger.error(f"Ошибка при обработке элемента списка: {e}")
                continue

        return subcourses

        for item in list_items:
            try:
                # Извлекаем текст элемента
                # Используем separator=' ' чтобы правильно обработать пробелы
                title = item.get_text(separator=' ', strip=True)
                if not title:
                    continue

                # Удаляем нумерацию в начале, если есть
                title = self._clean_list_item_title(title)
                
                # Нормализуем пробелы (множественные пробелы -> один)
                import re
                title = re.sub(r'\s+', ' ', title)
                # Убираем пробелы перед знаками препинания
                title = re.sub(r'\s+([.,:;!?])', r'\1', title)
                title = title.strip()

                if not title:
                    continue

                subcourse = Subcourse(
                    title=title,
                    level=2,
                )
                subcourses.append(subcourse)
                logger.debug(f"Найден подкурс уровня 2: {title}")

            except Exception as e:
                logger.error(f"Ошибка при обработке элемента списка: {e}")
                continue

        return subcourses

    def _find_plan_section(self, soup: BeautifulSoup):
        """
        Поиск раздела "Краткий план раздела"

        Args:
            soup: BeautifulSoup объект страницы

        Returns:
            Элемент заголовка или None
        """
        # Ищем заголовок с текстом "Краткий план раздела"
        # Проверяем разные уровни заголовков
        for tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            headers = soup.find_all(tag_name, string=lambda text: text and PLAN_SECTION_HEADER in text)
            if headers:
                # Возвращаем сам заголовок
                return headers[0]

        # Если не нашли заголовок, ищем по тексту в любом элементе
        elements = soup.find_all(string=lambda text: text and PLAN_SECTION_HEADER in text)
        for elem in elements:
            # Ищем родительский элемент, который является заголовком
            parent = elem.parent
            if parent and parent.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                return parent

        return None

    def _find_list_after_header(self, plan_header) -> Optional:
        """
        Поиск списка (ol или ul) после заголовка

        Args:
            plan_header: Элемент заголовка

        Returns:
            Тег <ol> или <ul> или None
        """
        if not plan_header:
            return None

        # Стратегия 1: Ищем список в следующих sibling элементах после заголовка
        current = plan_header
        for _ in range(50):
            # Переходим к следующему sibling
            if hasattr(current, "next_sibling"):
                current = current.next_sibling
            else:
                break

            if current is None:
                break

            # Пропускаем текстовые узлы и комментарии
            if not hasattr(current, "name"):
                continue

            # Если это <ol> или <ul>, возвращаем его
            if current.name in ["ol", "ul"]:
                return current

            # Если это контейнер, ищем список внутри (но не слишком глубоко)
            if hasattr(current, "find_all"):
                # Сначала проверяем прямых детей
                list_elem = current.find(["ol", "ul"], recursive=False)
                if list_elem:
                    return list_elem

        # Стратегия 2: Ищем все списки на странице и выбираем ближайший к заголовку
        soup = plan_header
        while soup and not isinstance(soup, BeautifulSoup):
            soup = soup.parent if hasattr(soup, "parent") else None
        
        if soup:
            # Находим все списки (ol и ul) на странице
            all_lists = soup.find_all(["ol", "ul"])
            if all_lists:
                # Находим ближайший список к нашему заголовку
                closest_list = None
                min_distance = float('inf')
                
                for list_elem in all_lists:
                    # Проверяем, что список идет после заголовка в DOM
                    if self._is_element_after(plan_header, list_elem):
                        # Вычисляем "расстояние" - количество элементов между ними
                        distance = self._calculate_dom_distance(plan_header, list_elem)
                        if distance < min_distance:
                            min_distance = distance
                            closest_list = list_elem
                
                if closest_list:
                    return closest_list
                
                # Если не нашли по порядку, возвращаем первый список после заголовка
                for list_elem in all_lists:
                    if self._is_element_after(plan_header, list_elem):
                        return list_elem

        return None

    def _find_any_list_with_header(self, soup: BeautifulSoup) -> Optional:
        """
        Поиск любого списка (ol или ul), который идет после заголовка в основном контенте

        Ищет все заголовки на странице и проверяет, есть ли после них список.
        Игнорирует списки в навигации и других служебных блоках.

        Args:
            soup: BeautifulSoup объект страницы

        Returns:
            Тег <ol> или <ul> или None
        """
        # Ищем основной контент страницы
        # Обычно это main, article, или div с классом содержащим content, post, entry
        main_content = None
        for selector in ["main", "article", "div.post", "div.entry", "div.content", 
                         "div.post-content", "div.entry-content"]:
            if "." in selector:
                tag, class_name = selector.split(".", 1)
                elements = soup.find_all(tag, class_=lambda x: x and class_name in str(x).lower())
            else:
                elements = soup.find_all(selector)
            
            if elements:
                main_content = elements[0]
                logger.debug(f"Найден основной контент: {selector}")
                break

        # Если не нашли специальный контейнер, используем весь soup
        search_area = main_content if main_content else soup

        # Ищем все заголовки в области поиска
        for tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            headers = search_area.find_all(tag_name)
            for header in headers:
                # Пропускаем заголовки в навигации
                if self._is_in_navigation(header):
                    continue
                
                # Проверяем, есть ли список после этого заголовка
                list_elem = self._find_list_after_header(header)
                if list_elem:
                    # Проверяем, что список не в навигации
                    if not self._is_in_navigation(list_elem):
                        logger.info(f"Найден список после заголовка '{header.get_text(strip=True)[:50]}'")
                        return list_elem

        return None

    def _is_in_navigation(self, element) -> bool:
        """
        Проверяет, находится ли элемент в навигации или других служебных блоках

        Args:
            element: Элемент для проверки

        Returns:
            True если элемент в навигации
        """
        if not element:
            return False

        # Проверяем родителей элемента
        current = element
        for _ in range(10):  # Проверяем до 10 уровней вверх
            if not current:
                break
            
            if hasattr(current, "name"):
                # Проверяем теги навигации
                if current.name in ["nav", "header", "aside", "footer"]:
                    return True
                
                # Проверяем классы, указывающие на навигацию
                if hasattr(current, "get") and current.get("class"):
                    classes = " ".join(current.get("class", [])).lower()
                    nav_keywords = ["nav", "menu", "header", "sidebar", "footer", "breadcrumb"]
                    if any(keyword in classes for keyword in nav_keywords):
                        return True

            if hasattr(current, "parent"):
                current = current.parent
            else:
                break

        return False

    def _find_ordered_list(self, plan_header) -> Optional:
        """
        Поиск нумерованного списка после заголовка "Краткий план раздела"

        Args:
            plan_header: Элемент заголовка с планом

        Returns:
            Тег <ol> или None
        """
        if not plan_header:
            return None

        # Стратегия 1: Ищем <ol> в следующих sibling элементах после заголовка
        current = plan_header
        for _ in range(50):  # Увеличиваем количество проверок
            # Переходим к следующему sibling
            if hasattr(current, "next_sibling"):
                current = current.next_sibling
            else:
                break

            if current is None:
                break

            # Пропускаем текстовые узлы и комментарии
            if not hasattr(current, "name"):
                continue

            # Если это <ol>, возвращаем его
            if current.name == "ol":
                return current

            # Если это контейнер, ищем <ol> внутри (но не слишком глубоко)
            if hasattr(current, "find_all"):
                # Сначала проверяем прямых детей
                ol = current.find("ol", recursive=False)
                if ol:
                    return ol

        # Стратегия 2: Ищем все <ol> на странице и выбираем ближайший к заголовку
        # Получаем soup из заголовка
        soup = plan_header
        while soup and not isinstance(soup, BeautifulSoup):
            soup = soup.parent if hasattr(soup, "parent") else None
        
        if soup:
            # Находим все <ol> на странице
            all_ol = soup.find_all("ol")
            if all_ol:
                # Находим ближайший <ol> к нашему заголовку
                # Проходим по DOM дереву от заголовка и ищем первый встреченный <ol>
                closest_ol = None
                min_distance = float('inf')
                
                for ol in all_ol:
                    # Проверяем, что список идет после заголовка в DOM
                    # Используем простую эвристику: ищем общий родитель и проверяем порядок
                    if self._is_element_after(plan_header, ol):
                        # Вычисляем "расстояние" - количество элементов между ними
                        distance = self._calculate_dom_distance(plan_header, ol)
                        if distance < min_distance:
                            min_distance = distance
                            closest_ol = ol
                
                if closest_ol:
                    return closest_ol
                
                # Если не нашли по порядку, возвращаем первый список после заголовка
                for ol in all_ol:
                    if self._is_element_after(plan_header, ol):
                        return ol

        return None

    def _is_element_after(self, first, second):
        """
        Проверяет, идет ли второй элемент после первого в DOM дереве

        Args:
            first: Первый элемент
            second: Второй элемент

        Returns:
            True если second идет после first
        """
        # Простая проверка: если у элементов общий родитель,
        # проверяем порядок siblings
        if first.parent == second.parent:
            current = first
            while current:
                if current == second:
                    return True
                if hasattr(current, "next_sibling"):
                    current = current.next_sibling
                else:
                    break
            return False
        
        # Если родители разные, проверяем через общих предков
        # Ищем общий родитель
        first_ancestors = []
        current = first
        while current:
            first_ancestors.append(current)
            current = current.parent if hasattr(current, "parent") else None
        
        current = second
        while current:
            if current in first_ancestors:
                # Нашли общего предка, проверяем порядок
                return True
            current = current.parent if hasattr(current, "parent") else None
        
        # Если не нашли общего предка или не можем определить порядок,
        # считаем что second идет после (эвристика)
        return True

    def _calculate_dom_distance(self, first, second):
        """
        Вычисляет примерное "расстояние" между элементами в DOM

        Args:
            first: Первый элемент
            second: Второй элемент

        Returns:
            Число, представляющее расстояние
        """
        distance = 0
        current = first
        
        # Считаем количество элементов между first и second
        while current and current != second:
            distance += 1
            if hasattr(current, "next_sibling"):
                current = current.next_sibling
            elif hasattr(current, "parent"):
                current = current.parent
            else:
                break
        
        return distance

    def _clean_list_item_title(self, title: str) -> str:
        """
        Очистка названия элемента списка от нумерации

        Args:
            title: Исходное название

        Returns:
            Очищенное название
        """
        # Удаляем нумерацию в начале (например, "1. ", "1) ", "1.1. ")
        import re

        title = re.sub(r"^\d+[\.\)]\s*", "", title)
        title = re.sub(r"^\d+\.\d+[\.\)]\s*", "", title)
        return title.strip()

    def extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Извлечение описания со страницы

        Args:
            soup: BeautifulSoup объект страницы

        Returns:
            Описание или None
        """
        # Ищем описание в различных местах
        # Например, первый параграф после заголовка
        paragraphs = soup.find_all("p", limit=5)
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Минимальная длина описания
                return text[:500]  # Ограничиваем длину

        return None
