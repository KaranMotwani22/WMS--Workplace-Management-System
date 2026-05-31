from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, WorkStatus, ParkingBooking, ParkingClaim, Notification
from forms import ParkingBookingForm
from config import Config

parking_bp = Blueprint('parking', __name__, url_prefix='/parking')

TOTAL_SPOTS = Config.PARKING_SPOTS_TOTAL

@parking_bp.route('/book', methods=['POST'])
@login_required
def book():
    form = ParkingBookingForm()
    if not form.validate_on_submit():
        flash('Invalid form submission.', 'danger')
        return redirect(url_for('parking.index'))

    chosen_date = form.date.data
    today = date.today()

    if chosen_date < today:
        flash('Cannot book parking for past dates.', 'warning')
        return redirect(url_for('parking.index'))

    # Check user has office status on that day
    ws = WorkStatus.query.filter_by(
        user_id=current_user.id, date=chosen_date
    ).first()
    if not ws or ws.status != 'office':
        flash('You must set your status to "Office" before booking parking.', 'warning')
        return redirect(url_for('parking.index'))

    # Already booked?
    existing = ParkingBooking.query.filter_by(
        user_id=current_user.id, date=chosen_date, status='active'
    ).first()
    if existing:
        flash('You already have a parking spot for that date.', 'info')
        return redirect(url_for('parking.index'))

    # Find free spot
    booked_spots = db.session.query(ParkingBooking.spot_number).filter(
        ParkingBooking.date == chosen_date,
        ParkingBooking.status == 'active'
    ).all()
    booked_nums = {s[0] for s in booked_spots}
    free = [s for s in range(1, TOTAL_SPOTS + 1) if s not in booked_nums]

    if not free:
        flash('No parking spots available for that date.', 'warning')
        return redirect(url_for('parking.index'))

    booking = ParkingBooking(
        user_id=current_user.id,
        date=chosen_date,
        spot_number=free[0],
        status='active'
    )
    db.session.add(booking)
    db.session.commit()
    flash(f'Parking spot {free[0]} reserved for {chosen_date}.', 'success')
    return redirect(url_for('parking.index'))
