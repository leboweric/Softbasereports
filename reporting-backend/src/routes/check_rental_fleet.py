"""
Check what RENTAL FLEET - EXPENSE means
"""

from flask import Blueprint, jsonify
import logging

from flask_jwt_extended import get_jwt_identity
from src.utils.tenant_utils import get_tenant_db
from src.models.user import User

def get_tenant_schema():
    """Get the database schema for the current user's organization"""
    try:
        user_id = get_jwt_identity()
        if user_id:
            user = User.query.get(int(user_id))
            if user and user.organization and user.organization.database_schema:
                return user.organization.database_schema
        return 'ben002'  # Fallback
    except:
        return 'ben002'



logger = logging.getLogger(__name__)

check_rental_fleet_bp = Blueprint('check_rental_fleet', __name__)

@check_rental_fleet_bp.route('/api/check/rental-fleet', methods=['GET'])
def check_rental_fleet():
    """Check RENTAL FLEET - EXPENSE customer"""
    
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        results = {}
        
        # 1. Check if RENTAL FLEET - EXPENSE is a customer
        customer_check = """
        SELECT Number, Name, Address, City, State
        FROM {schema}.Customer
        WHERE Name LIKE '%RENTAL FLEET%'
        OR Number = '900006'
        """
        try:
            result = db.execute_query(customer_check)
            results['rental_fleet_customer'] = result if result else []
        except Exception as e:
            results['customer_check_error'] = str(e)
        
        # 2. Check unit 21515 specifically
        unit_check = """
        -- Check equipment record
        SELECT 
            e.UnitNo,
            e.SerialNo,
            e.CustomerNo,
            e.InventoryDept,
            e.Customer as CustomerOwnedFlag,
            c.Name as CustomerName
        FROM {schema}.Equipment e
        LEFT JOIN {schema}.Customer c ON e.CustomerNo = c.Number
        WHERE e.UnitNo = '21515'
        """
        try:
            result = db.execute_query(unit_check)
            results['unit_21515_equipment'] = result if result else []
        except Exception as e:
            results['unit_21515_error'] = str(e)
        
        # 3. Check open WOs for 21515
        wo_check = """
        SELECT 
            wo.WONo,
            wo.Type,
            wo.OpenDate,
            wo.ClosedDate,
            wo.BillTo,
            c.Name as CustomerName,
            wr.UnitNo,
            wr.SerialNo
        FROM {schema}.WORental wr
        INNER JOIN {schema}.WO wo ON wr.WONo = wo.WONo
        LEFT JOIN {schema}.Customer c ON wo.BillTo = c.Number
        WHERE wr.UnitNo = '21515'
        AND wo.Type = 'R'
        AND wo.ClosedDate IS NULL
        """
        try:
            result = db.execute_query(wo_check)
            results['unit_21515_open_wos'] = result if result else []
        except Exception as e:
            results['unit_21515_wo_error'] = str(e)
        
        # 4. Check recent closed WOs for 21515
        closed_wo_check = """
        SELECT TOP 5
            wo.WONo,
            wo.Type,
            wo.OpenDate,
            wo.ClosedDate,
            wo.BillTo,
            c.Name as CustomerName
        FROM {schema}.WORental wr
        INNER JOIN {schema}.WO wo ON wr.WONo = wo.WONo
        LEFT JOIN {schema}.Customer c ON wo.BillTo = c.Number
        WHERE wr.UnitNo = '21515'
        AND wo.Type = 'R'
        AND wo.ClosedDate IS NOT NULL
        ORDER BY wo.ClosedDate DESC
        """
        try:
            result = db.execute_query(closed_wo_check)
            results['unit_21515_recent_closed'] = result if result else []
        except Exception as e:
            results['closed_wo_error'] = str(e)
        
        # 5. Check how many units show RENTAL FLEET - EXPENSE
        count_check = """
        SELECT COUNT(*) as count
        FROM {schema}.Equipment e
        LEFT JOIN {schema}.Customer c ON e.CustomerNo = c.Number
        WHERE e.InventoryDept = 60
        AND c.Name = 'RENTAL FLEET - EXPENSE'
        """
        try:
            result = db.execute_query(count_check)
            results['rental_fleet_count'] = result[0]['count'] if result else 0
        except Exception as e:
            results['count_error'] = str(e)
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Error checking rental fleet: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500