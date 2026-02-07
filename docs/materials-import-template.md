# Шаблон XLSX для импорта материалов

## Файл

- **Файл:** `materials_import_template.xlsx` (в корне проекта)
- **Генерация:** `python tests/generate_materials_import_xlsx.py` (нужен `pip install openpyxl`)

## Структура листа

- **Имя листа:** `Materials` (по умолчанию в API; можно указать другой в запросе `sheet_name`).

Колонки (заголовки в первой строке), распознаваемые парсером:

| Колонка          | Обязательно | Описание |
|------------------|-------------|----------|
| course_uid       | ✅          | Код курса из таблицы `courses` (например COURSE-PY-01, COURSE-MATH-01) |
| external_uid     | ✅          | Внешний код материала; пара (course_uid, external_uid) уникальна в курсе |
| title            | ✅          | Заголовок материала |
| type             | ✅          | Тип: text, video, audio, image, link, pdf, office_document, script, document |
| url              | ✅ для link | URL (обязателен для type=link; для video/image/pdf — источник) |
| description      | ⚪          | Описание |
| caption          | ⚪          | Подпись |
| order_position   | ⚪          | Позиция в курсе (целое ≥ 1; пусто = в конец) |
| is_active        | ⚪          | true/false, 1/0, да/нет |

## Пример данных в шаблоне

В сгенерированном файле уже есть примеры строк для курсов **COURSE-PY-01** и **COURSE-MATH-01** (типы: link, video, text, pdf). После проверки и правок:

1. Откройте файл в Excel/LibreOffice, при необходимости отредактируйте.
2. Загрузите содержимое в Google Таблицы (Файл → Импорт → Загрузить или копирование листа).
3. Убедитесь, что первый лист называется **Materials** (или укажите его имя в API в поле `sheet_name`).
4. Вызовите импорт: `POST /api/v1/materials/import/google-sheets` с `spreadsheet_url` вашей Google-таблицы.

## Повторная генерация шаблона

```bash
pip install openpyxl
python tests/generate_materials_import_xlsx.py
```

Файл будет перезаписан: `materials_import_template.xlsx`.
