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
    
    # Softbase Dealership Schema Information
    SCHEMA_CONTEXT = """
    You are an AI assistant for a Softbase dealership management system. The database uses the ben002 schema and contains the following main entities:
    
    CUSTOMER (ben002.Customer):
    - ID (primary key), Name, Address1, City, State, ZipCode, Phone, 
    - CreditLimit, CreditBalance, YTD (year-to-date sales), LastSaleDate, LastPaymentDate
    
    EQUIPMENT (ben002.Equipment):
    - StockNo, SerialNo, Make, Model, ModelYear, RentalStatus (In Stock, Sold, Rented),
    - Customer (foreign key), AcquiredDate, SaleAmount, Hours, Location
    
    INVOICES (ben002.InvoiceReg):
    - InvoiceNo, InvoiceDate, Customer (foreign key), BillToName, 
    - GrandTotal, SalesTax, InvoiceStatus, InvoiceType, Department
    
    SERVICE CLAIMS (ben002.ServiceClaim):
    - ServiceClaimNo, OpenDate, CloseDate, Customer (foreign key), StockNo, SerialNo,
    - TotalLabor, TotalParts, Status, Technician
    
    PARTS (ben002.NationalParts):
    - PartNo, Description, Supplier, Cost, Price, QtyOnHand, BinLocation
    
    AR DETAIL (ben002.ARDetail):
    - Customer, InvoiceNo, Balance, DueDate, DaysPastDue
    
    WORK ORDERS:
    - Work order management for service and repairs
    
    Common equipment brands in the system
    """
    
    # Query suggestion templates
    QUERY_SUGGESTIONS = {
        "sales": [
            "What were our total sales last month?",
            "Show me top customers by YTD sales",
            "List all invoices over $10,000 this quarter",
            "What's our average invoice amount this year?",
            "Which departments have the highest sales?"
        ],
        "inventory": [
            "How many units are currently in stock?",
            "Show equipment by rental status",
            "List all available equipment for sale",
            "Which models have we sold the most?",
            "What's the total value of our inventory?"
        ],
        "service": [
            "How many open service claims do we have?",
            "Show service claims by technician",
            "What's the average repair cost?",
            "List equipment with frequent service issues",
            "Show service revenue by month"
        ],
        "parts": [
            "Which parts are low in stock?",
            "Show parts usage for the last month",
            "List most frequently ordered parts",
            "What's our parts inventory value?",
            "Show parts by supplier"
        ],
        "customers": [
            "Who are our top 10 customers by credit limit?",
            "Show customers with overdue balances",
            "Which customers haven't purchased recently?",
            "List customers by state",
            "Show customer payment history"
        ],
        "financial": [
            "What's our AR aging summary?",
            "Show collections for this month",
            "List invoices past 60 days due",
            "What's our total outstanding AR?",
            "Show revenue by department"
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
        
        Your role is to help users query this Softbase dealership database using natural language.
        
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

