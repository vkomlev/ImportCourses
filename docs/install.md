# Установка

## Требования

- Python 3.9+
- Доступ по HTTP(S) к сайту victor-komlev.ru (парсер обращается к нему напрямую)

## Шаги

1. Клонируйте репозиторий или скачайте проект.
2. Создайте виртуальное окружение (например, `.venv`):
   ```bash
   python -m venv .venv
   ```
3. Активируйте виртуальное окружение:
   - Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
   - Windows (cmd): `.venv\Scripts\activate.bat`
   - Linux/Mac: `source .venv/bin/activate`
4. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

## Проверка установки

```bash
pytest tests/ -v
```

Все тесты должны пройти без сети — парсер тестируется на фикстурах HTML, реальные запросы к сайту не выполняются.

Далее — [README.md](../README.md) для быстрого старта или [configuration.md](configuration.md) для настройки под другой сайт/структуру страниц.
