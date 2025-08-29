"""
Test endpoint to debug rental availability query
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
import logging
from src.services.azure_sql_service import AzureSQLService

logger = logging.getLogger(__name__)

rental_test_bp = Blueprint('rental_test', __name__)

@rental_test_bp.route('/api/rental/test-query', methods=['GET'])
@jwt_required()
def test_rental_query():
    """Test different parts of the rental query to see what's failing"""
    
    try:
        db = AzureSQLService()
        results = {}
        
        # Test 1: Simple count of Department 60
        test1_query = """
        SELECT COUNT(*) as count
        FROM ben002.Equipment
        WHERE InventoryDept = 60
        """
        try:
            result = db.execute_query(test1_query)
            results['dept_60_count'] = result[0]['count'] if result else 0
        except Exception as e:
            results['dept_60_count'] = f"Error: {str(e)}"
        
        # Test 2: Count with IsDeleted filter
        test2_query = """
        SELECT COUNT(*) as count
        FROM ben002.Equipment
        WHERE InventoryDept = 60
        AND (IsDeleted = 0 OR IsDeleted IS NULL)
        """
        try:
            result = db.execute_query(test2_query)
            results['dept_60_not_deleted'] = result[0]['count'] if result else 0
        except Exception as e:
            results['dept_60_not_deleted'] = f"Error: {str(e)}"
        
        # Test 3: Sample records
        test3_query = """
        SELECT TOP 5 
            UnitNo,
            SerialNo,
            Make,
            Model,
            RentalStatus,
            Location,
            IsDeleted
        FROM ben002.Equipment
        WHERE InventoryDept = 60
        """
        try:
            result = db.execute_query(test3_query)
            results['sample_records'] = result if result else []
        except Exception as e:
            results['sample_records'] = f"Error: {str(e)}"
        
        # Test 4: Check RentalHistory
        test4_query = """
        SELECT COUNT(DISTINCT e.SerialNo) as count
        FROM ben002.Equipment e
        JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo
        WHERE e.InventoryDept = 60
        AND rh.Year = YEAR(GETDATE())
        AND rh.Month = MONTH(GETDATE())
        AND rh.DaysRented > 0
        """
        try:
            result = db.execute_query(test4_query)
            results['currently_on_rent'] = result[0]['count'] if result else 0
        except Exception as e:
            results['currently_on_rent'] = f"Error: {str(e)}"
        
        # Test 5: Simple version of main query
        test5_query = """
        SELECT COUNT(*) as count
        FROM ben002.Equipment e
        LEFT JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo 
            AND rh.Year = YEAR(GETDATE()) 
            AND rh.Month = MONTH(GETDATE())
            AND rh.DaysRented > 0
            AND rh.DeletionTime IS NULL
        WHERE e.InventoryDept = 60
        AND (e.IsDeleted = 0 OR e.IsDeleted IS NULL)
        """
        try:
            result = db.execute_query(test5_query)
            results['main_query_count'] = result[0]['count'] if result else 0
        except Exception as e:
            results['main_query_count'] = f"Error: {str(e)}"
        
        return jsonify({
            'success': True,
            'tests': results
        })
        
    except Exception as e:
        logger.error(f"Error in rental test: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500