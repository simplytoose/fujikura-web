from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from enum import Enum
from flask_login import UserMixin


class RoleEnum(Enum):
    ADMIN = "admin"
    TECHNICIAN = "technician"
    OPERATOR = "operator"


class StatusEnum(Enum):
    AVAILABLE = "AVAILABLE"
    SERVICE = "SERVICE"
    CUTTING = "CUTTING"
    CRIMPING = "CRIMPING"
    BLOCKED = "BLOCKED"
    INACTIVE = "INACTIVE"


class User(UserMixin):


    def __init__(self, id=None, username=None, email=None, password_hash=None,
                 role=None, is_active=True, created_at=None, last_login=None, theme=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        if isinstance(role, RoleEnum):
            self.role = role.value
        else:
            self.role = role or RoleEnum.OPERATOR.value
        self._is_active = is_active
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.last_login = last_login
        self.theme = theme or None
        # accept theme if passed via kwargs
        try:
            # if last argument passed as theme via positional may not be needed; ensure theme in kwargs handled by from_dict
            pass
        except Exception:
            pass

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    def set_password(self, password):

        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):

        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == RoleEnum.ADMIN.value or self.role == RoleEnum.ADMIN

    def is_technician(self):
        return self.role == RoleEnum.TECHNICIAN.value or self.role == RoleEnum.TECHNICIAN

    def is_operator(self):
        return self.role == RoleEnum.OPERATOR.value or self.role == RoleEnum.OPERATOR

    @property
    def created_at_dt(self):
        if isinstance(self.created_at, str):
            try:
                return datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return None
        return self.created_at

    @property
    def last_login_dt(self):
        if isinstance(self.last_login, str):
            try:
                return datetime.fromisoformat(self.last_login.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return None
        return self.last_login

    def to_dict(self):

        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'role': self.role,
            'is_active': self._is_active,
            'created_at': self.created_at,
            'last_login': self.last_login
            , 'theme': getattr(self, 'theme', None)
        }

    @staticmethod
    def from_dict(data):

        role = data.get('role')
        if isinstance(role, RoleEnum):
            role = role.value
        return User(
            id=data.get('id'),
            username=data.get('username'),
            email=data.get('email'),
            password_hash=data.get('password_hash'),
            role=role,
            is_active=data.get('is_active', True),
            created_at=data.get('created_at'),
            last_login=data.get('last_login'),
            theme=data.get('theme')
        )


class Applicator:


    def __init__(self, id=None, code=None, name=None, location=None, status=None,
                 machine=None, shelf_position=None, created_at=None, notes=None,
                 last_moved_at=None, technician_id=None, cell_number=None,
                 is_configured=False, configured_by=None, configured_at=None,
                 on_machine=False, on_shelf=False, blocked_reason=None,
                 blocked_by=None, blocked_at=None, inactive_reason=None,
                 inactive_by=None, inactive_at=None, comments=None):
        self.id = id
        self.code = code
        self._name = name or code
        self.location = location or "Aplicator Room"
        self.status = status or StatusEnum.AVAILABLE.value
        self.machine = machine
        self.shelf_position = shelf_position
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.notes = notes or ""
        self._last_moved_at = last_moved_at or self.created_at
        self.technician_id = technician_id
        self.cell_number = cell_number
        self.is_configured = is_configured
        self.configured_by = configured_by
        self.configured_at = configured_at
        self.on_machine = on_machine
        self.on_shelf = on_shelf
        self.blocked_reason = blocked_reason
        self.blocked_by = blocked_by
        self.blocked_at = blocked_at
        self.inactive_reason = inactive_reason
        self.inactive_by = inactive_by
        self.inactive_at = inactive_at
        self.comments = comments or []

    @property
    def number(self):

        return self.code

    @property
    def name(self):

        return self._name or self.code

    @name.setter
    def name(self, value):

        self._name = value

    @property
    def current_location(self):

        return self.location

    @property
    def current_machine(self):

        return self.machine

    @property
    def last_moved_at(self):

        if isinstance(self._last_moved_at, str):
            try:
                return datetime.fromisoformat(self._last_moved_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return None
        return self._last_moved_at

    def to_dict(self):

        return {
            'id': self.id,
            'code': self.code,
            'name': self._name,
            'location': self.location,
            'status': self.status,
            'machine': self.machine,
            'shelf_position': self.shelf_position,
            'created_at': self.created_at,
            'notes': self.notes,
            'last_moved_at': self._last_moved_at,
            'technician_id': self.technician_id,
            'cell_number': self.cell_number,
            'is_configured': self.is_configured,
            'configured_by': self.configured_by,
            'configured_at': self.configured_at,
            'on_machine': self.on_machine,
            'on_shelf': self.on_shelf,
            'blocked_reason': self.blocked_reason,
            'blocked_by': self.blocked_by,
            'blocked_at': self.blocked_at,
            'inactive_reason': self.inactive_reason,
            'inactive_by': self.inactive_by,
            'inactive_at': self.inactive_at,
            'comments': self.comments
        }

    @staticmethod
    def from_dict(data):

        return Applicator(
            id=data.get('id'),
            code=data.get('code'),
            name=data.get('name'),
            location=data.get('location'),
            status=data.get('status'),
            machine=data.get('machine'),
            shelf_position=data.get('shelf_position'),
            created_at=data.get('created_at'),
            notes=data.get('notes'),
            last_moved_at=data.get('last_moved_at'),
            technician_id=data.get('technician_id'),
            cell_number=data.get('cell_number'),
            is_configured=data.get('is_configured', False),
            configured_by=data.get('configured_by'),
            configured_at=data.get('configured_at'),
            on_machine=data.get('on_machine', False),
            on_shelf=data.get('on_shelf', False),
            blocked_reason=data.get('blocked_reason'),
            blocked_by=data.get('blocked_by'),
            blocked_at=data.get('blocked_at'),
            inactive_reason=data.get('inactive_reason'),
            inactive_by=data.get('inactive_by'),
            inactive_at=data.get('inactive_at'),
            comments=data.get('comments', [])
        )


class ApplicatorComment:


    def __init__(self, id=None, applicator_id=None, author=None, text=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.applicator_id = applicator_id
        self.author = author
        self.text = text or ""
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.updated_at = updated_at or self.created_at

    def to_dict(self):
        return {
            'id': self.id,
            'applicator_id': self.applicator_id,
            'author': self.author,
            'text': self.text,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @staticmethod
    def from_dict(data):
        return ApplicatorComment(
            id=data.get('id'),
            applicator_id=data.get('applicator_id'),
            author=data.get('author'),
            text=data.get('text'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


class Machine:


    def __init__(self, id=None, code=None, type=None, location=None,
                 max_capacity=None, created_at=None):
        self.id = id
        self.code = code
        self.type = type or "cutting"
        self.location = location
        self.max_capacity = max_capacity or (5 if type == "cutting" else 3)
        self.applicators = []
        self.created_at = created_at or datetime.utcnow().isoformat()

    def get_total_applicators(self):

        return len(self.applicators)

    @property
    def total(self):

        return self.get_total_applicators()

    @property
    def max(self):

        return self.max_capacity

    @property
    def full(self):

        return self.total >= self.max

    def to_dict(self):

        return {
            'id': self.id,
            'code': self.code,
            'type': self.type,
            'location': self.location,
            'max_capacity': self.max_capacity,
            'applicators': self.applicators,
            'created_at': self.created_at
        }

    @staticmethod
    def from_dict(data):

        m = Machine(
            id=data.get('id'),
            code=data.get('code'),
            type=data.get('type'),
            location=data.get('location'),
            max_capacity=data.get('max_capacity'),
            created_at=data.get('created_at')
        )
        m.applicators = data.get('applicators', [])
        return m


class MovementRecord:


    def __init__(self, id=None, applicator_id=None, applicator_code=None,
                 from_location=None, to_location=None, from_machine=None,
                 to_machine=None, user_id=None, username=None, moved_at=None, comment=None):
        self.id = id
        self.applicator_id = applicator_id
        self.applicator_code = applicator_code
        self.from_location = from_location
        self.to_location = to_location
        self.from_machine = from_machine
        self.to_machine = to_machine
        self.user_id = user_id
        self.username = username
        self.moved_at = moved_at or datetime.utcnow().isoformat()
        self.comment = comment or ""

    def to_dict(self):

        return {
            'id': self.id,
            'applicator_id': self.applicator_id,
            'applicator_code': self.applicator_code,
            'from_location': self.from_location,
            'to_location': self.to_location,
            'from_machine': self.from_machine,
            'to_machine': self.to_machine,
            'user_id': self.user_id,
            'username': self.username,
            'moved_at': self.moved_at,
            'comment': self.comment
        }

    @staticmethod
    def from_dict(data):

        return MovementRecord(
            id=data.get('id'),
            applicator_id=data.get('applicator_id'),
            applicator_code=data.get('applicator_code'),
            from_location=data.get('from_location'),
            to_location=data.get('to_location'),
            from_machine=data.get('from_machine'),
            to_machine=data.get('to_machine'),
            user_id=data.get('user_id'),
            username=data.get('username'),
            moved_at=data.get('moved_at') or data.get('date'),
            comment=data.get('comment')
        )


class BlockingRecord:


    def __init__(self, id=None, applicator_id=None, applicator_code=None,
                 reason=None, user_id=None, username=None, created_at=None, is_blocked=True):
        self.id = id
        self.applicator_id = applicator_id
        self.applicator_code = applicator_code
        self.reason = reason or ""
        self.user_id = user_id
        self.username = username
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.is_blocked = is_blocked

    def to_dict(self):

        return {
            'id': self.id,
            'applicator_id': self.applicator_id,
            'applicator_code': self.applicator_code,
            'reason': self.reason,
            'user_id': self.user_id,
            'username': self.username,
            'created_at': self.created_at,
            'is_blocked': self.is_blocked
        }

    @staticmethod
    def from_dict(data):

        return BlockingRecord(
            id=data.get('id'),
            applicator_id=data.get('applicator_id'),
            applicator_code=data.get('applicator_code'),
            reason=data.get('reason'),
            user_id=data.get('user_id'),
            username=data.get('username'),
            created_at=data.get('created_at') or data.get('date'),
            is_blocked=data.get('is_blocked', True)
        )


class Location:


    LOCATIONS = {
        'Aplicator Room': 'Основне сховище (300 комірок)',
        'Service': 'Дільниця обслуговування',
        'Cutting': 'Дільниця нарізки (G01-G30)',
        'Crimping': 'Дільниця кримпування (P01-P05)',
        'Blocked': 'Заблоковані аплікатори',
        'Inactive': 'Аплікатори без використання'
    }

    def __init__(self, code, name, description=""):
        self.code = code
        self.name = name
        self.description = description or self.LOCATIONS.get(code, "")

    def to_dict(self):
        return {
            'code': self.code,
            'name': self.name,
            'description': self.description
        }


class ApplicatorCell:


    def __init__(self, id=None, cell_number=None, is_occupied=False,
                 applicator_id=None, created_at=None):
        self.id = id
        self.cell_number = cell_number
        self.is_occupied = is_occupied
        self.applicator_id = applicator_id
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            'id': self.id,
            'cell_number': self.cell_number,
            'is_occupied': self.is_occupied,
            'applicator_id': self.applicator_id,
            'created_at': self.created_at
        }

    @staticmethod
    def from_dict(data):
        return ApplicatorCell(
            id=data.get('id'),
            cell_number=data.get('cell_number'),
            is_occupied=data.get('is_occupied', False),
            applicator_id=data.get('applicator_id'),
            created_at=data.get('created_at')
        )


class ServiceAreaConfirmation:


    def __init__(self, id=None, applicator_id=None, applicator_code=None,
                 is_configured=False, confirmed_by=None, confirmed_at=None):
        self.id = id
        self.applicator_id = applicator_id
        self.applicator_code = applicator_code
        self.is_configured = is_configured
        self.confirmed_by = confirmed_by
        self.confirmed_at = confirmed_at

    def to_dict(self):
        return {
            'id': self.id,
            'applicator_id': self.applicator_id,
            'applicator_code': self.applicator_code,
            'is_configured': self.is_configured,
            'confirmed_by': self.confirmed_by,
            'confirmed_at': self.confirmed_at
        }

    @staticmethod
    def from_dict(data):
        return ServiceAreaConfirmation(
            id=data.get('id'),
            applicator_id=data.get('applicator_id'),
            applicator_code=data.get('applicator_code'),
            is_configured=data.get('is_configured', False),
            confirmed_by=data.get('confirmed_by'),
            confirmed_at=data.get('confirmed_at')
        )


class InactiveRecord:


    def __init__(self, id=None, applicator_id=None, applicator_code=None,
                 reason=None, marked_by=None, marked_at=None, is_inactive=True):
        self.id = id
        self.applicator_id = applicator_id
        self.applicator_code = applicator_code
        self.reason = reason or ""
        self.marked_by = marked_by
        self.marked_at = marked_at or datetime.utcnow().isoformat()
        self.is_inactive = is_inactive

    def to_dict(self):
        return {
            'id': self.id,
            'applicator_id': self.applicator_id,
            'applicator_code': self.applicator_code,
            'reason': self.reason,
            'marked_by': self.marked_by,
            'marked_at': self.marked_at,
            'is_inactive': self.is_inactive
        }

    @staticmethod
    def from_dict(data):
        return InactiveRecord(
            id=data.get('id'),
            applicator_id=data.get('applicator_id'),
            applicator_code=data.get('applicator_code'),
            reason=data.get('reason'),
            marked_by=data.get('marked_by'),
            marked_at=data.get('marked_at'),
            is_inactive=data.get('is_inactive', True)
        )

