from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import logging
import traceback
import time
from datetime import datetime
from src.routes.ai_query import natural_language_query, generate_sql_from_analysis
from src.services.openai_service import OpenAIQueryService
from src.services.azure_sql_service import AzureSQLService
from src.models.user import User
import os

logger = logging.getLogger(__name__)
ai_query_test_bp = Blueprint('ai_query_test', __name__)

# Test queries organized by category
TEST_QUERIES = {
    "Sales Analysis": [
        {"query": "What were our total sales last month?", "expected_fields": ["total_sales", "period"], "expected_type": "aggregation"},
        {"query": "Who are our top 5 customers by revenue this year?", "expected_fields": ["CustomerName", "TotalRevenue"], "expected_type": "list", "expected_rows": 5},
        {"query": "Which salesperson had the highest sales last quarter?", "expected_fields": ["salesperson", "sales"], "expected_type": "aggregation"},
        {"query": "Show me all Toyota forklift sales from last week", "expected_fields": ["InvoiceNo", "Make"], "expected_type": "list"}
    ],
    "Inventory Management": [
        {"query": "How many Linde forklifts do we have in stock?", "expected_fields": ["Make", "quantity_in_stock"], "expected_type": "count"},
        {"query": "Which parts are running low on inventory?", "expected_fields": ["PartNo", "Description", "QtyOnHand"], "expected_type": "list"},
        {"query": "Show me all available forklifts under $20,000", "expected_fields": ["StockNo", "Make", "Model", "SaleAmount"], "expected_type": "list"},
        {"query": "What equipment is currently in maintenance?", "expected_fields": ["StockNo", "Make", "Model"], "expected_type": "list"}
    ],
    "Rental Operations": [
        {"query": "Which customers have active rentals?", "expected_fields": ["customer", "rental"], "expected_type": "list"},
        {"query": "Show me overdue rental returns", "expected_fields": ["rental", "due_date", "overdue"], "expected_type": "list"},
        {"query": "What's our total rental revenue this month?", "expected_fields": ["total_rental_sales", "period"], "expected_type": "aggregation"},
        {"query": "Which equipment is rented out to Polaris?", "expected_fields": ["equipment", "customer"], "expected_type": "list"}
    ],
    "Parts & Service": [
        {"query": "Which Linde parts were we not able to fill last week?", "expected_fields": ["PartNo", "Description"], "expected_type": "list"},
        {"query": "Show me all service appointments for tomorrow", "expected_fields": ["appointment", "service"], "expected_type": "list"},
        {"query": "What parts do we need to reorder?", "expected_fields": ["PartNo", "Description", "QtyOnHand"], "expected_type": "list"},
        {"query": "Which technician completed the most services this month?", "expected_fields": ["technician", "service_count"], "expected_type": "aggregation"}
    ],
    "Customer Insights": [
        {"query": "Give me the serial numbers of all forklifts that Polaris rents from us", "expected_fields": ["SerialNo", "Make", "Model"], "expected_type": "list"},
        {"query": "Which customers haven't made a purchase in 6 months?", "expected_fields": ["customer", "last_purchase"], "expected_type": "list"},
        {"query": "Show me all customers with outstanding invoices", "expected_fields": ["customer", "balance"], "expected_type": "list"},
        {"query": "What's the average order value by customer?", "expected_fields": ["customer", "average_value"], "expected_type": "aggregation"}
    ]
}

def test_single_query(query_info, user_context):
    """Test a single query and return results"""
    start_time = time.time()
    result = {
        "query": query_info["query"],
        "expected_fields": query_info.get("expected_fields", []),
        "expected_type": query_info.get("expected_type", "unknown"),
        "expected_rows": query_info.get("expected_rows"),
        "status": "pending",
        "error": None,
        "sql_query": None,
        "actual_fields": [],
        "actual_type": None,
        "row_count": 0,
        "execution_time": 0,
        "ai_analysis": None,
        "sample_results": None
    }
    
    try:
        # Initialize OpenAI service
        openai_service = OpenAIQueryService()
        
        # Process the query through OpenAI
        ai_result = openai_service.process_natural_language_query(query_info["query"], user_context)
        
        if not ai_result['success']:
            result["status"] = "failed"
            result["error"] = f"AI processing failed: {ai_result.get('error', 'Unknown error')}"
            return result
        
        query_analysis = ai_result['query_analysis']
        result["ai_analysis"] = query_analysis
        result["actual_type"] = query_analysis.get('query_type', 'unknown')
        
        # Generate SQL
        sql_query = generate_sql_from_analysis(query_analysis)
        result["sql_query"] = sql_query
        
        # Execute SQL
        db = AzureSQLService()
        query_results = db.execute_query(sql_query)
        
        if query_results:
            result["row_count"] = len(query_results)
            result["actual_fields"] = list(query_results[0].keys()) if query_results else []
            result["sample_results"] = query_results[:3]  # First 3 rows as sample
            
            # Check if results meet expectations
            result["status"] = "passed"
            
            # Validate expected fields are present
            if query_info.get("expected_fields"):
                missing_fields = []
                for expected_field in query_info["expected_fields"]:
                    # Check if any actual field contains the expected field name (case-insensitive)
                    found = any(expected_field.lower() in actual_field.lower() 
                              for actual_field in result["actual_fields"])
                    if not found:
                        missing_fields.append(expected_field)
                
                if missing_fields:
                    result["status"] = "partial"
                    result["error"] = f"Missing expected fields: {', '.join(missing_fields)}"
            
            # Validate row count if specified
            if query_info.get("expected_rows") and result["row_count"] != query_info["expected_rows"]:
                result["status"] = "partial"
                result["error"] = f"Expected {query_info['expected_rows']} rows, got {result['row_count']}"
            
            # Validate query type
            if result["actual_type"] != result["expected_type"]:
                result["status"] = "partial"
                if result["error"]:
                    result["error"] += f"; Type mismatch: expected {result['expected_type']}, got {result['actual_type']}"
                else:
                    result["error"] = f"Type mismatch: expected {result['expected_type']}, got {result['actual_type']}"
        else:
            result["status"] = "failed"
            result["error"] = "Query returned no results"
            
    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        logger.error(f"Error testing query '{query_info['query']}': {str(e)}", exc_info=True)
    
    result["execution_time"] = round(time.time() - start_time, 2)
    return result

@ai_query_test_bp.route('/test-all', methods=['POST'])
@jwt_required()
def test_all_queries():
    """Test all predefined queries and return comprehensive results"""
    try:
        # Get user context
        current_user_id = get_jwt_identity()
        jwt_claims = get_jwt()
        
        organization_id = jwt_claims.get('organization_id')
        if not organization_id:
            user = User.query.get(current_user_id)
            if user:
                organization_id = user.organization_id
        
        user_context = {'organization_id': organization_id}
        
        # Get optional category filter from request
        data = request.get_json() or {}
        category_filter = data.get('category')
        
        # Determine which categories to test
        categories_to_test = TEST_QUERIES.keys()
        if category_filter and category_filter in TEST_QUERIES:
            categories_to_test = [category_filter]
        
        # Test all queries
        test_results = {}
        total_queries = 0
        passed_queries = 0
        failed_queries = 0
        partial_queries = 0
        
        for category in categories_to_test:
            category_results = []
            for query_info in TEST_QUERIES[category]:
                result = test_single_query(query_info, user_context)
                category_results.append(result)
                total_queries += 1
                
                if result["status"] == "passed":
                    passed_queries += 1
                elif result["status"] == "partial":
                    partial_queries += 1
                else:
                    failed_queries += 1
            
            test_results[category] = category_results
        
        # Calculate summary statistics
        summary = {
            "total_queries": total_queries,
            "passed": passed_queries,
            "partial": partial_queries,
            "failed": failed_queries,
            "success_rate": round((passed_queries / total_queries * 100) if total_queries > 0 else 0, 2),
            "test_timestamp": datetime.now().isoformat(),
            "categories_tested": list(categories_to_test)
        }
        
        return jsonify({
            "success": True,
            "summary": summary,
            "results": test_results
        })
        
    except Exception as e:
        logger.error(f"Error in test-all endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@ai_query_test_bp.route('/test-single', methods=['POST'])
@jwt_required()
def test_single_query_endpoint():
    """Test a single custom query"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        # Get user context
        current_user_id = get_jwt_identity()
        jwt_claims = get_jwt()
        
        organization_id = jwt_claims.get('organization_id')
        if not organization_id:
            user = User.query.get(current_user_id)
            if user:
                organization_id = user.organization_id
        
        user_context = {'organization_id': organization_id}
        
        # Create query info object
        query_info = {
            "query": data['query'],
            "expected_fields": data.get('expected_fields', []),
            "expected_type": data.get('expected_type', 'unknown'),
            "expected_rows": data.get('expected_rows')
        }
        
        result = test_single_query(query_info, user_context)
        
        return jsonify({
            "success": True,
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Error in test-single endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Query variation groups for testing
QUERY_VARIATION_GROUPS = {
    "forklift_rentals": {
        "description": "Different ways to ask for rented forklifts",
        "expected_action": "list_equipment",
        "expected_entity_type": "equipment",
        "expected_entity_subtype": "forklift",
        "expected_filters": {"status": "rented"},
        "variations": [
            "give me a list of all forklifts currently being rented",
            "show me rented forklifts",
            "which forklifts are on rent",
            "list rental forklifts",
            "what forklifts do we have out",
            "I need to see our rental forklifts",
            "can you pull up the lifts we have out?",
            "forklift rentals list please",
            "what fork trucks are customers using",
            "display all forked vehicles currently deployed"
        ]
    },
    "parts_reorder": {
        "description": "Different ways to ask for parts that need reordering",
        "expected_action": "parts_status",
        "expected_entity_type": "parts",
        "expected_filters": {"status": "low"},
        "variations": [
            "what parts do we need to reorder",
            "show me parts running low",
            "which parts are below minimum stock",
            "parts needing reorder",
            "low inventory parts list",
            "what's running out in parts",
            "parts below reorder point",
            "inventory shortages",
            "which parts are low on stock",
            "parts with insufficient inventory"
        ]
    },
    "active_rentals": {
        "description": "Different ways to ask for customers with active rentals",
        "expected_action": "list_rentals",
        "expected_entity_type": "rental",
        "expected_filters": {"status": "active"},
        "variations": [
            "which customers have active rentals",
            "show me who's renting equipment",
            "list of customers with rentals",
            "active rental customers",
            "who has equipment out",
            "customers currently renting",
            "show active rental accounts",
            "who are we renting to",
            "current rental customers list",
            "display all active lessees"
        ]
    }
}

@ai_query_test_bp.route('/test-variations', methods=['POST'])
@jwt_required()
def test_query_variations():
    """Test multiple variations of queries to ensure they produce consistent results"""
    try:
        data = request.get_json() or {}
        group_name = data.get('group', None)
        
        # Get user context
        current_user_id = get_jwt_identity()
        jwt_claims = get_jwt()
        organization_id = jwt_claims.get('organization_id')
        if not organization_id:
            user = User.query.get(current_user_id)
            if user:
                organization_id = user.organization_id
        
        user_context = {'organization_id': organization_id}
        
        # Determine which groups to test
        if group_name and group_name in QUERY_VARIATION_GROUPS:
            groups_to_test = {group_name: QUERY_VARIATION_GROUPS[group_name]}
        else:
            groups_to_test = QUERY_VARIATION_GROUPS
        
        results = {}
        
        for group_name, group_data in groups_to_test.items():
            group_results = {
                "description": group_data["description"],
                "expected": {
                    "action": group_data.get("expected_action"),
                    "entity_type": group_data.get("expected_entity_type"),
                    "entity_subtype": group_data.get("expected_entity_subtype"),
                    "filters": group_data.get("expected_filters")
                },
                "variations": []
            }
            
            sql_queries_seen = {}
            unique_sql_count = 0
            
            for variation in group_data["variations"]:
                # Test each variation
                result = test_single_query(
                    {"query": variation, "expected_fields": [], "expected_type": "list"},
                    user_context
                )
                
                # Extract key information
                ai_analysis = result.get("ai_analysis", {})
                sql_query = result.get("sql_query", "")
                
                # Normalize SQL for comparison (remove extra whitespace)
                normalized_sql = " ".join(sql_query.split()) if sql_query else ""
                
                # Track unique SQL queries
                if normalized_sql and normalized_sql not in sql_queries_seen:
                    sql_queries_seen[normalized_sql] = []
                    unique_sql_count += 1
                
                if normalized_sql:
                    sql_queries_seen[normalized_sql].append(variation)
                
                variation_result = {
                    "query": variation,
                    "status": result["status"],
                    "ai_analysis": {
                        "query_action": ai_analysis.get("query_action"),
                        "entity_type": ai_analysis.get("entity_type"),
                        "entity_subtype": ai_analysis.get("entity_subtype"),
                        "filters": ai_analysis.get("filters"),
                        "use_rental_history": ai_analysis.get("use_rental_history")
                    },
                    "sql_normalized": normalized_sql[:100] + "..." if len(normalized_sql) > 100 else normalized_sql,
                    "error": result.get("error")
                }
                
                group_results["variations"].append(variation_result)
            
            # Add summary
            group_results["summary"] = {
                "total_variations": len(group_data["variations"]),
                "unique_sql_queries": unique_sql_count,
                "consistency_score": f"{(1 / unique_sql_count * 100):.1f}%" if unique_sql_count > 0 else "0%",
                "sql_groups": [{"sql": sql[:100] + "...", "queries": queries} 
                              for sql, queries in sql_queries_seen.items()]
            }
            
            results[group_name] = group_results
        
        return jsonify({
            "success": True,
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in test-variations endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@ai_query_test_bp.route('/test-categories', methods=['GET'])
@jwt_required()
def get_test_categories():
    """Get all available test categories and their queries"""
    categories = {}
    for category, queries in TEST_QUERIES.items():
        categories[category] = {
            "query_count": len(queries),
            "queries": [q["query"] for q in queries]
        }
    
    # Add variation groups
    categories["Variation Groups"] = {
        "groups": list(QUERY_VARIATION_GROUPS.keys()),
        "total_variations": sum(len(g["variations"]) for g in QUERY_VARIATION_GROUPS.values())
    }
    
    return jsonify({
        "success": True,
        "categories": categories
    })