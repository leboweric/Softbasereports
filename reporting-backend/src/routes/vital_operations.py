"""
Operational Efficiency Dashboard API Routes
Provides metrics for resource utilization, service delivery quality, and operational KPIs
"""
from flask import Blueprint, jsonify, request
from functools import wraps
import jwt
import os
from datetime import datetime, timedelta
from collections import defaultdict

from ..services.vital_azure_sql_service import VitalAzureSQLService
from ..services.cache_service import CacheService

vital_operations_bp = Blueprint('vital_operations', __name__, url_prefix='/api/vital/operations')
cache = CacheService()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Token is missing'}), 401
        
        if not token:
            return jsonify({'message': 'Missing Authorization Header'}), 401
        
        try:
            jwt.decode(token, os.environ.get('JWT_SECRET_KEY', 'dev-secret-key'), algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated


@vital_operations_bp.route('/dashboard', methods=['GET'])
@token_required
def get_operations_dashboard():
    """
    Get comprehensive operational efficiency metrics
    """
    try:
        days = request.args.get('days', 90, type=int)
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        cache_key = f"operations_dashboard_{days}"
        
        if not refresh:
            cached = cache.get(cache_key)
            if cached:
                return jsonify(cached)
        
        service = VitalAzureSQLService()
        
        # Get overall operational metrics
        metrics_query = f"""
        SELECT 
            COUNT(*) as total_cases,
            COUNT(CASE WHEN [Date Closed] IS NOT NULL THEN 1 END) as closed_cases,
            COUNT(CASE WHEN [Date Closed] IS NULL THEN 1 END) as open_cases,
            AVG(CAST([TAT - Client Contact to Case Closed] as FLOAT)) as avg_time_to_close,
            AVG(CAST([TAT - Client Contact to First Session] as FLOAT)) as avg_time_to_first_session,
            AVG(CAST([TAT - Consultant Assigned to First Session] as FLOAT)) as avg_consultant_to_session,
            AVG(CAST([Satisfaction] as FLOAT)) as avg_satisfaction,
            AVG(CAST([Net Promoter] as FLOAT)) as avg_nps,
            COUNT(CASE WHEN [Completed Session Count] > 0 THEN 1 END) as cases_with_sessions,
            SUM(CAST([Completed Session Count] as INT)) as total_sessions,
            AVG(CAST([Completed Session Count] as FLOAT)) as avg_sessions_per_case
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(day, -{days}, GETDATE())
        """
        
        metrics_result = service.execute_query(metrics_query)
        metrics = metrics_result[0] if metrics_result else {}
        
        # Get case manager workload
        workload_query = f"""
        SELECT TOP 20
            [Case Manager] as case_manager,
            COUNT(*) as total_cases,
            COUNT(CASE WHEN [Date Closed] IS NULL THEN 1 END) as open_cases,
            AVG(CAST([TAT - Client Contact to Case Closed] as FLOAT)) as avg_close_time,
            AVG(CAST([Satisfaction] as FLOAT)) as avg_satisfaction
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(day, -{days}, GETDATE())
            AND [Case Manager] IS NOT NULL
        GROUP BY [Case Manager]
        ORDER BY COUNT(*) DESC
        """
        
        workload_result = service.execute_query(workload_query)
        
        # Get service delivery quality by case type
        quality_query = f"""
        SELECT 
            [Case Type] as case_type,
            COUNT(*) as total_cases,
            AVG(CAST([TAT - Client Contact to First Session] as FLOAT)) as avg_time_to_session,
            AVG(CAST([Satisfaction] as FLOAT)) as avg_satisfaction,
            AVG(CAST([Net Promoter] as FLOAT)) as avg_nps,
            COUNT(CASE WHEN [Satisfaction] >= 4 THEN 1 END) * 100.0 / NULLIF(COUNT(CASE WHEN [Satisfaction] IS NOT NULL THEN 1 END), 0) as satisfaction_rate
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(day, -{days}, GETDATE())
            AND [Case Type] IS NOT NULL
        GROUP BY [Case Type]
        HAVING COUNT(*) >= 10
        ORDER BY COUNT(*) DESC
        """
        
        quality_result = service.execute_query(quality_query)
        
        # Get daily throughput trend
        throughput_query = f"""
        SELECT 
            CAST([Case Create Date] as DATE) as date,
            COUNT(*) as cases_opened,
            COUNT(CASE WHEN [Date Closed] IS NOT NULL THEN 1 END) as cases_closed
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(day, -{days}, GETDATE())
        GROUP BY CAST([Case Create Date] as DATE)
        ORDER BY CAST([Case Create Date] as DATE)
        """
        
        throughput_result = service.execute_query(throughput_query)
        
        # Get TAT distribution
        tat_query = f"""
        SELECT 
            CASE 
                WHEN [TAT - Client Contact to First Session] <= 1 THEN 'Same Day'
                WHEN [TAT - Client Contact to First Session] <= 3 THEN '1-3 Days'
                WHEN [TAT - Client Contact to First Session] <= 7 THEN '4-7 Days'
                WHEN [TAT - Client Contact to First Session] <= 14 THEN '8-14 Days'
                ELSE '15+ Days'
            END as tat_bucket,
            COUNT(*) as count
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(day, -{days}, GETDATE())
            AND [TAT - Client Contact to First Session] IS NOT NULL
        GROUP BY 
            CASE 
                WHEN [TAT - Client Contact to First Session] <= 1 THEN 'Same Day'
                WHEN [TAT - Client Contact to First Session] <= 3 THEN '1-3 Days'
                WHEN [TAT - Client Contact to First Session] <= 7 THEN '4-7 Days'
                WHEN [TAT - Client Contact to First Session] <= 14 THEN '8-14 Days'
                ELSE '15+ Days'
            END
        """
        
        tat_result = service.execute_query(tat_query)
        
        # Calculate efficiency score (composite metric)
        efficiency_score = 0
        if metrics:
            # Components: close rate, satisfaction, NPS, TAT performance
            close_rate = (metrics.get('closed_cases', 0) / max(metrics.get('total_cases', 1), 1)) * 25
            sat_score = ((metrics.get('avg_satisfaction', 0) or 0) / 5) * 25
            nps_score = (((metrics.get('avg_nps', 0) or 0) + 100) / 200) * 25  # NPS ranges -100 to 100
            tat_score = max(0, 25 - ((metrics.get('avg_time_to_first_session', 7) or 7) / 7) * 25)  # Lower is better
            efficiency_score = round(close_rate + sat_score + nps_score + tat_score, 1)
        
        result = {
            'overview': {
                'total_cases': metrics.get('total_cases', 0),
                'closed_cases': metrics.get('closed_cases', 0),
                'open_cases': metrics.get('open_cases', 0),
                'close_rate': round((metrics.get('closed_cases', 0) / max(metrics.get('total_cases', 1), 1)) * 100, 1),
                'avg_time_to_close': round(metrics.get('avg_time_to_close', 0) or 0, 1),
                'avg_time_to_first_session': round(metrics.get('avg_time_to_first_session', 0) or 0, 1),
                'avg_satisfaction': round(metrics.get('avg_satisfaction', 0) or 0, 2),
                'avg_nps': round(metrics.get('avg_nps', 0) or 0, 1),
                'total_sessions': metrics.get('total_sessions', 0) or 0,
                'avg_sessions_per_case': round(metrics.get('avg_sessions_per_case', 0) or 0, 1),
                'efficiency_score': efficiency_score
            },
            'case_manager_workload': [
                {
                    'case_manager': row.get('case_manager'),
                    'total_cases': row.get('total_cases', 0),
                    'open_cases': row.get('open_cases', 0),
                    'avg_close_time': round(row.get('avg_close_time', 0) or 0, 1),
                    'avg_satisfaction': round(row.get('avg_satisfaction', 0) or 0, 2)
                }
                for row in (workload_result or [])
            ],
            'quality_by_case_type': [
                {
                    'case_type': row.get('case_type'),
                    'total_cases': row.get('total_cases', 0),
                    'avg_time_to_session': round(row.get('avg_time_to_session', 0) or 0, 1),
                    'avg_satisfaction': round(row.get('avg_satisfaction', 0) or 0, 2),
                    'avg_nps': round(row.get('avg_nps', 0) or 0, 1),
                    'satisfaction_rate': round(row.get('satisfaction_rate', 0) or 0, 1)
                }
                for row in (quality_result or [])
            ],
            'daily_throughput': [
                {
                    'date': str(row.get('date', ''))[:10],
                    'opened': row.get('cases_opened', 0),
                    'closed': row.get('cases_closed', 0)
                }
                for row in (throughput_result or [])
            ],
            'tat_distribution': [
                {
                    'bucket': row.get('tat_bucket'),
                    'count': row.get('count', 0)
                }
                for row in (tat_result or [])
            ]
        }
        
        cache.set(cache_key, result, ttl=300)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_operations_bp.route('/capacity', methods=['GET'])
@token_required
def get_capacity_metrics():
    """
    Get capacity and resource utilization metrics
    """
    try:
        days = request.args.get('days', 30, type=int)
        
        service = VitalAzureSQLService()
        
        # Get weekly case volume to understand capacity needs
        capacity_query = f"""
        SELECT 
            DATEPART(week, [Case Create Date]) as week_num,
            MIN(CAST([Case Create Date] as DATE)) as week_start,
            COUNT(*) as cases_opened,
            COUNT(DISTINCT [Case Manager]) as active_case_managers,
            COUNT(DISTINCT [Organization]) as active_orgs,
            AVG(CAST([Completed Session Count] as FLOAT)) as avg_sessions
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(day, -{days}, GETDATE())
        GROUP BY DATEPART(week, [Case Create Date])
        ORDER BY MIN(CAST([Case Create Date] as DATE))
        """
        
        capacity_result = service.execute_query(capacity_query)
        
        # Get case manager capacity utilization
        utilization_query = f"""
        SELECT 
            [Case Manager] as case_manager,
            COUNT(*) as total_cases,
            SUM(CAST([Completed Session Count] as INT)) as total_sessions,
            COUNT(DISTINCT [Organization]) as unique_orgs,
            AVG(CAST([TAT - Client Contact to First Session] as FLOAT)) as avg_response_time
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(day, -{days}, GETDATE())
            AND [Case Manager] IS NOT NULL
        GROUP BY [Case Manager]
        HAVING COUNT(*) >= 5
        ORDER BY COUNT(*) DESC
        """
        
        utilization_result = service.execute_query(utilization_query)
        
        # Calculate average cases per manager
        if utilization_result:
            avg_cases = sum(r.get('total_cases', 0) for r in utilization_result) / len(utilization_result)
        else:
            avg_cases = 0
        
        return jsonify({
            'weekly_volume': [
                {
                    'week': row.get('week_num'),
                    'week_start': str(row.get('week_start', ''))[:10],
                    'cases': row.get('cases_opened', 0),
                    'case_managers': row.get('active_case_managers', 0),
                    'orgs': row.get('active_orgs', 0),
                    'avg_sessions': round(row.get('avg_sessions', 0) or 0, 1)
                }
                for row in (capacity_result or [])
            ],
            'case_manager_utilization': [
                {
                    'case_manager': row.get('case_manager'),
                    'cases': row.get('total_cases', 0),
                    'sessions': row.get('total_sessions', 0) or 0,
                    'orgs': row.get('unique_orgs', 0),
                    'avg_response_time': round(row.get('avg_response_time', 0) or 0, 1),
                    'utilization_pct': round((row.get('total_cases', 0) / max(avg_cases, 1)) * 100, 1)
                }
                for row in (utilization_result or [])
            ],
            'avg_cases_per_manager': round(avg_cases, 1)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_operations_bp.route('/sla-compliance', methods=['GET'])
@token_required
def get_sla_compliance():
    """
    Get SLA compliance metrics based on TAT thresholds
    """
    try:
        days = request.args.get('days', 30, type=int)
        
        service = VitalAzureSQLService()
        
        # Define SLA thresholds (in days)
        SLA_FIRST_SESSION = 3  # First session within 3 days
        SLA_CASE_CLOSE = 30    # Case closed within 30 days
        
        sla_query = f"""
        SELECT 
            COUNT(*) as total_cases,
            COUNT(CASE WHEN [TAT - Client Contact to First Session] <= {SLA_FIRST_SESSION} THEN 1 END) as first_session_met,
            COUNT(CASE WHEN [TAT - Client Contact to First Session] > {SLA_FIRST_SESSION} THEN 1 END) as first_session_missed,
            COUNT(CASE WHEN [TAT - Client Contact to Case Closed] <= {SLA_CASE_CLOSE} THEN 1 END) as close_time_met,
            COUNT(CASE WHEN [TAT - Client Contact to Case Closed] > {SLA_CASE_CLOSE} THEN 1 END) as close_time_missed,
            AVG(CAST([TAT - Client Contact to First Session] as FLOAT)) as avg_first_session_tat,
            AVG(CAST([TAT - Client Contact to Case Closed] as FLOAT)) as avg_close_tat
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(day, -{days}, GETDATE())
        """
        
        sla_result = service.execute_query(sla_query)
        sla = sla_result[0] if sla_result else {}
        
        # Get SLA compliance by case type
        by_type_query = f"""
        SELECT 
            [Case Type] as case_type,
            COUNT(*) as total,
            COUNT(CASE WHEN [TAT - Client Contact to First Session] <= {SLA_FIRST_SESSION} THEN 1 END) * 100.0 / COUNT(*) as first_session_compliance,
            AVG(CAST([TAT - Client Contact to First Session] as FLOAT)) as avg_tat
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(day, -{days}, GETDATE())
            AND [Case Type] IS NOT NULL
        GROUP BY [Case Type]
        HAVING COUNT(*) >= 10
        ORDER BY COUNT(*) DESC
        """
        
        by_type_result = service.execute_query(by_type_query)
        
        total = sla.get('total_cases', 0) or 1
        first_session_total = (sla.get('first_session_met', 0) or 0) + (sla.get('first_session_missed', 0) or 0) or 1
        close_total = (sla.get('close_time_met', 0) or 0) + (sla.get('close_time_missed', 0) or 0) or 1
        
        return jsonify({
            'sla_thresholds': {
                'first_session_days': SLA_FIRST_SESSION,
                'case_close_days': SLA_CASE_CLOSE
            },
            'overall': {
                'total_cases': total,
                'first_session_compliance': round((sla.get('first_session_met', 0) or 0) / first_session_total * 100, 1),
                'close_time_compliance': round((sla.get('close_time_met', 0) or 0) / close_total * 100, 1),
                'avg_first_session_tat': round(sla.get('avg_first_session_tat', 0) or 0, 1),
                'avg_close_tat': round(sla.get('avg_close_tat', 0) or 0, 1)
            },
            'by_case_type': [
                {
                    'case_type': row.get('case_type'),
                    'total': row.get('total', 0),
                    'compliance_pct': round(row.get('first_session_compliance', 0) or 0, 1),
                    'avg_tat': round(row.get('avg_tat', 0) or 0, 1)
                }
                for row in (by_type_result or [])
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
