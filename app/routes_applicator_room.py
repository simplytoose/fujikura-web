from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.services.applicator_service import ApplicatorService
from app.services.room_service import ApplicatorRoomService, ServiceAreaService, InactiveApplicatorService
from app.services.movement_service import MovementService
from app.services.production_service import CuttingAreaService, CrimpingAreaService
from app.models import StatusEnum
from functools import wraps
from datetime import datetime

applicator_room_bp = Blueprint('applicator_room', __name__, url_prefix='/applicator-room')

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


@applicator_room_bp.route('/')
@login_required
def view_room():

    ApplicatorRoomService.initialize_cells()

    page = request.args.get('page', 1, type=int)
    per_page = 15
    search = request.args.get('search', '')

    cells = ApplicatorRoomService.get_all_cells()

    if search:
        cells = [c for c in cells if str(c.cell_number).startswith(search)]

    total = len(cells)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_cells = cells[start:end]

    free_count = ApplicatorRoomService.get_free_cells_count()
    occupied_count = ApplicatorRoomService.get_occupied_cells_count()

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

    return render_template('applicator_room/view.html',
                         cells=paginated_cells,
                         pagination=pagination,
                         free_count=free_count,
                         occupied_count=occupied_count,
                         total=total,
                         search=search)


@applicator_room_bp.route('/assign/<int:applicator_id>', methods=['POST'])
@login_required
def assign_cell(applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        flash('Аплікатор не знайдено', 'danger')
        return redirect(url_for('applicator_room.view_room'))

    cell = ApplicatorRoomService.assign_cell(applicator_id)
    if cell:
        ApplicatorService.update_applicator(applicator_id,
                                          location='Aplicator Room',
                                          status=StatusEnum.AVAILABLE.value,
                                          cell_number=cell.cell_number)

        MovementService.record_movement(
            applicator_id, applicator.code,
            applicator.location, 'Aplicator Room',
            current_user.id, current_user.username,
            f'Призначена комірка №{cell.cell_number}'
        )

        flash(f'Комірка №{cell.cell_number} призначена аплікатору {applicator.code}', 'success')
    else:
        flash('Немає вільних комірок', 'danger')

    return redirect(url_for('applicator_room.view_room'))


@applicator_room_bp.route('/cell/<int:cell_number>')
@login_required
def view_cell(cell_number):

    cell = ApplicatorRoomService.get_cell(cell_number)
    if not cell:
        flash('Комірка не знайдена', 'danger')
        return redirect(url_for('applicator_room.view_room'))

    applicator = None
    if cell.applicator_id:
        applicator = ApplicatorService.get_applicator(cell.applicator_id)

    return render_template('applicator_room/cell_detail.html',
                         cell=cell,
                         applicator=applicator)


@applicator_room_bp.route('/free/<int:cell_number>', methods=['POST'])
@login_required
@technician_required
def free_cell(cell_number):

    cell = ApplicatorRoomService.get_cell(cell_number)
    if not cell or not cell.is_occupied:
        flash('Комірка не займана', 'danger')
        return redirect(url_for('applicator_room.view_room'))

    if cell.applicator_id:
        ApplicatorRoomService.free_cell(cell_number)
        flash(f'Комірка №{cell_number} звільнена', 'success')

    return redirect(url_for('applicator_room.view_cell', cell_number=cell_number))
