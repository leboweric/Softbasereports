from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
from datetime import datetime, timedelta

dashboard_pace_bp = Blueprint('dashboard_pace', __name__)

@dashboard_pace_bp.route('/api/dashboard/sales-pace', methods=['GET'])
@jwt_required()
def get_sales_pace():
    """Get sales pace data comparing current month to previous month through same day"""
    try:
        db = AzureSQLService()
        
        # Get current date info
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        current_day = now.day
        
        # Calculate previous month
        if current_month == 1:
            prev_month = 12
            prev_year = current_year - 1
        else:
            prev_month = current_month - 1
            prev_year = current_year
        
        # Query to get sales through same day for current and previous month
        current_sales_query = f"""
        SELECT 
            SUM(GrandTotal) as total_sales,
            SUM(GrandTotal - COALESCE(EquipmentTaxable, 0) - COALESCE(EquipmentNonTax, 0)) as sales_no_equipment
        FROM ben002.InvoiceReg
        WHERE YEAR(InvoiceDate) = {current_year}
            AND MONTH(InvoiceDate) = {current_month}
            AND DAY(InvoiceDate) <= {current_day}
        """
        
        prev_sales_query = f"""
        SELECT 
            SUM(GrandTotal) as total_sales,
            SUM(GrandTotal - COALESCE(EquipmentTaxable, 0) - COALESCE(EquipmentNonTax, 0)) as sales_no_equipment
        FROM ben002.InvoiceReg
        WHERE YEAR(InvoiceDate) = {prev_year}
            AND MONTH(InvoiceDate) = {prev_month}
            AND DAY(InvoiceDate) <= {current_day}
        """
        
        # Execute queries
        current_results = db.execute_query(current_sales_query)
        prev_results = db.execute_query(prev_sales_query)
        
        # Process results
        current_sales = 0
        previous_sales = 0
        current_no_equip = 0
        previous_no_equip = 0
        
        if current_results and len(current_results) > 0:
            current_sales = float(current_results[0]['total_sales'] or 0)
            current_no_equip = float(current_results[0]['sales_no_equipment'] or 0)
            
        if prev_results and len(prev_results) > 0:
            previous_sales = float(prev_results[0]['total_sales'] or 0)
            previous_no_equip = float(prev_results[0]['sales_no_equipment'] or 0)
        
        # Calculate pace percentages
        pace_pct = ((current_sales / previous_sales) - 1) * 100 if previous_sales > 0 else 0
        pace_pct_no_equip = ((current_no_equip / previous_no_equip) - 1) * 100 if previous_no_equip > 0 else 0
        
        # Get full month totals for context
        full_month_query = f"""
        SELECT 
            SUM(GrandTotal) as total_sales,
            SUM(CASE WHEN InvoiceType != 'M' THEN GrandTotal ELSE 0 END) as sales_no_equipment
        FROM ben002.InvoiceReg
        WHERE YEAR(InvoiceDate) = {prev_year}
            AND MONTH(InvoiceDate) = {prev_month}
        """
        
        full_month_results = db.execute_query(full_month_query)
        previous_full_month = float(full_month_results[0]['total_sales'] or 0) if full_month_results else 0
        previous_full_month_no_equip = float(full_month_results[0]['sales_no_equipment'] or 0) if full_month_results else 0
        
        # Project current month based on pace
        days_in_month = 31  # Approximate, could be calculated exactly
        projected_total = (current_sales / current_day) * days_in_month if current_day > 0 else 0
        projected_no_equip = (current_no_equip / current_day) * days_in_month if current_day > 0 else 0
        
        return jsonify({
            'current_month': {
                'year': current_year,
                'month': current_month,
                'day': current_day,
                'sales_to_date': current_sales,
                'sales_no_equipment_to_date': current_no_equip,
                'projected_total': projected_total,
                'projected_no_equipment': projected_no_equip
            },
            'previous_month': {
                'year': prev_year,
                'month': prev_month,
                'sales_through_same_day': previous_sales,
                'sales_no_equipment_through_same_day': previous_no_equip,
                'full_month_total': previous_full_month,
                'full_month_no_equipment': previous_full_month_no_equip
            },
            'pace': {
                'percentage': round(pace_pct, 1),
                'percentage_no_equipment': round(pace_pct_no_equip, 1),
                'ahead_behind': 'ahead' if pace_pct > 0 else 'behind' if pace_pct < 0 else 'on pace',
                'ahead_behind_no_equipment': 'ahead' if pace_pct_no_equip > 0 else 'behind' if pace_pct_no_equip < 0 else 'on pace'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get sales pace: {str(e)}'}), 500