"""Главный модуль парсера курсов"""

import argparse
import logging
import sys
from typing import List, Dict, Any, Optional

from .config import (
    DEFAULT_ACCESS_LEVEL,
    MAIN_COURSE_UID,
    MAIN_COURSE_TITLE,
)
from .excel_writer import write_courses_to_excel
from .parser import CourseParser, Subcourse
from .uid_generator import generate_uid, reset_uid_generator

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


def parse_courses(url: str, main_course_uid: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Парсинг курсов с сайта

    Args:
        url: URL главной страницы курса
        main_course_uid: UID главного курса (если None, используется из config)

    Returns:
        Список словарей с данными курсов
    """
    main_uid = main_course_uid or MAIN_COURSE_UID
    reset_uid_generator()

    parser = CourseParser()

    # Извлекаем название главного курса
    main_title = extract_main_course_title(parser, url)
    logger.info(f"Главный курс: {main_title} (UID: {main_uid})")

    # Парсим главную страницу
    logger.info("Парсинг главной страницы...")
    level1_subcourses = parser.parse_main_page(url)
    logger.info(f"Найдено подкурсов первого уровня: {len(level1_subcourses)}")

    # Формируем список всех курсов
    all_courses = []

    # Добавляем главный курс (опционально, если нужно)
    # main_course = {
    #     "course_uid": main_uid,
    #     "title": main_title,
    #     "description": "",
    #     "access_level": DEFAULT_ACCESS_LEVEL,
    #     "parent_course_uid": "",
    #     "required_courses_uid": "",
    #     "is_required": "false",
    # }
    # all_courses.append(main_course)

    # Обрабатываем подкурсы первого уровня
    order_number_l1 = 1  # Счетчик порядкового номера для подкурсов первого уровня
    
    for subcourse_l1 in level1_subcourses:
        # Генерируем UID для подкурса первого уровня
        subcourse_l1_uid = generate_uid(subcourse_l1.title, main_uid)

        # Извлекаем описание, если есть URL
        description = None
        if subcourse_l1.url:
            try:
                soup = parser._fetch_page(subcourse_l1.url)
                if soup:
                    description = parser.extract_description(soup)
            except Exception as e:
                logger.warning(f"Не удалось извлечь описание для {subcourse_l1.title}: {e}")

        # Добавляем подкурс первого уровня
        course_l1 = {
            "course_uid": subcourse_l1_uid,
            "title": subcourse_l1.title,
            "description": description or "",
            "access_level": DEFAULT_ACCESS_LEVEL,
            "parent_course_uid": main_uid,
            "order_number": order_number_l1,  # Порядковый номер подкурса у родителя
            "required_courses_uid": "",
            "is_required": "false",
        }
        all_courses.append(course_l1)
        logger.info(f"Добавлен курс уровня 1: {subcourse_l1.title} ({subcourse_l1_uid}), порядок: {order_number_l1}")
        order_number_l1 += 1

        # Парсим страницу подкурса для получения подкурсов второго уровня
        if subcourse_l1.url:
            logger.info(f"Парсинг страницы подкурса: {subcourse_l1.url}")
            level2_subcourses = parser.parse_subcourse_page(subcourse_l1.url)
            logger.info(f"Найдено подкурсов второго уровня: {len(level2_subcourses)}")

            # Обрабатываем подкурсы второго уровня
            order_number_l2 = 1  # Счетчик порядкового номера для подкурсов второго уровня
            
            for subcourse_l2 in level2_subcourses:
                # Генерируем UID для подкурса второго уровня
                subcourse_l2_uid = generate_uid(subcourse_l2.title, subcourse_l1_uid)

                # Добавляем подкурс второго уровня
                course_l2 = {
                    "course_uid": subcourse_l2_uid,
                    "title": subcourse_l2.title,
                    "description": subcourse_l2.description or "",
                    "access_level": DEFAULT_ACCESS_LEVEL,
                    "parent_course_uid": subcourse_l1_uid,
                    "order_number": order_number_l2,  # Порядковый номер подкурса у родителя
                    "required_courses_uid": "",
                    "is_required": "false",
                }
                all_courses.append(course_l2)
                logger.debug(f"Добавлен курс уровня 2: {subcourse_l2.title} ({subcourse_l2_uid}), порядок: {order_number_l2}")
                order_number_l2 += 1

    return all_courses


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
        help="Путь к выходному XLSX файлу (по умолчанию генерируется автоматически)",
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

        # Парсим курсы
        courses = parse_courses(args.url, args.main_uid)

        if not courses:
            logger.warning("Не найдено ни одного курса!")
            sys.exit(1)

        logger.info(f"Всего найдено курсов: {len(courses)}")

        # Записываем в Excel
        output_path = write_courses_to_excel(courses, args.output)
        logger.info(f"Парсинг завершен успешно!")
        logger.info(f"Результат сохранен в: {output_path}")

    except KeyboardInterrupt:
        logger.info("Парсинг прерван пользователем")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ошибка при парсинге: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
