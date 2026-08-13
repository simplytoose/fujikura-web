from data_manager import dm
from models import MovementRecord, BlockingRecord
from datetime import datetime, timedelta


class MovementService:


    @staticmethod
    def record_movement(applicator_id, applicator_code, from_location, to_location,
                       from_machine=None, to_machine=None, user_id=None, username=None, comment=""):

        movement = MovementRecord(
            applicator_id=applicator_id,
            applicator_code=applicator_code,
            from_location=from_location,
            to_location=to_location,
            from_machine=from_machine,
            to_machine=to_machine,
            user_id=user_id,
            username=username,
            comment=comment
        )

        movement_data = movement.to_dict()
        movement_data.pop('id', None)
        created = dm.create('movements', movement_data)

        MovementService.cleanup_old_movements(days=30)

        return MovementRecord.from_dict(created)

    @staticmethod
    def get_movement(movement_id):

        data = dm.read('movements', movement_id)
        return MovementRecord.from_dict(data) if data else None

    @staticmethod
    def get_all_movements():

        movements_data = dm.get_all('movements')
        return [MovementRecord.from_dict(m) for m in movements_data]

    @staticmethod
    def get_movements_by_applicator(applicator_id):

        movements_data = dm.list('movements', {'applicator_id': applicator_id})
        return [MovementRecord.from_dict(m) for m in movements_data]

    @staticmethod
    def get_movements_by_user(user_id):

        movements_data = dm.list('movements', {'user_id': user_id})
        return [MovementRecord.from_dict(m) for m in movements_data]

    @staticmethod
    def get_movements_by_location(location):

        to_location = dm.list('movements', {'to_location': location})
        from_location = dm.list('movements', {'from_location': location})

        movements_data = to_location + from_location
        return [MovementRecord.from_dict(m) for m in movements_data]

    @staticmethod
    def get_movements_by_machine(machine_code):

        to_machine = dm.list('movements', {'to_machine': machine_code})
        from_machine = dm.list('movements', {'from_machine': machine_code})

        movements_data = to_machine + from_machine
        return [MovementRecord.from_dict(m) for m in movements_data]

    @staticmethod
    def cleanup_old_movements(days=30):

        deleted = dm.cleanup_old_records('movements', days, 'moved_at')
        return deleted

    @staticmethod
    def count_movements():

        return dm.count('movements')

    @staticmethod
    def search_movements(query):

        results = dm.search('movements', 'applicator_code', query)
        return [MovementRecord.from_dict(m) for m in results]

    @staticmethod
    def get_movements_statistics():

        movements = MovementService.get_all_movements()

        if not movements:
            return {
                'total': 0,
                'last_24_hours': 0,
                'last_7_days': 0,
                'last_30_days': 0
            }

        now = datetime.utcnow()
        last_24h = now - timedelta(days=1)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)

        count_24h = 0
        count_7d = 0
        count_30d = 0

        for movement in movements:
            try:
                movement_date = datetime.fromisoformat(movement.moved_at.replace('Z', '+00:00'))
                if movement_date > last_24h:
                    count_24h += 1
                if movement_date > last_7d:
                    count_7d += 1
                if movement_date > last_30d:
                    count_30d += 1
            except:
                pass

        return {
            'total': len(movements),
            'last_24_hours': count_24h,
            'last_7_days': count_7d,
            'last_30_days': count_30d
        }


class BlockingService:


    @staticmethod
    def record_blocking(applicator_id, applicator_code, user_id=None, username=None, reason=""):

        blocking = BlockingRecord(
            applicator_id=applicator_id,
            applicator_code=applicator_code,
            user_id=user_id,
            username=username,
            reason=reason,
            is_blocked=True
        )

        blocking_data = blocking.to_dict()
        blocking_data.pop('id', None)
        created = dm.create('blocking_history', blocking_data)

        return BlockingRecord.from_dict(created)

    @staticmethod
    def record_unblocking(applicator_id, applicator_code, user_id=None, username=None):

        blocking = BlockingRecord(
            applicator_id=applicator_id,
            applicator_code=applicator_code,
            user_id=user_id,
            username=username,
            is_blocked=False
        )

        blocking_data = blocking.to_dict()
        blocking_data.pop('id', None)
        created = dm.create('blocking_history', blocking_data)

        return BlockingRecord.from_dict(created)

    @staticmethod
    def get_blocking(blocking_id):

        data = dm.read('blocking_history', blocking_id)
        return BlockingRecord.from_dict(data) if data else None

    @staticmethod
    def get_all_blocking_records():

        blocking_data = dm.get_all('blocking_history')
        return [BlockingRecord.from_dict(b) for b in blocking_data]

    @staticmethod
    def get_blocking_history_for_applicator(applicator_id):

        blocking_data = dm.list('blocking_history', {'applicator_id': applicator_id})
        return [BlockingRecord.from_dict(b) for b in blocking_data]

    @staticmethod
    def get_blocking_by_user(user_id):

        blocking_data = dm.list('blocking_history', {'user_id': user_id})
        return [BlockingRecord.from_dict(b) for b in blocking_data]

    @staticmethod
    def count_blocking_records():

        return dm.count('blocking_history')

    @staticmethod
    def cleanup_old_blocking_records(days=30):

        deleted = dm.cleanup_old_records('blocking_history', days, 'created_at')
        return deleted
