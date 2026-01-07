"""
VITAL HubSpot Integration Routes
Provides API endpoints for HubSpot CRM data for the VITAL tenant
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import os

logger = logging.getLogger(__name__)

vital_hubspot_bp = Blueprint('vital_hubspot', __name__)

# VITAL HubSpot Access Token - must be set in environment variable
VITAL_HUBSPOT_TOKEN = os.environ.get('VITAL_HUBSPOT_TOKEN')

def get_hubspot_service():
    """Get HubSpot service instance"""
    from src.services.hubspot_service import HubSpotService
    return HubSpotService(access_token=VITAL_HUBSPOT_TOKEN)

def is_vital_user():
    """Check if current user belongs to VITAL organization"""
    try:
        from src.services.postgres_service import PostgresService
        pg = PostgresService()
        user_id = get_jwt_identity()
        
        user = pg.execute_query(
            "SELECT o.name FROM users u JOIN organizations o ON u.organization_id = o.id WHERE u.id = %s",
            (user_id,)
        )
        
        if user and len(user) > 0:
            org_name = user[0].get('name', '').lower()
            return 'vital' in org_name
        return False
    except Exception as e:
        logger.error(f"Error checking VITAL user: {str(e)}")
        return False


# ==================== DASHBOARD ENDPOINTS ====================

@vital_hubspot_bp.route('/api/vital/hubspot/dashboard', methods=['GET'])
@jwt_required()
def get_hubspot_dashboard():
    """Get complete HubSpot dashboard data for VITAL"""
    try:
        # Verify user is from VITAL organization
        if not is_vital_user():
            return jsonify({"error": "Access denied. This endpoint is only available for VITAL users."}), 403
        
        hs = get_hubspot_service()
        dashboard_data = hs.get_dashboard_summary()
        
        return jsonify({
            "success": True,
            "data": dashboard_data
        })
    except Exception as e:
        logger.error(f"HubSpot dashboard error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@vital_hubspot_bp.route('/api/vital/hubspot/contacts/summary', methods=['GET'])
@jwt_required()
def get_contacts_summary():
    """Get contacts summary for VITAL"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied"}), 403
        
        hs = get_hubspot_service()
        
        total = hs.get_contacts_count()
        by_lifecycle = hs.get_contacts_by_lifecycle_stage()
        new_contacts = hs.get_new_contacts_trend(days=30)
        
        return jsonify({
            "success": True,
            "data": {
                "total_contacts": total,
                "by_lifecycle_stage": by_lifecycle,
                "new_last_30_days": new_contacts["total_new"]
            }
        })
    except Exception as e:
        logger.error(f"Contacts summary error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_hubspot_bp.route('/api/vital/hubspot/companies/summary', methods=['GET'])
@jwt_required()
def get_companies_summary():
    """Get companies summary for VITAL"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied"}), 403
        
        hs = get_hubspot_service()
        
        total = hs.get_companies_count()
        recent = hs.get_recent_companies(limit=10)
        
        return jsonify({
            "success": True,
            "data": {
                "total_companies": total,
                "recent_companies": [
                    {
                        "name": c.get("properties", {}).get("name"),
                        "domain": c.get("properties", {}).get("domain"),
                        "industry": c.get("properties", {}).get("industry"),
                        "employees": c.get("properties", {}).get("numberofemployees"),
                        "created": c.get("properties", {}).get("createdate")
                    }
                    for c in recent
                ]
            }
        })
    except Exception as e:
        logger.error(f"Companies summary error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_hubspot_bp.route('/api/vital/hubspot/deals/summary', methods=['GET'])
@jwt_required()
def get_deals_summary():
    """Get deals/pipeline summary for VITAL"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied"}), 403
        
        hs = get_hubspot_service()
        deals_data = hs.get_deals_summary()
        
        return jsonify({
            "success": True,
            "data": deals_data
        })
    except Exception as e:
        logger.error(f"Deals summary error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_hubspot_bp.route('/api/vital/hubspot/deals/pipeline', methods=['GET'])
@jwt_required()
def get_deals_pipeline():
    """Get deals grouped by pipeline stage for funnel visualization"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied"}), 403
        
        hs = get_hubspot_service()
        deals_by_stage = hs.get_deals_by_stage()
        
        # Group by pipeline
        pipelines = {}
        for stage in deals_by_stage:
            pipeline_name = stage["pipeline"]
            if pipeline_name not in pipelines:
                pipelines[pipeline_name] = []
            pipelines[pipeline_name].append({
                "stage": stage["stage_name"],
                "count": stage["count"],
                "value": stage["total_value"],
                "is_closed": stage["is_closed"]
            })
        
        return jsonify({
            "success": True,
            "data": {
                "pipelines": pipelines,
                "total_stages": len(deals_by_stage)
            }
        })
    except Exception as e:
        logger.error(f"Deals pipeline error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_hubspot_bp.route('/api/vital/hubspot/owners', methods=['GET'])
@jwt_required()
def get_owners():
    """Get HubSpot owners/sales reps"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied"}), 403
        
        hs = get_hubspot_service()
        owners = hs.get_owners()
        
        return jsonify({
            "success": True,
            "data": {
                "total_owners": len(owners),
                "owners": [
                    {
                        "id": o.get("id"),
                        "email": o.get("email"),
                        "first_name": o.get("firstName"),
                        "last_name": o.get("lastName"),
                        "teams": [t.get("name") for t in o.get("teams", [])]
                    }
                    for o in owners if not o.get("archived")
                ]
            }
        })
    except Exception as e:
        logger.error(f"Owners error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== HEALTH CHECK ====================

@vital_hubspot_bp.route('/api/vital/hubspot/health', methods=['GET'])
def hubspot_health_check():
    """Check HubSpot API connectivity"""
    try:
        hs = get_hubspot_service()
        # Simple test - get contacts count
        count = hs.get_contacts_count()
        return jsonify({
            "status": "healthy",
            "contacts_count": count,
            "message": "HubSpot API connection successful"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
