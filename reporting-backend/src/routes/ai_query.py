from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from src.services.openai_service import OpenAIQueryService
from src.services.softbase_service import SoftbaseService

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
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        openai_service = OpenAIQueryService(openai_api_key)
        
        # Parse the natural language query
        query_params = openai_service.parse_natural_language_query(query_text, organization_id)
        
        # Generate SQL query
        sql_query = openai_service.generate_sql_query(query_params)
        
        # Execute query through Softbase service
        softbase_service = SoftbaseService(organization_id)
        results = softbase_service.execute_custom_query(sql_query)
        
        # Generate explanation
        explanation = openai_service.explain_query_results(query_text, results, query_params)
        
        return jsonify({
            'success': True,
            'query': query_text,
            'parsed_params': query_params,
            'sql_query': sql_query,
            'results': results,
            'explanation': explanation,
            'result_count': len(results)
        })
        
    except Exception as e:
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
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        openai_service = OpenAIQueryService(openai_api_key)
        
        # Parse the natural language query
        query_params = openai_service.parse_natural_language_query(query_text, organization_id)
        
        # Generate SQL query
        sql_query = openai_service.generate_sql_query(query_params)
        
        return jsonify({
            'success': True,
            'query': query_text,
            'parsed_params': query_params,
            'sql_query': sql_query,
            'estimated_fields': query_params.get('fields', []),
            'query_type': query_params.get('query_type', 'unknown')
        })
        
    except Exception as e:
        return jsonify({'error': f'Query validation failed: {str(e)}'}), 500

