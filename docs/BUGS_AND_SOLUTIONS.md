# Потенційні проблеми та рішення

## Документація розпізнаних багів та стратегій їх вирішення

---

## 1. 🔄 Одночасне редагування (Race Condition)

### Проблема
Два користувачі одночасно переміщають один аплікатор на різні машини. Система записує обидва переміщення, але статус аплікатора неправильний.

### Сценарій
```
T1: Користувач A: Переміщує APP-001 на G01
T2: Користувач B: Переміщує APP-001 на G02
T3: Обидва запити досягають БД
Результат: APP-001 може бути на обох машинах або ні на одній
```

### Рішення
- **Оптимістичне блокування**: Додати версію до запису
- **Песимістичне блокування**: Lock на час операції
- **Transaction isolation**: Використовувати SERIALIZABLE рівень
- **Унікальний статус**: На кожен момент часу аплікатор в одному місці

### Реалізація
```python
# Додати version до моделі
class Applicator(db.Model):
    version = db.Column(db.Integer, default=1)

# При оновленні
def move_applicator(app_id, new_location, expected_version):
    app = Applicator.query.get(app_id)
    if app.version != expected_version:
        raise ConflictError("Дані змінилися")
    app.current_location = new_location
    app.version += 1
    db.session.commit()
```

---

## 2. 📋 Дублювання переміщень

### Проблема
При повільному мережевому з'єднанні користувач натискає "Переместить" два рази. Система записує дві операції для одного переміщення.

### Сценарій
```
T0: POST /machines/add-to-machine
T1: User видить "Loading..." (але сервер ще обробляє)
T2: User натискає кнопку знову (impatience)
T3: POST /machines/add-to-machine (дублікат)
Результат: Два ідентичних записи в історії
```

### Рішення
- **Idempotent operations**: Одна й та ж операція можна повторити без побічних ефектів
- **Request deduplication**: Генерувати UUID для кожного запиту
- **Disable button**: Відключити кнопку після першого натиску
- **Client-side caching**: Кешувати результати запитів

### Реалізація
```python
# На сервері: Таблиця для деліквації
class RequestDedup(db.Model):
    request_id = db.Column(db.String(36), unique=True, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# При обробці
def add_to_machine(request_id, applicator_id, machine_code):
    if RequestDedup.query.get(request_id):
        return {"status": "already_processed"}
    
    # Обробляємо запит
    # ...
    
    # Записуємо що обробили
    RequestDedup.query.create(request_id=request_id)
    db.session.commit()
```

```javascript
// На клієнті: UUID + disable button
function addToMachine(applicatorId, machineCode) {
    const requestId = generateUUID();
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = "Завантаження...";
    
    fetch('/machines/add-to-machine', {
        method: 'POST',
        headers: {'X-Request-ID': requestId},
        body: JSON.stringify({
            applicator_id: applicatorId,
            machine_code: machineCode
        })
    }).finally(() => {
        btn.disabled = false;
        btn.textContent = "Додати";
    });
}
```

---

## 3. 🔐 Втрачена сесія

### Проблема
Користувач заповнює форму, але сесія закінчується. При натиску на "Зберегти", система редирект на логін. Дані втрачаються.

### Сценарій
```
T0: User логується
T1: User відкриває форму редагування
T2: User їсть обід 25 хвилин
T3: User заповнює форму (сесія вже 24+ години)
T4: User натискає "Зберегти"
Результат: Редирект на логін, дані втрачені
```

### Рішення
- **Session refresh**: Оновлювати сесію при кожному запиті
- **Lungo timeout**: Збільшити таймаут сесії
- **Auto-save**: Зберігати чернетку локально
- **Warning**: Попередити користувача перед завершенням сесії

### Реалізація
```python
# config.py
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
SESSION_REFRESH_EACH_REQUEST = True

# routes.py
@app.before_request
def make_session_permanent():
    session.permanent = True
```

```html
<!-- Попередження про завершення сесії -->
<script>
let sessionTimeout;
function resetSessionTimeout() {
    clearTimeout(sessionTimeout);
    sessionTimeout = setTimeout(() => {
        showWarning('Ваша сесія ось-ось завершиться. Збережіть ваші зміни!');
    }, 20 * 60 * 1000); // 20 хвилин
}

document.addEventListener('mousemove', resetSessionTimeout);
document.addEventListener('keypress', resetSessionTimeout);
resetSessionTimeout();
</script>
```

---

## 4. ⛔ Некоректні права доступу

### Проблема
Оператор може отримати доступ до адмін функцій, змінивши URL з `/admin/users` на `/admin` напрямки або маніпулюючи cookies.

### Сценарій
```
Operator: GET /admin/users
Browser: 200 OK (баг!)
Expected: 403 Forbidden
```

### Рішення
- **Decorator checking**: Перевіряти права в кожному маршруті
- **Middleware**: Глобальна перевірка перед кожним запитом
- **Test coverage**: Юніт-тести для кожної ролі

### Реалізація
```python
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def technician_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not (current_user.is_technician() or current_user.is_admin()):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Використання
@admin_bp.route('/users')
@admin_required
def users():
    pass
```

---

## 5. 📊 Перевищення лімітів машин

### Проблема
Система не перевіряє обмеження, дозволяючи додати 6-й аплікатор на машину G01 (макс 5).

### Сценарій
```
Machine G01: 5/5 аплікаторів
User: POST /machines/add-to-machine (6-й)
Result: 6/5 (!!)
```

### Рішення
- **Database constraint**: `CHECK` constraint на БД рівні
- **Application logic**: Перевірка перед INSERT/UPDATE
- **Real-time validation**: Перевірка перед показом форми

### Реалізація
```python
# На БД рівні (SQLite не підтримує CHECK, але у PostgreSQL)
# ALTER TABLE machines ADD CONSTRAINT check_capacity
# CHECK (on_machine_count + on_shelf_count <= max_applicators);

# На рівні додатку
def can_add_applicator(machine_id):
    machine = Machine.query.get(machine_id)
    current_count = machine.on_machine_count + machine.on_shelf_count
    return current_count < machine.max_applicators

# У маршруті
@machines_bp.route('/add-to-machine', methods=['POST'])
def add_to_machine():
    machine_code = request.form.get('machine_code')
    machine = Machine.query.filter_by(code=machine_code).first_or_404()
    
    if not machine.can_add_applicator():
        return jsonify({
            'success': False,
            'message': f'На машині вже {machine.max_applicators} аплікаторів'
        }), 400
    
    # ... додавання
```

---

## 6. 🚨 Конфлікти статусів

### Проблема
Аплікатор має статус `CUTTING` але локація `Aplicator Room`. Система в невизначеному стані.

### Сценарій
```
Applicator.status = CUTTING
Applicator.current_location = Aplicator Room
Applicator.current_machine = NULL
← Невалідна комбінація!
```

### Рішення
- **State machine**: Тільки допустимі переходи
- **Invariants**: Перевіряти умови
- **Enums**: Використовувати типизовані enum'и

### Реалізація
```python
# Допустимі комбінації
VALID_STATES = {
    StatusEnum.AVAILABLE: ['Aplicator Room'],
    StatusEnum.SERVICE: ['Дільниця обслуговування'],
    StatusEnum.CUTTING: ['Дільниця нарізки'],
    StatusEnum.CRIMPING: ['Дільниця кримпування'],
    StatusEnum.BLOCKED: ['Дільниця заблокованих'],
    StatusEnum.INACTIVE: ['Дільниця не використовуються'],
}

def validate_applicator_state(applicator):
    allowed_locations = VALID_STATES.get(applicator.status, [])
    if applicator.current_location not in allowed_locations:
        raise ValueError(f"Невалідна комбінація статусу та локації")

# Перевіряємо перед збереженням
@event.listens_for(Applicator, 'before_update')
def validate_before_update(mapper, connection, target):
    validate_applicator_state(target)
```

---

## 7. 📈 Повільні запити

### Проблема
Вивантаження 100,000 записів з таблиці `movement_history` забирає 30 секунд.

### Сценарій
```
SELECT * FROM movement_history 
WHERE moved_at > '2026-01-01'
LIMIT 10000
→ 30 seconds! (Timeout)
```

### Рішення
- **Indexing**: Індекси на часто використовуваних полях
- **Pagination**: Навіш по 50 записів, не 10,000
- **Caching**: Redis cache для часто запитуваних даних
- **Archiving**: Архівувати старі дані

### Реалізація
```python
# Індекси у моделі
class MovementHistory(db.Model):
    __table_args__ = (
        db.Index('idx_applicator_moved_at', 'applicator_id', 'moved_at'),
        db.Index('idx_moved_at', 'moved_at'),
        db.Index('idx_user_id', 'user_id'),
    )

# Пагінація
def get_history_paginated(page=1, per_page=50, days=30):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    query = MovementHistory.query \
        .filter(MovementHistory.moved_at >= cutoff_date) \
        .order_by(MovementHistory.moved_at.desc())
    return query.paginate(page=page, per_page=per_page)

# Кеширование
from functools import lru_cache
@lru_cache(maxsize=128)
def get_applicator_stats(applicator_id):
    return db.session.query(...).first()
```

---

## 8. 🔐 SQL Injection

### Проблема
Якщо користувач введе `' OR '1'='1`, система виведе всіх користувачів.

### Сценарій
```javascript
// Вхід: username = "' OR '1'='1" password = "x"
// Неправильний код (вразливий):
query = f"SELECT * FROM users WHERE username='{username}'"
// Результат: SELECT * FROM users WHERE username='' OR '1'='1'
```

### Рішення
- **ORM**: Використовувати SQLAlchemy (вже робиться!)
- **Parameterized queries**: Ніколи не конкатенювати рядки
- **Input validation**: Перевіряти входи

### Реалізація
```python
# ✅ ПРАВИЛЬНО (ORM)
user = User.query.filter_by(username=username).first()

# ❌ НЕПРАВИЛЬНО (конкатенація)
user = db.session.query(User).filter(f"username = '{username}'")

# ✅ ПРАВИЛЬНО (параметризовані запити)
user = db.session.query(User).filter(User.username == username).first()
```

---

## 9. 🎯 XSS Attack

### Проблема
Користувач вводит `<script>alert('xss')</script>` у коментар. Скрипт виконується для кожного, хто переглядає цей аплікатор.

### Сценарій
```html
<!-- Коментар містить: -->
<script>fetch('/steal-data')</script>

<!-- Сторінка показує: -->
<p>Коментар: <script>fetch('/steal-data')</script></p>
<!-- Скрипт виконується! -->
```

### Рішення
- **Auto-escaping**: Jinja2 автоматично екранує
- **HTML sanitization**: Бібліотека bleach
- **CSP headers**: Content-Security-Policy
- **HTML encoding**: Кодувати усі користувацькі введення

### Реалізація
```html
<!-- ✅ ПРАВИЛЬНО: Jinja2 автоматично екранує -->
<p>Коментар: {{ applicator.comment }}</p>

<!-- ❌ НЕПРАВИЛЬНО: Небезпечно -->
<p>Коментар: {{ applicator.comment | safe }}</p>
```

```python
from bleach import clean

def sanitize_html(text):
    return clean(text, tags=[], strip=True)

# При збереженні
applicator.comment = sanitize_html(request.form.get('comment'))
```

```python
# CSP headers
@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = \
        "default-src 'self'; script-src 'self' 'unsafe-inline'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response
```

---

## 10. 💾 Втрата даних (Cascade Delete)

### Проблема
При видаленні користувача, видаляються усі його записи про переміщення. Історія втрачена.

### Сценарій
```python
user = User.query.get(5)
db.session.delete(user)
# Каскадно видаляються усі MovementHistory записи користувача 5
```

### Рішення
- **Soft delete**: Просто позначити як видалений
- **Archiving**: Переміщувати старі дані в архів
- **Backup**: Регулярні резервні копії перед видаленням

### Реалізація
```python
# Soft delete
class User(db.Model):
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    @property
    def is_deleted(self):
        return self.deleted_at is not None

def delete_user(user_id):
    user = User.query.get(user_id)
    user.deleted_at = datetime.utcnow()
    db.session.commit()

# Запити автоматично оновлюються
def get_active_users():
    return User.query.filter(User.deleted_at == None).all()
```

```python
# БД миграція
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('movement_history', 
        sa.Column('archived', sa.Boolean(), default=False)
    )

def downgrade():
    op.drop_column('movement_history', 'archived')
```

---

## 11. 🔑 CSRF Attack

### Проблема
Зловмисна сторінка може виконати дію від імені користувача (форма без CSRF токена).

### Сценарій
```html
<!-- На evil.com -->
<img src="http://localhost:5000/applicators/5/block" />
<!-- Якщо користувач авторизований, аплікатор буде заблокований -->
```

### Рішення
- **CSRF tokens**: Додавати унікальні токени до форм
- **Same-site cookies**: SameSite=Strict
- **Double-submit cookie**: Перевіряти cookie і параметр

### Реалізація
```html
<!-- у формах -->
<form method="POST">
    {{ csrf_token() }}
    <!-- інші поля -->
</form>
```

```python
# Flask-WTF розробляє CSRF захист
from flask_wtf.csrf import generate_csrf

@app.route('/form')
def form():
    return render_template('form.html', csrf_token=generate_csrf())
```

```python
# config.py
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = True  # HTTPS only
```

---

## 12. 🌐 Third-party vulnerability

### Проблема
Flask 3.0.0 має вразливість CVE-2024-XXXXX. Система скомпрометована.

### Рішення
- **Keep updated**: Регулярно оновлювати залежності
- **Scanning**: Використовувати tools як safety, snyk
- **Monitoring**: Підписатися на alerts

### Реалізація
```bash
# Перевіряти вразливості
pip install safety
safety check

# Регулярно оновлювати
pip list --outdated
pip install --upgrade flask sqlalchemy werkzeug

# У CI/CD
safety check --json > safety-report.json
```

---

## 13. ⏱️ Timeout

### Проблема
При переміщенні 1000 аплікаторів (batch operation) запит завершується з timeout 504 Gateway Timeout.

### Рішення
- **Async tasks**: Використовувати Celery
- **Batch processing**: Розбити на менші батчи
- **Background jobs**: Обробляти в background
- **Long polling**: Показувати прогрес користувачу

### Реалізація
```python
from celery import Celery

celery = Celery(__name__)

@celery.task
def process_batch_movement(applicator_ids, machine_code):
    for app_id in applicator_ids:
        # Переміщення...
        pass
    return f"Оброблено {len(applicator_ids)} аплікаторів"

# У маршруті
@machines_bp.route('/batch-move', methods=['POST'])
def batch_move():
    task = process_batch_movement.delay(applicator_ids, machine_code)
    return jsonify({'task_id': task.id})

# Перевіряти статус
@machines_bp.route('/batch-move/<task_id>')
def batch_move_status(task_id):
    task = celery.AsyncResult(task_id)
    return jsonify({'status': task.status, 'result': task.result})
```

---

## 14. 🔄 Database Connection Pool

### Проблема
При 100+ одночасних користувачах з'єднання з БД вичерпується. Новий користувач отримує помилку "Too many connections".

### Рішення
- **Connection pooling**: SQLAlchemy вже використовує
- **Pool size**: Налаштувати розмір пула
- **Recyclate**: Переробляти старі з'єднання

### Реалізація
```python
from sqlalchemy import create_engine

engine = create_engine(
    'sqlite:///fujikura_app.db',
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    pool_pre_ping=True,
)

# Flask integration
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': QueuePool,
    'pool_size': 20,
    'max_overflow': 40,
    'pool_recycle': 3600,
}
```

---

## 15. 🛡️ Weak password

### Проблема
Користувач встановлює пароль "123456". Через тиждень акаунт взломаний.

### Рішення
- **Password validation**: Вимагати сильні паролі
- **Rate limiting**: Обмежувати спроби входу
- **MFA**: Multi-factor authentication
- **Password manager**: Интегрувати з password manager

### Реалізація
```python
import re

def validate_password_strength(password):
    if len(password) < 8:
        raise ValueError("Пароль повинен мати мінімум 8 символів")
    if not re.search(r'[A-Z]', password):
        raise ValueError("Пароль повинен мати велику букву")
    if not re.search(r'[a-z]', password):
        raise ValueError("Пароль повинен мати малу букву")
    if not re.search(r'[0-9]', password):
        raise ValueError("Пароль повинен мати цифру")
    if not re.search(r'[!@#$%^&*]', password):
        raise ValueError("Пароль повинен мати спецсимвол")
    return True

# Rate limiting
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # ...
```

---

## 16. 🚀 Database migration

### Проблема
При додаванні нового поля в таблицю з 1 мільйоном записів, операція ALTER TABLE забирає 5 хвилин. Система недоступна.

### Рішення
- **Alembic**: Управління міграціями
- **Zero-downtime**: Нові поля з default значеннями
- **Background migration**: Обновляти в background

### Реалізація
```bash
# Ініціалізація
alembic init alembic

# Створення міграції
alembic revision --autogenerate -m "Add new column"

# Застосування
alembic upgrade head

# Откат
alembic downgrade -1
```

```python
# alembic/versions/001_add_column.py
def upgrade():
    op.add_column('applicators', 
        sa.Column('new_field', sa.String(100), nullable=True, server_default='')
    )

def downgrade():
    op.drop_column('applicators', 'new_field')
```

---

## 17. 📦 Dependency Hell

### Проблема
При оновленні одної залежності, ломаються 5 інших. Версії конфліктують.

### Рішення
- **requirements.txt**: Замороження точних версій
- **Virtual environment**: Ізолювати залежності
- **Testing**: Юніт-тести для кожної версії
- **Docker**: Контейнеризація для консистентності

### Реалізація
```bash
# Замороження точних версій
pip freeze > requirements-locked.txt

# Docker
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

---

## 18. 📊 Monitoring and Logging

### Проблема
Система крахується в 3:00 ночі. Адміністратор не знає що сталось.

### Рішення
- **Logging**: Логування усіх операцій
- **Error tracking**: Sentry для відстеження помилок
- **Monitoring**: Prometheus + Grafana
- **Alerts**: Відправляти email при помилках

### Реалізація
```python
import logging
from logging.handlers import RotatingFileHandler

# Налаштування логування
log_handler = RotatingFileHandler('app.log', maxBytes=10000000, backupCount=10)
log_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s'
))
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)

# Використання
app.logger.info('Користувач залогував: %s', username)
app.logger.error('Помилка: %s', str(e), exc_info=True)
```

```python
# Sentry integration
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://xxx@sentry.io/123456",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

---

## 19. 🔐 Authorization bypass

### Проблема
Користувач може змінити `user_id` в API запиті і отримати доступ до чужих даних.

### Сценарій
```javascript
// Запит користувача 5
fetch('/api/user/5/data')
// Користувач змінює 5 на 10
fetch('/api/user/10/data') // ❌ Доступ!
```

### Рішення
- **Current user**: Завжди використовувати current_user
- **Validation**: Перевіряти що користувач володіє ресурсом
- **Resource ownership**: Перевірка перед операцією

### Реалізація
```python
@app.route('/applicators/<int:applicator_id>/edit', methods=['POST'])
@login_required
def edit_applicator(applicator_id):
    applicator = Applicator.query.get_or_404(applicator_id)
    
    # Перевіряємо що це не чужий ресурс (якщо потрібно)
    # if applicator.owner_id != current_user.id:
    #     abort(403)
    
    # Обновляємо...
    db.session.commit()
```

---

## 20. 🌍 Localization issues

### Проблема
Система показує дати у американському форматі MM/DD/YYYY, але користувачі українські (DD.MM.YYYY).

### Рішення
- **Locale**: Встановити правильну локаль
- **Format**: Форматувати дати правильно
- **i18n**: Internationalization для повноти

### Реалізація
```python
from babel.dates import format_datetime
from flask_babel import Babel

babel = Babel(app)

@app.before_request
def before_request():
    g.locale = 'uk_UA'

# У шаблонах
{{ format_datetime(date, 'dd.MM.yyyy HH:mm', locale='uk_UA') }}
```

---

## 21. 📈 Scalability

### Проблема
При розростанні на 10,000+ користувачів та 1M+ аплікаторів, одиночний сервер не витримує.

### Рішення
- **Load balancing**: Nginx + multiple Flask instances
- **Database replication**: Master-Slave PostgreSQL
- **Caching**: Redis cache layer
- **CDN**: Static files на CDN
- **Microservices**: Розділити додаток на сервіси

### Реалізація (Nginx)
```nginx
upstream flask_app {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

server {
    listen 80;
    server_name fujikura.com;
    
    location / {
        proxy_pass http://flask_app;
        proxy_set_header Host $host;
    }
}
```

---

## 22. 🔑 Secrets management

### Проблема
SECRET_KEY та DATABASE_URL закоммічені в git. Кожен може бачити.

### Рішення
- **.env файли**: Глосити у .gitignore
- **Environment variables**: Читати з оточення
- **Secret manager**: AWS Secrets Manager, HashiCorp Vault
- **Rotation**: Періодично змінювати ключі

### Реалізація
```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///app.db')
```

```bash
# .env
SECRET_KEY=super-secret-key-change-this
DATABASE_URL=postgresql://user:pass@localhost/db
SENTRY_DSN=https://xxx@sentry.io/123456

# .gitignore
.env
.env.local
*.db
```

---

## 📋 Таблиця резюме

| # | Проблема | Серйозність | Рішення |
|---|----------|-------------|---------|
| 1 | Race condition | Висока | Optimistic locking |
| 2 | Дублювання | Середня | Request deduplication |
| 3 | Втрачена сесія | Низька | Auto-save, refresh |
| 4 | Некоректні права | Висока | Decorator checking |
| 5 | Перевищення лімітів | Висока | Validation logic |
| 6 | Конфлікти статусів | Середня | State machine |
| 7 | Повільні запити | Середня | Indexing, caching |
| 8 | SQL injection | Критична | ORM, parameterized |
| 9 | XSS attack | Висока | Auto-escaping |
| 10 | Втрата даних | Критична | Soft delete, backup |
| 11 | CSRF attack | Висока | CSRF tokens |
| 12 | Third-party vuln | Висока | Keep updated |
| 13 | Timeout | Середня | Async tasks |
| 14 | Pool exhaustion | Середня | Connection pooling |
| 15 | Weak password | Середня | Validation, MFA |
| 16 | DB migration | Низька | Alembic |
| 17 | Dependency hell | Низька | requirements.txt |
| 18 | No monitoring | Висока | Logging, Sentry |
| 19 | Auth bypass | Критична | Validation |
| 20 | Localization | Низька | Babel |
| 21 | Scalability | Середня | Load balancing |
| 22 | Secrets leak | Критична | .env files |

---

## 🔍 Рекомендації для лонгтерм-планування

1. **Регулярні security audits** (мінімум раз на квартал)
2. **Continuous monitoring** (Sentry, Prometheus)
3. **Regular backups** (щодня, мінімум 30 днів)
4. **Load testing** (simulated 10x traffic)
5. **Disaster recovery plan** (RTO/RPO визначити)
6. **Team training** на безпеку та best practices
7. **Documentation** усіх систем та процесів

---

*Останнє оновлення: 2026-06-06*
*Версія: 1.0.0*
