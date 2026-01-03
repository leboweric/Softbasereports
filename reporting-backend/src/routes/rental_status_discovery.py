"""
Endpoint to discover all RentalStatus values in the Equipment table
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

rental_status_discovery_bp = Blueprint('rental_status_discovery', __name__)

@rental_status_discovery_bp.route('/api/rental/discover-status-values', methods=['GET'])
@jwt_required()
def discover_rental_status():
    """Discover all RentalStatus values and their usage patterns."""
    
    try:
        db = AzureSQLService()
        schema = get_tenant_schema()
        # Query 1: Get all unique RentalStatus values for Dept 60
        dept60_status_query = f"""
        SELECT 
            RentalStatus,
            COUNT(*) as Count,
            -- Check if any are currently on rent
            SUM(CASE 
                WHEN EXISTS (
                    SELECT 1 FROM {schema}.RentalHistory rh 
                    WHERE rh.SerialNo = e.SerialNo 
                    AND rh.Year = YEAR(GETDATE()) 
                    AND rh.Month = MONTH(GETDATE())
                    AND rh.DaysRented > 0
                    AND rh.DeletionTime IS NULL
                ) THEN 1 ELSE 0 
            END) as CurrentlyOnRent,
            -- Sample data
            MIN(UnitNo) as SampleUnit1,
            MAX(UnitNo) as SampleUnit2,
            MIN(Location) as SampleLocation,
            AVG(CAST(RentalYTD as float)) as AvgRentalYTD,
            SUM(CASE WHEN DayRent > 0 OR WeekRent > 0 OR MonthRent > 0 THEN 1 ELSE 0 END) as UnitsWithRates
        FROM {schema}.Equipment e
        WHERE InventoryDept = 60
            AND (IsDeleted = 0 OR IsDeleted IS NULL)
        GROUP BY RentalStatus
        ORDER BY Count DESC
        """
        
        dept60_results = db.execute_query(dept60_status_query)
        
        # Query 2: Get all unique RentalStatus values across ALL departments for comparison
        all_status_query = f"""
        SELECT 
            RentalStatus,
            COUNT(*) as TotalCount,
            COUNT(DISTINCT InventoryDept) as DepartmentCount,
            STRING_AGG(CAST(DISTINCT InventoryDept as varchar), ', ') as Departments
        FROM {schema}.Equipment
        WHERE (IsDeleted = 0 OR IsDeleted IS NULL)
        GROUP BY RentalStatus
        ORDER BY TotalCount DESC
        """
        
        all_results = db.execute_query(all_status_query)
        
        # Query 3: Check Location field patterns for Dept 60
        location_patterns_query = f"""
        SELECT 
            CASE 
                WHEN UPPER(Location) LIKE '%SOLD%' THEN 'Contains SOLD'
                WHEN UPPER(Location) LIKE '%DISPOSED%' THEN 'Contains DISPOSED'
                WHEN UPPER(Location) LIKE '%SCRAP%' THEN 'Contains SCRAP'
                WHEN UPPER(Location) LIKE '%AUCTION%' THEN 'Contains AUCTION'
                WHEN UPPER(Location) LIKE '%TRANSFER%' THEN 'Contains TRANSFER'
                WHEN UPPER(Location) LIKE '%WAREHOUSE%' THEN 'Contains WAREHOUSE'
                WHEN UPPER(Location) LIKE '%SHOP%' THEN 'Contains SHOP'
                WHEN UPPER(Location) LIKE '%YARD%' THEN 'Contains YARD'
                WHEN Location IS NULL THEN 'NULL'
                WHEN Location = '' THEN 'EMPTY'
                ELSE 'Other'
            END as LocationPattern,
            COUNT(*) as Count,
            STRING_AGG(DISTINCT RentalStatus, ', ') as RelatedStatuses
        FROM {schema}.Equipment
        WHERE InventoryDept = 60
            AND (IsDeleted = 0 OR IsDeleted IS NULL)
        GROUP BY 
            CASE 
                WHEN UPPER(Location) LIKE '%SOLD%' THEN 'Contains SOLD'
                WHEN UPPER(Location) LIKE '%DISPOSED%' THEN 'Contains DISPOSED'
                WHEN UPPER(Location) LIKE '%SCRAP%' THEN 'Contains SCRAP'
                WHEN UPPER(Location) LIKE '%AUCTION%' THEN 'Contains AUCTION'
                WHEN UPPER(Location) LIKE '%TRANSFER%' THEN 'Contains TRANSFER'
                WHEN UPPER(Location) LIKE '%WAREHOUSE%' THEN 'Contains WAREHOUSE'
                WHEN UPPER(Location) LIKE '%SHOP%' THEN 'Contains SHOP'
                WHEN UPPER(Location) LIKE '%YARD%' THEN 'Contains YARD'
                WHEN Location IS NULL THEN 'NULL'
                WHEN Location = '' THEN 'EMPTY'
                ELSE 'Other'
            END
        ORDER BY Count DESC
        """
        
        location_results = db.execute_query(location_patterns_query)
        
        # Query 4: Sample problematic combinations
        problem_samples_query = f"""
        SELECT TOP 20
            UnitNo,
            SerialNo,
            RentalStatus,
            Location,
            Make,
            Model,
            RentalYTD,
            RentalITD,
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM {schema}.RentalHistory rh 
                    WHERE rh.SerialNo = e.SerialNo 
                    AND rh.Year = YEAR(GETDATE()) 
                    AND rh.Month = MONTH(GETDATE())
                    AND rh.DaysRented > 0
                    AND rh.DeletionTime IS NULL
                ) THEN 'Yes' ELSE 'No' 
            END as CurrentlyOnRent
        FROM {schema}.Equipment e
        WHERE InventoryDept = 60
            AND (IsDeleted = 0 OR IsDeleted IS NULL)
            AND (
                RentalStatus IN ('Sold', 'Disposed', 'Transferred')
                OR UPPER(Location) LIKE '%SOLD%'
                OR UPPER(Location) LIKE '%DISPOSED%'
                OR UPPER(Location) LIKE '%SCRAP%'
                OR UPPER(Location) LIKE '%AUCTION%'
            )
        ORDER BY RentalStatus, UnitNo
        """
        
        problem_samples = db.execute_query(problem_samples_query)
        
        # Build response
        response = {
            'success': True,
            'analysis': {
                'dept_60_rental_statuses': [],
                'all_rental_statuses': [],
                'location_patterns': [],
                'problem_samples': [],
                'recommendations': []
            }
        }
        
        # Process Dept 60 statuses
        if dept60_results:
            for row in dept60_results:
                response['analysis']['dept_60_rental_statuses'].append({
                    'status': row['RentalStatus'] or 'NULL',
                    'count': row['Count'],
                    'currently_on_rent': row['CurrentlyOnRent'],
                    'units_with_rates': row['UnitsWithRates'],
                    'avg_rental_ytd': float(row['AvgRentalYTD'] or 0),
                    'sample_units': [row['SampleUnit1'], row['SampleUnit2']],
                    'sample_location': row['SampleLocation']
                })
        
        # Process all statuses
        if all_results:
            for row in all_results:
                response['analysis']['all_rental_statuses'].append({
                    'status': row['RentalStatus'] or 'NULL',
                    'total_count': row['TotalCount'],
                    'department_count': row['DepartmentCount'],
                    'departments': row['Departments']
                })
        
        # Process location patterns
        if location_results:
            for row in location_results:
                response['analysis']['location_patterns'].append({
                    'pattern': row['LocationPattern'],
                    'count': row['Count'],
                    'related_statuses': row['RelatedStatuses']
                })
        
        # Process problem samples
        if problem_samples:
            for row in problem_samples:
                response['analysis']['problem_samples'].append({
                    'unit_no': row['UnitNo'],
                    'serial_no': row['SerialNo'],
                    'rental_status': row['RentalStatus'],
                    'location': row['Location'],
                    'make_model': f"{row['Make']} {row['Model']}",
                    'rental_ytd': float(row['RentalYTD'] or 0),
                    'rental_itd': float(row['RentalITD'] or 0),
                    'currently_on_rent': row['CurrentlyOnRent']
                })
        
        # Generate recommendations based on findings
        recommendations = []
        
        # Identify legitimate rental statuses
        legitimate_statuses = []
        problematic_statuses = []
        
        for status_info in response['analysis']['dept_60_rental_statuses']:
            status = status_info['status']
            if status in ['Sold', 'Disposed', 'Transferred']:
                problematic_statuses.append(f"{status} ({status_info['count']} units)")
            elif status_info['count'] > 0:
                legitimate_statuses.append(f"{status} ({status_info['count']} units)")
        
        if legitimate_statuses:
            recommendations.append(f"Legitimate RentalStatus values in Dept 60: {', '.join(legitimate_statuses)}")
        
        if problematic_statuses:
            recommendations.append(f"Problematic RentalStatus values to exclude: {', '.join(problematic_statuses)}")
        
        # Check location patterns
        problem_locations = [p for p in response['analysis']['location_patterns'] 
                           if p['pattern'] in ['Contains SOLD', 'Contains DISPOSED', 'Contains SCRAP', 'Contains AUCTION']]
        if problem_locations:
            total_problem = sum(p['count'] for p in problem_locations)
            recommendations.append(f"Found {total_problem} units with problematic location patterns")
        
        # Add filter recommendation
        recommendations.append("Suggested filter: InventoryDept = 60 AND RentalStatus NOT IN (identified problematic statuses)")
        
        response['analysis']['recommendations'] = recommendations
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error discovering rental statuses: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500