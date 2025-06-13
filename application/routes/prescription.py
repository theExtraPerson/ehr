from flask import Blueprint, redirect, url_for
from application.extensions import db


prescription = Blueprint('prescription', __name__, url_prefix='/prescribe')
                                                                                                                     
@prescription.route('/prescribe/<int:visit_id>', methods=['GET', 'POST'])
def prescribe(visit_id):
    # On POST, create Prescription entries and update drug stock
    return redirect(url_for('billing.generate_invoice', visit_id=visit_id))
