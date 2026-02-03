from flask import Blueprint, jsonify
from src.utils.tenant_utils import get_tenant_db
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
from datetime import datetime

sales_pace_debug_bp = Blueprint('sales_pace_debug', __name__)

@sales_pace_debug_bp.route('/api/diagnostics/sales-pace-debug', methods=['GET'])
@jwt_required()
def debug_sales_pace():
    """Debug sales pace calculations"""
    try:
        db = get_tenant_db()
        
        # Get detailed sales for first few days of July and August
        july_detail_query = """
        SELECT 
            DAY(InvoiceDate) as day,
            COUNT(*) as invoice_count,
            SUM(GrandTotal) as total_sales,
            SUM(GrandTotal - COALESCE(EquipmentTaxable, 0) - COALESCE(EquipmentNonTax, 0)) as sales_no_equipment,
            SUM(COALESCE(EquipmentTaxable, 0) + COALESCE(EquipmentNonTax, 0)) as equipment_sales
        FROM ben002.InvoiceReg
        WHERE YEAR(InvoiceDate) = 2025
            AND MONTH(InvoiceDate) = 7
            AND DAY(InvoiceDate) <= 5
        GROUP BY DAY(InvoiceDate)
        ORDER BY DAY(InvoiceDate)
        """
        
        august_detail_query = """
        SELECT 
            DAY(InvoiceDate) as day,
            COUNT(*) as invoice_count,
            SUM(GrandTotal) as total_sales,
            SUM(GrandTotal - COALESCE(EquipmentTaxable, 0) - COALESCE(EquipmentNonTax, 0)) as sales_no_equipment,
            SUM(COALESCE(EquipmentTaxable, 0) + COALESCE(EquipmentNonTax, 0)) as equipment_sales
        FROM ben002.InvoiceReg
        WHERE YEAR(InvoiceDate) = 2025
            AND MONTH(InvoiceDate) = 8
            AND DAY(InvoiceDate) <= 5
        GROUP BY DAY(InvoiceDate)
        ORDER BY DAY(InvoiceDate)
        """
        
        # Get sample invoices for each period
        july_sample_query = """
        SELECT TOP 10
            InvoiceNo,
            InvoiceDate,
            GrandTotal,
            COALESCE(EquipmentTaxable, 0) + COALESCE(EquipmentNonTax, 0) as EquipmentTotal,
            CustomerNo,
            CustomerName
        FROM ben002.InvoiceReg
        WHERE YEAR(InvoiceDate) = 2025
            AND MONTH(InvoiceDate) = 7
            AND DAY(InvoiceDate) = 2
        ORDER BY GrandTotal DESC
        """
        
        august_sample_query = """
        SELECT TOP 10
            InvoiceNo,
            InvoiceDate,
            GrandTotal,
            COALESCE(EquipmentTaxable, 0) + COALESCE(EquipmentNonTax, 0) as EquipmentTotal,
            CustomerNo,
            CustomerName
        FROM ben002.InvoiceReg
        WHERE YEAR(InvoiceDate) = 2025
            AND MONTH(InvoiceDate) = 8
            AND DAY(InvoiceDate) <= 2
        ORDER BY GrandTotal DESC
        """
        
        july_details = db.execute_query(july_detail_query)
        august_details = db.execute_query(august_detail_query)
        july_samples = db.execute_query(july_sample_query)
        august_samples = db.execute_query(august_sample_query)
        
        # Calculate cumulative totals
        july_cumulative = 0
        august_cumulative = 0
        
        for row in july_details:
            july_cumulative += float(row['total_sales'] or 0)
            row['cumulative_sales'] = july_cumulative
            
        for row in august_details:
            august_cumulative += float(row['total_sales'] or 0)
            row['cumulative_sales'] = august_cumulative
        
        return jsonify({
            'july_daily_breakdown': july_details,
            'august_daily_breakdown': august_details,
            'july_2nd_samples': july_samples,
            'august_samples': august_samples,
            'analysis': {
                'july_day2_total': float(july_details[1]['total_sales']) if len(july_details) > 1 else 0,
                'august_through_day2': august_cumulative,
                'difference': august_cumulative - (float(july_details[1]['cumulative_sales']) if len(july_details) > 1 else 0)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500