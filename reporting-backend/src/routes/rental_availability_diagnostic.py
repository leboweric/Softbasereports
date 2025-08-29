"""
Diagnostic endpoint to understand Equipment table structure and identify sold units
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.database_service import get_db
import logging

logger = logging.getLogger(__name__)
rental_diag_bp = Blueprint('rental_diagnostic', __name__, url_prefix='/api/rental-diagnostic')

@rental_diag_bp.route('/equipment-schema', methods=['GET'])
@jwt_required()
def get_equipment_schema():
    """Get all columns in Equipment table"""
    try:
        db = get_db()
        
        # Get all columns from Equipment table
        schema_query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002' 
        AND TABLE_NAME = 'Equipment'
        ORDER BY ORDINAL_POSITION
        """
        
        columns = db.execute_query(schema_query)
        
        return jsonify({
            'total_columns': len(columns) if columns else 0,
            'columns': columns
        })
        
    except Exception as e:
        logger.error(f"Error getting equipment schema: {str(e)}")
        return jsonify({'error': str(e)}), 500

@rental_diag_bp.route('/rental-status-values', methods=['GET'])
@jwt_required()
def get_rental_status_values():
    """Get all unique RentalStatus values"""
    try:
        db = get_db()
        
        query = """
        SELECT DISTINCT 
            RentalStatus,
            COUNT(*) as count
        FROM ben002.Equipment
        WHERE RentalStatus IS NOT NULL
        GROUP BY RentalStatus
        ORDER BY COUNT(*) DESC
        """
        
        statuses = db.execute_query(query)
        
        return jsonify({
            'total_unique_statuses': len(statuses) if statuses else 0,
            'statuses': statuses
        })
        
    except Exception as e:
        logger.error(f"Error getting rental statuses: {str(e)}")
        return jsonify({'error': str(e)}), 500

@rental_diag_bp.route('/problem-units', methods=['GET'])
@jwt_required()
def analyze_problem_units():
    """Analyze the specific units that manager said should not appear"""
    try:
        db = get_db()
        
        # Units from manager's feedback that are marked as sold
        problem_units = [
            '15597',    # Sold Unit
            '17004',    # Sold Unit  
            '17295B',   # Sold Unit
            '17636',    # Sold Unit
            '18552',    # Sold Unit
            '18808',    # Sold Unit
            '18823',    # Sold Unit
            '18835',    # Sold Unit
            '18838B',   # Sold Unit
            '18993B',   # Sold Unit
            '19060',    # Sold Unit
            '19063',    # Sold Unit
            '19306B',   # Sold Unit
            '19321B',   # Sold Unit
            '19332',    # Sold Unit
            '19420',    # Sold Unit
            '19421',    # Sold Unit
            '19463B',   # Sold Unit
            '19628B',   # Sold Unit
            '19645B',   # Transferred to Used / Sold Unit
            '19752B',   # Sold Unit
            '19809B',   # Sold Unit
            '19890',    # Sold Unit
            '19950B',   # Transferred to Used / Sold Unit
            '20134',    # Sold Unit
            '20134B',   # Sold Unit
            '20457',    # Sold Unit
            '20868B',   # Sold Unit
            '21775',    # Not a Rental Unit
            'SER01'     # Not a Rental Unit
        ]
        
        # Convert to SQL IN clause
        units_str = "','".join(problem_units)
        
        query = f"""
        SELECT 
            UnitNo,
            SerialNo,
            Make,
            Model,
            RentalStatus,
            CustomerNo,
            Location,
            DeletionTime,
            InventoryDept,
            DayRent,
            WeekRent,
            MonthRent,
            WebRentalFlag,
            RentalYTD,
            RentalITD,
            -- Check for recent rental history
            (SELECT TOP 1 1 
             FROM ben002.RentalHistory rh 
             WHERE rh.SerialNo = e.SerialNo 
             AND rh.Year >= YEAR(DATEADD(MONTH, -12, GETDATE()))
            ) as HasRecentRentalHistory,
            -- Get last rental date
            (SELECT MAX(CAST(CAST(Year AS VARCHAR(4)) + '-' + CAST(Month AS VARCHAR(2)) + '-01' AS DATE))
             FROM ben002.RentalHistory rh
             WHERE rh.SerialNo = e.SerialNo
             AND rh.DaysRented > 0
            ) as LastRentalMonth
        FROM ben002.Equipment e
        WHERE UnitNo IN ('{units_str}')
        ORDER BY UnitNo
        """
        
        results = db.execute_query(query)
        
        # Analyze patterns
        analysis = {
            'total_units_checked': len(problem_units),
            'units_found': len(results) if results else 0,
            'units_data': results,
            'patterns': {}
        }
        
        if results:
            # Look for common patterns
            rental_statuses = {}
            inventory_depts = {}
            has_rental_rates = 0
            has_recent_history = 0
            
            for unit in results:
                # Count rental statuses
                status = unit.get('RentalStatus', 'NULL')
                rental_statuses[status] = rental_statuses.get(status, 0) + 1
                
                # Count inventory departments
                dept = unit.get('InventoryDept', 'NULL')
                inventory_depts[dept] = inventory_depts.get(dept, 0) + 1
                
                # Check for rental rates
                if (unit.get('DayRent', 0) or unit.get('WeekRent', 0) or unit.get('MonthRent', 0)):
                    has_rental_rates += 1
                
                # Check for recent history
                if unit.get('HasRecentRentalHistory'):
                    has_recent_history += 1
            
            analysis['patterns'] = {
                'rental_statuses': rental_statuses,
                'inventory_departments': inventory_depts,
                'units_with_rental_rates': has_rental_rates,
                'units_with_recent_history': has_recent_history
            }
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing problem units: {str(e)}")
        return jsonify({'error': str(e)}), 500

@rental_diag_bp.route('/find-sold-pattern', methods=['GET'])
@jwt_required()
def find_sold_pattern():
    """Try to find what distinguishes sold units from available ones"""
    try:
        db = get_db()
        
        # Compare a known sold unit with a known available unit
        query = """
        SELECT 
            'Sold Unit (15597)' as Category,
            UnitNo,
            RentalStatus,
            CustomerNo,
            InventoryDept,
            Location,
            DeletionTime,
            WebRentalFlag,
            CASE WHEN DayRent > 0 OR WeekRent > 0 OR MonthRent > 0 THEN 'Yes' ELSE 'No' END as HasRentalRates
        FROM ben002.Equipment
        WHERE UnitNo = '15597'
        
        UNION ALL
        
        SELECT 
            'Available Unit Sample' as Category,
            UnitNo,
            RentalStatus,
            CustomerNo,
            InventoryDept,
            Location,
            DeletionTime,
            WebRentalFlag,
            CASE WHEN DayRent > 0 OR WeekRent > 0 OR MonthRent > 0 THEN 'Yes' ELSE 'No' END as HasRentalRates
        FROM ben002.Equipment
        WHERE RentalStatus = 'Available'
        AND DayRent > 0
        AND InventoryDept = 40
        AND ROWNUM <= 5
        """
        
        results = db.execute_query(query)
        
        return jsonify({
            'comparison': results,
            'note': 'Comparing known sold unit with available units to find distinguishing patterns'
        })
        
    except Exception as e:
        logger.error(f"Error finding sold pattern: {str(e)}")
        return jsonify({'error': str(e)}), 500