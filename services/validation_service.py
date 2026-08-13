from data_manager import dm
from models import Applicator, StatusEnum
from datetime import datetime


class ValidationService:


    @staticmethod
    def check_duplicate_locations():

        applicators = dm.get_all('applicators')
        duplicates = []

        for app in applicators:
            if app.get('location') and app.get('machine'):
                location = app['location']
                machine = app['machine']
                on_machine = app.get('on_machine', False)
                on_shelf = app.get('on_shelf', False)

                if not (on_machine or on_shelf):
                    duplicates.append({
                        'applicator_id': app['id'],
                        'code': app['code'],
                        'location': location,
                        'machine': machine,
                        'issue': 'Machine location без on_machine або on_shelf флага'
                    })

        return duplicates

    @staticmethod
    def check_blocked_movements():

        applicators = dm.get_all('applicators')
        issues = []

        for app in applicators:
            if app.get('status') == StatusEnum.BLOCKED.value:
                if app.get('location') != 'Blocked':
                    issues.append({
                        'applicator_id': app['id'],
                        'code': app['code'],
                        'status': 'BLOCKED',
                        'location': app.get('location'),
                        'issue': 'Заблокований аплікатор не в зоні Blocked'
                    })

                if app.get('machine'):
                    issues.append({
                        'applicator_id': app['id'],
                        'code': app['code'],
                        'status': 'BLOCKED',
                        'machine': app.get('machine'),
                        'issue': 'Заблокований аплікатор на машині'
                    })

        return issues

    @staticmethod
    def check_machine_limits():

        issues = []

        cutting_machines = {}
        crimping_machines = {}

        for app in dm.get_all('applicators'):
            machine = app.get('machine')
            location = app.get('location')

            if not machine or location not in ['Cutting', 'Crimping']:
                continue

            if location == 'Cutting':
                if machine not in cutting_machines:
                    cutting_machines[machine] = 0
                cutting_machines[machine] += 1

                if cutting_machines[machine] > 5:
                    issues.append({
                        'machine': machine,
                        'count': cutting_machines[machine],
                        'max_capacity': 5,
                        'issue': 'Cutting машина перевищує ліміт на 5 аплікаторів'
                    })

            elif location == 'Crimping':
                if machine not in crimping_machines:
                    crimping_machines[machine] = 0
                crimping_machines[machine] += 1

                if crimping_machines[machine] > 3:
                    issues.append({
                        'machine': machine,
                        'count': crimping_machines[machine],
                        'max_capacity': 3,
                        'issue': 'Crimping машина перевищує ліміт на 3 аплікатори'
                    })

        return issues

    @staticmethod
    def check_history_integrity():

        movements = dm.get_all('movements')
        issues = []

        for movement in movements:
            if not movement.get('applicator_id') or not movement.get('applicator_code'):
                issues.append({
                    'movement_id': movement['id'],
                    'issue': 'Рух без applicator_id або applicator_code'
                })

            if not movement.get('from_location') or not movement.get('to_location'):
                issues.append({
                    'movement_id': movement['id'],
                    'issue': 'Рух без from_location або to_location'
                })

        return issues

    @staticmethod
    def check_cell_consistency():

        issues = []

        cells = dm.get_all('applicator_cells')
        occupied_cell_ids = set()

        for cell in cells:
            if cell.get('is_occupied') and cell.get('applicator_id'):
                app_id = cell['applicator_id']

                if app_id in occupied_cell_ids:
                    issues.append({
                        'applicator_id': app_id,
                        'issue': 'Один аплікатор в кількох комірках'
                    })
                occupied_cell_ids.add(app_id)

                app = dm.read('applicators', app_id)
                if not app:
                    issues.append({
                        'cell_number': cell['cell_number'],
                        'applicator_id': app_id,
                        'issue': 'Комірка посилається на неіснуючий аплікатор'
                    })

        return issues

    @staticmethod
    def check_service_area_consistency():

        issues = []
        confirmations = dm.get_all('service_confirmations')

        for conf in confirmations:
            app = dm.read('applicators', conf['applicator_id'])
            if not app:
                issues.append({
                    'confirmation_id': conf['id'],
                    'applicator_id': conf['applicator_id'],
                    'issue': 'Підтвердження для неіснуючого аплікатора'
                })

        return issues

    @staticmethod
    def run_full_validation():

        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'duplicate_locations': ValidationService.check_duplicate_locations(),
            'blocked_movements': ValidationService.check_blocked_movements(),
            'machine_limits': ValidationService.check_machine_limits(),
            'history_integrity': ValidationService.check_history_integrity(),
            'cell_consistency': ValidationService.check_cell_consistency(),
            'service_area_consistency': ValidationService.check_service_area_consistency()
        }

        total_issues = sum(len(issues) for issues in results.values() if isinstance(issues, list))
        results['total_issues'] = total_issues

        return results

    @staticmethod
    def fix_duplicate_location_flags(applicator_id):

        app = dm.read('applicators', applicator_id)
        if not app:
            return False

        if app.get('location') and app.get('machine'):
            if not (app.get('on_machine') or app.get('on_shelf')):
                dm.update('applicators', applicator_id, {'on_shelf': True})
                return True

        return False

    @staticmethod
    def fix_blocked_applicator_location(applicator_id):

        app = dm.read('applicators', applicator_id)
        if not app or app.get('status') != StatusEnum.BLOCKED.value:
            return False

        update_data = {
            'location': 'Blocked',
            'machine': None,
            'on_machine': False,
            'on_shelf': False
        }

        dm.update('applicators', applicator_id, update_data)
        return True

    @staticmethod
    def cleanup_invalid_cells():

        cells = dm.get_all('applicator_cells')
        cleaned = 0

        for cell in cells:
            if cell.get('is_occupied') and cell.get('applicator_id'):
                app = dm.read('applicators', cell['applicator_id'])
                if not app:
                    dm.update('applicator_cells', cell['id'],
                             {'is_occupied': False, 'applicator_id': None})
                    cleaned += 1

        return cleaned
