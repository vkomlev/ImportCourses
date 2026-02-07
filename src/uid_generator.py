"""Генерация UID для курсов"""

import re
import unicodedata
from typing import Set
from transliterate import translit

from .config import UID_MAX_LENGTH, UID_SEPARATOR


class UIDGenerator:
    """Генератор уникальных идентификаторов для курсов"""

    def __init__(self):
        """Инициализация генератора"""
        self._used_uids: Set[str] = set()

    def reset(self):
        """Сброс списка использованных UID"""
        self._used_uids.clear()

    def transliterate(self, text: str) -> str:
        """
        Транслитерация русского текста в латиницу

        Args:
            text: Текст на русском языке

        Returns:
            Транслитерированный текст
        """
        try:
            # Пытаемся транслитерировать
            result = translit(text, "ru", reversed=True)
            return result
        except Exception:
            # Если transliterate не справился, используем простую замену
            return self._simple_transliterate(text)

    def _simple_transliterate(self, text: str) -> str:
        """
        Простая транслитерация (fallback)

        Args:
            text: Текст на русском языке

        Returns:
            Транслитерированный текст
        """
        # Базовая таблица транслитерации
        translit_map = {
            "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
            "е": "e", "ё": "yo", "ж": "zh", "з": "z", "и": "i",
            "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
            "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
            "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch",
            "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
            "э": "e", "ю": "yu", "я": "ya",
            "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D",
            "Е": "E", "Ё": "Yo", "Ж": "Zh", "З": "Z", "И": "I",
            "Й": "Y", "К": "K", "Л": "L", "М": "M", "Н": "N",
            "О": "O", "П": "P", "Р": "R", "С": "S", "Т": "T",
            "У": "U", "Ф": "F", "Х": "H", "Ц": "Ts", "Ч": "Ch",
            "Ш": "Sh", "Щ": "Sch", "Ъ": "", "Ы": "Y", "Ь": "",
            "Э": "E", "Ю": "Yu", "Я": "Ya",
        }

        result = []
        for char in text:
            if char in translit_map:
                result.append(translit_map[char])
            else:
                result.append(char)

        return "".join(result)

    def create_slug(self, text: str) -> str:
        """
        Создание slug из текста

        Args:
            text: Исходный текст

        Returns:
            Slug (lowercase, дефисы вместо пробелов, удаление спецсимволов)
        """
        # Транслитерация если есть русские символы
        if any("\u0400" <= char <= "\u04FF" for char in text):
            text = self.transliterate(text)

        # Нормализация Unicode (удаление диакритических знаков)
        text = unicodedata.normalize("NFKD", text)

        # Преобразование в lowercase
        text = text.lower()

        # Замена пробелов и подчеркиваний на дефисы
        text = re.sub(r"[\s_]+", UID_SEPARATOR, text)

        # Удаление всех символов кроме букв, цифр и дефисов
        text = re.sub(r"[^a-z0-9\-]", "", text)

        # Удаление множественных дефисов
        text = re.sub(r"-+", UID_SEPARATOR, text)

        # Удаление дефисов в начале и конце
        text = text.strip(UID_SEPARATOR)

        return text

    def generate_uid(self, title: str, parent_uid: str = None) -> str:
        """
        Генерация UID для курса

        Args:
            title: Название курса
            parent_uid: UID родительского курса (опционально)

        Returns:
            Уникальный UID
        """
        # Создаем slug из названия
        slug = self.create_slug(title)

        # Ограничиваем длину slug
        if len(slug) > UID_MAX_LENGTH:
            slug = slug[:UID_MAX_LENGTH]

        # Формируем UID с префиксом родителя
        if parent_uid:
            uid = f"{parent_uid}{UID_SEPARATOR}{slug}"
        else:
            uid = slug

        # Ограничиваем общую длину
        if len(uid) > UID_MAX_LENGTH:
            # Сокращаем slug часть
            max_slug_length = UID_MAX_LENGTH - len(parent_uid) - len(UID_SEPARATOR)
            slug = slug[:max_slug_length]
            uid = f"{parent_uid}{UID_SEPARATOR}{slug}"

        # Обрабатываем дубликаты
        uid = self._ensure_unique(uid)

        # Сохраняем использованный UID
        self._used_uids.add(uid)

        return uid

    def _ensure_unique(self, uid: str) -> str:
        """
        Обеспечение уникальности UID

        Args:
            uid: Исходный UID

        Returns:
            Уникальный UID (с суффиксом при необходимости)
        """
        if uid not in self._used_uids:
            return uid

        # Добавляем числовой суффикс
        counter = 2
        while True:
            new_uid = f"{uid}{UID_SEPARATOR}{counter}"
            if new_uid not in self._used_uids:
                return new_uid
            counter += 1

            # Защита от бесконечного цикла
            if counter > 1000:
                raise ValueError(f"Не удалось создать уникальный UID для {uid}")


# Глобальный экземпляр генератора
_generator = UIDGenerator()


def generate_uid(title: str, parent_uid: str = None) -> str:
    """
    Удобная функция для генерации UID

    Args:
        title: Название курса
        parent_uid: UID родительского курса (опционально)

    Returns:
        Уникальный UID
    """
    return _generator.generate_uid(title, parent_uid)


def reset_uid_generator():
    """Сброс генератора UID"""
    _generator.reset()
