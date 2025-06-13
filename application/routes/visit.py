from flask import Blueprint, render_template
from application.models.models import Visit

visit = Blueprint('visit', __name__, url_prefix='/visit')


@visit.route('/visit/<int:visit_id>/form')
def generate_medical_form(visit_id):
    visit = Visit.query.get_or_404(visit_id)
    return render_template('visit_summary.html', visit=visit)
