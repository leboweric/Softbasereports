import os

class OpenAIConfig:
    """Configuration for OpenAI integration"""
    
    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your-openai-api-key-here')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
    
    # Query Processing Configuration
    MAX_QUERY_LENGTH = 500
    QUERY_TIMEOUT = 30  # seconds
    
    # Forklift Dealership Schema Information
    SCHEMA_CONTEXT = """
    You are an AI assistant for a forklift dealership management system. The database contains the following main entities:
    
    CUSTOMERS:
    - customer_id, company_name, contact_person, phone, email, address, credit_limit, account_status
    
    INVENTORY:
    - item_id, item_type (forklift, part, accessory, battery), brand, model, serial_number, 
    - condition (new, used, refurbished), location, cost, selling_price, quantity_available
    
    SALES:
    - sale_id, customer_id, item_id, sale_date, quantity, unit_price, total_amount, 
    - salesperson, payment_terms, delivery_date, warranty_info
    
    RENTALS:
    - rental_id, customer_id, equipment_id, start_date, end_date, daily_rate, 
    - total_amount, deposit, status (active, completed, overdue)
    
    PARTS_ORDERS:
    - order_id, customer_id, part_id, order_date, quantity_ordered, quantity_filled,
    - unit_price, total_amount, supplier, expected_delivery, status
    
    SERVICE_TICKETS:
    - ticket_id, customer_id, equipment_id, service_date, service_type, technician,
    - labor_hours, parts_used, labor_cost, parts_cost, total_cost, status
    
    EMPLOYEES:
    - employee_id, name, role (salesperson, technician, manager), hire_date, territory
    
    Common brands: Linde, Toyota, Crown, Yale, Hyster, Clark, Caterpillar
    """
    
    # Query suggestion templates
    QUERY_SUGGESTIONS = {
        "sales": [
            "What were our total sales last month?",
            "Which salesperson had the highest sales this quarter?",
            "Show me sales by brand for the last 6 months",
            "What's our average sale amount this year?",
            "Which customers bought the most equipment last year?"
        ],
        "inventory": [
            "How many Linde forklifts do we have in stock?",
            "What parts are running low on inventory?",
            "Show me all used equipment available for sale",
            "Which location has the most inventory?",
            "What's the total value of our current inventory?"
        ],
        "rentals": [
            "Which equipment is currently on rental?",
            "What's our rental utilization rate this month?",
            "Show me overdue rental returns",
            "Which customers rent the most equipment?",
            "What's our average rental duration?"
        ],
        "service": [
            "How many service tickets were completed last week?",
            "Which technician has the highest productivity?",
            "What are the most common service issues?",
            "Show me warranty claims for this month",
            "What's our average service response time?"
        ],
        "parts": [
            "Which Linde parts were we not able to fill last week?",
            "What's our parts fill rate this month?",
            "Show me the most ordered parts",
            "Which suppliers have the longest delivery times?",
            "What parts orders are overdue?"
        ],
        "customers": [
            "Who are our top 10 customers by revenue?",
            "Which customers haven't placed orders recently?",
            "Show me customers with overdue payments",
            "What's our customer retention rate?",
            "Which customers need credit limit reviews?"
        ]
    }
    
    # Date parsing patterns
    DATE_PATTERNS = {
        "last week": "DATE >= DATE('now', '-7 days')",
        "this week": "DATE >= DATE('now', 'weekday 0', '-7 days')",
        "last month": "DATE >= DATE('now', 'start of month', '-1 month') AND DATE < DATE('now', 'start of month')",
        "this month": "DATE >= DATE('now', 'start of month')",
        "last quarter": "DATE >= DATE('now', 'start of year', '+' || ((CAST(strftime('%m', 'now') AS INTEGER) - 1) / 3) * 3 || ' months', '-3 months')",
        "this quarter": "DATE >= DATE('now', 'start of year', '+' || ((CAST(strftime('%m', 'now') AS INTEGER) - 1) / 3) * 3 || ' months')",
        "last year": "DATE >= DATE('now', 'start of year', '-1 year') AND DATE < DATE('now', 'start of year')",
        "this year": "DATE >= DATE('now', 'start of year')",
        "yesterday": "DATE = DATE('now', '-1 day')",
        "today": "DATE = DATE('now')"
    }
    
    @classmethod
    def get_system_prompt(cls):
        """Get the system prompt for OpenAI"""
        return f"""
        {cls.SCHEMA_CONTEXT}
        
        Your role is to help users query this forklift dealership database using natural language.
        
        When a user asks a question:
        1. Analyze the intent and identify relevant tables/fields
        2. Convert time references (last week, this month, etc.) to appropriate date filters
        3. Generate a structured query plan that can be executed against the database
        4. Provide a clear explanation of what data will be retrieved
        
        Always respond in JSON format with:
        {{
            "intent": "brief description of what user wants",
            "tables": ["list", "of", "relevant", "tables"],
            "filters": {{"field": "condition", "date_range": "parsed_dates"}},
            "query_type": "aggregation|list|count|analysis",
            "explanation": "human-readable explanation of the query",
            "suggested_visualization": "chart_type if applicable"
        }}
        
        Be helpful but accurate. If a query is ambiguous, ask for clarification.
        """

