from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

pm_report_bp = Blueprint('pm_report', __name__)

@pm_report_bp.route('/api/reports/service/pms-due', methods=['GET'])
@jwt_required()
def get_pms_due():
    """
    Get PM (Planned Maintenance) schedules that are due.
    Queries the PM table (not WO table) for equipment PM schedules.
    Matches the Softbase "PM List By Due Date, by Tech" report.
    """
    try:
        db = AzureSQLService()
        
        # Query PM table for active PM schedules
        query = """
        SELECT 
            pm.Id,
            pm.SerialNo,
            pm.ShipTo as CustomerNo,
            c.Name as CustomerName,
            c.Address as CustomerAddress,
            c.City as CustomerCity,
            c.State as CustomerState,
            c.ZipCode as CustomerZip,
            c.Phone as CustomerPhone,
            pm.CustomerContact,
            pm.ContactPhone,
            e.UnitNo,
            e.Make,
            e.Model,
            e.SerialNo as EquipmentSerial,
            pm.Frequency,
            pm.FrequencyHours,
            pm.LastLaborDate,
            pm.NextPMDate,
            pm.Mechanic as Technician,
            pm.OpenPmWO,
            pm.WONo,
            pm.Status,
            pm.Comments,
            pm.CurrentHourMeter,
            pm.LastHourMeter,
            pm.Automatic,
            pm.PMCancelled,
            CASE 
                WHEN pm.NextPMDate IS NULL THEN NULL
                WHEN pm.NextPMDate < GETDATE() THEN DATEDIFF(day, pm.NextPMDate, GETDATE()) * -1
                ELSE DATEDIFF(day, GETDATE(), pm.NextPMDate)
            END as DaysUntilDue
        FROM ben002.PM pm
        LEFT JOIN ben002.Customer c ON pm.ShipTo = c.Number
        LEFT JOIN ben002.Equipment e ON pm.SerialNo = e.SerialNo
        WHERE pm.PMCancelled = 0
        AND (
            pm.NextPMDate IS NULL 
            OR pm.NextPMDate <= DATEADD(day, 90, GETDATE())
        )
        ORDER BY 
            CASE WHEN pm.NextPMDate IS NULL THEN 2 ELSE 1 END,
            pm.NextPMDate ASC,
            pm.Mechanic,
            c.Name
        """
        
        logger.info("Executing PM schedule query...")
        results = db.execute_query(query)
        
        if not results:
            logger.info("No PM schedules found")
            return jsonify({
                'summary': {
                    'total': 0,
                    'overdue': 0,
                    'due_soon': 0,
                    'scheduled': 0,
                    'not_scheduled': 0
                },
                'pms': []
            })
        
        # Process results
        pms_list = []
        total = 0
        overdue = 0
        due_soon = 0
        scheduled = 0
        not_scheduled = 0
        
        for row in results:
            total += 1
            
            # Determine status
            days_until_due = row.get('DaysUntilDue')
            next_pm_date = row.get('NextPMDate')
            
            if next_pm_date is None:
                status = 'Not Scheduled'
                not_scheduled += 1
            elif days_until_due is not None and days_until_due < 0:
                status = 'Overdue'
                overdue += 1
            elif days_until_due is not None and days_until_due <= 14:
                status = 'Due Soon'
                due_soon += 1
            else:
                status = 'Scheduled'
                scheduled += 1
            
            pm_data = {
                'id': row.get('Id'),
                'serial_no': row.get('SerialNo'),
                'customer_no': row.get('CustomerNo'),
                'customer_name': row.get('CustomerName'),
                'customer_address': row.get('CustomerAddress'),
                'customer_city': row.get('CustomerCity'),
                'customer_state': row.get('CustomerState'),
                'customer_zip': row.get('CustomerZip'),
                'customer_phone': row.get('CustomerPhone') or row.get('ContactPhone'),
                'customer_contact': row.get('CustomerContact'),
                'unit_no': row.get('UnitNo'),
                'make': row.get('Make'),
                'model': row.get('Model'),
                'equipment_serial': row.get('EquipmentSerial'),
                'frequency': row.get('Frequency'),
                'frequency_hours': float(row.get('FrequencyHours')) if row.get('FrequencyHours') else None,
                'last_labor_date': row.get('LastLaborDate').isoformat() if row.get('LastLaborDate') else None,
                'next_pm_date': next_pm_date.isoformat() if next_pm_date else None,
                'technician': row.get('Technician'),
                'open_pm_wo': row.get('OpenPmWO'),
                'wo_no': int(row.get('WONo')) if row.get('WONo') else None,
                'pm_status': row.get('Status'),
                'comments': row.get('Comments'),
                'current_hour_meter': float(row.get('CurrentHourMeter')) if row.get('CurrentHourMeter') else None,
                'last_hour_meter': float(row.get('LastHourMeter')) if row.get('LastHourMeter') else None,
                'automatic': row.get('Automatic'),
                'days_until_due': days_until_due,
                'status': status
            }
            
            pms_list.append(pm_data)
        
        logger.info(f"Found {total} PM schedules: {overdue} overdue, {due_soon} due soon, {scheduled} scheduled, {not_scheduled} not scheduled")
        
        return jsonify({
            'summary': {
                'total': total,
                'overdue': overdue,
                'due_soon': due_soon,
                'scheduled': scheduled,
                'not_scheduled': not_scheduled
            },
            'pms': pms_list
        })
        
    except Exception as e:
        logger.error(f"PM report failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'message': 'Failed to retrieve PM schedule data'
        }), 500
