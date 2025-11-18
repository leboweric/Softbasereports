from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.azure_sql_service import AzureSQLService
from src.services.postgres_service import get_postgres_db
import openai
import os
import json
import logging
import requests
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

service_assistant_bp = Blueprint('service_assistant', __name__)

@service_assistant_bp.route('/api/service-assistant/chat', methods=['POST'])
@jwt_required()
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
        
        # Search web for external technical resources if internal data is limited
        web_context = []
        total_internal_results = len(kb_context) + len(wo_context)
        if total_internal_results < 5:
            logger.info(f"Limited internal results ({total_internal_results}), searching web for additional resources")
            web_context = search_web_resources(user_message)
        
        # Build context for AI
        context = build_context(kb_context, wo_context, web_context)
        
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
                "content": f"""You are a service technician assistant for a forklift and material handling equipment company.

Your job is to help technicians by searching through the company's Knowledge Base articles and historical work order data.

IMPORTANT INSTRUCTIONS:
1. **ALWAYS cite specific sources** when providing information:
   - Internal KB articles: "KB Article #[ID]"
   - Internal work orders: "WO #[number]"
   - External resources: "[Resource Title]" with URL
   - Example: "According to WO #12345, the technician found..."
   - Example: "The Linde service manual indicates..."

2. **Prioritize internal company data**:
   - Start with KB articles and work orders from your company's database
   - These contain actual repair history and proven solutions
   - Quote specific symptoms, solutions, and technician notes
   - If multiple relevant WOs exist, mention the most relevant ones

3. **Use external resources as supplementary information**:
   - When external technical resources are provided, use them to supplement internal data
   - Manufacturer service manuals and technical guides provide official procedures
   - Clearly distinguish between company experience and manufacturer recommendations
   - Provide URLs for external resources so technicians can access full documentation

4. **Be specific and practical**:
   - Provide step-by-step troubleshooting based on actual past repairs
   - Mention specific parts, procedures, or findings from the work orders
   - If a pattern emerges from multiple WOs, point it out
   - Combine internal experience with manufacturer best practices

5. **When limited data is available**:
   - Use whatever context is provided (internal or external)
   - If only external resources are available, rely on those
   - If no specific data exists, provide general troubleshooting advice
   - Suggest what information would be helpful to search for

---
CONTEXT FROM YOUR COMPANY'S DATABASE:
{context}
---

Now answer the technician's question using the above context. Remember to cite specific WO numbers and KB article IDs!
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
        
        # Log the query for analytics
        try:
            log_query(
                query_text=user_message,
                kb_results_count=len(kb_context),
                wo_results_count=len(wo_context),
                web_results_count=len(web_context),
                response_text=assistant_message,
                user_email=get_jwt_identity()
            )
        except Exception as log_error:
            logger.error(f"Failed to log query: {str(log_error)}")
            # Don't fail the request if logging fails
        
        return jsonify({
            'response': assistant_message,
            'context': {
                'kb_articles': kb_context,
                'work_orders': wo_context
            }
        })
        
    except Exception as e:
        logger.error(f"Error in service assistant chat: {str(e)}")
        return jsonify({'error': str(e)}), 500


def extract_keywords(query):
    """Extract key technical terms from user query"""
    # Remove common question words
    stop_words = {'how', 'do', 'i', 'what', 'when', 'where', 'why', 'is', 'are', 'the', 'a', 'an', 'to', 'for', 'on', 'troubleshoot', 'fix', 'repair'}
    words = query.lower().split()
    keywords = [w.strip('?.,!') for w in words if w.lower() not in stop_words and len(w) > 2]
    return keywords

def extract_equipment_info(query):
    """Extract equipment make and model from query"""
    query_lower = query.lower()
    makes = ['linde', 'yale', 'crown', 'toyota', 'hyster', 'clark', 'raymond', 'jungheinrich', 'nissan', 'mitsubishi', 'komatsu', 'cat', 'caterpillar']
    
    found_make = None
    for make in makes:
        if make in query_lower:
            found_make = make.capitalize()
            break
    
    # Simple model extraction (look for patterns like H20, E50, etc.)
    import re
    model_match = re.search(r'\b[A-Z]\d{2,4}\b', query, re.IGNORECASE)
    found_model = model_match.group(0).upper() if model_match else None
    
    return found_make, found_model

def log_query(query_text, kb_results_count, wo_results_count, web_results_count, response_text, user_email):
    """Log Service Assistant query for analytics"""
    try:
        postgres = get_postgres_db()
        keywords = extract_keywords(query_text)
        equipment_make, equipment_model = extract_equipment_info(query_text)
        
        insert_query = """
            INSERT INTO service_assistant_queries 
            (query_text, keywords, equipment_make, equipment_model, 
             kb_results_count, wo_results_count, web_results_count, 
             response_text, user_email)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        postgres.execute_update(
            insert_query,
            (query_text, keywords, equipment_make, equipment_model,
             kb_results_count, wo_results_count, web_results_count,
             response_text, user_email)
        )
        
        logger.info(f"Logged query: '{query_text[:50]}...' from {user_email}")
        
    except Exception as e:
        logger.error(f"Error logging query: {str(e)}")
        raise

def search_kb_articles(query):
    """Search KB articles for relevant context"""
    try:
        postgres = get_postgres_db()
        keywords = extract_keywords(query)
        
        if not keywords:
            return []
        
        # Build OR conditions for each keyword
        conditions = []
        params = []
        for keyword in keywords[:5]:  # Limit to 5 keywords
            conditions.append("""
                (title ILIKE %s OR
                 symptoms ILIKE %s OR
                 solution ILIKE %s OR
                 root_cause ILIKE %s OR
                 equipment_make ILIKE %s OR
                 equipment_model ILIKE %s)
            """)
            pattern = f'%{keyword}%'
            params.extend([pattern] * 6)
        
        search_query = f"""
            SELECT id, title, equipment_make, equipment_model, issue_category, 
                   symptoms, root_cause, solution, related_wo_numbers
            FROM knowledge_base
            WHERE {' OR '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT 10
        """
        
        results = postgres.execute_query(search_query, tuple(params))
        logger.info(f"KB search for keywords {keywords}: found {len(results) if results else 0} articles")
        
        articles = []
        if results:
            for row in results:
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'make': row[2],
                    'model': row[3],
                    'category': row[4],
                    'symptoms': row[5],
                    'root_cause': row[6],
                    'solution': row[7],
                    'related_wo_numbers': row[8]
                })
        
        return articles
        
    except Exception as e:
        logger.error(f"Error searching KB articles: {str(e)}")
        return []


def search_work_orders(query):
    """Search work orders for relevant context"""
    try:
        azure_sql = AzureSQLService()
        keywords = extract_keywords(query)
        
        if not keywords:
            return []
        
        # Build search conditions for each keyword
        conditions = []
        for keyword in keywords[:5]:  # Limit to 5 keywords
            safe_keyword = keyword.replace("'", "''")
            conditions.append(f"""
                (w.Comments LIKE '%{safe_keyword}%' OR
                 w.PrivateComments LIKE '%{safe_keyword}%' OR
                 w.ShopComments LIKE '%{safe_keyword}%' OR
                 w.Make LIKE '%{safe_keyword}%' OR
                 w.Model LIKE '%{safe_keyword}%')
            """)
        
        search_query = f"""
            SELECT TOP 20
                w.WONo,
                w.Make,
                w.Model,
                w.Comments,
                w.PrivateComments,
                w.ShopComments,
                w.ClosedDate,
                w.BillTo
            FROM [ben002].WO w
            WHERE 
                w.ClosedDate IS NOT NULL
                AND ({' OR '.join(conditions)})
            ORDER BY w.ClosedDate DESC
        """
        
        results = azure_sql.execute_query(search_query)
        logger.info(f"WO search for keywords {keywords}: found {len(results) if results else 0} work orders")
        
        work_orders = []
        if results:
            for row in results:
                work_orders.append({
                    'wo_number': row['WONo'],
                    'make': row['Make'],
                    'model': row['Model'],
                    'customer': row['BillTo'],
                    'comments': row['Comments'],
                    'private_comments': row['PrivateComments'],
                    'shop_comments': row['ShopComments'],
                    'closed_date': row['ClosedDate'].isoformat() if row['ClosedDate'] else None
                })
        
        return work_orders
        
    except Exception as e:
        logger.error(f"Error searching work orders: {str(e)}")
        return []


def search_web_resources(query):
    """Search web for manufacturer service manuals and technical documentation"""
    try:
        keywords = extract_keywords(query)
        if not keywords:
            return []
        
        # Build search query focused on technical documentation
        search_terms = ' '.join(keywords[:5])
        # Add technical terms to focus on service manuals and troubleshooting guides
        technical_query = f"{search_terms} service manual troubleshooting repair guide"
        
        # Use DuckDuckGo HTML search (no API key required)
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(technical_query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=5)
        
        if response.status_code != 200:
            logger.warning(f"Web search failed with status {response.status_code}")
            return []
        
        # Parse results (simple extraction from HTML)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        result_links = soup.find_all('a', class_='result__a', limit=5)
        
        for link in result_links:
            title = link.get_text(strip=True)
            url = link.get('href', '')
            
            # Filter for relevant domains (manufacturer sites, technical resources)
            relevant_domains = ['linde', 'yale', 'crown', 'toyota', 'hyster', 'clark', 'raymond', 
                              'jungheinrich', 'manual', 'service', 'repair', 'technical', 'pdf']
            
            if any(domain in url.lower() or domain in title.lower() for domain in relevant_domains):
                results.append({
                    'title': title,
                    'url': url,
                    'source': 'Web Search'
                })
        
        logger.info(f"Web search for '{search_terms}': found {len(results)} relevant resources")
        return results[:3]  # Limit to top 3 web results
        
    except Exception as e:
        logger.error(f"Error searching web resources: {str(e)}")
        return []


def build_context(kb_articles, work_orders, web_resources=None):
    """Build context string from KB articles, work orders, and web resources"""
    context_parts = []
    
    if kb_articles:
        context_parts.append("=== KNOWLEDGE BASE ARTICLES ===")
        for i, article in enumerate(kb_articles, 1):
            context_parts.append(f"\n[KB Article #{article['id']}] {article['title']}")
            if article['make']:
                context_parts.append(f"  Equipment: {article['make']} {article['model']}")
            context_parts.append(f"  Category: {article['category']}")
            if article['symptoms']:
                context_parts.append(f"  Symptoms: {article['symptoms'][:300]}")
            if article['root_cause']:
                context_parts.append(f"  Root Cause: {article['root_cause'][:300]}")
            if article['solution']:
                context_parts.append(f"  Solution: {article['solution'][:300]}")
            if article.get('related_wo_numbers'):
                context_parts.append(f"  Related WOs: {article['related_wo_numbers']}")
            context_parts.append("")
    
    if work_orders:
        context_parts.append("\n=== HISTORICAL WORK ORDERS ===")
        for wo in work_orders:
            context_parts.append(f"\n[WO #{wo['wo_number']}]")
            if wo['make']:
                context_parts.append(f"  Equipment: {wo['make']} {wo['model']}")
            if wo.get('customer'):
                context_parts.append(f"  Customer: {wo['customer']}")
            if wo['comments']:
                context_parts.append(f"  Technician Comments: {wo['comments'][:400]}")
            if wo['private_comments']:
                context_parts.append(f"  Private Notes: {wo['private_comments'][:400]}")
            if wo['shop_comments']:
                context_parts.append(f"  Shop Notes: {wo['shop_comments'][:400]}")
            if wo['closed_date']:
                context_parts.append(f"  Completed: {wo['closed_date'][:10]}")
            context_parts.append("")
    
    if web_resources:
        context_parts.append("\n=== EXTERNAL TECHNICAL RESOURCES ===")
        context_parts.append("(Manufacturer service manuals, technical guides, and documentation)\n")
        for resource in web_resources:
            context_parts.append(f"[External Resource] {resource['title']}")
            context_parts.append(f"  URL: {resource['url']}")
            context_parts.append("")
    
    if not kb_articles and not work_orders and not web_resources:
        return "No specific KB articles, work orders, or external resources found for this query. Provide general troubleshooting advice."
    
    return "\n".join(context_parts)
