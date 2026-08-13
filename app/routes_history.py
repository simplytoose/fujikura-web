from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services.movement_service import MovementService, BlockingService
from datetime import datetime, timedelta

history_bp = Blueprint('history', __name__, url_prefix='/history')


@history_bp.route('/')
@login_required
def movement_history():

    if current_user.is_operator():
        flash('Операторам доступ до історії заборонено', 'warning')
        return redirect(url_for('dashboard.dashboard'))
    days_filter = request.args.get('days', '30', type=str)
    applicator_filter = request.args.get('applicator', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 20

    movements = MovementService.get_all_movements()

    if days_filter and days_filter != 'all':
        try:
            days = int(days_filter)
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            movements = [m for m in movements if datetime.fromisoformat(m.moved_at.replace('Z', '+00:00')) >= cutoff_date]
        except:
            pass

    if applicator_filter:
        movements = [m for m in movements if applicator_filter.lower() in m.applicator_code.lower()]

    movements = sorted(movements, key=lambda m: m.moved_at, reverse=True)

    total = len(movements)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_movements = movements[start:end]

    class Pagination:
        def __init__(self, page, per_page, total):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page

        @property
        def has_prev(self):
            return self.page > 1

        @property
        def has_next(self):
            return self.page < self.pages

        @property
        def prev_num(self):
            return self.page - 1 if self.has_prev else None

        @property
        def next_num(self):
            return self.page + 1 if self.has_next else None

    pagination = Pagination(page, per_page, total)

    return render_template('history/movement.html',
                         history=paginated_movements,
                         pagination=pagination,
                         days_filter=days_filter,
                         applicator_filter=applicator_filter)


@history_bp.route('/blocking')
@login_required
def blocking_history():

    if current_user.is_operator():
        flash('Операторам доступ до історії заборонено', 'warning')
        return redirect(url_for('dashboard.dashboard'))
    days_filter = request.args.get('days', '30', type=str)
    action_filter = request.args.get('action', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 20

    blocking_records = BlockingService.get_all_blocking_records()

    if days_filter and days_filter != 'all':
        try:
            days = int(days_filter)
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            blocking_records = [b for b in blocking_records if datetime.fromisoformat(b.created_at.replace('Z', '+00:00')) >= cutoff_date]
        except:
            pass

    if action_filter:
        if action_filter == 'blocked':
            blocking_records = [b for b in blocking_records if b.is_blocked]
        elif action_filter == 'unblocked':
            blocking_records = [b for b in blocking_records if not b.is_blocked]

    blocking_records = sorted(blocking_records, key=lambda b: b.created_at, reverse=True)

    total = len(blocking_records)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_records = blocking_records[start:end]

    class Pagination:
        def __init__(self, page, per_page, total):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page

        @property
        def has_prev(self):
            return self.page > 1

        @property
        def has_next(self):
            return self.page < self.pages

        @property
        def prev_num(self):
            return self.page - 1 if self.has_prev else None

        @property
        def next_num(self):
            return self.page + 1 if self.has_next else None

    pagination = Pagination(page, per_page, total)

    return render_template('history/blocking.html',
                         history=paginated_records,
                         pagination=pagination,
                         days_filter=days_filter,
                         action_filter=action_filter)
