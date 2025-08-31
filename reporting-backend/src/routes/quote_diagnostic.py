"""
Diagnostic to understand quotes vs work orders
"""

from flask import Blueprint, jsonify
from src.services.azure_sql_service import AzureSQLService
import logging

logger = logging.getLogger(__name__)

quote_diagnostic_bp = Blueprint('quote_diagnostic', __name__)

@quote_diagnostic_bp.route('/api/diagnostic/quotes', methods=['GET'])
def check_quotes():
    """Check how quotes are distinguished from work orders"""
    
    try:
        db = AzureSQLService()
        results = {}
        
        # Check WO 91600003 specifically
        check_91600003 = """
        SELECT 
            WONo,
            Type,
            OpenDate,
            ClosedDate,
            CompletedDate,
            QuoteNo,
            EstimateNo,
            BillTo,
            RentalContractNo,
            DeletionTime
        FROM ben002.WO
        WHERE WONo = '91600003'
        """
        try:
            result = db.execute_query(check_91600003)
            results['wo_91600003'] = result if result else []
        except Exception as e:
            results['wo_91600003_error'] = str(e)
        
        # Check if quotes have a different type or indicator
        type_check = """
        SELECT DISTINCT TOP 20
            Type,
            COUNT(*) as Count,
            MIN(WONo) as SampleWONo
        FROM ben002.WO
        WHERE OpenDate >= DATEADD(month, -1, GETDATE())
        GROUP BY Type
        ORDER BY Count DESC
        """
        try:
            result = db.execute_query(type_check)
            results['wo_types'] = result if result else []
        except Exception as e:
            results['type_check_error'] = str(e)
        
        # Check for quote-specific fields
        quote_fields = """
        SELECT TOP 10
            WONo,
            Type,
            QuoteNo,
            EstimateNo,
            OpenDate,
            ClosedDate
        FROM ben002.WO
        WHERE (QuoteNo IS NOT NULL AND QuoteNo != '')
        OR (EstimateNo IS NOT NULL AND EstimateNo != '')
        OR WONo LIKE '9%'  -- Quotes might start with 9
        ORDER BY OpenDate DESC
        """
        try:
            result = db.execute_query(quote_fields)
            results['potential_quotes'] = result if result else []
        except Exception as e:
            results['quote_fields_error'] = str(e)
        
        # Check WORental entries for 91600003
        worental_check = """
        SELECT 
            wr.WONo,
            wr.UnitNo,
            wr.SerialNo,
            wo.Type,
            wo.OpenDate,
            wo.ClosedDate
        FROM ben002.WORental wr
        INNER JOIN ben002.WO wo ON wr.WONo = wo.WONo
        WHERE wr.WONo = '91600003'
        """
        try:
            result = db.execute_query(worental_check)
            results['worental_91600003'] = result if result else []
        except Exception as e:
            results['worental_check_error'] = str(e)
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Error in quote diagnostic: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500