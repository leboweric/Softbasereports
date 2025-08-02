from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService

monthly_expense_debug_bp = Blueprint('monthly_expense_debug', __name__)

@monthly_expense_debug_bp.route('/api/diagnostics/monthly-expense-debug', methods=['GET'])
@jwt_required()
def debug_monthly_expenses():
    """Debug monthly expense data to see why some months are missing"""
    try:
        db = AzureSQLService()
        results = {}
        
        # 1. Check raw monthly data from GLDetail
        raw_monthly_query = """
        SELECT 
            YEAR(EffectiveDate) as year,
            MONTH(EffectiveDate) as month,
            COUNT(*) as transaction_count,
            SUM(Amount) as total_amount,
            MIN(EffectiveDate) as first_date,
            MAX(EffectiveDate) as last_date
        FROM ben002.GLDetail
        WHERE AccountNo LIKE '6%'
        AND YEAR(EffectiveDate) = 2025
        GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        ORDER BY year, month
        """
        results['raw_monthly_data'] = db.execute_query(raw_monthly_query)
        
        # 2. Check the exact query used in the accounting endpoint
        endpoint_query = """
        WITH MonthlyExpenses AS (
            SELECT 
                YEAR(gld.EffectiveDate) as year,
                MONTH(gld.EffectiveDate) as month,
                SUM(gld.Amount) as total_expenses
            FROM ben002.GLDetail gld
            WHERE gld.AccountNo LIKE '6%'
                AND gld.EffectiveDate >= '2025-03-01'
                AND gld.EffectiveDate < DATEADD(DAY, 1, GETDATE())
            GROUP BY YEAR(gld.EffectiveDate), MONTH(gld.EffectiveDate)
        )
        SELECT 
            CONCAT(DATENAME(MONTH, DATEFROMPARTS(year, month, 1)), ' ', year) as month,
            total_expenses as expenses
        FROM MonthlyExpenses
        ORDER BY year, month
        """
        results['endpoint_query_results'] = db.execute_query(endpoint_query)
        
        # 3. Check for any date filtering issues
        date_check_query = """
        SELECT 
            MONTH(EffectiveDate) as month,
            COUNT(*) as count,
            MIN(CAST(EffectiveDate AS DATE)) as min_date,
            MAX(CAST(EffectiveDate AS DATE)) as max_date
        FROM ben002.GLDetail
        WHERE AccountNo LIKE '6%'
        AND EffectiveDate >= '2025-01-01'
        AND EffectiveDate < '2025-12-31'
        GROUP BY MONTH(EffectiveDate)
        ORDER BY month
        """
        results['date_distribution'] = db.execute_query(date_check_query)
        
        # 4. Sample transactions from each month
        sample_query = """
        SELECT 
            MONTH(EffectiveDate) as month,
            AccountNo,
            CAST(EffectiveDate AS DATE) as date,
            Amount,
            Description
        FROM (
            SELECT *,
                ROW_NUMBER() OVER (PARTITION BY MONTH(EffectiveDate) ORDER BY EffectiveDate DESC) as rn
            FROM ben002.GLDetail
            WHERE AccountNo LIKE '6%'
            AND YEAR(EffectiveDate) = 2025
        ) t
        WHERE rn <= 3
        ORDER BY month, date DESC
        """
        results['sample_transactions'] = db.execute_query(sample_query)
        
        # 5. Check for NULL or problematic dates
        null_check_query = """
        SELECT 
            COUNT(*) as total_expense_records,
            SUM(CASE WHEN EffectiveDate IS NULL THEN 1 ELSE 0 END) as null_dates,
            SUM(CASE WHEN YEAR(EffectiveDate) = 2025 THEN 1 ELSE 0 END) as records_2025,
            SUM(CASE WHEN YEAR(EffectiveDate) = 2025 AND MONTH(EffectiveDate) = 3 THEN 1 ELSE 0 END) as march_2025,
            SUM(CASE WHEN YEAR(EffectiveDate) = 2025 AND MONTH(EffectiveDate) = 4 THEN 1 ELSE 0 END) as april_2025,
            SUM(CASE WHEN YEAR(EffectiveDate) = 2025 AND MONTH(EffectiveDate) = 5 THEN 1 ELSE 0 END) as may_2025,
            SUM(CASE WHEN YEAR(EffectiveDate) = 2025 AND MONTH(EffectiveDate) = 6 THEN 1 ELSE 0 END) as june_2025,
            SUM(CASE WHEN YEAR(EffectiveDate) = 2025 AND MONTH(EffectiveDate) = 7 THEN 1 ELSE 0 END) as july_2025
        FROM ben002.GLDetail
        WHERE AccountNo LIKE '6%'
        """
        results['record_counts'] = db.execute_query(null_check_query)
        
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to debug monthly expenses: {str(e)}'
        }), 500