from flask import jsonify
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db
from src.routes.reports import reports_bp
import logging

from flask_jwt_extended import get_jwt_identity
from src.models.user import User

logger = logging.getLogger(__name__)

@reports_bp.route('/departments/rental/customer-solution', methods=['GET'])
@jwt_required()
def rental_customer_solution():
    """Properly link rental equipment to actual customers using the discovered WO.RentalContractNo field"""
    try:
        db = get_tenant_db()
        results = {}
        
        # 1. Test the discovered linkage: RentalContract -> WO -> Customer
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT TOP 10
                rc.RentalContractNo,
                rc.StartDate,
                rc.EndDate,
                wo.WONo,
                wo.BillTo as CustomerNo,
                c.Name as CustomerName,
                wo.ShipTo as ShipToCustomer,
                wo.ShipName,
                wo.UnitNo,
                wo.SerialNo as WOSerialNo
            FROM {schema}.RentalContract rc
            INNER JOIN {schema}.WO wo ON rc.RentalContractNo = wo.RentalContractNo
            LEFT JOIN {schema}.Customer c ON wo.BillTo = c.Number
            WHERE (rc.EndDate IS NULL OR rc.EndDate > GETDATE())
            ORDER BY rc.StartDate DESC
            """
            results['active_rentals_with_customers'] = db.execute_query(query)
        except Exception as e:
            results['active_rentals_with_customers'] = str(e)
        
        # 2. Find equipment currently on rent with proper customer info
        try:
            schema = get_tenant_schema()

            query = f"""
            WITH CurrentRentals AS (
                -- Equipment that's currently rented (has rental history this month)
                SELECT DISTINCT 
                    rh.SerialNo,
                    rh.DaysRented,
                    rh.RentAmount
                FROM {schema}.RentalHistory rh
                WHERE rh.Year = YEAR(GETDATE())
                AND rh.Month = MONTH(GETDATE())
                AND rh.DaysRented > 0
            ),
            RentalCustomers AS (
                -- Get customer info from RentalContract -> WO -> Customer
                SELECT 
                    wo.SerialNo,
                    wo.UnitNo,
                    rc.RentalContractNo,
                    wo.WONo,
                    wo.BillTo as CustomerNo,
                    c.Name as CustomerName,
                    wo.ShipTo as ShipToCustomer,
                    wo.ShipName,
                    rc.StartDate,
                    rc.EndDate
                FROM {schema}.RentalContract rc
                INNER JOIN {schema}.WO wo ON rc.RentalContractNo = wo.RentalContractNo
                LEFT JOIN {schema}.Customer c ON wo.BillTo = c.Number
                WHERE (rc.EndDate IS NULL OR rc.EndDate > GETDATE())
                AND wo.SerialNo IS NOT NULL
            )
            SELECT TOP 20
                e.UnitNo,
                e.SerialNo,
                e.Make,
                e.Model,
                e.CustomerNo as EquipmentCustomerNo,
                COALESCE(rc.CustomerNo, e.CustomerNo) as ActualCustomerNo,
                COALESCE(rc.CustomerName, c2.Name, 'UNKNOWN') as ActualCustomerName,
                rc.RentalContractNo,
                rc.WONo,
                cr.DaysRented,
                cr.RentAmount,
                e.Location
            FROM CurrentRentals cr
            INNER JOIN {schema}.Equipment e ON cr.SerialNo = e.SerialNo
            LEFT JOIN RentalCustomers rc ON e.SerialNo = rc.SerialNo
            LEFT JOIN {schema}.Customer c2 ON e.CustomerNo = c2.Number
            ORDER BY cr.RentAmount DESC
            """
            results['current_rentals_fixed'] = db.execute_query(query)
        except Exception as e:
            results['current_rentals_fixed'] = str(e)
        
        # 3. Check how many rental contracts have associated work orders
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT 
                COUNT(DISTINCT rc.RentalContractNo) as TotalContracts,
                COUNT(DISTINCT wo.RentalContractNo) as ContractsWithWO,
                COUNT(DISTINCT CASE WHEN wo.BillTo IS NOT NULL THEN rc.RentalContractNo END) as ContractsWithCustomer
            FROM {schema}.RentalContract rc
            LEFT JOIN {schema}.WO wo ON rc.RentalContractNo = wo.RentalContractNo
            WHERE (rc.EndDate IS NULL OR rc.EndDate > GETDATE())
            """
            results['contract_coverage'] = db.execute_query(query)
        except Exception as e:
            results['contract_coverage'] = str(e)
        
        # 4. Find rental work orders with equipment info
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT TOP 10
                wo.WONo,
                wo.Type,
                wo.RentalContractNo,
                wo.BillTo as CustomerNo,
                c.Name as CustomerName,
                wo.UnitNo,
                wo.SerialNo,
                wo.Make,
                wo.Model,
                wr.SerialNo as WORentalSerialNo,
                wr.UnitNo as WORentalUnitNo
            FROM {schema}.WO wo
            LEFT JOIN {schema}.Customer c ON wo.BillTo = c.Number
            LEFT JOIN {schema}.WORental wr ON wo.WONo = wr.WONo
            WHERE wo.RentalContractNo IS NOT NULL
            AND wo.RentalContractNo > 0
            ORDER BY wo.OpenDate DESC
            """
            results['rental_work_orders'] = db.execute_query(query)
        except Exception as e:
            results['rental_work_orders'] = str(e)
        
        # 5. Alternative approach using WORental table
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT TOP 10
                wr.WONo,
                wr.SerialNo,
                wr.UnitNo,
                wr.Make,
                wr.Model,
                wo.RentalContractNo,
                wo.BillTo as CustomerNo,
                c.Name as CustomerName,
                wo.ShipTo,
                wo.ShipName,
                wr.DayRent,
                wr.MonthRent
            FROM {schema}.WORental wr
            INNER JOIN {schema}.WO wo ON wr.WONo = wo.WONo
            LEFT JOIN {schema}.Customer c ON wo.BillTo = c.Number
            WHERE wo.RentalContractNo IS NOT NULL
            ORDER BY wo.OpenDate DESC
            """
            results['worental_with_customers'] = db.execute_query(query)
        except Exception as e:
            results['worental_with_customers'] = str(e)
        
        # 6. Summary of findings
        try:
            schema = get_tenant_schema()

            query = f"""
            -- Count different scenarios
            SELECT 
                'Total Active Rental Contracts' as Metric,
                COUNT(*) as Count
            FROM {schema}.RentalContract
            WHERE (EndDate IS NULL OR EndDate > GETDATE())
            
            UNION ALL
            
            SELECT 
                'Contracts with Work Orders' as Metric,
                COUNT(DISTINCT rc.RentalContractNo) as Count
            FROM {schema}.RentalContract rc
            INNER JOIN {schema}.WO wo ON rc.RentalContractNo = wo.RentalContractNo
            WHERE (rc.EndDate IS NULL OR rc.EndDate > GETDATE())
            
            UNION ALL
            
            SELECT 
                'Equipment Currently Rented' as Metric,
                COUNT(DISTINCT SerialNo) as Count
            FROM {schema}.RentalHistory
            WHERE Year = YEAR(GETDATE())
            AND Month = MONTH(GETDATE())
            AND DaysRented > 0
            
            UNION ALL
            
            SELECT 
                'Rental WOs with Equipment' as Metric,
                COUNT(DISTINCT wo.WONo) as Count
            FROM {schema}.WO wo
            WHERE wo.RentalContractNo IS NOT NULL
            AND wo.SerialNo IS NOT NULL
            """
            results['summary_metrics'] = db.execute_query(query)
        except Exception as e:
            results['summary_metrics'] = str(e)
            
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in rental customer solution: {str(e)}")
        return jsonify({'error': str(e)}), 500