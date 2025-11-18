from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.postgres_service import get_postgres_db
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('service_assistant_analytics', __name__)

@analytics_bp.route('/api/service-assistant/analytics/summary', methods=['GET'])
@jwt_required()
def get_analytics_summary():
    """Get overall analytics summary"""
    try:
        postgres = get_postgres_db()
        
        # Total queries
        total_query = "SELECT COUNT(*) as total FROM service_assistant_queries"
        total_result = postgres.execute_query(total_query)
        total_queries = total_result[0]['count'] if total_result else 0
        
        # Queries last 7 days
        week_query = """
            SELECT COUNT(*) as count 
            FROM service_assistant_queries 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """
        week_result = postgres.execute_query(week_query)
        queries_last_week = week_result[0]['count'] if week_result else 0
        
        # Queries last 30 days
        month_query = """
            SELECT COUNT(*) as count 
            FROM service_assistant_queries 
            WHERE created_at >= NOW() - INTERVAL '30 days'
        """
        month_result = postgres.execute_query(month_query)
        queries_last_month = month_result[0]['count'] if month_result else 0
        
        # Average results per query
        avg_query = """
            SELECT 
                AVG(kb_results_count) as avg_kb,
                AVG(wo_results_count) as avg_wo,
                AVG(web_results_count) as avg_web
            FROM service_assistant_queries
        """
        avg_result = postgres.execute_query(avg_query)
        avg_results = avg_result[0] if avg_result else {'avg_kb': 0, 'avg_wo': 0, 'avg_web': 0}
        
        return jsonify({
            'totalQueries': total_queries,
            'queriesLastWeek': queries_last_week,
            'queriesLastMonth': queries_last_month,
            'averageResults': {
                'kbArticles': float(avg_results['avg_kb'] or 0),
                'workOrders': float(avg_results['avg_wo'] or 0),
                'webResources': float(avg_results['avg_web'] or 0)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting analytics summary: {str(e)}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/api/service-assistant/analytics/top-questions', methods=['GET'])
@jwt_required()
def get_top_questions():
    """Get most frequently asked questions"""
    try:
        postgres = get_postgres_db()
        
        query = """
            SELECT 
                query_text,
                COUNT(*) as frequency,
                MAX(created_at) as last_asked,
                AVG(kb_results_count + wo_results_count) as avg_results
            FROM service_assistant_queries
            GROUP BY query_text
            ORDER BY frequency DESC
            LIMIT 20
        """
        
        results = postgres.execute_query(query)
        
        questions = []
        if results:
            for row in results:
                questions.append({
                    'question': row['query_text'],
                    'frequency': row['frequency'],
                    'lastAsked': row['last_asked'].isoformat() if row['last_asked'] else None,
                    'avgResults': float(row['avg_results'] or 0)
                })
        
        return jsonify({'questions': questions}), 200
        
    except Exception as e:
        logger.error(f"Error getting top questions: {str(e)}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/api/service-assistant/analytics/equipment-breakdown', methods=['GET'])
@jwt_required()
def get_equipment_breakdown():
    """Get breakdown of queries by equipment make"""
    try:
        postgres = get_postgres_db()
        
        query = """
            SELECT 
                equipment_make,
                COUNT(*) as query_count,
                AVG(kb_results_count + wo_results_count) as avg_internal_results
            FROM service_assistant_queries
            WHERE equipment_make IS NOT NULL
            GROUP BY equipment_make
            ORDER BY query_count DESC
        """
        
        results = postgres.execute_query(query)
        
        equipment = []
        if results:
            for row in results:
                equipment.append({
                    'make': row['equipment_make'],
                    'queryCount': row['query_count'],
                    'avgInternalResults': float(row['avg_internal_results'] or 0)
                })
        
        return jsonify({'equipment': equipment}), 200
        
    except Exception as e:
        logger.error(f"Error getting equipment breakdown: {str(e)}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/api/service-assistant/analytics/knowledge-gaps', methods=['GET'])
@jwt_required()
def get_knowledge_gaps():
    """Identify questions with low internal results (knowledge gaps)"""
    try:
        postgres = get_postgres_db()
        
        query = """
            SELECT 
                query_text,
                equipment_make,
                equipment_model,
                kb_results_count,
                wo_results_count,
                web_results_count,
                COUNT(*) as frequency,
                MAX(created_at) as last_asked
            FROM service_assistant_queries
            WHERE (kb_results_count + wo_results_count) < 3
            GROUP BY query_text, equipment_make, equipment_model, 
                     kb_results_count, wo_results_count, web_results_count
            HAVING COUNT(*) >= 2
            ORDER BY frequency DESC, last_asked DESC
            LIMIT 20
        """
        
        results = postgres.execute_query(query)
        
        gaps = []
        if results:
            for row in results:
                gaps.append({
                    'question': row['query_text'],
                    'make': row['equipment_make'],
                    'model': row['equipment_model'],
                    'kbResults': row['kb_results_count'],
                    'woResults': row['wo_results_count'],
                    'webResults': row['web_results_count'],
                    'frequency': row['frequency'],
                    'lastAsked': row['last_asked'].isoformat() if row['last_asked'] else None,
                    'suggestion': 'Consider creating a KB article for this topic'
                })
        
        return jsonify({'gaps': gaps}), 200
        
    except Exception as e:
        logger.error(f"Error getting knowledge gaps: {str(e)}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/api/service-assistant/analytics/trending-topics', methods=['GET'])
@jwt_required()
def get_trending_topics():
    """Get trending keywords and topics"""
    try:
        postgres = get_postgres_db()
        
        # Get top keywords from last 30 days
        query = """
            SELECT 
                UNNEST(keywords) as keyword,
                COUNT(*) as frequency
            FROM service_assistant_queries
            WHERE created_at >= NOW() - INTERVAL '30 days'
              AND keywords IS NOT NULL
            GROUP BY keyword
            ORDER BY frequency DESC
            LIMIT 30
        """
        
        results = postgres.execute_query(query)
        
        topics = []
        if results:
            for row in results:
                topics.append({
                    'keyword': row['keyword'],
                    'frequency': row['frequency']
                })
        
        return jsonify({'topics': topics}), 200
        
    except Exception as e:
        logger.error(f"Error getting trending topics: {str(e)}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/api/service-assistant/analytics/daily-usage', methods=['GET'])
@jwt_required()
def get_daily_usage():
    """Get daily usage statistics for the last 30 days"""
    try:
        postgres = get_postgres_db()
        
        query = """
            SELECT 
                DATE(created_at) as query_date,
                COUNT(*) as query_count,
                COUNT(DISTINCT user_email) as unique_users
            FROM service_assistant_queries
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY query_date DESC
        """
        
        results = postgres.execute_query(query)
        
        usage = []
        if results:
            for row in results:
                usage.append({
                    'date': row['query_date'].isoformat() if row['query_date'] else None,
                    'queryCount': row['query_count'],
                    'uniqueUsers': row['unique_users']
                })
        
        return jsonify({'usage': usage}), 200
        
    except Exception as e:
        logger.error(f"Error getting daily usage: {str(e)}")
        return jsonify({'error': str(e)}), 500
