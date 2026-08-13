from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.services.applicator_service import ApplicatorService
from app.services.movement_service import MovementService, BlockingService
from app.services.maintenance_service import MaintenanceService
from app.models import StatusEnum
from functools import wraps

applicators_bp = Blueprint('applicators', __name__, url_prefix='/applicators')


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


@applicators_bp.route('/')
@login_required
def list_applicators():

    status_filter = request.args.get('status', 'all')
    location_filter = request.args.get('location', 'all')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10

    applicators = ApplicatorService.get_all_applicators()
    applicators.sort(key=lambda a: a.id or 0, reverse=True)

    if search:
        query = search.lower()
        applicators = [
            a for a in applicators
            if query in (a.code or '').lower() or query in (a.name or '').lower()
        ]

    if status_filter and status_filter != 'all':
        applicators = [a for a in applicators if a.status == status_filter]

    if location_filter and location_filter != 'all':
        applicators = [a for a in applicators if a.location == location_filter]

    total = len(applicators)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_applicators = applicators[start:end]

    class Pagination:
        def __init__(self, page, per_page, total):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page

        @property
        def has_prev(self):
            return self.page > 1

        @property
        def has_next(self):
            return self.page < self.pages

        @property
        def prev_num(self):
            return self.page - 1 if self.has_prev else None

        @property
        def next_num(self):
            return self.page + 1 if self.has_next else None

    pagination = Pagination(page, per_page, total)

    return render_template('applicators/list.html',
                         applicators=paginated_applicators,
                         pagination=pagination,
                         status_filter=status_filter,
                         location_filter=location_filter,
                         search=search)


@applicators_bp.route('/<int:applicator_id>')
@login_required
def applicator_detail(applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        flash('Аплікатор не знайдено', 'danger')
        return redirect(url_for('applicators.list_applicators'))

    history = MovementService.get_movements_by_applicator(applicator_id)
    blocking_history = BlockingService.get_blocking_history_for_applicator(applicator_id)
    maintenance_records = MaintenanceService.get_records_by_applicator(applicator_id)

    return render_template('applicators/detail.html',
                         applicator=applicator,
                         history=history,
                         blocking_history=blocking_history,
                         maintenance_records=maintenance_records)


@applicators_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_applicator():

    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        name = request.form.get('name', '').strip()

        if not code:
            flash('Будь ласка, заповніть код аплікатора', 'danger')
            return redirect(url_for('applicators.add_applicator'))

        if not name:
            flash('Будь ласка, заповніть назву аплікатора', 'danger')
            return redirect(url_for('applicators.add_applicator'))

        existing = ApplicatorService.get_applicator_by_code(code)
        if existing:
            flash('Аплікатор з таким кодом вже існує', 'danger')
            return redirect(url_for('applicators.add_applicator'))

        applicator = ApplicatorService.create_applicator(
            code=code,
            name=name,
            location='Aplicator Room',
            status=StatusEnum.AVAILABLE.value
        )

        if applicator.cell_number:
            flash(f'Аплікатор {code} успішно додано (комірка №{applicator.cell_number})', 'success')
        else:
            flash(f'Аплікатор {code} додано, але вільних комірок у Aplicator Room не залишилось', 'warning')
        return redirect(url_for('applicators.applicator_detail', applicator_id=applicator.id))

    return render_template('applicators/add.html')


@applicators_bp.route('/edit/<int:applicator_id>', methods=['GET', 'POST'])
@admin_required
def edit_applicator(applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        flash('Аплікатор не знайдено', 'danger')
        return redirect(url_for('applicators.list_applicators'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        notes = request.form.get('notes', '').strip()

        if not name:
            flash('Будь ласка, заповніть назву аплікатора', 'danger')
            return redirect(url_for('applicators.edit_applicator', applicator_id=applicator_id))

        ApplicatorService.update_applicator(applicator_id, name=name, notes=notes)

        flash('Аплікатор успішно оновлено', 'success')
        return redirect(url_for('applicators.applicator_detail', applicator_id=applicator_id))

    return render_template('applicators/edit.html', applicator=applicator)


@applicators_bp.route('/<int:applicator_id>/delete', methods=['POST'])
@admin_required
def delete_applicator(applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        flash('Аплікатор не знайдено', 'danger')
        return redirect(url_for('applicators.list_applicators'))

    code = applicator.code
    if ApplicatorService.delete_applicator(applicator_id):
        flash(f'Аплікатор {code} видалено', 'success')
    else:
        flash('Не вдалося видалити аплікатор', 'danger')

    return redirect(url_for('applicators.list_applicators'))


@applicators_bp.route('/<int:applicator_id>/block', methods=['POST'])
@login_required
def block_applicator(applicator_id):

    if not (current_user.is_technician() or current_user.is_admin()):
        return jsonify({'success': False, 'message': 'Ви не маєте прав'}), 403

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        return jsonify({'success': False, 'message': 'Аплікатор не знайдено'}), 404

    if applicator.status == StatusEnum.BLOCKED.value:
        return jsonify({'success': False, 'message': 'Аплікатор вже заблокований'}), 400

    reason = request.form.get('reason', '') or request.json.get('reason', '')

    ApplicatorService.block_applicator(applicator_id, reason)
    BlockingService.record_blocking(
        applicator_id=applicator_id,
        applicator_code=applicator.code,
        user_id=current_user.id,
        username=current_user.username,
        reason=reason
    )

    return jsonify({'success': True, 'message': 'Аплікатор заблокований'})


@applicators_bp.route('/<int:applicator_id>/unblock', methods=['POST'])
@login_required
def unblock_applicator(applicator_id):

    if not (current_user.is_technician() or current_user.is_admin()):
        return jsonify({'success': False, 'message': 'Ви не маєте прав'}), 403

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        return jsonify({'success': False, 'message': 'Аплікатор не знайдено'}), 404

    if applicator.status != StatusEnum.BLOCKED.value:
        return jsonify({'success': False, 'message': 'Аплікатор не заблокований'}), 400

    ApplicatorService.unblock_applicator(applicator_id)
    ApplicatorService.update_applicator(applicator_id, location='Aplicator Room', status=StatusEnum.AVAILABLE.value)

    BlockingService.record_unblocking(
        applicator_id=applicator_id,
        applicator_code=applicator.code,
        user_id=current_user.id,
        username=current_user.username
    )

    return jsonify({'success': True, 'message': 'Аплікатор розблокований'})


@applicators_bp.route('/<int:applicator_id>/confirm-service', methods=['POST'])
@login_required
def confirm_service(applicator_id):

    if not (current_user.is_technician() or current_user.is_admin()):
        return jsonify({'success': False, 'message': 'Ви не маєте прав'}), 403

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        return jsonify({'success': False, 'message': 'Аплікатор не знайдено'}), 404

    if applicator.status != StatusEnum.SERVICE.value:
        return jsonify({'success': False, 'message': 'Аплікатор не на обслуговуванні'}), 400

    ApplicatorService.update_applicator(applicator_id,
                                       location='Aplicator Room',
                                       status=StatusEnum.AVAILABLE.value)

    MovementService.record_movement(
        applicator_id=applicator_id,
        applicator_code=applicator.code,
        from_location='Service',
        to_location='Aplicator Room',
        user_id=current_user.id,
        username=current_user.username,
        comment='Обслуговування підтверджено'
    )

    return jsonify({'success': True, 'message': 'Обслуговування підтверджено'})


@applicators_bp.route('/<int:applicator_id>/update-name', methods=['POST'])
@admin_required
def update_applicator_name(applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        return jsonify({'success': False, 'message': 'Аплікатор не знайдено'}), 404

    name = request.json.get('name', '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Ім\'я аплікатора не може бути пустим'}), 400

    ApplicatorService.update_applicator_name(applicator_id, name)
    return jsonify({'success': True, 'message': 'Назва аплікатора оновлена'})


@applicators_bp.route('/<int:applicator_id>/comments', methods=['GET'])
@login_required
def get_comments(applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        return jsonify({'success': False, 'message': 'Аплікатор не знайдено'}), 404

    comments = ApplicatorService.get_comments(applicator_id)
    return jsonify({'success': True, 'comments': comments})


@applicators_bp.route('/<int:applicator_id>/comment', methods=['POST'])
@login_required
def add_comment(applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        return jsonify({'success': False, 'message': 'Аплікатор не знайдено'}), 404

    text = request.json.get('text', '').strip()
    if not text:
        return jsonify({'success': False, 'message': 'Текст коментаря не може бути пустим'}), 400

    ApplicatorService.add_comment(applicator_id, current_user.username, text)
    return jsonify({'success': True, 'message': 'Коментар додано'})


@applicators_bp.route('/<int:applicator_id>/comment/<comment_id>', methods=['DELETE'])
@login_required
def delete_comment(applicator_id, comment_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        return jsonify({'success': False, 'message': 'Аплікатор не знайдено'}), 404

    if not (current_user.is_admin() or current_user.username == ApplicatorService.get_comments(applicator_id).__iter__().__next__().get('author')):
        return jsonify({'success': False, 'message': 'Ви не можете видалити цей коментар'}), 403

    ApplicatorService.delete_comment(applicator_id, float(comment_id))
    return jsonify({'success': True, 'message': 'Коментар видалено'})

