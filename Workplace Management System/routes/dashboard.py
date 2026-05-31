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
