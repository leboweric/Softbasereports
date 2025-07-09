# Natural Language Report Creation Feature

## Overview

Your forklift reporting system now includes a powerful **Natural Language Report Creation** feature that allows users to create custom reports using plain English descriptions. This revolutionary feature eliminates the need for complex query builders or technical knowledge.

## How It Works

### 1. AI-Powered Query Processing
- Users describe their reporting needs in natural language
- OpenAI processes the description and converts it to structured database queries
- The system automatically identifies relevant data sources and relationships
- Smart date parsing handles relative dates like "last week", "this month", etc.

### 2. Example Queries You Can Use

**Work Orders & Service:**
- "Show me all work orders that are complete but haven't been invoiced"
- "Create a report of all Service and Parts WIP with total $ value"
- "List all open work orders for Linde equipment from last month"
- "Show me completed repairs that took longer than 5 days"

**Inventory & Parts:**
- "Which Linde parts were we not able to fill last week?"
- "Show me all parts with low inventory levels"
- "Create a report of parts ordered but not yet received"
- "List all parts sales by manufacturer for this quarter"

**Customer & Rental Management:**
- "Give me the serial numbers of all forklifts that Polaris rents from us"
- "Show me all customers with overdue invoices"
- "Create a report of rental equipment due for maintenance"
- "List all new customers acquired this year"

**Financial Reports:**
- "Show me total revenue by customer for the last 6 months"
- "Create a profit analysis report for parts sales"
- "List all unpaid invoices older than 30 days"
- "Show me monthly sales trends for the past year"

### 3. Key Features

**Smart Query Understanding:**
- Recognizes forklift industry terminology (WIP, parts, service, rentals)
- Understands equipment brands (Linde, Toyota, Crown, etc.)
- Processes time ranges naturally ("last week", "this quarter", "YTD")
- Handles complex relationships between work orders, invoices, and customers

**Report Templates:**
- Save frequently used queries as templates
- Share templates across your organization
- Modify existing templates with natural language
- Quick access to common report types

**Export Options:**
- Generate reports in CSV, Excel, or PDF format
- Email reports automatically
- Schedule recurring reports
- Custom formatting and branding

### 4. Technical Implementation

**Backend Services:**
- `ReportCreator` service processes natural language descriptions
- OpenAI integration for intelligent query parsing
- Softbase Evolution API integration for data retrieval
- Multi-tenant support with organization-based data isolation

**Frontend Components:**
- `ReportCreator` component with intuitive interface
- Real-time query validation and suggestions
- Template management and sharing
- Export and scheduling options

### 5. Configuration Requirements

**OpenAI API Setup:**
1. Obtain an OpenAI API key from https://platform.openai.com/
2. Set the `OPENAI_API_KEY` environment variable in your backend
3. Configure the OpenAI model preferences in `src/config/openai_config.py`

**Softbase Evolution Integration:**
1. Configure your Softbase Evolution API credentials
2. Update the `SoftbaseService` with your API endpoints
3. Map your database schema to the report generator

### 6. Usage Instructions

1. **Navigate to Report Creator:**
   - Click on "Report Creator" in the main navigation menu

2. **Describe Your Report:**
   - Type your request in plain English in the text area
   - Be specific about what data you want to see
   - Include time ranges and filtering criteria

3. **Create the Report:**
   - Click "Create Report" to generate the report immediately
   - Or click "Create & Save Template" to save for future use

4. **Review and Export:**
   - Review the generated report data
   - Export in your preferred format (CSV, Excel, PDF)
   - Schedule recurring reports if needed

### 7. Best Practices

**Writing Effective Queries:**
- Be specific about the data you want
- Include relevant time ranges
- Mention specific equipment types or brands when relevant
- Use industry terminology for better recognition

**Examples of Good Queries:**
✅ "Show me all Toyota forklift work orders completed last month with labor costs over $500"
✅ "Create a report of Linde parts inventory levels below reorder point"
✅ "List all rental customers with equipment due for annual maintenance"

**Examples to Improve:**
❌ "Show me stuff" (too vague)
❌ "Reports" (no specific request)
❌ "Everything from last year" (too broad)

### 8. Troubleshooting

**Common Issues:**
- **Authentication errors:** Ensure you're logged in and have proper permissions
- **No results:** Check if your query criteria are too restrictive
- **Slow responses:** Complex queries may take longer to process
- **API errors:** Verify OpenAI API key and Softbase Evolution connectivity

**Getting Help:**
- Use the "Examples" tab for query inspiration
- Check saved templates for similar reports
- Contact your system administrator for technical issues

## Benefits

### Cost Savings
- Eliminates need for technical report writers
- Reduces time spent creating custom reports
- Minimizes training requirements for new users

### Efficiency Gains
- Instant report generation from natural language
- No need to learn complex query languages
- Reusable templates for common reports

### Business Intelligence
- Easy access to critical business data
- Quick answers to operational questions
- Data-driven decision making capabilities

This feature transforms your reporting system from a traditional tool into an intelligent assistant that understands your business needs and delivers exactly the information you're looking for.

