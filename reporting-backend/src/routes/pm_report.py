"""
PM (Planned Maintenance) Report API
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.azure_sql_service import AzureSQLService
from src.models.user import User
import logging
from datetime import datetime

pm_report_bp = Blueprint('pm_report', __name__)
logger = logging.getLogger(__name__)

@pm_report_bp.route('/api/reports/service/pms-due', methods=['GET'])
@jwt_required()
def get_pms_due():
    """
    Get list of PM (Planned Maintenance) work orders that are due or overdue
    
    Query parameters:
    - status: 'all', 'due', 'overdue' (default: 'all')
    - days_ahead: number of days to look ahead for upcoming PMs (default: 30)
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get query parameters
        status_filter = request.args.get('status', 'all')
        days_ahead = int(request.args.get('days_ahead', 30))
        
        db = AzureSQLService()
        
        # Build the query to get PM work orders
        # PM work orders are identified by Type = 'PM'
        query = """
        SELECT 
            wo.WONo,
            wo.OpenDate,
            wo.ScheduleDate,
            wo.CompletedDate,
            wo.ClosedDate,
            wo.Type,
            wo.UnitNo,
            wo.Technician,
            wo.Comments,
            wo.BillTo as CustomerNo,
            c.Name as CustomerName,
            c.Phone as CustomerPhone,
            c.City as CustomerCity,
            c.State as CustomerState,
            e.Make,
            e.Model,
            e.SerialNo,
            e.ModelYear,
            -- Calculate days until due (negative means overdue, NULL if no schedule date)
            CASE 
                WHEN wo.ScheduleDate IS NOT NULL THEN DATEDIFF(day, GETDATE(), wo.ScheduleDate)
                ELSE NULL
            END as DaysUntilDue,
            -- Status indicator
            CASE 
                WHEN wo.ClosedDate IS NOT NULL THEN 'Completed'
                WHEN wo.ScheduleDate IS NULL THEN 'Not Scheduled'
                WHEN DATEDIFF(day, GETDATE(), wo.ScheduleDate) < 0 THEN 'Overdue'
                WHEN DATEDIFF(day, GETDATE(), wo.ScheduleDate) <= 7 THEN 'Due Soon'
                ELSE 'Scheduled'
            END as Status
        FROM ben002.WO wo
        LEFT JOIN ben002.Customer c ON wo.BillTo = c.Number
        LEFT JOIN ben002.Equipment e ON wo.UnitNo = e.UnitNo
        WHERE wo.ClosedDate IS NULL  -- Only open work orders
        AND wo.Type = 'PM'  -- PM work orders only
        """
        
        # Add status filter
        if status_filter == 'overdue':
            query += " AND wo.ScheduleDate IS NOT NULL AND DATEDIFF(day, GETDATE(), wo.ScheduleDate) < 0"
        elif status_filter == 'due':
            query += f" AND wo.ScheduleDate IS NOT NULL AND DATEDIFF(day, GETDATE(), wo.ScheduleDate) BETWEEN 0 AND {days_ahead}"
        else:
            # 'all' - show all open PMs (with or without schedule date)
            # If they have a schedule date, only show if within days_ahead or overdue
            query += f" AND (wo.ScheduleDate IS NULL OR DATEDIFF(day, GETDATE(), wo.ScheduleDate) <= {days_ahead})"
        
        query += " ORDER BY CASE WHEN wo.ScheduleDate IS NULL THEN 1 ELSE 0 END, wo.ScheduleDate ASC"
        
        results = db.execute_query(query)
        
        # Format the results
        pms_due = []
        overdue_count = 0
        due_soon_count = 0
        scheduled_count = 0
        
        if results:
            for row in results:
                days_until = row.get('DaysUntilDue')
                status = row.get('Status')
                
                # Count by status
                if status == 'Overdue':
                    overdue_count += 1
                elif status == 'Due Soon':
                    due_soon_count += 1
                elif status == 'Scheduled':
                    scheduled_count += 1
                
                pm_item = {
                    'wo_number': row.get('WONo'),
                    'customer_name': row.get('CustomerName', 'N/A'),
                    'customer_number': row.get('CustomerNo'),
                    'customer_phone': row.get('CustomerPhone'),
                    'customer_city': row.get('CustomerCity'),
                    'customer_state': row.get('CustomerState'),
                    'equipment_unit': row.get('UnitNo'),
                    'equipment_make': row.get('Make'),
                    'equipment_model': row.get('Model'),
                    'equipment_serial': row.get('SerialNo'),
                    'equipment_year': row.get('ModelYear'),
                    'technician': row.get('Technician', 'Unassigned'),
                    'service_type': 'Preventive Maintenance',  # All PM type work orders
                    'schedule_date': row.get('ScheduleDate').strftime('%Y-%m-%d') if row.get('ScheduleDate') else None,
                    'open_date': row.get('OpenDate').strftime('%Y-%m-%d') if row.get('OpenDate') else None,
                    'days_until_due': days_until,
                    'status': status,
                    'comments': row.get('Comments')
                }
                
                pms_due.append(pm_item)
        
        summary = {
            'total': len(pms_due),
            'overdue': overdue_count,
            'due_soon': due_soon_count,
            'scheduled': scheduled_count
        }
        
        return jsonify({
            'success': True,
            'pms': pms_due,
            'summary': summary,
            'filters': {
                'status': status_filter,
                'days_ahead': days_ahead
            }
        }), 200
        
    except Exception as e:
        logger.error(f"PM report failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate PM report',
            'message': str(e)
        }), 500
