import json
import os
import logging
from app.models import MaintenanceRecord

logger = logging.getLogger(__name__)

class MaintenanceService:
    DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'maintenance.json')

    @classmethod
    def get_all_records(cls):
        if not os.path.exists(cls.DATA_FILE):
            return []
        try:
            with open(cls.DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [MaintenanceRecord.from_dict(d) for d in data]
        except Exception as e:
            logger.error(f"Error loading maintenance records: {e}")
            return []

    @classmethod
    def save_all_records(cls, records):
        try:
            with open(cls.DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump([r.to_dict() for r in records], f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving maintenance records: {e}")
            return False

    @classmethod
    def get_records_by_applicator(cls, applicator_id):
        records = cls.get_all_records()
        return [r for r in records if r.applicator_id == applicator_id]

    @classmethod
    def record_maintenance(cls, applicator_id, applicator_code, replaced_parts, reason, technician_id, technician_name):
        records = cls.get_all_records()
        new_id = 1
        if records:
            new_id = max((r.id for r in records if isinstance(r.id, int)), default=0) + 1
            
        new_record = MaintenanceRecord(
            id=new_id,
            applicator_id=applicator_id,
            applicator_code=applicator_code,
            replaced_parts=replaced_parts,
            reason=reason,
            technician_id=technician_id,
            technician_name=technician_name
        )
        records.append(new_record)
        return cls.save_all_records(records)
