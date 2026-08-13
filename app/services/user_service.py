from app.data_manager import dm
from app.models import User, RoleEnum
from datetime import datetime


class UserService:


    @staticmethod
    def create_user(username, email, password, role=RoleEnum.OPERATOR.value):

        if UserService.user_exists(username):
            return None

        user = User(
            username=username,
            email=email,
            role=role,
            is_active=True
        )
        user.set_password(password)

        user_data = user.to_dict()
        user_data.pop('id', None)
        created = dm.create('users', user_data)

        return User.from_dict(created)

    @staticmethod
    def get_user_by_id(user_id):

        data = dm.read('users', user_id)
        return User.from_dict(data) if data else None

    @staticmethod
    def get_user_by_username(username):

        data = dm.find_by_field('users', 'username', username)
        return User.from_dict(data) if data else None

    @staticmethod
    def get_user_by_email(email):

        data = dm.find_by_field('users', 'email', email)
        return User.from_dict(data) if data else None

    @staticmethod
    def authenticate(username, password):

        user = UserService.get_user_by_username(username)
        if user and user.check_password(password):
            UserService.update_last_login(user.id)
            return user
        return None

    @staticmethod
    def update_last_login(user_id):

        dm.update('users', user_id, {'last_login': datetime.utcnow().isoformat()})

    @staticmethod
    def user_exists(username):

        return dm.find_by_field('users', 'username', username) is not None

    @staticmethod
    def get_all_users():

        users_data = dm.get_all('users')
        return [User.from_dict(u) for u in users_data]

    @staticmethod
    def update_user(user_id, **kwargs):

        data = {}
        if 'email' in kwargs:
            data['email'] = kwargs['email']
        if 'role' in kwargs:
            data['role'] = kwargs['role']
        if 'is_active' in kwargs:
            data['is_active'] = kwargs['is_active']
        if 'theme' in kwargs:
            data['theme'] = kwargs['theme']
        if 'password' in kwargs:
            user = UserService.get_user_by_id(user_id)
            user.set_password(kwargs['password'])
            data['password_hash'] = user.password_hash

        updated = dm.update('users', user_id, data)
        return User.from_dict(updated) if updated else None

    @staticmethod
    def delete_user(user_id):

        return dm.delete('users', user_id)

    @staticmethod
    def get_users_by_role(role):

        users_data = dm.list('users', {'role': role})
        return [User.from_dict(u) for u in users_data]

    @staticmethod
    def count_users():

        return dm.count('users')
