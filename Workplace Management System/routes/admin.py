from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Team, WorkStatus, ParkingBooking
from forms import CreateUserForm, EditUserForm, TeamForm

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def executive_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_executive:
            flash('Executive access required.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


def leader_or_exec(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or (
            not current_user.is_executive and not current_user.is_team_leader
        ):
            flash('Access denied.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated

