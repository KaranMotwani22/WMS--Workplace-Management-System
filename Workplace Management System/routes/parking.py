from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, WorkStatus, ParkingBooking, ParkingClaim, Notification
from forms import ParkingBookingForm
from config import Config
from datetime import date, timedelta

parking_bp = Blueprint('parking', __name__, url_prefix='/parking')

TOTAL_SPOTS = Config.PARKING_SPOTS_TOTAL

def _can_manage_booking(booking):
    """Return True if current_user is allowed to release/manage this booking."""
    if booking.user_id == current_user.id:
        return True
    if current_user.is_executive:
        return True
    if (current_user.is_team_leader
            and current_user.team_id is not None
            and booking.user.team_id == current_user.team_id):
        return True
    return False


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


@parking_bp.route('/release/<int:booking_id>', methods=['POST'])
@login_required
def release(booking_id):
    booking = ParkingBooking.query.get_or_404(booking_id)

    if not _can_manage_booking(booking):
        flash('Not authorized. You can only release spots for members of your own team.', 'danger')
        return redirect(url_for('parking.index'))

    if booking.status != 'active':
        flash('Booking is not active.', 'warning')
        return redirect(url_for('parking.index'))

    booking.status = 'released'
    booking.released_by_id = current_user.id

    # Notify all users with office status that day (except original owner)
    office_users = db.session.query(WorkStatus.user_id).filter(
        WorkStatus.date == booking.date,
        WorkStatus.status == 'office',
        WorkStatus.user_id != booking.user_id
    ).all()

    for (uid,) in office_users:
        has_parking = ParkingBooking.query.filter_by(
            user_id=uid, date=booking.date, status='active'
        ).first()
        if not has_parking:
            _notify(
                uid,
                f'A parking spot (Spot {booking.spot_number}) was released for {booking.date}. You can claim it!',
                'parking_released',
                booking.id
            )

    db.session.commit()
    flash('Parking spot released. Others have been notified.', 'success')
    return redirect(url_for('parking.index'))

@parking_bp.route('/claim/<int:booking_id>', methods=['POST'])
@login_required
def claim(booking_id):
    booking = ParkingBooking.query.get_or_404(booking_id)

    if booking.status != 'released':
        flash('Spot is no longer available.', 'warning')
        return redirect(url_for('parking.index'))

    if booking.date < date.today():
        flash('Cannot claim past bookings.', 'warning')
        return redirect(url_for('parking.index'))

    # Check office status
    ws = WorkStatus.query.filter_by(
        user_id=current_user.id, date=booking.date
    ).first()
    if not ws or ws.status != 'office':
        flash('You must have Office status to claim a parking spot.', 'warning')
        return redirect(url_for('parking.index'))

    # Block claim if user already has an active booking that day
    has_booking = ParkingBooking.query.filter(
        ParkingBooking.user_id == current_user.id,
        ParkingBooking.date == booking.date,
        ParkingBooking.status == 'active'
    ).first()
    if has_booking:
        flash(f'You already have Spot {has_booking.spot_number} booked for that day.', 'warning')
        return redirect(url_for('parking.index'))

    # No duplicate claim
    already = ParkingClaim.query.filter_by(
        booking_id=booking.id, user_id=current_user.id, status='pending'
    ).first()
    if already:
        flash('You already submitted a claim for this spot.', 'info')
        return redirect(url_for('parking.index'))

    clm = ParkingClaim(
        booking_id=booking.id,
        user_id=current_user.id,
        status='pending'
    )
    db.session.add(clm)

    # Notify only the team leader of the claimant's team
    if current_user.team_id:
        leaders = User.query.filter_by(
            role='team_leader', team_id=current_user.team_id, is_active=True
        ).all()
    else:
        leaders = User.query.filter_by(role='team_leader', is_active=True).all()

    for leader in leaders:
        _notify(
            leader.id,
            f'{current_user.full_name} claimed Spot {booking.spot_number} for {booking.date}. Awaiting approval.',
            'info'
        )

    db.session.commit()
    flash('Claim submitted. Awaiting team leader approval.', 'success')
    return redirect(url_for('parking.index'))


@parking_bp.route('/claim/review/<int:claim_id>/<action>', methods=['POST'])
@login_required
def review_claim(claim_id, action):
    clm = ParkingClaim.query.get_or_404(claim_id)

    # Executive can review any claim
    # Team leader can only review claims from their own team members
    if current_user.is_executive:
        pass
    elif current_user.is_team_leader and current_user.team_id:
        claimant = User.query.get(clm.user_id)
        if claimant.team_id != current_user.team_id:
            flash('Not authorized. You can only review claims from your own team.', 'danger')
            return redirect(url_for('parking.index'))
    else:
        flash('Not authorized.', 'danger')
        return redirect(url_for('parking.index'))

    if clm.status != 'pending':
        flash('Claim already reviewed.', 'info')
        return redirect(url_for('parking.index'))

    if action == 'approve':
        booking = clm.booking
        # Guard: claimant must not already have an active booking that day
        existing = ParkingBooking.query.filter(
            ParkingBooking.user_id == clm.user_id,
            ParkingBooking.date == booking.date,
            ParkingBooking.status == 'active',
            ParkingBooking.id != booking.id
        ).first()
        if existing:
            clm.status = 'rejected'
            clm.reviewed_by_id = current_user.id
            _notify(clm.user_id,
                    f'Your claim for Spot {booking.spot_number} on {booking.date} could not be approved — you already have Spot {existing.spot_number} that day.',
                    'claim_rejected')
            db.session.commit()
            flash('Cannot approve — claimant already has an active booking that day.', 'warning')
            return redirect(url_for('parking.index'))

        clm.status = 'approved'
        clm.reviewed_by_id = current_user.id
        booking = clm.booking
        booking.user_id = clm.user_id
        booking.status = 'active'
        booking.released_by_id = None
        # Reject other pending claims for same booking
        others = ParkingClaim.query.filter(
            ParkingClaim.booking_id == booking.id,
            ParkingClaim.id != clm.id,
            ParkingClaim.status == 'pending'
        ).all()
        for o in others:
            o.status = 'rejected'
            o.reviewed_by_id = current_user.id
            _notify(o.user_id, f'Your claim for Spot {booking.spot_number} on {booking.date} was not approved.', 'claim_rejected')

        _notify(clm.user_id, f'Your claim for Spot {booking.spot_number} on {booking.date} was approved!', 'claim_approved', booking.id)
        flash('Claim approved.', 'success')

    elif action == 'reject':
        clm.status = 'rejected'
        clm.reviewed_by_id = current_user.id
        booking = clm.booking
        _notify(clm.user_id, f'Your claim for Spot {booking.spot_number} on {booking.date} was rejected.', 'claim_rejected')
        flash('Claim rejected.', 'info')
    else:
        flash('Invalid action.', 'danger')

    db.session.commit()
    return redirect(url_for('parking.index'))

def _notify(user_id, message, ntype='info', booking_id=None):
    n = Notification(
        user_id=user_id,
        message=message,
        type=ntype,
        related_booking_id=booking_id
    )
    db.session.add(n)


@parking_bp.route('/')
@login_required
def index():
    today = date.today()
    form = ParkingBookingForm()

    # My upcoming bookings
    my_bookings = ParkingBooking.query.filter(
        ParkingBooking.user_id == current_user.id,
        ParkingBooking.date >= today,
        ParkingBooking.status == 'active'
    ).order_by(ParkingBooking.date).all()

    # Released spots available to claim
    released = ParkingBooking.query.filter(
        ParkingBooking.date >= today,
        ParkingBooking.status == 'released'
    ).order_by(ParkingBooking.date).all()

    # Team bookings: team leader sees active bookings of their own team
    # so they can release on behalf of a member
    team_bookings = []
    if current_user.is_team_leader and current_user.team_id:
        team_member_ids = [
            u.id for u in User.query.filter_by(
                team_id=current_user.team_id, is_active=True
            ).all()
            if u.id != current_user.id
        ]
        if team_member_ids:
            team_bookings = ParkingBooking.query.filter(
                ParkingBooking.user_id.in_(team_member_ids),
                ParkingBooking.date >= today,
                ParkingBooking.status == 'active'
            ).order_by(ParkingBooking.date).all()

    # Pending claims:
    # - Executive sees all
    # - Team leader sees only claims by their own team members
    # - Operator sees only their own
    if current_user.is_executive:
        pending_claims = ParkingClaim.query.filter_by(status='pending').all()
    elif current_user.is_team_leader and current_user.team_id:
        team_member_ids = [
            u.id for u in User.query.filter_by(
                team_id=current_user.team_id, is_active=True
            ).all()
        ]
        pending_claims = ParkingClaim.query.filter(
            ParkingClaim.status == 'pending',
            ParkingClaim.user_id.in_(team_member_ids)
        ).all()
    else:
        pending_claims = ParkingClaim.query.filter_by(
            user_id=current_user.id, status='pending'
        ).all()

    return render_template(
        'parking/index.html',
        form=form,
        my_bookings=my_bookings,
        team_bookings=team_bookings,
        released=released,
        pending_claims=pending_claims,
        today=today,
        timedelta=timedelta,
        total_spots=TOTAL_SPOTS
    )
