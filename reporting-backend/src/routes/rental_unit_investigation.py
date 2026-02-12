"""
Investigate specific rental units to debug status detection issues
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime

from flask_jwt_extended import get_jwt_identity
from src.utils.tenant_utils import get_tenant_db
from src.models.user import User

logger = logging.getLogger(__name__)

rental_investigation_bp = Blueprint('rental_investigation', __name__)

@rental_investigation_bp.route('/api/rental/investigate-units', methods=['GET'])
def investigate_units():
    """Investigate specific units to understand rental status issues"""
    
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Get unit numbers from query params or use defaults
        units = request.args.get('units', '21515,21728,21729').split(',')
        
        results = {}
        
        for unit_no in units:
            unit_no = unit_no.strip()
            unit_data = {}
            
            # 1. Check Equipment table
            equipment_query = f"""
            SELECT 
                UnitNo,
                SerialNo,
                Make,
                Model,
                CustomerNo,
                Customer as CustomerOwnedFlag,
                RentalStatus,
                Location,
                InventoryDept,
                DayRent,
                WeekRent,
                MonthRent
            FROM {schema}.Equipment
            WHERE UnitNo = '{unit_no}'
            """
            
            equipment = db.execute_query(equipment_query)
            if equipment:
                unit_data['equipment'] = equipment[0]
                serial_no = equipment[0].get('SerialNo', '')
            else:
                unit_data['equipment'] = None
                results[unit_no] = unit_data
                continue
                
            # 2. Check current month RentalHistory
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            rental_history_query = f"""
            SELECT 
                SerialNo,
                UnitNo,
                Year,
                Month,
                DaysRented,
                RentAmount,
                CustomerNo,
                DeletionTime
            FROM {schema}.RentalHistory
            WHERE (UnitNo = '{unit_no}' OR SerialNo = '{serial_no}')
            AND Year = {current_year}
            AND Month = {current_month}
            """
            
            unit_data['current_month_rental'] = db.execute_query(rental_history_query)
            
            # 3. Check last 3 months rental history
            history_query = f"""
            SELECT 
                Year,
                Month,
                DaysRented,
                RentAmount,
                CustomerNo,
                DeletionTime
            FROM {schema}.RentalHistory
            WHERE (UnitNo = '{unit_no}' OR SerialNo = '{serial_no}')
            AND ((Year = {current_year} AND Month >= {max(1, current_month - 2)})
                 OR (Year = {current_year - 1} AND Month >= {current_month + 10}))
            ORDER BY Year DESC, Month DESC
            """
            
            unit_data['recent_rental_history'] = db.execute_query(history_query)
            
            # 4. Check recent WORental records
            wo_rental_query = f"""
            SELECT TOP 10
                wr.WONo,
                wr.SerialNo,
                wr.UnitNo,
                wo.Type,
                wo.OpenDate,
                wo.CompletedDate,
                wo.ClosedDate,
                wo.RentalContractNo,
                wo.BillTo,
                c.Name as CustomerName
            FROM {schema}.WORental wr
            JOIN {schema}.WO wo ON wr.WONo = wo.WONo
            LEFT JOIN {schema}.Customer c ON wo.BillTo = c.Number
            WHERE (wr.UnitNo = '{unit_no}' OR wr.SerialNo = '{serial_no}')
            ORDER BY wo.OpenDate DESC
            """
            
            unit_data['recent_work_orders'] = db.execute_query(wo_rental_query)
            
            # 5. Check for open rental WOs
            open_wo_query = f"""
            SELECT 
                wr.WONo,
                wo.Type,
                wo.OpenDate,
                wo.RentalContractNo,
                wo.BillTo,
                c.Name as CustomerName
            FROM {schema}.WORental wr
            JOIN {schema}.WO wo ON wr.WONo = wo.WONo
            LEFT JOIN {schema}.Customer c ON wo.BillTo = c.Number
            WHERE (wr.UnitNo = '{unit_no}' OR wr.SerialNo = '{serial_no}')
            AND wo.ClosedDate IS NULL
            AND wo.Type = 'R'
            """
            
            unit_data['open_rental_work_orders'] = db.execute_query(open_wo_query)
            
            # 6. For units 21728/21729, check for document 16001378
            if unit_no in ['21728', '21729']:
                doc_query = f"""
                SELECT 
                    wo.WONo,
                    wo.Type,
                    wo.OpenDate,
                    wo.ClosedDate,
                    wo.BillTo,
                    c.Name as CustomerName,
                    wr.UnitNo,
                    wr.SerialNo
                FROM {schema}.WO wo
                LEFT JOIN {schema}.WORental wr ON wo.WONo = wr.WONo
                LEFT JOIN {schema}.Customer c ON wo.BillTo = c.Number
                WHERE wo.WONo LIKE '%16001378%'
                OR wo.RentalContractNo = '16001378'
                """
                
                unit_data['document_16001378'] = db.execute_query(doc_query)
                
            # 7. Apply the same logic as the availability report to determine status
            availability_logic_query = f"""
            SELECT 
                e.UnitNo,
                CASE 
                    WHEN rh.SerialNo IS NOT NULL AND rh.DaysRented > 0 THEN 'On Rent (per RentalHistory)'
                    WHEN e.RentalStatus = 'Hold' THEN 'Hold'
                    ELSE 'Available (per logic)'
                END as CalculatedStatus,
                rh.DaysRented as CurrentMonthDaysRented,
                rh.RentAmount as CurrentMonthRentAmount
            FROM {schema}.Equipment e
            LEFT JOIN {schema}.RentalHistory rh ON e.SerialNo = rh.SerialNo 
                AND rh.Year = {current_year}
                AND rh.Month = {current_month}
                AND rh.DaysRented > 0
                AND rh.DeletionTime IS NULL
            WHERE e.UnitNo = '{unit_no}'
            AND e.InventoryDept = 60
            AND (e.Customer = 0 OR e.Customer IS NULL)
            """
            
            unit_data['availability_logic_result'] = db.execute_query(availability_logic_query)
            
            results[unit_no] = unit_data
            
        return jsonify({
            'success': True,
            'investigation_date': datetime.now().isoformat(),
            'current_month': datetime.now().strftime('%B %Y'),
            'units': results
        })
        
    except Exception as e:
        logger.error(f"Error investigating rental units: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500