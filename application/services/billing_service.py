from flask import Blueprint, render_template, request, redirect, url_for, send_file
from application.models.models import Invoice
from application.services.document_service import DocumentService
from application import db
from datetime import datetime

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

@billing_bp.route('/invoices')
def invoice_list():
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    return render_template('billing/invoice_list.html', invoices=invoices)

@billing_bp.route('/invoice/<int:invoice_id>/download')
def download_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    try:
        # Try Word document first
        doc_stream = DocumentService.generate_word_invoice(invoice)
        return send_file(
            doc_stream,
            as_attachment=True,
            download_name=f"Invoice_{invoice.id}.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        # Fallback to PDF
        pdf_stream = DocumentService.generate_pdf_invoice(invoice)
        return send_file(
            pdf_stream,
            as_attachment=True,
            download_name=f"Invoice_{invoice.id}.pdf",
            mimetype='application/pdf'
        )