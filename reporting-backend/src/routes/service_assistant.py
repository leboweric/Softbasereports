from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
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
        
        # Extract equipment info from work orders for web search
        equipment_make = None
        equipment_model = None
        if wo_context:
            # Get the most common make/model from the WO results
            equipment_make = wo_context[0].get('make')
            equipment_model = wo_context[0].get('model')
        
        # Check if this is an error code query
        keywords = extract_keywords(user_message)
        import re
        error_code_pattern = re.compile(r'^[a-z]?[0-9]{2,5}[a-z]?$', re.IGNORECASE)
        has_error_codes = any(error_code_pattern.match(k) for k in keywords[:5])
        
        # Search web for external technical resources
        web_context = []
        total_internal_results = len(kb_context) + len(wo_context)
        
        # Always search web for error code queries (to get manufacturer documentation)
        # Or if internal data is limited (< 5 results)
        if has_error_codes or total_internal_results < 5:
            reason = "error code query" if has_error_codes else f"limited internal results ({total_internal_results})"
            logger.warning(f"[WEB SEARCH] Triggering web search: {reason}")
            web_context = search_web_resources(user_message, equipment_make, equipment_model)
        
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
    import re
    
    logger.warning(f"[KEYWORD EXTRACTION] Original query: '{query}'")
    
    # Extract error codes - both numeric (1410, 335) and alphanumeric (L232, E20)
    # Pattern matches:
    # - Pure numbers: 1410, 335, 1862
    # - Letter + numbers: L232, E20, H25
    # - Numbers + letters: 1410A, 335B (less common but possible)
    error_codes = re.findall(r'\b(?:error\s*)?(?:code\s*)?([A-Z]?[0-9]{2,5}[A-Z]?)\b', query, re.IGNORECASE)
    # Convert to lowercase for consistent searching
    error_codes = [code.lower() for code in error_codes if code]
    logger.warning(f"[KEYWORD EXTRACTION] Error codes detected: {error_codes}")
    
    # Remove common question words
    stop_words = {'how', 'do', 'i', 'what', 'when', 'where', 'why', 'is', 'are', 'the', 'a', 'an', 'to', 'for', 'on', 'troubleshoot', 'fix', 'repair', 'mean', 'does', 'and', 'or'}
    words = query.lower().split()
    keywords = [w.strip('?.,!&') for w in words if w.lower() not in stop_words and len(w) > 2]
    logger.warning(f"[KEYWORD EXTRACTION] Initial keywords (before error code processing): {keywords}")
    
    # Add error codes as priority keywords (they'll be searched first)
    if error_codes:
        # Remove 'error' and 'code' from keywords if error codes were found
        keywords = [k for k in keywords if k not in ['error', 'code', 'codes']]
        # Remove any error codes that were already in keywords to avoid duplicates
        keywords = [k for k in keywords if k not in error_codes]
        # Remove any remaining stop words that slipped through
        keywords = [k for k in keywords if k not in stop_words]
        # Prepend error codes so they're searched first
        keywords = error_codes + keywords
    
    logger.warning(f"[KEYWORD EXTRACTION] Final keywords: {keywords}")
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
        
        insert_query = f"""
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
        
        # Build AND conditions - each keyword must appear somewhere in the article
        # For each keyword, check if it appears in ANY of the searchable fields
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
        
        # Join with AND instead of OR - ALL keywords must be present
        search_query = f"""
            SELECT id, title, equipment_make, equipment_model, issue_category, 
                   symptoms, root_cause, solution, related_wo_numbers
            FROM knowledge_base
            WHERE {' AND '.join(conditions)}
            ORDER BY created_date DESC
            LIMIT 10
        """
        
        logger.warning(f"[KB SEARCH] Executing query with {len(conditions)} conditions for keywords: {keywords}")
        results = postgres.execute_query(search_query, tuple(params))
        logger.warning(f"[KB SEARCH] Found {len(results) if results else 0} articles")
        
        if results:
            logger.warning(f"[KB SEARCH] First result: KB #{results[0].get('id')} - {results[0].get('title')}")
        
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
        azure_sql = get_tenant_db()
        schema = get_tenant_schema()
        keywords = extract_keywords(query)
        
        if not keywords:
            return []
        
        # Check if keywords are error codes (alphanumeric patterns)
        import re
        error_code_pattern = re.compile(r'^[a-z]?[0-9]{2,5}[a-z]?$', re.IGNORECASE)
        
        # Separate error codes from other keywords
        error_codes = [k for k in keywords[:5] if error_code_pattern.match(k)]
        other_keywords = [k for k in keywords[:5] if not error_code_pattern.match(k)]
        
        logger.warning(f"[WO SEARCH] Error codes: {error_codes}, Other keywords: {other_keywords}")
        
        # Build search conditions
        conditions = []
        
        # If we have multiple error codes, use OR logic between them
        # (find WOs with ANY of the error codes)
        if error_codes:
            error_code_conditions = []
            for code in error_codes:
                safe_code = code.replace("'", "''")
                error_code_conditions.append(f"""
                    (w.Comments LIKE '%{safe_code}%' OR
                     w.PrivateComments LIKE '%{safe_code}%' OR
                     w.ShopComments LIKE '%{safe_code}%')
                """)
            # Join error codes with OR
            conditions.append(f"({' OR '.join(error_code_conditions)})")
        
        # For other keywords, require ALL of them (AND logic)
        for keyword in other_keywords:
            safe_keyword = keyword.replace("'", "''")
            conditions.append(f"""
                (w.Comments LIKE '%{safe_keyword}%' OR
                 w.PrivateComments LIKE '%{safe_keyword}%' OR
                 w.ShopComments LIKE '%{safe_keyword}%' OR
                 w.Make LIKE '%{safe_keyword}%' OR
                 w.Model LIKE '%{safe_keyword}%')
            """)
        
        # For error code searches, prioritize results that have codes in comments
        order_by = "w.ClosedDate DESC"
        if error_codes:
            # Build CASE statement for all error codes
            case_conditions = []
            for idx, code in enumerate(error_codes, 1):
                safe_code = code.replace("'", "''")
                case_conditions.append(f"WHEN w.Comments LIKE '%{safe_code}%' THEN {idx}")
            for idx, code in enumerate(error_codes, len(error_codes) + 1):
                safe_code = code.replace("'", "''")
                case_conditions.append(f"WHEN w.PrivateComments LIKE '%{safe_code}%' THEN {idx}")
            
            order_by = f"""
                CASE 
                    {' '.join(case_conditions)}
                    ELSE 999
                END,
                w.ClosedDate DESC
            """
        
        # Join all conditions with AND
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
            FROM {schema}.WO w
            WHERE 
                w.ClosedDate IS NOT NULL
                AND ({' AND '.join(conditions)})
            ORDER BY {order_by}
        """
        
        logger.warning(f"[WO SEARCH] Executing SQL query: {search_query[:500]}...")
        results = azure_sql.execute_query(search_query)
        logger.warning(f"[WO SEARCH] Found {len(results) if results else 0} work orders for keywords {keywords}")
        
        if results:
            logger.warning(f"[WO SEARCH] First result: WO #{results[0].get('WONo')} - {results[0].get('Comments', '')[:100]}...")
        
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


def search_web_resources(query, equipment_make=None, equipment_model=None):
    """Search web for technical documentation and service manuals
    
    Args:
        query: The user's question
        equipment_make: Equipment make extracted from WO results (e.g., 'Linde')
        equipment_model: Equipment model extracted from WO results (e.g., 'E20')
    """
    try:
        keywords = extract_keywords(query)
        
        if not keywords:
            return []
        
        # Build search query focused on technical documentation
        search_terms = ' '.join(keywords[:5])
        
        # If we have equipment info from WOs, include it for manufacturer-specific results
        if equipment_make:
            # Clean the model string - remove fleet numbers (FL#XX), unit numbers, etc.
            clean_model = equipment_model or ''
            if clean_model:
                # Remove patterns like "FL#54", "Unit 123", etc.
                import re
                clean_model = re.sub(r'\s*FL#\d+', '', clean_model)  # Remove FL#XX
                clean_model = re.sub(r'\s*Unit\s*\d+', '', clean_model, flags=re.IGNORECASE)  # Remove Unit XX
                clean_model = re.sub(r'\s*#\d+', '', clean_model)  # Remove #XX
                clean_model = clean_model.strip()
            
            search_terms = f"{equipment_make} {clean_model} {search_terms}".strip()
            logger.warning(f"[WEB SEARCH] Using equipment info from WOs: {equipment_make} {clean_model}")
        
        # For error code queries, build a more focused search
        # Check if keywords are primarily error codes (alphanumeric patterns)
        error_code_pattern = re.compile(r'^[A-Z]?\d{2,5}[A-Z]?$', re.IGNORECASE)
        if all(error_code_pattern.match(kw) for kw in keywords[:3]):
            # This is an error code query - use a more direct search
            technical_query = f"{equipment_make or ''} {clean_model if equipment_make else ''} error code {' '.join(keywords[:3])}".strip()
            logger.warning(f"[WEB SEARCH] Error code query detected, using focused search")
        else:
            # General query - add technical terms
            technical_query = f"{search_terms} service manual troubleshooting repair guide"
        
        logger.warning(f"[WEB SEARCH] Query: {technical_query}")
        
        # Get Google API credentials
        google_api_key = os.getenv('GOOGLE_API_KEY')
        google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        if not google_api_key or not google_search_engine_id:
            logger.warning("[WEB SEARCH] Google API credentials not configured, skipping web search")
            return []
        
        # Use Google Custom Search API
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': google_api_key,
            'cx': google_search_engine_id,
            'q': technical_query,
            'num': 5  # Number of results
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"[WEB SEARCH] Google API failed with status {response.status_code}: {response.text}")
            return []
        
        data = response.json()
        results = []
        
        # Extract search results
        for idx, item in enumerate(data.get('items', []), 1):
            title = item.get('title', '')
            url = item.get('link', '')
            snippet = item.get('snippet', '')
            
            logger.warning(f"[WEB SEARCH] Result #{idx}: {title}")
            logger.warning(f"[WEB SEARCH] URL: {url}")
            logger.warning(f"[WEB SEARCH] Snippet: {snippet[:150]}...")  # First 150 chars
            
            # Filter for relevant domains (manufacturer sites, technical resources)
            relevant_domains = ['linde', 'yale', 'crown', 'toyota', 'hyster', 'clark', 'raymond', 
                              'jungheinrich', 'manual', 'service', 'repair', 'technical', 'pdf']
            
            if any(domain in url.lower() or domain in title.lower() or domain in snippet.lower() for domain in relevant_domains):
                logger.warning(f"[WEB SEARCH] ✓ Result #{idx} is RELEVANT")
                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet,
                    'source': 'Web Search'
                })
            else:
                logger.warning(f"[WEB SEARCH] ✗ Result #{idx} is NOT relevant")
        
        logger.warning(f"[WEB SEARCH] Found {len(results)} relevant resources out of {len(data.get('items', []))} total results")
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
