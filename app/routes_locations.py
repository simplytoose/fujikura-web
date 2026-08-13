from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services.applicator_service import ApplicatorService
from app.models import StatusEnum, Location

locations_bp = Blueprint('locations', __name__, url_prefix='/locations')


@locations_bp.route('/room')
@login_required
def room():

    location = Location('Aplicator Room', 'Aplicator Room')
    for applicator in ApplicatorService.get_applicators_by_location('Aplicator Room'):
        if not applicator.cell_number and not applicator.machine:
            ApplicatorService._assign_room_cell(applicator.id)

    applicators = ApplicatorService.get_applicators_by_location('Aplicator Room')
    applicators.sort(key=lambda a: a.id or 0, reverse=True)
    stats = {
        'total': len(applicators),
        'available': len([a for a in applicators if a.status == StatusEnum.AVAILABLE.value]),
    }
    return render_template('locations/room.html', location=location, applicators=applicators, stats=stats)


@locations_bp.route('/service')
@login_required
def service():

    location = Location('Service', 'Дільниця обслуговування')
    applicators = ApplicatorService.get_applicators_by_location('Service')
    stats = {
        'total': len(applicators),
        'service': len([a for a in applicators if a.status == StatusEnum.SERVICE.value]),
    }
    return render_template('locations/service.html', location=location, applicators=applicators, stats=stats)


@locations_bp.route('/blocked')
@login_required
def blocked():

    location = Location('Blocked', 'Заблоковані аплікатори')
    applicators = ApplicatorService.get_applicators_by_status(StatusEnum.BLOCKED.value)
    stats = {
        'total': len(applicators),
    }
    return render_template('locations/blocked.html', location=location, applicators=applicators, stats=stats)


@locations_bp.route('/inactive')
@login_required
def inactive():

    location = Location('Inactive', 'Аплікатори без використання')
    applicators = ApplicatorService.get_applicators_by_status(StatusEnum.INACTIVE.value)
    stats = {
        'total': len(applicators),
    }
    return render_template('locations/inactive.html', location=location, applicators=applicators, stats=stats)


@locations_bp.route('/active')
@login_required
def active():

    location = Location('Active', 'Активні аплікатори')

    if current_user.is_admin():
        applicators = ApplicatorService.get_applicators_by_status(StatusEnum.AVAILABLE.value)
    else:
        applicators = ApplicatorService.get_active_applicators_by_technician(current_user.id)

    stats = {
        'total': len(applicators),
    }
    return render_template('locations/active.html', location=location, applicators=applicators, stats=stats)


@locations_bp.route('/applicator/<int:applicator_id>/take_to_work', methods=['POST'])
@login_required
def take_applicator_to_work(applicator_id):

    if not current_user.is_technician():
        flash('Тільки технарі можуть брати аплікатори в роботу', 'danger')
        return redirect(url_for('locations.inactive'))

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        flash('Аплікатор не знайдено', 'danger')
        return redirect(url_for('locations.inactive'))

    if applicator.status != StatusEnum.INACTIVE.value:
        flash('Цей аплікатор уже в роботі', 'warning')
        return redirect(url_for('locations.inactive'))

    result = ApplicatorService.take_to_work(applicator_id, current_user.id)
    if result:
        flash(f'Аплікатор {applicator.code} успішно взято в роботу', 'success')
    else:
        flash('Помилка при взятті аплікатора в роботу', 'danger')

    return redirect(url_for('locations.inactive'))


@locations_bp.route('/applicator/<int:applicator_id>/return_to_use', methods=['POST'])
@login_required
def return_applicator_to_use(applicator_id):

    if not current_user.is_technician() and not current_user.is_admin():
        flash('Тільки технарі та адміни можуть повертати аплікатори', 'danger')
        return redirect(url_for('locations.active'))

    applicator = ApplicatorService.get_applicator(applicator_id)
    if not applicator:
        flash('Аплікатор не знайдено', 'danger')
        return redirect(url_for('locations.active'))

    if applicator.status != StatusEnum.AVAILABLE.value:
        flash('Цей аплікатор не активний', 'warning')
        return redirect(url_for('locations.active'))

    if current_user.is_technician() and applicator.technician_id != current_user.id:
        flash('Ви можете повертати тільки свої аплікатори', 'danger')
        return redirect(url_for('locations.active'))

    result = ApplicatorService.return_to_use(applicator_id)
    if result:
        flash(f'Аплікатор {applicator.code} успішно повернуто в користування', 'success')
    else:
        flash('Помилка при повертанні аплікатора', 'danger')

    return redirect(url_for('locations.active'))
