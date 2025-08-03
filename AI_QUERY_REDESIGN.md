# AI Query System Redesign Proposal

## Current Problem

The system uses hardcoded pattern matching for every query variation:
- "give me a list of all forklifts currently being rented"
- "show me rented forklifts"
- "which forklifts are on rent"
- "list rental forklifts"
- "what forklifts do we have out"

All mean the same thing but require separate handlers!

## Root Cause

1. **OpenAI correctly identifies intent** but returns generic labels like:
   - `"intent": "list all rented forklifts"`
   - `"query_type": "list"`
   - `"tables": ["Equipment"]`

2. **generate_sql_from_analysis()** then does string matching on the intent instead of understanding it

## Proposed Solution

### Option 1: Enhanced OpenAI Prompt (Recommended)
Make OpenAI return a structured query plan with specific actions:

```json
{
  "intent": "list all rented forklifts",
  "query_type": "list",
  "action": "list_equipment",
  "filters": {
    "equipment_type": "forklift",
    "status": "rented"
  },
  "joins": ["Customer"],
  "fields": ["UnitNo", "SerialNo", "Make", "Model", "CustomerName"],
  "use_rental_history": true
}
```

### Option 2: Category-Based Handlers
Instead of exact string matching, use categories:

```python
# Rental queries
if query_analysis.get('action') == 'list_rentals':
    equipment_type = query_analysis['filters'].get('equipment_type', 'all')
    if equipment_type == 'forklift':
        # Generate forklift rental query
    else:
        # Generate general rental query
```

### Option 3: SQL Template System
Create reusable SQL templates:

```python
SQL_TEMPLATES = {
    'list_rentals': """
        SELECT {fields}
        FROM ben002.RentalHistory rh
        INNER JOIN ben002.Equipment e ON rh.SerialNo = e.SerialNo
        LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
        WHERE rh.Year = {year} AND rh.Month = {month}
        {equipment_filter}
        {customer_filter}
        ORDER BY {order_by}
    """
}
```

## Implementation Steps

1. **Update OpenAI prompt** to return structured actions
2. **Create action handlers** instead of string matchers
3. **Build SQL dynamically** from components
4. **Test with variations** to ensure flexibility

## Benefits

- **No more pattern matching** for every variation
- **LLM does what it's good at** - understanding intent
- **Maintainable** - add new capabilities without new patterns
- **Scalable** - handles unlimited phrasings

## Example Variations That Would Work

All of these would map to `action: "list_equipment", filters: {status: "rented", type: "forklift"}`:

- "give me a list of all forklifts currently being rented"
- "show me rented forklifts"
- "which forklifts are on rent"
- "I need to see our rental forklifts"
- "can you pull up the lifts we have out?"
- "forklift rentals list please"
- "what fork trucks are customers using"