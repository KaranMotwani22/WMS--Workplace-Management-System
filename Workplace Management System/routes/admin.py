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


@admin_bp.route('/')
@login_required
@leader_or_exec
def index():
    users = User.query.order_by(User.team_id, User.last_name).all()
    teams = Team.query.order_by(Team.name).all()
    return render_template('admin/index.html', users=users, teams=teams)


# ── Users ──────────────────────────────────────────────────────────────────────

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@executive_required
def create_user():
    form = CreateUserForm()
    teams = Team.query.order_by(Team.name).all()
    form.team_id.choices = [(0, '— No Team —')] + [(t.id, t.name) for t in teams]
    if form.validate_on_submit():
        user = User(
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            email=form.email.data.lower().strip(),
            role=form.role.data,
            team_id=form.team_id.data if form.team_id.data != 0 else None
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.full_name} created.', 'success')
        return redirect(url_for('admin.index'))
    return render_template('admin/create_user.html', form=form)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@executive_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    teams = Team.query.order_by(Team.name).all()
    form.team_id.choices = [(0, '— No Team —')] + [(t.id, t.name) for t in teams]
    if form.validate_on_submit():
        user.first_name = form.first_name.data.strip()
        user.last_name = form.last_name.data.strip()
        user.role = form.role.data
        user.team_id = form.team_id.data if form.team_id.data != 0 else None
        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('admin.index'))
    if user.team_id:
        form.team_id.data = user.team_id
    return render_template('admin/edit_user.html', form=form, user=user)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@executive_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot deactivate yourself.', 'warning')
        return redirect(url_for('admin.index'))
    user.is_active = not user.is_active
    db.session.commit()
    state = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.full_name} {state}.', 'success')
    return redirect(url_for('admin.index'))


# ── Teams ──────────────────────────────────────────────────────────────────────

@admin_bp.route('/teams/create', methods=['GET', 'POST'])
@login_required
@executive_required
def create_team():
    form = TeamForm()
    if form.validate_on_submit():
        team = Team(name=form.name.data.strip())
        db.session.add(team)
        db.session.commit()
        flash(f'Team "{team.name}" created.', 'success')
        return redirect(url_for('admin.index'))
    return render_template('admin/create_team.html', form=form)


@admin_bp.route('/teams/<int:team_id>/edit', methods=['GET', 'POST'])
@login_required
@executive_required
def edit_team(team_id):
    team = Team.query.get_or_404(team_id)
    form = TeamForm(obj=team)
    if form.validate_on_submit():
        team.name = form.name.data.strip()
        db.session.commit()
        flash('Team updated.', 'success')
        return redirect(url_for('admin.index'))
    return render_template('admin/edit_team.html', form=form, team=team)


