"""
Check units with Hold status
"""

from flask import Blueprint, jsonify
from src.services.azure_sql_service import AzureSQLService
import logging

logger = logging.getLogger(__name__)

check_hold_bp = Blueprint('check_hold', __name__)

@check_hold_bp.route('/api/check/hold-status', methods=['GET'])
def check_hold_status():
    """Check units with Hold rental status"""
    
    try:
        db = AzureSQLService()
        
        # Check units with Hold status
        query = """
        SELECT 
            UnitNo,
            SerialNo,
            Make,
            Model,
            RentalStatus,
            CustomerNo,
            Customer as CustomerOwnedFlag,
            Location
        FROM ben002.Equipment
        WHERE InventoryDept = 60
        AND RentalStatus = 'Hold'
        """
        
        result = db.execute_query(query)
        
        return jsonify({
            'success': True,
            'units_with_hold': result if result else [],
            'count': len(result) if result else 0
        })
        
    except Exception as e:
        logger.error(f"Error checking hold status: {str(e)}", exc_info=True)  
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500