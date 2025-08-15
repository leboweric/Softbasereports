from flask import jsonify, request
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from src.services.azure_sql_service import AzureSQLService
from src.routes.reports import reports_bp
import logging

logger = logging.getLogger(__name__)

@reports_bp.route('/departments/accounting/find-control-fields', methods=['GET'])
@jwt_required()
def find_control_fields():
    """Get report showing all equipment identification fields including potential control numbers"""
    try:
        logger.info("Starting equipment identifiers report")
        db = AzureSQLService()
        
        # Get all equipment with various identification fields
        # Since we don't know what the control number field is, we'll show all potential fields
        query = """
        SELECT 
            e.UnitNo,
            e.SerialNo,
            e.Make,
            e.Model,
            e.ModelYear,
            e.Location,
            e.CustomerNo,
            c.Name as CustomerName,
            e.RentalStatus,
            -- Include any rental contract info
            rc.RentalContractNo,
            rc.StartDate as ContractStartDate,
            rc.EndDate as ContractEndDate,
            -- Include work order info
            wo.WONo as LastWorkOrderNo,
            wo.OpenDate as LastWODate,
            -- Include invoice info if equipment was sold
            e.Cost,
            e.Sell,
            e.Retail,
            e.RentalYTD,
            e.RentalITD
        FROM ben002.Equipment e
        LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
        LEFT JOIN (
            SELECT SerialNo, RentalContractNo, StartDate, EndDate,
                   ROW_NUMBER() OVER (PARTITION BY SerialNo ORDER BY StartDate DESC) as rn
            FROM ben002.RentalContract
            WHERE DeletionTime IS NULL
        ) rc ON e.SerialNo = rc.SerialNo AND rc.rn = 1
        LEFT JOIN (
            SELECT UnitNo, WONo, OpenDate,
                   ROW_NUMBER() OVER (PARTITION BY UnitNo ORDER BY OpenDate DESC) as rn
            FROM ben002.WO
            WHERE DeletionTime IS NULL
        ) wo ON e.UnitNo = wo.UnitNo AND wo.rn = 1
        WHERE e.SerialNo IS NOT NULL
        ORDER BY e.UnitNo
        """
        
        result = db.execute_query(query)
        
        if not result:
            return jsonify({
                'equipment': [],
                'summary': {
                    'total_equipment': 0,
                    'with_rental_contracts': 0,
                    'with_work_orders': 0
                }
            })
        
        equipment = []
        with_contracts = 0
        with_work_orders = 0
        
        for row in result:
            if row.get('RentalContractNo'):
                with_contracts += 1
            if row.get('LastWorkOrderNo'):
                with_work_orders += 1
                
            equipment.append({
                'unit_number': row.get('UnitNo', ''),
                'serial_number': row.get('SerialNo', ''),
                'make': row.get('Make', ''),
                'model': row.get('Model', ''),
                'model_year': row.get('ModelYear', ''),
                'location': row.get('Location', ''),
                'customer_number': row.get('CustomerNo', ''),
                'customer_name': row.get('CustomerName', ''),
                'rental_status': row.get('RentalStatus', ''),
                'rental_contract_no': row.get('RentalContractNo', ''),
                'contract_start': row.get('ContractStartDate').strftime('%Y-%m-%d') if row.get('ContractStartDate') else None,
                'contract_end': row.get('ContractEndDate').strftime('%Y-%m-%d') if row.get('ContractEndDate') else None,
                'last_work_order': row.get('LastWorkOrderNo', ''),
                'last_wo_date': row.get('LastWODate').strftime('%Y-%m-%d') if row.get('LastWODate') else None,
                'cost': float(row.get('Cost', 0) or 0),
                'ytd_rental': float(row.get('RentalYTD', 0) or 0)
            })
        
        summary = {
            'total_equipment': len(equipment),
            'with_rental_contracts': with_contracts,
            'with_work_orders': with_work_orders
        }
        
        return jsonify({
            'equipment': equipment,
            'summary': summary,
            'note': 'The control number field is not standard in the Equipment table. Please check if UnitNo is your control number, or if it exists in a custom field.'
        })
        
    except Exception as e:
        logger.error(f"Error in equipment identifiers report: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/departments/accounting/control-serial-link', methods=['GET'])
@jwt_required() 
def get_control_serial_link_report():
    """Get report linking rental contract control numbers with equipment serial numbers"""
    try:
        logger.info("Starting control number to serial number link report")
        db = AzureSQLService()
        
        # Get all rental contracts with their associated equipment
        query = """
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
        FROM ben002.RentalContract rc
        LEFT JOIN ben002.Equipment e ON rc.SerialNo = e.SerialNo
        LEFT JOIN ben002.Customer c ON rc.CustomerNo = c.Number
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
        db = AzureSQLService()
        
        # Get summary by customer
        customer_summary_query = """
        SELECT 
            c.Number as CustomerNo,
            c.Name as CustomerName,
            COUNT(DISTINCT rc.RentalContractNo) as ContractCount,
            COUNT(DISTINCT rc.SerialNo) as EquipmentCount,
            MIN(rc.StartDate) as FirstContractDate,
            MAX(rc.StartDate) as LatestContractDate,
            SUM(CASE WHEN rc.EndDate IS NULL OR rc.EndDate > GETDATE() THEN 1 ELSE 0 END) as ActiveContracts
        FROM ben002.RentalContract rc
        LEFT JOIN ben002.Customer c ON rc.CustomerNo = c.Number
        WHERE rc.DeletionTime IS NULL
        GROUP BY c.Number, c.Name
        HAVING COUNT(DISTINCT rc.RentalContractNo) > 0
        ORDER BY COUNT(DISTINCT rc.RentalContractNo) DESC
        """
        
        customer_results = db.execute_query(customer_summary_query)
        
        # Get equipment utilization
        utilization_query = """
        SELECT 
            e.Make,
            e.Model,
            COUNT(DISTINCT e.SerialNo) as TotalUnits,
            COUNT(DISTINCT rc.SerialNo) as UnitsOnContract,
            CAST(COUNT(DISTINCT rc.SerialNo) * 100.0 / NULLIF(COUNT(DISTINCT e.SerialNo), 0) as DECIMAL(5,2)) as UtilizationRate
        FROM ben002.Equipment e
        LEFT JOIN ben002.RentalContract rc ON e.SerialNo = rc.SerialNo 
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