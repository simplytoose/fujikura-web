from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask import jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app.services.user_service import UserService
from app.models import RoleEnum
from app.forms import LoginForm, RegistrationForm, ChangePasswordForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = UserService.authenticate(form.username.data, form.password.data)

        if user:
            if not user.is_active:
                flash('Ваш акаунт деактивований', 'danger')
                return redirect(url_for('auth.login'))

            login_user(user, remember=form.remember.data)

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Невірне ім\'я користувача або пароль', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():

    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = UserService.create_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                role=RoleEnum.TECHNICIAN.value
            )

            if user:
                flash('Реєстрація успішна! Тепер ви можете увійти.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Помилка при реєстрації. Спробуйте ще раз.', 'danger')
        except Exception as e:
            flash(f'Помилка при реєстрації: {str(e)}', 'danger')

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():

    logout_user()
    flash('Ви вийшли з системи', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():

    if request.method == 'POST':
        action = request.form.get('action', '')

        if action == 'change_password':
            form = ChangePasswordForm()
            if form.validate_on_submit():
                if current_user.check_password(form.current_password.data):
                    UserService.update_user(
                        current_user.id,
                        password=form.new_password.data
                    )
                    flash('Пароль успішно змінений', 'success')
                    return redirect(url_for('auth.profile'))
                else:
                    flash('Поточний пароль невірний', 'danger')
            return render_template('auth/profile.html', change_password_form=form)

    change_password_form = ChangePasswordForm()
    return render_template('auth/profile.html', change_password_form=change_password_form)


@auth_bp.route('/set-theme', methods=['POST'])
@login_required
def set_theme():
    try:
        data = request.get_json() or {}
        theme = data.get('theme')
        if theme not in (None, 'dark', 'light', 'auto', ''):
            return jsonify({'success': False, 'message': 'Invalid theme'}), 400

        UserService.update_user(current_user.id, theme=theme if theme else None)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

