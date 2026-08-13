from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from config import config
from models import User
from services.user_service import UserService
from data_manager import DataManager
import os


def create_app(config_name=None):

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config[config_name])

    csrf = CSRFProtect(app)

    dm = DataManager(app.config['DATA_DIR'])

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Будь ласка, увійдіть до системи'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return UserService.get_user_by_id(int(user_id))

    auth_bp = create_auth_blueprint()
    dashboard_bp = create_dashboard_blueprint()
    applicators_bp = create_applicators_blueprint()
    locations_bp = create_locations_blueprint()
    machines_bp = create_machines_blueprint()
    history_bp = create_history_blueprint()
    admin_bp = create_admin_blueprint()
    applicator_room_bp = create_applicator_room_blueprint()
    service_area_bp = create_service_area_blueprint()
    production_bp = create_production_blueprint()
    management_bp = create_management_blueprint()
    maintenance_bp = create_maintenance_blueprint()

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(applicators_bp)
    app.register_blueprint(locations_bp)
    app.register_blueprint(machines_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(applicator_room_bp)
    app.register_blueprint(service_area_bp)
    app.register_blueprint(production_bp)
    app.register_blueprint(management_bp)
    app.register_blueprint(maintenance_bp)

    @app.context_processor
    def inject_user():
        is_operator = False
        try:
            is_operator = current_user.is_authenticated and (
                getattr(current_user, 'is_operator', lambda: False)() or
                getattr(current_user, 'role', None) == 'operator' or
                getattr(current_user, 'role', None) == 'Operator'
            )
        except Exception:
            is_operator = False
        return {'current_user': current_user, 'is_operator': is_operator}

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.dashboard'))
        return redirect(url_for('auth.login'))

    return app


def create_auth_blueprint():
    from routes_auth import auth_bp
    return auth_bp


def create_dashboard_blueprint():
    from routes_dashboard import dashboard_bp
    return dashboard_bp


def create_applicators_blueprint():
    from routes_applicators import applicators_bp
    return applicators_bp


def create_locations_blueprint():
    from routes_locations import locations_bp
    return locations_bp


def create_machines_blueprint():
    from routes_machines import machines_bp
    return machines_bp


def create_history_blueprint():
    from routes_history import history_bp
    return history_bp


def create_admin_blueprint():
    from routes_admin import admin_bp
    return admin_bp


def create_applicator_room_blueprint():
    from routes_applicator_room import applicator_room_bp
    return applicator_room_bp


def create_service_area_blueprint():
    from routes_service_area import service_area_bp
    return service_area_bp


def create_production_blueprint():
    from routes_production import production_bp
    return production_bp


def create_management_blueprint():
    from routes_management import management_bp
    return management_bp

def create_maintenance_blueprint():
    from routes_maintenance import maintenance_bp
    return maintenance_bp

