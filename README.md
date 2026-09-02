# AI-наставник 360 — обучение, практика и контроль знаний персонала

Корпоративный MVP: сотрудник учится в Telegram, методист и руководитель работают в web-панели.
Наставник, конструктор заданий и экзаменатор — **разные компоненты**. Бот не принимает кадровые решения и не подтверждает квалификацию единолично.

Маскот: **ДИС**, цифровой лис.

## Текущий этап

Реализован **этап 2 — курсы и обучение**: назначения, учебные сессии, прогресс, web-логин, Telegram `/courses` `/continue` `/progress`.

Ещё нет RAG, практики, экзамена и полной аналитики.

## Быстрый запуск

```bash
cp .env.example .env
docker compose up --build -d
```

Миграции и демо-seed выполняются при старте `web`.

- Панель: http://localhost:8000/login
- Health: http://localhost:8000/health/ready

Демо-пользователи (вымышленные, пароль у всех `DemoPass123!`):

| Роль | Email |
|------|--------|
| Сотрудник | employee@demo.local |
| Методист | methodist@demo.local |
| Руководитель | manager@demo.local |
| Администратор | admin@demo.local |

В Telegram: `/start`, затем рабочий email `employee@demo.local`. Команды `/courses`, `/continue`, `/progress`.

Структурированные JSON-логи пишут `web` и `bot` (`docker compose logs -f web bot`). Секреты и пароли маскируются.

## Локальные тесты

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -e ".[dev]"
pytest -q
```

## Переменные

См. `.env.example`. Для бота нужен `TELEGRAM_BOT_TOKEN`. `LOG_LEVEL=INFO`. `SEED_ON_START=true` наполняет демо-курс.

## Архитектура

[docs/architecture.md](docs/architecture.md)
