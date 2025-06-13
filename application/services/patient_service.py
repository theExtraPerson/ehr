from application.models.models import Patient, db
from datetime import datetime

class PatientService:
    @staticmethod
    def register_patient(patient_data):
        """Register a new patient with custom ID"""
        patient = Patient(
            custom_id=Patient.generate_custom_id(),
            first_name=patient_data['first_name'],
            last_name=patient_data['last_name'],
            age=patient_data['age'],
            gender=patient_data['gender'],
            phone=patient_data['phone'],
            email=patient_data.get('email'),
            address=patient_data.get('address')
        )
        db.session.add(patient)
        db.session.commit()
        return patient