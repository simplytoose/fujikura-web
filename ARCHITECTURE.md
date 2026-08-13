# Архітектура Fujikura Web System

## 📋 Огляд системи

**Fujikura Web** — це веб-система для управління та відстеження аплікаторів на виробництві. Система побудована на Flask (Python) з використанням JSON для збереження даних та забезпечує повну історію переміщень аплікаторів між машинами.

---

## 🏗️ Структура архітектури

### Рівні абстракції

```
┌─────────────────────────────────────────┐
│      🌐 HTML Templates (Presentation)   │
│     (base.html, dashboard, admin...)    │
├─────────────────────────────────────────┤
│   🎛️  Flask Routes (routes_*.py)        │
│   (Controllers, запити від UI)          │
├─────────────────────────────────────────┤
│   📦 Services (services/*.py)           │
│   (Бізнес-логіка)                       │
├─────────────────────────────────────────┤
│   🗄️  Data Layer (DataManager)          │
│   (Відкриття/запис JSON файлів)         │
├─────────────────────────────────────────┤
│   💾 Data Files (data/*.json)           │
│   (Збереження дані в JSON форматі)      │
└─────────────────────────────────────────┘
```

---

## 📁 Основні компоненти

### 1. **Конфігурація та Initialization**

#### `config.py`
- Налаштування для development/production режимів
- Шляхи до папок даних, ключі сесій

#### `app.py` 
- **Application Factory** — створює Flask додаток з усіма компонентами
- Реєструє всі blueprints (маршрути)
- Налаштовує Flask-Login для аутентифікації
- CSRF захист через CSRFProtect
- Реєструє context processor для доступу до поточного користувача в шаблонах

**Реєстровані blueprints:**
- `auth_bp` → Аутентифікація (логін, реєстрація)
- `dashboard_bp` → Головна сторінка з статистикою
- `applicators_bp` → Управління аплікаторами
- `locations_bp` → Управління дільницями
- `machines_bp` → Управління машинами
- `history_bp` → Виведення історії
- `admin_bp` → Адмін-панель
- `applicator_room_bp` → Управління кімнатою аплікаторів
- `service_area_bp` → Управління сервісною дільницею
- `production_bp` → Виробництво/статистика
- `management_bp` → Управління

#### `models.py`
Визначає моделі даних:

**User** - Користувач системи
```python
- id, username, email, password_hash
- role (ADMIN, TECHNICIAN, OPERATOR)
- is_active, created_at, last_login
- Методи: set_password(), check_password(), is_admin/technician/operator()
```

**Enums:**
- `RoleEnum`: ADMIN, TECHNICIAN, OPERATOR
- `StatusEnum`: AVAILABLE, SERVICE, CUTTING, CRIMPING, BLOCKED, INACTIVE

---

### 2. **Data Layer - Управління даними**

#### `data_manager.py` - DataManager
Клас для роботи з JSON файлами (міст між в пам'яті та дисками):

**Методи:**
- `load_data(filename)` → Завантажує JSON з диску
- `save_data(filename, data)` → Зберігає дані в JSON
- `get_data_file_path(filename)` → Повертає повний шлях до файлу

**JSON файли (в папці `data/`):**
```
data/
├── users.json           # Всі користувачі
├── applicators.json     # Всі аплікатори з історією
├── machines.json        # Все про машини
├── rooms.json          # Дані про кімнати
├── locations.json      # Дільниці
└── movements.json      # Вся історія переміщень
```

---

### 3. **Services - Бізнес логіка**

Папка `services/` містить всю бізнес-логіку, відокремлену від маршрутів:

#### `user_service.py` - UserService
Управління користувачами:
```python
- get_user_by_id(user_id)
- authenticate(username, password)
- create_user(username, email, password, role)
- update_user(...)
- get_all_users()
```

#### `applicator_service.py` - ApplicatorService ⭐ (НАЙВАЖЛИВІШИЙ)
Управління аплікаторами та їхніми переміщеннями:

**Ключові методи:**
- `create_applicator(number, location)` → Создавання нового аплікатора
- `move_applicator(app_id, to_location, moved_by)` → Переміщення аплікатора
- `block_applicator(app_id, reason, blocked_by)` → Блокування
- `unblock_applicator(app_id, unblocked_by)` → Розблокування
- `get_applicator_history(app_id)` → Вся історія переміщень одного аплікатора
- `get_applicator_by_location(location)` → Всі аплікатори на дільниці
- `update_applicator_status(app_id, status)` → Оновлення статусу
- `check_machine_capacity(machine_id)` → Перевірка вільних місць на машині

#### `machine_service.py` - MachineService
Управління машинами:
```python
- get_machine(machine_id)
- get_all_machines()
- update_machine_status(machine_id, status)
- get_machines_by_type(machine_type) # G - нарізка, P - кримпування
```

#### `movement_service.py` - MovementService
Управління історією переміщень:
```python
- record_movement(applicator_id, from_loc, to_loc, user_id)
- get_movement_history(applicator_id, days=30)
- get_statistics() → Статистика за період
```

#### `production_service.py` - ProductionService
Виробництво та звіти:
```python
- get_production_stats(date_range)
- get_machine_load()
- generate_report()
```

#### `room_service.py` - RoomService
Управління кімнатою аплікаторів:
```python
- get_room_status()
- add_to_room(applicator_id)
- remove_from_room(applicator_id)
```

#### `validation_service.py` - ValidationService
Валідація даних:
```python
- validate_applicator_number(number)
- validate_location(location)
- validate_machine_id(machine_id)
- validate_user_input(data, rules)
```

---

### 4. **Routes - Контролери (маршрути)**

Кожен файл `routes_*.py` — це Flask Blueprint з маршрутами для певного модуля:

#### `routes_auth.py` - Аутентифікація
```
POST  /auth/login       → Логін користувача
GET   /auth/logout      → Вихід
POST  /auth/register    → Реєстрація (якщо дозволено)
```

#### `routes_dashboard.py` - Головна сторінка
```
GET   /dashboard        → Показ stats та основної інформації
```

#### `routes_applicators.py` - Аплікатори ⭐ (ГОЛОВНИЙ)
```
GET   /applicators              → Список аплікаторів
GET   /applicators/<id>         → Деталі аплікатора
POST  /applicators/move         → Переміщення аплікатора
POST  /applicators/block        → Блокування
POST  /applicators/unblock      → Розблокування
GET   /applicators/<id>/history → Історія одного аплікатора
```

#### `routes_machines.py` - Машини
```
GET   /machines         → Список всіх машин
GET   /machines/<id>    → Деталі машини (які аплікатори на ній)
POST  /machines/status  → Оновлення статусу машини
```

#### `routes_locations.py` - Дільниці
```
GET   /locations        → Список дільниць
GET   /locations/<name> → Аплікатори на дільниці
```

#### `routes_history.py` - Історія
```
GET   /history          → Вся історія переміщень
GET   /history/filter   → Фільтрована історія
```

#### `routes_admin.py` - Адміністрація
```
GET   /admin                    → Адмін-панель
POST  /admin/users/create       → Создавання користувача
POST  /admin/users/<id>/delete  → Видалення користувача
```

#### `routes_applicator_room.py` - Кімната аплікаторів
```
GET   /applicator-room          → Стан кімнати
POST  /applicator-room/add      → Додавання аплікатора до кімнати
```

#### `routes_service_area.py` - Сервісна дільниця
```
GET   /service-area             → Стан сервісної дільниці
```

#### `routes_management.py` - Управління
```
GET   /management               → Звіти та аналітика
```

#### `routes_production.py` - Виробництво
```
GET   /production               → Виробнича статистика
```

---

### 5. **Frontend - Шаблони (Templates)**

Папка `templates/` → HTML шаблони на Jinja2:

#### `base.html` - Базовий шаблон
- Bootstrap 5 навігаційна панель
- Меню з посиланнями на всі сторінки (в залежності від ролі користувача)
- Flash-повідомлення (для сповіщень)
- Footer з інформацією
- CSS та JS посилання

#### `auth/`
- `login.html` → Форма логіну
- `register.html` → Форма реєстрації (якщо потрібна)

#### `applicators/` - Головні шаблони
- `list.html` → Таблиця зі всіма аплікаторами
  - Фільтрування по статусу
  - Кнопки: Переміщення, Блокування, Переглянути історію
- `details.html` → Деталі одного аплікатора
  - Поточна локація, статус
  - Кнопки дій
- `history.html` → Історія переміщень аплікатора
  - Таблиця з датами, локаціями, користувачем

#### `dashboard.html`
- Статистика:
  - Всього аплікаторів, на машинах, в кімнаті, заблокованих
  - Машини по типам (G - нарізка, P - кримпування)
- Графіки/діаграми з використанням Chart.js або Canvas

#### `machines/`
- `list.html` → Список машин
- `details.html` → Деталі машини (які аплікатори)
- `status.html` → Зміна статусу

#### `locations/`
- `list.html` → Дільниці
- `details.html` → Аплікатори на дільниці

#### `history/`
- `list.html` → Вся історія переміщень з фільтрами

#### `admin/`
- `panel.html` → Адмін-панель
  - Управління користувачами (створення, видалення)
  - Бекап/восстановлення даних

---

### 6. **Frontend - Статичні файли**

#### `static/css/style.css`
- Custom CSS стилі
- Переважно використовується Bootstrap 5

#### `static/js/main.js`
- JavaScript функції для інтерактивності
- AJAX запити для переміщення, блокування без перезавантаження сторінки

---

## 🔄 Потік даних: Приклад - Переміщення аплікатора

### Сценарій: Оператор переміщує аплікатор G01 з машини G01 на машину G02

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User Interface (HTML form в templates/applicators/)     │
│    └─ Користувач вводить: ID аплікатора, нову локацію      │
│    └─ Натискає кнопку "Переміщення"                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Flask Route (routes_applicators.py)                      │
│    └─ @app.route('/applicators/move', methods=['POST'])     │
│    └─ Отримує дані з форми                                 │
│    └─ Перевіряє дозволи користувача (role-based check)     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Services Layer (services/applicator_service.py)          │
│    └─ ApplicatorService.move_applicator()                   │
│    └─ Завантажує дані аплікаторів з JSON                    │
│    └─ Виконує бізнес-логіку:                               │
│       • Перевіряє, що аплікатор існує                      │
│       • Перевіряє, що ціль-локація існує                   │
│       • Перевіряє вільне місце на машині (capacity)        │
│       • Оновлює поточну локацію аплікатора                 │
│       • Записує запис в историю (movement_history)         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Data Layer (data_manager.py)                             │
│    └─ DataManager.save_data('applicators.json', data)       │
│    └─ DataManager.save_data('movements.json', movement)     │
│    └─ Записує змінені дані назад в JSON файли               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Database (JSON Files в data/)                            │
│    └─ data/applicators.json ОНОВЛЕНО                        │
│    └─ data/movements.json ОНОВЛЕНО                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Response to User (Route returns)                         │
│    └─ JSON response з результатом: {'success': true, ...}   │
│    └─ Frontend JS оновлює сторінку (AJAX)                   │
│    └─ Показує flash-повідомлення: "Переміщено успішно"      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Безпека та Ролі

### Рольова система (Role-based Access Control)

**Ролі:**
- **ADMIN** - Повний доступ до всього, управління користувачами
- **TECHNICIAN** - Управління аплікаторами, переміщення, блокування
- **OPERATOR** - Тільки перегляд, без змін

### Захист:
- ✅ Хеширование паролей PBKDF2:SHA256
- ✅ CSRF захист через `CSRFProtect`
- ✅ Session-based аутентифікація Flask-Login
- ✅ Проверка прав доступу в кожному маршруті (`@login_required`, role check)

---

## 📊 Основні структури даних

### `applicators.json` - Аплікатори
```json
[
  {
    "id": "APP001",
    "number": "G01",
    "status": "AVAILABLE",
    "current_location": "Machine G01",
    "machine_type": "cutting",
    "created_at": "2024-01-01T10:00:00",
    "created_by": "admin",
    "blocked": false,
    "blocked_reason": null,
    "blocked_at": null,
    "blocked_by": null,
    "movement_history": [...]
  }
]
```

### `movements.json` - Історія переміщень
```json
[
  {
    "id": "MOV001",
    "applicator_id": "APP001",
    "from_location": "Machine G01",
    "to_location": "Machine G02",
    "timestamp": "2024-06-15T14:30:00",
    "moved_by": "tech1",
    "reason": "scheduled rotation"
  }
]
```

### `users.json` - Користувачі
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@fujikura.local",
    "password_hash": "pbkdf2:sha256:...",
    "role": "admin",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00",
    "last_login": "2024-06-15T14:00:00"
  }
]
```

---

## 🚀 Ключові файли для запуску

1. **`run.py`** - Точка входу, запускає Flask сервер
2. **`init_db.py`** - Ініціалізація БД з тестовими даними (100 аплікаторів, 9 користувачів)
3. **`create_admin.py`** - Утиліта для створення адмін користувача

---

## 🔄 Життєвий цикл запиту

```
1. User натискає кнопку в HTML → JavaScript AJAX запит
2. Flask route отримує запит → Валідація даних
3. Services оновлюють бізнес-логіку → Перевіряють правила
4. DataManager записує в JSON файли
5. JSON файли збережені на диску
6. Flask повертає JSON response
7. JavaScript оновлює DOM без перезавантаження
8. User видить результат в UI
```

---

## 📈 Розширюваність

Система легко розширюється:

1. **Додавання нового модуля:**
   - Створити `routes_newmodule.py`
   - Створити `services/newmodule_service.py` (якщо потрібна логіка)
   - Додати шаблони в `templates/newmodule/`
   - Реєструвати blueprint в `app.py`

2. **Додавання нового JSON файлу:**
   - Додати його в папку `data/`
   - Додати методи завантаження в `DataManager`
   - Використовувати в сервісах

3. **Додавання нових ролей:**
   - Оновити `RoleEnum` в `models.py`
   - Додати перевірки в маршрутах
   - Оновити шаблони для нової ролі

---

## ⚙️ Точки розширення

| Компонент | Файл | Для чого |
|-----------|------|---------|
| Нова сторінка | `templates/` + `routes_new.py` | Новий функціонал |
| Нова логіка | `services/new_service.py` | Бізнес-правила |
| Новий JSON | `data/new.json` | Нові дані |
| Нова роль | `models.py` RoleEnum | Контроль доступу |
| Новий стиль | `static/css/` | Дизайн |

