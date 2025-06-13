from flask import redirect, render_template, request, url_for, Blueprint, flash
from application.models.models import Visit, Patient, Triage, db
from application.services.visit_service import VisitService
from datetime import datetime

triage = Blueprint('triage', __name__, url_prefix='/triage')

@triage.route('/<string:patient_custom_id>', methods=['GET', 'POST'])
def manage_triage(patient_custom_id):
    # Get patient by custom ID
    patient = Patient.query.filter_by(custom_id=patient_custom_id).first_or_404()
    
    # Get active visit or create a new one if none exists
    active_visit = Visit.query.filter_by(
        patient_id=patient.id,
        status='in-progress'
    ).order_by(Visit.visit_date.desc()).first()

    if request.method == 'POST':
        try:
            # Process form data
            triage_data = {
                'height': float(request.form.get('height')) if request.form.get('height') else None,
                'weight': float(request.form.get('weight')) if request.form.get('weight') else None,
                'temperature': float(request.form.get('temperature')) if request.form.get('temperature') else None,
                'blood_pressure': request.form.get('blood_pressure'),
                'pulse': int(request.form.get('pulse')) if request.form.get('pulse') else None,
                'notes': request.form.get('notes')
            }

            # Update patient basic info if provided
            if request.form.get('phone'):
                patient.phone = request.form.get('phone')
            if request.form.get('address'):
                patient.address = request.form.get('address')
            
            # Create visit if none exists
            if not active_visit:
                active_visit = Visit(
                    patient_id=patient.id,
                    doctor_id=1,  # Default doctor or get from session
                    visit_date=datetime.utcnow(),
                    visit_type='Walk-in',
                    status='in-progress'
                )
                db.session.add(active_visit)
                db.session.commit()

            # Save triage data
            VisitService.update_triage(active_visit.id, triage_data)
            
            flash('Triage data saved successfully', 'success')
            return redirect(url_for('visit.generate_medical_form', visit_id=active_visit.id))
            
        except ValueError as e:
            db.session.rollback()
            flash(f'Invalid data: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash('Error saving triage data', 'danger')

    # Get existing triage data if available
    triage_data = {}
    if active_visit and active_visit.triage:
        triage_data = {
            'height': active_visit.triage.height,
            'weight': active_visit.triage.weight,
            'temperature': active_visit.triage.temperature,
            'blood_pressure': active_visit.triage.blood_pressure,
            'pulse': active_visit.triage.pulse,
            'notes': active_visit.triage.notes
        }

    return render_template(
        'ehr/triage_form.html',
        patient=patient,
        triage_data=triage_data,
        visit=active_visit
    )
