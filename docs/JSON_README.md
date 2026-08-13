# Система обліку та відстеження аплікаторів - JSON Edition

## Опис

Повнофункціональна веб-система для управління та відстеження аплікаторів на виробництві, **100% на JSON без БД**.

## Архітектура (JSON-базована)

```
data/
├── applicators.json      # Аплікатори (100 шт у демо)
├── users.json           # Користувачі (9 шт)
├── machines.json        # Машини (35: 30 нарізка + 5 кримпування)
├── movements.json       # Історія переміщень (50+ записів)
├── blocking_history.json # Історія блокування
└── settings.json        # ID-счітчики та конфіг

backend/
├── data_manager.py      # Universal JSON CRUD
├── models.py            # Plain Python classes
├── services/
│   ├── user_service.py
│   ├── applicator_service.py
│   ├── machine_service.py
│   └── movement_service.py
└── routes_*.py          # Flask маршрути

frontend/
├── templates/           # HTML шаблони
└── static/              # CSS, JS
```

## Встановлення

```bash
# 1. Перейти до проекту
cd c:\Users\simplytoose\IdeaProjects\fujikura_web

# 2. Встановити залежності
pip install -r requirements.txt

# 3. Генерувати демо-дані (опціонально - вже готові)
python init_demo_data.py

# 4. Запустити
python run.py
```

## Демо облікові записи

| Роль | Користувач | Пароль |
|------|------------|--------|
| Адміністратор | admin | admin123 |
| Технік | tech1 | tech123 |
| Оператор | operator1 | op123 |

## Особливості

✅ **Без БД** - 100% JSON файли
✅ **DataManager** - універсальний CRUD для всіх таблиць
✅ **100 аплікаторів** - розподілені по локаціям
✅ **35 машин** - 30 нарізки (G01-G30), 5 кримпування (P01-P05)
✅ **Обмеження** - 5 макс на нарізці, 3 на кримпуванні
✅ **Історія 30 днів** - автоочищення старих записів
✅ **Хешовані паролі** - PBKDF2:SHA256
✅ **Ролевий доступ** - Admin, Technician, Operator
✅ **Переміщення** - з записом в историю
✅ **Блокування** - несправних аплікаторів

## Сторінки

- **Login** - `/auth/login` - вхід у систему
- **Dashboard** - `/dashboard/` - статистика та огляд
- **Аплікатори** - `/applicators/` - список, фільтр, пошук
- **Нарізка** - `/machines/cutting` - машини G01-G30
- **Кримпування** - `/machines/crimping` - машини P01-P05
- **Історія** - `/history/` - переміщення та блокування
- **Адмін** - `/admin/` - управління користувачами

## Структура JSON

### users.json
```json
{
  "records": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@fujikura.com",
      "password_hash": "pbkdf2:sha256:...",
      "role": "admin",
      "is_active": true,
      "created_at": "2026-06-06T...",
      "last_login": null
    }
  ]
}
```

### applicators.json
```json
{
  "records": [
    {
      "id": 1,
      "code": "APP-0001",
      "location": "Aplicator Room",
      "status": "AVAILABLE",
      "machine": null,
      "shelf_position": null,
      "created_at": "...",
      "notes": ""
    }
  ]
}
```

### machines.json
```json
{
  "records": [
    {
      "id": 1,
      "code": "G01",
      "type": "cutting",
      "location": "Cutting",
      "max_capacity": 5,
      "applicators": [1, 2],
      "created_at": "..."
    }
  ]
}
```

### movements.json
```json
{
  "records": [
    {
      "id": 1,
      "applicator_id": 1,
      "applicator_code": "APP-0001",
      "from_location": "Aplicator Room",
      "to_location": "Cutting",
      "from_machine": null,
      "to_machine": "G01",
      "user_id": 2,
      "username": "tech1",
      "date": "2026-06-06T...",
      "comment": "Розміщено на машині"
    }
  ]
}
```

## API Endpoints (JSON-based)

### Auth
- `POST /auth/login` - вхід (username, password)
- `GET /auth/logout` - вихід

### Applicators
- `GET /applicators/` - список всіх
- `GET /applicators/<id>` - деталі
- `POST /applicators/<id>/block` - блокувати
- `POST /applicators/<id>/unblock` - розблокувати

### Machines
- `POST /machines/add-to-machine` - додати на машину
- `POST /machines/remove-from-machine` - видалити з машини

### History
- `GET /history/` - переміщення
- `GET /history/blocking` - блокування

## Обмеження машин

### Нарізка (G01-G30)
- **Максимум**: 5 аплікаторів на машину
- **На машині**: 2 робочих
- **На стелажі**: 3 запасних

### Кримпування (P01-P05)
- **Максимум**: 3 аплікатора на машину
- **На машині**: 1 робочий
- **На стелажі**: 2 запасні

При перевищенні - помилка: "На машині вже знаходиться максимальна кількість аплікаторів (5)"

## Технології

- **Backend**: Flask 3.0.0 + Python 3.12+
- **Data**: JSON (без SQLAlchemy, SQLite, MongoDB)
- **Frontend**: Bootstrap 5 + Vanilla JS
- **Auth**: Flask-Login + Werkzeug PBKDF2
- **Server**: Flask development server

## Структура папок

```
fujikura_web/
├── app.py                    # Flask factory
├── config.py                 # Конфіг
├── run.py                    # Entry point
├── data_manager.py           # JSON CRUD
├── models.py                 # Python classes
├── requirements.txt          # Залежності
├── init_demo_data.py         # Demo generator
├── services/
│   ├── __init__.py
│   ├── user_service.py       # User CRUD
│   ├── applicator_service.py # Applicator ops
│   ├── machine_service.py    # Machine logic
│   └── movement_service.py   # History + cleanup
├── routes_*.py               # Flask blueprints
├── templates/                # HTML
│   ├── base.html
│   ├── auth/
│   ├── applicators/
│   ├── machines/
│   ├── history/
│   └── admin/
├── static/
│   ├── css/
│   └── js/
└── data/                     # Generated JSON
    ├── applicators.json
    ├── users.json
    ├── machines.json
    ├── movements.json
    ├── blocking_history.json
    └── settings.json
```

## Запуск

```bash
# Стандартний запуск
python run.py
# Доступна за: http://localhost:5000

# Debug режим
export FLASK_ENV=development
python run.py
```

## Тестування

Всі дані вже готові у `/data`:
- 100 аплікаторів розподілені по локаціям
- 35 машин (30+5)
- 9 користувачів
- 50+ записів переміщень

Просто запустіть та залогуйтесь!

## Можливості

### Для Адміністратора
- Повний доступ до всіх функцій
- Управління користувачами
- Перегляд усієї статистики
- Видалення даних

### Для Техніка
- Переміщення аплікаторів
- Блокування/розблокування
- Підтвердження обслуговування
- Перегляд історії

### Для Оператора
- Видача аплікаторів
- Повернення аплікаторів
- Перегляд статусів

## Дані зберігаються в JSON

Усі дані автоматично:
- Записуються в JSON при кожній операції
- Очищуються від старих записів (>30 днів)
- Синхронізуються через DataManager
- Мають thread-safe операції (threading.Lock)

## Без залежностей від БД

❌ Немає SQLAlchemy
❌ Немає SQLite
❌ Немає MySQL/PostgreSQL
❌ Немає MongoDB

✅ Все на JSON файлах!

---

**Версія**: 1.0.0 JSON Edition
**Дата**: 2026-06-06
**Розроблено на**: Python 3.12, Flask 3.0.0
