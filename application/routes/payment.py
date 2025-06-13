from flask import request, redirect, render_template, url_for, Blueprint
from application.models.models import Invoice
from application.extensions import db

payment = Blueprint('payment', __name__, url_prefix='/payment')

@payment.route('/pay/<int:invoice_id>', methods=['GET', 'POST'])
def pay(invoice_id):
    if request.method == 'POST':
        # Save payment record
        return redirect(url_for('payment.receipt', payment_id=payment.id))
    return render_template('payment_form.html', invoice=invoice)


@payment.route('/receipt/<int:payment_id>')
def receipt(payment_id):
    return render_template('receipt.html', payment=payment)
