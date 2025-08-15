from flask import jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
from src.routes.reports import reports_bp
import logging

logger = logging.getLogger(__name__)

@reports_bp.route('/departments/rental/customer-solution', methods=['GET'])
@jwt_required()
def rental_customer_solution():
    """Properly link rental equipment to actual customers using the discovered WO.RentalContractNo field"""
    try:
        db = AzureSQLService()
        results = {}
        
        # 1. Test the discovered linkage: RentalContract -> WO -> Customer
        try:
            query = """
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
            FROM ben002.RentalContract rc
            INNER JOIN ben002.WO wo ON rc.RentalContractNo = wo.RentalContractNo
            LEFT JOIN ben002.Customer c ON wo.BillTo = c.Number
            WHERE (rc.EndDate IS NULL OR rc.EndDate > GETDATE())
            ORDER BY rc.StartDate DESC
            """
            results['active_rentals_with_customers'] = db.execute_query(query)
        except Exception as e:
            results['active_rentals_with_customers'] = str(e)
        
        # 2. Find equipment currently on rent with proper customer info
        try:
            query = """
            WITH CurrentRentals AS (
                -- Equipment that's currently rented (has rental history this month)
                SELECT DISTINCT 
                    rh.SerialNo,
                    rh.DaysRented,
                    rh.RentAmount
                FROM ben002.RentalHistory rh
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
                FROM ben002.RentalContract rc
                INNER JOIN ben002.WO wo ON rc.RentalContractNo = wo.RentalContractNo
                LEFT JOIN ben002.Customer c ON wo.BillTo = c.Number
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
            INNER JOIN ben002.Equipment e ON cr.SerialNo = e.SerialNo
            LEFT JOIN RentalCustomers rc ON e.SerialNo = rc.SerialNo
            LEFT JOIN ben002.Customer c2 ON e.CustomerNo = c2.Number
            ORDER BY cr.RentAmount DESC
            """
            results['current_rentals_fixed'] = db.execute_query(query)
        except Exception as e:
            results['current_rentals_fixed'] = str(e)
        
        # 3. Check how many rental contracts have associated work orders
        try:
            query = """
            SELECT 
                COUNT(DISTINCT rc.RentalContractNo) as TotalContracts,
                COUNT(DISTINCT wo.RentalContractNo) as ContractsWithWO,
                COUNT(DISTINCT CASE WHEN wo.BillTo IS NOT NULL THEN rc.RentalContractNo END) as ContractsWithCustomer
            FROM ben002.RentalContract rc
            LEFT JOIN ben002.WO wo ON rc.RentalContractNo = wo.RentalContractNo
            WHERE (rc.EndDate IS NULL OR rc.EndDate > GETDATE())
            """
            results['contract_coverage'] = db.execute_query(query)
        except Exception as e:
            results['contract_coverage'] = str(e)
        
        # 4. Find rental work orders with equipment info
        try:
            query = """
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
            FROM ben002.WO wo
            LEFT JOIN ben002.Customer c ON wo.BillTo = c.Number
            LEFT JOIN ben002.WORental wr ON wo.WONo = wr.WONo
            WHERE wo.RentalContractNo IS NOT NULL
            AND wo.RentalContractNo > 0
            ORDER BY wo.OpenDate DESC
            """
            results['rental_work_orders'] = db.execute_query(query)
        except Exception as e:
            results['rental_work_orders'] = str(e)
        
        # 5. Alternative approach using WORental table
        try:
            query = """
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
            FROM ben002.WORental wr
            INNER JOIN ben002.WO wo ON wr.WONo = wo.WONo
            LEFT JOIN ben002.Customer c ON wo.BillTo = c.Number
            WHERE wo.RentalContractNo IS NOT NULL
            ORDER BY wo.OpenDate DESC
            """
            results['worental_with_customers'] = db.execute_query(query)
        except Exception as e:
            results['worental_with_customers'] = str(e)
        
        # 6. Summary of findings
        try:
            query = """
            -- Count different scenarios
            SELECT 
                'Total Active Rental Contracts' as Metric,
                COUNT(*) as Count
            FROM ben002.RentalContract
            WHERE (EndDate IS NULL OR EndDate > GETDATE())
            
            UNION ALL
            
            SELECT 
                'Contracts with Work Orders' as Metric,
                COUNT(DISTINCT rc.RentalContractNo) as Count
            FROM ben002.RentalContract rc
            INNER JOIN ben002.WO wo ON rc.RentalContractNo = wo.RentalContractNo
            WHERE (rc.EndDate IS NULL OR rc.EndDate > GETDATE())
            
            UNION ALL
            
            SELECT 
                'Equipment Currently Rented' as Metric,
                COUNT(DISTINCT SerialNo) as Count
            FROM ben002.RentalHistory
            WHERE Year = YEAR(GETDATE())
            AND Month = MONTH(GETDATE())
            AND DaysRented > 0
            
            UNION ALL
            
            SELECT 
                'Rental WOs with Equipment' as Metric,
                COUNT(DISTINCT wo.WONo) as Count
            FROM ben002.WO wo
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