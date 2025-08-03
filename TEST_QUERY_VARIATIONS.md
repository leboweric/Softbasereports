# Test Query Variations

## Forklift Rental Queries
All of these should map to the same SQL query:

1. "give me a list of all forklifts currently being rented"
2. "show me rented forklifts"
3. "which forklifts are on rent"
4. "list rental forklifts"
5. "what forklifts do we have out"
6. "I need to see our rental forklifts"
7. "can you pull up the lifts we have out?"
8. "forklift rentals list please"
9. "what fork trucks are customers using"
10. "display all forked vehicles currently deployed"

Expected structured response:
```json
{
    "query_action": "list_equipment",
    "entity_type": "equipment", 
    "entity_subtype": "forklift",
    "filters": {
        "status": "rented"
    },
    "use_rental_history": "true"
}
```

## Parts Inventory Queries
All of these should check for low inventory:

1. "what parts do we need to reorder"
2. "show me parts running low"
3. "which parts are below minimum stock"
4. "parts needing reorder"
5. "low inventory parts list"
6. "what's running out in parts"
7. "parts below reorder point"
8. "inventory shortages"

Expected structured response:
```json
{
    "query_action": "parts_status",
    "entity_type": "parts",
    "filters": {
        "status": "low"
    }
}
```

## Customer Rental Queries

1. "which customers have active rentals"
2. "show me who's renting equipment"
3. "list of customers with rentals"
4. "active rental customers"
5. "who has equipment out"

Expected structured response:
```json
{
    "query_action": "list_rentals",
    "entity_type": "rental",
    "filters": {
        "status": "active"
    },
    "use_rental_history": "true"
}
```

## Test Process

1. Deploy the updated code
2. Test each variation using `/api/ai/test-structured-prompt`
3. Verify structured response matches expected format
4. Test full query execution with `/api/ai/query`
5. Document any variations that fail