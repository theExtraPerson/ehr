from flask import app, request, jsonify
from application.models.models import Patient
from application.services.patient_service import PatientService
from application.services.visit_service import VisitService


@app.route('/patients', methods=['POST'])
def register_patient():
    data = request.get_json()
    try:
        patient = PatientService.register_patient(data)
        return jsonify({
            'message': 'Patient registered successfully',
            'patient_id': patient.custom_id,
            'public_id': patient.public_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@app.route('patient/<int:patient_id>')
def get_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return {
        'id': patient_id,
        'full_name': patient.full_name,
        'gender': patient.gender,
        'address': patient.address,
        'email': patient.email
    }

@app.route('/drug/<int:drug_id>')
def get_drug(drug_id):
    drug = drug.qury.get_or_404(drug_id)
    return{
        'id': drug.id,
        'name': drug.name,
        'unit_prize': float(drug.unit_price)
    }

@app.route('/visits', methods=['POST'])
def create_visit():
    data = request.get_json()
    try:
        visit = VisitService.create_visit(
            data['patient_id'],  # custom_id
            data['doctor_id'],   # custom_id
            data['visit_type']
        )
        return jsonify({
            'message': 'Visit created successfully',
            'visit_id': visit.id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/visits/<int:visit_id>/triage', methods=['PUT'])
def update_triage(visit_id):
    data = request.get_json()
    try:
        triage = VisitService.update_triage(visit_id, data)
        return jsonify({
            'message': 'Triage updated successfully',
            'bmi': triage.bmi
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    