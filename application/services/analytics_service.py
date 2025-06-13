from application.models import db, Invoice, Prescription
from datetime import datetime, timedelta
import pandas as pd

class AnalyticsService:
    @staticmethod
    def get_financial_report(start_date=None, end_date=None):
        """Generate financial summary"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
            
        query = db.session.query(
            Invoice.status,
            db.func.sum(Invoice.total_amount).label('total'),
            db.func.count().label('count')
        ).filter(
            Invoice.created_at.between(start_date, end_date)
        ).group_by(Invoice.status)
        
        return pd.DataFrame(query.all(), columns=['status', 'total', 'count'])
    
    @staticmethod
    def get_prescription_analytics():
        """Top prescribed medications"""
        query = db.session.query(
            Prescription.medication,
            db.func.count().label('prescription_count')
        ).group_by(Prescription.medication).order_by(db.desc('prescription_count')).limit(10)
        
        return pd.DataFrame(query.all(), columns=['medication', 'count'])