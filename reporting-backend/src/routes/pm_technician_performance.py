from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from src.services.azure_sql_service import AzureSQLService
from flask_jwt_extended import jwt_required

pm_technician_performance_bp = Blueprint('pm_technician_performance', __name__)

@pm_technician_performance_bp.route('/api/reports/service/pm-technician-performance', methods=['GET'])
@jwt_required()
def get_pm_technician_performance():
    """
    Get PM completion performance by technician for contest tracking
    """
    try:
        # Get query parameters
        days = request.args.get('days', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Calculate date range
        if start_date and end_date:
            start = start_date
            end = end_date
            period_label = f"{start} to {end}"
        elif days:
            end = datetime.now().date()
            start = end - timedelta(days=days)
            period_label = f"Last {days} days"
        else:
            # Default to contest period (Nov 1, 2025 to today)
            start = "2025-11-01"
            end = datetime.now().date()
            period_label = f"{start} to {end}"
        
        sql_service = AzureSQLService()
        
        # Query to get PM completions by technician
        query = """
        WITH TechPMs AS (
            SELECT 
                l.MechanicName as technician,
                l.WONo,
                l.DateOfLabor,
                l.Hours,
                wo.Customer,
                wo.UnitNo,
                wo.SerialNo,
                wo.Model
            FROM ben002.WOLabor l
            INNER JOIN ben002.WO wo ON l.WONo = wo.WONo
            WHERE wo.Type = 'PM'
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
                    'avgPerEmployee': 0,
                    'period': period_label
                }
            })
        
        # Calculate totals
        total_pms = sum(row['total_pms'] for row in results)
        total_employees = len(results)
        
        # Format employee data
        employees = []
        for row in results:
            tech_pms = row['total_pms']
            days_worked = row['days_worked'] or 1
            total_hours = row['total_hours'] or 0
            
            employees.append({
                'employeeId': row['technician'],
                'employeeName': row['technician'],
                'totalPMs': tech_pms,
                'percentOfTotal': round((tech_pms / total_pms * 100), 1) if total_pms > 0 else 0,
                'daysWorked': days_worked,
                'avgDailyPMs': round(tech_pms / days_worked, 1),
                'totalHours': round(total_hours, 1),
                'avgTimePerPM': round(total_hours / tech_pms, 1) if tech_pms > 0 else 0,
                'lastPMDate': row['last_pm_date'].strftime('%Y-%m-%d') if row['last_pm_date'] else None,
                'daysInactive': row['days_inactive'] or 0
            })
        
        # Summary data
        summary = {
            'totalEmployees': total_employees,
            'totalPMs': total_pms,
            'topPerformer': employees[0] if employees else None,
            'avgPerEmployee': round(total_pms / total_employees, 1) if total_employees > 0 else 0,
            'period': period_label
        }
        
        return jsonify({
            'employees': employees,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pm_technician_performance_bp.route('/api/reports/service/pm-technician-details', methods=['GET'])
@jwt_required()
def get_pm_technician_details():
    """
    Get detailed PM list for a specific technician
    """
    try:
        technician = request.args.get('technician')
        days = request.args.get('days', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not technician:
            return jsonify({'error': 'Technician parameter required'}), 400
        
        # Calculate date range
        if start_date and end_date:
            start = start_date
            end = end_date
        elif days:
            end = datetime.now().date()
            start = end - timedelta(days=days)
        else:
            start = "2025-11-01"
            end = datetime.now().date()
        
        sql_service = AzureSQLService()
        
        query = """
        SELECT 
            l.WONo,
            l.DateOfLabor,
            l.Hours,
            wo.Customer,
            wo.UnitNo,
            wo.SerialNo,
            wo.Model,
            wo.Make,
            wo.BillToPhone as CustomerPhone
        FROM ben002.WOLabor l
        INNER JOIN ben002.WO wo ON l.WONo = wo.WONo
        WHERE wo.Type = 'PM'
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
                'customer': row['Customer'],
                'unitNo': row['UnitNo'],
                'serialNo': row['SerialNo'],
                'model': row['Model'],
                'make': row['Make'],
                'customerPhone': row['CustomerPhone']
            })
        
        return jsonify({'pms': pms})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
