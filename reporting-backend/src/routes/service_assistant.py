from flask import Blueprint, request, jsonify, Response, stream_with_context
from src.middleware.auth import require_auth
from src.services.azure_sql_service import AzureSQLService
from src.services.postgres_service import PostgresService
from src.services.openai_service import OpenAIQueryService
import openai
import os
import json
import logging

logger = logging.getLogger(__name__)

service_assistant_bp = Blueprint('service_assistant', __name__)

@service_assistant_bp.route('/api/service-assistant/chat', methods=['POST'])
@require_auth
def chat():
    """
    Chat with AI assistant about service issues
    Searches KB articles and work orders to provide context
    """
    try:
        data = request.json
        user_message = data.get('message', '')
        chat_history = data.get('history', [])
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Search KB articles for relevant context
        kb_context = search_kb_articles(user_message)
        
        # Search work orders for relevant context
        wo_context = search_work_orders(user_message)
        
        # Build context for AI
        context = build_context(kb_context, wo_context)
        
        # Get OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        # Create OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Build messages for chat
        messages = [
            {
                "role": "system",
                "content": f"""You are a helpful service assistant for a forklift dealership. 
You help technicians troubleshoot equipment issues and find solutions.

You have access to:
1. Knowledge Base articles with documented solutions
2. Historical work orders with technician notes

When answering:
- Be concise and practical
- Reference specific KB articles or work orders when relevant
- Provide step-by-step troubleshooting when appropriate
- If you don't have enough information, ask clarifying questions

Context from Knowledge Base and Work Orders:
{context}
"""
            }
        ]
        
        # Add chat history
        for msg in chat_history[-10:]:  # Last 10 messages for context
            messages.append({
                "role": msg.get('role', 'user'),
                "content": msg.get('content', '')
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4'),
            messages=messages,
            max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', '1000')),
            temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        )
        
        assistant_message = response.choices[0].message.content
        
        return jsonify({
            'message': assistant_message,
            'context': {
                'kb_articles': kb_context,
                'work_orders': wo_context
            }
        })
        
    except Exception as e:
        logger.error(f"Error in service assistant chat: {str(e)}")
        return jsonify({'error': str(e)}), 500


def search_kb_articles(query):
    """Search KB articles for relevant context"""
    try:
        postgres = PostgresService()
        
        # Search for relevant articles
        search_query = """
            SELECT id, title, equipment_make, equipment_model, issue_category, 
                   symptoms, root_cause, solution
            FROM knowledge_base
            WHERE 
                title ILIKE %s OR
                symptoms ILIKE %s OR
                solution ILIKE %s OR
                root_cause ILIKE %s
            ORDER BY created_at DESC
            LIMIT 5
        """
        
        search_pattern = f'%{query}%'
        results = postgres.execute_query(
            search_query,
            (search_pattern, search_pattern, search_pattern, search_pattern)
        )
        
        articles = []
        for row in results:
            articles.append({
                'id': row[0],
                'title': row[1],
                'make': row[2],
                'model': row[3],
                'category': row[4],
                'symptoms': row[5],
                'root_cause': row[6],
                'solution': row[7]
            })
        
        return articles
        
    except Exception as e:
        logger.error(f"Error searching KB articles: {str(e)}")
        return []


def search_work_orders(query):
    """Search work orders for relevant context"""
    try:
        azure_sql = AzureSQLService()
        
        # Search for relevant work orders
        safe_query = query.replace("'", "''")
        
        search_query = f"""
            SELECT TOP 5
                w.WONo,
                w.Make,
                w.Model,
                w.Comments,
                w.PrivateComments,
                w.ShopComments,
                w.ClosedDate
            FROM [ben002].WO w
            WHERE 
                w.ClosedDate IS NOT NULL
                AND (
                    w.Comments LIKE '%{safe_query}%' OR
                    w.PrivateComments LIKE '%{safe_query}%' OR
                    w.ShopComments LIKE '%{safe_query}%'
                )
            ORDER BY w.ClosedDate DESC
        """
        
        results = azure_sql.execute_query(search_query)
        
        work_orders = []
        for row in results:
            work_orders.append({
                'wo_number': row['WONo'],
                'make': row['Make'],
                'model': row['Model'],
                'comments': row['Comments'],
                'private_comments': row['PrivateComments'],
                'shop_comments': row['ShopComments'],
                'closed_date': row['ClosedDate'].isoformat() if row['ClosedDate'] else None
            })
        
        return work_orders
        
    except Exception as e:
        logger.error(f"Error searching work orders: {str(e)}")
        return []


def build_context(kb_articles, work_orders):
    """Build context string from KB articles and work orders"""
    context_parts = []
    
    if kb_articles:
        context_parts.append("=== KNOWLEDGE BASE ARTICLES ===")
        for article in kb_articles:
            context_parts.append(f"\nArticle: {article['title']}")
            if article['make']:
                context_parts.append(f"Equipment: {article['make']} {article['model']}")
            if article['symptoms']:
                context_parts.append(f"Symptoms: {article['symptoms'][:200]}")
            if article['solution']:
                context_parts.append(f"Solution: {article['solution'][:200]}")
            context_parts.append("")
    
    if work_orders:
        context_parts.append("\n=== RECENT WORK ORDERS ===")
        for wo in work_orders:
            context_parts.append(f"\nWO #{wo['wo_number']}")
            if wo['make']:
                context_parts.append(f"Equipment: {wo['make']} {wo['model']}")
            if wo['comments']:
                context_parts.append(f"Notes: {wo['comments'][:200]}")
            context_parts.append("")
    
    if not kb_articles and not work_orders:
        return "No specific KB articles or work orders found for this query."
    
    return "\n".join(context_parts)
