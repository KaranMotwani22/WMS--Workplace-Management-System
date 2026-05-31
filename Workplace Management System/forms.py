from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(1, 80)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(1, 80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('Email already registered.')

class WorkStatusForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('office', 'Working from Office'),
        ('remote', 'Remote'),
        ('pto', 'PTO / Paid Time Off')
    ])
    submit = SubmitField('Set Status')

class ParkingBookingForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Reserve Spot')

class CreateUserForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(1, 80)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(1, 80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[
        ('operator', 'Operator'),
        ('team_leader', 'Team Leader'),
        ('executive', 'Executive')
    ])
    team_id = SelectField('Team', coerce=int)
    submit = SubmitField('Create User')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('Email already registered.')


class EditUserForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(1, 80)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(1, 80)])
    role = SelectField('Role', choices=[
        ('operator', 'Operator'),
        ('team_leader', 'Team Leader'),
        ('executive', 'Executive')
    ])
    team_id = SelectField('Team', coerce=int)
    submit = SubmitField('Update User')

class TeamForm(FlaskForm):
    name = StringField('Team Name', validators=[DataRequired(), Length(1, 100)])
    submit = SubmitField('Save')
