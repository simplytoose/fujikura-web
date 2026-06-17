from data_manager import dm
from models import ApplicatorCell, ServiceAreaConfirmation, InactiveRecord
from datetime import datetime


class ApplicatorRoomService:


    @staticmethod
    def initialize_cells():

        cells_data = dm.load_file('applicator_cells')
        if not cells_data or 'records' not in cells_data:
            cells_data = {'records': []}
            for i in range(1, 301):
                cell = ApplicatorCell(cell_number=i, is_occupied=False)
                cell_dict = cell.to_dict()
                cell_dict.pop('id', None)
                created = dm.create('applicator_cells', cell_dict)
            return True
        return False

    @staticmethod
    def get_cell(cell_number):

        records = dm.list('applicator_cells', {'cell_number': cell_number})
        return ApplicatorCell.from_dict(records[0]) if records else None

    @staticmethod
    def assign_cell(applicator_id):

        records = dm.list('applicator_cells', {'is_occupied': False})
        if records:
            cell = records[0]
            updated = dm.update('applicator_cells', cell['id'],
                              {'is_occupied': True, 'applicator_id': applicator_id})
            return ApplicatorCell.from_dict(updated) if updated else None
        return None

    @staticmethod
    def free_cell(cell_number):

        records = dm.list('applicator_cells', {'cell_number': cell_number})
        if records:
            cell = records[0]
            updated = dm.update('applicator_cells', cell['id'],
                              {'is_occupied': False, 'applicator_id': None})
            return ApplicatorCell.from_dict(updated) if updated else None
        return None

    @staticmethod
    def get_free_cells_count():

        return dm.count('applicator_cells', {'is_occupied': False})

    @staticmethod
    def get_occupied_cells_count():

        return dm.count('applicator_cells', {'is_occupied': True})

    @staticmethod
    def get_all_cells():

        cells_data = dm.get_all('applicator_cells')
        return [ApplicatorCell.from_dict(c) for c in cells_data]


class ServiceAreaService:


    @staticmethod
    def confirm_setup(applicator_id, applicator_code, user_id, username):

        confirmation = ServiceAreaConfirmation(
            applicator_id=applicator_id,
            applicator_code=applicator_code,
            is_configured=True,
            confirmed_by=username,
            confirmed_at=datetime.utcnow().isoformat()
        )

        conf_data = confirmation.to_dict()
        conf_data.pop('id', None)
        created = dm.create('service_confirmations', conf_data)

        return ServiceAreaConfirmation.from_dict(created)

    @staticmethod
    def get_confirmation(applicator_id):

        records = dm.list('service_confirmations', {'applicator_id': applicator_id})
        if records:
            return ServiceAreaConfirmation.from_dict(records[-1])
        return None

    @staticmethod
    def is_configured(applicator_id):

        conf = ServiceAreaService.get_confirmation(applicator_id)
        return conf and conf.is_configured

    @staticmethod
    def get_unconfirmed_count():

        return dm.count('service_confirmations', {'is_configured': False})

    @staticmethod
    def get_all_confirmations():

        records = dm.get_all('service_confirmations')
        return [ServiceAreaConfirmation.from_dict(r) for r in records]


class InactiveApplicatorService:


    @staticmethod
    def mark_inactive(applicator_id, applicator_code, reason, user_id, username):

        record = InactiveRecord(
            applicator_id=applicator_id,
            applicator_code=applicator_code,
            reason=reason,
            marked_by=username,
            is_inactive=True
        )

        record_data = record.to_dict()
        record_data.pop('id', None)
        created = dm.create('inactive_applicators', record_data)

        return InactiveRecord.from_dict(created)

    @staticmethod
    def restore_active(applicator_id):

        records = dm.list('inactive_applicators', {'applicator_id': applicator_id})
        if records:
            last_record = records[-1]
            dm.update('inactive_applicators', last_record['id'],
                     {'is_inactive': False})
            return True
        return False

    @staticmethod
    def get_inactive_record(applicator_id):

        records = dm.list('inactive_applicators', {'applicator_id': applicator_id})
        if records:
            return InactiveRecord.from_dict(records[-1])
        return None

    @staticmethod
    def is_inactive(applicator_id):

        record = InactiveApplicatorService.get_inactive_record(applicator_id)
        return record and record.is_inactive

    @staticmethod
    def get_all_inactive():

        records = dm.list('inactive_applicators', {'is_inactive': True})
        return [InactiveRecord.from_dict(r) for r in records]

    @staticmethod
    def get_inactive_count():

        return dm.count('inactive_applicators', {'is_inactive': True})
