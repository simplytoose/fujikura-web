import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import threading

class DataManager:


    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir
        self.lock = threading.Lock()
        self._ensure_directory()

    def _ensure_directory(self):

        os.makedirs(self.data_dir, exist_ok=True)

    def _get_file_path(self, table: str) -> str:

        return os.path.join(self.data_dir, f'{table}.json')

    def load_file(self, table: str) -> Dict[str, Any]:

        file_path = self._get_file_path(table)
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading {table}.json: {e}")
        return {}

    def save_file(self, table: str, data: Dict[str, Any]):

        with self.lock:
            file_path = self._get_file_path(table)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Error saving {table}.json: {e}")

    def _get_next_id(self, table: str) -> int:

        settings = self.load_file('settings')
        id_key = f'last_{table}_id'
        next_id = settings.get(id_key, 0) + 1
        settings[id_key] = next_id
        self.save_file('settings', settings)
        return next_id

    def create(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:

        file_data = self.load_file(table)

        if not isinstance(file_data, dict):
            file_data = {'records': []}

        if 'records' not in file_data:
            file_data['records'] = []

        record = {
            'id': self._get_next_id(table),
            **data,
            'created_at': datetime.utcnow().isoformat() if 'created_at' not in data else data['created_at']
        }

        file_data['records'].append(record)
        self.save_file(table, file_data)
        return record

    def read(self, table: str, record_id: int) -> Optional[Dict[str, Any]]:

        file_data = self.load_file(table)

        if not isinstance(file_data, dict) or 'records' not in file_data:
            return None

        for record in file_data.get('records', []):
            if record.get('id') == record_id:
                return record

        return None

    def update(self, table: str, record_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:

        file_data = self.load_file(table)

        if not isinstance(file_data, dict) or 'records' not in file_data:
            return None

        for i, record in enumerate(file_data.get('records', [])):
            if record.get('id') == record_id:
                record.update(data)
                record['updated_at'] = datetime.utcnow().isoformat()
                self.save_file(table, file_data)
                return record

        return None

    def delete(self, table: str, record_id: int) -> bool:

        file_data = self.load_file(table)

        if not isinstance(file_data, dict) or 'records' not in file_data:
            return False

        for i, record in enumerate(file_data.get('records', [])):
            if record.get('id') == record_id:
                del file_data['records'][i]
                self.save_file(table, file_data)
                return True

        return False

    def list(self, table: str, filters: Optional[Dict[str, Any]] = None,
             sort_by: str = 'id', sort_desc: bool = False) -> List[Dict[str, Any]]:

        file_data = self.load_file(table)

        if not isinstance(file_data, dict) or 'records' not in file_data:
            return []

        records = file_data.get('records', [])

        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    records = [r for r in records if r.get(key) in value]
                else:
                    records = [r for r in records if r.get(key) == value]

        if sort_by:
            records = sorted(records, key=lambda r: (r.get(sort_by) is not None, r.get(sort_by, '')),
                           reverse=sort_desc)

        return records

    def search(self, table: str, field: str, query: str) -> List[Dict[str, Any]]:

        file_data = self.load_file(table)

        if not isinstance(file_data, dict) or 'records' not in file_data:
            return []

        query_lower = query.lower()
        results = []

        for record in file_data.get('records', []):
            value = str(record.get(field, '')).lower()
            if query_lower in value:
                results.append(record)

        return results

    def count(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:

        return len(self.list(table, filters))

    def cleanup_old_records(self, table: str, days: int, date_field: str = 'created_at') -> int:

        file_data = self.load_file(table)

        if not isinstance(file_data, dict) or 'records' not in file_data:
            return 0

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        initial_count = len(file_data['records'])

        filtered_records = []
        for record in file_data['records']:
            try:
                record_date = datetime.fromisoformat(record.get(date_field, '').replace('Z', '+00:00'))
                if record_date > cutoff_date:
                    filtered_records.append(record)
            except:
                filtered_records.append(record)

        file_data['records'] = filtered_records
        self.save_file(table, file_data)

        return initial_count - len(filtered_records)

    def exists(self, table: str, record_id: int) -> bool:

        return self.read(table, record_id) is not None

    def find_by_field(self, table: str, field: str, value: Any) -> Optional[Dict[str, Any]]:

        records = self.list(table, {field: value})
        return records[0] if records else None

    def find_all_by_field(self, table: str, field: str, value: Any) -> List[Dict[str, Any]]:

        return self.list(table, {field: value})

    def get_all(self, table: str) -> List[Dict[str, Any]]:

        return self.list(table)


dm = DataManager()

