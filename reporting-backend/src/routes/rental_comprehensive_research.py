from flask import jsonify
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db
from src.routes.reports import reports_bp
import logging

from flask_jwt_extended import get_jwt_identity
from src.models.user import User

logger = logging.getLogger(__name__)

@reports_bp.route('/departments/rental/comprehensive-research', methods=['GET'])
@jwt_required()
def comprehensive_rental_research():
    """Comprehensive research to find how competing products get rental customer"""
    try:
        db = get_tenant_db()
        results = {}
        
        # 1. Check RentalHistory table structure - maybe it has customer info
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}'
            AND TABLE_NAME = 'RentalHistory'
            ORDER BY ORDINAL_POSITION
            """
            results['rental_history_columns'] = db.execute_query(query)
        except Exception as e:
            results['rental_history_columns'] = str(e)
        
        # 2. Sample RentalHistory data with all columns
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT TOP 3
                SerialNo,
                Year,
                Month,
                DaysRented,
                RentAmount,
                CreationTime,
                CreatorUserId,
                LastModificationTime,
                LastModifierUserId,
                DeletionTime,
                DeleterUserId,
                TenantId,
                Id
            FROM {schema}.RentalHistory
            WHERE Year = YEAR(GETDATE())
            AND Month = MONTH(GETDATE())
            AND DaysRented > 0
            """
            results['rental_history_sample'] = db.execute_query(query)
        except Exception as e:
            results['rental_history_sample'] = str(e)
        
        # 3. Find ALL tables with "Rental" in the name
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT 
                TABLE_NAME,
                TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{schema}'
            AND TABLE_NAME LIKE '%Rental%'
            ORDER BY TABLE_NAME
            """
            results['all_rental_tables'] = db.execute_query(query)
        except Exception as e:
            results['all_rental_tables'] = str(e)
        
        # 4. Check if there's a RentalDetail or RentalInvoice table
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT 
                TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{schema}'
            AND (
                TABLE_NAME LIKE '%RentalDetail%'
                OR TABLE_NAME LIKE '%RentalInvoice%'
                OR TABLE_NAME LIKE '%RentalBilling%'
                OR TABLE_NAME LIKE '%RentalCustomer%'
            )
            """
            results['rental_detail_tables'] = db.execute_query(query)
        except Exception as e:
            results['rental_detail_tables'] = str(e)
        
        # 5. Check InvoiceReg for rental invoices with ship info
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT 
                COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}'
            AND TABLE_NAME = 'InvoiceReg'
            AND (
                COLUMN_NAME LIKE '%Ship%'
                OR COLUMN_NAME LIKE '%Deliver%'
            )
            """
            results['invoice_ship_columns'] = db.execute_query(query)
        except Exception as e:
            results['invoice_ship_columns'] = str(e)
        
        # 6. Find a rental invoice and check its data
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT TOP 3
                InvoiceNo,
                InvoiceDate,
                BillTo,
                BillToName,
                SaleCode,
                ControlNo,
                Customer
            FROM {schema}.InvoiceReg
            WHERE SaleCode LIKE 'RENT%'
            ORDER BY InvoiceDate DESC
            """
            results['rental_invoices'] = db.execute_query(query)
        except Exception as e:
            results['rental_invoices'] = str(e)
        
        # 7. Check for Views related to rentals
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT 
                TABLE_NAME
            FROM INFORMATION_SCHEMA.VIEWS
            WHERE TABLE_SCHEMA = '{schema}'
            AND (
                TABLE_NAME LIKE '%Rental%'
                OR TABLE_NAME LIKE '%Equipment%'
            )
            ORDER BY TABLE_NAME
            """
            results['rental_views'] = db.execute_query(query)
        except Exception as e:
            results['rental_views'] = str(e)
        
        # 8. Check if Equipment has additional customer fields we missed
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT 
                COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}'
            AND TABLE_NAME = 'Equipment'
            AND (
                COLUMN_NAME LIKE '%Customer%'
                OR COLUMN_NAME LIKE '%Ship%'
                OR COLUMN_NAME LIKE '%Bill%'
                OR COLUMN_NAME LIKE '%Deliver%'
            )
            ORDER BY COLUMN_NAME
            """
            results['equipment_customer_columns'] = db.execute_query(query)
        except Exception as e:
            results['equipment_customer_columns'] = str(e)
        
        # 9. Try to find how equipment links to actual rental customer
        # Check if there's a pattern in the data
        try:
            schema = get_tenant_schema()

            query = f"""
            -- Find equipment that's on rent and has different customer patterns
            SELECT TOP 5
                e.UnitNo,
                e.SerialNo,
                e.CustomerNo as EquipCustomer,
                e.RentalStatus,
                c1.Name as EquipCustomerName,
                rc.CustomerNo as ContractCustomer,
                c2.Name as ContractCustomerName,
                rc.RentalContractNo
            FROM {schema}.Equipment e
            LEFT JOIN {schema}.Customer c1 ON e.CustomerNo = c1.Number
            LEFT JOIN {schema}.RentalContract rc ON e.SerialNo = rc.SerialNo
                AND (rc.EndDate IS NULL OR rc.EndDate > GETDATE())
            LEFT JOIN {schema}.Customer c2 ON rc.CustomerNo = c2.Number
            WHERE EXISTS (
                SELECT 1 FROM {schema}.RentalHistory rh
                WHERE rh.SerialNo = e.SerialNo
                AND rh.Year = YEAR(GETDATE())
                AND rh.Month = MONTH(GETDATE())
                AND rh.DaysRented > 0
            )
            """
            results['equipment_customer_analysis'] = db.execute_query(query)
        except Exception as e:
            results['equipment_customer_analysis'] = str(e)
        
        # 10. Check if RentalContract has additional fields for delivery/ship-to
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}'
            AND TABLE_NAME = 'RentalContract'
            AND (
                COLUMN_NAME LIKE '%Ship%'
                OR COLUMN_NAME LIKE '%Deliver%'
                OR COLUMN_NAME LIKE '%Location%'
                OR COLUMN_NAME LIKE '%Address%'
            )
            ORDER BY COLUMN_NAME
            """
            results['contract_delivery_columns'] = db.execute_query(query)
        except Exception as e:
            results['contract_delivery_columns'] = str(e)
        
        # 11. Look for any EquipmentLocation or similar tables
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT 
                TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{schema}'
            AND (
                TABLE_NAME LIKE '%Location%'
                OR TABLE_NAME LIKE '%Delivery%'
                OR TABLE_NAME LIKE '%Assignment%'
            )
            AND TABLE_NAME LIKE '%Equip%'
            """
            results['location_tables'] = db.execute_query(query)
        except Exception as e:
            results['location_tables'] = str(e)
        
        # 12. CRITICAL: Look for RentalContractDetail or any link table
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT 
                TABLE_NAME,
                TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{schema}'
            AND (
                TABLE_NAME LIKE '%RentalContract%'
                OR TABLE_NAME LIKE '%ContractCustomer%'
                OR TABLE_NAME LIKE '%ContractDetail%'
                OR TABLE_NAME LIKE '%ContractLine%'
                OR TABLE_NAME LIKE '%ContractEquipment%'
            )
            ORDER BY TABLE_NAME
            """
            results['contract_link_tables'] = db.execute_query(query)
        except Exception as e:
            results['contract_link_tables'] = str(e)
        
        # 13. Check if RentalContract has an Id that links elsewhere
        try:
            schema = get_tenant_schema()

            query = f"""
            -- Find tables with RentalContractNo or ContractId columns
            SELECT 
                TABLE_NAME,
                COLUMN_NAME,
                DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}'
            AND (
                COLUMN_NAME LIKE '%RentalContract%'
                OR COLUMN_NAME LIKE '%ContractNo%'
                OR COLUMN_NAME LIKE '%ContractId%'
            )
            AND TABLE_NAME != 'RentalContract'
            ORDER BY TABLE_NAME, COLUMN_NAME
            """
            results['contract_reference_columns'] = db.execute_query(query)
        except Exception as e:
            results['contract_reference_columns'] = str(e)
        
        # 14. Check RecentCustomer table - might have rental info
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT TOP 5
                rc.CustomerNo,
                rc.EntryDate,
                c.Name as CustomerName,
                rc.SecureName
            FROM {schema}.RecentCustomer rc
            LEFT JOIN {schema}.Customer c ON rc.CustomerNo = c.Number
            WHERE rc.CustomerNo IS NOT NULL
            ORDER BY rc.EntryDate DESC
            """
            results['recent_customer_sample'] = db.execute_query(query)
        except Exception as e:
            results['recent_customer_sample'] = str(e)
        
        # 15. Try to find how RentalContract.Id links to anything
        try:
            schema = get_tenant_schema()

            query = f"""
            SELECT TOP 3
                rc.Id as ContractId,
                rc.RentalContractNo,
                rc.StartDate,
                rc.EndDate,
                rc.DeliveryCharge,
                rc.PickupCharge
            FROM {schema}.RentalContract rc
            WHERE rc.EndDate IS NULL OR rc.EndDate > GETDATE()
            ORDER BY rc.StartDate DESC
            """
            results['active_contracts_sample'] = db.execute_query(query)
        except Exception as e:
            results['active_contracts_sample'] = str(e)
            
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in comprehensive rental research: {str(e)}")
        return jsonify({'error': str(e)}), 500