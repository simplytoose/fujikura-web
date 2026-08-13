from app.data_manager import dm
from app.models import Applicator, StatusEnum
from datetime import datetime
from app.services.room_service import ApplicatorRoomService


class ApplicatorService:


    @staticmethod
    def create_applicator(code, name=None, location="Aplicator Room", status=StatusEnum.AVAILABLE.value, notes=""):

        applicator = Applicator(
            code=code,
            name=name or code,
            location=location,
            status=status,
            notes=notes
        )

        app_data = applicator.to_dict()
        app_data.pop('id', None)
        created = dm.create('applicators', app_data)
        applicator = Applicator.from_dict(created)

        if location == "Aplicator Room":
            ApplicatorService._assign_room_cell(applicator.id)

        return ApplicatorService.get_applicator(applicator.id) or applicator

    @staticmethod
    def _assign_room_cell(app_id):

        ApplicatorRoomService.initialize_cells()
        cell = ApplicatorRoomService.assign_cell(app_id)
        if cell:
            ApplicatorService.update_applicator(app_id, cell_number=cell.cell_number)
        return cell

    @staticmethod
    def get_applicator(app_id):

        data = dm.read('applicators', app_id)
        return Applicator.from_dict(data) if data else None

    @staticmethod
    def get_applicator_by_code(code):

        data = dm.find_by_field('applicators', 'code', code)
        return Applicator.from_dict(data) if data else None

    @staticmethod
    def update_applicator(app_id, **kwargs):

        update_data = {}
        allowed_keys = ['location', 'status', 'machine', 'shelf_position', 'notes', 'last_moved_at',
                       'technician_id', 'name', 'cell_number', 'is_configured', 'configured_by',
                       'configured_at', 'on_machine', 'on_shelf', 'blocked_reason', 'blocked_by',
                       'blocked_at', 'inactive_reason', 'inactive_by', 'inactive_at', 'comments',
                       'current_cycles', 'max_cycles']
        for key in allowed_keys:
            if key in kwargs:
                update_data[key] = kwargs[key]

        updated = dm.update('applicators', app_id, update_data)
        return Applicator.from_dict(updated) if updated else None

    @staticmethod
    def _purge_related_records(table, field, value):

        file_data = dm.load_file(table)
        if not isinstance(file_data, dict) or 'records' not in file_data:
            return

        file_data['records'] = [
            record for record in file_data['records']
            if record.get(field) != value
        ]
        dm.save_file(table, file_data)

    @staticmethod
    def delete_applicator(app_id):

        applicator = ApplicatorService.get_applicator(app_id)
        if not applicator:
            return False

        if applicator.cell_number:
            ApplicatorRoomService.free_cell(applicator.cell_number)
        else:
            for cell in dm.list('applicator_cells', {'applicator_id': app_id}):
                dm.update('applicator_cells', cell['id'],
                          {'is_occupied': False, 'applicator_id': None})

        for table in ('movements', 'blocking_history', 'service_confirmations', 'inactive_applicators'):
            ApplicatorService._purge_related_records(table, 'applicator_id', app_id)

        return dm.delete('applicators', app_id)

    @staticmethod
    def get_all_applicators():

        apps_data = dm.get_all('applicators')
        return [Applicator.from_dict(a) for a in apps_data]

    @staticmethod
    def get_applicators_by_location(location):

        apps_data = dm.list('applicators', {'location': location})
        return [Applicator.from_dict(a) for a in apps_data]

    @staticmethod
    def get_applicators_by_status(status):

        apps_data = dm.list('applicators', {'status': status})
        return [Applicator.from_dict(a) for a in apps_data]

    @staticmethod
    def get_applicators_by_machine(machine_code):

        apps_data = dm.list('applicators', {'machine': machine_code})
        return [Applicator.from_dict(a) for a in apps_data]

    @staticmethod
    def count_applicators():

        return dm.count('applicators')

    @staticmethod
    def count_by_location(location):

        return dm.count('applicators', {'location': location})

    @staticmethod
    def count_by_status(status):

        return dm.count('applicators', {'status': status})

    @staticmethod
    def block_applicator(app_id, reason=""):

        return ApplicatorService.update_applicator(app_id, status=StatusEnum.BLOCKED.value, notes=reason)

    @staticmethod
    def unblock_applicator(app_id):

        return ApplicatorService.update_applicator(app_id, status=StatusEnum.AVAILABLE.value)

    @staticmethod
    def is_blocked(app_id):

        app = ApplicatorService.get_applicator(app_id)
        return app and app.status == StatusEnum.BLOCKED.value

    @staticmethod
    def is_available(app_id):

        app = ApplicatorService.get_applicator(app_id)
        return app and app.status in [StatusEnum.AVAILABLE.value, StatusEnum.SERVICE.value]

    @staticmethod
    def get_applicators_available_for_machine():

        eligible_statuses = {StatusEnum.AVAILABLE.value, StatusEnum.SERVICE.value}
        return [
            app for app in ApplicatorService.get_all_applicators()
            if not app.machine and app.status in eligible_statuses
        ]

    @staticmethod
    def search_applicators(query):

        results = dm.search('applicators', 'code', query)
        results += dm.search('applicators', 'notes', query)

        seen = set()
        unique_results = []
        for r in results:
            if r['code'] not in seen:
                unique_results.append(r)
                seen.add(r['code'])

        return [Applicator.from_dict(a) for a in unique_results]

    @staticmethod
    def get_statistics():

        total = ApplicatorService.count_applicators()

        return {
            'total': total,
            'available': dm.count('applicators', {'status': StatusEnum.AVAILABLE.value}),
            'service': dm.count('applicators', {'status': StatusEnum.SERVICE.value}),
            'cutting': dm.count('applicators', {'status': StatusEnum.CUTTING.value}),
            'crimping': dm.count('applicators', {'status': StatusEnum.CRIMPING.value}),
            'blocked': dm.count('applicators', {'status': StatusEnum.BLOCKED.value}),
            'inactive': dm.count('applicators', {'status': StatusEnum.INACTIVE.value}),
        }

    @staticmethod
    def get_location_statistics():

        return {
            'Aplicator Room': ApplicatorService.count_by_location('Aplicator Room'),
            'Service': ApplicatorService.count_by_location('Service'),
            'Cutting': ApplicatorService.count_by_location('Cutting'),
            'Crimping': ApplicatorService.count_by_location('Crimping'),
            'Blocked': dm.count('applicators', {'status': StatusEnum.BLOCKED.value}),
            'Inactive': dm.count('applicators', {'status': StatusEnum.INACTIVE.value}),
        }

    @staticmethod
    def take_to_work(app_id, technician_id):

        app = ApplicatorService.get_applicator(app_id)
        if not app:
            return None

        if app.status != StatusEnum.INACTIVE.value:
            return None

        return ApplicatorService.update_applicator(
            app_id,
            status=StatusEnum.AVAILABLE.value,
            technician_id=technician_id,
            last_moved_at=datetime.utcnow().isoformat()
        )

    @staticmethod
    def return_to_use(app_id):

        app = ApplicatorService.get_applicator(app_id)
        if not app:
            return None

        if app.status != StatusEnum.AVAILABLE.value:
            return None

        return ApplicatorService.update_applicator(
            app_id,
            status=StatusEnum.INACTIVE.value,
            technician_id=None,
            last_moved_at=datetime.utcnow().isoformat()
        )

    @staticmethod
    def get_active_applicators_by_technician(technician_id):

        apps_data = dm.list('applicators', {'technician_id': technician_id, 'status': StatusEnum.AVAILABLE.value})
        return [Applicator.from_dict(a) for a in apps_data]

    @staticmethod
    def add_comment(app_id, author, text):

        app = ApplicatorService.get_applicator(app_id)
        if not app:
            return None

        comment = {
            'id': datetime.utcnow().timestamp(),
            'author': author,
            'text': text,
            'created_at': datetime.utcnow().isoformat()
        }

        if not app.comments:
            app.comments = []
        app.comments.append(comment)

        return ApplicatorService.update_applicator(app_id, comments=app.comments)

    @staticmethod
    def delete_comment(app_id, comment_id):

        app = ApplicatorService.get_applicator(app_id)
        if not app or not app.comments:
            return False

        app.comments = [c for c in app.comments if c.get('id') != comment_id]
        ApplicatorService.update_applicator(app_id, comments=app.comments)
        return True

    @staticmethod
    def get_comments(app_id):

        app = ApplicatorService.get_applicator(app_id)
        return app.comments if app and app.comments else []

    @staticmethod
    def update_applicator_name(app_id, name):

        return ApplicatorService.update_applicator(app_id, name=name)

    @staticmethod
    def add_cycles(app_id, cycles):
        app = ApplicatorService.get_applicator(app_id)
        if not app:
            return None
        
        new_cycles = app.current_cycles + cycles
        new_status = app.status
        
        if new_cycles >= app.max_cycles and app.status != StatusEnum.SERVICE.value and app.status != StatusEnum.IN_REPAIR.value and app.status != StatusEnum.WRITTEN_OFF.value:
            new_status = StatusEnum.NEEDS_TO.value
            
        return ApplicatorService.update_applicator(
            app_id,
            current_cycles=new_cycles,
            status=new_status
        )

    @staticmethod
    def reset_cycles(app_id):
        return ApplicatorService.update_applicator(
            app_id,
            current_cycles=0,
            status=StatusEnum.AVAILABLE.value
        )
