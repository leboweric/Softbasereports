from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import logging
import traceback
from src.services.openai_service import OpenAIQueryService
from src.services.softbase_service import SoftbaseService

logger = logging.getLogger(__name__)
ai_query_bp = Blueprint('ai_query', __name__)

@ai_query_bp.route('/query', methods=['POST'])
@jwt_required()
def natural_language_query():
    """
    Process natural language queries and return structured results
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query text is required'}), 400
        
        query_text = data['query']
        organization_id = current_user.get('organization_id')
        
        # Initialize OpenAI service
        try:
            logger.info(f"Initializing OpenAI service for query: {query_text[:50]}...")
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key or openai_api_key == 'your-openai-api-key-here':
                logger.error("OpenAI API key not properly configured")
                return jsonify({'error': 'OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.'}), 500
            
            openai_service = OpenAIQueryService()
            logger.info("OpenAI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {str(e)}", exc_info=True)
            return jsonify({'error': f'Failed to initialize OpenAI service: {str(e)}'}), 500
        
        # Process the natural language query
        try:
            logger.info("Processing natural language query...")
            result = openai_service.process_natural_language_query(query_text, {'organization_id': organization_id})
            logger.info(f"Query processing result: {result.get('success', False)}")
        except Exception as e:
            logger.error(f"Error during query processing: {str(e)}", exc_info=True)
            return jsonify({'error': f'Error processing query: {str(e)}'}), 500
        
        if not result['success']:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to process query')
            }), 400
        
        query_analysis = result['query_analysis']
        
        # For now, return the analysis without executing SQL
        # TODO: Implement SQL generation and execution based on query_analysis
        sql_query = 'SQL generation not yet implemented'
        results = []
        explanation = f"Query understood: {query_analysis.get('intent', 'Unknown intent')}"
        
        return jsonify({
            'success': True,
            'query': query_text,
            'parsed_params': query_analysis,
            'sql_query': sql_query,
            'results': results,
            'explanation': explanation,
            'result_count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': f'Query processing failed: {str(e)}'}), 500

@ai_query_bp.route('/suggestions', methods=['GET'])
@jwt_required()
def get_query_suggestions():
    """
    Get suggested natural language queries based on common use cases
    """
    suggestions = [
        {
            'category': 'Sales Analysis',
            'queries': [
                "What were our total sales last month?",
                "Who are our top 5 customers by revenue this year?",
                "Which salesperson had the highest sales last quarter?",
                "Show me all Toyota forklift sales from last week"
            ]
        },
        {
            'category': 'Inventory Management', 
            'queries': [
                "How many Linde forklifts do we have in stock?",
                "Which parts are running low on inventory?",
                "Show me all available forklifts under $20,000",
                "What equipment is currently in maintenance?"
            ]
        },
        {
            'category': 'Rental Operations',
            'queries': [
                "Which customers have active rentals?",
                "Show me overdue rental returns",
                "What's our total rental revenue this month?",
                "Which equipment is rented out to Polaris?"
            ]
        },
        {
            'category': 'Parts & Service',
            'queries': [
                "Which Linde parts were we not able to fill last week?",
                "Show me all service appointments for tomorrow",
                "What parts do we need to reorder?",
                "Which technician completed the most services this month?"
            ]
        },
        {
            'category': 'Customer Insights',
            'queries': [
                "Give me the serial numbers of all forklifts that Polaris rents from us",
                "Which customers haven't made a purchase in 6 months?",
                "Show me all customers with outstanding invoices",
                "What's the average order value by customer?"
            ]
        }
    ]
    
    return jsonify({
        'success': True,
        'suggestions': suggestions
    })

@ai_query_bp.route('/query-history', methods=['GET'])
@jwt_required()
def get_query_history():
    """
    Get user's query history (would be stored in database in production)
    """
    # This would typically fetch from a query_history table
    # For now, return mock data
    
    history = [
        {
            'id': 1,
            'query': "Which Linde parts were we not able to fill last week?",
            'timestamp': "2025-01-15T10:30:00Z",
            'result_count': 12
        },
        {
            'id': 2,
            'query': "Show me all Toyota forklift sales from last month",
            'timestamp': "2025-01-14T14:22:00Z", 
            'result_count': 8
        },
        {
            'id': 3,
            'query': "Give me the serial numbers of all forklifts that Polaris rents from us",
            'timestamp': "2025-01-13T09:15:00Z",
            'result_count': 5
        }
    ]
    
    return jsonify({
        'success': True,
        'history': history
    })

@ai_query_bp.route('/validate-query', methods=['POST'])
@jwt_required()
def validate_query():
    """
    Validate and preview what a natural language query would return
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query text is required'}), 400
        
        query_text = data['query']
        organization_id = current_user.get('organization_id')
        
        # Initialize OpenAI service
        try:
            logger.info(f"Initializing OpenAI service for query: {query_text[:50]}...")
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key or openai_api_key == 'your-openai-api-key-here':
                logger.error("OpenAI API key not properly configured")
                return jsonify({'error': 'OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.'}), 500
            
            openai_service = OpenAIQueryService()
            logger.info("OpenAI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {str(e)}", exc_info=True)
            return jsonify({'error': f'Failed to initialize OpenAI service: {str(e)}'}), 500
        
        # Process the natural language query
        try:
            logger.info("Processing natural language query...")
            result = openai_service.process_natural_language_query(query_text, {'organization_id': organization_id})
            logger.info(f"Query processing result: {result.get('success', False)}")
        except Exception as e:
            logger.error(f"Error during query processing: {str(e)}", exc_info=True)
            return jsonify({'error': f'Error processing query: {str(e)}'}), 500
        
        if not result['success']:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to validate query')
            }), 400
        
        query_analysis = result['query_analysis']
        sql_query = 'SQL generation not yet implemented'
        
        return jsonify({
            'success': True,
            'query': query_text,
            'parsed_params': query_analysis,
            'sql_query': sql_query,
            'estimated_fields': query_analysis.get('fields', []),
            'query_type': query_analysis.get('query_type', 'unknown')
        })
        
    except Exception as e:
        return jsonify({'error': f'Query validation failed: {str(e)}'}), 500

