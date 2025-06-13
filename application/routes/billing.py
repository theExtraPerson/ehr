from flask import Blueprint, render_template
from application.models.models import Invoice, Prescription, Drug, Visit
from application.extensions import db

billing = Blueprint('billing', __name__, url_prefix='/billing')

@billing.route('/invoice/<int:visit_id>')
def generate_invoice(visit_id):
    visit = Visit.query.get_or_404(visit_id)
    prescriptions = Prescription.query.filter_by(visit_id=visit_id)

    drug_items = []
    drug_total = 0
    for pres in prescriptions:
        subtotal = pres.quantity * pres.drug.unit_price
        drug_total += subtotal
        drug_items.append({
            'drug': pres.drug.name,
            'dosage': pres.dosage,
            'quantity': pres.quantity,
            'unit_price': pres.drug.unit_price,
            'subtotal': subtotal
        })
    
    invoice = visit.invoice

    # Calculate total, store invoice
    total = drug_total + invoice.consultation_fee + invoice.sundries

    return render_template('invoice_summary.html',
                        invoice=invoice,
                        patient=visit.patient,
                        visit=visit,
                        drug_items=drug_items,
                        total=total)
