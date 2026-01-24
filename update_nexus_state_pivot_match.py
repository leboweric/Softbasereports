#!/usr/bin/env python3
"""
Update nexus_state values in finance_clients to match Excel PIVOT Nexus State sheet.

The Excel pivot shows specific nexus state assignments that differ from the raw data:
1. WAFCO/ATEK Companies: IA → MN (moved to MN in pivot)
2. Southwestern Healthcare, Inc: IN → blank (moved to blank in pivot)
3. Lawrence Memorial Hospital: KS → blank (moved to blank in pivot)
4. MSV VEMA: VA → blank (moved to blank in pivot)

These changes make the app match the Excel PIVOT exactly.
"""

import psycopg2
import os

# Database connection
DATABASE_URL = "postgresql://postgres:ZINQrdsRJEQeYMsLEPazJJbyztwWSMiY@nozomi.proxy.rlwy.net:45435/railway"

def update_nexus_states():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Updates to match Excel PIVOT
    updates = [
        # WAFCO/ATEK Companies: IA → MN
        ("MN", "WAFCO/ATEK Companies", 6),
        # Southwestern Healthcare, Inc: IN → blank
        (None, "Southwestern Healthcare, Inc", 6),
        # Lawrence Memorial Hospital: KS → blank
        (None, "Lawrence Memorial Hospital", 6),
        # MSV VEMA: VA → blank
        (None, "MSV VEMA", 6),
    ]
    
    print("=== Updating nexus_state values to match Excel PIVOT ===\n")
    
    for new_state, client_name, org_id in updates:
        # Get current value
        cursor.execute("""
            SELECT id, billing_name, nexus_state 
            FROM finance_clients 
            WHERE billing_name = %s AND org_id = %s
        """, (client_name, org_id))
        
        result = cursor.fetchone()
        if result:
            client_id, name, old_state = result
            state_display = new_state if new_state else "(blank)"
            old_display = old_state if old_state else "(blank)"
            
            # Update
            cursor.execute("""
                UPDATE finance_clients 
                SET nexus_state = %s 
                WHERE id = %s
            """, (new_state, client_id))
            
            print(f"✓ {name}: {old_display} → {state_display}")
        else:
            print(f"✗ Client not found: {client_name}")
    
    conn.commit()
    
    # Verify the changes
    print("\n=== Verification ===")
    
    # Check totals by nexus state with tier filter
    cursor.execute("""
        SELECT 
            COALESCE(fc.nexus_state, '(blank)') as nexus_state,
            SUM(fmb.revenue_cash) as total_revenue
        FROM finance_clients fc
        JOIN finance_monthly_billing fmb ON fc.id = fmb.client_id
        WHERE fc.org_id = 6 
        AND fmb.billing_year = 2026
        AND fc.tier IN ('A', 'B', 'C', 'D')
        GROUP BY COALESCE(fc.nexus_state, '(blank)')
        ORDER BY total_revenue DESC
    """)
    
    print("\nNexus State Revenue (Cash, Valid Tier only):")
    total = 0
    for row in cursor.fetchall():
        state, revenue = row
        total += float(revenue) if revenue else 0
        print(f"  {state}: ${float(revenue):,.2f}" if revenue else f"  {state}: $0.00")
    
    print(f"\n  Grand Total: ${total:,.2f}")
    print(f"  Excel PIVOT Total: $11,350,684.41")
    
    cursor.close()
    conn.close()
    
    print("\n=== Update Complete ===")

if __name__ == "__main__":
    update_nexus_states()
