from application.models.models import Doctor, db

class DoctorService:
    @staticmethod
    def register_doctor(doctor_data):
        """Register a new doctor with custom ID"""
        doctor = Doctor(
            custom_id=Doctor.generate_custom_id(),
            first_name=doctor_data['first_name'],
            last_name=doctor_data['last_name'],
            license_number=doctor_data['license_number'],
            specialty=doctor_data['specialty']
        )
        db.session.add(doctor)
        db.session.commit()
        return doctor