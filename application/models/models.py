from datetime import datetime, date, timezone
import uuid
from sqlalchemy.orm import validates
from sqlalchemy import event, CheckConstraint, func, UniqueConstraint, text
from sqlalchemy.ext.hybrid import hybrid_property

from application.extensions import db

class BaseModel(db.Model):
    """Base model with common columns and methods"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

class Patient(BaseModel):
    """Patient information model with medical validation"""
    __tablename__ = 'patients'
    
    patient_id = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    gender_choices = [('male', 'Male'), ('female', 'Female')]
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    address = db.Column(db.String(255))
    blood_type = db.Column(db.String(10))
    allergies = db.Column(db.Text)
    
    # Relationships
    diagnoses = db.relationship('Diagnosis', back_populates='patient', cascade='all, delete-orphan')
    visits = db.relationship('Visit', back_populates='patient', cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', back_populates='patient', cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', back_populates='patient', cascade='all, delete-orphan')
    
    @hybrid_property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @full_name.expression
    def full_name(cls):
        return func.concat(cls.first_name, ' ', cls.last_name)
    
    @validates('gender')
    def validate_gender(self, key, gender):
        assert gender.lower() in ['male', 'female'], "Invalid gender"
        return gender.lower()
    

@event.listens_for(Patient, 'before_insert')
def generate_patient_id(mapper, connection, target):
    if not target.patient_id:
        month = datetime.now().month
        year = datetime.now().year
        result = connection.execute(
            text("SELECT patient_id FROM patients ORDER BY patient_id DESC LIMIT 1")
        ).fetchone()

        if result and result[0]:
            try:
                seq_num = int(result[0].split('-')[-1]) + 1
            except:
                seq_num = 1
        else:
            seq_num = 1
        target.patient_id = f"KMC-{month:02d}-{year}-{seq_num:04d}"
    
    
class Doctor(BaseModel):
    """Healthcare provider model"""
    __tablename__ = 'doctors'
    
    doctor_id = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    diagnoses = db.relationship('Diagnosis', back_populates='doctor')
    visits = db.relationship('Visit', back_populates='doctor')
    prescriptions = db.relationship('Prescription', back_populates='doctor')
    
    @hybrid_property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @full_name.expression
    def full_name(cls):
        return func.concat(cls.first_name, ' ', cls.last_name)
    
@event.listens_for(Doctor, 'before_insert')
def generate_doctor_id(mapper, connection, target):
    if not target.doctor_id:
        month = datetime.now().month
        year = datetime.now().year
        result = connection.execute(
            text("SELECT doctor_id FROM doctors ORDER BY doctor_id DESC LIMIT 1")
        ).fetchone()
        
        if result and result[0]:
            try:
                seq_num = int(result[0].split('-')[-1]) + 1
            except:
                seq_num = 1
        else:
            seq_num = 1
        target.doctor_id = f"KMC-DOC-{month:02d}-{year}-{seq_num:04d}"


class Visit(BaseModel):
    """Patient visit with triage data"""
    __tablename__ = 'visits'
    
    visit_id = db.Column(db.String(50), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    visit_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    visit_type = db.Column(db.String(50))  # Checkup, Emergency, Follow-up, etc.
    status = db.Column(db.String(20), default='completed')  # scheduled, in-progress, completed, cancelled
    
    # Relationships
    patient = db.relationship('Patient', back_populates='visits')
    doctor = db.relationship('Doctor', back_populates='visits')
    triage = db.relationship('Triage', back_populates='visit', uselist=False, cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', back_populates='visit', cascade='all, delete-orphan')
    diagnoses = db.relationship('Diagnosis', back_populates='visit', cascade='all, delete-orphan')
    invoice = db.relationship('Invoice', back_populates='visit', uselist=False, cascade='all, delete-orphan')
        
    @property
    def visit_reference(self):
        return f'Visit #{self.id} - {self.visit_date.strftime("%Y-%m-%d")}'

@event.listens_for(Visit, 'before_insert')
def generate_visit_id(mapper, connection, target):
    if not target.visit_id:
        month = datetime.now().month
        year = datetime.now().year
        result = connection.execute(
            text("SELECT visit_id FROM visits ORDER BY visit_id DESC LIMIT 1")
        ).scalar()
        
        if result:
            try:
                seq_num = int(result[0].split('/')[-1]) + 1
            except:
                seq_num = 1
        else:
            seq_num = 1
        target.visit_id = f"KMC-VIS-{month:02d}{year:02d}/{seq_num:04d}"
    

class VisitReport(BaseModel):
    __tablename__ = 'visit_reports'
    
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    visit_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
       
    # Medical Information
    presenting_complaint = db.Column(db.Text)
    history_complaint = db.Column(db.Text)
    medical_history = db.Column(db.Text)
    physical_examination = db.Column(db.Text)
    investigations = db.Column(db.Text)
    preliminary_diagnosis = db.Column(db.Text)
    final_diagnosis = db.Column(db.Text)
    management_plan = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    review_date = db.Column(db.Date)
    
    # Relationships
    patient = db.relationship('Patient', backref='visit_reports')
    doctor = db.relationship('Doctor', backref='visit_reports')
    
    def __repr__(self):
        return f'<VisitReport {self.id} for Patient {self.patient_id}>'

class Triage(BaseModel):
    """Medical triage data with validation"""
    __tablename__ = 'triage'
    
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=False)
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    temperature = db.Column(db.Float)  # in °C
    blood_pressure_systolic = db.Column(db.Integer)
    blood_pressure_diastolic = db.Column(db.Integer)
    pulse = db.Column(db.Integer)
    oxygen_saturation = db.Column(db.Integer)  # SpO2 percentage
    notes = db.Column(db.Text)
    
    # Relationships
    visit = db.relationship('Visit', back_populates='triage')
    
    @hybrid_property
    def bmi(self):
        if self.height and self.weight:
            return round(self.weight / ((self.height / 100) ** 2), 1)
        return None
    
    @bmi.expression
    def bmi(cls):
        return func.round(cls.weight / func.pow(cls.height / 100, 2), 1)

    
    @hybrid_property
    def blood_pressure(self):
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None
    
    @validates('temperature')
    def validate_temperature(self, key, temp):
        if temp is not None and (temp < 25 or temp > 45):  # Reasonable human range in °C
            raise ValueError("Invalid temperature reading")
        return temp
    
    @validates('pulse')
    def validate_pulse(self, key, pulse):
        if pulse is not None and (pulse < 30 or pulse > 200):  # Reasonable human range
            raise ValueError("Invalid pulse reading")
        return pulse
    
    @validates('blood_pressure_systolic', 'blood_pressure_diastolic')
    def validate_blood_pressure(self, key, value):
        if value is not None and (value < 40 or value > 250):
            raise ValueError(f"Invalid {key} reading")
        return value

class Diagnosis(BaseModel):
    """Medical diagnosis with ICD-10 support"""
    __tablename__ = 'diagnoses'
    
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    icd10_code = db.Column(db.String(10))
    condition = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    is_primary = db.Column(db.Boolean, default=False)
    
    # Relationships
    visit = db.relationship('Visit', back_populates='diagnoses')
    patient = db.relationship('Patient', back_populates='diagnoses')
    doctor = db.relationship('Doctor', back_populates='diagnoses')

class Drug(BaseModel):
    __tablename__ = 'drugs'

    name = db.Column(db.String(100), nullable=False, unique=True)
    vendor = db.Column(db.String(100))
    dosage_form = db.Column(db.String(50))
    strength = db.Column(db.String(50))
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    expiry_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship to PrescriptionDrug association table
    prescription_drugs = db.relationship(
        'PrescriptionDrug',
        back_populates='drug',
        cascade='all, delete-orphan'
    )

    invoice_items = db.relationship(
        'InvoiceItem',
        back_populates='drugs',
        cascade='all, delete-orphan'
    )

    @validates('stock')
    def validate_stock(self, key, stock):
        if stock < 0:
            raise ValueError("Stock cannot be negative")
        return stock

class Prescription(BaseModel):
    __tablename__ = 'prescriptions'

    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'))
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)

    dosage = db.Column(db.String(50))  # Optional, can be per drug in PrescriptionDrug
    frequency = db.Column(db.String(50))  # Optional, can be per drug in PrescriptionDrug
    quantity = db.Column(db.Integer)  # Optional, can be per drug in PrescriptionDrug
    duration_days = db.Column(db.Integer)
    start_date = db.Column(db.Date, default=date.today)
    end_date = db.Column(db.Date)
    instructions = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled

    # Relationships
    visit = db.relationship('Visit', back_populates='prescriptions')
    patient = db.relationship('Patient', back_populates='prescriptions')
    doctor = db.relationship('Doctor', back_populates='prescriptions')

    # Association to drugs via PrescriptionDrug
    prescription_drugs = db.relationship(
        'PrescriptionDrug',
        back_populates='prescriptions',
        cascade='all, delete-orphan'
    )

    invoice_items = db.relationship(
        'InvoiceItem',
        back_populates='prescriptions'
    )


    __table_args__ = (
        CheckConstraint("status IN ('active', 'completed', 'cancelled')", name='valid_prescription_status'),
        CheckConstraint("quantity IS NULL OR quantity > 0", name='positive_quantity_if_set'),
        UniqueConstraint("visit_id", name="unique_prescription"),
    )

    @hybrid_property
    def is_active(self):
        return self.status == 'active' and (self.end_date is None or self.end_date >= date.today())



class PrescriptionDrug(BaseModel):
    __tablename__ = 'prescription_drugs'

    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), primary_key=True)
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.id'), primary_key=True)

    dosage = db.Column(db.String(50), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    # Relationships
    prescriptions = db.relationship('Prescription', back_populates='prescription_drugs')
    drug = db.relationship('Drug', back_populates='prescription_drugs')

    @validates('quantity')
    def validate_quantity(self, key, quantity):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        return quantity



class Invoice(BaseModel):
    """Medical billing invoice"""
    __tablename__ = 'invoices'
    
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    invoice_date = db.Column(db.Date, default=date.today, nullable=False)
    due_date = db.Column(db.Date)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    professional_fee = db.Column(db.Numeric(10, 2), default=0)
    sundries = db.Column(db.Numeric(10, 2), default=0)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, partial, paid, cancelled
    notes = db.Column(db.Text)
    
    # Relationships
    visit = db.relationship('Visit', back_populates='invoice')
    patient = db.relationship('Patient', back_populates='invoices')
    invoice_items = db.relationship('InvoiceItem', back_populates='invoice', cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='invoice', cascade='all, delete-orphan')
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'partial', 'paid', 'cancelled')", name='valid_invoice_status'),
    )
    
    @hybrid_property
    def amount_paid(self):
        return sum(payment.amount for payment in self.payments) if self.payments else 0
    
    @hybrid_property
    def balance_due(self):
        return self.total_amount - self.amount_paid
    
    @validates('due_date')
    def validate_due_date(self, key, due_date):
        if due_date and due_date < self.invoice_date:
            raise ValueError("Due date cannot be before invoice date")
        return due_date

class InvoiceItem(BaseModel):
    """Line items for invoices"""
    __tablename__ = 'invoice_items'
    
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=True)
    item_type = db.Column(db.String(50), nullable=False)  # consultation, procedure, medication, etc.
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Relationships
    invoice = db.relationship('Invoice', back_populates='invoice_items')
    drugs = db.relationship('Drug', back_populates='invoice_items')
    prescriptions = db.relationship('Prescription', back_populates='invoice_items')
    
    __table_args__ = (
        CheckConstraint("quantity > 0", name='positive_item_quantity'),
    )
    
    @validates('unit_price')
    def validate_unit_price(self, key, price):
        assert price >= 0, "Price cannot be negative"
        return price

class Payment(BaseModel):
    """Payment transactions"""
    __tablename__ = 'payments'
    
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    payment_date = db.Column(db.Date, default=date.today, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # cash, credit, insurance, etc.
    transaction_reference = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    # Relationships
    invoice = db.relationship('Invoice', back_populates='payments')
    receipt = db.relationship('Receipt', back_populates='payment', uselist=False, cascade='all, delete-orphan')
    
    __table_args__ = (
        CheckConstraint("amount > 0", name='positive_payment_amount'),
    )

class Receipt(BaseModel):
    """Payment receipts"""
    __tablename__ = 'receipts'
    
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    receipt_date = db.Column(db.Date, default=date.today, nullable=False)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False)
    issued_by = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    
    # Relationships
    payment = db.relationship('Payment', back_populates='receipt')

# Event listeners for database operations
@event.listens_for(Prescription, 'after_insert')
def update_drug_stock(mapper, connection, target):
    """Reduce drug stock when prescription is created"""
    drug = Drug.query.get(target.drug_id)
    if drug:
        drug.stock -= target.quantity
        db.session.add(drug)

@event.listens_for(Prescription, 'after_delete')
def restore_drug_stock(mapper, connection, target):
    """Restore drug stock when prescription is deleted"""
    drug = Drug.query.get(target.drug_id)
    if drug:
        drug.stock += target.quantity
        db.session.add(drug)