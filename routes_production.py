from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.applicator_service import ApplicatorService
from services.production_service import CuttingAreaService, CrimpingAreaService
from services.movement_service import MovementService
from models import StatusEnum
from functools import wraps

production_bp = Blueprint('production', __name__, url_prefix='/production')

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


@production_bp.route('/cutting')
@login_required
def cutting_area():

    machines = CuttingAreaService.get_all_machines()
    total_on_machines = sum(m['on_machine'] for m in machines)
    total_on_shelves = sum(m['on_shelf'] for m in machines)

    return render_template('production/cutting_area.html',
                         machines=machines,
                         total_applicators=total_on_machines + total_on_shelves,
                         total_on_machines=total_on_machines,
                         total_on_shelves=total_on_shelves)


@production_bp.route('/cutting/<machine_code>')
@login_required
def cutting_machine(machine_code):

    machine = CuttingAreaService.get_machine(machine_code)
    applicators = [ApplicatorService.get_applicator(a['id']) for a in machine['applicators']]
    applicators = [a for a in applicators if a]

    return render_template('production/cutting_machine.html',
                         machine=machine,
                         applicators=applicators)


@production_bp.route('/cutting/<machine_code>/add/<int:applicator_id>', methods=['POST'])
@login_required
def add_to_cutting(machine_code, applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        return jsonify({'success': False, 'message': 'Аплікатор не знайдено'}), 404

    on_machine = request.json.get('on_machine', False) if request.is_json else False

    result, message = CuttingAreaService.add_applicator(applicator_id, machine_code, on_machine)

    if result:
        MovementService.record_movement(
            applicator_id, applicator.code,
            applicator.location or 'Service', 'Cutting',
            current_user.id, current_user.username,
            f'Додан на {"машину" if on_machine else "стелаж"} {machine_code}'
        )
        return jsonify({'success': True, 'message': 'Аплікатор додан'}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400


@production_bp.route('/cutting/<machine_code>/remove/<int:applicator_id>', methods=['POST'])
@login_required
def remove_from_cutting(machine_code, applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        return jsonify({'success': False, 'message': 'Аплікатор не знайдено'}), 404

    result = CuttingAreaService.remove_applicator(applicator_id, machine_code)

    if result:
        MovementService.record_movement(
            applicator_id, applicator.code,
            'Cutting', 'Service',
            current_user.id, current_user.username,
            f'Видалений з {machine_code}'
        )
        return jsonify({'success': True, 'message': 'Аплікатор видалений'}), 200
    else:
        return jsonify({'success': False, 'message': 'Помилка при видаленні'}), 400


@production_bp.route('/crimping')
@login_required
def crimping_area():

    machines = CrimpingAreaService.get_all_machines()
    total_on_machines = sum(m['on_machine'] for m in machines)
    total_on_shelves = sum(m['on_shelf'] for m in machines)

    return render_template('production/crimping_area.html',
                         machines=machines,
                         total_applicators=total_on_machines + total_on_shelves,
                         total_on_machines=total_on_machines,
                         total_on_shelves=total_on_shelves)


@production_bp.route('/crimping/<machine_code>')
@login_required
def crimping_machine(machine_code):

    machine = CrimpingAreaService.get_machine(machine_code)
    applicators = [ApplicatorService.get_applicator(a['id']) for a in machine['applicators']]
    applicators = [a for a in applicators if a]

    return render_template('production/crimping_machine.html',
                         machine=machine,
                         applicators=applicators)


@production_bp.route('/crimping/<machine_code>/add/<int:applicator_id>', methods=['POST'])
@login_required
def add_to_crimping(machine_code, applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        return jsonify({'success': False, 'message': 'Аплікатор не знайдено'}), 404

    on_machine = request.json.get('on_machine', False) if request.is_json else False

    result, message = CrimpingAreaService.add_applicator(applicator_id, machine_code, on_machine)

    if result:
        MovementService.record_movement(
            applicator_id, applicator.code,
            applicator.location or 'Service', 'Crimping',
            current_user.id, current_user.username,
            f'Додан на {"машину" if on_machine else "стелаж"} {machine_code}'
        )
        return jsonify({'success': True, 'message': 'Аплікатор додан'}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400


@production_bp.route('/crimping/<machine_code>/remove/<int:applicator_id>', methods=['POST'])
@login_required
def remove_from_crimping(machine_code, applicator_id):

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        return jsonify({'success': False, 'message': 'Аплікатор не знайдено'}), 404

    result = CrimpingAreaService.remove_applicator(applicator_id, machine_code)

    if result:
        MovementService.record_movement(
            applicator_id, applicator.code,
            'Crimping', 'Service',
            current_user.id, current_user.username,
            f'Видалений з {machine_code}'
        )
        return jsonify({'success': True, 'message': 'Аплікатор видалений'}), 200
    else:
        return jsonify({'success': False, 'message': 'Помилка при видаленні'}), 400
