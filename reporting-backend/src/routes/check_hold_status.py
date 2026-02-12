"""
Check units with Hold status
"""

from flask import Blueprint, jsonify
import logging

from flask_jwt_extended import get_jwt_identity
from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
from src.models.user import User

logger = logging.getLogger(__name__)

check_hold_bp = Blueprint('check_hold', __name__)

@check_hold_bp.route('/api/check/hold-status', methods=['GET'])
def check_hold_status():
    """Check units with Hold rental status"""
    
    try:
        db = get_tenant_db()
        
        # Check units with Hold status
        schema = get_tenant_schema()

        query = f"""
        SELECT 
            UnitNo,
            SerialNo,
            Make,
            Model,
            RentalStatus,
            CustomerNo,
            Customer as CustomerOwnedFlag,
            Location
        FROM {schema}.Equipment
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