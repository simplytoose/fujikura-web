from data_manager import dm
from models import Machine
from services.applicator_service import ApplicatorService
from datetime import datetime


class MachineService:


    @staticmethod
    def create_machine(code, machine_type="cutting", location=None):

        max_capacity = 5 if machine_type == "cutting" else 3

        machine = Machine(
            code=code,
            type=machine_type,
            location=location or ("Cutting" if machine_type == "cutting" else "Crimping"),
            max_capacity=max_capacity
        )

        machine_data = machine.to_dict()
        machine_data.pop('id', None)
        created = dm.create('machines', machine_data)

        return Machine.from_dict(created)

    @staticmethod
    def get_machine(machine_id):

        data = dm.read('machines', machine_id)
        return Machine.from_dict(data) if data else None

    @staticmethod
    def get_machine_by_code(code):

        data = dm.find_by_field('machines', 'code', code)
        return Machine.from_dict(data) if data else None

    @staticmethod
    def get_all_machines():

        machines_data = dm.get_all('machines')
        return [Machine.from_dict(m) for m in machines_data]

    @staticmethod
    def get_cutting_machines():

        machines_data = dm.list('machines', {'type': 'cutting'})
        return [Machine.from_dict(m) for m in machines_data]

    @staticmethod
    def search_machines(query, machine_type=None):

        if not query:
            machines_data = dm.list('machines', {'type': machine_type}) if machine_type else dm.get_all('machines')
            return [Machine.from_dict(m) for m in machines_data]

        results = dm.search('machines', 'code', query)
        unique_results = []
        seen_ids = set()

        for record in results:
            if record['id'] in seen_ids:
                continue
            if machine_type and record.get('type') != machine_type:
                continue
            unique_results.append(record)
            seen_ids.add(record['id'])

        return [Machine.from_dict(m) for m in unique_results]

    @staticmethod
    def get_crimping_machines():

        machines_data = dm.list('machines', {'type': 'crimping'})
        return [Machine.from_dict(m) for m in machines_data]

    @staticmethod
    def can_add_applicator(machine_code):

        machine = MachineService.get_machine_by_code(machine_code)
        if not machine:
            return False, "Машина не знайдена"

        if len(machine.applicators) >= machine.max_capacity:
            return False, f"На машині вже знаходиться максимальна кількість аплікаторів ({machine.max_capacity})"

        return True, "OK"

    @staticmethod
    def add_applicator_to_machine(machine_code, applicator_id):

        can_add, message = MachineService.can_add_applicator(machine_code)
        if not can_add:
            return False, message

        machine = MachineService.get_machine_by_code(machine_code)

        if applicator_id in machine.applicators:
            return False, "Аплікатор вже знаходиться на машині"

        machine.applicators.append(applicator_id)

        machine_data = machine.to_dict()
        dm.update('machines', machine.id, machine_data)

        ApplicatorService.update_applicator(applicator_id, machine=machine_code)

        return True, "OK"

    @staticmethod
    def remove_applicator_from_machine(machine_code, applicator_id):

        machine = MachineService.get_machine_by_code(machine_code)
        if not machine:
            return False, "Машина не знайдена"

        if applicator_id not in machine.applicators:
            return False, "Аплікатор не знаходиться на цій машині"

        machine.applicators.remove(applicator_id)

        machine_data = machine.to_dict()
        dm.update('machines', machine.id, machine_data)

        ApplicatorService.update_applicator(applicator_id, machine=None)

        return True, "OK"

    @staticmethod
    def get_applicators_on_machine(machine_code):

        return ApplicatorService.get_applicators_by_machine(machine_code)

    @staticmethod
    def get_machine_load(machine_code):

        machine = MachineService.get_machine_by_code(machine_code)
        if not machine:
            return 0

        return (len(machine.applicators) / machine.max_capacity) * 100 if machine.max_capacity > 0 else 0

    @staticmethod
    def get_machines_by_location(location):

        machines_data = dm.list('machines', {'location': location})
        return [Machine.from_dict(m) for m in machines_data]

    @staticmethod
    def count_machines():

        return dm.count('machines')

    @staticmethod
    def count_machines_by_type(machine_type):

        return dm.count('machines', {'type': machine_type})

    @staticmethod
    def get_machines_statistics():

        machines = MachineService.get_all_machines()
        stats = {
            'total': len(machines),
            'cutting': 0,
            'crimping': 0,
            'total_applicators': 0,
            'machines': []
        }

        for machine in machines:
            machine_stat = {
                'code': machine.code,
                'type': machine.type,
                'applicators_count': len(machine.applicators),
                'max_capacity': machine.max_capacity,
                'load_percentage': MachineService.get_machine_load(machine.code)
            }
            stats['machines'].append(machine_stat)
            stats['total_applicators'] += len(machine.applicators)

            if machine.type == 'cutting':
                stats['cutting'] += 1
            elif machine.type == 'crimping':
                stats['crimping'] += 1

        return stats

    @staticmethod
    def move_applicator_to_machine(from_machine_code, to_machine_code, applicator_id):

        from_machine = MachineService.get_machine_by_code(from_machine_code)
        to_machine = MachineService.get_machine_by_code(to_machine_code)
        applicator = ApplicatorService.get_applicator(applicator_id)

        if not from_machine:
            return False, "Машина відправлення не знайдена"
        if not to_machine:
            return False, "Машина призначення не знайдена"
        if not applicator:
            return False, "Аплікатор не знайдено"

        if applicator_id not in from_machine.applicators:
            return False, f"Аплікатор не знаходиться на машині {from_machine_code}"

        from models import StatusEnum
        if applicator.status == StatusEnum.BLOCKED.value:
            return False, "Неможливо перемістити заблокований аплікатор"

        can_add, message = MachineService.can_add_applicator(to_machine_code)
        if not can_add:
            return False, "Неможливо перемістити аплікатор. Машина заповнена."

        from_machine.applicators.remove(applicator_id)
        to_machine.applicators.append(applicator_id)

        dm.update('machines', from_machine.id, from_machine.to_dict())
        dm.update('machines', to_machine.id, to_machine.to_dict())

        ApplicatorService.update_applicator(
            applicator_id,
            machine=to_machine_code,
            location=to_machine.location
        )

        return True, f"Аплікатор успішно переміщено на машину {to_machine_code}"
