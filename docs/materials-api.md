# API учебных материалов курса

**Базовый URL:** `http://localhost:8000/api/v1`  
**Аутентификация:** query-параметр `api_key` (обязателен для всех запросов).

Учебные материалы привязаны к курсам. Поддерживаются типы: `text`, `video`, `audio`, `image`, `link`, `pdf`, `office_document`, `script`, `document`. Порядок материалов в курсе задаётся полем `order_position`; при создании без указания позиции триггер БД ставит материал в конец.

---

## Содержание

1. [CRUD эндпойнты](#crud-эндпойнты)
2. [Поиск материалов](#поиск-материалов)
3. [Список материалов курса и операции](#список-материалов-курса-и-операции)
4. [Загрузка файлов](#загрузка-файлов)
5. [Импорт из Google Sheets](#импорт-из-google-sheets)
6. [Структура контента по типам материала](#структура-контента-по-типам-материала)
7. [Ответы и валидация](#ответы-и-валидация)
8. [Коды ошибок](#коды-ошибок)

---

## CRUD эндпойнты

Стандартные операции выполняются через общий префикс `/materials`.

### POST /materials — создание материала

**Тело запроса:**
```json
{
  "course_id": 7,
  "title": "Введение в Python",
  "type": "link",
  "content": {
    "url": "https://docs.python.org/3/tutorial/introduction.html",
    "title": "Введение в Python",
    "description": "Официальный туториал",
    "preview_image": null
  },
  "description": "Официальный туториал Python",
  "caption": null,
  "order_position": null,
  "is_active": true,
  "external_uid": "MAT-PY-01-INTRO"
}
```

- `order_position`: необязателен; если не передан или `null`, триггер БД ставит материал в конец курса.
- `external_uid`: необязателен; при импорте используется для upsert (уникальность пары `course_id` + `external_uid`).

**Ответ (201 Created):** объект материала в формате [MaterialRead](#формат-ответа-materialread).

---

### GET /materials/{id} — получение материала по ID

**Ответ (200 OK):** объект материала в формате [MaterialRead](#формат-ответа-materialread).

**Ошибки:** `404` — материал не найден.

---

### PATCH /materials/{id} — частичное обновление материала

Можно передать только изменяемые поля (остальные не меняются).

**Важно про поле `content`:**
- При изменении **только других полей** (title, is_active и т.д.) поле `content` передавать не нужно.
- Если в запросе передаётся **`content`** — ожидается **полный объект** для текущего типа материала (глубокое слияние внутри `content` не выполняется: значение заменяется целиком).
- При **смене `type`** в том же запросе обязательно передать **полный валидный `content`** для нового типа; иначе вернётся `422`.

**Пример тела (только метаданные):**
```json
{
  "title": "Новое название",
  "is_active": false
}
```

**Ответ (200 OK):** обновлённый объект материала.

**Ошибки:** `404` — материал не найден; `422` — неверная структура `content` для указанного `type` (в теле ответа — массив ошибок валидации с полями `loc` и `msg`, см. [Ответы и валидация](#ответ-422---детализация-ошибок-валидации)).

---

### DELETE /materials/{id} — удаление материала

**Ответ:** `204 No Content`.

После удаления триггер БД пересчитывает `order_position` у оставшихся материалов курса.

**Ошибки:** `404` — материал не найден.

---

## Поиск материалов

### GET /materials/search — глобальный поиск по title и external_uid

Поиск по всем курсам или по одному курсу. Подходит для сценария «найти материал по названию или UID».

**Параметры запроса:**

| Параметр   | Тип    | Обязательный | Описание |
|------------|--------|--------------|----------|
| q          | string | да           | Строка поиска (минимум 1 символ). Поиск по полям `title` и `external_uid` (ILIKE, без учёта регистра). |
| course_id  | int    | нет          | Ограничить поиск одним курсом. При отсутствии — поиск по всем курсам. |
| skip       | int    | нет (0)      | Смещение для пагинации |
| limit      | int    | нет (100)    | Максимум записей (1–500) |

**Пример:**
```
GET /api/v1/materials/search?q=Python&course_id=7&limit=20&api_key=...
```

**Ответ (200 OK):** тот же формат, что и у списка по курсу — объект с полями `items`, `total`, `skip`, `limit` (см. [Формат ответа со списком](#формат-ответа-со-списком-items-total-skip-limit)).

---

## Список материалов курса и операции

### GET /courses/{course_id}/materials — список материалов курса

**Параметры запроса:**

| Параметр   | Тип    | По умолчанию    | Описание |
|------------|--------|-----------------|----------|
| q          | string | —               | Поиск по заголовку и external_uid в рамках курса (ILIKE). |
| is_active  | bool   | —               | Фильтр по активности |
| type       | string | —               | Фильтр по типу материала |
| order_by   | string | order_position  | Сортировка: `order_position`, `title`, `created_at` |
| skip       | int    | 0               | Смещение для пагинации |
| limit      | int    | 100             | Максимум записей (1–500) |

**Пример:**
```
GET /api/v1/courses/7/materials?order_by=order_position&limit=50&api_key=...
```

**Формат ответа со списком (items, total, skip, limit):** во всех ответах со списком материалов присутствуют поля `total`, `skip`, `limit` — их наличие зафиксировано в контракте для пагинации в UI.

**Ответ (200 OK):**
```json
{
  "items": [
    {
      "id": 13,
      "course_id": 7,
      "title": "Введение в Python",
      "description": "Официальный туториал Python",
      "caption": null,
      "type": "link",
      "content": {
        "url": "https://docs.python.org/3/tutorial/introduction.html",
        "title": "Введение в Python",
        "description": "Официальный туториал",
        "preview_image": null
      },
      "order_position": 1,
      "is_active": true,
      "external_uid": "MAT-PY-01-INTRO",
      "created_at": "2026-01-30T11:01:47.360000Z",
      "updated_at": "2026-01-30T11:01:47.360000Z"
    }
  ],
  "total": 3,
  "skip": 0,
  "limit": 50
}
```

**Ошибки:** `404` — курс не найден.

---

### POST /courses/{course_id}/materials/reorder — изменить порядок материалов

Массовое задание нового порядка. Триггер БД пересчитывает позиции.

**Тело запроса:**
```json
{
  "material_orders": [
    { "material_id": 14, "order_position": 1 },
    { "material_id": 13, "order_position": 2 },
    { "material_id": 15, "order_position": 3 }
  ]
}
```

**Ответ (200 OK):**
```json
{
  "updated": 3,
  "materials": [
    { "id": 14, "order_position": 1 },
    { "id": 13, "order_position": 2 },
    { "id": 15, "order_position": 3 }
  ]
}
```

**Ошибки:** `400` — материал не принадлежит курсу или не найден; `404` — курс не найден.

---

### POST /materials/{material_id}/move — переместить материал

Перемещение в другую позицию в том же курсе или в другой курс.

**Тело запроса:**
```json
{
  "new_order_position": 1,
  "course_id": null
}
```

| Поле                | Тип    | Обязательность | Описание |
|---------------------|--------|----------------|----------|
| new_order_position  | int    | условно        | Новая позиция в курсе (≥ 1). **При переносе в другой курс** (`course_id` указан и отличается от текущего) — можно не передавать: материал будет поставлен **в конец** целевого курса. **В рамках того же курса** (только смена позиции) — обязателен. |
| course_id           | int    | нет            | ID курса назначения. Если не передан или `null` — перемещение **внутри текущего курса** (меняется только позиция). Допустимо передать текущий `course_id` материала — тогда меняется только позиция. |

**Примеры:**
- Только смена позиции в том же курсе: `{ "new_order_position": 3, "course_id": null }` или `{ "new_order_position": 3, "course_id": 7 }` (если материал уже в курсе 7).
- Перенос в другой курс в конец: `{ "course_id": 8 }` (без `new_order_position`).
- Перенос в другой курс на конкретную позицию: `{ "new_order_position": 1, "course_id": 8 }`.

**Ответ (200 OK):** объект материала после перемещения.

**Ошибки:** `400` — некорректный курс/позиция или при перемещении внутри курса не указан `new_order_position`; `404` — материал или курс не найден.

---

### POST /courses/{course_id}/materials/bulk-update — массовое обновление активности

Обновление `is_active` у нескольких материалов курса.

**Тело запроса:**
```json
{
  "material_ids": [13, 14, 15],
  "is_active": false
}
```

**Ответ (200 OK):**
```json
{
  "updated": 3
}
```

**Ошибки:** `404` — курс не найден.

---

### POST /materials/{material_id}/copy — копировать материал в другой курс

Создаётся новая запись в целевом курсе (контент и метаданные копируются). `external_uid` у копии не задаётся, чтобы избежать конфликта уникальности.

**Тело запроса:**
```json
{
  "target_course_id": 8,
  "order_position": null
}
```

- `order_position`: необязателен; `null` — в конец курса.

**Ответ (201 Created):** объект созданного материала (с новым `id`).

**Ошибки:** `400` — целевой курс недоступен; `404` — материал или курс не найден.

---

### GET /courses/{course_id}/materials/stats — статистика материалов курса

**Ответ (200 OK):**
```json
{
  "total": 5,
  "active": 4,
  "inactive": 1,
  "by_type": {
    "link": 2,
    "video": 1,
    "text": 1,
    "pdf": 1
  }
}
```

**Ошибки:** `404` — курс не найден.

---

## Загрузка файлов

Для материалов с контентом «файл на сервере» (PDF, документ, изображение и т.д.) предусмотрена загрузка файла и подстановка полученного URL в `content`.

**Важно:** загрузка **не обновляет** поле `content` материала автоматически. После успешного upload клиент должен выполнить **PATCH материала**, добавив возвращённый `url` в `content` (например, в `content.sources` для типов pdf/video/audio/image/office_document или в `content.url` для типа link). При PATCH передавайте **полный** объект `content`, чтобы сохранить уже существующие источники (внешние ссылки): наш файл и внешняя ссылка могут сосуществовать в одном материале (см. [Хранение в нескольких местах](#хранение-в-нескольких-местах-наш-сервер--внешняя-ссылка)).

### POST /materials/upload — загрузить файл

Загружает файл на сервер. Возвращает URL для подстановки в `content` материала (например, в `content.sources[].url` для типа `pdf`/`video` или в `content.url` для типа `link`). **Никакой материал при этом не изменяется** — обновление `content` выполняет клиент через PATCH.

**Запрос:** `multipart/form-data`, поле `file` — файл (PDF, документ, изображение и т.д.).

**Лимит размера:** `MAX_ATTACHMENT_SIZE_BYTES` (по умолчанию 10 MB). Папка хранения: `MATERIALS_UPLOAD_DIR` (по умолчанию `uploads/materials`).

**Ответ (200 OK):**
```json
{
  "url": "/api/v1/materials/files/abc123_original.pdf",
  "filename": "original.pdf"
}
```

- `url` — относительный путь для скачивания файла; его подставляют в `content.sources[].url` (с `type: "file"`) или в `content.url` (для link). На клиенте при необходимости дополняется базовым URL сервера.
- `filename` — исходное имя файла.

**Ошибки:** `413` — файл превышает лимит размера.

---

### GET /materials/files/{file_id} — скачать загруженный файл

Отдаёт файл по идентификатору (имя файла, выданное при upload). `file_id` не должен содержать `/` или `..`. Используйте этот эндпойнт (или полный URL из `content.sources[].url` с путём `/api/v1/materials/files/...`) для получения файла с нашего сервера; внешние ссылки из `content.sources[].url` с `type: "url"` открываются по этому URL как есть.

**Пример:** `GET /api/v1/materials/files/abc123_original.pdf?api_key=...`

**Ответ (200 OK):** тело файла с соответствующим `Content-Type`.

**Ошибки:** `400` — недопустимый `file_id`; `404` — файл не найден.

---

## Импорт из Google Sheets

Импорт материалов из листа Google Таблицы. Курс для каждой строки задаётся полем **course_uid** в таблице (многокурсовой импорт). Upsert по паре `(course_id, external_uid)`: если материал с таким `external_uid` в курсе уже есть — он обновляется, иначе создаётся новый.

### POST /materials/import/google-sheets

**Тело запроса:**
```json
{
  "spreadsheet_url": "https://docs.google.com/spreadsheets/d/16xdksyZnll09VQ5tGnwSEFCtiK4f9wF2tTxW14GKZjA/edit?usp=sharing",
  "sheet_name": "Materials",
  "dry_run": false,
  "column_mapping": null
}
```

| Поле             | Тип    | Обязательно | Описание |
|------------------|--------|-------------|----------|
| spreadsheet_url  | string | да          | URL таблицы или spreadsheet_id |
| sheet_name       | string | нет         | Имя листа (по умолчанию `Materials`) |
| dry_run          | bool   | нет         | `true` — только проверка, без записи в БД |
| column_mapping   | object | нет         | Маппинг «название колонки» → «поле»; по умолчанию выводится из заголовков |

**Колонки листа (по умолчанию распознаются по заголовкам):**

| Поле            | Обязательно | Описание |
|-----------------|-------------|----------|
| course_uid      | да          | Код курса (`courses.course_uid`) |
| external_uid    | да          | Внешний код материала (уникален в паре с course_uid) |
| title           | да          | Заголовок |
| type            | да          | text, video, audio, image, link, pdf, office_document, script, document |
| url             | да для link | Ссылка (для link обязательна; для video/pdf — источник) |
| description     | нет         | Описание |
| caption         | нет         | Подпись |
| order_position  | нет         | Позиция (целое ≥ 1; пусто — в конец) |
| is_active       | нет         | true/false, да/нет, 1/0 |

**Ответ (200 OK):**
```json
{
  "imported": 5,
  "updated": 0,
  "total_rows": 5,
  "by_course": [
    {
      "course_uid": "COURSE-PY-01",
      "course_id": 7,
      "imported": 3,
      "updated": 0,
      "errors": []
    },
    {
      "course_uid": "COURSE-MATH-01",
      "course_id": 8,
      "imported": 2,
      "updated": 0,
      "errors": []
    }
  ],
  "errors": []
}
```

При ошибках разбора или «курс не найден» соответствующие строки попадают в `errors` (с полями `row`, `error`, `course_uid`, `external_uid`) или в `by_course[].errors`.

**Режим dry_run:**
- При `dry_run: true` в ответе возвращаются **те же структуры** (`imported`, `updated`, `total_rows`, `by_course`, `errors`), но **без записи в БД**.
- В UI удобно показывать пользователю превью «что будет создано/обновлено» (например, список title + course_uid + external_uid по `by_course` и разобранным строкам) до подтверждения реального импорта.

**Заполнение content при импорте:**
- **Тип `text`:** колонка `url` не обязательна. Поле `content.text` заполняется в порядке приоритета: значение из колонки `url`, затем из колонки `title`, при отсутствии — пустая строка.
- **Типы `video`, `audio`, `image`, `pdf`, `office_document`, `script`, `document`:** при наличии колонки `url` создаётся один источник с `type: "url"` и этим URL, в ответе `default_source: 0`.

**Рекомендации:**

1. Сначала вызвать импорт с `dry_run: true`, проверить ответ и отсутствие ошибок.
2. Использовать шаблон `materials_import_template.xlsx` (см. [docs/materials-import-template.md](materials-import-template.md)): сгенерировать, заполнить, загрузить в Google Таблицы, указать в запросе `spreadsheet_url` и при необходимости `sheet_name`.

**Ошибки:** `400` — неверный URL/ID таблицы; `500` — ошибка чтения Google Sheets.

---

## Структура контента по типам материала

Поле `content` в запросах и ответах имеет разную структуру в зависимости от `type`. Ниже — допустимые форматы.

### Хранение в нескольких местах (наш сервер + внешняя ссылка)

Материал может храниться в нескольких местах одновременно: например, файл на нашем сервере (после upload) и URL внешнего ресурса. Для типов **video, audio, image, pdf, office_document, script, document** это реализуется через массив **`sources`**:

- В `sources` можно передать несколько элементов: один с `type: "file"` и `url: "/api/v1/materials/files/..."` (файл с нашего сервера), другой с `type: "url"` и `url: "https://..."` (внешняя ссылка).
- Поле **`default_source`** (индекс, по умолчанию 0) задаёт, какой источник показывать по умолчанию.
- **Получить файл с нашего сервера:** запрос `GET /materials/files/{file_id}` (или GET по полному URL из `content.sources[i].url`, где путь начинается с `/api/v1/materials/files/`).
- **Получить внешнюю ссылку:** значение `content.sources[j].url` для элемента с `type: "url"` — клиент использует этот URL для перехода или встроенного просмотра.

При обновлении материала после загрузки нового файла передавайте в PATCH **полный** объект `content`, включая все уже существующие источники — тогда внешняя ссылка останется, а новый файл добавится (или заменит нужный элемент в `sources`).

Для типа **link** поддерживается одно поле `url` (основная ссылка). Если нужны «наш файл + внешняя ссылка», используйте тип с массивом `sources` (например, `pdf`, `office_document`, `script` или `document`).

---

### Формат ответа (MaterialRead)

Во всех ответах материал возвращается в виде:

- `id`, `course_id`, `title`, `description`, `caption`, `type`, `content`, `order_position`, `is_active`, `external_uid`, `created_at`, `updated_at`

---

### type: text

```json
{
  "text": "Основной текст материала",
  "format": "markdown"
}
```

- `format`: `"markdown"` | `"html"` | `"plain"`

---

### type: video

```json
{
  "sources": [
    {
      "type": "url",
      "url": "https://www.youtube.com/watch?v=...",
      "thumbnail_url": null,
      "duration_seconds": null,
      "quality": null
    }
  ],
  "default_source": 0
}
```

- `sources[].type`: `file` | `url` | `telegram` | `youtube` | `vimeo`
- При импорте из таблицы по умолчанию создаётся один источник с `type: "url"` и переданным URL.

---

### type: audio

```json
{
  "sources": [
    {
      "type": "url",
      "url": "https://...",
      "duration_seconds": null
    }
  ],
  "default_source": 0
}
```

---

### type: image

```json
{
  "sources": [
    {
      "type": "url",
      "url": "https://...",
      "width": null,
      "height": null,
      "alt_text": null
    }
  ],
  "default_source": 0
}
```

---

### type: link

```json
{
  "url": "https://...",
  "title": "Название ссылки",
  "description": "Описание",
  "preview_image": null
}
```

- Для типа `link` поле `url` обязательно.

---

### type: pdf

```json
{
  "sources": [
    {
      "type": "url",
      "url": "https://...",
      "pages_count": null,
      "file_size_bytes": null
    }
  ],
  "default_source": 0
}
```

---

### type: office_document

```json
{
  "sources": [
    {
      "type": "url",
      "url": "https://...",
      "format": "docx",
      "file_size_bytes": null
    }
  ],
  "default_source": 0
}
```

- `sources[].format`: `docx` | `xlsx` | `pptx` | `odt` | `ods` | `odp`

---

### type: script

Программы и скрипты (py, js, ps1 и т.д.).

```json
{
  "sources": [
    {
      "type": "file",
      "url": "/api/v1/materials/files/abc123_hello.py",
      "format": "py",
      "file_size_bytes": null
    }
  ],
  "default_source": 0
}
```

- `sources[].type`: `file` | `url` | `telegram`
- `sources[].format`: `py` | `js` | `ts` | `ps1` | `sh` | `bat` | `cmd` | `sql` | `yaml` | `json` (опционально)

---

### type: document

Документы (docx, xlsx, pptx, txt).

```json
{
  "sources": [
    {
      "type": "url",
      "url": "https://...",
      "format": "docx",
      "file_size_bytes": null
    }
  ],
  "default_source": 0
}
```

- `sources[].type`: `file` | `url` | `telegram`
- `sources[].format`: `docx` | `xlsx` | `pptx` | `txt` | `odt` | `ods` | `odp` (опционально)

---

## Ответы и валидация

### Формат ответа со списком (items, total, skip, limit)

Во всех ответах со списком материалов присутствуют поля **`total`**, **`skip`**, **`limit`** — их наличие зафиксировано в контракте для пагинации в UI. Используются в:
- `GET /courses/{course_id}/materials`
- `GET /materials/search`

### Ответ 422 — детализация ошибок валидации

При ошибке валидации (в т.ч. неверная структура `content` для указанного `type`) сервер возвращает **422 Unprocessable Entity** с телом в формате FastAPI/Pydantic:
- массив **`detail`** с элементами вида `{ "loc": ["body", "content", "url"], "msg": "...", "type": "..." }`;
- `loc` — путь к полю (например, `["body", "content", "sources", 0, "url"]`);
- `msg` — текст ошибки.

Этого достаточно для формирования понятных сообщений пользователю в боте или в UI.

---

## Коды ошибок

- **400** — Ошибка бизнес-логики (материал не в курсе, некорректный порядок, неверный URL таблицы, при move внутри курса не указан `new_order_position` и т.п.).
- **403** — Неверный или отсутствующий API ключ.
- **404** — Курс, материал или файл не найден.
- **413** — Файл при загрузке превышает лимит размера.
- **422** — Ошибка валидации (в т.ч. неверная структура `content` для указанного `type`); в теле — массив `detail` с полями `loc` и `msg`.
- **500** — Ошибка при обращении к Google Sheets или к БД.

---

**См. также:**

- [Шаблон XLSX и импорт из Google Таблиц](materials-import-template.md)
- [Анализ и проектирование API материалов](materials-api-analysis.md)
- [Контракт триггеров БД](database-triggers-contract.md) — нумерация и пересчёт `order_position`
