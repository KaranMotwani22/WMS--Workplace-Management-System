from datetime import date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, User, WorkStatus, ParkingBooking, Notification
from forms import WorkStatusForm

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    return redirect(url_for('dashboard.calendar'))

@dashboard_bp.route('/status/set', methods=['GET', 'POST'])
@login_required
def set_status():
    form = WorkStatusForm()
    today = date.today()

    if form.validate_on_submit():
        chosen_date = form.date.data
        if chosen_date < today:
            flash('Cannot set status for past dates.', 'warning')
            return redirect(url_for('dashboard.set_status'))

        existing = WorkStatus.query.filter_by(
            user_id=current_user.id, date=chosen_date
        ).first()

        if existing:
            existing.status = form.status.data
            flash('Status updated.', 'success')
        else:
            ws = WorkStatus(
                user_id=current_user.id,
                date=chosen_date,
                status=form.status.data
            )
            db.session.add(ws)
            flash('Status set.', 'success')

        db.session.commit()
        return redirect(url_for('dashboard.calendar'))

    return render_template('dashboard/set_status.html', form=form, today=today)

@dashboard_bp.route('/dashboard')
@login_required
def calendar():
    today = date.today()
    # Build week starting Monday
    week_start = today - timedelta(days=today.weekday())
    week_dates = [week_start + timedelta(days=i) for i in range(7)]

    # All users + their statuses for this week
    users = User.query.filter_by(is_active=True).order_by(User.team_id, User.last_name).all()
    statuses = WorkStatus.query.filter(
        WorkStatus.date >= week_start,
        WorkStatus.date <= week_dates[-1]
    ).all()

    # Build lookup: {user_id: {date: status}}
    status_map = {}
    for s in statuses:
        status_map.setdefault(s.user_id, {})[s.date] = s.status

    # Unread notifications count
    notif_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    return render_template(
        'dashboard/calendar.html',
        users=users,
        week_dates=week_dates,
        status_map=status_map,
        today=today,
        notif_count=notif_count
    )


