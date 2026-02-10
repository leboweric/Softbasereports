from flask import jsonify, request
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db
from datetime import datetime, timedelta
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

@reports_bp.route('/departments/accounting/control-serial-link', methods=['GET'])
@jwt_required() 
def get_control_serial_link_report():
    """Get report linking rental contract control numbers with equipment serial numbers"""
    try:
        logger.info("Starting control number to serial number link report")
        db = get_tenant_db()
        
        # Get all rental contracts with their associated equipment
        schema = get_tenant_schema()

        query = f"""
        SELECT DISTINCT
            rc.RentalContractNo as ControlNumber,
            rc.SerialNo,
            e.UnitNo,
            e.Make,
            e.Model,
            rc.CustomerNo,
            c.Name as CustomerName,
            rc.StartDate,
            rc.EndDate,
            CASE 
                WHEN rc.EndDate IS NULL THEN 'Open-Ended'
                WHEN rc.EndDate > GETDATE() THEN 'Active'
                WHEN rc.EndDate <= GETDATE() THEN 'Expired'
                ELSE 'Unknown'
            END as ContractStatus,
            rc.DeliveryCharge,
            rc.PickupCharge,
            e.DayRent,
            e.WeekRent,
            e.MonthRent,
            -- Calculate estimated monthly revenue
            CASE 
                WHEN e.MonthRent > 0 THEN e.MonthRent
                WHEN e.WeekRent > 0 THEN e.WeekRent * 4.33
                WHEN e.DayRent > 0 THEN e.DayRent * 30
                ELSE 0
            END as EstimatedMonthlyRevenue
        FROM {schema}.RentalContract rc
        LEFT JOIN {schema}.Equipment e ON rc.SerialNo = e.SerialNo
        LEFT JOIN {schema}.Customer c ON rc.CustomerNo = c.Number
        WHERE rc.DeletionTime IS NULL
        ORDER BY 
            CASE 
                WHEN rc.EndDate IS NULL THEN 0
                WHEN rc.EndDate > GETDATE() THEN 1
                ELSE 2
            END,
            rc.RentalContractNo DESC
        """
        
        result = db.execute_query(query)
        
        if not result:
            logger.warning("No rental contracts found")
            return jsonify({
                'contracts': [],
                'summary': {
                    'total_contracts': 0,
                    'active_contracts': 0,
                    'expired_contracts': 0,
                    'open_ended_contracts': 0,
                    'total_equipment': 0,
                    'total_monthly_revenue': 0
                }
            })
        
        # Process results
        contracts = []
        active_count = 0
        expired_count = 0
        open_ended_count = 0
        total_monthly_revenue = 0
        unique_serials = set()
        
        for row in result:
            contract_status = row.get('ContractStatus', 'Unknown')
            
            if contract_status == 'Active':
                active_count += 1
            elif contract_status == 'Expired':
                expired_count += 1
            elif contract_status == 'Open-Ended':
                open_ended_count += 1
            
            serial_no = row.get('SerialNo', '')
            if serial_no:
                unique_serials.add(serial_no)
            
            monthly_revenue = float(row.get('EstimatedMonthlyRevenue', 0) or 0)
            if contract_status in ['Active', 'Open-Ended']:
                total_monthly_revenue += monthly_revenue
            
            contracts.append({
                'control_number': row.get('ControlNumber', ''),
                'serial_number': serial_no,
                'unit_number': row.get('UnitNo', ''),
                'make': row.get('Make', ''),
                'model': row.get('Model', ''),
                'customer_number': row.get('CustomerNo', ''),
                'customer_name': row.get('CustomerName', ''),
                'start_date': row.get('StartDate').strftime('%Y-%m-%d') if row.get('StartDate') else None,
                'end_date': row.get('EndDate').strftime('%Y-%m-%d') if row.get('EndDate') else None,
                'contract_status': contract_status,
                'delivery_charge': float(row.get('DeliveryCharge', 0) or 0),
                'pickup_charge': float(row.get('PickupCharge', 0) or 0),
                'day_rate': float(row.get('DayRent', 0) or 0),
                'week_rate': float(row.get('WeekRent', 0) or 0),
                'month_rate': float(row.get('MonthRent', 0) or 0),
                'estimated_monthly_revenue': monthly_revenue
            })
        
        summary = {
            'total_contracts': len(contracts),
            'active_contracts': active_count,
            'expired_contracts': expired_count,
            'open_ended_contracts': open_ended_count,
            'total_equipment': len(unique_serials),
            'total_monthly_revenue': round(total_monthly_revenue, 2)
        }
        
        logger.info(f"Found {len(contracts)} rental contracts linking to {len(unique_serials)} pieces of equipment")
        
        return jsonify({
            'contracts': contracts,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error in control-serial link report: {str(e)}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/departments/accounting/control-serial-summary', methods=['GET'])
@jwt_required()
def get_control_serial_summary():
    """Get summary statistics for control number to serial number relationships"""
    try:
        db = get_tenant_db()
        
        # Get summary by customer
        customer_summary_query = f"""
        SELECT 
            c.Number as CustomerNo,
            c.Name as CustomerName,
            COUNT(DISTINCT rc.RentalContractNo) as ContractCount,
            COUNT(DISTINCT rc.SerialNo) as EquipmentCount,
            MIN(rc.StartDate) as FirstContractDate,
            MAX(rc.StartDate) as LatestContractDate,
            SUM(CASE WHEN rc.EndDate IS NULL OR rc.EndDate > GETDATE() THEN 1 ELSE 0 END) as ActiveContracts
        FROM {schema}.RentalContract rc
        LEFT JOIN {schema}.Customer c ON rc.CustomerNo = c.Number
        WHERE rc.DeletionTime IS NULL
        GROUP BY c.Number, c.Name
        HAVING COUNT(DISTINCT rc.RentalContractNo) > 0
        ORDER BY COUNT(DISTINCT rc.RentalContractNo) DESC
        """
        
        customer_results = db.execute_query(customer_summary_query)
        
        # Get equipment utilization
        utilization_query = f"""
        SELECT 
            e.Make,
            e.Model,
            COUNT(DISTINCT e.SerialNo) as TotalUnits,
            COUNT(DISTINCT rc.SerialNo) as UnitsOnContract,
            CAST(COUNT(DISTINCT rc.SerialNo) * 100.0 / NULLIF(COUNT(DISTINCT e.SerialNo), 0) as DECIMAL(5,2)) as UtilizationRate
        FROM {schema}.Equipment e
        LEFT JOIN {schema}.RentalContract rc ON e.SerialNo = rc.SerialNo 
            AND rc.DeletionTime IS NULL
            AND (rc.EndDate IS NULL OR rc.EndDate > GETDATE())
        WHERE e.DayRent > 0 OR e.WeekRent > 0 OR e.MonthRent > 0
        GROUP BY e.Make, e.Model
        HAVING COUNT(DISTINCT e.SerialNo) > 0
        ORDER BY COUNT(DISTINCT rc.SerialNo) DESC
        """
        
        utilization_results = db.execute_query(utilization_query)
        
        # Format results
        customer_summary = []
        for row in customer_results:
            customer_summary.append({
                'customer_number': row.get('CustomerNo', ''),
                'customer_name': row.get('CustomerName', ''),
                'total_contracts': row.get('ContractCount', 0),
                'equipment_count': row.get('EquipmentCount', 0),
                'first_contract': row.get('FirstContractDate').strftime('%Y-%m-%d') if row.get('FirstContractDate') else None,
                'latest_contract': row.get('LatestContractDate').strftime('%Y-%m-%d') if row.get('LatestContractDate') else None,
                'active_contracts': row.get('ActiveContracts', 0)
            })
        
        equipment_utilization = []
        for row in utilization_results:
            equipment_utilization.append({
                'make': row.get('Make', ''),
                'model': row.get('Model', ''),
                'total_units': row.get('TotalUnits', 0),
                'units_on_contract': row.get('UnitsOnContract', 0),
                'utilization_rate': float(row.get('UtilizationRate', 0))
            })
        
        return jsonify({
            'customer_summary': customer_summary,
            'equipment_utilization': equipment_utilization
        })
        
    except Exception as e:
        logger.error(f"Error in control-serial summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/departments/accounting/absorption-rate', methods=['GET'])
@jwt_required()
def get_monthly_absorption_rate():
    """
    Get monthly absorption rate data.
    Absorption Rate = (Service GP + Parts GP + Rental GP) / Overhead Expenses × 100%
    
    Returns trailing 13 months of data.
    Uses tenant-aware GL account mappings from gl_accounts_loader.
    """
    try:
        logger.info("Starting absorption rate calculation")
        db = get_tenant_db()
        schema = get_tenant_schema()
        
        # Use tenant-aware GL accounts (supports both Bennett and IPS account formats)
        from src.config.gl_accounts_loader import get_gl_accounts, get_expense_accounts
        
        gl_accounts = get_gl_accounts(schema)
        expense_accounts = get_expense_accounts(schema)
        
        # Get service, parts, rental revenue and COGS accounts for this tenant
        service_sales = gl_accounts.get('service', {}).get('revenue', [])
        service_cos = gl_accounts.get('service', {}).get('cogs', [])
        parts_sales = gl_accounts.get('parts', {}).get('revenue', [])
        parts_cos = gl_accounts.get('parts', {}).get('cogs', [])
        rental_sales = gl_accounts.get('rental', {}).get('revenue', [])
        rental_cos = gl_accounts.get('rental', {}).get('cogs', [])
        
        # Get all overhead expense accounts (flatten all categories)
        overhead_accounts = []
        for category, accounts in expense_accounts.items():
            overhead_accounts.extend(accounts)
        
        logger.info(f"Absorption rate for schema={schema}: service_sales={len(service_sales)}, "
                    f"parts_sales={len(parts_sales)}, rental_sales={len(rental_sales)}, "
                    f"overhead={len(overhead_accounts)} accounts")
        
        # Format for SQL IN clause
        service_sales_list = "', '".join(service_sales)
        service_cos_list = "', '".join(service_cos)
        parts_sales_list = "', '".join(parts_sales)
        parts_cos_list = "', '".join(parts_cos)
        rental_sales_list = "', '".join(rental_sales)
        rental_cos_list = "', '".join(rental_cos)
        overhead_list = "', '".join(overhead_accounts)
        
        # Combine all accounts for the query
        all_accounts = (service_sales + service_cos + parts_sales + parts_cos + 
                       rental_sales + rental_cos + overhead_accounts)
        all_accounts_list = "', '".join(all_accounts)
        
        query = f"""
        SELECT 
            YEAR(EffectiveDate) as year,
            MONTH(EffectiveDate) as month,
            -- Service Revenue and Cost (negate revenue since credits are negative)
            -SUM(CASE WHEN AccountNo IN ('{service_sales_list}') THEN Amount ELSE 0 END) as service_revenue,
            SUM(CASE WHEN AccountNo IN ('{service_cos_list}') THEN Amount ELSE 0 END) as service_cost,
            -- Parts Revenue and Cost
            -SUM(CASE WHEN AccountNo IN ('{parts_sales_list}') THEN Amount ELSE 0 END) as parts_revenue,
            SUM(CASE WHEN AccountNo IN ('{parts_cos_list}') THEN Amount ELSE 0 END) as parts_cost,
            -- Rental Revenue and Cost
            -SUM(CASE WHEN AccountNo IN ('{rental_sales_list}') THEN Amount ELSE 0 END) as rental_revenue,
            SUM(CASE WHEN AccountNo IN ('{rental_cos_list}') THEN Amount ELSE 0 END) as rental_cost,
            -- Overhead Expenses
            SUM(CASE WHEN AccountNo IN ('{overhead_list}') THEN Amount ELSE 0 END) as overhead_expenses
        FROM {schema}.GLDetail
        WHERE AccountNo IN ('{all_accounts_list}')
            AND EffectiveDate >= DATEADD(month, -13, GETDATE())
            AND Posted = 1
        GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        ORDER BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        """
        
        results = db.execute_query(query)
        
        # Process results
        monthly_data = []
        for row in results:
            year = row['year']
            month = row['month']
            month_date = datetime(year, month, 1)
            month_str = month_date.strftime("%b '%y")
            
            # Calculate gross profits
            service_revenue = float(row['service_revenue'] or 0)
            service_cost = float(row['service_cost'] or 0)
            service_gp = service_revenue - service_cost
            
            parts_revenue = float(row['parts_revenue'] or 0)
            parts_cost = float(row['parts_cost'] or 0)
            parts_gp = parts_revenue - parts_cost
            
            rental_revenue = float(row['rental_revenue'] or 0)
            rental_cost = float(row['rental_cost'] or 0)
            rental_gp = rental_revenue - rental_cost
            
            # Total aftermarket GP
            total_aftermarket_gp = service_gp + parts_gp + rental_gp
            
            # Overhead expenses
            overhead = float(row['overhead_expenses'] or 0)
            
            # Calculate absorption rate
            absorption_rate = (total_aftermarket_gp / overhead * 100) if overhead > 0 else 0
            
            monthly_data.append({
                'month': month_str,
                'year': year,
                'month_num': month,
                'service_gp': round(service_gp, 2),
                'parts_gp': round(parts_gp, 2),
                'rental_gp': round(rental_gp, 2),
                'total_aftermarket_gp': round(total_aftermarket_gp, 2),
                'overhead_expenses': round(overhead, 2),
                'absorption_rate': round(absorption_rate, 1)
            })
        
        # Calculate averages
        if monthly_data:
            avg_absorption = sum(d['absorption_rate'] for d in monthly_data) / len(monthly_data)
            avg_aftermarket_gp = sum(d['total_aftermarket_gp'] for d in monthly_data) / len(monthly_data)
            avg_overhead = sum(d['overhead_expenses'] for d in monthly_data) / len(monthly_data)
        else:
            avg_absorption = 0
            avg_aftermarket_gp = 0
            avg_overhead = 0
        
        return jsonify({
            'monthly_data': monthly_data,
            'summary': {
                'average_absorption_rate': round(avg_absorption, 1),
                'average_aftermarket_gp': round(avg_aftermarket_gp, 2),
                'average_overhead': round(avg_overhead, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating absorption rate: {str(e)}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/departments/accounting/parts-commissions', methods=['GET'])
@jwt_required()
def get_parts_commissions():
    """
    Parts Commissions report - Invoice Detail by Salesmen (Parts).
    Returns parts invoice data grouped by salesman for a given month/year.
    Columns: Invoice Date, Invoice No, Customer, Parts Sale, Parts Cost, Parts Profit
    """
    try:
        schema = get_tenant_schema()
        db = get_tenant_db()
        
        # Get month/year from query params (default to previous month)
        now = datetime.now()
        # Default to previous month
        if now.month == 1:
            default_month = 12
            default_year = now.year - 1
        else:
            default_month = now.month - 1
            default_year = now.year
        
        from flask import request
        month = int(request.args.get('month', default_month))
        year = int(request.args.get('year', default_year))
        
        logger.info(f"Parts Commissions report for {schema}: {year}-{month:02d}")
        
        # Query InvoiceReg for parts invoices in the given month
        # Parts Sale = PartsTaxable + PartsNonTax
        # Parts Profit = Parts Sale - PartsCost
        # Salesman comes from Customer table - join via BillTo = Customer.Number
        # (BillTo is the customer number on the invoice, confirmed working for both tenants)
        from src.config.column_mappings import get_column
        
        # Get tenant-specific column names
        cust_no_col = get_column(schema, 'Customer', 'cust_no')    # 'Number' for IPS, 'CustNo' for Bennett
        salesman_col = get_column(schema, 'Customer', 'salesman')  # 'Salesman1' for IPS, 'Salesman' for Bennett
        
        query = f"""
            SELECT 
                ir.InvoiceDate,
                ir.InvoiceNo,
                ir.BillToName as CustomerName,
                ISNULL(c.{salesman_col}, 'Unassigned') as Salesman,
                ISNULL(ir.PartsTaxable, 0) + ISNULL(ir.PartsNonTax, 0) as PartsSale,
                ISNULL(ir.PartsCost, 0) as PartsCost,
                (ISNULL(ir.PartsTaxable, 0) + ISNULL(ir.PartsNonTax, 0)) - ISNULL(ir.PartsCost, 0) as PartsProfit
            FROM {schema}.InvoiceReg ir
            LEFT JOIN {schema}.Customer c ON ir.BillTo = c.{cust_no_col}
            WHERE YEAR(ir.InvoiceDate) = {year}
                AND MONTH(ir.InvoiceDate) = {month}
                AND (
                    ISNULL(ir.PartsTaxable, 0) + ISNULL(ir.PartsNonTax, 0) != 0
                    OR ISNULL(ir.PartsCost, 0) != 0
                )
            ORDER BY c.{salesman_col}, ir.InvoiceDate, ir.InvoiceNo
        """
        
        results = db.execute_query(query)
        
        if not results:
            return jsonify({
                'month': month,
                'year': year,
                'salesmen': [],
                'grand_total': {
                    'parts_sale': 0,
                    'parts_cost': 0,
                    'parts_profit': 0,
                    'invoice_count': 0
                }
            })
        
        # Group by salesman
        from collections import OrderedDict
        salesmen = OrderedDict()
        grand_total_sale = 0
        grand_total_cost = 0
        grand_total_profit = 0
        
        for row in results:
            salesman = row['Salesman'] or 'Unassigned'
            parts_sale = float(row['PartsSale'] or 0)
            parts_cost = float(row['PartsCost'] or 0)
            parts_profit = float(row['PartsProfit'] or 0)
            
            if salesman not in salesmen:
                salesmen[salesman] = {
                    'name': salesman,
                    'invoices': [],
                    'total_sale': 0,
                    'total_cost': 0,
                    'total_profit': 0
                }
            
            invoice_date = row['InvoiceDate']
            if hasattr(invoice_date, 'strftime'):
                invoice_date_str = invoice_date.strftime('%m/%d/%Y')
            else:
                invoice_date_str = str(invoice_date)
            
            salesmen[salesman]['invoices'].append({
                'invoice_date': invoice_date_str,
                'invoice_no': row['InvoiceNo'],
                'customer': row['CustomerName'] or 'Unknown',
                'parts_sale': round(parts_sale, 2),
                'parts_cost': round(parts_cost, 2),
                'parts_profit': round(parts_profit, 2)
            })
            
            salesmen[salesman]['total_sale'] += parts_sale
            salesmen[salesman]['total_cost'] += parts_cost
            salesmen[salesman]['total_profit'] += parts_profit
            
            grand_total_sale += parts_sale
            grand_total_cost += parts_cost
            grand_total_profit += parts_profit
        
        # Round salesman totals
        salesmen_list = []
        for s in salesmen.values():
            s['total_sale'] = round(s['total_sale'], 2)
            s['total_cost'] = round(s['total_cost'], 2)
            s['total_profit'] = round(s['total_profit'], 2)
            s['invoice_count'] = len(s['invoices'])
            salesmen_list.append(s)
        
        return jsonify({
            'month': month,
            'year': year,
            'salesmen': salesmen_list,
            'grand_total': {
                'parts_sale': round(grand_total_sale, 2),
                'parts_cost': round(grand_total_cost, 2),
                'parts_profit': round(grand_total_profit, 2),
                'invoice_count': sum(len(s['invoices']) for s in salesmen.values())
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching parts commissions: {str(e)}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/departments/accounting/table-columns', methods=['GET'])
@jwt_required()
def get_table_columns():
    """Temporary diagnostic endpoint to discover table columns for a tenant"""
    try:
        schema = get_tenant_schema()
        db = get_tenant_db()
        from flask import request
        table = request.args.get('table', 'Customer')
        
        query = f"""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'
            ORDER BY ORDINAL_POSITION
        """
        results = db.execute_query(query)
        columns = [{'name': r['COLUMN_NAME'], 'type': r['DATA_TYPE'], 'max_len': r.get('CHARACTER_MAXIMUM_LENGTH')} for r in results]
        return jsonify({'schema': schema, 'table': table, 'columns': columns})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/departments/accounting/diag-query', methods=['GET'])
@jwt_required()
def diag_query():
    """Temporary diagnostic endpoint to run custom queries"""
    try:
        schema = get_tenant_schema()
        db = get_tenant_db()
        from flask import request
        q = request.args.get('q', '')
        if not q:
            return jsonify({'error': 'No query provided'})
        # Replace {schema} placeholder
        q = q.replace('{schema}', schema)
        results = db.execute_query(q)
        # Convert to serializable format
        rows = []
        for r in results:
            row = {}
            for k, v in r.items():
                if hasattr(v, 'strftime'):
                    row[k] = v.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(v, (int, float, str, bool, type(None))):
                    row[k] = v
                else:
                    row[k] = str(v)
            rows.append(row)
        return jsonify({'schema': schema, 'count': len(rows), 'rows': rows[:200]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
