# Project Memory

Project: ParseCourse
Path: `d:\Work\ParseCourse`
Created: 2026-05-26

## Purpose

- What this project is responsible for: парсинг иерархической структуры курсов (главная страница → подкурсы уровня 1 → подкурсы уровня 2) и учебных материалов (текстовые/видео уроки) с сайта `victor-komlev.ru`; экспорт результата в два XLSX-файла (курсы, материалы) для последующего импорта в LMS.
- What it is not responsible for: сам импорт в LMS (это делает отдельный API/скрипт, см. `docs/courses-import-manual.md`, `docs/materials-api.md`); хранение данных в БД — своей БД у проекта нет.

## Durable Context

- Product/domain facts that should survive across sessions: разметка сайта-источника (заголовки `<h3>`, ссылки «Перейти», раздел «Краткий план раздела», секции «Текстовые уроки»/«Видеоуроки») жёстко завязана на конкретный сайт и может измениться без предупреждения — тексты заголовков вынесены в `src/config.py`, а не хардкожены в логике парсинга.
- Important integration partners and contracts: целевой сайт `victor-komlev.ru` (единственный поддерживаемый источник на сейчас); LMS-приёмник импорта курсов/материалов через Google Sheets + API (контракты колонок — `docs/courses-import-manual.md`, `docs/materials-import-template.md`, `docs/materials-api.md`).
- Operational constraints: запуск ручной/по требованию (не по расписанию); один процесс — один сайт/URL за запуск.

## Commands

- Setup: `python -m venv .venv && pip install -r requirements.txt`
- Test: `pytest tests/ -v` (без сети — тесты используют встроенные HTML-фикстуры)
- Lint/typecheck: `flake8 src/ tests/`; форматирование — `black src/ tests/`
- Run locally: `python run.py --url <URL>`
- Smoke checks: прогон на реальном `--url` с `--verbose`, проверка непустого `output/courses_*.xlsx`

## Architecture Notes

- Core modules: `parser` (HTML), `uid_generator` (транслит + slug), `excel_writer` (XLSX), `main` (оркестрация + CLI) — подробности в `docs/ai/architecture.md`.
- Data/storage: только файловая система — вход не хранится, выход пишется в `output/*.xlsx`; общей БД нет (поэтому `docs/ai/WORKFLOWS/db-change.md` для этого проекта неприменим).
- External services: HTTP-доступ к сайту-источнику (единственная сетевая зависимость времени выполнения).
- Trust boundaries: вход — произвольный HTML внешнего сайта, парсится через BeautifulSoup без исполнения кода страницы; выход — локальные файлы, дальнейшая доставка в LMS вне зоны ответственности этого проекта.

## Known Risks

- Reliability: смена вёрстки сайта-источника (переименование заголовков, другая структура списков) молча уменьшает/обнуляет результат — нет автоматической проверки актуальности селекторов против живого сайта.
- Security/privacy: файл `docs/courses-import-manual.md` содержит пример пути к Service Account JSON (`secrets/gscapi-...json`) и пример API-ключа (`bot-key-1`) в curl-примерах — не проверено, боевые ли это значения; см. отчёт по документации от 2026-07-18 (`/project-docs update`), решение за оператором.
- Data/encoding: кодировка страницы определяется через `response.apparent_encoding` с fallback на `utf-8`; для нестандартных кодировок сайта возможны артефакты в `title`/`description`.
- Cross-project contract drift: формат колонок XLSX (курсы/материалы) должен оставаться синхронным с LMS-стороной импорта — при изменении контракта на стороне LMS нужно обновить `src/excel_writer.py` и соответствующие `docs/*-import-*.md`.

## Current Decisions

| Date | Decision | Why | Owner/Source |
| --- | --- | --- | --- |

## Prevention Register

| Date | Incident/Risk | Prevention Rule | Related Skill |
| --- | --- | --- | --- |

## Handoff Notes

- Current focus:
- Blockers:
- Follow-ups:

## Maintenance Rules

- Keep durable facts here; keep transient task notes in session summaries or issue docs.
- Do not store credentials, tokens, cookies, personal secrets, or private keys.
- When implementation intentionally diverges from specs, record the decision and update the relevant specs/docs in the same task.
- Prefer links to canonical docs over duplicating long content.
