from datetime import date, timedelta
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, User, WorkStatus, ParkingBooking, Notification

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/week-statuses')
@login_required
def week_statuses():
    """Return all user statuses for a given week (AJAX for calendar navigation)."""
    week_offset = request.args.get('offset', 0, type=int)
    today = date.today()
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    week_dates = [week_start + timedelta(days=i) for i in range(7)]

    statuses = WorkStatus.query.filter(
        WorkStatus.date >= week_start,
        WorkStatus.date <= week_dates[-1]
    ).all()

    data = {}
    for s in statuses:
        data.setdefault(s.user_id, {})[s.date.isoformat()] = s.status

    users = User.query.filter_by(is_active=True).order_by(User.last_name).all()
    users_data = [{'id': u.id, 'name': u.full_name, 'team': u.team.name if u.team else ''} for u in users]

    return jsonify({
        'week_dates': [d.isoformat() for d in week_dates],
        'users': users_data,
        'statuses': data
    })


@api_bp.route('/parking/availability')
@login_required
def parking_availability():
    """Return available spots for a given date."""
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'date required'}), 400
    try:
        chosen = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'invalid date'}), 400

    from config import Config
    total = Config.PARKING_SPOTS_TOTAL
    booked = db.session.query(ParkingBooking.spot_number).filter(
        ParkingBooking.date == chosen,
        ParkingBooking.status == 'active'
    ).all()
    booked_nums = [b[0] for b in booked]
    free = [s for s in range(1, total + 1) if s not in booked_nums]

    return jsonify({'date': date_str, 'available': free, 'booked': booked_nums, 'total': total})
