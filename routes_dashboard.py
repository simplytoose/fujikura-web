from flask import Blueprint, render_template, request
from flask_login import login_required
from services.applicator_service import ApplicatorService
from services.machine_service import MachineService
from services.room_service import ApplicatorRoomService, ServiceAreaService, InactiveApplicatorService
from services.production_service import CuttingAreaService, CrimpingAreaService
from services.movement_service import MovementService

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/')
@login_required
def dashboard():

    ApplicatorRoomService.initialize_cells()

    stats = ApplicatorService.get_statistics()
    location_stats = ApplicatorService.get_location_statistics()

    search_query = request.args.get('search', '').strip()
    applicator_search_results = []
    machine_search_results = []
    if search_query:
        applicator_search_results = ApplicatorService.search_applicators(search_query)
        machine_search_results = MachineService.search_machines(search_query)


    room_stats = {
        'free': ApplicatorRoomService.get_free_cells_count(),
        'occupied': ApplicatorRoomService.get_occupied_cells_count(),
        'total': 300
    }

    service_area = {
        'total': ApplicatorService.count_by_location('Service'),
        'configured': sum(1 for a in ApplicatorService.get_applicators_by_location('Service')
                         if ServiceAreaService.is_configured(a.id)),
        'unconfigured': ServiceAreaService.get_unconfirmed_count()
    }

    cutting_area = {
        'total': ApplicatorService.count_by_location('Cutting'),
        'machines': CuttingAreaService.get_all_machines()
    }

    crimping_area = {
        'total': ApplicatorService.count_by_location('Crimping'),
        'machines': CrimpingAreaService.get_all_machines()
    }

    blocked = {
        'total': stats['blocked']
    }

    inactive = {
        'total': InactiveApplicatorService.get_inactive_count()
    }

    recent_movements = MovementService.get_all_movements()[-10:] if MovementService.get_all_movements() else []

    return render_template('dashboard.html',
                         stats=stats,
                         location_stats=location_stats,
                         room_stats=room_stats,
                         service_area=service_area,
                         cutting_area=cutting_area,
                         blocked=blocked,
                         inactive=inactive,
                         recent_movements=recent_movements,
                         search_query=search_query,
                         applicator_search_results=applicator_search_results,
                         machine_search_results=machine_search_results)

