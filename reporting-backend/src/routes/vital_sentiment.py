"""
Sentiment Analysis API Routes
Provides endpoints for analyzing satisfaction comments and feedback
"""
from flask import Blueprint, jsonify, request
from functools import wraps
import jwt
import os
from datetime import datetime, timedelta
from collections import defaultdict

from ..services.vital_azure_sql_service import VitalAzureSQLService
from ..services.sentiment_service import analyze_feedback_batch, calculate_sentiment_trend
from ..services.cache_service import CacheService

vital_sentiment_bp = Blueprint('vital_sentiment', __name__, url_prefix='/api/vital/sentiment')
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


@vital_sentiment_bp.route('/analysis', methods=['GET'])
@token_required
def get_sentiment_analysis():
    """
    Get sentiment analysis of satisfaction comments
    Query params:
    - days: number of days to analyze (default 90)
    - refresh: bypass cache if true
    """
    try:
        days = request.args.get('days', 90, type=int)
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        cache_key = f"sentiment_analysis_{days}"
        
        if not refresh:
            cached = cache.get(cache_key)
            if cached:
                return jsonify(cached)
        
        service = VitalAzureSQLService()
        
        # Query satisfaction comments from Azure SQL
        query = f"""
        SELECT 
            [Satisfaction Comments] as comment,
            [Satisfaction] as satisfaction,
            [Net Promoter] as nps,
            [Case Create Date] as date,
            [Organization] as organization,
            [Case Type] as case_type,
            [Provider Type] as provider_type
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Satisfaction Comments] IS NOT NULL 
            AND LEN([Satisfaction Comments]) > 10
            AND [Case Create Date] >= DATEADD(day, -{days}, GETDATE())
        ORDER BY [Case Create Date] DESC
        """
        
        results = service.execute_query(query)
        
        if not results:
            return jsonify({
                'total_analyzed': 0,
                'sentiment_distribution': {'positive': 0, 'neutral': 0, 'negative': 0},
                'average_score': 0,
                'message': 'No feedback comments found for the selected period'
            })
        
        # Convert to feedback format
        feedbacks = []
        feedbacks_by_date = defaultdict(list)
        feedbacks_by_org = defaultdict(list)
        
        for row in results:
            feedback = {
                'comment': row.get('comment', ''),
                'satisfaction': row.get('satisfaction'),
                'nps': row.get('nps'),
                'date': str(row.get('date', ''))[:10] if row.get('date') else None,
                'organization': row.get('organization'),
                'case_type': row.get('case_type'),
                'provider_type': row.get('provider_type')
            }
            feedbacks.append(feedback)
            
            if feedback['date']:
                feedbacks_by_date[feedback['date']].append(feedback)
            if feedback['organization']:
                feedbacks_by_org[feedback['organization']].append(feedback)
        
        # Analyze all feedback
        analysis = analyze_feedback_batch(feedbacks)
        
        # Calculate trend
        analysis['trend'] = calculate_sentiment_trend(feedbacks_by_date)
        
        # Calculate sentiment by organization (top 10)
        org_sentiment = []
        for org, org_feedbacks in feedbacks_by_org.items():
            org_analysis = analyze_feedback_batch(org_feedbacks)
            if org_analysis['total_analyzed'] >= 3:  # Minimum sample size
                org_sentiment.append({
                    'organization': org,
                    'count': org_analysis['total_analyzed'],
                    'score': org_analysis['average_score'],
                    'positive_pct': round(org_analysis['sentiment_distribution']['positive'] / org_analysis['total_analyzed'] * 100, 1),
                    'negative_pct': round(org_analysis['sentiment_distribution']['negative'] / org_analysis['total_analyzed'] * 100, 1)
                })
        
        # Sort by negative percentage (highest first) to identify at-risk orgs
        org_sentiment.sort(key=lambda x: x['negative_pct'], reverse=True)
        analysis['organizations_at_risk'] = org_sentiment[:10]
        
        # Sort by positive percentage for top performers
        org_sentiment.sort(key=lambda x: x['positive_pct'], reverse=True)
        analysis['top_performing_orgs'] = org_sentiment[:10]
        
        # Cache for 15 minutes
        cache.set(cache_key, analysis, ttl=900)
        
        return jsonify(analysis)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_sentiment_bp.route('/by-provider', methods=['GET'])
@token_required
def get_sentiment_by_provider():
    """
    Get sentiment analysis grouped by provider type
    """
    try:
        days = request.args.get('days', 90, type=int)
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        cache_key = f"sentiment_by_provider_{days}"
        
        if not refresh:
            cached = cache.get(cache_key)
            if cached:
                return jsonify(cached)
        
        service = VitalAzureSQLService()
        
        query = f"""
        SELECT 
            [Provider Type] as provider_type,
            [Satisfaction Comments] as comment,
            [Satisfaction] as satisfaction,
            [Net Promoter] as nps
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Satisfaction Comments] IS NOT NULL 
            AND LEN([Satisfaction Comments]) > 10
            AND [Provider Type] IS NOT NULL
            AND [Case Create Date] >= DATEADD(day, -{days}, GETDATE())
        """
        
        results = service.execute_query(query)
        
        # Group by provider type
        by_provider = defaultdict(list)
        for row in results:
            by_provider[row['provider_type']].append({
                'comment': row['comment'],
                'satisfaction': row['satisfaction'],
                'nps': row['nps']
            })
        
        # Analyze each provider type
        provider_analysis = []
        for provider_type, feedbacks in by_provider.items():
            analysis = analyze_feedback_batch(feedbacks)
            if analysis['total_analyzed'] >= 5:
                provider_analysis.append({
                    'provider_type': provider_type,
                    'count': analysis['total_analyzed'],
                    'average_score': analysis['average_score'],
                    'sentiment_distribution': analysis['sentiment_distribution'],
                    'top_positive': analysis['top_positive_keywords'][:5],
                    'top_negative': analysis['top_negative_keywords'][:5]
                })
        
        # Sort by average score
        provider_analysis.sort(key=lambda x: x['average_score'], reverse=True)
        
        result = {
            'providers': provider_analysis,
            'total_providers': len(provider_analysis)
        }
        
        cache.set(cache_key, result, ttl=900)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@vital_sentiment_bp.route('/alerts', methods=['GET'])
@token_required
def get_sentiment_alerts():
    """
    Get sentiment alerts - recent negative feedback that needs attention
    """
    try:
        days = request.args.get('days', 7, type=int)
        
        service = VitalAzureSQLService()
        
        query = f"""
        SELECT TOP 50
            [Satisfaction Comments] as comment,
            [Satisfaction] as satisfaction,
            [Net Promoter] as nps,
            [Case Create Date] as date,
            [Organization] as organization,
            [Case Type] as case_type,
            [Provider Type] as provider_type,
            [Case Manager] as case_manager
        FROM [Case_Data_Summary_NOPHI]
        WHERE [Satisfaction Comments] IS NOT NULL 
            AND LEN([Satisfaction Comments]) > 10
            AND ([Satisfaction] <= 2 OR [Net Promoter] <= 6)
            AND [Case Create Date] >= DATEADD(day, -{days}, GETDATE())
        ORDER BY [Case Create Date] DESC
        """
        
        results = service.execute_query(query)
        
        alerts = []
        for row in results:
            from ..services.sentiment_service import analyze_sentiment, extract_topics
            
            sentiment = analyze_sentiment(row.get('comment', ''))
            topics = extract_topics(row.get('comment', ''))
            
            alerts.append({
                'date': str(row.get('date', ''))[:10] if row.get('date') else None,
                'organization': row.get('organization'),
                'case_type': row.get('case_type'),
                'provider_type': row.get('provider_type'),
                'case_manager': row.get('case_manager'),
                'satisfaction': row.get('satisfaction'),
                'nps': row.get('nps'),
                'comment': row.get('comment', '')[:300],
                'sentiment_score': sentiment['score'],
                'topics': topics,
                'negative_keywords': sentiment['negative_matches']
            })
        
        return jsonify({
            'alerts': alerts,
            'total': len(alerts),
            'period_days': days
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
