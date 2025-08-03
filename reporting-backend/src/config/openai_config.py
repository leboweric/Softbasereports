import os

class OpenAIConfig:
    """Configuration for OpenAI integration"""
    
    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your-openai-api-key-here')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')  # More cost-effective and supports JSON
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
    - CreditLimit, Balance, YTD (year-to-date sales), 
    - LastYrYTD (last year's YTD), TwoYrYTD (two years ago YTD),
    - LastSaleDate, LastPaymentDate, CustomerStatus
    
    EQUIPMENT (ben002.Equipment):
    - UnitNo (equipment identifier - NOT StockNo), SerialNo, Make, Model, ModelYear, 
    - RentalStatus (In Stock, Sold, Rented), Id (primary key), Cost, Sell, 
    - Location, Department, Customer (customer ID when sold/rented)
    - Note: Use UnitNo for equipment lookups, NOT StockNo
    
    INVOICES (ben002.InvoiceReg):
    - InvoiceNo, InvoiceDate, Customer (customer ID), BillToName, 
    - GrandTotal (total invoice amount), SalesTax, InvoiceStatus, 
    - Department (department field, e.g. 'Service'), 
    - SaleCode (more specific: 'SVE'=Service, 'PRT'=Parts, 'RENTR'=Rental Repairs, 'RENTRS'=Rental Repairs Shop)
    - LaborTaxable, LaborNonTax (labor revenue)
    - PartsTaxable, PartsNonTax (parts revenue)
    - MiscTaxable, MiscNonTax (misc revenue)
    - Note: For total labor revenue use (LaborTaxable + LaborNonTax)
    - Note: For total parts revenue use (PartsTaxable + PartsNonTax)
    
    SERVICE CLAIMS (ben002.ServiceClaim):
    - ServiceClaimNo, OpenDate, CloseDate, Customer (customer ID), 
    - StockNo, SerialNo, TotalLabor, TotalParts, Technician
    - Note: Use CloseDate IS NULL to find open claims
    
    PARTS (ben002.Parts) - NOT NationalParts!:
    - PartNo, Description, Supplier, Cost, List (list price), 
    - OnHand (quantity on hand), BinLocation, PartType
    - Note: The actual parts inventory is in Parts table, NOT NationalParts
    
    AR DETAIL (ben002.ARDetail):
    - Customer, InvoiceNo, InvoiceDate, OriginalAmount, Balance, 
    - DueDate, DaysPastDue, InvoiceType
    
    WORK ORDERS (ben002.WO):
    - WONo (primary key), OpenDate, ClosedDate, CompletedDate, 
    - Type (S=Service, R=Rental, I=Internal), BillTo (customer ID), 
    - UnitNo (equipment), Technician, ServiceType, Department
    - Note: Use ClosedDate IS NULL to find open work orders
    
    WORK ORDER COSTS:
    - ben002.WOLabor: WONo, Sell (labor rate), Hours, TotalSell (total labor)
    - ben002.WOParts: WONo, PartNo, Sell (unit price), Qty, BOQty (backorder qty)
    - ben002.WOMisc: WONo, Description, Sell (misc cost)
    
    WORK ORDER QUOTES (ben002.WOQuote):
    - WONo, QuoteLine (line number), Type (L=Labor, P=Parts), 
    - Amount, CreationTime, QuoteNo
    - Note: This contains quote line items, not complete quotes
    
    INVOICE SALES (ben002.InvoiceSales):
    - InvoiceNo, ItemNo, Description, Quantity, Price, ExtPrice
    
    KEY VIEWS FOR REPORTING:
    - ben002.Sales: Pre-aggregated sales data
    - ben002.PartsSales: Parts sales analytics
    - ben002.WIPView: Work in progress summary
    - ben002.GLDetail: General ledger details
    - ben002.EquipmentHistory: Equipment usage history
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
    
    # Date parsing patterns (SQL Server compatible)
    DATE_PATTERNS = {
        "last week": ">= DATEADD(day, -7, GETDATE())",
        "this week": ">= DATEADD(day, -DATEPART(dw, GETDATE()) + 1, GETDATE())",
        "last month": ">= DATEADD(month, -1, DATEADD(day, 1-DAY(GETDATE()), GETDATE())) AND < DATEADD(day, 1-DAY(GETDATE()), GETDATE())",
        "this month": ">= DATEADD(day, 1-DAY(GETDATE()), GETDATE())",
        "last quarter": ">= DATEADD(quarter, -1, DATEADD(quarter, DATEDIFF(quarter, 0, GETDATE()), 0)) AND < DATEADD(quarter, DATEDIFF(quarter, 0, GETDATE()), 0)",
        "this quarter": ">= DATEADD(quarter, DATEDIFF(quarter, 0, GETDATE()), 0)",
        "last year": ">= DATEADD(year, -1, DATEADD(year, DATEDIFF(year, 0, GETDATE()), 0)) AND < DATEADD(year, DATEDIFF(year, 0, GETDATE()), 0)",
        "this year": ">= DATEADD(year, DATEDIFF(year, 0, GETDATE()), 0)",
        "yesterday": "= CAST(DATEADD(day, -1, GETDATE()) AS DATE)",
        "today": "= CAST(GETDATE() AS DATE)"
    }
    
    @classmethod
    def get_system_prompt(cls):
        """Get the system prompt for OpenAI"""
        return f"""
        {cls.SCHEMA_CONTEXT}
        
        Your role is to help users query this Softbase dealership database using natural language.
        
        When a user asks a question:
        1. Analyze the intent and identify relevant tables/fields
        2. Prefer using optimized views when available (e.g., Sales view for sales analytics, PartsSales for parts analytics)
        3. Convert time references (last week, this month, etc.) to appropriate date filters
        4. Generate a structured query plan that can be executed against the database
        5. Provide a clear explanation of what data will be retrieved
        
        IMPORTANT distinctions:
        - "sales" or "revenue" = total invoice amounts (GrandTotal from InvoiceReg)
        - "net income" or "profit" = revenue minus costs (requires cost data - not available)
        - "gross margin" = revenue minus cost of goods sold (requires COGS - not available)
        - "collections" or "payments" = actual cash received (requires payment data)
        
        If user asks for net income, profit, or margin data, indicate in the intent that cost data is needed.
        
        Always respond in JSON format with:
        {{
            "intent": "brief description of what user wants (be specific about sales vs profit vs income)",
            "tables": ["list", "of", "relevant", "tables"],
            "filters": {{"field": "condition", "date_range": "parsed_dates"}},
            "query_type": "aggregation|list|count|analysis",
            "explanation": "human-readable explanation of the query",
            "suggested_visualization": "chart_type if applicable"
        }}
        
        Be helpful but accurate. If a query is ambiguous, ask for clarification.
        """

