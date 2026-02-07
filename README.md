# ParseCourse — парсер курсов с сайта victor-komlev.ru

Python-приложение для парсинга иерархической структуры курсов с сайта victor-komlev.ru и генерации XLSX файла для последующего импорта в LMS (через Google Sheets API или загрузку таблицы).

---

## Анализ проекта

| Аспект | Описание |
|--------|----------|
| **Назначение** | Извлечение структуры курсов (главная страница → подкурсы уровня 1 → подкурсы уровня 2) из HTML и экспорт в формат, совместимый с импортом в LMS. |
| **Вход** | URL главной страницы курса (например, victor-komlev.ru). |
| **Выход** | XLSX-файл с колонками `course_uid`, `title`, `description`, `access_level`, `parent_course_uid`, `order_number`, `required_courses_uid`, `is_required`. |
| **Стек** | Python 3, requests, BeautifulSoup4, openpyxl, transliterate; тесты — pytest. |
| **Архитектура** | Модули: `parser` (HTML), `uid_generator` (транслит + slug), `excel_writer` (XLSX), `main` (оркестрация и CLI). Конфигурация в `config.py`. |
| **Зависимости** | Внешний сайт (доступ по HTTP), локальная запись в `output/`. Документация по импорту в LMS — в `docs/courses-import-manual.md`. |

---

## Описание

Парсер извлекает иерархическую структуру курсов:
- Главный курс (задается через константу)
- Подкурсы первого уровня (заголовки h3 на главной странице)
- Подкурсы второго уровня (нумерованные списки на страницах подкурсов)

Результат сохраняется в XLSX файл, совместимый с форматом импорта из Google Sheets.

## Установка

1. Клонируйте репозиторий или скачайте проект
2. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   ```
3. Активируйте виртуальное окружение:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

## Использование

### Базовое использование

**Вариант 1: Через скрипт запуска (рекомендуется)**
```bash
python run.py --url https://victor-komlev.ru/python-dlya-ege-navigator-po-kursu/
```

**Вариант 2: Как модуль Python**
```bash
python -m src.main --url https://victor-komlev.ru/python-dlya-ege-navigator-po-kursu/
```

### С указанием выходного файла

```bash
python run.py --url https://victor-komlev.ru/python-dlya-ege-navigator-po-kursu/ --output output/courses.xlsx
```

### С указанием UID главного курса

```bash
python run.py --url https://victor-komlev.ru/python-dlya-ege-navigator-po-kursu/ --main-uid PYTHON-EGE-MAIN
```

### С подробным логированием

```bash
python run.py --url https://victor-komlev.ru/python-dlya-ege-navigator-po-kursu/ --verbose
```

### Параметры командной строки

- `--url` (обязательно) - URL главной страницы курса
- `--output` (опционально) - путь к выходному XLSX файлу (по умолчанию: `output/courses_<timestamp>.xlsx`)
- `--main-uid` (опционально) - UID главного курса (по умолчанию: `PY` из config.py)
- `--verbose` (опционально) - включить подробное логирование (DEBUG уровень)

## Структура проекта

```
ParseCourse/
├── src/                    # Исходный код
│   ├── main.py            # Главный модуль
│   ├── parser.py          # Парсинг HTML
│   ├── uid_generator.py   # Генерация UID
│   ├── excel_writer.py    # Запись в XLSX
│   └── config.py          # Конфигурация
├── tests/                 # Тесты
├── output/                # Выходные файлы
├── docs/                  # Документация
├── run.py                 # Скрипт запуска
├── requirements.txt       # Зависимости
└── README.md              # Документация
```

## Формат выходного файла

XLSX файл содержит следующие колонки (согласно [мануалу импорта](docs/courses-import-manual.md)):

1. `course_uid` — уникальный код курса (обязательно)
2. `title` — название курса (обязательно)
3. `description` — описание (опционально, может быть пустым)
4. `access_level` — уровень доступа (обязательно, по умолчанию: `manual_check`)
5. `parent_course_uid` — код родительского курса (опционально, пусто для корневых курсов)
6. `order_number` — порядковый номер подкурса у родителя (опционально, целое число)
7. `required_courses_uid` — зависимости через запятую (опционально, по умолчанию пусто)
8. `is_required` — обязательность курса (опционально, по умолчанию: `false`)

### Пример структуры данных

| course_uid | title | description | access_level | parent_course_uid | order_number | required_courses_uid | is_required |
|------------|-------|-------------|--------------|-------------------|--------------|---------------------|-------------|
| PY-osnovy-python | Основы Python | Введение в Python | manual_check | PY | 1 | | false |
| PY-osnovy-python-pervaya-programma | Первая программа на Python | ... | manual_check | PY-osnovy-python | 1 | | false |

### Генерация UID

UID генерируется автоматически по следующим правилам:
- Транслитерация русского текста в латиницу
- Преобразование в slug (lowercase, дефисы вместо пробелов)
- Добавление префикса родительского UID через дефис
- Обработка дубликатов (добавление числового суффикса: `-2`, `-3`, и т.д.)

Примеры:
- "Основы Python" → `osnovy-python`
- Родитель: `PY` → `PY-osnovy-python`
- Подкурс: `PY-osnovy-python` → `PY-osnovy-python-pervaya-programma`

## Конфигурация

Настройки можно изменить в файле `src/config.py`:

### Основные настройки
- `MAIN_COURSE_UID` — UID главного курса (по умолчанию: `"PY"`)
- `DEFAULT_ACCESS_LEVEL` - уровень доступа по умолчанию (по умолчанию: `"manual_check"`)

### Настройки парсинга
- `USER_AGENT` - User-Agent для HTTP запросов
- `REQUEST_TIMEOUT` - таймаут запросов в секундах (по умолчанию: 30)
- `RETRY_ATTEMPTS` - количество попыток при ошибке (по умолчанию: 3)
- `H3_TAG` - тег для поиска подкурсов первого уровня (по умолчанию: `"h3"`)
- `GO_LINK_TEXT` - текст ссылки для перехода (по умолчанию: `"Перейти"`)
- `PLAN_SECTION_HEADER` - заголовок раздела с планом (по умолчанию: `"Краткий план раздела"`)

### Настройки генерации UID
- `UID_MAX_LENGTH` - максимальная длина UID (по умолчанию: 100)
- `UID_SEPARATOR` - разделитель в UID (по умолчанию: `"-"`)

## Алгоритм работы

1. **Парсинг главной страницы**: Извлечение всех заголовков `<h3>` и ссылок "Перейти" под ними
2. **Генерация UID уровня 1**: Для каждого найденного подкурса генерируется UID с префиксом главного курса
3. **Парсинг страниц подкурсов**: Для каждого подкурса первого уровня парсится страница по ссылке "Перейти"
4. **Извлечение плана**: На странице подкурса ищется раздел "Краткий план раздела" и нумерованный список под ним
5. **Генерация UID уровня 2**: Для каждого элемента списка генерируется UID с префиксом родительского подкурса
6. **Формирование данных**: Создание структуры данных с иерархией курсов
7. **Запись в Excel**: Сохранение всех курсов в XLSX файл с правильной структурой колонок

## Разработка

### Запуск тестов

```bash
# Все тесты
pytest tests/

# Конкретный модуль
pytest tests/test_parser.py

# С подробным выводом
pytest tests/ -v
```

### Форматирование кода

```bash
black src/ tests/
```

### Линтинг

```bash
flake8 src/ tests/
```

## Обработка ошибок

Парсер обрабатывает следующие ситуации:
- **Ошибки сети**: Автоматические повторы с экспоненциальной задержкой
- **Отсутствие элементов**: Логирование предупреждений, продолжение работы
- **Ошибки парсинга**: Логирование ошибок, пропуск проблемных элементов
- **Дубликаты UID**: Автоматическое добавление числового суффикса

## Примеры использования

### Базовый запуск
```bash
python run.py --url https://victor-komlev.ru/python-dlya-ege-navigator-po-kursu/
```

Или через модуль:
```bash
python -m src.main --url https://victor-komlev.ru/python-dlya-ege-navigator-po-kursu/
```

### С сохранением в конкретный файл
```bash
python run.py --url https://victor-komlev.ru/python-dlya-ege-navigator-po-kursu/ --output my_courses.xlsx
```

### С кастомным UID главного курса
```bash
python run.py --url https://victor-komlev.ru/python-dlya-ege-navigator-po-kursu/ --main-uid MY-COURSE-UID
```

### С подробным логированием для отладки
```bash
python run.py --url https://victor-komlev.ru/python-dlya-ege-navigator-po-kursu/ --verbose
```

## Следующие шаги после парсинга

1. Проверьте сгенерированный XLSX файл в `output/`
2. Загрузите файл в Google Sheets
3. Используйте API импорта согласно [мануалу](docs/courses-import-manual.md) для загрузки курсов в LMS
4. Проверьте корректность импорта через API или веб-интерфейс LMS

## Лицензия

Проект для внутреннего использования.
