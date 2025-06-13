from application.models.models import Patient, Doctor, Visit, Triage, db


class VisitService:
    @staticmethod
    def create_visit(patient_custom_id, doctor_custom_id, visit_type):
        """Create a new visit using custom IDs"""
        patient = Patient.query.filter_by(custom_id=patient_custom_id).first_or_404()
        doctor = Doctor.query.filter_by(custom_id=doctor_custom_id).first_or_404()
        
        visit = Visit(
            patient_id=patient.id,
            doctor_id=doctor.id,
            visit_type=visit_type
        )
        db.session.add(visit)
        db.session.commit()
        return visit

    @staticmethod
    def update_triage(visit_id, triage_data):
        """Update or create triage record for a visit"""
        visit = Visit.query.get_or_404(visit_id)
        
        if visit.triage:
            # Update existing triage
            triage = visit.triage
            triage.height = triage_data.get('height', triage.height)
            triage.weight = triage_data.get('weight', triage.weight)
            triage.temperature = triage_data.get('temperature', triage.temperature)
            triage.blood_pressure = triage_data.get('blood_pressure', triage.blood_pressure)
            triage.pulse = triage_data.get('pulse', triage.pulse)
            triage.notes = triage_data.get('notes', triage.notes)
        else:
            # Create new triage
            triage = Triage(
                visit_id=visit.id,
                height=triage_data.get('height'),
                weight=triage_data.get('weight'),
                temperature=triage_data.get('temperature'),
                blood_pressure=triage_data.get('blood_pressure'),
                pulse=triage_data.get('pulse'),
                notes=triage_data.get('notes')
            )
            db.session.add(triage)
        
        db.session.commit()
        return triage