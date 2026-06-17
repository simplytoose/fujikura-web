from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.applicator_service import ApplicatorService
from services.room_service import ServiceAreaService, InactiveApplicatorService
from services.movement_service import MovementService
from models import StatusEnum
from functools import wraps

service_area_bp = Blueprint('service_area', __name__, url_prefix='/service-area')

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


@service_area_bp.route('/')
@login_required
def view_service_area():

    applicators = ApplicatorService.get_applicators_by_location('Service')

    page = request.args.get('page', 1, type=int)
    per_page = 10

    total = len(applicators)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated = applicators[start:end]

    configured_count = sum(1 for a in applicators if ServiceAreaService.is_configured(a.id))
    unconfigured_count = len(applicators) - configured_count

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

    return render_template('service_area/view.html',
                         applicators=paginated,
                         pagination=pagination,
                         configured_count=configured_count,
                         unconfigured_count=unconfigured_count,
                         total=total)


@service_area_bp.route('/<int:applicator_id>/confirm', methods=['POST'])
@login_required
@technician_required
def confirm_setup(applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        flash('Аплікатор не знайдено', 'danger')
        return redirect(url_for('service_area.view_service_area'))

    conf = ServiceAreaService.confirm_setup(
        applicator_id,
        applicator.code,
        current_user.id,
        current_user.username
    )

    if conf:
        ApplicatorService.update_applicator(
            applicator_id,
            is_configured=True,
            configured_by=current_user.username,
            configured_at=conf.confirmed_at
        )

        MovementService.record_movement(
            applicator_id, applicator.code,
            applicator.location, 'Service',
            current_user.id, current_user.username,
            'Налаштування підтверджено'
        )

        flash(f'Налаштування аплікатора {applicator.code} підтверджено', 'success')
    else:
        flash('Помилка при підтвердженні налаштування', 'danger')

    return redirect(url_for('service_area.view_service_area'))


@service_area_bp.route('/<int:applicator_id>')
@login_required
def applicator_detail(applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        flash('Аплікатор не знайдено', 'danger')
        return redirect(url_for('service_area.view_service_area'))

    conf = ServiceAreaService.get_confirmation(applicator_id)
    movements = MovementService.get_movements_by_applicator(applicator_id)[-10:]

    return render_template('service_area/detail.html',
                         applicator=applicator,
                         confirmation=conf,
                         movements=movements)


@service_area_bp.route('/return/<int:applicator_id>', methods=['POST'])
@login_required
def return_to_production(applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        flash('Аплікатор не знайдено', 'danger')
        return redirect(url_for('service_area.view_service_area'))

    if not ServiceAreaService.is_configured(applicator_id):
        flash('Аплікатор не налаштований. Спочатку підтвердіть налаштування', 'warning')
        return redirect(url_for('service_area.applicator_detail', applicator_id=applicator_id))

    ApplicatorService.update_applicator(
        applicator_id,
        status=StatusEnum.AVAILABLE.value,
        location='Aplicator Room'
    )

    MovementService.record_movement(
        applicator_id, applicator.code,
        'Service', 'Aplicator Room',
        current_user.id, current_user.username,
        'Повернення в сховище'
    )

    flash(f'Аплікатор {applicator.code} повернений у Aplicator Room', 'success')
    return redirect(url_for('service_area.view_service_area'))
