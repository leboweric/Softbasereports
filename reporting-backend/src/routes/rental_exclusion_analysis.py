"""
Endpoint to analyze why certain units that should be excluded were appearing
in the rental availability report.
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
import logging
from src.services.azure_sql_service import AzureSQLService

logger = logging.getLogger(__name__)

rental_exclusion_analysis_bp = Blueprint('rental_exclusion_analysis', __name__)

@rental_exclusion_analysis_bp.route('/api/rental/analyze-excluded-units', methods=['GET'])
@jwt_required()
def analyze_excluded_units():
    """Analyze the units that should be excluded to understand their characteristics."""
    
    try:
        db = AzureSQLService()
        
        # Units that should be excluded
        excluded_units = {
            'Not a Rental Unit': ['293060', '218919', 'Z452512A-43084', '21775', 'SER01'],
            'Sold Unit': ['15597', '17004', '17295B', '17636', '18552', '18808', '18823',
                          '18835', '18838B', '18993B', '19060', '19063', '19306B', '19321B',
                          '19332', '19420', '19421', '19463B', '19628B', '19752B', '19809B',
                          '19890', '20134', '20134B', '20457', '20868B'],
            'Transferred to Used/Sold Unit': ['19645B', '19950B'],
            'Rerent Unit - Should not be in inventory': ['RTRSEL']
        }
        
        # Combine all units
        all_excluded = []
        for units in excluded_units.values():
            all_excluded.extend(units)
        
        # Create SQL IN clause
        units_list = "', '".join(all_excluded)
        
        # Query to analyze these units
        query = f"""
        SELECT 
            e.UnitNo,
            e.SerialNo,
            e.Make,
            e.Model,
            e.ModelYear,
            e.RentalStatus,
            e.InventoryDept,
            e.Location,
            e.CustomerNo,
            c.Name as CustomerName,
            e.DayRent,
            e.WeekRent,
            e.MonthRent,
            e.WebRentalFlag,
            e.IsDeleted,
            e.DeletionTime,
            e.Cost,
            e.Sell,
            e.RentalYTD,
            e.RentalITD,
            -- Check if in RentalHistory
            CASE WHEN rh.SerialNo IS NOT NULL THEN 1 ELSE 0 END as InRentalHistory,
            rh.DaysRented,
            rh.RentAmount,
            -- Check for EquipmentRemoved view indicators
            CASE 
                WHEN e.RentalStatus = 'Sold' THEN 'Sold Status'
                WHEN e.RentalStatus = 'Disposed' THEN 'Disposed Status'
                WHEN e.RentalStatus = 'Transferred' THEN 'Transferred Status'
                WHEN e.Location LIKE '%SOLD%' THEN 'SOLD in Location'
                WHEN e.Location LIKE '%DISPOSED%' THEN 'DISPOSED in Location'
                WHEN e.Location LIKE '%TRANSFER%' THEN 'TRANSFER in Location'
                WHEN e.IsDeleted = 1 THEN 'IsDeleted Flag'
                WHEN e.DeletionTime IS NOT NULL THEN 'Has DeletionTime'
                ELSE 'None'
            END as RemovalIndicator,
            -- Why it passed our filter
            CASE
                WHEN e.RentalStatus IN ('Ready To Rent', 'Hold') THEN 'RentalStatus: ' + e.RentalStatus
                WHEN rh.SerialNo IS NOT NULL AND rh.DaysRented > 0 THEN 'In RentalHistory'
                WHEN e.InventoryDept = 60 THEN 'InventoryDept = 60'
                ELSE 'Unknown'
            END as WhyIncluded
        FROM ben002.Equipment e
        LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
        LEFT JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo 
            AND rh.Year = YEAR(GETDATE()) 
            AND rh.Month = MONTH(GETDATE())
            AND rh.DeletionTime IS NULL
        WHERE e.UnitNo IN ('{units_list}')
        ORDER BY 
            CASE 
                WHEN e.RentalStatus = 'Sold' THEN 1
                WHEN e.RentalStatus = 'Disposed' THEN 2
                WHEN e.RentalStatus = 'Transferred' THEN 3
                ELSE 4
            END,
            e.UnitNo
        """
        
        result = db.execute_query(query)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'No data found for excluded units'
            }), 404
        
        # Process results
        analysis = {
            'units_by_reason': {},
            'summary': {
                'total_units': len(result),
                'by_rental_status': {},
                'by_inventory_dept': {},
                'by_removal_indicator': {},
                'by_inclusion_reason': {}
            },
            'detailed_units': []
        }
        
        # Group by exclusion reason
        for reason, units in excluded_units.items():
            analysis['units_by_reason'][reason] = []
            
            for row in result:
                if row['UnitNo'] in units:
                    unit_info = {
                        'unit_no': row['UnitNo'],
                        'serial_no': row['SerialNo'],
                        'make_model': f"{row['Make']} {row['Model']} ({row['ModelYear']})",
                        'rental_status': row['RentalStatus'],
                        'inventory_dept': row['InventoryDept'],
                        'location': row['Location'],
                        'customer': f"{row['CustomerNo']} - {row['CustomerName']}",
                        'rental_rates': {
                            'day': float(row['DayRent'] or 0),
                            'week': float(row['WeekRent'] or 0),
                            'month': float(row['MonthRent'] or 0)
                        },
                        'web_rental_flag': row['WebRentalFlag'],
                        'is_deleted': row['IsDeleted'],
                        'deletion_time': str(row['DeletionTime']) if row['DeletionTime'] else None,
                        'rental_ytd': float(row['RentalYTD'] or 0),
                        'rental_itd': float(row['RentalITD'] or 0),
                        'in_rental_history': bool(row['InRentalHistory']),
                        'days_rented': row['DaysRented'],
                        'rent_amount': float(row['RentAmount'] or 0) if row['RentAmount'] else None,
                        'removal_indicator': row['RemovalIndicator'],
                        'why_included': row['WhyIncluded']
                    }
                    analysis['units_by_reason'][reason].append(unit_info)
        
        # Calculate summary statistics
        for row in result:
            # Rental Status
            status = row['RentalStatus'] or 'NULL'
            if status not in analysis['summary']['by_rental_status']:
                analysis['summary']['by_rental_status'][status] = 0
            analysis['summary']['by_rental_status'][status] += 1
            
            # Inventory Dept
            dept = str(row['InventoryDept'] or 'NULL')
            if dept not in analysis['summary']['by_inventory_dept']:
                analysis['summary']['by_inventory_dept'][dept] = 0
            analysis['summary']['by_inventory_dept'][dept] += 1
            
            # Removal Indicator
            removal = row['RemovalIndicator']
            if removal not in analysis['summary']['by_removal_indicator']:
                analysis['summary']['by_removal_indicator'][removal] = 0
            analysis['summary']['by_removal_indicator'][removal] += 1
            
            # Why Included
            why = row['WhyIncluded']
            if why not in analysis['summary']['by_inclusion_reason']:
                analysis['summary']['by_inclusion_reason'][why] = 0
            analysis['summary']['by_inclusion_reason'][why] += 1
            
            # Add to detailed list
            analysis['detailed_units'].append({
                'unit_no': row['UnitNo'],
                'rental_status': row['RentalStatus'],
                'inventory_dept': row['InventoryDept'],
                'removal_indicator': row['RemovalIndicator'],
                'why_included': row['WhyIncluded']
            })
        
        # Identify patterns
        patterns = []
        
        # Check if most are from wrong department
        dept_60_count = analysis['summary']['by_inventory_dept'].get('60', 0)
        if dept_60_count > len(result) * 0.5:
            patterns.append(f"Most units ({dept_60_count}/{len(result)}) have InventoryDept=60 despite being sold/non-rental")
        
        # Check RentalStatus patterns
        sold_count = analysis['summary']['by_rental_status'].get('Sold', 0)
        if sold_count > 0:
            patterns.append(f"{sold_count} units have RentalStatus='Sold' but still passed filter")
        
        # Check removal indicators
        if analysis['summary']['by_removal_indicator'].get('None', 0) < len(result):
            patterns.append("Some units have clear removal indicators that should be used for filtering")
        
        analysis['patterns'] = patterns
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error analyzing excluded units: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500