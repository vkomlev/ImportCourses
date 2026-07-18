# ParseCourse — парсер курсов с сайта victor-komlev.ru

Python-приложение для парсинга иерархической структуры курсов с сайта victor-komlev.ru и генерации XLSX файла для последующего импорта в LMS (через Google Sheets API или загрузку таблицы).

---

## Анализ проекта

| Аспект | Описание |
|--------|----------|
| **Назначение** | Извлечение структуры курсов (главная страница → подкурсы уровня 1 → подкурсы уровня 2) и материалов (текстовые уроки, видеоуроки) из HTML; экспорт в XLSX для импорта в LMS. |
| **Вход** | URL главной страницы курса (например, victor-komlev.ru). |
| **Выход** | Два XLSX: **курсы** (`course_uid`, `title`, `description`, `access_level`, …) и **материалы** (`course_uid`, `external_uid`, `title`, `type`, `url`, …). |
| **Стек** | Python 3, requests, BeautifulSoup4, openpyxl, transliterate; тесты — pytest. |
| **Архитектура** | Модули: `parser` (HTML, секции материалов), `uid_generator` (транслит + slug), `excel_writer` (XLSX курсов и материалов), `main` (оркестрация и CLI). Конфигурация в `config.py`. |
| **Зависимости** | Внешний сайт (доступ по HTTP), локальная запись в `output/`. Импорт: курсы — [courses-import-manual.md](docs/courses-import-manual.md), материалы — [materials-import-template.md](docs/materials-import-template.md), [materials-api.md](docs/materials-api.md). |

---

## Описание

Парсер извлекает:

- **Курсы**: главный курс (UID из конфига), подкурсы уровня 1 (заголовки `<h3>` и ссылки «Перейти»), подкурсы уровня 2 (список под разделом «Краткий план раздела»).
- **Материалы**: на страницах подкурсов — секции «Текстовые уроки» и «Видеоуроки»; ссылки под этими заголовками собираются и привязываются к курсу: если текст ссылки полностью или частично совпадает с названием подкурса второго уровня — материал привязывается к этому подкурсу, иначе к подкурсу первого уровня (родителю).

Результат: два XLSX-файла (курсы и материалы), совместимые с импортом в LMS (Google Sheets API и др.).

## Быстрый старт

```bash
python -m venv .venv
# Windows (PowerShell): .\.venv\Scripts\Activate.ps1  |  Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python run.py --url https://victor-komlev.ru/python-dlya-ege-navigator-po-kursu/
```

Подробная установка (требования, шаги, платформы) — [docs/install.md](docs/install.md).

## Использование

```bash
# Через скрипт запуска (рекомендуется) или как модуль Python — эквивалентно
python run.py --url https://victor-komlev.ru/python-dlya-ege-navigator-po-kursu/
python -m src.main --url https://victor-komlev.ru/python-dlya-ege-navigator-po-kursu/

# С указанием выходных файлов
python run.py --url https://victor-komlev.ru/python-dlya-ege-navigator-po-kursu/ --output output/courses.xlsx --output-materials output/materials.xlsx

# С указанием UID главного курса и подробным логированием
python run.py --url https://victor-komlev.ru/python-dlya-ege-navigator-po-kursu/ --main-uid MY-COURSE --verbose
```

### Параметры командной строки

| Параметр | Описание |
|----------|----------|
| `--url` | **(обязательно)** URL главной страницы курса |
| `--output` | Путь к XLSX с курсами (по умолчанию: `output/courses_<timestamp>.xlsx`) |
| `--output-materials` | Путь к XLSX с материалами (по умолчанию: `output/materials_<timestamp>.xlsx`) |
| `--main-uid` | UID главного курса (по умолчанию: `PY` из config.py) |
| `--verbose` | Подробное логирование (DEBUG) |

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

## Выходные файлы

Парсер создаёт один или два XLSX в каталоге `output/`:

1. **Курсы** — всегда (если найдена хотя бы одна запись). Имя по умолчанию: `courses_<timestamp>.xlsx`. Формат колонок — [мануал импорта курсов](docs/courses-import-manual.md).
2. **Материалы** — только если на страницах подкурсов найдены секции «Текстовые уроки» или «Видеоуроки». Имя по умолчанию: `materials_<timestamp>.xlsx`. Формат колонок — [шаблон импорта материалов](docs/materials-import-template.md) и [API материалов](docs/materials-api.md).

UID курсов генерируется автоматически (транслитерация + slug + префикс родителя); детали алгоритма и модули парсера — [docs/ai/architecture.md](docs/ai/architecture.md).

## Разработка

### Запуск тестов

```bash
pytest tests/ -v                  # все тесты
pytest tests/test_parser.py -v    # конкретный модуль
```

### Форматирование кода

```bash
black src/ tests/
```

### Линтинг

```bash
flake8 src/ tests/
```

## Следующие шаги после парсинга

1. Проверьте файлы в `output/`: курсы (`courses_*.xlsx`) и при наличии — материалы (`materials_*.xlsx`).
2. Загрузите таблицы в Google Sheets (по одной или два листа в одной книге).
3. **Курсы:** импорт по [мануалу импорта курсов](docs/courses-import-manual.md) (эндпойнт импорта из Google Sheets).
4. **Материалы:** импорт по [шаблону и API материалов](docs/materials-import-template.md) и [materials-api.md](docs/materials-api.md) (лист Materials, колонки course_uid, external_uid, title, type, url и др.).
5. Проверьте результат в веб-интерфейсе или через API LMS.

## Документация

- [docs/install.md](docs/install.md) — требования и установка
- [docs/configuration.md](docs/configuration.md) — параметры `src/config.py`
- [docs/troubleshooting.md](docs/troubleshooting.md) — типовые проблемы и их решение
- [docs/ai/architecture.md](docs/ai/architecture.md) — модули и алгоритм работы
- [docs/courses-import-manual.md](docs/courses-import-manual.md) — импорт курсов в LMS
- [docs/materials-import-template.md](docs/materials-import-template.md), [docs/materials-api.md](docs/materials-api.md) — импорт материалов

## Лицензия

Проект для внутреннего использования.
