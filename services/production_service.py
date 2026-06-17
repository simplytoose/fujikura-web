from data_manager import dm
from models import Applicator, StatusEnum
from datetime import datetime


class CuttingAreaService:


    MACHINE_PREFIX = 'G'
    TOTAL_MACHINES = 30
    MAX_CAPACITY = 5
    MAX_ON_MACHINE = 2
    MAX_ON_SHELF = 3

    @staticmethod
    def get_all_machines():

        machines = []
        for i in range(1, CuttingAreaService.TOTAL_MACHINES + 1):
            code = f"{CuttingAreaService.MACHINE_PREFIX}{i:02d}"
            apps = dm.list('applicators', {'machine': code, 'location': 'Cutting'})
            on_machine = [a for a in apps if a.get('on_machine', False)]
            on_shelf = [a for a in apps if a.get('on_shelf', False)]

            machines.append({
                'code': code,
                'total': len(apps),
                'on_machine': len(on_machine),
                'on_shelf': len(on_shelf),
                'max_capacity': CuttingAreaService.MAX_CAPACITY,
                'is_full': len(apps) >= CuttingAreaService.MAX_CAPACITY,
                'applicators': apps
            })
        return machines

    @staticmethod
    def get_machine(machine_code):

        apps = dm.list('applicators', {'machine': machine_code, 'location': 'Cutting'})
        on_machine = [a for a in apps if a.get('on_machine', False)]
        on_shelf = [a for a in apps if a.get('on_shelf', False)]

        return {
            'code': machine_code,
            'total': len(apps),
            'on_machine': len(on_machine),
            'on_shelf': len(on_shelf),
            'max_capacity': CuttingAreaService.MAX_CAPACITY,
            'is_full': len(apps) >= CuttingAreaService.MAX_CAPACITY,
            'applicators': apps
        }

    @staticmethod
    def can_add_to_machine(machine_code, on_machine=False):

        machine = CuttingAreaService.get_machine(machine_code)

        if machine['total'] >= CuttingAreaService.MAX_CAPACITY:
            return False, "Неможливо перемістити аплікатор. Машина заповнена."

        if on_machine and machine['on_machine'] >= CuttingAreaService.MAX_ON_MACHINE:
            return False, "На машині вже максимум аплікаторів. Залишилось тільки місце на стелажі"

        if not on_machine and machine['on_shelf'] >= CuttingAreaService.MAX_ON_SHELF:
            return False, "На стелажі вже максимум аплікаторів. Залишилось тільки місце на машині"

        return True, ""

    @staticmethod
    def add_applicator(applicator_id, machine_code, on_machine=False):

        app_data = dm.read('applicators', applicator_id)
        if not app_data:
            return None, "Аплікатор не знайдено"

        if app_data.get('status') == StatusEnum.BLOCKED.value:
            return None, "Неможливо перемістити заблокований аплікатор"

        can_add, error_msg = CuttingAreaService.can_add_to_machine(machine_code, on_machine)
        if not can_add:
            return None, error_msg

        update_data = {
            'machine': machine_code,
            'location': 'Cutting',
            'status': StatusEnum.CUTTING.value,
            'on_machine': on_machine,
            'on_shelf': not on_machine,
            'last_moved_at': datetime.utcnow().isoformat()
        }

        updated = dm.update('applicators', applicator_id, update_data)
        return updated, "" if updated else (None, "Не вдалося оновити аплікатор")

    @staticmethod
    def remove_applicator(applicator_id, machine_code):

        update_data = {
            'machine': None,
            'location': 'Service',
            'status': StatusEnum.SERVICE.value,
            'on_machine': False,
            'on_shelf': False,
            'last_moved_at': datetime.utcnow().isoformat()
        }

        updated = dm.update('applicators', applicator_id, update_data)
        return updated


class CrimpingAreaService:


    MACHINE_PREFIX = 'P'
    TOTAL_MACHINES = 5
    MAX_CAPACITY = 3
    MAX_ON_MACHINE = 1
    MAX_ON_SHELF = 2

    @staticmethod
    def get_all_machines():

        machines = []
        for i in range(1, CrimpingAreaService.TOTAL_MACHINES + 1):
            code = f"{CrimpingAreaService.MACHINE_PREFIX}{i:02d}"
            apps = dm.list('applicators', {'machine': code, 'location': 'Crimping'})
            on_machine = [a for a in apps if a.get('on_machine', False)]
            on_shelf = [a for a in apps if a.get('on_shelf', False)]

            machines.append({
                'code': code,
                'total': len(apps),
                'on_machine': len(on_machine),
                'on_shelf': len(on_shelf),
                'max_capacity': CrimpingAreaService.MAX_CAPACITY,
                'is_full': len(apps) >= CrimpingAreaService.MAX_CAPACITY,
                'applicators': apps
            })
        return machines

    @staticmethod
    def get_machine(machine_code):

        apps = dm.list('applicators', {'machine': machine_code, 'location': 'Crimping'})
        on_machine = [a for a in apps if a.get('on_machine', False)]
        on_shelf = [a for a in apps if a.get('on_shelf', False)]

        return {
            'code': machine_code,
            'total': len(apps),
            'on_machine': len(on_machine),
            'on_shelf': len(on_shelf),
            'max_capacity': CrimpingAreaService.MAX_CAPACITY,
            'is_full': len(apps) >= CrimpingAreaService.MAX_CAPACITY,
            'applicators': apps
        }

    @staticmethod
    def can_add_to_machine(machine_code, on_machine=False):

        machine = CrimpingAreaService.get_machine(machine_code)

        if machine['total'] >= CrimpingAreaService.MAX_CAPACITY:
            return False, "Неможливо перемістити аплікатор. Машина заповнена."

        if on_machine and machine['on_machine'] >= CrimpingAreaService.MAX_ON_MACHINE:
            return False, "На машині вже максимум аплікаторів. Залишилось тільки місце на стелажі"

        if not on_machine and machine['on_shelf'] >= CrimpingAreaService.MAX_ON_SHELF:
            return False, "На стелажі вже максимум аплікаторів. Залишилось тільки місце на машині"

        return True, ""

    @staticmethod
    def add_applicator(applicator_id, machine_code, on_machine=False):

        app_data = dm.read('applicators', applicator_id)
        if not app_data:
            return None, "Аплікатор не знайдено"

        if app_data.get('status') == StatusEnum.BLOCKED.value:
            return None, "Неможливо перемістити заблокований аплікатор"

        can_add, error_msg = CrimpingAreaService.can_add_to_machine(machine_code, on_machine)
        if not can_add:
            return None, error_msg

        update_data = {
            'machine': machine_code,
            'location': 'Crimping',
            'status': StatusEnum.CRIMPING.value,
            'on_machine': on_machine,
            'on_shelf': not on_machine,
            'last_moved_at': datetime.utcnow().isoformat()
        }

        updated = dm.update('applicators', applicator_id, update_data)
        return updated, "" if updated else (None, "Не вдалося оновити аплікатор")

    @staticmethod
    def remove_applicator(applicator_id, machine_code):

        update_data = {
            'machine': None,
            'location': 'Service',
            'status': StatusEnum.SERVICE.value,
            'on_machine': False,
            'on_shelf': False,
            'last_moved_at': datetime.utcnow().isoformat()
        }

        updated = dm.update('applicators', applicator_id, update_data)
        return updated
