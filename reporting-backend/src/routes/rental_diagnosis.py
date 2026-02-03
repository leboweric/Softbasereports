from flask import jsonify, request
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db
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

@reports_bp.route('/departments/rental/diagnose-equipment', methods=['GET'])
@jwt_required()
def diagnose_rental_equipment():
    """Diagnose why specific equipment shows RENTAL FLEET instead of actual customer"""
    try:
        db = get_tenant_db()
        
        # Test with specific serial numbers that are showing RENTAL FLEET
        test_serials = ['99W15913', '103274', '95U8371', '30001912', 'H2X335R05931']
        
        results = {
            'equipment_details': [],
            'rental_contracts': [],
            'work_orders': [],
            'analysis': {}
        }
        
        # 1. Get equipment details
        for serial in test_serials:
            try:
                schema = get_tenant_schema()

                query = f"""
                SELECT 
                    e.SerialNo,
                    e.UnitNo,
                    e.Make,
                    e.Model,
                    e.CustomerNo,
                    c.Name as CustomerName,
                    e.RentalStatus,
                    rh.DaysRented,
                    rh.RentAmount
                FROM {schema}.Equipment e
                LEFT JOIN {schema}.Customer c ON e.CustomerNo = c.Number
                LEFT JOIN {schema}.RentalHistory rh ON e.SerialNo = rh.SerialNo
                    AND rh.Year = YEAR(GETDATE())
                    AND rh.Month = MONTH(GETDATE())
                WHERE e.SerialNo = %s
                """
                result = db.execute_query(query, [serial])
                if result:
                    results['equipment_details'].append(result[0])
            except Exception as e:
                results['equipment_details'].append({'serial': serial, 'error': str(e)})
        
        # 2. Check for rental contracts via WO
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT 
                wo.SerialNo,
                wo.UnitNo,
                wo.WONo,
                wo.Type,
                wo.RentalContractNo,
                wo.BillTo,
                c.Name as BillToName,
                wo.ShipTo,
                wo.ShipName,
                wo.OpenDate,
                wo.ClosedDate,
                rc.StartDate as ContractStart,
                rc.EndDate as ContractEnd
            FROM {schema}.WO wo
            LEFT JOIN {schema}.Customer c ON wo.BillTo = c.Number
            LEFT JOIN {schema}.RentalContract rc ON wo.RentalContractNo = rc.RentalContractNo
            WHERE wo.SerialNo IN (%s)
            AND wo.RentalContractNo IS NOT NULL
            ORDER BY wo.OpenDate DESC
            """ % ','.join(['%s'] * len(test_serials))
            
            result = db.execute_query(query, test_serials)
            results['rental_contracts'] = result if result else []
        except Exception as e:
            results['rental_contracts'] = f"Error: {str(e)}"
        
        # 3. Check ALL work orders for these serials
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT TOP 50
                wo.SerialNo,
                wo.UnitNo,
                wo.WONo,
                wo.Type,
                wo.RentalContractNo,
                wo.BillTo,
                c.Name as BillToName,
                wo.OpenDate,
                wo.ClosedDate
            FROM {schema}.WO wo
            LEFT JOIN {schema}.Customer c ON wo.BillTo = c.Number
            WHERE wo.SerialNo IN (%s)
            OR wo.UnitNo IN (
                SELECT UnitNo FROM {schema}.Equipment 
                WHERE SerialNo IN (%s)
            )
            ORDER BY wo.OpenDate DESC
            """ % (','.join(['%s'] * len(test_serials)), ','.join(['%s'] * len(test_serials)))
            
            result = db.execute_query(query, test_serials + test_serials)
            results['work_orders'] = result if result else []
        except Exception as e:
            results['work_orders'] = f"Error: {str(e)}"
        
        # 4. Analysis - why are we not finding the customer?
        analysis = []
        
        # Check if any equipment has rental contracts
        if isinstance(results['rental_contracts'], list):
            contracts_count = len(results['rental_contracts'])
            if contracts_count == 0:
                analysis.append("❌ NO rental contracts found via WO.RentalContractNo for these serial numbers")
                analysis.append("This means Work Orders don't have RentalContractNo populated")
            else:
                analysis.append(f"✅ Found {contracts_count} rental contracts via WO table")
        
        # Check if work orders exist but without RentalContractNo
        if isinstance(results['work_orders'], list):
            wo_count = len(results['work_orders'])
            wo_with_contract = sum(1 for wo in results['work_orders'] if wo.get('RentalContractNo'))
            if wo_count > 0 and wo_with_contract == 0:
                analysis.append(f"⚠️ Found {wo_count} work orders but NONE have RentalContractNo populated")
                analysis.append("🔴 This is why we can't link to actual customers - WO.RentalContractNo is NULL")
                analysis.append("The field exists but is not being populated when creating rental work orders")
            elif wo_count > 0 and wo_with_contract > 0:
                analysis.append(f"Found {wo_with_contract} of {wo_count} work orders with RentalContractNo")
        
        # Check if equipment CustomerNo is RENTAL FLEET
        rental_fleet_count = 0
        for equip in results['equipment_details']:
            if isinstance(equip, dict) and 'CustomerName' in equip:
                if 'RENTAL FLEET' in str(equip.get('CustomerName', '')):
                    rental_fleet_count += 1
        
        if rental_fleet_count > 0:
            analysis.append(f"⚠️ {rental_fleet_count} equipment records have CustomerNo = RENTAL FLEET account")
        
        # KEY FINDING
        analysis.append("🔑 KEY FINDING: The RentalContract → WO → Customer linkage only works if:")
        analysis.append("1. Work Orders have RentalContractNo populated (currently NOT happening)")
        analysis.append("2. RentalContract records exist and are active")
        analysis.append("3. Without RentalContractNo in WO, we cannot determine actual rental customer")
        
        results['analysis'] = analysis
        
        # 5. Alternative approach - check WORental table
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT TOP 20
                wr.SerialNo,
                wr.UnitNo,
                wr.WONo,
                wo.RentalContractNo,
                wo.BillTo,
                c.Name as BillToName,
                wo.Type
            FROM {schema}.WORental wr
            INNER JOIN {schema}.WO wo ON wr.WONo = wo.WONo
            LEFT JOIN {schema}.Customer c ON wo.BillTo = c.Number
            WHERE wr.SerialNo IN (%s)
            OR wr.UnitNo IN (
                SELECT UnitNo FROM {schema}.Equipment 
                WHERE SerialNo IN (%s)
            )
            """ % (','.join(['%s'] * len(test_serials)), ','.join(['%s'] * len(test_serials)))
            
            result = db.execute_query(query, test_serials + test_serials)
            results['worental_records'] = result if result else []
            
            if result and len(result) > 0:
                analysis.append(f"Found {len(result)} records in WORental table - alternative data source")
        except Exception as e:
            results['worental_records'] = f"Error: {str(e)}"
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in rental diagnosis: {str(e)}")
        return jsonify({'error': str(e)}), 500