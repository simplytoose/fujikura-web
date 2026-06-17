from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.applicator_service import ApplicatorService
from services.movement_service import BlockingService
from services.room_service import InactiveApplicatorService
from services.validation_service import ValidationService
from services.movement_service import MovementService
from models import StatusEnum
from functools import wraps
from datetime import datetime

management_bp = Blueprint('management', __name__, url_prefix='/management')

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


@management_bp.route('/blocked')
@login_required
def view_blocked():

    applicators = ApplicatorService.get_applicators_by_status(StatusEnum.BLOCKED.value)

    page = request.args.get('page', 1, type=int)
    per_page = 10

    total = len(applicators)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated = applicators[start:end]

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

    return render_template('management/blocked.html',
                         applicators=paginated,
                         pagination=pagination,
                         total=total)


@management_bp.route('/block/<int:applicator_id>', methods=['POST'])
@login_required
@technician_required
def block_applicator(applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        flash('Аплікатор не знайдено', 'danger')
        return redirect(url_for('management.view_blocked'))

    reason = request.form.get('reason', 'Немає причини')

    ApplicatorService.update_applicator(
        applicator_id,
        status=StatusEnum.BLOCKED.value,
        location='Blocked',
        blocked_reason=reason,
        blocked_by=current_user.username,
        blocked_at=datetime.utcnow().isoformat(),
        machine=None,
        on_machine=False,
        on_shelf=False
    )

    blocking_record = BlockingService.record_blocking(
        applicator_id,
        applicator.code,
        current_user.id,
        current_user.username,
        reason
    )

    MovementService.record_movement(
        applicator_id, applicator.code,
        applicator.location or 'Service', 'Blocked',
        current_user.id, current_user.username,
        f'Заблокований: {reason}'
    )

    flash(f'Аплікатор {applicator.code} заблокований', 'success')
    return redirect(url_for('management.view_blocked'))


@management_bp.route('/unblock/<int:applicator_id>', methods=['POST'])
@login_required
@technician_required
def unblock_applicator(applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        flash('Аплікатор не знайдено', 'danger')
        return redirect(url_for('management.view_blocked'))

    ApplicatorService.update_applicator(
        applicator_id,
        status=StatusEnum.SERVICE.value,
        location='Service',
        blocked_reason=None,
        blocked_by=None,
        blocked_at=None,
        is_configured=False
    )

    blocking_record = BlockingService.record_unblocking(
        applicator_id,
        applicator.code,
        current_user.id,
        current_user.username
    )

    MovementService.record_movement(
        applicator_id, applicator.code,
        'Blocked', 'Service',
        current_user.id, current_user.username,
        'Розблокований, переведений у Service Area'
    )

    flash(f'Аплікатор {applicator.code} розблокований', 'success')
    return redirect(url_for('management.view_blocked'))


@management_bp.route('/inactive')
@login_required
def view_inactive():

    inactive_records = InactiveApplicatorService.get_all_inactive()
    applicators = []

    for record in inactive_records:
        app = ApplicatorService.get_applicator(record.applicator_id)
        if app:
            applicators.append({'applicator': app, 'record': record})

    page = request.args.get('page', 1, type=int)
    per_page = 10

    total = len(applicators)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated = applicators[start:end]

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

    return render_template('management/inactive.html',
                         applicators=paginated,
                         pagination=pagination,
                         total=total)


@management_bp.route('/mark-inactive/<int:applicator_id>', methods=['POST'])
@login_required
@technician_required
def mark_inactive(applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        flash('Аплікатор не знайдено', 'danger')
        return redirect(url_for('management.view_inactive'))

    reason = request.form.get('reason', 'Немає причини')

    record = InactiveApplicatorService.mark_inactive(
        applicator_id,
        applicator.code,
        reason,
        current_user.id,
        current_user.username
    )

    ApplicatorService.update_applicator(
        applicator_id,
        status=StatusEnum.INACTIVE.value,
        location='Inactive',
        inactive_reason=reason,
        inactive_by=current_user.username,
        inactive_at=datetime.utcnow().isoformat(),
        machine=None,
        on_machine=False,
        on_shelf=False
    )

    MovementService.record_movement(
        applicator_id, applicator.code,
        applicator.location or 'Service', 'Inactive',
        current_user.id, current_user.username,
        f'Позначений неактивним: {reason}'
    )

    flash(f'Аплікатор {applicator.code} позначений неактивним', 'success')
    return redirect(url_for('management.view_inactive'))


@management_bp.route('/restore-inactive/<int:applicator_id>', methods=['POST'])
@login_required
@technician_required
def restore_inactive(applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        flash('Аплікатор не знайдено', 'danger')
        return redirect(url_for('management.view_inactive'))

    InactiveApplicatorService.restore_active(applicator_id)

    ApplicatorService.update_applicator(
        applicator_id,
        status=StatusEnum.SERVICE.value,
        location='Service',
        inactive_reason=None,
        inactive_by=None,
        inactive_at=None,
        is_configured=False
    )

    MovementService.record_movement(
        applicator_id, applicator.code,
        'Inactive', 'Service',
        current_user.id, current_user.username,
        'Повернений у Service Area'
    )

    flash(f'Аплікатор {applicator.code} повернений у Service Area', 'success')
    return redirect(url_for('management.view_inactive'))


@management_bp.route('/validation')
@login_required
@admin_required
def validation():

    results = ValidationService.run_full_validation()

    return render_template('management/validation.html',
                         results=results)


@management_bp.route('/fix-issues', methods=['POST'])
@login_required
@admin_required
def fix_issues():

    action = request.form.get('action')

    if action == 'fix_duplicate_location_flags':
        fixed = 0
        for app_data in ValidationService.check_duplicate_locations():
            if ValidationService.fix_duplicate_location_flags(app_data['applicator_id']):
                fixed += 1
        flash(f'Виправлено {fixed} запису', 'success')

    elif action == 'fix_blocked_locations':
        fixed = 0
        for app_data in ValidationService.check_blocked_movements():
            if app_data['status'] == 'BLOCKED' and app_data['location'] != 'Blocked':
                if ValidationService.fix_blocked_applicator_location(app_data['applicator_id']):
                    fixed += 1
        flash(f'Виправлено {fixed} заблокованих аплікаторів', 'success')

    elif action == 'cleanup_invalid_cells':
        cleaned = ValidationService.cleanup_invalid_cells()
        flash(f'Очищено {cleaned} невідповідностей', 'success')

    return redirect(url_for('management.validation'))
