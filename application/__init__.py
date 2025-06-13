from flask import Flask
from flask_migrate import Migrate

import os

from application.admin import setup_admin
from application.routes.billing import billing
from application.routes.payment import payment
from application.routes.visit import visit
from application.routes.main import main
from application.routes.prescription import prescription
from application.routes.triage import triage
from application.extensions import db, migrate

def create_app():

    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    template_dir = os.path.join(basedir, 'templates')
    static_dir = os.path.join(basedir, 'application/static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    setup_admin(app)

    from application.models.models import Patient, Doctor, Visit, Triage, Prescription, Invoice, InvoiceItem

    app.register_blueprint(billing, name='billing.bp')
    app.register_blueprint(visit, name='visit_bp')
    app.register_blueprint(payment, name='payment_bp')
    app.register_blueprint(triage, name='triage_bp')
    app.register_blueprint(prescription, name='prescription_bp')
    app.register_blueprint(main, name='main_bp' )

    with app.app_context():
        db.create_all()
    
    return app