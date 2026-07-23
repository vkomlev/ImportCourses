"""Главный модуль парсера курсов"""

import argparse
import logging
import sys
from typing import List, Dict, Any, Optional, Tuple

from .config import (
    DEFAULT_ACCESS_LEVEL,
    MAIN_COURSE_UID,
    MAIN_COURSE_TITLE,
)
from .excel_writer import write_courses_to_excel, write_materials_to_excel
from .parser import CourseParser, RawMaterial, Subcourse
from .uid_generator import UIDGenerator, generate_uid, reset_uid_generator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


def extract_main_course_title(parser: CourseParser, url: str) -> str:
    """
    Извлечение названия главного курса из страницы

    Args:
        parser: Парсер курсов
        url: URL главной страницы

    Returns:
        Название курса
    """
    soup = parser._fetch_page(url)
    if not soup:
        return MAIN_COURSE_TITLE or "Главный курс"

    # Ищем заголовок страницы
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)
        # Убираем суффикс сайта, если есть
        if " - " in title:
            title = title.split(" - ")[0]
        return title

    # Ищем h1
    h1_tag = soup.find("h1")
    if h1_tag:
        return h1_tag.get_text(strip=True)

    return MAIN_COURSE_TITLE or "Главный курс"


def _material_title_matches_subcourse(link_text: str, subcourse_title: str) -> bool:
    """
    Проверка совпадения текста ссылки с названием подкурса (полное или частичное).

    Args:
        link_text: Текст ссылки на материал
        subcourse_title: Название подкурса второго уровня

    Returns:
        True если есть совпадение (в любую сторону)
    """
    a = (link_text or "").strip().lower()
    b = (subcourse_title or "").strip().lower()
    if not a or not b:
        return False
    return b in a or a in b


def _unique_external_uid_for_course(
    title: str, course_uid: str, used: Dict[str, set], uid_gen: UIDGenerator, max_len: int = 80
) -> str:
    """Генерация уникального external_uid для материала в рамках курса."""
    slug = uid_gen.create_slug(title)
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip("-")
    used_in_course = used.setdefault(course_uid, set())
    external_uid = slug
    counter = 2
    while external_uid in used_in_course:
        suffix = f"-{counter}"
        external_uid = (slug[: max_len - len(suffix)] if len(slug) + len(suffix) > max_len else slug) + suffix
        counter += 1
    used_in_course.add(external_uid)
    return external_uid


def parse_courses(
    url: str, main_course_uid: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Парсинг курсов и материалов с сайта.

    Args:
        url: URL главной страницы курса
        main_course_uid: UID главного курса (если None, используется из config)

    Returns:
        (список курсов, список материалов для выгрузки)
    """
    main_uid = main_course_uid or MAIN_COURSE_UID
    reset_uid_generator()
    parser = CourseParser()
    uid_gen = UIDGenerator()
    used_external_uids: Dict[str, set] = {}
    order_position_by_course: Dict[str, int] = {}

    main_title = extract_main_course_title(parser, url)
    logger.info(f"Главный курс: {main_title} (UID: {main_uid})")

    logger.info("Парсинг главной страницы...")
    level1_subcourses = parser.parse_main_page(url)
    logger.info(f"Найдено подкурсов первого уровня: {len(level1_subcourses)}")

    all_courses: List[Dict[str, Any]] = []
    all_materials: List[Dict[str, Any]] = []
    order_number_l1 = 1

    for subcourse_l1 in level1_subcourses:
        subcourse_l1_uid = generate_uid(subcourse_l1.title, main_uid)
        description = None
        level2_subcourses = []
        raw_materials: List[RawMaterial] = []

        if subcourse_l1.url:
            soup = parser._fetch_page(subcourse_l1.url)
            if soup:
                try:
                    description = parser.extract_description(soup)
                except Exception as e:
                    logger.warning(f"Не удалось извлечь описание для {subcourse_l1.title}: {e}")
                level2_subcourses = parser.parse_subcourse_page(subcourse_l1.url, soup=soup)
                raw_materials = parser.parse_materials_sections(soup, subcourse_l1.url)
            logger.info(f"Парсинг страницы подкурса: {subcourse_l1.url}")
        else:
            logger.info(f"Нет URL для подкурса {subcourse_l1.title}, пропуск страницы и материалов")

        course_l1 = {
            "course_uid": subcourse_l1_uid,
            "title": subcourse_l1.title,
            "description": description or "",
            "access_level": DEFAULT_ACCESS_LEVEL,
            "parent_course_uid": main_uid,
            "order_number": order_number_l1,
            "required_courses_uid": "",
            "is_required": "false",
        }
        all_courses.append(course_l1)
        logger.info(f"Добавлен курс уровня 1: {subcourse_l1.title} ({subcourse_l1_uid}), порядок: {order_number_l1}")
        order_number_l1 += 1

        # Список подкурсов второго уровня с уже сгенерированными UID для привязки материалов
        level2_with_uid: List[Tuple[str, str]] = []
        order_number_l2 = 1
        for subcourse_l2 in level2_subcourses:
            subcourse_l2_uid = generate_uid(subcourse_l2.title, subcourse_l1_uid)
            level2_with_uid.append((subcourse_l2.title, subcourse_l2_uid))
            course_l2 = {
                "course_uid": subcourse_l2_uid,
                "title": subcourse_l2.title,
                "description": subcourse_l2.description or "",
                "access_level": DEFAULT_ACCESS_LEVEL,
                "parent_course_uid": subcourse_l1_uid,
                "order_number": order_number_l2,
                "required_courses_uid": "",
                "is_required": "false",
            }
            all_courses.append(course_l2)
            logger.debug(f"Добавлен курс уровня 2: {subcourse_l2.title} ({subcourse_l2_uid}), порядок: {order_number_l2}")
            order_number_l2 += 1

        # Привязка материалов: совпадение текста ссылки с названием подкурса → к подкурсу, иначе → к родителю.
        # Нумерация order_position ведётся отдельно для каждого course_uid (без пропусков в рамках курса).
        for raw in raw_materials:
            course_uid = subcourse_l1_uid
            for sub_title, sub_uid in level2_with_uid:
                if _material_title_matches_subcourse(raw.title, sub_title):
                    course_uid = sub_uid
                    break
            pos = order_position_by_course.get(course_uid, 1)
            order_position_by_course[course_uid] = pos + 1
            external_uid = _unique_external_uid_for_course(
                raw.title, course_uid, used_external_uids, uid_gen
            )
            all_materials.append({
                "course_uid": course_uid,
                "external_uid": external_uid,
                "title": raw.title,
                "type": raw.material_type,
                "url": raw.url,
                "description": "",
                "caption": "",
                "order_position": pos,
                "is_active": "true",
            })
        if raw_materials:
            logger.info(f"Добавлено материалов с страницы {subcourse_l1.title}: {len(raw_materials)}")

    return all_courses, all_materials


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description="Парсер курсов с сайта victor-komlev.ru"
    )
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="URL главной страницы курса",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Путь к выходному XLSX файлу курсов (по умолчанию: output/courses_<timestamp>.xlsx)",
    )
    parser.add_argument(
        "--output-materials",
        type=str,
        default=None,
        help="Путь к XLSX файлу материалов (по умолчанию: output/materials_<timestamp>.xlsx)",
    )
    parser.add_argument(
        "--main-uid",
        type=str,
        default=None,
        help=f"UID главного курса (по умолчанию: {MAIN_COURSE_UID})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Включить подробное логирование",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        logger.info(f"Начало парсинга: {args.url}")
        logger.info(f"UID главного курса: {args.main_uid or MAIN_COURSE_UID}")

        courses, materials = parse_courses(args.url, args.main_uid)

        if not courses:
            logger.warning("Не найдено ни одного курса!")
            sys.exit(1)

        logger.info(f"Всего найдено курсов: {len(courses)}")
        logger.info(f"Всего найдено материалов: {len(materials)}")

        output_path = write_courses_to_excel(courses, args.output)
        logger.info(f"Курсы сохранены: {output_path}")

        if materials:
            materials_path = write_materials_to_excel(materials, args.output_materials)
            logger.info(f"Материалы сохранены: {materials_path}")

        logger.info("Парсинг завершен успешно!")

    except KeyboardInterrupt:
        logger.info("Парсинг прерван пользователем")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ошибка при парсинге: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
