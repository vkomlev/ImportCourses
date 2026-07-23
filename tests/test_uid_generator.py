"""Тесты для модуля генерации UID"""

import pytest
from src.uid_generator import UIDGenerator, generate_uid, reset_uid_generator


class TestUIDGenerator:
    """Тесты для класса UIDGenerator"""

    def test_transliterate(self):
        """Тест транслитерации"""
        generator = UIDGenerator()
        assert generator.transliterate("Привет") == "Privet"
        assert generator.transliterate("Python") == "Python"
        assert generator.transliterate("Основы Python") == "Osnovy Python"

    def test_create_slug(self):
        """Тест создания slug"""
        generator = UIDGenerator()
        assert generator.create_slug("Основы Python") == "osnovy-python"
        # «я» может давать "ya" (простая транслит) или "ja" (библиотека transliterate)
        assert generator.create_slug("Python для ЕГЭ") in ("python-dlya-ege", "python-dlja-ege")
        assert generator.create_slug("Test 123") == "test-123"
        assert generator.create_slug("  Много   пробелов  ") == "mnogo-probelov"

    def test_generate_uid_without_parent(self):
        """Тест генерации UID без родителя"""
        generator = UIDGenerator()
        uid = generator.generate_uid("Основы Python")
        assert uid == "osnovy-python"
        assert uid.islower()

    def test_generate_uid_with_parent(self):
        """Тест генерации UID с родителем"""
        generator = UIDGenerator()
        uid = generator.generate_uid("Основы Python", "PYTHON-EGE-MAIN")
        assert uid == "PYTHON-EGE-MAIN-osnovy-python"
        assert uid.startswith("PYTHON-EGE-MAIN")

    def test_ensure_unique(self):
        """Тест обработки дубликатов"""
        generator = UIDGenerator()
        uid1 = generator.generate_uid("Тест")
        uid2 = generator.generate_uid("Тест")
        assert uid1 == "test"
        assert uid2 == "test-2"

    def test_reset(self):
        """Тест сброса генератора"""
        generator = UIDGenerator()
        generator.generate_uid("Тест")
        assert len(generator._used_uids) == 1
        generator.reset()
        assert len(generator._used_uids) == 0


class TestGenerateUIDFunction:
    """Тесты для функции generate_uid"""

    def test_generate_uid_function(self):
        """Тест функции generate_uid"""
        reset_uid_generator()
        uid = generate_uid("Основы Python", "PYTHON-EGE-MAIN")
        assert uid.startswith("PYTHON-EGE-MAIN")

    def test_reset_function(self):
        """Тест функции reset"""
        reset_uid_generator()
        uid1 = generate_uid("Тест")
        reset_uid_generator()
        uid2 = generate_uid("Тест")
        # После reset дубликаты должны быть разрешены
        assert uid1 == uid2
