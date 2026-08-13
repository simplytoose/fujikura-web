# 📚 Повна Архітектура Fujikura Web System

Це **комплексний опис** всієї системи управління аплікаторами - від конфігурації до найменших деталей.

---

## 📖 Зміст

1. [Огляд системи](#огляд-системи)
2. [Шари архітектури](#шари-архітектури)
3. [Моделі даних](#моделі-даних)
4. [Управління даними](#управління-даними)
5. [Сервіси](#сервіси)
6. [Маршрути (Routes)](#маршрути-routes)
7. [Forms](#forms)
8. [Frontend](#frontend)
9. [Потоки даних](#потоки-даних)
10. [Безпека](#безпека)
11. [Розширюваність](#розширюваність)

---

## Огляд системи

**Fujikura Web** — веб-система для управління аплікаторами на виробництві, побудована на Flask.

### Ключові характеристики:
- ✅ JSON-based сховище (без БД)
- ✅ Рольова система доступу (ADMIN, TECHNICIAN, OPERATOR)
- ✅ Управління переміщеннями аплікаторів
- ✅ Блокування/розблокування аплікаторів
- ✅ Повна історія операцій
- ✅ Система коментарів
- ✅ REST API для операцій

### Стек технологій:
```
┌─────────────────────────────────────────┐
│ Frontend: HTML5/CSS3/JavaScript/Bootstrap│
├─────────────────────────────────────────┤
│ Backend: Flask 3.0, Python 3.12+        │
├─────────────────────────────────────────┤
│ Database: JSON Files в папці data/      │
├─────────────────────────────────────────┤
│ ORM:없음, свої моделі в models.py      │
├─────────────────────────────────────────┤
│ Auth: Flask-Login, Session-based        │
├─────────────────────────────────────────┤
│ Forms: Flask-WTF з валідацією           │
└─────────────────────────────────────────┘
```

---

## Шари архітектури

### Многошарова архітектура (Layered Architecture)

```
層 1: Presentation Layer (UI)
    ├─ templates/base.html (базовий шаблон)
    ├─ templates/applicators/*.html (шаблони аплікаторів)
    ├─ templates/machines/*.html (шаблони машин)
    ├─ templates/history/*.html (шаблони історії)
    └─ static/js/main.js (JavaScript)

層 2: Control Layer (Routes & Forms)
    ├─ routes_applicators.py (контролер аплікаторів)
    ├─ routes_machines.py (контролер машин)
    ├─ routes_auth.py (контролер аутентифікації)
    ├─ routes_admin.py (контролер адмін)
    ├─ routes_dashboard.py, history.py, тощо
    └─ forms.py (WTF форми)

層 3: Business Logic Layer (Services)
    ├─ applicator_service.py (логіка аплікаторів)
    ├─ user_service.py (логіка користувачів)
    ├─ machine_service.py (логіка машин)
    ├─ movement_service.py (логіка переміщень)
    ├─ room_service.py (логіка кімнати)
    ├─ production_service.py (логіка виробництва)
    ├─ validation_service.py (валідація)
    └─ movement_service.py (BlockingService для блокування)

層 4: Data Access Layer (DataManager)
    └─ data_manager.py (универсальний менеджер JSON)

層 5: Persistence Layer (JSON Files)
    ├─ data/applicators.json
    ├─ data/users.json
    ├─ data/machines.json
    ├─ data/movements.json
    ├─ data/blocking_history.json
    ├─ data/rooms.json
    └─ data/settings.json
```

---

## Моделі даних

### `models.py` - Визначення всіх моделей

#### 1. **RoleEnum** - Ролі користувачів
```python
class RoleEnum(Enum):
    ADMIN = "admin"           # Адміністратор - повний доступ
    TECHNICIAN = "technician" # Технік - управління аплікаторами
    OPERATOR = "operator"     # Оператор - тільки перегляд
```

#### 2. **StatusEnum** - Статуси аплікаторів
```python
class StatusEnum(Enum):
    AVAILABLE = "AVAILABLE"   # Доступний, можна використовувати
    SERVICE = "SERVICE"       # На обслуговуванні
    CUTTING = "CUTTING"       # На машині G01-G30 (нарізка)
    CRIMPING = "CRIMPING"     # На машині P01-P05 (кримпування)
    BLOCKED = "BLOCKED"       # Заблокований (несправний)
    INACTIVE = "INACTIVE"     # Неактивний (не використовується)
```

#### 3. **User** - Модель користувача
```python
class User(UserMixin):
    id                 # ID користувача
    username          # Ім'я для входу
    email             # Email
    password_hash     # Хеш пароля (PBKDF2:SHA256)
    role              # Роль (admin/technician/operator)
    is_active         # Активний користувач
    created_at        # Дата створення
    last_login        # Останній вхід
    
    # Методи:
    set_password(password)      # Хешувати пароль
    check_password(password)    # Перевірити пароль
    is_admin()                  # Перевірити роль
    is_technician()
    is_operator()
    to_dict()                   # Конвертувати в JSON
    @staticmethod from_dict()   # Конвертувати з JSON
```

**JSON приклад:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@fujikura.local",
  "password_hash": "pbkdf2:sha256:600000$...",
  "role": "admin",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "last_login": "2024-06-15T14:00:00"
}
```

#### 4. **Applicator** - Модель аплікатора (НАЙВАЖЛИВІША)
```python
class Applicator:
    id                    # ID аплікатора
    code                  # Код (G01, P02, тощо)
    name                  # Назва (опціонально)
    location              # Локація (Aplicator Room, Service, Cutting, тощо)
    status                # Статус (AVAILABLE, BLOCKED, CUTTING, тощо)
    machine               # На якій машині (машина, на якій установлений)
    shelf_position        # Позиція на полиці
    cell_number           # Номер комірки у Aplicator Room (1-300)
    
    # Конфігурація
    is_configured         # Чи налагоджений (true/false)
    configured_by         # Хто налагоджував (user_id)
    configured_at         # Коли налагоджувався
    
    # Статус розташування
    on_machine            # true, якщо на машині
    on_shelf              # true, якщо на полиці
    
    # Блокування
    blocked_reason        # Причина блокування
    blocked_by            # Хто заблокував (user_id)
    blocked_at            # Коли заблокований
    
    # Інактивність
    inactive_reason       # Причина інактивності
    inactive_by           # Хто позначив неактивним
    inactive_at           # Коли позначений неактивним
    
    # Інше
    technician_id         # Технік, що має аплікатор
    created_at            # Коли створений
    last_moved_at         # Коли останній раз переміщено
    notes                 # Нотатки
    comments              # Список коментарів [{id, author, text, created_at}, ...]
    
    # Методи:
    to_dict()             # Конвертувати в JSON
    @staticmethod from_dict()  # Конвертувати з JSON
```

**JSON приклад:**
```json
{
  "id": 1,
  "code": "G01",
  "name": "Applicator G01",
  "location": "Aplicator Room",
  "status": "AVAILABLE",
  "machine": null,
  "shelf_position": null,
  "cell_number": 1,
  "is_configured": false,
  "configured_by": null,
  "configured_at": null,
  "on_machine": false,
  "on_shelf": false,
  "blocked_reason": null,
  "blocked_by": null,
  "blocked_at": null,
  "inactive_reason": null,
  "inactive_by": null,
  "inactive_at": null,
  "technician_id": null,
  "created_at": "2024-01-01T10:00:00",
  "last_moved_at": "2024-01-01T10:00:00",
  "notes": "",
  "comments": []
}
```

#### 5. **Machine** - Модель машини
```python
class Machine:
    id              # ID
    code            # Код (G01, G30, P01, P05, тощо)
    type            # Тип: "cutting" (нарізка) або "crimping" (кримпування)
    location        # Локація
    max_capacity    # Макс. аплікаторів на машині (5 для cutting, 3 для crimping)
    applicators     # Список ID аплікаторів на машині
    created_at      # Дата створення
    
    # Методи:
    get_total_applicators()  # Кількість аплікаторів
    is_full()                # Чи заповнена машина
    to_dict()
    @staticmethod from_dict()
```

**JSON приклад:**
```json
{
  "id": 1,
  "code": "G01",
  "type": "cutting",
  "location": "Cutting Section",
  "max_capacity": 5,
  "applicators": [1, 2, 3],
  "created_at": "2024-01-01T10:00:00"
}
```

#### 6. **MovementRecord** - Запис про переміщення
```python
class MovementRecord:
    id               # ID запису
    applicator_id    # ID аплікатора
    applicator_code  # Код аплікатора (G01)
    from_location    # Звідки переміщено
    to_location      # Куди переміщено
    from_machine     # З якої машини
    to_machine       # На яку машину
    user_id          # Хто переміщував (user_id)
    username         # Ім'я користувача
    moved_at         # Коли переміщено
    comment          # Коментар до переміщення
```

**JSON приклад:**
```json
{
  "id": 1,
  "applicator_id": 1,
  "applicator_code": "G01",
  "from_location": "Aplicator Room",
  "to_location": "Service",
  "from_machine": null,
  "to_machine": null,
  "user_id": 2,
  "username": "tech1",
  "moved_at": "2024-06-15T14:30:00",
  "comment": "For maintenance"
}
```

#### 7. **BlockingRecord** - Запис про блокування
```python
class BlockingRecord:
    id               # ID
    applicator_id    # ID аплікатора
    applicator_code  # Код
    reason           # Причина блокування
    user_id          # Хто заблокував
    username         # Ім'я користувача
    created_at       # Коли заблокований
    is_blocked       # true = заблокований, false = розблокований
```

#### 8. **Location** - Модель локації
```python
class Location:
    code        # Код локації
    name        # Назва
    description # Опис
    
    # Предефіновані локації:
    LOCATIONS = {
        'Aplicator Room': 'Основне сховище (300 комірок)',
        'Service': 'Дільниця обслуговування',
        'Cutting': 'Дільниця нарізки (G01-G30)',
        'Crimping': 'Дільниця кримпування (P01-P05)',
        'Blocked': 'Заблоковані аплікатори',
        'Inactive': 'Аплікатори без використання'
    }
```

#### 9. **ApplicatorCell** - Комірка в Aplicator Room
```python
class ApplicatorCell:
    id              # ID комірки
    cell_number     # Номер комірки (1-300)
    is_occupied     # true, якщо зайнята
    applicator_id   # ID аплікатора в комірці
    created_at      # Коли створена
```

#### 10. **ApplicatorComment** - Коментар до аплікатора
```python
class ApplicatorComment:
    id              # ID коментаря
    applicator_id   # ID аплікатора
    author          # Хто написав
    text            # Текст коментаря
    created_at      # Коли написаний
    updated_at      # Коли оновлено
```

#### 11. **ServiceAreaConfirmation** - Підтвердження налаштування
```python
class ServiceAreaConfirmation:
    id               # ID
    applicator_id    # ID аплікатора
    applicator_code  # Код
    is_configured    # Налагоджений
    confirmed_by     # Хто підтвердив
    confirmed_at     # Коли
```

#### 12. **InactiveRecord** - Запис про неактивність
```python
class InactiveRecord:
    id               # ID
    applicator_id    # ID аплікатора
    applicator_code  # Код
    reason           # Причина
    marked_by        # Хто позначив
    marked_at        # Коли
    is_inactive      # true/false
```

---

## Управління даними

### `config.py` - Конфігурація

```python
class Config:
    """Базова конфігурація"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DATA_DIR = os.environ.get('DATA_DIR') or 'data'  # Папка з JSON файлами
    
    # Session
    SESSION_COOKIE_HTTPONLY = True           # Не доступний з JS
    SESSION_COOKIE_SAMESITE = 'Lax'          # CSRF захист
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Сесія на 7 днів
    
    # CSRF
    WTF_CSRF_ENABLED = True                  # CSRF захист включено
    WTF_CSRF_TIME_LIMIT = None               # Без ліміту часу для CSRF
    
    # JSON
    JSON_SORT_KEYS = False                   # Не сортувати ключі
    JSONIFY_PRETTYPRINT_REGULAR = True       # Красивий JSON в відповідях

class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True             # Тільки HTTPS

class TestingConfig(Config):
    TESTING = True
    DATA_DIR = 'test_data'                   # Окремі тестові дані
```

### `data_manager.py` - Універсальний менеджер JSON

Це **ядро всієї системи** для роботи з JSON файлами. Забезпечує CRUD операції та багато корисних методів.

```python
class DataManager:
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir                    # Папка з JSON
        self.lock = threading.Lock()                # Thread-safe доступ
        self._ensure_directory()
    
    # Базові методи:
    
    def load_file(self, table: str) -> Dict:
        """Завантажити JSON файл
        Повертає {} якщо файл не існує"""
        file_path = self._get_file_path(table)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_file(self, table: str, data: Dict):
        """Зберегти дані в JSON файл"""
        with self.lock:  # Thread safety
            file_path = self._get_file_path(table)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    # CRUD операції:
    
    def create(self, table: str, data: Dict) -> Dict:
        """Створити новий запис з автоматичним ID"""
        file_data = self.load_file(table)
        record = {
            'id': self._get_next_id(table),
            **data,
            'created_at': datetime.utcnow().isoformat()
        }
        if 'records' not in file_data:
            file_data['records'] = []
        file_data['records'].append(record)
        self.save_file(table, file_data)
        return record
    
    def read(self, table: str, record_id: int) -> Optional[Dict]:
        """Прочитати один запис за ID"""
        file_data = self.load_file(table)
        for record in file_data.get('records', []):
            if record.get('id') == record_id:
                return record
        return None
    
    def update(self, table: str, record_id: int, data: Dict) -> Optional[Dict]:
        """Оновити запис"""
        file_data = self.load_file(table)
        for i, record in enumerate(file_data.get('records', [])):
            if record.get('id') == record_id:
                record.update(data)
                record['updated_at'] = datetime.utcnow().isoformat()
                self.save_file(table, file_data)
                return record
        return None
    
    def delete(self, table: str, record_id: int) -> bool:
        """Видалити запис"""
        file_data = self.load_file(table)
        for i, record in enumerate(file_data.get('records', [])):
            if record.get('id') == record_id:
                del file_data['records'][i]
                self.save_file(table, file_data)
                return True
        return False
    
    # Пошукові методи:
    
    def list(self, table: str, filters: Dict = None,
             sort_by: str = 'id', sort_desc: bool = False) -> List[Dict]:
        """Список записів з фільтруванням та сортуванням"""
        file_data = self.load_file(table)
        records = file_data.get('records', [])
        
        # Фільтрування
        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    records = [r for r in records if r.get(key) in value]
                else:
                    records = [r for r in records if r.get(key) == value]
        
        # Сортування
        if sort_by:
            records = sorted(records,
                           key=lambda r: (r.get(sort_by) is not None, r.get(sort_by, '')),
                           reverse=sort_desc)
        
        return records
    
    def search(self, table: str, field: str, query: str) -> List[Dict]:
        """Пошук записів по полю (like '%query%')"""
        file_data = self.load_file(table)
        results = []
        query_lower = query.lower()
        
        for record in file_data.get('records', []):
            value = str(record.get(field, '')).lower()
            if query_lower in value:
                results.append(record)
        
        return results
    
    def find_by_field(self, table: str, field: str, value: Any) -> Optional[Dict]:
        """Знайти перший запис за значенням поля"""
        records = self.list(table, {field: value})
        return records[0] if records else None
    
    def find_all_by_field(self, table: str, field: str, value: Any) -> List[Dict]:
        """Знайти всі записи за значенням поля"""
        return self.list(table, {field: value})
    
    def count(self, table: str, filters: Dict = None) -> int:
        """Лічити записи"""
        return len(self.list(table, filters))
    
    def get_all(self, table: str) -> List[Dict]:
        """Отримати всі записи"""
        return self.list(table)
    
    # Спеціальні методи:
    
    def cleanup_old_records(self, table: str, days: int, 
                           date_field: str = 'created_at') -> int:
        """Видалити записи старші за кількість днів"""
        file_data = self.load_file(table)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        initial_count = len(file_data['records'])
        
        filtered_records = []
        for record in file_data['records']:
            try:
                record_date = datetime.fromisoformat(
                    record.get(date_field, '').replace('Z', '+00:00')
                )
                if record_date > cutoff_date:
                    filtered_records.append(record)
            except:
                filtered_records.append(record)
        
        file_data['records'] = filtered_records
        self.save_file(table, file_data)
        return initial_count - len(filtered_records)
```

### JSON файли у папці `data/`

```
data/
├── applicators.json         # Всі аплікатори
│   └─ records: [Applicator, ...]
│
├── users.json              # Всі користувачі
│   └─ records: [User, ...]
│
├── machines.json           # Всі машини
│   └─ records: [Machine, ...]
│
├── movements.json          # Вся історія переміщень
│   └─ records: [MovementRecord, ...]
│
├── blocking_history.json   # Вся історія блокування
│   └─ records: [BlockingRecord, ...]
│
├── applicator_cells.json   # Комірки Aplicator Room
│   └─ records: [ApplicatorCell, ...]
│
├── service_confirmations.json # Підтвердження налаштування
│   └─ records: [ServiceAreaConfirmation, ...]
│
├── inactive_applicators.json  # Історія неактивності
│   └─ records: [InactiveRecord, ...]
│
└── settings.json           # Налаштування (счетчики ID)
    └─ last_applicators_id: N
       last_users_id: N
       ...
```

---

## Сервіси

Папка `services/` містить всю бізнес-логіку. Кожен сервіс — це набір статичних методів для роботи з однією сутністю.

### `user_service.py` - UserService

```python
class UserService:
    @staticmethod
    def create_user(username, email, password, role='operator') -> User:
        """Створити нового користувача"""
        if UserService.user_exists(username):
            return None
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        created = dm.create('users', user.to_dict())
        return User.from_dict(created)
    
    @staticmethod
    def get_user_by_id(user_id) -> User:
        """Отримати користувача за ID"""
        data = dm.read('users', user_id)
        return User.from_dict(data) if data else None
    
    @staticmethod
    def get_user_by_username(username) -> User:
        """Отримати користувача за ім'ям"""
        data = dm.find_by_field('users', 'username', username)
        return User.from_dict(data) if data else None
    
    @staticmethod
    def authenticate(username, password) -> User:
        """Аутентифікувати користувача (для login)"""
        user = UserService.get_user_by_username(username)
        if user and user.check_password(password):
            UserService.update_last_login(user.id)
            return user
        return None
    
    @staticmethod
    def get_all_users() -> List[User]:
        """Отримати всіх користувачів"""
        return [User.from_dict(u) for u in dm.get_all('users')]
    
    @staticmethod
    def update_user(user_id, **kwargs) -> User:
        """Оновити користувача"""
        data = {}
        if 'email' in kwargs:
            data['email'] = kwargs['email']
        if 'role' in kwargs:
            data['role'] = kwargs['role']
        if 'password' in kwargs:
            user = UserService.get_user_by_id(user_id)
            user.set_password(kwargs['password'])
            data['password_hash'] = user.password_hash
        updated = dm.update('users', user_id, data)
        return User.from_dict(updated) if updated else None
    
    @staticmethod
    def delete_user(user_id) -> bool:
        """Видалити користувача"""
        return dm.delete('users', user_id)
```

### `applicator_service.py` - ApplicatorService (ГОЛОВНИЙ СЕРВІС)

Це **найбільш важливий сервіс** — управління аплікаторами.

```python
class ApplicatorService:
    
    @staticmethod
    def create_applicator(code, name=None, location="Aplicator Room", 
                         status=StatusEnum.AVAILABLE.value, notes="") -> Applicator:
        """Створити новий аплікатор"""
        applicator = Applicator(code=code, name=name or code, 
                               location=location, status=status, notes=notes)
        created = dm.create('applicators', applicator.to_dict())
        applicator = Applicator.from_dict(created)
        
        # Присвоїти комірку в Aplicator Room
        if location == "Aplicator Room":
            ApplicatorService._assign_room_cell(applicator.id)
        
        return ApplicatorService.get_applicator(applicator.id)
    
    @staticmethod
    def get_applicator(app_id) -> Applicator:
        """Отримати аплікатор за ID"""
        data = dm.read('applicators', app_id)
        return Applicator.from_dict(data) if data else None
    
    @staticmethod
    def get_applicator_by_code(code) -> Applicator:
        """Отримати аплікатор за кодом (G01, P02, тощо)"""
        data = dm.find_by_field('applicators', 'code', code)
        return Applicator.from_dict(data) if data else None
    
    @staticmethod
    def update_applicator(app_id, **kwargs) -> Applicator:
        """Оновити аплікатор"""
        allowed_keys = ['location', 'status', 'machine', 'shelf_position', 'notes',
                       'last_moved_at', 'technician_id', 'name', 'cell_number',
                       'is_configured', 'configured_by', 'configured_at',
                       'on_machine', 'on_shelf', 'blocked_reason', 'blocked_by',
                       'blocked_at', 'inactive_reason', 'inactive_by',
                       'inactive_at', 'comments']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_keys}
        updated = dm.update('applicators', app_id, update_data)
        return Applicator.from_dict(updated) if updated else None
    
    @staticmethod
    def delete_applicator(app_id) -> bool:
        """Видалити аплікатор та всі його записи"""
        applicator = ApplicatorService.get_applicator(app_id)
        if not applicator:
            return False
        
        # Звільнити комірку
        if applicator.cell_number:
            ApplicatorRoomService.free_cell(applicator.cell_number)
        
        # Видалити пов'язані записи
        for table in ('movements', 'blocking_history', 'service_confirmations', 'inactive_applicators'):
            ApplicatorService._purge_related_records(table, 'applicator_id', app_id)
        
        return dm.delete('applicators', app_id)
    
    @staticmethod
    def get_all_applicators() -> List[Applicator]:
        """Отримати всіх аплікаторів"""
        return [Applicator.from_dict(a) for a in dm.get_all('applicators')]
    
    @staticmethod
    def get_applicators_by_location(location) -> List[Applicator]:
        """Отримати аплікатори в локації"""
        apps_data = dm.list('applicators', {'location': location})
        return [Applicator.from_dict(a) for a in apps_data]
    
    @staticmethod
    def get_applicators_by_status(status) -> List[Applicator]:
        """Отримати аплікатори зі статусом"""
        apps_data = dm.list('applicators', {'status': status})
        return [Applicator.from_dict(a) for a in apps_data]
    
    @staticmethod
    def block_applicator(app_id, reason="") -> Applicator:
        """Заблокувати аплікатор"""
        return ApplicatorService.update_applicator(
            app_id, 
            status=StatusEnum.BLOCKED.value,
            notes=reason
        )
    
    @staticmethod
    def unblock_applicator(app_id) -> Applicator:
        """Розблокувати аплікатор"""
        return ApplicatorService.update_applicator(
            app_id, 
            status=StatusEnum.AVAILABLE.value
        )
    
    @staticmethod
    def is_blocked(app_id) -> bool:
        """Перевірити, чи аплікатор заблокований"""
        app = ApplicatorService.get_applicator(app_id)
        return app and app.status == StatusEnum.BLOCKED.value
    
    @staticmethod
    def get_statistics() -> Dict:
        """Отримати статистику по статусам"""
        return {
            'total': ApplicatorService.count_applicators(),
            'available': dm.count('applicators', {'status': StatusEnum.AVAILABLE.value}),
            'service': dm.count('applicators', {'status': StatusEnum.SERVICE.value}),
            'cutting': dm.count('applicators', {'status': StatusEnum.CUTTING.value}),
            'crimping': dm.count('applicators', {'status': StatusEnum.CRIMPING.value}),
            'blocked': dm.count('applicators', {'status': StatusEnum.BLOCKED.value}),
            'inactive': dm.count('applicators', {'status': StatusEnum.INACTIVE.value}),
        }
    
    @staticmethod
    def add_comment(app_id, author, text) -> Applicator:
        """Додати коментар до аплікатора"""
        app = ApplicatorService.get_applicator(app_id)
        if not app:
            return None
        
        comment = {
            'id': datetime.utcnow().timestamp(),
            'author': author,
            'text': text,
            'created_at': datetime.utcnow().isoformat()
        }
        
        if not app.comments:
            app.comments = []
        app.comments.append(comment)
        
        return ApplicatorService.update_applicator(app_id, comments=app.comments)
    
    @staticmethod
    def search_applicators(query) -> List[Applicator]:
        """Пошук аплікаторів по коду або нотаткам"""
        results = dm.search('applicators', 'code', query)
        results += dm.search('applicators', 'notes', query)
        
        # Видалити дублікати
        seen = set()
        unique = []
        for r in results:
            if r['id'] not in seen:
                unique.append(r)
                seen.add(r['id'])
        
        return [Applicator.from_dict(a) for a in unique]
```

### `movement_service.py` - MovementService та BlockingService

```python
class MovementService:
    @staticmethod
    def record_movement(applicator_id, applicator_code, from_location, 
                       to_location, user_id, username, comment=""):
        """Записати переміщення аплікатора"""
        movement = {
            'applicator_id': applicator_id,
            'applicator_code': applicator_code,
            'from_location': from_location,
            'to_location': to_location,
            'from_machine': None,
            'to_machine': None,
            'user_id': user_id,
            'username': username,
            'moved_at': datetime.utcnow().isoformat(),
            'comment': comment
        }
        return dm.create('movements', movement)
    
    @staticmethod
    def get_movements_by_applicator(app_id, limit=50):
        """Отримати переміщення аплікатора"""
        movements = dm.list('movements', {'applicator_id': app_id}, 
                          sort_by='moved_at', sort_desc=True)
        return movements[:limit]
    
    @staticmethod
    def get_all_movements(limit=100):
        """Отримати всі переміщення"""
        return dm.list('movements', sort_by='moved_at', 
                      sort_desc=True)[:limit]

class BlockingService:
    @staticmethod
    def record_blocking(applicator_id, applicator_code, user_id, username, reason=""):
        """Записати блокування"""
        blocking = {
            'applicator_id': applicator_id,
            'applicator_code': applicator_code,
            'reason': reason,
            'user_id': user_id,
            'username': username,
            'created_at': datetime.utcnow().isoformat(),
            'is_blocked': True
        }
        return dm.create('blocking_history', blocking)
    
    @staticmethod
    def record_unblocking(applicator_id, applicator_code, user_id, username):
        """Записати розблокування"""
        blocking = {
            'applicator_id': applicator_id,
            'applicator_code': applicator_code,
            'reason': 'Розблоковано',
            'user_id': user_id,
            'username': username,
            'created_at': datetime.utcnow().isoformat(),
            'is_blocked': False
        }
        return dm.create('blocking_history', blocking)
    
    @staticmethod
    def get_blocking_history_for_applicator(app_id):
        """Отримати історію блокування аплікатора"""
        return dm.list('blocking_history', {'applicator_id': app_id}, 
                      sort_by='created_at', sort_desc=True)
```

### `machine_service.py` - MachineService

```python
class MachineService:
    @staticmethod
    def get_machine(machine_id) -> Machine:
        """Отримати машину"""
        data = dm.read('machines', machine_id)
        return Machine.from_dict(data) if data else None
    
    @staticmethod
    def get_all_machines() -> List[Machine]:
        """Отримати всі машини"""
        machines_data = dm.get_all('machines')
        return [Machine.from_dict(m) for m in machines_data]
    
    @staticmethod
    def get_machines_by_type(machine_type) -> List[Machine]:
        """Отримати машини певного типу"""
        machines_data = dm.list('machines', {'type': machine_type})
        return [Machine.from_dict(m) for m in machines_data]
    
    @staticmethod
    def is_full(machine_id) -> bool:
        """Перевірити, чи машина заповнена"""
        machine = MachineService.get_machine(machine_id)
        return machine and machine.full
```

### `room_service.py` - ApplicatorRoomService

```python
class ApplicatorRoomService:
    @staticmethod
    def initialize_cells():
        """Ініціалізувати 300 комірок Aplicator Room"""
        cells = dm.get_all('applicator_cells')
        if len(cells) == 0:
            for i in range(1, 301):
                dm.create('applicator_cells', {
                    'cell_number': i,
                    'is_occupied': False,
                    'applicator_id': None
                })
    
    @staticmethod
    def assign_cell(applicator_id):
        """Присвоїти вільну комірку аплікатору"""
        ApplicatorRoomService.initialize_cells()
        cells = dm.list('applicator_cells', {'is_occupied': False})
        if cells:
            cell = cells[0]
            dm.update('applicator_cells', cell['id'], {
                'is_occupied': True,
                'applicator_id': applicator_id
            })
            return ApplicatorCell.from_dict(cell)
        return None
    
    @staticmethod
    def free_cell(cell_number):
        """Звільнити комірку"""
        cells = dm.list('applicator_cells', {'cell_number': cell_number})
        if cells:
            cell = cells[0]
            dm.update('applicator_cells', cell['id'], {
                'is_occupied': False,
                'applicator_id': None
            })
```

---

## Маршрути (Routes)

Файли `routes_*.py` — це Flask Blueprints, які обробляють HTTP запити.

### Структура Blueprint

```python
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.applicator_service import ApplicatorService
# ...

# Створити blueprint
applicators_bp = Blueprint('applicators', __name__, url_prefix='/applicators')

# Декоратори для контролю доступу
def technician_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not (current_user.is_technician() or current_user.is_admin()):
            flash('Ви не маєте доступу до цієї сторінки', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin():
            flash('Ви не маєте доступу до цієї сторінки', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Маршрути...
```

### `routes_applicators.py` - Основні маршрути аплікаторів

**1. Список аплікаторів**
```python
@applicators_bp.route('/')
@login_required
def list_applicators():
    """GET /applicators/ — Показ всіх аплікаторів"""
    # Параметри:
    # ?status=AVAILABLE     # Фільтр по статусу
    # ?location=Service     # Фільтр по локації
    # ?search=G01           # Пошук
    # ?page=2               # Сторінка
    
    # Поворот: templates/applicators/list.html
    #   - applicators: List[Applicator]
    #   - pagination: Pagination object
    #   - status_filter, location_filter, search
```

**2. Деталі аплікатора**
```python
@applicators_bp.route('/<int:applicator_id>')
@login_required
def applicator_detail(applicator_id):
    """GET /applicators/<id> — Показ деталей аплікатора"""
    # Поворот: templates/applicators/detail.html
    #   - applicator: Applicator
    #   - history: List[MovementRecord]
    #   - blocking_history: List[BlockingRecord]
```

**3. Додавання аплікатора**
```python
@applicators_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_applicator():
    """GET  /applicators/add  — Форма додавання
       POST /applicators/add  — Criar новий аплікатор"""
    # POST параметри:
    #   - code: str (G01)
    #   - name: str (опціонально)
```

**4. Редагування аплікатора**
```python
@applicators_bp.route('/edit/<int:applicator_id>', methods=['GET', 'POST'])
@admin_required
def edit_applicator(applicator_id):
    """GET  /applicators/edit/<id> — Форма редагування
       POST /applicators/edit/<id> — Оновити"""
    # POST параметри:
    #   - name: str
    #   - notes: str
```

**5. Видалення аплікатора**
```python
@applicators_bp.route('/<int:applicator_id>/delete', methods=['POST'])
@admin_required
def delete_applicator(applicator_id):
    """POST /applicators/<id>/delete — Видалити аплікатор"""
    # Повертає: redirect на список
```

**6. Блокування аплікатора**
```python
@applicators_bp.route('/<int:applicator_id>/block', methods=['POST'])
@login_required
def block_applicator(applicator_id):
    """POST /applicators/<id>/block — Заблокувати аплікатор"""
    # POST параметри:
    #   - reason: str
    # Повертає: JSON {'success': true/false, 'message': '...'}
```

**7. Розблокування**
```python
@applicators_bp.route('/<int:applicator_id>/unblock', methods=['POST'])
@login_required
def unblock_applicator(applicator_id):
    """POST /applicators/<id>/unblock — Розблокувати"""
    # Повертає: JSON
```

**8. Підтвердження обслуговування**
```python
@applicators_bp.route('/<int:applicator_id>/confirm-service', methods=['POST'])
@login_required
def confirm_service(applicator_id):
    """POST /applicators/<id>/confirm-service — Завершити обслуговування"""
    # Змінює статус з SERVICE на AVAILABLE
```

**9. Коментарі**
```python
@applicators_bp.route('/<int:applicator_id>/comments', methods=['GET'])
@login_required
def get_comments(applicator_id):
    """GET /applicators/<id>/comments — Список коментарів"""
    # Повертає: JSON {'success': true, 'comments': [...]}

@applicators_bp.route('/<int:applicator_id>/comment', methods=['POST'])
@login_required
def add_comment(applicator_id):
    """POST /applicators/<id>/comment — Додати коментар"""
    # JSON параметри:
    #   - text: str
    # Повертає: JSON

@applicators_bp.route('/<int:applicator_id>/comment/<comment_id>', methods=['DELETE'])
@login_required
def delete_comment(applicator_id, comment_id):
    """DELETE /applicators/<id>/comment/<cid> — Видалити коментар"""
    # Повертає: JSON
```

### Інші маршрути

```
routes_auth.py:
  GET    /auth/login        → login сторінка
  POST   /auth/login        → authenticate
  GET    /auth/logout       → logout
  GET    /auth/register     → register сторінка
  POST   /auth/register     → створити користувача

routes_machines.py:
  GET    /machines          → список машин
  GET    /machines/<id>     → деталі машини
  POST   /machines/<id>/status → оновити статус

routes_history.py:
  GET    /history           → вся історія переміщень
  GET    /history/filter    → фільтрована історія

routes_admin.py:
  GET    /admin             → адмін панель
  POST   /admin/users/create → створити користувача
  GET    /admin/users/<id>/edit → редагування користувача
  POST   /admin/users/<id>/delete → видалити користувача

routes_dashboard.py:
  GET    /dashboard         → головна сторінка зі статистикою

routes_locations.py:
  GET    /locations         → список дільниць
  GET    /locations/<name>  → аплікатори на дільниці

routes_applicator_room.py:
  GET    /applicator-room   → стан кімнати аплікаторів
  POST   /applicator-room/add → додати до кімнати

routes_service_area.py:
  GET    /service-area      → сервісна дільниця

routes_production.py:
  GET    /production        → виробнича статистика

routes_management.py:
  GET    /management        → управління та звіти
```

---

## Forms

Файл `forms.py` — валідовані WTF форми для всіх операцій.

```python
# Форми для входу
class LoginForm(FlaskForm):
    username = StringField('Ім\'я користувача', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запам\'ятати мене')
    submit = SubmitField('Вхід')

# Форма реєстрації
class RegistrationForm(FlaskForm):
    username = StringField('Ім\'я користувача',
                          validators=[DataRequired(), 
                                    Length(min=3, max=20),
                                    Regexp('^[A-Za-z0-9_]+$')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Підтвердити пароль',
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зареєструватися')

# Адмін форма для створення користувача
class AdminCreateUserForm(FlaskForm):
    username = StringField('Ім\'я користувача', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=8)])
    role = SelectField('Роль', 
                       choices=[('technician', 'Технік'),
                               ('operator', 'Оператор'),
                               ('admin', 'Адміністратор')],
                       validators=[DataRequired()])
    submit = SubmitField('Створити користувача')

# Форма редагування користувача
class EditUserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Роль', choices=[...], validators=[DataRequired()])
    password = PasswordField('Новий пароль (залиште порожнім)',
                           validators=[Length(min=8)])
    submit = SubmitField('Зберегти зміни')
```

---

## Frontend

### `base.html` — Базовий шаблон

Містить Bootstrap 5 структуру, навігацію та основні компоненти.

```html
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Fujikura Web{% endblock %}</title>
    
    <!-- Bootstrap 5 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Custom CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Навігаційна панель -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="{{ url_for('dashboard.dashboard') }}">
                <span class="badge bg-danger">Fujikura Web</span>
            </a>
            
            {% if current_user.is_authenticated %}
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarMenu">
                    <span class="navbar-toggler-icon"></span>
                </button>
                
                <div class="collapse navbar-collapse" id="navbarMenu">
                    <ul class="navbar-nav ms-auto">
                        <!-- Посилання залежать від ролі користувача -->
                        {% if current_user.is_admin() or current_user.is_technician() %}
                            <li class="nav-item">
                                <a class="nav-link" href="{{ url_for('applicators.list_applicators') }}">
                                    Аплікатори
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="{{ url_for('machines.list_machines') }}">
                                    Машини
                                </a>
                            </li>
                        {% endif %}
                        
                        {% if current_user.is_admin() %}
                            <li class="nav-item">
                                <a class="nav-link" href="{{ url_for('admin.panel') }}">
                                    Адмін
                                </a>
                            </li>
                        {% endif %}
                        
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('history.list_history') }}">
                                Історія
                            </a>
                        </li>
                        
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('auth.logout') }}">
                                Вихід ({{ current_user.username }})
                            </a>
                        </li>
                    </ul>
                </div>
            {% endif %}
        </div>
    </nav>
    
    <!-- Flash повідомлення -->
    <div class="container mt-3">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'success' if category == 'success' else 'danger' if category == 'danger' else 'warning' }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>
    
    <!-- Основна сторінка -->
    <main class="container mt-4 mb-5">
        {% block content %}{% endblock %}
    </main>
    
    <!-- Footer -->
    <footer class="bg-dark text-white text-center py-3 mt-5">
        <p>&copy; 2024 Fujikura Web System. Всі права захищені.</p>
    </footer>
    
    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### `templates/applicators/list.html` — Список аплікаторів

```html
{% extends "base.html" %}

{% block title %}Аплікатори - Fujikura Web{% endblock %}

{% block content %}
<h1>Аплікатори</h1>

<!-- Фільтри -->
<div class="row mb-3">
    <div class="col-md-3">
        <input type="text" id="searchInput" class="form-control" placeholder="Пошук...">
    </div>
    <div class="col-md-3">
        <select id="statusFilter" class="form-select">
            <option value="">Всі статуси</option>
            <option value="AVAILABLE">Доступні</option>
            <option value="BLOCKED">Заблоковані</option>
            <option value="CUTTING">Нарізка</option>
            <option value="CRIMPING">Кримпування</option>
        </select>
    </div>
    <div class="col-md-3">
        <select id="locationFilter" class="form-select">
            <option value="">Всі локації</option>
            <option value="Aplicator Room">Кімната</option>
            <option value="Service">Обслуговування</option>
            <option value="Cutting">Нарізка</option>
            <option value="Crimping">Кримпування</option>
        </select>
    </div>
    <div class="col-md-3">
        {% if current_user.is_admin() %}
            <a href="{{ url_for('applicators.add_applicator') }}" class="btn btn-success w-100">
                + Додати аплікатор
            </a>
        {% endif %}
    </div>
</div>

<!-- Таблиця аплікаторів -->
<table class="table table-striped table-hover">
    <thead class="table-dark">
        <tr>
            <th>Код</th>
            <th>Назва</th>
            <th>Статус</th>
            <th>Локація</th>
            <th>Машина</th>
            <th>Дійс</th>
        </tr>
    </thead>
    <tbody>
        {% for applicator in applicators %}
        <tr>
            <td>
                <a href="{{ url_for('applicators.applicator_detail', applicator_id=applicator.id) }}">
                    {{ applicator.code }}
                </a>
            </td>
            <td>{{ applicator.name }}</td>
            <td>
                <span class="badge 
                    {% if applicator.status == 'AVAILABLE' %}bg-success
                    {% elif applicator.status == 'BLOCKED' %}bg-danger
                    {% elif applicator.status == 'SERVICE' %}bg-warning
                    {% else %}bg-info{% endif %}">
                    {{ applicator.status }}
                </span>
            </td>
            <td>{{ applicator.location }}</td>
            <td>{{ applicator.machine or '-' }}</td>
            <td>
                {% if applicator.status != 'BLOCKED' and (current_user.is_technician() or current_user.is_admin()) %}
                    <button class="btn btn-sm btn-danger" onclick="blockApplicator({{ applicator.id }})">
                        Блокувати
                    </button>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<!-- Пагінація -->
{% if pagination.pages > 1 %}
<nav>
    <ul class="pagination">
        {% if pagination.has_prev %}
            <li class="page-item">
                <a class="page-link" href="?page={{ pagination.prev_num }}">Попередня</a>
            </li>
        {% endif %}
        
        {% for page_num in range(1, pagination.pages + 1) %}
            <li class="page-item {% if page_num == pagination.page %}active{% endif %}">
                <a class="page-link" href="?page={{ page_num }}">{{ page_num }}</a>
            </li>
        {% endfor %}
        
        {% if pagination.has_next %}
            <li class="page-item">
                <a class="page-link" href="?page={{ pagination.next_num }}">Наступна</a>
            </li>
        {% endif %}
    </ul>
</nav>
{% endif %}

{% endblock %}

{% block extra_js %}
<script>
function blockApplicator(applicatorId) {
    const reason = prompt('Причина блокування:');
    if (reason === null) return;
    
    fetch(`/applicators/${applicatorId}/block`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `reason=${encodeURIComponent(reason)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Аплікатор заблокований');
            location.reload();
        } else {
            alert('Помилка: ' + data.message);
        }
    });
}
</script>
{% endblock %}
```

### `templates/auth/login.html` — Форма входу

```html
{% extends "base.html" %}

{% block title %}Вхід - Fujikura Web{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card mt-5">
            <div class="card-header bg-primary text-white">
                <h3 class="mb-0">Вхід до системи</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    {{ form.hidden_tag() }}
                    
                    <div class="mb-3">
                        {{ form.username.label(class="form-label") }}
                        {{ form.username(class="form-control") }}
                        {% if form.username.errors %}
                            <div class="text-danger">
                                {{ form.username.errors[0] }}
                            </div>
                        {% endif %}
                    </div>
                    
                    <div class="mb-3">
                        {{ form.password.label(class="form-label") }}
                        {{ form.password(class="form-control") }}
                        {% if form.password.errors %}
                            <div class="text-danger">
                                {{ form.password.errors[0] }}
                            </div>
                        {% endif %}
                    </div>
                    
                    <div class="mb-3 form-check">
                        {{ form.remember(class="form-check-input") }}
                        {{ form.remember.label(class="form-check-label") }}
                    </div>
                    
                    {{ form.submit(class="btn btn-primary w-100") }}
                </form>
                
                <hr>
                <p class="text-center">
                    Немає облікового запису? 
                    <a href="{{ url_for('auth.register') }}">Зареєструватися</a>
                </p>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### `static/js/main.js` — JavaScript

```javascript
// AJAX для блокування без перезагрузки сторінки
async function blockApplicator(appId) {
    const reason = prompt('Причина блокування:');
    if (reason === null) return;
    
    const response = await fetch(`/applicators/${appId}/block`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `reason=${encodeURIComponent(reason)}`
    });
    
    const data = await response.json();
    if (data.success) {
        alert('Аплікатор заблокований');
        location.reload();
    } else {
        alert('Помилка: ' + data.message);
    }
}

// AJAX для розблокування
async function unblockApplicator(appId) {
    const response = await fetch(`/applicators/${appId}/unblock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });
    
    const data = await response.json();
    if (data.success) {
        alert('Аплікатор розблокований');
        location.reload();
    }
}

// AJAX для додавання коментаря
async function addComment(appId) {
    const text = prompt('Введіть коментар:');
    if (!text) return;
    
    const response = await fetch(`/applicators/${appId}/comment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
    });
    
    const data = await response.json();
    if (data.success) {
        alert('Коментар додано');
        location.reload();
    }
}
```

---

## Потоки даних

### 1. Сценарій: Користувач входить в систему

```
┌─────────────────────────────────────────────────┐
│ 1. User вводить username/password в HTML форму  │
│    (templates/auth/login.html)                  │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│ 2. POST /auth/login → routes_auth.py            │
│    - Отримати form.username і form.password     │
│    - Валідація форми (forms.py → LoginForm)     │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│ 3. UserService.authenticate(username, password) │
│    - UserService.get_user_by_username()         │
│    - dm.find_by_field('users', 'username', ...) │
│    - user.check_password(password)              │
│    - user.check_password() → Werkzeug validate  │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│ 4. Якщо пароль правильний:                      │
│    - UserService.update_last_login(user_id)     │
│    - dm.update('users', user_id, {...})         │
│    - Login Manager записує session              │
│    - Redirect до dashboard                      │
└─────────────────────────────────────────────────┘
```

### 2. Сценарій: Технік переміщує аплікатор G01 з Service в Aplicator Room

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. UI: Технік відкриває applicators/detail.html (аплікатор G01)  │
│    - GET /applicators/1                                          │
│    - Показує кнопку "Переміщення" (тільки для technician+)      │
└──────────────────────────────────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ 2. Технік натискає кнопку переміщення                            │
│    - JavaScript AJAX запит:                                      │
│    - POST /applicators/move                                      │
│    - Data: {applicator_id: 1, to_location: 'Aplicator Room'}    │
└──────────────────────────────────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ 3. Route: routes_applicators.py → move_applicator()             │
│    - @login_required перевіряє аутентифікацію                    │
│    - @technician_required перевіряє роль                         │
│    - Отримує дані з request.form/json                           │
│    - Базова валідація: app_id > 0, location != null             │
└──────────────────────────────────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ 4. Service Layer:                                                │
│    ApplicatorService.get_applicator(1)                           │
│      ↓ dm.read('applicators', 1)                                 │
│      ↓ Applicator.from_dict(data)                                │
│      ↓ Повертає: Applicator(                                     │
│           id=1, code='G01', status='SERVICE',                    │
│           location='Service', machine=None)                      │
└──────────────────────────────────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ 5. ValidationService перевіряє:                                  │
│    ✓ Аплікатор існує                                             │
│    ✓ Локація 'Aplicator Room' валідна                            │
│    ✓ Аплікатор не заблокований                                   │
│    ✓ У Aplicator Room є вільна комірка (cell_number)             │
└──────────────────────────────────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ 6. Бізнес-логіка:                                                │
│    ApplicatorService.update_applicator(1,                        │
│       location='Aplicator Room',                                 │
│       status='AVAILABLE',                                        │
│       last_moved_at=datetime.now()                               │
│    )                                                             │
│      ↓ dm.update('applicators', 1, {...})                        │
│      ↓ applicators.json оновлено                                 │
│      ↓ Повертає оновлений Applicator                             │
└──────────────────────────────────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ 7. Запис переміщення:                                            │
│    MovementService.record_movement(                              │
│       applicator_id=1,                                           │
│       applicator_code='G01',                                     │
│       from_location='Service',                                   │
│       to_location='Aplicator Room',                              │
│       user_id=current_user.id,                                   │
│       username=current_user.username,                            │
│       comment=''                                                 │
│    )                                                             │
│      ↓ dm.create('movements', {...})                             │
│      ↓ movements.json розширено новим записом                    │
└──────────────────────────────────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ 8. Response:                                                     │
│    jsonify({                                                     │
│       'success': True,                                           │
│       'message': 'Аплікатор переміщено успішно',                 │
│       'applicator': {...}                                        │
│    })                                                            │
└──────────────────────────────────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│ 9. Frontend:                                                     │
│    - JavaScript отримує JSON response                            │
│    - Flash повідомлення: "Успішно!"                              │
│    - Оновлення DOM без перезагрузки (AJAX)                       │
│    - Показ оновленого аплікатора                                 │
└──────────────────────────────────────────────────────────────────┘
```

### 3. Сценарій: Адміністратор створює нового користувача

```
Admin Panel → /admin/users/create (GET)
             ↓
          AdminCreateUserForm в HTML
             ↓
          Admin заповнює форму і натискає "Створити"
             ↓
          POST /admin/users/create
             ↓
          routes_admin.py → create_user()
             ↓
          Forms.validate() перевіряє:
          - username унікальний
          - email унікальний
          - пароль >= 8 символів
             ↓
          UserService.create_user(username, email, password, role)
             ↓
          User(username=..., email=..., role=...)
          user.set_password(password)
             ↓
          dm.create('users', user.to_dict())
             ↓
          users.json розширено новим користувачем
             ↓
          Flash: "Користувач створено"
          Redirect до admin panel
```

---

## Безпека

### 1. Аутентифікація

- **Session-based**: Користувач входить → Flask-Login створює сесію
- **Хеширование пароля**: PBKDF2:SHA256 (бібліотека Werkzeug)
- **Session TTL**: 7 днів (конфіг у `config.py`)
- **HttpOnly cookies**: Не доступні з JavaScript

```python
# models.py
def set_password(self, password):
    self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

def check_password(self, password):
    return check_password_hash(self.password_hash, password)
```

### 2. Авторизація (RBAC)

**Три ролі:**
- **ADMIN** - Повний доступ (управління користувачами)
- **TECHNICIAN** - Управління аплікаторами, переміщення, блокування
- **OPERATOR** - Тільки перегляд

**Перевірки в маршрутах:**
```python
@login_required                      # Обов'язково залогінений
def list_applicators():
    # Доступ: всі ролі

@technician_required                 # Admin або Technician
def move_applicator(app_id):
    # Доступ: technician, admin

@admin_required                      # Тільки admin
def create_user():
    # Доступ: admin
```

### 3. CSRF захист

- **Flask-WTF**: CSRFProtect() включено в app.py
- **CSRF token**: Генерується для кожної форми
- **SameSite cookies**: Lax режим (захист від cross-site attacks)

```python
# app.py
csrf = CSRFProtect(app)

# HTML форма
{{ form.hidden_tag() }}  <!-- Містить CSRF token -->
```

### 4. Input Validation

**WTF Forms перевіряють:**
- Email валідність
- Пароль >= 8 символів
- Username: 3-20 символів, тільки [A-Za-z0-9_]
- Унікальність username/email

```python
class RegistrationForm(FlaskForm):
    username = StringField('Ім\'я',
        validators=[DataRequired(),
                  Length(min=3, max=20),
                  Regexp('^[A-Za-z0-9_]+$')])
```

### 5. SQL Injection - НЕ ЗАСТОСОВУЄТЬСЯ

- Система не використовує SQL
- JSON файли не мають SQL-injection вразливостей
- Але все одно перевіряємо входи в сервісах

### 6. XSS захист

- **Jinja2 автоescaping**: HTML теги автоматично екрануються
- **safe filter**: Використовується тільки для контрольованого контенту

```html
<!-- Безпечно (автоescaping) -->
{{ user_input }}  <!-- <script> → &lt;script&gt; -->

<!-- Контрольоване (safe) -->
{{ trusted_html | safe }}
```

### 7. Thread-safety

- **DataManager.lock**: Threading.Lock() для операцій з JSON
- Запобігає конфліктам при одночасному доступі

```python
class DataManager:
    def __init__(self):
        self.lock = threading.Lock()
    
    def save_file(self, table, data):
        with self.lock:  # Критична секція
            # Запис у файл
```

---

## Розширюваність

### Додавання нового модуля

**Крок 1: Створити сервіс**
```python
# services/new_service.py
class NewService:
    @staticmethod
    def do_something():
        # Бізнес-логіка
        pass
```

**Крок 2: Створити маршрути**
```python
# routes_new.py
new_bp = Blueprint('new', __name__, url_prefix='/new')

@new_bp.route('/')
@login_required
def list_new():
    # Логіка
    pass
```

**Крок 3: Зареєструвати blueprint**
```python
# app.py
from routes_new import new_bp
app.register_blueprint(new_bp)
```

**Крок 4: Додати шаблони**
```
templates/new/
├── list.html
├── detail.html
└── form.html
```

**Крок 5: Додати посилання у навігацію**
```html
<!-- base.html -->
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('new.list_new') }}">Новий модуль</a>
</li>
```

### Додавання нової таблиці JSON

```python
# У сервісі:
def get_all_items():
    items_data = dm.get_all('items')  # items.json
    return [Item.from_dict(i) for i in items_data]

def create_item(data):
    return dm.create('items', data)
```

### Додавання нової ролі

```python
# models.py
class RoleEnum(Enum):
    # ...
    SUPERVISOR = "supervisor"

# routes.py
def supervisor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.role == "supervisor":
            return "Forbidden", 403
        return f(*args, **kwargs)
    return decorated_function

# forms.py - оновити choices
role = SelectField('Роль',
    choices=[(...), ('supervisor', 'Керівник')])
```

---

## Резюме

**Fujikura Web** — це добре структурована веб-система на Flask з чітким розділенням обов'язків:

1. **Models** (models.py) — Визначення всіх сутностей
2. **Data Layer** (data_manager.py) — CRUD для JSON файлів
3. **Services** (services/) — Бізнес-логіка
4. **Routes** (routes_*.py) — HTTP контролери
5. **Forms** (forms.py) — Валідовані WTF форми
6. **Templates** (templates/) — HTML з Jinja2
7. **Config** (config.py) — Налаштування

Система легко розширюється та підтримується. Кожен рівень має чітку відповідальність і може розвиватися незалежно від інших.

