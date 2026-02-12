from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
import logging
from datetime import datetime, timedelta

from flask_jwt_extended import get_jwt_identity
from src.models.user import User

logger = logging.getLogger(__name__)

pm_technician_performance_bp = Blueprint('pm_technician_performance', __name__)

@pm_technician_performance_bp.route('/api/reports/service/pm-technician-performance', methods=['GET'])
@jwt_required()
def get_pm_technician_performance():
    """
    Get PM technician performance metrics for the contest period.
    Shows completed PMs by technician with performance statistics.
    """
    try:
        start = request.args.get('start_date', '2025-11-01')
        end = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Determine period label
        if start == '2025-11-01' and end >= '2026-01-31':
            period_label = "Q1 FY2026 Contest Period"
        else:
            period_label = f"{start} to {end}"
        
        sql_service = get_tenant_db()
        
        # Query to get PM completions by technician
        # Only counts INVOICED PMs (wo.InvoiceDate IS NOT NULL)
        schema = get_tenant_schema()

        query = f"""
        WITH TechPMs AS (
            SELECT
                l.MechanicName as technician,
                l.WONo,
                l.DateOfLabor,
                l.Hours,
                wo.BillTo,
                wo.UnitNo,
                wo.SerialNo,
                wo.Model
            FROM {schema}.WOLabor l
            INNER JOIN {schema}.WO wo ON l.WONo = wo.WONo
            WHERE wo.Type = 'PM'
                AND wo.InvoiceDate IS NOT NULL
                AND l.DateOfLabor >= %s
                AND l.DateOfLabor <= %s
                AND l.MechanicName IS NOT NULL
                AND l.MechanicName != ''
        )
        SELECT 
            technician,
            COUNT(DISTINCT WONo) as total_pms,
            COUNT(DISTINCT CAST(DateOfLabor as DATE)) as days_worked,
            SUM(Hours) as total_hours,
            MAX(DateOfLabor) as last_pm_date,
            DATEDIFF(day, MAX(DateOfLabor), GETDATE()) as days_inactive
        FROM TechPMs
        GROUP BY technician
        ORDER BY total_pms DESC
        """
        
        results = sql_service.execute_query(query, [start, end])
        
        if not results:
            return jsonify({
                'employees': [],
                'summary': {
                    'totalEmployees': 0,
                    'totalPMs': 0,
                    'topPerformer': None,
                    'avgPMsPerTech': 0
                },
                'period': period_label
            })
        
        # Process results
        employees = []
        total_pms = 0
        top_performer = None
        max_pms = 0
        
        for row in results:
            tech_name = row['technician']
            pms = int(row['total_pms'])
            days_worked = int(row['days_worked']) if row['days_worked'] else 0
            total_hours = float(row['total_hours']) if row['total_hours'] else 0
            last_pm = row['last_pm_date']
            days_inactive = int(row['days_inactive']) if row['days_inactive'] else 0
            
            total_pms += pms
            
            if pms > max_pms:
                max_pms = pms
                top_performer = tech_name
            
            employees.append({
                'name': tech_name,
                'totalPMs': pms,
                'daysWorked': days_worked,
                'avgPMsPerDay': round(pms / days_worked, 2) if days_worked > 0 else 0,
                'totalHours': round(total_hours, 1),
                'avgTimePerPM': round(total_hours / pms, 2) if pms > 0 else 0,
                'lastPMDate': last_pm.strftime('%Y-%m-%d') if last_pm else None,
                'daysInactive': days_inactive
            })
        
        avg_pms = round(total_pms / len(employees), 1) if employees else 0
        
        return jsonify({
            'employees': employees,
            'summary': {
                'totalEmployees': len(employees),
                'totalPMs': total_pms,
                'topPerformer': top_performer,
                'avgPMsPerTech': avg_pms
            },
            'period': period_label
        })
        
    except Exception as e:
        logger.error(f"PM technician performance query failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@pm_technician_performance_bp.route('/api/reports/service/pm-technician-details', methods=['GET'])
@jwt_required()
def get_pm_technician_details():
    """
    Get detailed PM list for a specific technician.
    """
    try:
        technician = request.args.get('technician')
        if not technician:
            return jsonify({'error': 'Technician name required'}), 400
        
        # Parse date range
        days = request.args.get('days', type=int)
        if days:
            end = datetime.now().date()
            start = end - timedelta(days=days)
        else:
            start = "2025-11-01"
            end = datetime.now().date()
        
        sql_service = get_tenant_db()
        
        # Query pattern copied from department_reports.py
        # Only shows INVOICED PMs (wo.InvoiceDate IS NOT NULL)
        schema = get_tenant_schema()

        query = f"""
        SELECT
            l.WONo,
            l.DateOfLabor,
            l.Hours,
            wo.BillTo,
            billToCustomer.Name as BillToName,
            wo.ShipTo,
            shipToCustomer.Name as ShipToName,
            wo.UnitNo,
            wo.SerialNo,
            wo.Model,
            wo.Make,
            wo.InvoiceDate
        FROM {schema}.WOLabor l
        INNER JOIN {schema}.WO wo ON l.WONo = wo.WONo
        LEFT JOIN {schema}.Customer shipToCustomer ON wo.ShipTo = shipToCustomer.Number
        LEFT JOIN {schema}.Customer billToCustomer ON wo.BillTo = billToCustomer.Number
        WHERE wo.Type = 'PM'
            AND wo.InvoiceDate IS NOT NULL
            AND l.MechanicName = %s
            AND l.DateOfLabor >= %s
            AND l.DateOfLabor <= %s
        ORDER BY l.DateOfLabor DESC
        """
        
        results = sql_service.execute_query(query, [technician, start, end])
        
        pms = []
        for row in results:
            pms.append({
                'woNo': row['WONo'],
                'laborDate': row['DateOfLabor'].strftime('%Y-%m-%d') if row['DateOfLabor'] else None,
                'hours': round(row['Hours'], 1) if row['Hours'] else 0,
                'shipTo': row['ShipTo'],
                'shipToName': row['ShipToName'],
                'billTo': row['BillTo'],
                'billToName': row['BillToName'],
                'unitNo': row['UnitNo'],
                'serialNo': row['SerialNo'],
                'model': row['Model'],
                'make': row['Make'],
                'invoiceDate': row['InvoiceDate'].strftime('%Y-%m-%d') if row['InvoiceDate'] else None
            })
        
        return jsonify({'pms': pms})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
