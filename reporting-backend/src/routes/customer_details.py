from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)

customer_details_bp = Blueprint('customer_details', __name__)

@customer_details_bp.route('/api/customers/<int:customer_id>/details', methods=['GET'])
@jwt_required()
def get_customer_details(customer_id):
    """Get detailed information for a specific customer"""
    # Get tenant schema
    from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
    try:
        schema = get_tenant_schema()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        db = get_tenant_db()
        
        # Current fiscal year dates
        current_date = datetime.now()
        if current_date.month >= 11:
            fiscal_year_start = datetime(current_date.year, 11, 1)
        else:
            fiscal_year_start = datetime(current_date.year - 1, 11, 1)
        
        fiscal_year_start_str = fiscal_year_start.strftime('%Y-%m-%d')
        
        # Customer summary
        summary_query = f"""
        SELECT 
            Customer as customer_id,
            MAX(BillToName) as customer_name,
            COUNT(DISTINCT InvoiceNo) as total_invoices,
            SUM(GrandTotal) as total_sales,
            AVG(GrandTotal) as avg_invoice_value,
            MIN(InvoiceDate) as first_purchase_date,
            MAX(InvoiceDate) as last_purchase_date,
            DATEDIFF(day, MAX(InvoiceDate), GETDATE()) as days_since_last_invoice
        FROM {schema}.InvoiceReg
        WHERE Customer = {customer_id}
            AND InvoiceDate >= '{fiscal_year_start_str}'
        GROUP BY Customer
        """
        
        summary_result = db.execute_query(summary_query)
        
        if not summary_result or len(summary_result) == 0:
            return jsonify({
                'error': 'Customer not found',
                'message': f'No data found for customer ID {customer_id}'
            }), 404
        
        summary = summary_result[0]
        
        # Recent invoices (last 10)
        invoices_query = f"""
        SELECT TOP 10
            InvoiceNo as invoice_no,
            InvoiceDate as invoice_date,
            GrandTotal as grand_total,
            CASE 
                WHEN DATEDIFF(day, InvoiceDate, GETDATE()) <= 30 THEN 'Recent'
                WHEN DATEDIFF(day, InvoiceDate, GETDATE()) <= 90 THEN 'Normal'
                ELSE 'Old'
            END as status
        FROM {schema}.InvoiceReg
        WHERE Customer = {customer_id}
            AND InvoiceDate >= '{fiscal_year_start_str}'
        ORDER BY InvoiceDate DESC
        """
        
        recent_invoices = db.execute_query(invoices_query)
        
        # Monthly purchase history (last 12 months)
        twelve_months_ago = (current_date - timedelta(days=365)).strftime('%Y-%m-%d')
        
        monthly_query = f"""
        SELECT 
            YEAR(InvoiceDate) as year,
            MONTH(InvoiceDate) as month,
            SUM(GrandTotal) as sales,
            COUNT(DISTINCT InvoiceNo) as invoice_count
        FROM {schema}.InvoiceReg
        WHERE Customer = {customer_id}
            AND InvoiceDate >= '{twelve_months_ago}'
        GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
        ORDER BY year, month
        """
        
        monthly_purchases = db.execute_query(monthly_query)
        
        # Format monthly purchases with month names
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        formatted_monthly = []
        
        if monthly_purchases:
            for mp in monthly_purchases:
                month_name = month_names[mp['month'] - 1]
                formatted_monthly.append({
                    'month': f"{month_name} '{str(mp['year'])[2:]}",
                    'sales': float(mp['sales']),
                    'invoice_count': mp['invoice_count']
                })
        
        return jsonify({
            'customer_id': summary['customer_id'],
            'customer_name': summary['customer_name'],
            'total_invoices': summary['total_invoices'],
            'total_sales': float(summary['total_sales']),
            'avg_invoice_value': float(summary['avg_invoice_value']),
            'first_purchase_date': summary['first_purchase_date'].strftime('%Y-%m-%d'),
            'last_purchase_date': summary['last_purchase_date'].strftime('%Y-%m-%d'),
            'days_since_last_invoice': summary['days_since_last_invoice'],
            'recent_invoices': [
                {
                    'invoice_no': inv['invoice_no'],
                    'invoice_date': inv['invoice_date'].strftime('%Y-%m-%d'),
                    'grand_total': float(inv['grand_total']),
                    'status': inv['status']
                }
                for inv in recent_invoices
            ] if recent_invoices else [],
            'monthly_purchases': formatted_monthly
        })
        
    except Exception as e:
        logger.error(f"Error fetching customer details for ID {customer_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch customer details',
            'message': str(e)
        }), 500
