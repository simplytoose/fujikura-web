from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.user_service import UserService
from models import RoleEnum
from functools import wraps
from forms import AdminCreateUserForm, EditUserForm
from math import ceil

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


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


@admin_bp.route('/')
@admin_required
def admin():

    total_users = UserService.count_users()
    admin_users = UserService.get_users_by_role(RoleEnum.ADMIN.value)
    tech_users = UserService.get_users_by_role(RoleEnum.TECHNICIAN.value)
    op_users = UserService.get_users_by_role(RoleEnum.OPERATOR.value)
    active_users = len([u for u in UserService.get_all_users() if u.is_active])

    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'admins': len(admin_users),
        'technicians': len(tech_users),
        'operators': len(op_users)
    }

    return render_template('admin/dashboard.html', stats=stats)


@admin_bp.route('/users')
@admin_required
def users():

    page = request.args.get('page', 1, type=int)
    per_page = 10

    all_users = UserService.get_all_users()
    all_users = sorted(all_users, key=lambda u: u.created_at, reverse=True)

    total = len(all_users)
    total_pages = (total + per_page - 1) // per_page

    if page < 1:
        page = 1
    if page > total_pages and total_pages > 0:
        page = total_pages

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    users_list = all_users[start_idx:end_idx]

    class Pagination:
        pass

    pagination = Pagination()
    pagination.items = users_list
    pagination.page = page
    pagination.per_page = per_page
    pagination.pages = total_pages
    pagination.total = total
    pagination.has_prev = page > 1
    pagination.has_next = page < total_pages
    pagination.prev_num = page - 1 if pagination.has_prev else None
    pagination.next_num = page + 1 if pagination.has_next else None

    return render_template('admin/users.html', users=users_list, pagination=pagination)


@admin_bp.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():

    form = AdminCreateUserForm()
    if form.validate_on_submit():
        try:
            user = UserService.create_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                role=form.role.data
            )

            if user:
                flash(f'Користувач {form.username.data} успішно створено', 'success')
                return redirect(url_for('admin.users'))
            else:
                flash('Не вдалось створити користувача', 'danger')
        except Exception as e:
            flash(f'Помилка при створенні користувача: {str(e)}', 'danger')

    return render_template('admin/add_user.html', form=form)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):

    user = UserService.get_user_by_id(user_id)
    if not user:
        flash('Користувач не знайдено', 'danger')
        return redirect(url_for('admin.users'))

    form = EditUserForm()
    if form.validate_on_submit():
        update_data = {'email': form.email.data, 'role': form.role.data}

        if form.password.data:
            update_data['password'] = form.password.data

        UserService.update_user(user_id, **update_data)
        flash('Користувач успішно оновлено', 'success')
        return redirect(url_for('admin.users'))
    elif request.method == 'GET':
        form.email.data = user.email
        form.role.data = user.role

    return render_template('admin/edit_user.html', form=form, user=user)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user(user_id):

    user = UserService.get_user_by_id(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'Користувач не знайдено'}), 404

    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Ви не можете деактивувати свій облік'}), 400

    UserService.update_user(user_id, is_active=not user.is_active)

    status = 'активовано' if not user.is_active else 'деактивовано'
    return jsonify({'success': True, 'message': f'Користувач {status}'})


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):

    user = UserService.get_user_by_id(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'Користувач не знайдено'}), 404

    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Ви не можете видалити свій облік'}), 400

    UserService.delete_user(user_id)

    return jsonify({'success': True, 'message': 'Користувач видалено'})
