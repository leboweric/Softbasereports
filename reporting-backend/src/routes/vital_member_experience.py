"""
VITAL Member Experience Dashboard Routes
Provides API endpoints for member experience, service delivery, and utilization metrics from Azure SQL
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime, timedelta
from src.services.cache_service import cache_service

logger = logging.getLogger(__name__)

# Cache TTL for member experience data (5 minutes)
CACHE_TTL = 300

vital_member_experience_bp = Blueprint('vital_member_experience', __name__)


def get_azure_sql_service():
    """Get Azure SQL service instance"""
    from src.services.vital_azure_sql_service import VitalAzureSQLService
    return VitalAzureSQLService()


def is_vital_user():
    """Check if current user belongs to VITAL organization"""
    try:
        from src.models.user import User, Organization
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.organization_id:
            return False
        
        org = Organization.query.get(user.organization_id)
        if org and org.name:
            return 'vital' in org.name.lower()
        return False
    except Exception as e:
        logger.error(f"Error checking VITAL user: {str(e)}")
        return False


# ==================== HEALTH CHECK ====================

@vital_member_experience_bp.route('/api/vital/member-experience/health', methods=['GET'])
def member_experience_health_check():
    """Check Azure SQL API connectivity"""
    try:
        service = get_azure_sql_service()
        health = service.check_connection()
        return jsonify({
            "status": "healthy" if health.get("connected") else "error",
            "message": health.get("message", "Unknown")
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ==================== MEMBER EXPERIENCE ENDPOINTS ====================

@vital_member_experience_bp.route('/api/vital/member-experience/overview', methods=['GET'])
@jwt_required()
def get_member_experience_overview():
    """Get comprehensive member experience overview"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        days = request.args.get('days', 90, type=int)
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        cache_key = f"vital_member_exp_overview:{days}"
        
        # Check cache first
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                logger.info("Cache HIT for member experience overview")
                return jsonify({
                    "success": True,
                    "data": cached,
                    "from_cache": True
                })
        
        logger.info("Cache MISS for member experience overview, fetching from Azure SQL")
        service = get_azure_sql_service()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime("%Y-%m-%d")
        
        # Query for key metrics
        query = f"""
        SELECT 
            COUNT(*) as total_cases,
            COUNT(CASE WHEN [Date Closed] IS NULL THEN 1 END) as open_cases,
            COUNT(CASE WHEN [Date Closed] IS NOT NULL THEN 1 END) as closed_cases,
            AVG(CAST([Satisfaction] as FLOAT)) as avg_satisfaction,
            AVG(CAST([Net Promoter] as FLOAT)) as avg_nps,
            AVG(CAST([TAT - Client Contact to First Session] as FLOAT)) as avg_time_to_first_session,
            AVG(CAST([TAT - Client Contact to Case Closed] as FLOAT)) as avg_time_to_resolution,
            SUM(CAST([Completed Session Count] as INT)) as total_sessions,
            SUM(CAST([Web Logins] as INT)) as total_web_logins,
            SUM(CAST([Mobile App Count] as INT)) as total_mobile_app_usage,
            COUNT(CASE WHEN [Triage Tier] IN ('High', 'Crisis', 'Urgent') THEN 1 END) as high_acuity_cases
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= '{start_date_str}'
        """
        
        result = service.execute_query(query)
        
        if result and len(result) > 0:
            row = result[0]
            overview = {
                "total_cases": row.get("total_cases", 0) or 0,
                "open_cases": row.get("open_cases", 0) or 0,
                "closed_cases": row.get("closed_cases", 0) or 0,
                "avg_satisfaction": round(row.get("avg_satisfaction", 0) or 0, 2),
                "avg_nps": round(row.get("avg_nps", 0) or 0, 1),
                "avg_time_to_first_session": round(row.get("avg_time_to_first_session", 0) or 0, 1),
                "avg_time_to_resolution": round(row.get("avg_time_to_resolution", 0) or 0, 1),
                "total_sessions": row.get("total_sessions", 0) or 0,
                "total_web_logins": row.get("total_web_logins", 0) or 0,
                "total_mobile_app_usage": row.get("total_mobile_app_usage", 0) or 0,
                "high_acuity_cases": row.get("high_acuity_cases", 0) or 0,
                "period_days": days
            }
        else:
            overview = {
                "total_cases": 0,
                "open_cases": 0,
                "closed_cases": 0,
                "avg_satisfaction": 0,
                "avg_nps": 0,
                "avg_time_to_first_session": 0,
                "avg_time_to_resolution": 0,
                "total_sessions": 0,
                "total_web_logins": 0,
                "total_mobile_app_usage": 0,
                "high_acuity_cases": 0,
                "period_days": days
            }
        
        # Cache the result
        cache_service.set(cache_key, overview, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": overview,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"Member experience overview error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_member_experience_bp.route('/api/vital/member-experience/utilization-by-demographics', methods=['GET'])
@jwt_required()
def get_utilization_by_demographics():
    """Get utilization breakdown by member demographics"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        days = request.args.get('days', 90, type=int)
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        cache_key = f"vital_member_exp_demographics:{days}"
        
        # Check cache first
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                return jsonify({"success": True, "data": cached, "from_cache": True})
        
        service = get_azure_sql_service()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime("%Y-%m-%d")
        
        # By Client Type
        client_type_query = f"""
        SELECT 
            [Client Type] as client_type,
            COUNT(*) as case_count,
            AVG(CAST([Satisfaction] as FLOAT)) as avg_satisfaction
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= '{start_date_str}'
            AND [Client Type] IS NOT NULL
        GROUP BY [Client Type]
        ORDER BY case_count DESC
        """
        
        # By Role/Provider Type
        role_query = f"""
        SELECT TOP 15
            [Provider Type] as role,
            COUNT(*) as case_count,
            AVG(CAST([Satisfaction] as FLOAT)) as avg_satisfaction
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= '{start_date_str}'
            AND [Provider Type] IS NOT NULL
        GROUP BY [Provider Type]
        ORDER BY case_count DESC
        """
        
        # By Presenting Problem
        problem_query = f"""
        SELECT TOP 10
            [Primary Presenting Problem] as problem,
            COUNT(*) as case_count,
            AVG(CAST([Satisfaction] as FLOAT)) as avg_satisfaction
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= '{start_date_str}'
            AND [Primary Presenting Problem] IS NOT NULL
        GROUP BY [Primary Presenting Problem]
        ORDER BY case_count DESC
        """
        
        client_types = service.execute_query(client_type_query) or []
        roles = service.execute_query(role_query) or []
        problems = service.execute_query(problem_query) or []
        
        result = {
            "by_client_type": [
                {
                    "client_type": r.get("client_type", "Unknown"),
                    "case_count": r.get("case_count", 0),
                    "avg_satisfaction": round(r.get("avg_satisfaction", 0) or 0, 2)
                }
                for r in client_types
            ],
            "by_role": [
                {
                    "role": r.get("role", "Unknown"),
                    "case_count": r.get("case_count", 0),
                    "avg_satisfaction": round(r.get("avg_satisfaction", 0) or 0, 2)
                }
                for r in roles
            ],
            "by_presenting_problem": [
                {
                    "problem": r.get("problem", "Unknown"),
                    "case_count": r.get("case_count", 0),
                    "avg_satisfaction": round(r.get("avg_satisfaction", 0) or 0, 2)
                }
                for r in problems
            ],
            "period_days": days
        }
        
        # Cache the result
        cache_service.set(cache_key, result, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": result,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"Utilization by demographics error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_member_experience_bp.route('/api/vital/member-experience/access-times', methods=['GET'])
@jwt_required()
def get_access_times():
    """Get access and wait time metrics"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        days = request.args.get('days', 90, type=int)
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        cache_key = f"vital_member_exp_access_times:{days}"
        
        # Check cache first
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                return jsonify({"success": True, "data": cached, "from_cache": True})
        
        service = get_azure_sql_service()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime("%Y-%m-%d")
        
        # TAT metrics by month
        monthly_tat_query = f"""
        SELECT 
            FORMAT([Case Create Date], 'yyyy-MM') as month,
            AVG(CAST([TAT - Client Contact to First Session] as FLOAT)) as avg_time_to_first_session,
            AVG(CAST([TAT - Client Contact to Case Closed] as FLOAT)) as avg_time_to_resolution,
            AVG(CAST([TAT - Client Contact to Consultant Assigned] as FLOAT)) as avg_time_to_assignment,
            COUNT(*) as case_count
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= '{start_date_str}'
        GROUP BY FORMAT([Case Create Date], 'yyyy-MM')
        ORDER BY month
        """
        
        # TAT by case type
        tat_by_type_query = f"""
        SELECT TOP 10
            [Case Type] as case_type,
            AVG(CAST([TAT - Client Contact to First Session] as FLOAT)) as avg_time_to_first_session,
            AVG(CAST([TAT - Client Contact to Case Closed] as FLOAT)) as avg_time_to_resolution,
            COUNT(*) as case_count
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= '{start_date_str}'
            AND [Case Type] IS NOT NULL
        GROUP BY [Case Type]
        ORDER BY case_count DESC
        """
        
        monthly_tat = service.execute_query(monthly_tat_query) or []
        tat_by_type = service.execute_query(tat_by_type_query) or []
        
        result = {
            "monthly_trend": [
                {
                    "month": r.get("month", ""),
                    "avg_time_to_first_session": round(r.get("avg_time_to_first_session", 0) or 0, 1),
                    "avg_time_to_resolution": round(r.get("avg_time_to_resolution", 0) or 0, 1),
                    "avg_time_to_assignment": round(r.get("avg_time_to_assignment", 0) or 0, 1),
                    "case_count": r.get("case_count", 0)
                }
                for r in monthly_tat
            ],
            "by_case_type": [
                {
                    "case_type": r.get("case_type", "Unknown"),
                    "avg_time_to_first_session": round(r.get("avg_time_to_first_session", 0) or 0, 1),
                    "avg_time_to_resolution": round(r.get("avg_time_to_resolution", 0) or 0, 1),
                    "case_count": r.get("case_count", 0)
                }
                for r in tat_by_type
            ],
            "period_days": days
        }
        
        # Cache the result
        cache_service.set(cache_key, result, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": result,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"Access times error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_member_experience_bp.route('/api/vital/member-experience/satisfaction-analysis', methods=['GET'])
@jwt_required()
def get_satisfaction_analysis():
    """Get detailed satisfaction and NPS analysis"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        days = request.args.get('days', 90, type=int)
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        cache_key = f"vital_member_exp_satisfaction:{days}"
        
        # Check cache first
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                return jsonify({"success": True, "data": cached, "from_cache": True})
        
        service = get_azure_sql_service()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime("%Y-%m-%d")
        
        # Monthly satisfaction trend
        monthly_sat_query = f"""
        SELECT 
            FORMAT([Case Create Date], 'yyyy-MM') as month,
            AVG(CAST([Satisfaction] as FLOAT)) as avg_satisfaction,
            AVG(CAST([Net Promoter] as FLOAT)) as avg_nps,
            COUNT(*) as response_count
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= '{start_date_str}'
            AND [Satisfaction] IS NOT NULL
        GROUP BY FORMAT([Case Create Date], 'yyyy-MM')
        ORDER BY month
        """
        
        # Satisfaction by case type
        sat_by_type_query = f"""
        SELECT TOP 10
            [Case Type] as case_type,
            AVG(CAST([Satisfaction] as FLOAT)) as avg_satisfaction,
            AVG(CAST([Net Promoter] as FLOAT)) as avg_nps,
            COUNT(*) as response_count
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= '{start_date_str}'
            AND [Satisfaction] IS NOT NULL
            AND [Case Type] IS NOT NULL
        GROUP BY [Case Type]
        ORDER BY response_count DESC
        """
        
        # NPS distribution (Promoters, Passives, Detractors)
        nps_dist_query = f"""
        SELECT 
            CASE 
                WHEN CAST([Net Promoter] as INT) >= 9 THEN 'Promoter'
                WHEN CAST([Net Promoter] as INT) >= 7 THEN 'Passive'
                ELSE 'Detractor'
            END as nps_category,
            COUNT(*) as count
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= '{start_date_str}'
            AND [Net Promoter] IS NOT NULL
        GROUP BY 
            CASE 
                WHEN CAST([Net Promoter] as INT) >= 9 THEN 'Promoter'
                WHEN CAST([Net Promoter] as INT) >= 7 THEN 'Passive'
                ELSE 'Detractor'
            END
        """
        
        monthly_sat = service.execute_query(monthly_sat_query) or []
        sat_by_type = service.execute_query(sat_by_type_query) or []
        nps_dist = service.execute_query(nps_dist_query) or []
        
        # Calculate NPS score
        nps_counts = {r.get("nps_category", ""): r.get("count", 0) for r in nps_dist}
        total_nps_responses = sum(nps_counts.values())
        if total_nps_responses > 0:
            promoter_pct = (nps_counts.get("Promoter", 0) / total_nps_responses) * 100
            detractor_pct = (nps_counts.get("Detractor", 0) / total_nps_responses) * 100
            nps_score = promoter_pct - detractor_pct
        else:
            nps_score = 0
            promoter_pct = 0
            detractor_pct = 0
        
        result = {
            "monthly_trend": [
                {
                    "month": r.get("month", ""),
                    "avg_satisfaction": round(r.get("avg_satisfaction", 0) or 0, 2),
                    "avg_nps": round(r.get("avg_nps", 0) or 0, 1),
                    "response_count": r.get("response_count", 0)
                }
                for r in monthly_sat
            ],
            "by_case_type": [
                {
                    "case_type": r.get("case_type", "Unknown"),
                    "avg_satisfaction": round(r.get("avg_satisfaction", 0) or 0, 2),
                    "avg_nps": round(r.get("avg_nps", 0) or 0, 1),
                    "response_count": r.get("response_count", 0)
                }
                for r in sat_by_type
            ],
            "nps_distribution": [
                {"category": cat, "count": nps_counts.get(cat, 0)}
                for cat in ["Promoter", "Passive", "Detractor"]
            ],
            "nps_score": round(nps_score, 1),
            "promoter_pct": round(promoter_pct, 1),
            "detractor_pct": round(detractor_pct, 1),
            "period_days": days
        }
        
        # Cache the result
        cache_service.set(cache_key, result, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": result,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"Satisfaction analysis error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_member_experience_bp.route('/api/vital/member-experience/digital-adoption', methods=['GET'])
@jwt_required()
def get_digital_adoption():
    """Get digital vs telephonic adoption metrics"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        days = request.args.get('days', 90, type=int)
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        cache_key = f"vital_member_exp_digital:{days}"
        
        # Check cache first
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                return jsonify({"success": True, "data": cached, "from_cache": True})
        
        service = get_azure_sql_service()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime("%Y-%m-%d")
        
        # Digital engagement by month
        digital_monthly_query = f"""
        SELECT 
            FORMAT([Case Create Date], 'yyyy-MM') as month,
            SUM(CAST(ISNULL([Web Logins], 0) as INT)) as web_logins,
            SUM(CAST(ISNULL([Mobile App Count], 0) as INT)) as mobile_app_usage,
            SUM(CAST(ISNULL([Web Hits], 0) as INT)) as web_hits,
            COUNT(*) as total_cases
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= '{start_date_str}'
        GROUP BY FORMAT([Case Create Date], 'yyyy-MM')
        ORDER BY month
        """
        
        # Session modality breakdown
        modality_query = f"""
        SELECT 
            [Initial Session Modality] as modality,
            COUNT(*) as count
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= '{start_date_str}'
            AND [Initial Session Modality] IS NOT NULL
        GROUP BY [Initial Session Modality]
        ORDER BY count DESC
        """
        
        # Virtual vs In-Person sessions
        session_type_query = f"""
        SELECT 
            SUM(CAST(ISNULL([Virtual Sessions], 0) as INT)) as virtual_sessions,
            SUM(CAST(ISNULL([In-Person Sessions], 0) as INT)) as in_person_sessions
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= '{start_date_str}'
        """
        
        digital_monthly = service.execute_query(digital_monthly_query) or []
        modality = service.execute_query(modality_query) or []
        session_types = service.execute_query(session_type_query) or []
        
        session_data = session_types[0] if session_types else {}
        
        result = {
            "monthly_trend": [
                {
                    "month": r.get("month", ""),
                    "web_logins": r.get("web_logins", 0) or 0,
                    "mobile_app_usage": r.get("mobile_app_usage", 0) or 0,
                    "web_hits": r.get("web_hits", 0) or 0,
                    "total_cases": r.get("total_cases", 0)
                }
                for r in digital_monthly
            ],
            "by_modality": [
                {
                    "modality": r.get("modality", "Unknown"),
                    "count": r.get("count", 0)
                }
                for r in modality
            ],
            "session_types": {
                "virtual": session_data.get("virtual_sessions", 0) or 0,
                "in_person": session_data.get("in_person_sessions", 0) or 0
            },
            "period_days": days
        }
        
        # Cache the result
        cache_service.set(cache_key, result, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": result,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"Digital adoption error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_member_experience_bp.route('/api/vital/member-experience/crisis-management', methods=['GET'])
@jwt_required()
def get_crisis_management():
    """Get crisis and high-acuity case metrics"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        days = request.args.get('days', 90, type=int)
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        cache_key = f"vital_member_exp_crisis:{days}"
        
        # Check cache first
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                return jsonify({"success": True, "data": cached, "from_cache": True})
        
        service = get_azure_sql_service()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime("%Y-%m-%d")
        
        # High acuity by triage tier
        acuity_query = f"""
        SELECT 
            [Triage Tier] as triage_tier,
            COUNT(*) as case_count,
            AVG(CAST([TAT - Client Contact to First Session] as FLOAT)) as avg_response_time
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= '{start_date_str}'
            AND [Triage Tier] IS NOT NULL
        GROUP BY [Triage Tier]
        ORDER BY case_count DESC
        """
        
        # Monthly high acuity trend
        monthly_acuity_query = f"""
        SELECT 
            FORMAT([Case Create Date], 'yyyy-MM') as month,
            COUNT(CASE WHEN [Triage Tier] IN ('High', 'Crisis', 'Urgent') THEN 1 END) as high_acuity_count,
            COUNT(*) as total_cases
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Case Create Date] >= '{start_date_str}'
        GROUP BY FORMAT([Case Create Date], 'yyyy-MM')
        ORDER BY month
        """
        
        acuity = service.execute_query(acuity_query) or []
        monthly_acuity = service.execute_query(monthly_acuity_query) or []
        
        result = {
            "by_triage_tier": [
                {
                    "triage_tier": r.get("triage_tier", "Unknown"),
                    "case_count": r.get("case_count", 0),
                    "avg_response_time": round(r.get("avg_response_time", 0) or 0, 1)
                }
                for r in acuity
            ],
            "monthly_trend": [
                {
                    "month": r.get("month", ""),
                    "high_acuity_count": r.get("high_acuity_count", 0) or 0,
                    "total_cases": r.get("total_cases", 0),
                    "high_acuity_pct": round((r.get("high_acuity_count", 0) or 0) / max(r.get("total_cases", 1), 1) * 100, 1)
                }
                for r in monthly_acuity
            ],
            "period_days": days
        }
        
        # Cache the result
        cache_service.set(cache_key, result, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": result,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"Crisis management error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
