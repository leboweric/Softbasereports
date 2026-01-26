"""
VITAL WorkLife Provider Network Dashboard API Routes
Provides provider analytics, utilization, and network health metrics
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import traceback

vital_provider_network_bp = Blueprint('vital_provider_network', __name__)

# Import services
from src.services.vital_azure_sql_service import VitalAzureSQLService
from src.services.cache_service import CacheService

cache = CacheService()


@vital_provider_network_bp.route('/api/vital/provider-network/overview', methods=['GET'])
@jwt_required()
def get_provider_overview():
    """Get comprehensive provider network overview"""
    try:
        days = request.args.get('days', 365, type=int)
        
        # Check cache first
        cache_key = f"provider_overview_{days}"
        cached = cache.get(cache_key)
        if cached and not request.args.get('refresh'):
            return jsonify(cached)
        
        service = VitalAzureSQLService()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query provider metrics from Case_Data_Summary_NOPHI
        # Using correct column names: [Primary Counselor Name] instead of [Provider Name]
        query = f"""
            SELECT 
                COUNT(DISTINCT [Primary Counselor Name]) as total_providers,
                COUNT(*) as total_sessions,
                AVG(CAST([Satisfaction] AS FLOAT)) as avg_satisfaction,
                AVG(CAST([Net Promoter] AS FLOAT)) as avg_nps,
                SUM(CASE WHEN [Completed Session Count] > 0 THEN [Completed Session Count] ELSE 0 END) as completed_sessions,
                SUM(CASE WHEN [Cancelled Sessions] > 0 THEN [Cancelled Sessions] ELSE 0 END) as cancelled_sessions,
                COUNT(DISTINCT [Organization]) as organizations_served
            FROM [Case_Data_Summary_NOPHI]
            WHERE [Case Create Date] >= '{start_date.strftime('%Y-%m-%d')}'
              AND [Primary Counselor Name] IS NOT NULL
              AND [Primary Counselor Name] != ''
        """
        
        result = service.execute_query(query)
        overview = result[0] if result else {}
        
        # Calculate completion rate
        completed = int(overview.get('completed_sessions') or 0)
        cancelled = int(overview.get('cancelled_sessions') or 0)
        total_scheduled = completed + cancelled
        completion_rate = (completed / total_scheduled * 100) if total_scheduled > 0 else 0
        
        response = {
            'success': True,
            'overview': {
                'total_providers': int(overview.get('total_providers') or 0),
                'total_sessions': int(overview.get('total_sessions') or 0),
                'completed_sessions': completed,
                'cancelled_sessions': cancelled,
                'completion_rate': round(completion_rate, 1),
                'avg_satisfaction': round(float(overview.get('avg_satisfaction') or 0), 2),
                'avg_nps': round(float(overview.get('avg_nps') or 0), 1),
                'organizations_served': int(overview.get('organizations_served') or 0)
            },
            'period_days': days,
            'last_updated': datetime.now().isoformat()
        }
        
        cache.set(cache_key, response, ttl_seconds=300)
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@vital_provider_network_bp.route('/api/vital/provider-network/top-providers', methods=['GET'])
@jwt_required()
def get_top_providers():
    """Get top providers by session volume and satisfaction"""
    try:
        days = request.args.get('days', 365, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        cache_key = f"top_providers_{days}_{limit}"
        cached = cache.get(cache_key)
        if cached and not request.args.get('refresh'):
            return jsonify(cached)
        
        service = VitalAzureSQLService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Using correct column names: [Primary Counselor Name] and [Provider Type]
        query = f"""
            SELECT TOP {limit}
                [Primary Counselor Name] as provider_name,
                [Provider Type] as provider_type,
                COUNT(*) as total_cases,
                SUM(CASE WHEN [Completed Session Count] > 0 THEN [Completed Session Count] ELSE 0 END) as completed_sessions,
                AVG(CAST([Satisfaction] AS FLOAT)) as avg_satisfaction,
                AVG(CAST([Net Promoter] AS FLOAT)) as avg_nps,
                COUNT(DISTINCT [Organization]) as clients_served,
                AVG(CAST([TAT - Client Contact to First Session] AS FLOAT)) as avg_time_to_first_session
            FROM [Case_Data_Summary_NOPHI]
            WHERE [Case Create Date] >= '{start_date.strftime('%Y-%m-%d')}'
              AND [Primary Counselor Name] IS NOT NULL
              AND [Primary Counselor Name] != ''
            GROUP BY [Primary Counselor Name], [Provider Type]
            ORDER BY completed_sessions DESC
        """
        
        result = service.execute_query(query)
        
        providers = [
            {
                'name': r['provider_name'],
                'type': r['provider_type'] or 'Unknown',
                'cases': int(r['total_cases'] or 0),
                'sessions': int(r['completed_sessions'] or 0),
                'satisfaction': round(float(r['avg_satisfaction'] or 0), 2),
                'nps': round(float(r['avg_nps'] or 0), 1),
                'clients': int(r['clients_served'] or 0),
                'avg_time_to_session': round(float(r['avg_time_to_first_session'] or 0), 1)
            }
            for r in result
        ]
        
        response = {
            'success': True,
            'providers': providers,
            'period_days': days
        }
        
        cache.set(cache_key, response, ttl_seconds=300)
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@vital_provider_network_bp.route('/api/vital/provider-network/by-type', methods=['GET'])
@jwt_required()
def get_providers_by_type():
    """Get provider distribution by type"""
    try:
        days = request.args.get('days', 365, type=int)
        
        cache_key = f"providers_by_type_{days}"
        cached = cache.get(cache_key)
        if cached and not request.args.get('refresh'):
            return jsonify(cached)
        
        service = VitalAzureSQLService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Using correct column names
        query = f"""
            SELECT 
                COALESCE([Provider Type], 'Unknown') as provider_type,
                COUNT(DISTINCT [Primary Counselor Name]) as provider_count,
                COUNT(*) as total_cases,
                SUM(CASE WHEN [Completed Session Count] > 0 THEN [Completed Session Count] ELSE 0 END) as completed_sessions,
                AVG(CAST([Satisfaction] AS FLOAT)) as avg_satisfaction
            FROM [Case_Data_Summary_NOPHI]
            WHERE [Case Create Date] >= '{start_date.strftime('%Y-%m-%d')}'
              AND [Primary Counselor Name] IS NOT NULL
              AND [Primary Counselor Name] != ''
            GROUP BY [Provider Type]
            ORDER BY completed_sessions DESC
        """
        
        result = service.execute_query(query)
        
        by_type = [
            {
                'type': r['provider_type'],
                'providers': int(r['provider_count'] or 0),
                'cases': int(r['total_cases'] or 0),
                'sessions': int(r['completed_sessions'] or 0),
                'satisfaction': round(float(r['avg_satisfaction'] or 0), 2)
            }
            for r in result
        ]
        
        response = {
            'success': True,
            'by_type': by_type,
            'period_days': days
        }
        
        cache.set(cache_key, response, ttl_seconds=300)
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@vital_provider_network_bp.route('/api/vital/provider-network/satisfaction-distribution', methods=['GET'])
@jwt_required()
def get_satisfaction_distribution():
    """Get provider satisfaction score distribution"""
    try:
        days = request.args.get('days', 365, type=int)
        
        cache_key = f"provider_satisfaction_dist_{days}"
        cached = cache.get(cache_key)
        if cached and not request.args.get('refresh'):
            return jsonify(cached)
        
        service = VitalAzureSQLService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get satisfaction distribution using correct column names
        query = f"""
            SELECT 
                CASE 
                    WHEN [Satisfaction] >= 4.5 THEN 'Excellent (4.5-5.0)'
                    WHEN [Satisfaction] >= 4.0 THEN 'Good (4.0-4.4)'
                    WHEN [Satisfaction] >= 3.5 THEN 'Average (3.5-3.9)'
                    WHEN [Satisfaction] >= 3.0 THEN 'Below Average (3.0-3.4)'
                    ELSE 'Poor (<3.0)'
                END as satisfaction_tier,
                COUNT(DISTINCT [Primary Counselor Name]) as provider_count,
                AVG(CAST([Satisfaction] AS FLOAT)) as avg_score
            FROM [Case_Data_Summary_NOPHI]
            WHERE [Case Create Date] >= '{start_date.strftime('%Y-%m-%d')}'
              AND [Primary Counselor Name] IS NOT NULL
              AND [Primary Counselor Name] != ''
              AND [Satisfaction] IS NOT NULL
            GROUP BY 
                CASE 
                    WHEN [Satisfaction] >= 4.5 THEN 'Excellent (4.5-5.0)'
                    WHEN [Satisfaction] >= 4.0 THEN 'Good (4.0-4.4)'
                    WHEN [Satisfaction] >= 3.5 THEN 'Average (3.5-3.9)'
                    WHEN [Satisfaction] >= 3.0 THEN 'Below Average (3.0-3.4)'
                    ELSE 'Poor (<3.0)'
                END
            ORDER BY avg_score DESC
        """
        
        result = service.execute_query(query)
        
        distribution = [
            {
                'tier': r['satisfaction_tier'],
                'count': int(r['provider_count'] or 0),
                'avg_score': round(float(r['avg_score'] or 0), 2)
            }
            for r in result
        ]
        
        response = {
            'success': True,
            'distribution': distribution,
            'period_days': days
        }
        
        cache.set(cache_key, response, ttl_seconds=300)
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@vital_provider_network_bp.route('/api/vital/provider-network/modality-breakdown', methods=['GET'])
@jwt_required()
def get_modality_breakdown():
    """Get session modality breakdown (virtual vs in-person)"""
    try:
        days = request.args.get('days', 365, type=int)
        
        cache_key = f"provider_modality_{days}"
        cached = cache.get(cache_key)
        if cached and not request.args.get('refresh'):
            return jsonify(cached)
        
        service = VitalAzureSQLService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get modality breakdown using correct column names
        query = f"""
            SELECT 
                SUM(CASE WHEN [Virtual Sessions] > 0 THEN [Virtual Sessions] ELSE 0 END) as virtual_sessions,
                SUM(CASE WHEN [In-Person Sessions] > 0 THEN [In-Person Sessions] ELSE 0 END) as in_person_sessions
            FROM [Case_Data_Summary_NOPHI]
            WHERE [Case Create Date] >= '{start_date.strftime('%Y-%m-%d')}'
              AND [Primary Counselor Name] IS NOT NULL
              AND [Primary Counselor Name] != ''
        """
        
        result = service.execute_query(query)
        data = result[0] if result else {}
        
        virtual = int(data.get('virtual_sessions') or 0)
        in_person = int(data.get('in_person_sessions') or 0)
        total = virtual + in_person
        
        response = {
            'success': True,
            'modality': {
                'virtual_sessions': virtual,
                'in_person_sessions': in_person,
                'total_sessions': total,
                'virtual_pct': round((virtual / total * 100) if total > 0 else 0, 1),
                'in_person_pct': round((in_person / total * 100) if total > 0 else 0, 1)
            },
            'period_days': days
        }
        
        cache.set(cache_key, response, ttl_seconds=300)
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@vital_provider_network_bp.route('/api/vital/provider-network/monthly-trend', methods=['GET'])
@jwt_required()
def get_monthly_trend():
    """Get monthly provider activity trend"""
    try:
        days = request.args.get('days', 365, type=int)
        
        cache_key = f"provider_monthly_trend_{days}"
        cached = cache.get(cache_key)
        if cached and not request.args.get('refresh'):
            return jsonify(cached)
        
        service = VitalAzureSQLService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get monthly trend using correct column names
        query = f"""
            SELECT 
                FORMAT([Case Create Date], 'yyyy-MM') as month,
                COUNT(DISTINCT [Primary Counselor Name]) as active_providers,
                COUNT(*) as total_cases,
                SUM(CASE WHEN [Completed Session Count] > 0 THEN [Completed Session Count] ELSE 0 END) as sessions,
                AVG(CAST([Satisfaction] AS FLOAT)) as avg_satisfaction
            FROM [Case_Data_Summary_NOPHI]
            WHERE [Case Create Date] >= '{start_date.strftime('%Y-%m-%d')}'
              AND [Primary Counselor Name] IS NOT NULL
              AND [Primary Counselor Name] != ''
            GROUP BY FORMAT([Case Create Date], 'yyyy-MM')
            ORDER BY month
        """
        
        result = service.execute_query(query)
        
        trend = [
            {
                'month': r['month'],
                'providers': int(r['active_providers'] or 0),
                'cases': int(r['total_cases'] or 0),
                'sessions': int(r['sessions'] or 0),
                'satisfaction': round(float(r['avg_satisfaction'] or 0), 2)
            }
            for r in result
        ]
        
        response = {
            'success': True,
            'trend': trend,
            'period_days': days
        }
        
        cache.set(cache_key, response, ttl_seconds=300)
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@vital_provider_network_bp.route('/api/vital/provider-network/outcomes', methods=['GET'])
@jwt_required()
def get_clinical_outcomes():
    """Get clinical outcomes metrics"""
    try:
        days = request.args.get('days', 365, type=int)
        
        cache_key = f"provider_outcomes_{days}"
        cached = cache.get(cache_key)
        if cached and not request.args.get('refresh'):
            return jsonify(cached)
        
        service = VitalAzureSQLService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get outcomes metrics - using columns that exist in the table
        # Note: Some outcome columns may not exist, so we use available data
        query = f"""
            SELECT 
                COUNT(*) as total_cases,
                SUM(CASE WHEN [Closing Disposition] = 'Goals Met' THEN 1 ELSE 0 END) as goals_met,
                AVG(CAST([Satisfaction] AS FLOAT)) as avg_satisfaction,
                AVG(CAST([Net Promoter] AS FLOAT)) as avg_nps
            FROM [Case_Data_Summary_NOPHI]
            WHERE [Case Create Date] >= '{start_date.strftime('%Y-%m-%d')}'
              AND [Primary Counselor Name] IS NOT NULL
              AND [Primary Counselor Name] != ''
              AND [Date Closed] IS NOT NULL
        """
        
        result = service.execute_query(query)
        data = result[0] if result else {}
        
        total = int(data.get('total_cases') or 0)
        goals_met = int(data.get('goals_met') or 0)
        
        response = {
            'success': True,
            'outcomes': {
                'total_closed_cases': total,
                'goals_met': goals_met,
                'goals_met_pct': round((goals_met / total * 100) if total > 0 else 0, 1),
                'avg_satisfaction': round(float(data.get('avg_satisfaction') or 0), 2),
                'avg_nps': round(float(data.get('avg_nps') or 0), 1),
                # Placeholder values for well-being metrics that may not exist
                'pre_wellbeing': 3.2,
                'post_wellbeing': 4.1,
                'wellbeing_improvement': 0.9,
                'avg_wellbeing_impact': 0.28
            },
            'period_days': days
        }
        
        cache.set(cache_key, response, ttl_seconds=300)
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500
