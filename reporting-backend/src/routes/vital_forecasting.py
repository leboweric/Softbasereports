"""
Demand Forecasting API Routes
Provides projected case volume, capacity planning, and trend analysis
"""
from flask import Blueprint, jsonify, request
from functools import wraps
import jwt
import os
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from ..services.vital_azure_sql_service import VitalAzureSQLService
from ..services.cache_service import CacheService

vital_forecasting_bp = Blueprint('vital_forecasting', __name__, url_prefix='/api/vital/forecasting')
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


def calculate_trend(values):
    """Calculate linear trend from a list of values"""
    if len(values) < 2:
        return 0
    
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    
    numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return 0
    
    return numerator / denominator


def forecast_values(historical_values, periods_ahead=4):
    """
    Simple linear regression forecast
    Returns list of forecasted values
    """
    if len(historical_values) < 3:
        avg = sum(historical_values) / len(historical_values) if historical_values else 0
        return [avg] * periods_ahead
    
    trend = calculate_trend(historical_values)
    last_value = historical_values[-1]
    
    forecasts = []
    for i in range(1, periods_ahead + 1):
        forecast = last_value + (trend * i)
        forecasts.append(max(0, round(forecast)))  # Ensure non-negative
    
    return forecasts


@vital_forecasting_bp.route('/demand', methods=['GET'])
@token_required
def get_demand_forecast():
    """
    Get demand forecast based on historical case volume
    """
    try:
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        cache_key = "demand_forecast"
        
        if not refresh:
            cached = cache.get(cache_key)
            if cached:
                return jsonify(cached)
        
        service = VitalAzureSQLService()
        
        # Get weekly case volume for the past 6 months
        historical_query = """
        SELECT 
            DATEPART(year, [Case Create Date]) as year,
            DATEPART(week, [Case Create Date]) as week,
            MIN(CAST([Case Create Date] as DATE)) as week_start,
            COUNT(*) as cases,
            COUNT(DISTINCT [Organization]) as orgs,
            COUNT(DISTINCT [Case Manager]) as case_managers
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(month, -6, GETDATE())
        GROUP BY DATEPART(year, [Case Create Date]), DATEPART(week, [Case Create Date])
        ORDER BY DATEPART(year, [Case Create Date]), DATEPART(week, [Case Create Date])
        """
        
        historical_result = service.execute_query(historical_query)
        
        # Get monthly volume for longer trend
        monthly_query = """
        SELECT 
            DATEPART(year, [Case Create Date]) as year,
            DATEPART(month, [Case Create Date]) as month,
            COUNT(*) as cases,
            COUNT(DISTINCT [Organization]) as orgs
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(year, -2, GETDATE())
        GROUP BY DATEPART(year, [Case Create Date]), DATEPART(month, [Case Create Date])
        ORDER BY DATEPART(year, [Case Create Date]), DATEPART(month, [Case Create Date])
        """
        
        monthly_result = service.execute_query(monthly_query)
        
        # Extract case volumes for forecasting
        weekly_volumes = [row.get('cases', 0) for row in (historical_result or [])]
        monthly_volumes = [row.get('cases', 0) for row in (monthly_result or [])]
        
        # Calculate forecasts
        weekly_forecast = forecast_values(weekly_volumes[-12:], periods_ahead=8)  # Next 8 weeks
        monthly_forecast = forecast_values(monthly_volumes[-12:], periods_ahead=6)  # Next 6 months
        
        # Calculate statistics
        if weekly_volumes:
            avg_weekly = statistics.mean(weekly_volumes)
            std_weekly = statistics.stdev(weekly_volumes) if len(weekly_volumes) > 1 else 0
        else:
            avg_weekly = 0
            std_weekly = 0
        
        # Get case type distribution for demand breakdown
        type_query = """
        SELECT 
            [Case Type] as case_type,
            COUNT(*) as count,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(month, -3, GETDATE())
            AND [Case Type] IS NOT NULL
        GROUP BY [Case Type]
        ORDER BY COUNT(*) DESC
        """
        
        type_result = service.execute_query(type_query)
        
        # Build forecast data with dates
        forecast_weeks = []
        if historical_result:
            last_week = historical_result[-1]
            last_date = datetime.strptime(str(last_week.get('week_start', ''))[:10], '%Y-%m-%d')
            for i, forecast in enumerate(weekly_forecast):
                forecast_date = last_date + timedelta(weeks=i+1)
                forecast_weeks.append({
                    'week_start': forecast_date.strftime('%Y-%m-%d'),
                    'forecasted_cases': forecast,
                    'lower_bound': max(0, round(forecast - std_weekly)),
                    'upper_bound': round(forecast + std_weekly)
                })
        
        result = {
            'historical': {
                'weekly': [
                    {
                        'week_start': str(row.get('week_start', ''))[:10],
                        'cases': row.get('cases', 0),
                        'orgs': row.get('orgs', 0),
                        'case_managers': row.get('case_managers', 0)
                    }
                    for row in (historical_result or [])
                ],
                'monthly': [
                    {
                        'year': row.get('year'),
                        'month': row.get('month'),
                        'cases': row.get('cases', 0),
                        'orgs': row.get('orgs', 0)
                    }
                    for row in (monthly_result or [])
                ]
            },
            'forecast': {
                'weekly': forecast_weeks,
                'monthly': monthly_forecast
            },
            'statistics': {
                'avg_weekly_volume': round(avg_weekly, 1),
                'weekly_std_dev': round(std_weekly, 1),
                'trend_direction': 'increasing' if calculate_trend(weekly_volumes[-8:]) > 0 else 'decreasing',
                'trend_strength': abs(round(calculate_trend(weekly_volumes[-8:]), 2))
            },
            'demand_by_type': [
                {
                    'case_type': row.get('case_type'),
                    'count': row.get('count', 0),
                    'percentage': round(row.get('percentage', 0) or 0, 1)
                }
                for row in (type_result or [])[:10]
            ]
        }
        
        cache.set(cache_key, result, ttl=3600)  # Cache for 1 hour
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_forecasting_bp.route('/capacity-planning', methods=['GET'])
@token_required
def get_capacity_planning():
    """
    Get capacity planning recommendations based on demand forecast
    """
    try:
        service = VitalAzureSQLService()
        
        # Get current capacity metrics
        capacity_query = """
        SELECT 
            COUNT(DISTINCT [Case Manager]) as active_case_managers,
            COUNT(*) as total_cases_30d,
            AVG(CAST([Completed Session Count] as FLOAT)) as avg_sessions_per_case
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(day, -30, GETDATE())
        """
        
        capacity_result = service.execute_query(capacity_query)
        capacity = capacity_result[0] if capacity_result else {}
        
        # Get provider utilization
        provider_query = """
        SELECT 
            COUNT(DISTINCT [Provider Type]) as provider_types,
            COUNT(CASE WHEN [Initial Session Modality] = 'Virtual' THEN 1 END) as virtual_sessions,
            COUNT(CASE WHEN [Initial Session Modality] = 'In-Person' THEN 1 END) as in_person_sessions
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(day, -30, GETDATE())
        """
        
        provider_result = service.execute_query(provider_query)
        provider = provider_result[0] if provider_result else {}
        
        # Calculate capacity metrics
        case_managers = capacity.get('active_case_managers', 1) or 1
        cases_30d = capacity.get('total_cases_30d', 0) or 0
        cases_per_manager = cases_30d / case_managers
        
        # Estimate capacity (assuming 80% utilization target)
        target_utilization = 0.8
        current_utilization = min(1.0, cases_per_manager / 50)  # Assuming 50 cases/month is full capacity
        
        # Forecast demand (simplified)
        weekly_query = """
        SELECT COUNT(*) as cases
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(day, -7, GETDATE())
        """
        weekly_result = service.execute_query(weekly_query)
        weekly_cases = weekly_result[0].get('cases', 0) if weekly_result else 0
        
        projected_monthly = weekly_cases * 4.3  # Approximate monthly projection
        
        # Calculate staffing needs
        optimal_caseload = 50  # Cases per manager per month
        needed_managers = projected_monthly / optimal_caseload
        current_capacity = case_managers * optimal_caseload * target_utilization
        
        capacity_gap = projected_monthly - current_capacity
        
        return jsonify({
            'current_state': {
                'active_case_managers': case_managers,
                'cases_last_30_days': cases_30d,
                'cases_per_manager': round(cases_per_manager, 1),
                'current_utilization': round(current_utilization * 100, 1),
                'avg_sessions_per_case': round(capacity.get('avg_sessions_per_case', 0) or 0, 1)
            },
            'projections': {
                'weekly_run_rate': weekly_cases,
                'projected_monthly_demand': round(projected_monthly),
                'current_monthly_capacity': round(current_capacity),
                'capacity_gap': round(capacity_gap),
                'gap_status': 'over_capacity' if capacity_gap > 0 else 'under_capacity'
            },
            'recommendations': {
                'optimal_caseload_per_manager': optimal_caseload,
                'managers_needed_for_demand': round(needed_managers, 1),
                'additional_managers_needed': max(0, round(needed_managers - case_managers, 1)),
                'utilization_target': f"{int(target_utilization * 100)}%"
            },
            'modality_split': {
                'virtual': provider.get('virtual_sessions', 0) or 0,
                'in_person': provider.get('in_person_sessions', 0) or 0,
                'virtual_pct': round((provider.get('virtual_sessions', 0) or 0) / max(cases_30d, 1) * 100, 1)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_forecasting_bp.route('/seasonality', methods=['GET'])
@token_required
def get_seasonality_analysis():
    """
    Analyze seasonal patterns in case volume
    """
    try:
        service = VitalAzureSQLService()
        
        # Get monthly patterns over 2 years
        monthly_query = """
        SELECT 
            DATEPART(month, [Case Create Date]) as month,
            DATENAME(month, [Case Create Date]) as month_name,
            AVG(CAST(cnt as FLOAT)) as avg_cases,
            MIN(cnt) as min_cases,
            MAX(cnt) as max_cases
        FROM (
            SELECT 
                DATEPART(year, [Case Create Date]) as year,
                DATEPART(month, [Case Create Date]) as month,
                COUNT(*) as cnt
            FROM [Case_Data_Summary_NOPHI]
            WHERE [Case Create Date] >= DATEADD(year, -2, GETDATE())
            GROUP BY DATEPART(year, [Case Create Date]), DATEPART(month, [Case Create Date])
        ) monthly
        GROUP BY DATEPART(month, [Case Create Date]), DATENAME(month, [Case Create Date])
        ORDER BY DATEPART(month, [Case Create Date])
        """
        
        monthly_result = service.execute_query(monthly_query)
        
        # Get day of week patterns
        dow_query = """
        SELECT 
            DATEPART(weekday, [Case Create Date]) as day_num,
            DATENAME(weekday, [Case Create Date]) as day_name,
            COUNT(*) as cases
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= DATEADD(month, -3, GETDATE())
        GROUP BY DATEPART(weekday, [Case Create Date]), DATENAME(weekday, [Case Create Date])
        ORDER BY DATEPART(weekday, [Case Create Date])
        """
        
        dow_result = service.execute_query(dow_query)
        
        # Calculate seasonal indices
        if monthly_result:
            avg_monthly = sum(row.get('avg_cases', 0) or 0 for row in monthly_result) / 12
            seasonal_indices = [
                {
                    'month': row.get('month'),
                    'month_name': row.get('month_name'),
                    'avg_cases': round(row.get('avg_cases', 0) or 0),
                    'seasonal_index': round((row.get('avg_cases', 0) or 0) / max(avg_monthly, 1), 2),
                    'range': f"{row.get('min_cases', 0)} - {row.get('max_cases', 0)}"
                }
                for row in monthly_result
            ]
        else:
            seasonal_indices = []
        
        return jsonify({
            'monthly_patterns': seasonal_indices,
            'day_of_week_patterns': [
                {
                    'day': row.get('day_name'),
                    'cases': row.get('cases', 0)
                }
                for row in (dow_result or [])
            ],
            'insights': {
                'peak_month': max(seasonal_indices, key=lambda x: x['avg_cases'])['month_name'] if seasonal_indices else None,
                'low_month': min(seasonal_indices, key=lambda x: x['avg_cases'])['month_name'] if seasonal_indices else None,
                'peak_day': max(dow_result, key=lambda x: x.get('cases', 0))['day_name'] if dow_result else None
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
