"""
VITAL Azure SQL Integration Routes
Provides API endpoints for Case_Data_Summary_NOPHI data for the VITAL tenant
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import os

logger = logging.getLogger(__name__)

vital_azure_sql_bp = Blueprint('vital_azure_sql', __name__)


def get_azure_sql_service():
    """Get VITAL Azure SQL service instance"""
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

@vital_azure_sql_bp.route('/api/vital/azure-sql/health', methods=['GET'])
def azure_sql_health_check():
    """Check Azure SQL connectivity (no auth required for health check)"""
    try:
        service = get_azure_sql_service()
        result = service.test_connection()
        
        if result['status'] == 'connected':
            return jsonify({
                "status": "healthy",
                "message": "Azure SQL connection successful",
                "table": "Case_Data_Summary_NOPHI"
            })
        else:
            return jsonify({
                "status": "unhealthy",
                "error": result.get('error', 'Unknown error')
            }), 500
    except ValueError as e:
        return jsonify({
            "status": "not_configured",
            "error": str(e)
        }), 503
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ==================== DASHBOARD ENDPOINTS ====================

@vital_azure_sql_bp.route('/api/vital/azure-sql/dashboard', methods=['GET'])
@jwt_required()
def get_azure_sql_dashboard():
    """Get Azure SQL dashboard data for VITAL"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        service = get_azure_sql_service()
        dashboard_data = service.get_dashboard_data()
        
        return jsonify({
            "success": True,
            "data": dashboard_data
        })
    except Exception as e:
        logger.error(f"Azure SQL dashboard error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@vital_azure_sql_bp.route('/api/vital/azure-sql/schema', methods=['GET'])
@jwt_required()
def get_table_schema():
    """Get the schema/columns of the Case_Data_Summary_NOPHI table"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        service = get_azure_sql_service()
        schema = service.get_table_schema()
        
        return jsonify({
            "success": True,
            "data": {
                "table": "Case_Data_Summary_NOPHI",
                "columns": schema
            }
        })
    except Exception as e:
        logger.error(f"Schema error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_azure_sql_bp.route('/api/vital/azure-sql/summary', methods=['GET'])
@jwt_required()
def get_summary_stats():
    """Get summary statistics"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        service = get_azure_sql_service()
        stats = service.get_summary_stats()
        
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        logger.error(f"Summary error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== DATA ENDPOINTS ====================

@vital_azure_sql_bp.route('/api/vital/azure-sql/data', methods=['GET'])
@jwt_required()
def get_case_data():
    """Get case data with pagination"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        # Get pagination params
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        service = get_azure_sql_service()
        result = service.get_case_data(limit=limit, offset=offset)
        
        return jsonify({
            "success": True,
            "data": result['data'],
            "pagination": result['pagination']
        })
    except Exception as e:
        logger.error(f"Data fetch error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_azure_sql_bp.route('/api/vital/azure-sql/aggregate', methods=['GET'])
@jwt_required()
def get_aggregated_data():
    """Get aggregated data grouped by a column"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        group_by = request.args.get('group_by')
        if not group_by:
            return jsonify({"error": "group_by parameter is required"}), 400
        
        service = get_azure_sql_service()
        result = service.get_aggregated_data(group_by)
        
        return jsonify({
            "success": True,
            "data": result
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Aggregation error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_azure_sql_bp.route('/api/vital/azure-sql/count', methods=['GET'])
@jwt_required()
def get_row_count():
    """Get total row count"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        service = get_azure_sql_service()
        count = service.get_row_count()
        
        return jsonify({
            "success": True,
            "data": {
                "table": "Case_Data_Summary_NOPHI",
                "count": count
            }
        })
    except Exception as e:
        logger.error(f"Count error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== CEO DASHBOARD ENDPOINTS ====================

@vital_azure_sql_bp.route('/api/vital/azure-sql/case-metrics', methods=['GET'])
@jwt_required()
def get_case_metrics():
    """Get case metrics for CEO Dashboard with timeframe filtering"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        # Get days parameter (default 30)
        days = request.args.get('days', 30, type=int)
        
        # Validate days range
        if days < 1 or days > 365:
            return jsonify({"error": "days must be between 1 and 365"}), 400
        
        service = get_azure_sql_service()
        metrics = service.get_case_metrics(days=days)
        
        return jsonify({
            "success": True,
            "data": metrics
        })
    except ValueError as e:
        # Handle configuration errors gracefully
        logger.warning(f"Case metrics not available: {str(e)}")
        return jsonify({
            "success": True,
            "data": {
                "new_cases": 0,
                "closed_cases": 0,
                "open_cases": 0,
                "total_cases": 0,
                "daily_trend": [],
                "period_days": days,
                "error": "Azure SQL not configured"
            }
        })
    except Exception as e:
        logger.error(f"Case metrics error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
