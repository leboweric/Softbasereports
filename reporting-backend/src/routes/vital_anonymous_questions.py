"""
VITAL Anonymous Questions API Routes
Provides endpoints for submitting anonymous questions and viewing trend analysis
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
import logging
from datetime import datetime
from src.models.user import db
from src.services.cache_service import cache_service

logger = logging.getLogger(__name__)

# Cache TTL for analysis data (30 minutes)
CACHE_TTL = 1800

vital_questions_bp = Blueprint('vital_questions', __name__)


def get_questions_service():
    """Get Anonymous Questions service instance"""
    from src.services.vital_anonymous_questions import VitalAnonymousQuestionsService
    return VitalAnonymousQuestionsService(db_session=db.session)


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


def is_vital_admin():
    """Check if current user is a VITAL HR admin"""
    try:
        from src.models.user import User, Organization
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.organization_id:
            return False
        
        org = Organization.query.get(user.organization_id)
        if not org or 'vital' not in org.name.lower():
            return False
        
        # Check if user has admin role
        return user.role in ['admin', 'hr_admin', 'owner']
    except Exception as e:
        logger.error(f"Error checking VITAL admin: {str(e)}")
        return False


# ==================== QUESTION SUBMISSION ====================

@vital_questions_bp.route('/api/vital/questions/submit', methods=['POST'])
def submit_question():
    """Submit an anonymous question (authentication optional for true anonymity)"""
    try:
        data = request.get_json()
        
        if not data or not data.get('question'):
            return jsonify({
                "success": False,
                "error": "Question text is required"
            }), 400
        
        question_text = data.get('question', '').strip()
        category = data.get('category')
        
        if len(question_text) < 10:
            return jsonify({
                "success": False,
                "error": "Question must be at least 10 characters long"
            }), 400
        
        if len(question_text) > 2000:
            return jsonify({
                "success": False,
                "error": "Question must be less than 2000 characters"
            }), 400
        
        # Get user ID if authenticated (optional)
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except:
            pass
        
        service = get_questions_service()
        result = service.submit_question(
            question_text=question_text,
            user_id=user_id,
            category=category
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Submit question error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_questions_bp.route('/api/vital/questions/categories', methods=['GET'])
def get_categories():
    """Get list of question categories"""
    from src.services.vital_anonymous_questions import VitalAnonymousQuestionsService
    return jsonify({
        "success": True,
        "categories": VitalAnonymousQuestionsService.CATEGORIES
    })


# ==================== ADMIN ENDPOINTS ====================

@vital_questions_bp.route('/api/vital/questions/list', methods=['GET'])
@jwt_required()
def get_questions():
    """Get list of questions (admin only)"""
    try:
        if not is_vital_admin():
            return jsonify({"error": "Access denied. VITAL HR admins only."}), 403
        
        status = request.args.get('status')
        category = request.args.get('category')
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        service = get_questions_service()
        result = service.get_questions(
            status=status,
            category=category,
            days=days,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Get questions error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_questions_bp.route('/api/vital/questions/stats', methods=['GET'])
@jwt_required()
def get_question_stats():
    """Get question statistics (admin only)"""
    try:
        if not is_vital_admin():
            return jsonify({"error": "Access denied. VITAL HR admins only."}), 403
        
        days = request.args.get('days', 30, type=int)
        
        cache_key = f"vital_questions_stats:{days}"
        cached = cache_service.get(cache_key)
        if cached:
            return jsonify({
                "success": True,
                "data": cached,
                "from_cache": True
            })
        
        service = get_questions_service()
        result = service.get_question_stats(days=days)
        
        cache_service.set(cache_key, result, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": result,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"Get question stats error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_questions_bp.route('/api/vital/questions/update-status', methods=['POST'])
@jwt_required()
def update_question_status():
    """Update question status (admin only)"""
    try:
        if not is_vital_admin():
            return jsonify({"error": "Access denied. VITAL HR admins only."}), 403
        
        data = request.get_json()
        
        if not data or not data.get('question_id') or not data.get('status'):
            return jsonify({
                "success": False,
                "error": "question_id and status are required"
            }), 400
        
        service = get_questions_service()
        result = service.update_question_status(
            question_id=data['question_id'],
            status=data['status'],
            admin_notes=data.get('admin_notes')
        )
        
        return jsonify(result)
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Update question status error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== AI TREND ANALYSIS ====================

@vital_questions_bp.route('/api/vital/questions/analyze-trends', methods=['GET'])
@jwt_required()
def analyze_trends():
    """Get AI-powered trend analysis (admin only)"""
    try:
        if not is_vital_admin():
            return jsonify({"error": "Access denied. VITAL HR admins only."}), 403
        
        days = request.args.get('days', 30, type=int)
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        cache_key = f"vital_questions_trends:{days}"
        
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                return jsonify({
                    "success": True,
                    "data": cached,
                    "from_cache": True
                })
        
        service = get_questions_service()
        result = service.analyze_trends(days=days)
        
        # Cache for longer (1 hour) since AI analysis is expensive
        cache_service.set(cache_key, result, 3600)
        
        return jsonify({
            "success": True,
            "data": result,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"Analyze trends error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== DASHBOARD ====================

@vital_questions_bp.route('/api/vital/questions/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Get comprehensive dashboard data (admin only)"""
    try:
        if not is_vital_admin():
            return jsonify({"error": "Access denied. VITAL HR admins only."}), 403
        
        days = request.args.get('days', 30, type=int)
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        cache_key = f"vital_questions_dashboard:{days}"
        
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                return jsonify({
                    "success": True,
                    "data": cached,
                    "from_cache": True
                })
        
        service = get_questions_service()
        result = service.get_dashboard_data(days=days)
        
        cache_service.set(cache_key, result, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": result,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
