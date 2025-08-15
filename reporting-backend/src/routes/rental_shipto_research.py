from flask import jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
from src.routes.reports import reports_bp
import logging

logger = logging.getLogger(__name__)

@reports_bp.route('/departments/rental/shipto-research', methods=['GET'])
@jwt_required()
def research_rental_shipto():
    """Research how to find Ship To customer for rental equipment"""
    try:
        db = AzureSQLService()
        research_results = {}
        
        # 1. Check RentalContract columns
        contract_cols_query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002'
        AND TABLE_NAME = 'RentalContract'
        ORDER BY ORDINAL_POSITION
        """
        research_results['rental_contract_columns'] = db.execute_query(contract_cols_query)
        
        # 2. Sample RentalContract data
        contract_sample_query = """
        SELECT TOP 5 * 
        FROM ben002.RentalContract
        WHERE EndDate IS NULL OR EndDate > GETDATE()
        ORDER BY StartDate DESC
        """
        research_results['rental_contract_sample'] = db.execute_query(contract_sample_query)
        
        # 3. Check WO table for rental work orders with ShipTo
        wo_rental_query = """
        SELECT TOP 10
            wo.WONo,
            wo.Type,
            wo.BillTo,
            wo.ShipTo,
            wo.UnitNo,
            wo.OpenDate,
            wo.ClosedDate,
            bill_cust.Name as BillToName,
            ship_cust.Name as ShipToName
        FROM ben002.WO wo
        LEFT JOIN ben002.Customer bill_cust ON wo.BillTo = bill_cust.Number
        LEFT JOIN ben002.Customer ship_cust ON wo.ShipTo = ship_cust.Number
        WHERE wo.Type = 'R'
        AND wo.ClosedDate IS NULL
        ORDER BY wo.OpenDate DESC
        """
        research_results['rental_work_orders'] = db.execute_query(wo_rental_query)
        
        # 4. Check WORental table columns
        worental_cols_query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002'
        AND TABLE_NAME = 'WORental'
        ORDER BY ORDINAL_POSITION
        """
        research_results['worental_columns'] = db.execute_query(worental_cols_query)
        
        # 5. Sample WORental data
        worental_sample_query = """
        SELECT TOP 5 *
        FROM ben002.WORental
        """
        research_results['worental_sample'] = db.execute_query(worental_sample_query)
        
        # 6. Find all ShipTo related fields
        shipto_fields_query = """
        SELECT DISTINCT
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002'
        AND (
            COLUMN_NAME LIKE '%Ship%'
            OR COLUMN_NAME LIKE '%Deliver%'
        )
        ORDER BY TABLE_NAME, COLUMN_NAME
        """
        research_results['shipto_fields'] = db.execute_query(shipto_fields_query)
        
        # 7. Trace a specific rental unit through the system
        trace_query = """
        -- Find a unit that's currently on rent
        WITH CurrentRental AS (
            SELECT TOP 1
                e.UnitNo,
                e.SerialNo,
                e.CustomerNo as EquipmentCustomerNo,
                e.RentalStatus,
                e.Location
            FROM ben002.Equipment e
            JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo
            WHERE rh.Year = YEAR(GETDATE())
            AND rh.Month = MONTH(GETDATE())
            AND rh.DaysRented > 0
        )
        SELECT 
            'Equipment' as DataSource,
            cr.UnitNo,
            cr.SerialNo,
            cr.EquipmentCustomerNo as CustomerNo,
            eq_cust.Name as CustomerName,
            cr.RentalStatus,
            cr.Location,
            NULL as WONo,
            NULL as RentalContractNo,
            NULL as BillTo,
            NULL as ShipTo
        FROM CurrentRental cr
        LEFT JOIN ben002.Customer eq_cust ON cr.EquipmentCustomerNo = eq_cust.Number
        
        UNION ALL
        
        -- Get rental contract for this equipment
        SELECT 
            'RentalContract' as DataSource,
            cr.UnitNo,
            rc.SerialNo,
            rc.CustomerNo,
            rc_cust.Name as CustomerName,
            NULL as RentalStatus,
            NULL as Location,
            NULL as WONo,
            rc.RentalContractNo,
            NULL as BillTo,
            NULL as ShipTo
        FROM CurrentRental cr
        JOIN ben002.RentalContract rc ON cr.SerialNo = rc.SerialNo
        LEFT JOIN ben002.Customer rc_cust ON rc.CustomerNo = rc_cust.Number
        WHERE rc.EndDate IS NULL OR rc.EndDate > GETDATE()
        
        UNION ALL
        
        -- Get work orders for this unit
        SELECT 
            'WorkOrder' as DataSource,
            wo.UnitNo,
            cr.SerialNo,
            wo.BillTo as CustomerNo,
            bill_cust.Name as CustomerName,
            NULL as RentalStatus,
            NULL as Location,
            wo.WONo,
            NULL as RentalContractNo,
            wo.BillTo,
            wo.ShipTo
        FROM CurrentRental cr
        JOIN ben002.WO wo ON cr.UnitNo = wo.UnitNo
        LEFT JOIN ben002.Customer bill_cust ON wo.BillTo = bill_cust.Number
        WHERE wo.Type = 'R'
        AND wo.ClosedDate IS NULL
        """
        research_results['rental_trace'] = db.execute_query(trace_query)
        
        # 8. Check if RentalContract has a relationship with WO
        contract_wo_link_query = """
        SELECT TOP 10
            rc.RentalContractNo,
            rc.SerialNo,
            rc.CustomerNo as ContractCustomer,
            e.UnitNo,
            wo.WONo,
            wo.BillTo as WOBillTo,
            wo.ShipTo as WOShipTo,
            wo.OpenDate as WODate
        FROM ben002.RentalContract rc
        JOIN ben002.Equipment e ON rc.SerialNo = e.SerialNo
        LEFT JOIN ben002.WO wo ON e.UnitNo = wo.UnitNo AND wo.Type = 'R'
        WHERE (rc.EndDate IS NULL OR rc.EndDate > GETDATE())
        AND wo.WONo IS NOT NULL
        ORDER BY wo.OpenDate DESC
        """
        research_results['contract_wo_relationships'] = db.execute_query(contract_wo_link_query)
        
        # 9. Check InvoiceReg structure for ShipTo fields
        invoice_cols_query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002'
        AND TABLE_NAME = 'InvoiceReg'
        AND (
            COLUMN_NAME LIKE '%Ship%'
            OR COLUMN_NAME LIKE '%Deliver%'
            OR COLUMN_NAME = 'BillTo'
            OR COLUMN_NAME = 'BillToName'
        )
        ORDER BY ORDINAL_POSITION
        """
        research_results['invoice_shipto_fields'] = db.execute_query(invoice_cols_query)
        
        return jsonify(research_results)
        
    except Exception as e:
        logger.error(f"Error in rental ship-to research: {str(e)}")
        return jsonify({'error': str(e)}), 500