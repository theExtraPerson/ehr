from flask import Blueprint, redirect, url_for
from application.models.models import Patient, Visit

main = Blueprint('main', __name__, url_prefix='/main')


@main.route('/patient-journey/<patient_id>')
def patient_journey(patient_id):
    """Central hub for patient's clinical journey"""
    patient = Patient.query.filter_by(patient_id=patient_id).first_or_404()
    active_visit = Visit.query.filter_by(patient_id=patient.id, status='in-progress').first()
    
    if not active_visit:
        return redirect(url_for('admin.create_view', url='/admin/visit', patient_id=patient.id))
    
    if not active_visit.triage:
        return redirect(url_for('admin.create_view', url='/admin/triage', visit_id=active_visit.id))
    
    if not active_visit.prescriptions:
        return redirect(url_for('admin.create_view', url='/admin/prescription', visit_id=active_visit.id))
    
    if not active_visit.invoice:
        return redirect(url_for('admin.create_view', url='/admin/invoice', visit_id=active_visit.id))
    
    return redirect(url_for('admin.index'))
