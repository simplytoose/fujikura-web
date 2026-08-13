from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.services.machine_service import MachineService
from app.services.applicator_service import ApplicatorService
from app.services.movement_service import MovementService
from app.models import StatusEnum
from functools import wraps

machines_bp = Blueprint('machines', __name__, url_prefix='/machines')


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


@machines_bp.route('/cutting')
@login_required
def cutting():

    machines = MachineService.get_cutting_machines()
    applicators = ApplicatorService.get_applicators_by_location('Cutting')

    return render_template('machines/cutting.html', machines=machines, applicators=applicators)


@machines_bp.route('/crimping')
@login_required
def crimping():

    machines = MachineService.get_crimping_machines()
    applicators = ApplicatorService.get_applicators_by_location('Crimping')

    return render_template('machines/crimping.html', machines=machines, applicators=applicators)


@machines_bp.route('/add-to-machine', methods=['POST'])
@technician_required
def add_to_machine():

    data = request.get_json() if request.is_json else request.form

    applicator_id = int(data.get('applicator_id', 0))
    machine_code = data.get('machine_code', '').strip()

    applicator = ApplicatorService.get_applicator(applicator_id)
    machine = MachineService.get_machine_by_code(machine_code)

    if not applicator or not machine:
        return jsonify({'success': False, 'message': 'Аплікатор або машина не знайдена'}), 404

    if applicator.status == StatusEnum.BLOCKED.value:
        return jsonify({'success': False, 'message': 'Аплікатор заблокований та недоступний для використання'}), 400

    if applicator.status == StatusEnum.INACTIVE.value:
        return jsonify({'success': False, 'message': 'Аплікатор виведений з експлуатації'}), 400

    if applicator.machine and applicator.machine != machine_code:
        return jsonify({
            'success': False,
            'message': f'Аплікатор вже знаходиться на машині {applicator.machine}'
        }), 400

    can_add, message = MachineService.can_add_applicator(machine_code)
    if not can_add:
        return jsonify({'success': False, 'message': message}), 400

    success, message = MachineService.add_applicator_to_machine(machine_code, applicator_id)
    if not success:
        return jsonify({'success': False, 'message': message}), 400

    old_location = applicator.location
    new_status = StatusEnum.CUTTING.value if machine.type == 'cutting' else StatusEnum.CRIMPING.value

    ApplicatorService.update_applicator(applicator_id, location=machine.location, status=new_status, machine=machine_code)

    MovementService.record_movement(
        applicator_id=applicator_id,
        applicator_code=applicator.code,
        from_location=old_location,
        to_location=machine.location,
        to_machine=machine_code,
        user_id=current_user.id,
        username=current_user.username,
        comment=f'Розміщено на машині'
    )

    return jsonify({
        'success': True,
        'message': f'Аплікатор {applicator.code} додано на машину {machine_code}'
    })


@machines_bp.route('/remove-from-machine', methods=['POST'])
@technician_required
def remove_from_machine():

    data = request.get_json() if request.is_json else request.form

    applicator_id = int(data.get('applicator_id', 0))
    machine_code = data.get('machine_code', '').strip()

    applicator = ApplicatorService.get_applicator(applicator_id)
    machine = MachineService.get_machine_by_code(machine_code)

    if not applicator or not machine:
        return jsonify({'success': False, 'message': 'Аплікатор або машина не знайдена'}), 404

    if applicator.machine != machine_code:
        return jsonify({'success': False, 'message': 'Аплікатор не знаходиться на цій машині'}), 400

    success, message = MachineService.remove_applicator_from_machine(machine_code, applicator_id)
    if not success:
        return jsonify({'success': False, 'message': message}), 400

    old_location = applicator.location

    ApplicatorService.update_applicator(applicator_id, location='Service', status=StatusEnum.SERVICE.value, machine=None)

    MovementService.record_movement(
        applicator_id=applicator_id,
        applicator_code=applicator.code,
        from_location=old_location,
        from_machine=machine_code,
        to_location='Service',
        user_id=current_user.id,
        username=current_user.username,
        comment='Знято з машини'
    )

    return jsonify({
        'success': True,
        'message': f'Аплікатор {applicator.code} видалено з машини {machine_code}'
    })


@machines_bp.route('/<machine_code>')
@login_required
def machine_detail(machine_code):

    machine = MachineService.get_machine_by_code(machine_code)
    if not machine:
        flash('Машина не знайдена', 'danger')
        location = 'cutting'
        return redirect(url_for('machines.' + location))

    applicators = ApplicatorService.get_applicators_by_machine(machine_code)
    available_applicators = sorted(
        ApplicatorService.get_applicators_available_for_machine(),
        key=lambda a: a.id or 0,
        reverse=True
    )
    history = MovementService.get_movements_by_machine(machine_code)

    return render_template(
        'machines/detail.html',
        machine=machine,
        applicators=applicators,
        available_applicators=available_applicators,
        history=history,
    )


@machines_bp.route('/<machine_code>/move/<int:applicator_id>', methods=['POST'])
@technician_required
def move_applicator(machine_code, applicator_id):

    try:
        data = request.get_json() if request.is_json else request.form

        to_machine_code = data.get('to_machine_code', '').strip() if data else ''

        if not to_machine_code:
            return jsonify({'success': False, 'message': 'Машина призначення не вибрана'}), 400

        applicator = ApplicatorService.get_applicator(applicator_id)
        if not applicator:
            return jsonify({'success': False, 'message': 'Аплікатор не знайдено'}), 404

        if applicator.status == StatusEnum.BLOCKED.value:
            return jsonify({'success': False, 'message': 'Неможливо перемістити заблокований аплікатор.'}), 400

        success, message = MachineService.move_applicator_to_machine(machine_code, to_machine_code, applicator_id)
        if not success:
            return jsonify({'success': False, 'message': message}), 400

        old_location = applicator.location
        from_machine = MachineService.get_machine_by_code(machine_code)
        to_machine = MachineService.get_machine_by_code(to_machine_code)

        MovementService.record_movement(
            applicator_id=applicator_id,
            applicator_code=applicator.code,
            from_location=old_location,
            to_location=to_machine.location if to_machine else 'Unknown',
            from_machine=machine_code,
            to_machine=to_machine_code,
            user_id=current_user.id,
            username=current_user.username,
            comment=f'Переміщено з {machine_code} на {to_machine_code}'
        )

        return jsonify({
            'success': True,
            'message': f'Аплікатор успішно переміщено на машину {to_machine_code}'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Помилка сервера: {str(e)}'
        }), 500
