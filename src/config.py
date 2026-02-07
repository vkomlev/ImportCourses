"""Конфигурация парсера курсов"""

# UID главного курса (можно переопределить через параметры командной строки)
MAIN_COURSE_UID = "PY"

# Название главного курса (будет извлечено из заголовка страницы или задано вручную)
MAIN_COURSE_TITLE = None  # Если None, будет извлечено из страницы

# Уровень доступа по умолчанию для всех курсов
DEFAULT_ACCESS_LEVEL = "manual_check"

# Настройки HTTP запросов
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 30
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # секунды

# Настройки генерации UID
UID_MAX_LENGTH = 100  # Максимальная длина UID
UID_SEPARATOR = "-"  # Разделитель в UID

# Настройки парсинга
H3_TAG = "h3"  # Тег для поиска подкурсов первого уровня
GO_LINK_TEXT = "Перейти"  # Текст ссылки для перехода на страницу подкурса
PLAN_SECTION_HEADER = "Краткий план раздела"  # Заголовок раздела с планом

# Настройки Excel
EXCEL_DEFAULT_FILENAME = "courses"
EXCEL_OUTPUT_DIR = "output"
