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
    
    # ERP Dealership Schema Information
    SCHEMA_CONTEXT = """
    You are an AI assistant for a dealership ERP management system. The database uses the ben002 schema and contains the following main entities:
    
    CUSTOMER (ben002.Customer):
    - Id (bigint PK), Number (customer number), Name, Address, City, State, ZipCode, Phone,
    - Terms, CreditHoldFlag, Taxable, TaxCode, 
    - Salesman1, Salesman2, Salesman3, Salesman4, Salesman5, Salesman6,
    - Note: Use Number field to join with other tables, not Id
    - Note: NO Balance or YTD columns - use ARDetail for outstanding balances
    
    EQUIPMENT (ben002.Equipment):
    - UnitNo (nvarchar - equipment identifier), SerialNo, Make, Model, ModelYear,
    - RentalStatus (In Stock, Sold, Rented), Location, SubLocation
    - Customer (bit - boolean flag), CustomerNo (nvarchar - actual customer number)
    - Cost (decimal), Sell (decimal), Retail (decimal)
    - DayRent, WeekRent, MonthRent, FourWeekRent (rental rates)
    - NO Description field! NO StockNo field!
    - Join with Customer using CustomerNo = Customer.Number (NOT Customer field which is boolean)
    
    INVOICES (ben002.InvoiceReg):
    - InvoiceNo (int PK), InvoiceDate, BillTo, BillToName (customer name string),
    - Customer (bit NOT NULL - boolean flag, NOT a customer ID!)
    - GrandTotal (total invoice amount), TotalTax
    - SaleCode (e.g. 'SVE'=Service, 'PRT'=Parts), SaleDept (smallint), SaleBranch
    - LaborTaxable, LaborNonTax, PartsTaxable, PartsNonTax (revenue fields)
    - MiscTaxable, MiscNonTax, EquipmentTaxable, EquipmentNonTax
    - RentalTaxable, RentalNonTax
    - NO Department field! Use SaleCode/SaleDept
    - Customer field is boolean - join invoices to customers via separate table
    - For customer name in queries, use BillToName field
    
    SERVICE CLAIMS (ben002.ServiceClaim):
    - ServiceClaimNo, OpenDate, CloseDate, Customer (customer ID), 
    - StockNo, SerialNo, TotalLabor, TotalParts, Technician
    - Note: Use CloseDate IS NULL to find open claims
    
    PARTS (ben002.Parts) - NOT NationalParts!:
    - Id (bigint PK), PartNo (nvarchar), Warehouse, Description,
    - OnHand (decimal - quantity on hand), MinStock, MaxStock, AbsoluteMin
    - Cost (decimal), List (decimal - list price), Discount, Wholesale
    - Bin, Bin1, Bin2, Bin3, Bin4 (location fields)
    - Allocated, OnOrder, BackOrder (inventory tracking)
    - NO Supplier column! NO QtyOnHand - use OnHand!
    - NO Price field - use List for list price!
    
    AR DETAIL (ben002.ARDetail):
    - CustomerNo (nvarchar), InvoiceNo (int), Amount (decimal), ApplyToInvoiceNo, CheckNo,
    - Due (datetime - due date), EffectiveDate, EntryDate, EntryType
    - NO Balance column - use Amount field for outstanding balances
    - Join with Customer using CustomerNo = Customer.Number
    - EntryType indicates transaction type (invoice, payment, credit, etc.)
    
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
    
    RENTAL HISTORY (ben002.RentalHistory):
    - Id (bigint PK), SerialNo (nvarchar), Year (smallint), Month (smallint),
    - DaysRented (int), RentAmount (decimal), CreationTime (datetime2)
    - Tracks monthly rental activity for each equipment
    - To find active rentals: Look for records in current/recent months
    - Join with Equipment on SerialNo, then Customer on Equipment.CustomerNo
    
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
        
        Your role is to help users query this dealership ERP database using natural language.
        
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
        - "how many" questions = use count_equipment or count_rentals action, NOT list actions
        - "list" or "show me" = use list actions
        
        If user asks for net income, profit, or margin data, indicate in the intent that cost data is needed.
        If user asks "how many", always set query_type to "count" and use count_equipment or count_rentals.
        
        Always respond in JSON format with:
        {{
            "intent": "brief description of what user wants (be specific about sales vs profit vs income)",
            "query_action": "categorize the action: list_equipment|list_rentals|count_equipment|count_rentals|show_sales|show_inventory|service_status|parts_status|customer_info|financial_summary",
            "entity_type": "main entity: equipment|customer|invoice|parts|technician|rental",
            "entity_subtype": "if applicable: forklift|truck|part_type|etc",
            "tables": ["list", "of", "relevant", "tables"],
            "filters": {{
                "status": "if applicable: rented|available|sold|active|overdue",
                "time_period": "if applicable: current|last_month|last_week|specific_date",
                "customer": "if specific customer mentioned",
                "other": "any other filter conditions"
            }},
            "query_type": "aggregation|list|count|analysis",
            "use_rental_history": "true if query is about current/active rentals",
            "explanation": "human-readable explanation of the query",
            "suggested_visualization": "chart_type if applicable"
        }}
        
        Be helpful but accurate. If a query is ambiguous, ask for clarification.
        """

