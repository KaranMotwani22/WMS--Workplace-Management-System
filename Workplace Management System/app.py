from flask import Flask
from flask_login import LoginManager
from models import db, User
from config import Config

login_manager = LoginManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.parking import parking_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(parking_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
