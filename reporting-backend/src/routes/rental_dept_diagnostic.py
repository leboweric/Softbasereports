"""
Diagnostic endpoint to understand Rental Department inventory structure
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
import logging
from src.services.azure_sql_service import AzureSQLService

from flask_jwt_extended import get_jwt_identity
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

rental_dept_diagnostic_bp = Blueprint('rental_dept_diagnostic', __name__)

@rental_dept_diagnostic_bp.route('/api/rental/department-diagnostic', methods=['GET'])
@jwt_required()
def rental_department_diagnostic():
    """Analyze how Rental Department units are identified in the Equipment table."""
    
    try:
        db = AzureSQLService()
        schema = get_tenant_schema()
        # Query 1: Count units by InventoryDept
        dept_query = """
        SELECT 
            InventoryDept,
            COUNT(*) as UnitCount,
            COUNT(DISTINCT RentalStatus) as UniqueStatuses
        FROM {schema}.Equipment
        WHERE IsDeleted = 0 OR IsDeleted IS NULL
        GROUP BY InventoryDept
        ORDER BY InventoryDept
        """
        
        dept_results = db.execute_query(dept_query)
        
        # Query 2: For Dept 60 (Rental), breakdown by RentalStatus
        rental_status_query = """
        SELECT 
            RentalStatus,
            COUNT(*) as Count,
            -- Sample some fields to understand the data
            MIN(UnitNo) as SampleUnit,
            MIN(Location) as SampleLocation,
            CASE 
                WHEN SUM(CASE WHEN DayRent > 0 OR WeekRent > 0 OR MonthRent > 0 THEN 1 ELSE 0 END) > 0 
                THEN 'Has Rental Rates' 
                ELSE 'No Rental Rates' 
            END as RateStatus
        FROM {schema}.Equipment
        WHERE InventoryDept = 60
            AND (IsDeleted = 0 OR IsDeleted IS NULL)
        GROUP BY RentalStatus
        ORDER BY Count DESC
        """
        
        rental_status_results = db.execute_query(rental_status_query)
        
        # Query 3: Check for problematic statuses in Dept 60
        problem_query = """
        SELECT 
            UnitNo,
            SerialNo,
            Make,
            Model,
            RentalStatus,
            Location,
            DayRent,
            WeekRent,
            MonthRent,
            WebRentalFlag,
            CASE
                WHEN RentalStatus = 'Sold' THEN 'Sold Status'
                WHEN RentalStatus = 'Disposed' THEN 'Disposed Status'
                WHEN RentalStatus = 'Transferred' THEN 'Transferred Status'
                WHEN Location LIKE '%SOLD%' THEN 'SOLD in Location'
                WHEN Location LIKE '%DISPOSED%' THEN 'DISPOSED in Location'
                WHEN Location LIKE '%SCRAP%' THEN 'SCRAP in Location'
                WHEN Location LIKE '%AUCTION%' THEN 'AUCTION in Location'
                ELSE 'None'
            END as ProblemIndicator
        FROM {schema}.Equipment
        WHERE InventoryDept = 60
            AND (IsDeleted = 0 OR IsDeleted IS NULL)
            AND (
                RentalStatus IN ('Sold', 'Disposed', 'Transferred')
                OR Location LIKE '%SOLD%'
                OR Location LIKE '%DISPOSED%'
                OR Location LIKE '%SCRAP%'
                OR Location LIKE '%AUCTION%'
            )
        ORDER BY RentalStatus, UnitNo
        """
        
        problem_results = db.execute_query(problem_query)
        
        # Query 4: Current rental activity for Dept 60
        activity_query = """
        SELECT 
            'Currently On Rent' as Status,
            COUNT(DISTINCT e.UnitNo) as Count
        FROM {schema}.Equipment e
        JOIN {schema}.RentalHistory rh ON e.SerialNo = rh.SerialNo
        WHERE e.InventoryDept = 60
            AND (e.IsDeleted = 0 OR e.IsDeleted IS NULL)
            AND rh.Year = YEAR(GETDATE())
            AND rh.Month = MONTH(GETDATE())
            AND rh.DaysRented > 0
            AND rh.DeletionTime IS NULL
        
        UNION ALL
        
        SELECT 
            'Available (Ready To Rent)' as Status,
            COUNT(*) as Count
        FROM {schema}.Equipment e
        WHERE e.InventoryDept = 60
            AND (e.IsDeleted = 0 OR e.IsDeleted IS NULL)
            AND e.RentalStatus = 'Ready To Rent'
            AND e.SerialNo NOT IN (
                SELECT SerialNo 
                FROM {schema}.RentalHistory 
                WHERE Year = YEAR(GETDATE()) 
                    AND Month = MONTH(GETDATE())
                    AND DaysRented > 0
                    AND DeletionTime IS NULL
            )
        
        UNION ALL
        
        SELECT 
            'On Hold' as Status,
            COUNT(*) as Count
        FROM {schema}.Equipment e
        WHERE e.InventoryDept = 60
            AND (e.IsDeleted = 0 OR e.IsDeleted IS NULL)
            AND e.RentalStatus = 'Hold'
        """
        
        activity_results = db.execute_query(activity_query)
        
        # Query 5: Check other departments that might have rental equipment
        cross_dept_query = """
        SELECT 
            e.InventoryDept,
            sd.Description as DeptName,
            COUNT(*) as UnitsWithRentalRates
        FROM {schema}.Equipment e
        LEFT JOIN {schema}.SaleCodes sd ON e.InventoryDept = sd.Dept
        WHERE (e.DayRent > 0 OR e.WeekRent > 0 OR e.MonthRent > 0)
            AND (e.IsDeleted = 0 OR e.IsDeleted IS NULL)
        GROUP BY e.InventoryDept, sd.Description
        ORDER BY UnitsWithRentalRates DESC
        """
        
        cross_dept_results = db.execute_query(cross_dept_query)
        
        # Build response
        response = {
            'success': True,
            'analysis': {
                'units_by_department': [],
                'dept_60_rental_status': [],
                'problematic_units': [],
                'rental_activity_summary': [],
                'departments_with_rental_rates': [],
                'recommendations': []
            }
        }
        
        # Process department counts
        if dept_results:
            for row in dept_results:
                response['analysis']['units_by_department'].append({
                    'department': row['InventoryDept'] or 'NULL',
                    'unit_count': row['UnitCount'],
                    'unique_statuses': row['UniqueStatuses'],
                    'is_rental_dept': row['InventoryDept'] == 60
                })
        
        # Process rental status breakdown
        if rental_status_results:
            for row in rental_status_results:
                response['analysis']['dept_60_rental_status'].append({
                    'status': row['RentalStatus'] or 'NULL',
                    'count': row['Count'],
                    'sample_unit': row['SampleUnit'],
                    'sample_location': row['SampleLocation'],
                    'rate_status': row['RateStatus']
                })
        
        # Process problematic units
        if problem_results:
            for row in problem_results:
                response['analysis']['problematic_units'].append({
                    'unit_no': row['UnitNo'],
                    'serial_no': row['SerialNo'],
                    'make_model': f"{row['Make']} {row['Model']}",
                    'rental_status': row['RentalStatus'],
                    'location': row['Location'],
                    'problem': row['ProblemIndicator'],
                    'has_rates': bool(row['DayRent'] or row['WeekRent'] or row['MonthRent'])
                })
        
        # Process activity summary
        if activity_results:
            for row in activity_results:
                response['analysis']['rental_activity_summary'].append({
                    'status': row['Status'],
                    'count': row['Count']
                })
        
        # Process cross-department rental rates
        if cross_dept_results:
            for row in cross_dept_results:
                response['analysis']['departments_with_rental_rates'].append({
                    'department': row['InventoryDept'],
                    'name': row['DeptName'] or f"Dept {row['InventoryDept']}",
                    'units_with_rates': row['UnitsWithRentalRates']
                })
        
        # Generate recommendations
        recommendations = []
        
        if problem_results and len(problem_results) > 0:
            recommendations.append(f"Found {len(problem_results)} units in Dept 60 with problematic statuses (Sold/Disposed/Transferred)")
        
        # Check if Dept 60 is the primary rental department
        dept_60_count = next((d['unit_count'] for d in response['analysis']['units_by_department'] if d['department'] == 60), 0)
        if dept_60_count > 0:
            recommendations.append(f"Dept 60 contains {dept_60_count} units - appears to be the Rental Department")
        
        # Add filter recommendations
        recommendations.append("Recommended filter: InventoryDept = 60 AND RentalStatus NOT IN ('Sold', 'Disposed', 'Transferred')")
        recommendations.append("Additional check: Exclude units where Location contains 'SOLD', 'DISPOSED', 'SCRAP', or 'AUCTION'")
        
        response['analysis']['recommendations'] = recommendations
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in rental department diagnostic: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500