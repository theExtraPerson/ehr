from dataclasses import fields
from typing import Optional
from flask import Flask, make_response, render_template, request, redirect, url_for, flash
from flask_admin.model.form import InlineFormAdmin
from flask_login import current_user
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from flask_admin.form import rules
from sqlalchemy import func
from wtforms import DateField, DateTimeField, DecimalField, SelectField, TextAreaField, StringField
from wtforms.validators import DataRequired, NumberRange, ValidationError, Length, Email, Optional
from application.models.models import Invoice, VisitReport, db, Patient, Payment, Prescription, Visit, Drug, Triage, Doctor, InvoiceItem
from datetime import datetime, timedelta
import pdfkit

class KMCAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        # Example: Calculate monthly metrics for the last 6 months
        today = datetime.today()
        six_months_ago = today - timedelta(days=180)

        # Aggregate visits per month
        visits_per_month = (
            db.session.query(
                db.func.strftime('%Y-%m', Visit.visit_date).label('month'),
                db.func.count(Visit.id)
            )
            .filter(Visit.visit_date >= six_months_ago)
            .group_by('month')
            .order_by('month')
            .all()
        )

        # Aggregate prescriptions per month
        prescriptions_per_month = (
            db.session.query(
                db.func.strftime('%Y-%m', Prescription.start_date).label('month'),
                db.func.count(Prescription.id)
            )
            .filter(Prescription.start_date >= six_months_ago)
            .group_by('month')
            .order_by('month')
            .all()
        )

        # Aggregate invoices total per month
        invoices_per_month = (
            db.session.query(
                db.func.strftime('%Y-%m', Invoice.invoice_date).label('month'),
                db.func.sum(Invoice.total_amount).label('total_amount')
            )
            .filter(Invoice.invoice_date >= six_months_ago)
            .group_by('month')
            .order_by('month')
            .all()
        )

        # Total active patients
        active_patients_count = db.session.query(func.count(func.distinct(Visit.patient_id))).scalar()

        # Prepare data for charts (convert query results to dict or lists)
        def unpack_monthly_data(data, value_index=1):
            months = [row[0] for row in data]
            values = [row[value_index] for row in data]
            return months, values

        visits_months, visits_counts = unpack_monthly_data(visits_per_month)
        prescriptions_months, prescriptions_counts = unpack_monthly_data(prescriptions_per_month)
        invoices_months, invoices_totals = unpack_monthly_data(invoices_per_month, value_index=1)

        # Flash a welcome message
        flash("Welcome to the KMC EHR Admin Dashboard!", "info")

        # Render a custom dashboard template with metrics and charts
        return self.render(
            'admin/dashboard.html',
            visits_months=visits_months,
            visits_counts=visits_counts,
            prescriptions_months=prescriptions_months,
            prescriptions_counts=prescriptions_counts,
            invoices_months=invoices_months,
            invoices_totals=invoices_totals,
            active_patients_count=active_patients_count,
            side_panel_links=[
                {'name': 'Patients', 'url': '/admin/patient/'},
                {'name': 'Visits', 'url': '/admin/visit/'},
                {'name': 'Prescriptions', 'url': '/admin/prescription/'},
                {'name': 'Invoices', 'url': '/admin/invoice/'},
                {'name': 'Doctors', 'url': '/admin/doctor/'},
                {'name': 'Reports', 'url': '/admin/reports/'},
            ]
        )

class PatientAdminView(ModelView):
    column_list = ['patient_id', 'full_name', 'age', 'gender', 'phone', 'email', 'address']
    column_searchable_list = ['patient_id', 'first_name', 'last_name', 'phone']
    column_filters = ['gender', 'age']
    form_columns = ['first_name', 'last_name', 'age', 'gender', 'phone', 'email', 'address']
    form_args = {
        'gender': {
            'validators': [DataRequired()],
            'choices': [
                ('male', 'Male'),
                ('female', 'Female')
            ]
        }
    }
    form_overrides = {'gender': SelectField}
    form_widget_args ={
        'gender': {
            'style': 'width: 100px;'
        }
    }

    @action('start_visit', 'Start Visit', 'Start a new visit for selected patients?')
    def action_start_visit(self, ids):
        for patient_id in ids:
            patient = Patient.query.get(patient_id)
            visit = Visit(
                patient_id=patient.id,
                doctor_id=1,  # Default doctor
                visit_date=datetime.now(),
                visit_type='Walk-in',
                status='in-progress'
            )
            db.session.add(visit)
        db.session.commit()
        flash(f"{len(ids)} visit(s) started.", "success")

class DoctorAdminView(ModelView):
    # Basic configuration
    column_list = ['doctor_id', 'full_name', 'specialty', 'phone', 'is_active']
    column_searchable_list = ['doctor_id', 'first_name', 'last_name', 'license_number']
    column_filters = ['specialty', 'is_active']
    form_columns = [
        'first_name', 
        'last_name', 
        'license_number', 
        'specialty', 
        'phone', 
        'email', 
        'is_active'
    ]
    form_args = {
        'license_number': {
            'validators': [DataRequired(), Length(min=5, max=50)]
        },
        'email': {
            'validators': [Email(), Optional()]
        }
    }
    form_widget_args = {
        'phone': {
            'placeholder': 'Format: +25675678900'
        }
    }
    form_overrides = dict(specialty=SelectField)
    form_choices = {
        'specialty': [
            ('general', 'General Physician'),
            ('obs-gyn', 'Obs-Gynae Specialist'),
            ('ent', 'Ear, Nose and Throat Specialist'),
            ('pediatrics', 'Pediatrics'),
            ('surgery', 'Surgery')
        ]
    }
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.doctor_id = Doctor.generate_doctor_id()


class VisitAdminView(ModelView):
    column_list = ['id', 'patient', 'doctor', 'visit_date', 'visit_type', 'status']
    column_labels = {
        'patient': 'Patient Name',
        'doctor': 'Attending Doctor'
    }

    form_widget_args = {
        'visit_date': {
            'style': 'width: 100px;',
            'data-date-format': 'yyyy-mm-dd hh:ii:ss'
        }
    }

    column_formatters = {
        'patient': lambda v, c, m, p: m.patient.full_name if m.patient else '',
        'doctor': lambda v, c, m, p: m.doctor.full_name if m.doctor else ''
    }
    
    form_columns = ['patient', 'doctor', 'visit_date', 'visit_type', 'status']
    
    form_overrides = {
        'visit_date': DateTimeField,
        'visit_type': SelectField,
        'status': SelectField,
        'patient': SelectField,  
        'doctor': SelectField
    }

    form_args = {
        'visit_type': {
            'choices': [
                ('walk-in', 'Walk-in', True, {}),
                ('scheduled', 'Scheduled', False, {}),
                ('appointment', 'Appointment', False, {}),
                ('emergency', 'Emergency', False, {}),
                ('follow-up', 'Follow-up', False, {})
            ],
            'validators': [DataRequired()]
        },
        'status': {
            'choices': [
                ('scheduled', 'Scheduled', False, {}),
                ('in-progress', 'In Progress', True, {}),
                ('completed', 'Completed', False, {}),
                ('cancelled', 'Cancelled', False, {})
            ],
            'validators': [DataRequired()]
        },
        'visit_date': {
            'default': datetime.now(),
            'validators': [DataRequired()]
        }
    }

    def on_form_prefill(self, form, id):
        """Load dynamic choices when editing an existing record"""
        self._load_dynamic_choices(form)

    def create_form(self, obj=None):
        """Load dynamic choices when creating a new record"""
        form = super(VisitAdminView, self).create_form(obj)
        self._load_dynamic_choices(form)
        return form

    def _load_dynamic_choices(self, form):
        """Helper method to load patient and doctor choices"""
        from application.models.models import Patient, Doctor
        
        # Load patients
        patients = Patient.query.order_by(Patient.full_name).all()
        form.patient.choices = [(str(p.id), p.full_name) for p in patients]
        
        # Load active doctors
        doctors = Doctor.query.filter_by(is_active=True).order_by(Doctor.full_name).all()
        form.doctor.choices = [(str(d.id), d.full_name) for d in doctors]

    def on_model_change(self, form, model, is_created):
        """Handle post-create/update actions"""
        from application.models.models import Triage
        
        db.session.flush()

        if is_created and model.status == 'in-progress':
            triage = Triage(visit_id=model.id)
            db.session.add(triage)
            db.session.commit()

    def after_model_change(self, form, model, is_created):
        """Ensure changes are committed"""
        db.session.commit()


class VisitReportView(ModelView):
    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True

    # Field display options
    column_list = ['visit_date', 'patient', 'doctor', 'final_diagnosis']
    
    # Set editable form columns (no nested/related fields)
    form_columns = [
        'patient', 'visit_date',
        'presenting_complaint', 'history_complaint',
        'medical_history', 'physical_examination',
        'investigations', 'preliminary_diagnosis',
        'final_diagnosis', 'management_plan',
        'recommendations', 'review_date'
    ]

    # TextArea fields for better UX
    form_overrides = {
        'presenting_complaint': TextAreaField,
        'history_complaint': TextAreaField,
        'physical_examination': TextAreaField,
        'management_plan': TextAreaField
    }

    form_widget_args = {
        'presenting_complaint': {'rows': 3},
        'history_complaint': {'rows': 3},
        'physical_examination': {'rows': 5},
        'management_plan': {'rows': 5}
    }

    # Read-only field for displaying patient info
    form_extra_fields = {
        'patient_info': rules.HTML('')
    }

    # Custom form layout
    form_edit_rules = [
        rules.FieldSet(['patient', 'visit_date'], 'Visit Information'),
        'patient_info',  # Read-only section
        rules.FieldSet([
            'presenting_complaint', 'history_complaint',
            'physical_examination'
        ], 'Clinical Assessment'),
        rules.FieldSet([
            'investigations', 'preliminary_diagnosis', 'final_diagnosis'
        ], 'Diagnosis'),
        rules.FieldSet([
            'management_plan', 'recommendations', 'review_date'
        ], 'Treatment Plan')
    ]

    # Update patient info block on edit
    def on_form_prefill(self, form, id):
        report = VisitReport.query.get(id)
        if report and report.patient:
            form.patient_info = rules.HTML(
                f"""
                <div class="alert alert-info">
                    <strong>Patient Info:</strong><br>
                    <b>Name:</b> {report.patient.full_name}<br>
                    <b>Age:</b> {report.patient.age} years<br>
                    <b>Gender:</b> {report.patient.gender}<br>
                    <b>Address:</b> {report.patient.address}<br>
                    <b>Phone:</b> {report.patient.phone}
                </div>
                """
            )

    # Automatically assign doctor on create
    def on_model_change(self, form, model, is_created):
        if is_created and not model.doctor_id:
            model.doctor_id = current_user.id

    # Add print icon in list view
    column_extra_row_actions = [{
        'label': 'Print',
        'url': lambda view, context, model, name: url_for('.print_report', report_id=model.id),
        'icon_class': 'glyphicon glyphicon-print'
    }]

    # Templates (if needed for customization)
    list_template = 'reports/visit_report_list.html'
    edit_template = 'reports/visit_report_edit.html'

    # PDF Print Route
    @expose('/print/<int:report_id>')
    def print_report(self, report_id):
        report = VisitReport.query.get_or_404(report_id)
        rendered = render_template('admin/visit_report_print.html', report=report)
        pdf = pdfkit.from_string(rendered, False)

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=report_{report_id}.pdf'
        return response

class PrescriptionAdminView(ModelView):
    column_list = ['id', 'visit', 'dosage', 'frequency', 'start_date']
    form_columns = ['visit', 'dosage', 'frequency', 'quantity', 'status', 'start_date', 'end_date']
    form_args = {
        'status': {
            'validators': [DataRequired()],
            'choices': [
                ('active', 'Active', True, {}),
                ('completed', 'Completed', False, {}),
                ('cancelled', 'Cancelled', False, {})
            ]
        },
        'quantity': {
            'validators': [DataRequired(), NumberRange(min=1)]
        }
    }
    form_extra_fields = {
        'start_date': DateField('Start date', format='%Y-%m-%d'),
        'end_date': DateField('End date', format='%Y-%m-%d')
    }

    
    def on_model_change(self, form, model, is_created):
        if is_created:
            drug = Drug.query.get(model.drug_id)
            if drug.stock >= model.quantity:
                drug.stock -= model.quantity
            else:
                raise ValidationError("Insufficient drug stock")
            

class InvoiceView(ModelView):
    column_list = ['id', 'patient', 'invoice_date', 'total_amount']
    
    form_columns = [
        'patient',
        'visit',
        'invoice_date',
        'professional_fee',
        'tax_amount',
        'discount_amount',
        'notes',
        'invoice_items'
    ]

    # ✅ Correct usage of inline_models with configuration
    inline_models = [
        (
            InvoiceItem,
            {
                'form_columns': ['drugs', 'description', 'quantity', 'unit_price'],
                'form_args': {
                    'drugs': {
                        'query_factory': lambda: Drug.query.filter_by(is_active=True),
                        'get_label': 'name'
                    },
                    'unit_price': {
                        'validators': [NumberRange(min=0)]
                    },
                    'quantity': {
                        'validators': [NumberRange(min=1)]
                    }
                },
                'form_extra_fields': {
                    'unit_price': DecimalField('Unit Price', validators=[NumberRange(min=0)]),
                    'quantity': DecimalField('Quantity', validators=[NumberRange(min=1)])
                }
            }
        )
    ]

    # Custom templates
    edit_template = 'billing/invoice_edit.html'
    details_template = 'billing/invoice_details.html'

    form_args = {
        'patient': {
            'query_factory': lambda: Patient.query.order_by(Patient.full_name),
            'get_label': 'full_name'
        },
        'visit': {
            'query_factory': lambda: Visit.query.order_by(Visit.visit_date.desc()),
            'get_label': 'visit_reference'  # Assumes you have this property defined
        }
    }

    column_extra_row_actions = [
        {
            'label': 'Print',
            'url': 'invoice.print_invoice',
            'icon_class': 'glyphicon glyphicon-print'
        }
    ]

    form_create_rules = [
        rules.Field('patient'),
        rules.HTML('<div id="patient-info">{{ form._obj.patient_info if form._obj else ""|safe }}</div>'),
        rules.FieldSet(
            (
                'visit',
                'invoice_date',
                'professional_fee',
                'tax_amount',
                'discount_amount',
                'notes',
                'invoice_items'
            ),
            'Invoice Details'
        )
    ]
    form_edit_rules = form_create_rules

    def create_form(self, obj=None):
        form = super().create_form(obj)
        form.patient.query = Patient.query.order_by(Patient.full_name)
        return form

    def on_model_change(self, form, model, is_created):
        if is_created and not getattr(model, 'doctor_id', None):
            model.doctor_id = current_user.id  # Assumes Flask-Login is used

    @expose('/print/<int:invoice_id>')
    def print_invoice(self, invoice_id):
        invoice = Invoice.query.get_or_404(invoice_id)
        rendered = render_template('billing/invoice_print.html', invoice=invoice)
        pdf = pdfkit.from_string(rendered, False)
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=invoice{invoice_id}.pdf'
        return response

    @expose('/preview/<int:invoice_id>')
    def preview_invoice(self, invoice_id):
        invoice = Invoice.query.get_or_404(invoice_id)
        return render_template('billing/invoice_preview.html', invoice=invoice)
    
    @expose('/download/<int:invoice_id>')
    def download_pdf(self, invoice_id):
        invoice = Invoice.query.get_or_404(invoice_id)
        rendered = render_template('billing/invoice_print.html', invoice=invoice)
        config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')  # if needed
        pdf = pdfkit.from_string(rendered, False, configuration=config)

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=invoice_{invoice_id}.pdf'
        return response


class TriageAdminView(ModelView):
    column_list = ['visit', 'blood_pressure', 'temperature', 'pulse', 'bmi']
    form_columns = ['visit', 'height', 'weight', 'temperature', 
                    'blood_pressure_systolic', 'blood_pressure_diastolic', 
                    'pulse', 'notes']

    def on_model_change(self, form, model, is_created):
        if model.height > 0 and model.weight:
            model.bmi = round(model.weight / ((model.height / 100) ** 2))

class PaymentAdminView(ModelView):
    column_list = ['invoice', 'amount', 'payment_method', 'payment_date']
    form_columns = ['invoice', 'amount', 'payment_method', 'payment_date', 'transaction_reference']

def setup_admin(app):
    admin = Admin(
        app,
        name='KMC EHR Admin',
        template_mode='bootstrap4',  # or 'bootstrap3'
        index_view=KMCAdminIndexView(
            name='Dashboard',
            url='/admin',
            endpoint='admin'
        )
    )
    
    admin.add_view(PatientAdminView(Patient, db.session, name='Patients', category='Records'))
    admin.add_view(VisitAdminView(Visit, db.session, name='Visits', category='Records'))
    admin.add_view(TriageAdminView(Triage, db.session, name='Triage', category='Medical'))
    admin.add_view(PrescriptionAdminView(Prescription, db.session, name='Prescriptions', category='Medical'))
    admin.add_view(ModelView(Drug, db.session, name='Drug Inventory', category='Pharmacy'))
    admin.add_view(PaymentAdminView(Payment, db.session, name='Payments', category='Billing'))
    admin.add_view(ModelView(Doctor, db.session, name='Doctors', category='Staff'))
    admin.add_view(VisitReportView(VisitReport, db.session, name='Medical Form', category='Medical'))
    admin.add_view(InvoiceView(Invoice, db.session, name='Invoices', category="Billing"))