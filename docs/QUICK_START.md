# 🎯 Квик-старт: Система управління користувачами

## 1️⃣ Запуск (3 мінути)

```bash
# Встановлення залежностей (якщо не встановлені)
pip install Flask-WTF WTForms email-validator

# Створення першого адміністратора
python create_admin.py

# Запуск сервера
python run.py
```

**Сервер доступний:** http://localhost:5000

---

## 2️⃣ Основні маршрути

### 📱 Для всіх користувачів

| URL | Функція | Метод |
|-----|---------|-------|
| `/` | Перенаправлення | GET |
| `/auth/login` | 🔑 Вхід | GET, POST |
| `/auth/register` | 📝 Реєстрація (технік) | GET, POST |
| `/auth/logout` | 🚪 Вихід | GET |

### 👤 Для авторизованих

| URL | Функція | Метод |
|-----|---------|-------|
| `/auth/profile` | 👤 Профіль + зміна пароля | GET, POST |
| `/dashboard` | 📊 Панель управління | GET |

### 🔐 Для адміністраторів

| URL | Функція | Метод |
|-----|---------|-------|
| `/admin/` | 📊 Статистика | GET |
| `/admin/users` | 👥 Список користувачів | GET |
| `/admin/users/add` | ➕ Додати користувача | GET, POST |
| `/admin/users/<id>/edit` | ✏️ Редагувати | GET, POST |
| `/admin/users/<id>/toggle` | 🔒 Блокувати/розблокувати | POST |
| `/admin/users/<id>/delete` | 🗑️ Видалити | POST |

---

## 3️⃣ Демо облікові записи

```
Username: admin          | Password: admin123 | Роль: Admin
Username: tech1          | Password: tech123  | Роль: Technician
Username: operator1      | Password: op123    | Роль: Operator
```

---

## 4️⃣ Основні операції

### ➕ Реєстрація як технік
1. Перейти на http://localhost:5000/auth/register
2. Заповнити форму
3. Клік "Зареєструватися"
4. Логін з новими обліковими даними

### ✏️ Зміна пароля
1. Клік на username у меню → Профіль
2. Заповнити форму "Змінити пароль"
3. Клік "Змінити пароль"

### 👥 Управління користувачами (адмін)
1. Перейти на http://localhost:5000/admin/users
2. Операції:
   - **Додати:** ➕ Клік "Додати користувача"
   - **Редагувати:** ✏️ Клік "Редагувати"
   - **Блокувати:** 🔒 Клік "Деактивувати"
   - **Видалити:** 🗑️ Клік "Видалити"

---

## 5️⃣ Структура даних

### Користувач містить:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "password_hash": "pbkdf2:sha256:...",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-06-06T10:00:00",
  "last_login": "2026-06-06T12:30:00"
}
```

### Ролі:
- **admin** - Адміністратор (повний доступ)
- **technician** - Технік (управління аплікаторами)
- **operator** - Оператор (обмежений доступ)

---

## 6️⃣ Валідація форм

### Реєстрація:
- ✅ Username: 3-20 символів, [A-Za-z0-9_]
- ✅ Email: коректна адреса
- ✅ Password: мінімум 8 символів
- ✅ Повинні співпадати паролі

### Профіль:
- ✅ Password: мінімум 8 символів (опціонально)

### Адмін форма:
- ✅ Все як у реєстрації
- ✅ Роль: admin, technician, operator

---

## 7️⃣ API для розробників

### Перевірка ролей у коді

```python
# У маршруті
if current_user.is_admin():
    # Адміністративні операції
    
# У шаблоні
{% if current_user.is_technician() %}
    <!-- Видимо тільки для техніків -->
{% endif %}

# Декоратор
from routes_admin import admin_required

@bp.route('/admin-only')
@admin_required
def admin_only():
    return "Тільки для адміна"
```

### UserService API

```python
from services.user_service import UserService

# Створення
user = UserService.create_user('username', 'email@example.com', 'password', 'technician')

# Отримання
user = UserService.get_user_by_id(1)
user = UserService.get_user_by_username('admin')
user = UserService.get_user_by_email('admin@example.com')

# Аутентифікація
user = UserService.authenticate('username', 'password')

# Обновление
UserService.update_user(1, email='new@example.com', role='admin')

# Видалення
UserService.delete_user(1)

# Отримання за роллю
admins = UserService.get_users_by_role('admin')

# Статистика
total = UserService.count_users()
all_users = UserService.get_all_users()
```

---

## 8️⃣ CSRF захист

**Важливо:** Всі форми мають автоматичний CSRF захист!

```html
<!-- У всіх формах -->
<form method="POST">
    {{ form.hidden_tag() }}  <!-- CSRF токен -->
    <!-- Решта форми -->
</form>
```

---

## 9️⃣ Безпека

- ✅ Паролі хешуються (pbkdf2:sha256)
- ✅ CSRF токени на всіх формах
- ✅ Сесійні куки - HttpOnly + SameSite
- ✅ Валідація всіх входів
- ✅ Проверка прав доступу

---

## 🔟 Документація

- 📖 **SETUP_USERS.md** - Детальне налаштування
- 🧪 **TESTING_GUIDE.md** - Рекомендації з тестування
- 📋 **CHANGES_SUMMARY.md** - Що змінилось

---

## ⚠️ Частые помилки

| Помилка | Рішення |
|---------|--------|
| "CSRF token is missing" | Переконайтеся що форма має `{{ form.hidden_tag() }}` |
| "Password must be at least 8 characters" | Пароль повинен мати 8+ символів |
| "Username already exists" | Виберіть інше ім'я користувача |
| "This email is already registered" | Використайте інший email |
| "Access denied" | Логініться з обліком, що має достатньо прав |

---

## 📞 Отримати допомогу

1. Прочитайте SETUP_USERS.md
2. Проверьте TESTING_GUIDE.md
3. Подивіться логи Flask
4. Зв'яжіться з адміністратором

---

**Готово до роботи!** ✅

Переходьте на http://localhost:5000 та почніть використовувати систему.
