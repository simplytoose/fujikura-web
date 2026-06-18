from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp
from services.user_service import UserService


class LoginForm(FlaskForm):

    username = StringField(
        'Ім\'я користувача',
        validators=[
            DataRequired('Ім\'я користувача обов\'язкове'),
            Regexp('^[A-Za-z0-9_]+$', message='Ім\'я може містити тільки букви, цифри та підкреслення')
        ],
        render_kw={'class': 'form-control form-control-lg', 'autofocus': True}
    )
    password = PasswordField(
        'Пароль',
        validators=[DataRequired('Пароль обов\'язковий')],
        render_kw={'class': 'form-control form-control-lg'}
    )
    remember = BooleanField(
        'Запам\'ятати мене',
        render_kw={'class': 'form-check-input'}
    )
    submit = SubmitField('Вхід', render_kw={'class': 'btn btn-primary btn-lg w-100'})


class RegistrationForm(FlaskForm):

    username = StringField(
        'Ім\'я користувача',
        validators=[
            DataRequired('Ім\'я користувача обов\'язкове'),
            Length(min=3, max=20, message='Ім\'я користувача повинно бути від 3 до 20 символів'),
            Regexp('^[A-Za-z0-9_]+$', message='Ім\'я може містити тільки букви, цифри та підкреслення')
        ],
        render_kw={'class': 'form-control', 'placeholder': 'tech_01'}
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired('Email обов\'язковий'),
            Email('Невалідна адреса email')
        ],
        render_kw={'class': 'form-control', 'placeholder': 'tech@example.com'}
    )
    password = PasswordField(
        'Пароль',
        validators=[
            DataRequired('Пароль обов\'язковий'),
            Length(min=8, message='Пароль повинен містити мінімум 8 символів')
        ],
        render_kw={'class': 'form-control', 'placeholder': '••••••••'}
    )
    confirm_password = PasswordField(
        'Підтвердити пароль',
        validators=[
            DataRequired('Підтвердження пароля обов\'язкове'),
            EqualTo('password', message='Паролі повинні співпадати')
        ],
        render_kw={'class': 'form-control', 'placeholder': '••••••••'}
    )
    submit = SubmitField('Зареєструватися', render_kw={'class': 'btn btn-primary w-100'})

    def validate_username(self, field):

        if UserService.user_exists(field.data):
            raise ValidationError('Ім\'я користувача вже існує. Виберіть інше.')

    def validate_email(self, field):

        user = UserService.get_user_by_email(field.data)
        if user:
            raise ValidationError('Цей email вже зареєстрований.')


class AdminCreateUserForm(FlaskForm):

    username = StringField(
        'Ім\'я користувача',
        validators=[
            DataRequired('Ім\'я користувача обов\'язкове'),
            Length(min=3, max=20, message='Ім\'я користувача повинно бути від 3 до 20 символів'),
            Regexp('^[A-Za-z0-9_]+$', message='Ім\'я може містити тільки букви, цифри та підкреслення')
        ],
        render_kw={'class': 'form-control'}
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired('Email обов\'язковий'),
            Email('Невалідна адреса email')
        ],
        render_kw={'class': 'form-control'}
    )
    password = PasswordField(
        'Пароль',
        validators=[
            DataRequired('Пароль обов\'язковий'),
            Length(min=8, message='Пароль повинен містити мінімум 8 символів')
        ],
        render_kw={'class': 'form-control', 'placeholder': '••••••••'}
    )
    role = SelectField(
        'Роль',
        choices=[
            ('technician', 'Технік'),
            ('operator', 'Оператор'),
            ('admin', 'Адміністратор')
        ],
        validators=[DataRequired('Роль обов\'язкова')],
        render_kw={'class': 'form-control'}
    )
    submit = SubmitField('Створити користувача', render_kw={'class': 'btn btn-primary'})

    def validate_username(self, field):

        if UserService.user_exists(field.data):
            raise ValidationError('Ім\'я користувача вже існує.')

    def validate_email(self, field):

        user = UserService.get_user_by_email(field.data)
        if user:
            raise ValidationError('Цей email вже зареєстрований.')


class EditUserForm(FlaskForm):

    email = StringField(
        'Email',
        validators=[
            DataRequired('Email обов\'язковий'),
            Email('Невалідна адреса email')
        ],
        render_kw={'class': 'form-control'}
    )
    role = SelectField(
        'Роль',
        choices=[
            ('technician', 'Технік'),
            ('operator', 'Оператор'),
            ('admin', 'Адміністратор')
        ],
        validators=[DataRequired('Роль обов\'язкова')],
        render_kw={'class': 'form-control'}
    )
    password = PasswordField(
        'Новий пароль (залиште порожнім, щоб не змінювати)',
        validators=[Length(min=8, message='Пароль повинен містити мінімум 8 символів')],
        render_kw={'class': 'form-control', 'placeholder': '••••••••'}
    )
    submit = SubmitField('Зберегти зміни', render_kw={'class': 'btn btn-primary'})


class ChangePasswordForm(FlaskForm):

    current_password = PasswordField(
        'Поточний пароль',
        validators=[DataRequired('Поточний пароль обов\'язковий')],
        render_kw={'class': 'form-control'}
    )
    new_password = PasswordField(
        'Новий пароль',
        validators=[
            DataRequired('Новий пароль обов\'язковий'),
            Length(min=8, message='Пароль повинен містити мінімум 8 символів')
        ],
        render_kw={'class': 'form-control'}
    )
    confirm_password = PasswordField(
        'Підтвердити новий пароль',
        validators=[
            DataRequired('Підтвердження пароля обов\'язкове'),
            EqualTo('new_password', message='Паролі повинні співпадати')
        ],
        render_kw={'class': 'form-control'}
    )
    submit = SubmitField('Змінити пароль', render_kw={'class': 'btn btn-primary'})

