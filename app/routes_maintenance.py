from flask import Blueprint, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.applicator_service import ApplicatorService
from app.services.maintenance_service import MaintenanceService
from app.models import StatusEnum

maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')

@maintenance_bp.route('/cycles/add', methods=['POST'])
@login_required
def add_cycles():
    applicator_id = request.form.get('applicator_id')
    cycles_str = request.form.get('cycles', '0')
    
    if not applicator_id or not cycles_str.isdigit():
        flash('Некоректні дані', 'danger')
        return redirect(request.referrer or url_for('dashboard.dashboard'))
    
    cycles = int(cycles_str)
    if cycles <= 0:
        flash('Кількість циклів повинна бути більше нуля', 'warning')
        return redirect(request.referrer or url_for('dashboard.dashboard'))
        
    app = ApplicatorService.add_cycles(int(applicator_id), cycles)
    if app:
        flash(f'Додано {cycles} циклів до аплікатора {app.code}', 'success')
        if app.status == StatusEnum.NEEDS_TO.value:
            flash(f'Аплікатор {app.code} потребує ТО!', 'warning')
    else:
        flash('Аплікатор не знайдено', 'danger')
        
    return redirect(request.referrer or url_for('dashboard.dashboard'))

@maintenance_bp.route('/records/add', methods=['POST'])
@login_required
def add_maintenance_record():
    if not (current_user.is_technician() or current_user.is_admin()):
        flash('Ви не маєте доступу до цієї дії', 'danger')
        return redirect(request.referrer or url_for('dashboard.dashboard'))

    applicator_id = request.form.get('applicator_id')
    reason = request.form.get('reason', '').strip()
    replaced_parts_str = request.form.get('replaced_parts', '').strip()
    
    if not applicator_id or not reason:
        flash('Некоректні дані: ID або Причина відсутні', 'danger')
        return redirect(request.referrer or url_for('dashboard.dashboard'))
        
    app = ApplicatorService.get_applicator(int(applicator_id))
    if not app:
        flash('Аплікатор не знайдено', 'danger')
        return redirect(request.referrer or url_for('dashboard.dashboard'))
        
    replaced_parts = [p.strip() for p in replaced_parts_str.split(',') if p.strip()] if replaced_parts_str else []
    
    success = MaintenanceService.record_maintenance(
        applicator_id=app.id,
        applicator_code=app.code,
        replaced_parts=replaced_parts,
        reason=reason,
        technician_id=current_user.id,
        technician_name=current_user.username
    )
    
    if success:
        ApplicatorService.reset_cycles(app.id)
        flash('Запис про ТО додано, лічильник циклів скинуто', 'success')
    else:
        flash('Помилка при збереженні запису ТО', 'danger')
        
    return redirect(request.referrer or url_for('dashboard.dashboard'))
