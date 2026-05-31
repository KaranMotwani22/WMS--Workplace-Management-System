from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship('User', foreign_keys='User.team_id', back_populates='team')
    leader = db.relationship('User', foreign_keys='User.team_id',
                             primaryjoin='and_(User.team_id==Team.id, User.role=="team_leader")',
                             viewonly=True, uselist=False)

    def __repr__(self):
        return f'<Team {self.name}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='operator')
    # roles: 'executive', 'team_leader', 'operator'
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    team = db.relationship('Team', foreign_keys=[team_id], back_populates='members')
    work_statuses = db.relationship('WorkStatus', back_populates='user', lazy='dynamic')
    parking_bookings = db.relationship('ParkingBooking', back_populates='user', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic')
    claims = db.relationship('ParkingClaim', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def is_executive(self):
        return self.role == 'executive'

    @property
    def is_team_leader(self):
        return self.role == 'team_leader'

    def __repr__(self):
        return f'<User {self.email}>'


class WorkStatus(db.Model):
    __tablename__ = 'work_statuses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    # statuses: 'office', 'remote', 'pto'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='work_statuses')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='uq_user_date_status'),
    )

    def __repr__(self):
        return f'<WorkStatus {self.user_id} {self.date} {self.status}>'


class ParkingBooking(db.Model):
    __tablename__ = 'parking_bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    spot_number = db.Column(db.Integer, nullable=False)  # 1-4
    status = db.Column(db.String(20), nullable=False, default='active')
    # statuses: 'active', 'released', 'cancelled'
    released_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    released_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], back_populates='parking_bookings')
    released_by = db.relationship('User', foreign_keys=[released_by_id])
    claims = db.relationship('ParkingClaim', back_populates='booking', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='uq_user_date_parking'),
        db.UniqueConstraint('spot_number', 'date', 'status',
                            name='uq_spot_date_active'),
    )

    def __repr__(self):
        return f'<ParkingBooking spot={self.spot_number} date={self.date} user={self.user_id}>'


class ParkingClaim(db.Model):
    __tablename__ = 'parking_claims'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('parking_bookings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    # statuses: 'pending', 'approved', 'rejected'
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    booking = db.relationship('ParkingBooking', back_populates='claims')
    user = db.relationship('User', foreign_keys=[user_id], back_populates='claims')
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(50), nullable=False, default='info')
    # types: 'info', 'parking_released', 'claim_approved', 'claim_rejected'
    is_read = db.Column(db.Boolean, default=False)
    related_booking_id = db.Column(db.Integer, db.ForeignKey('parking_bookings.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='notifications')
    related_booking = db.relationship('ParkingBooking')

    def __repr__(self):
        return f'<Notification {self.user_id} {self.type}>'
