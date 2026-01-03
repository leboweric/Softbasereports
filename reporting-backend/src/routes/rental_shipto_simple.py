from flask import jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
from src.routes.reports import reports_bp
import logging

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

@reports_bp.route('/departments/rental/shipto-simple', methods=['GET'])
@jwt_required()
def simple_rental_research():
    """Simple research to find rental customer relationships"""
    try:
        db = AzureSQLService()
        schema = get_tenant_schema()
        results = {}
        
        # 1. Just check if RentalContract table exists and has data
        try:
            query1 = """
            SELECT COUNT(*) as contract_count 
            FROM {schema}.RentalContract
            """
            result = db.execute_query(query1)
            results['rental_contracts_exist'] = result[0]['contract_count'] if result else 0
        except Exception as e:
            results['rental_contracts_exist'] = f"Error: {str(e)}"
        
        # 2. Check for rental work orders
        try:
            query2 = """
            SELECT COUNT(*) as rental_wo_count
            FROM {schema}.WO
            WHERE Type = 'R'
            """
            result = db.execute_query(query2)
            results['rental_work_orders'] = result[0]['rental_wo_count'] if result else 0
        except Exception as e:
            results['rental_work_orders'] = f"Error: {str(e)}"
        
        # 3. Check a sample rental work order
        try:
            query3 = """
            SELECT TOP 1
                WONo,
                Type,
                BillTo,
                ShipTo,
                UnitNo
            FROM {schema}.WO
            WHERE Type = 'R'
            ORDER BY OpenDate DESC
            """
            result = db.execute_query(query3)
            if result:
                results['sample_rental_wo'] = {
                    'WONo': result[0].get('WONo'),
                    'BillTo': result[0].get('BillTo'),
                    'ShipTo': result[0].get('ShipTo'),
                    'UnitNo': result[0].get('UnitNo')
                }
            else:
                results['sample_rental_wo'] = None
        except Exception as e:
            results['sample_rental_wo'] = f"Error: {str(e)}"
        
        # 4. Check equipment with rental status
        try:
            query4 = """
            SELECT TOP 1
                UnitNo,
                SerialNo,
                CustomerNo,
                RentalStatus
            FROM {schema}.Equipment
            WHERE RentalStatus IS NOT NULL
            AND RentalStatus != ''
            """
            result = db.execute_query(query4)
            if result:
                results['sample_equipment'] = {
                    'UnitNo': result[0].get('UnitNo'),
                    'SerialNo': result[0].get('SerialNo'),
                    'CustomerNo': result[0].get('CustomerNo'),
                    'RentalStatus': result[0].get('RentalStatus')
                }
            else:
                results['sample_equipment'] = None
        except Exception as e:
            results['sample_equipment'] = f"Error: {str(e)}"
        
        # 5. Find equipment currently on rent and trace it
        try:
            query5 = """
            SELECT TOP 1
                e.UnitNo,
                e.SerialNo,
                e.CustomerNo as EquipmentCustomer,
                e.RentalStatus,
                rh.DaysRented,
                rh.RentAmount
            FROM {schema}.Equipment e
            INNER JOIN {schema}.RentalHistory rh ON e.SerialNo = rh.SerialNo
            WHERE rh.Year = YEAR(GETDATE())
            AND rh.Month = MONTH(GETDATE())
            AND rh.DaysRented > 0
            """
            result = db.execute_query(query5)
            if result:
                unit_no = result[0].get('UnitNo')
                serial_no = result[0].get('SerialNo')
                
                results['on_rent_equipment'] = {
                    'UnitNo': unit_no,
                    'SerialNo': serial_no,
                    'EquipmentCustomer': result[0].get('EquipmentCustomer'),
                    'RentalStatus': result[0].get('RentalStatus'),
                    'DaysRented': result[0].get('DaysRented')
                }
                
                # Now find related records
                if serial_no:
                    # Check RentalContract
                    try:
                        contract_query = f"""
                        SELECT TOP 1
                            RentalContractNo,
                            CustomerNo,
                            StartDate,
                            EndDate
                        FROM {schema}.RentalContract
                        WHERE SerialNo = '{serial_no}'
                        ORDER BY StartDate DESC
                        """
                        contract_result = db.execute_query(contract_query)
                        if contract_result:
                            results['related_contract'] = {
                                'RentalContractNo': contract_result[0].get('RentalContractNo'),
                                'CustomerNo': contract_result[0].get('CustomerNo')
                            }
                    except:
                        results['related_contract'] = None
                    
                    # Check Work Order
                    if unit_no:
                        try:
                            wo_query = f"""
                            SELECT TOP 1
                                WONo,
                                BillTo,
                                ShipTo,
                                Type
                            FROM {schema}.WO
                            WHERE UnitNo = '{unit_no}'
                            AND Type = 'R'
                            ORDER BY OpenDate DESC
                            """
                            wo_result = db.execute_query(wo_query)
                            if wo_result:
                                results['related_work_order'] = {
                                    'WONo': wo_result[0].get('WONo'),
                                    'BillTo': wo_result[0].get('BillTo'),
                                    'ShipTo': wo_result[0].get('ShipTo')
                                }
                        except:
                            results['related_work_order'] = None
            else:
                results['on_rent_equipment'] = "No equipment currently on rent found"
        except Exception as e:
            results['on_rent_equipment'] = f"Error: {str(e)}"
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in simple rental research: {str(e)}")
        return jsonify({'error': str(e), 'type': 'main_error'}), 500