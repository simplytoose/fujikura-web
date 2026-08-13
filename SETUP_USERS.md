# 🔐 Система управління користувачами та ролями

Це повна документація для роботи з системою управління користувачами у Flask-додатку **Fujikura Applicators**.

## 📋 Вміст

1. [Інсталяція](#інсталяція)
2. [Створення першого адміністратора](#створення-першого-адміністратора)
3. [Структура ролей](#структура-ролей)
4. [Маршрути та доступ](#маршрути-та-доступ)
5. [API перевірки прав](#api-перевірки-прав)
6. [Приклади використання](#приклади-використання)
7. [Безпека](#безпека)

## 🚀 Інсталяція

### 1. Встановіть залежності

```bash
pip install -r requirements.txt
```

**Нові пакети:**
- `Flask-WTF==1.2.1` - CSRF захист та обробка форм
- `WTForms==3.1.1` - Валідація форм
- `email-validator==2.1.0` - Валідація email адрес

### 2. Запустіть додаток

```bash
python run.py
```

Додаток доступний за адресою: `http://localhost:5000`

## 👨‍💼 Створення першого адміністратора

### Автоматичний скрипт (рекомендується)

```bash
python create_admin.py
```

Слідуйте інтерактивним інструкціям у терміналі:
- Введіть ім'я користувача (мінімум 3 символи)
- Введіть email адресу
- Введіть пароль (мінімум 8 символів)
- Підтвердіть пароль

**Приклад:**
```
Ім'я користувача: admin
Email: admin@fujikura.local
Пароль: admin123456
```

### Ручне створення через CLI

Якщо скрипт не працює, спробуйте:

```python
from app import create_app
from services.user_service import UserService
from models import RoleEnum

app = create_app()
with app.app_context():
    user = UserService.create_user(
        username='admin',
        email='admin@example.com',
        password='admin123456',
        role=RoleEnum.ADMIN.value
    )
    print(f"Користувач {user.username} створено!")
```

## 👥 Структура ролей

### Ролі в системі

| Роль | Опис | Права | API |
|------|------|-------|-----|
| **Admin** | Адміністратор | Повний доступ | `@admin_required` |
| **Technician** | Технік | Управління аплікаторами, історія | `@technician_required` |
| **Operator** | Оператор | Обмежений доступ | `@login_required` |

### Методи перевірки ролей

На об'єкті користувача доступні методи:

```python
current_user.is_admin()         # True для адміністраторів
current_user.is_technician()    # True для техніків
current_user.is_operator()      # True для операторів
current_user.is_active          # Статус активності
```

## 🛣️ Маршрути та доступ

### Аутентифікація

| Маршрут | Метод | Опис | Доступ |
|---------|-------|------|--------|
| `/auth/login` | GET, POST | Форма входу | Всім |
| `/auth/register` | GET, POST | Реєстрація як технік | Всім |
| `/auth/logout` | GET | Вихід | Авторизовані |
| `/auth/profile` | GET, POST | Профіль користувача | Авторизовані |

### Адміністрація

| Маршрут | Метод | Опис | Доступ |
|---------|-------|------|--------|
| `/admin/` | GET | Панель адміністратора | Тільки admin |
| `/admin/users` | GET | Список користувачів | Тільки admin |
| `/admin/users/add` | GET, POST | Створення користувача | Тільки admin |
| `/admin/users/<id>/edit` | GET, POST | Редагування користувача | Тільки admin |
| `/admin/users/<id>/toggle` | POST | Блокування/розблокування | Тільки admin |
| `/admin/users/<id>/delete` | POST | Видалення користувача | Тільки admin |

### Дані користувача

**Модель User містить:**
```python
User.id              # Унікальний ID
User.username        # Ім'я користувача (унікальне)
User.email          # Email (унікальний)
User.password_hash  # Захешований пароль
User.role           # Роль (admin, technician, operator)
User.is_active      # Активність облікового запису
User.created_at     # Дата створення
User.last_login     # Дата останнього входу
```

## 🔒 API перевірки прав

### Використання в маршрутах

```python
from flask import Blueprint
from flask_login import login_required, current_user
from routes_admin import admin_required

bp = Blueprint('example', __name__)

# Для адміністраторів
@bp.route('/admin-only')
@admin_required
def admin_only():
    return "Тільки для адміністраторів"

# Для авторизованих користувачів
@bp.route('/profile')
@login_required
def user_profile():
    return f"Привіт, {current_user.username}"

# Перевірка ролі в коді
@bp.route('/check')
@login_required
def check_role():
    if current_user.is_admin():
        return "Ви адміністратор"
    elif current_user.is_technician():
        return "Ви технік"
    else:
        return "Ви оператор"
```

### Користувацькі декоратори

Якщо потрібні додаткові декоратори:

```python
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def technician_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_technician():
            flash('Доступ тільки для техніків', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated_function
```

## 📚 Приклади використання

### Приклад 1: Реєстрація нового технік

```
URL: http://localhost:5000/auth/register
Метод: POST
Дані форми:
  - username: tech_01
  - email: tech@example.com
  - password: tech123456
  - confirm_password: tech123456
```

Результат: Користувач з роллю "technician" створено.

### Приклад 2: Логін

```
URL: http://localhost:5000/auth/login
Метод: POST
Дані форми:
  - username: tech_01
  - password: tech123456
  - remember: on (опціонально)
```

### Приклад 3: Адміністратор створює користувача

```
URL: http://localhost:5000/admin/users/add
Метод: POST
Дані форми:
  - username: operator_01
  - email: operator@example.com
  - password: op123456
  - role: operator
```

### Приклад 4: Редагування користувача

```
URL: http://localhost:5000/admin/users/2/edit
Метод: POST
Дані форми:
  - email: new_email@example.com
  - role: technician
  - password: new_password123 (опціонально)
```

### Приклад 5: Блокування користувача

```
URL: http://localhost:5000/admin/users/3/toggle
Метод: POST
Результат: JSON {'success': true, 'message': 'Користувач деактивовано'}
```

## 🔐 Безпека

### Захист паролів

- ✅ Паролі хешуються з використанням `werkzeug.security.generate_password_hash`
- ✅ Хешування: `pbkdf2:sha256`
- ✅ Мінімальна довжина пароля: **8 символів**
- ✅ Перевірка: `check_password_hash()`

### CSRF захист

- ✅ Всі форми містять `{{ form.hidden_tag() }}` для CSRF токену
- ✅ Flask-WTF автоматично перевіряє токени
- ✅ Конфіг: `WTF_CSRF_ENABLED = True`

### Сесійна безпека

```python
# app.config
SESSION_COOKIE_HTTPONLY = True      # JS не може читати куки
SESSION_COOKIE_SAMESITE = 'Lax'     # CSRF захист
PERMANENT_SESSION_LIFETIME = 7 days # Час сесії
```

### Валідація форм

- ✅ Email валідація (з `email-validator`)
- ✅ Ім'я користувача: A-Z, 0-9, _, довжина 3-20
- ✅ Проверка унікальності username та email
- ✅ Підтвердження пароля

### Захист маршрутів

- ✅ `@admin_required` - тільки адміністратори
- ✅ `@login_required` - тільки авторизовані
- ✅ Перенаправлення на `/auth/login` при відсутності доступу

## 📝 Демо облікові записи

**За замовчуванням в системі:**

| Username | Password | Роль | Email |
|----------|----------|------|-------|
| admin | admin123 | Admin | admin@demo.local |
| tech1 | tech123 | Technician | tech@demo.local |
| operator1 | op123 | Operator | op@demo.local |

## 🐛 Можливі проблеми

### Помилка: "The CSRF token is missing"

**Рішення:** Переконайтеся, що форма містить `{{ form.hidden_tag() }}`

### Помилка: "WTForms is not installed"

**Рішення:** `pip install Flask-WTF WTForms`

### Пароль не приймається

**Рішення:** Пароль повинен містити мінімум 8 символів

### Адміністратор не створюється

**Рішення:** Проверте, чи запущена команда `python create_admin.py` коректно

## 📞 Контакти

Для питань або проблем зверніться до адміністратора системи.

---

**Версія:** 2.0  
**Дата останнього оновлення:** 2026-06-06  
**Статус:** ✅ Готово до використання
