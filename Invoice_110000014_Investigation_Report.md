# Investigation Report: Invoice 110000014 Assignment Issue

## Executive Summary

Invoice **110000014** was incorrectly assigned to the **House** account instead of **Kevin Buckman** in the Sales Commissions report. This investigation reveals that the issue stems from the **customer record lookup logic** used by the commission system, which relies on matching the invoice's billing information to customer records in the database, rather than examining salesman information directly on the invoice itself.

---

## How the Commission Assignment System Works

The Sales Commission report uses a **three-tier priority system** to determine which salesman should receive credit for each invoice. The system looks up the salesman by matching the invoice's billing information against customer records in the `ben002.Customer` table.

### Priority-Based Salesman Lookup

**Priority 1: BillTo Customer Number Match** (Highest Priority)
- Matches the invoice's `BillTo` field (customer account number) with the `Number` field in the Customer table
- If a match is found, the `Salesman1` field from that customer record is used

**Priority 2: Exact BillToName Match**
- If Priority 1 fails or returns no salesman, the system tries to match the invoice's `BillToName` field with the `Name` field in the Customer table (exact string match)
- Only considers records where `Salesman1` is not NULL

**Priority 3: First Word of Company Name Match**
- If Priority 1 and 2 fail, the system extracts the first word from the invoice's `BillToName` and matches it against the first word of customer names in the database
- Case-insensitive comparison
- Only considers records where `Salesman1` is not NULL

### House Account Filtering

After determining the salesman, the system applies a filter:

```sql
AND UPPER(sl.Salesman1) != 'HOUSE'
```

This means:
- Invoices assigned to "HOUSE" are **excluded** from individual salesman commission calculations
- These invoices appear in the **"Unassigned"** section of the report
- No commission is calculated for House invoices

---

## Why Invoice 110000014 Was Assigned to House

Based on the code analysis, invoice 110000014 was assigned to "HOUSE" because one of the following occurred:

### Most Likely Cause: Priority 1 Match
The invoice's `BillTo` customer number matched a customer record in the database where the `Salesman1` field is set to **"HOUSE"**.

**Example scenario:**
```
Invoice 110000014:
  BillTo: "12345"
  BillToName: "ACME Corporation"

Customer Table:
  Number: "12345"
  Name: "ACME Corporation"
  Salesman1: "HOUSE"  ← This is the problem
```

### Alternative Causes

**Priority 2 Match:**
The invoice's `BillToName` exactly matched a customer record with `Salesman1 = "HOUSE"`

**Priority 3 Match:**
The first word of the invoice's `BillToName` matched a customer record with `Salesman1 = "HOUSE"`

---

## Critical Finding: The System Does NOT Look at Invoice Fields

**Important:** The commission system does **NOT** examine:
- ❌ Salesman fields on the invoice itself
- ❌ Sales rep information in invoice line items
- ❌ Any text fields or notes containing salesman names
- ❌ Who actually made the sale according to the invoice

**It ONLY looks at:**
- ✅ The `Salesman1` field in the Customer table records that match the invoice's billing information

This means even if **Kevin Buckman's name appears on the invoice**, the system will assign it to "HOUSE" if the customer record has "HOUSE" in the `Salesman1` field.

---

## Root Cause Analysis

The invoice was assigned to House because of a **customer record data issue**, not an invoice issue. Specifically:

1. **Incorrect Customer Record**: The customer record associated with this invoice has `Salesman1 = "HOUSE"` in the database
2. **Billing Information Mismatch**: The invoice's `BillTo` number or `BillToName` is pointing to a customer record that is designated as a House account
3. **Multiple Customer Records**: There may be multiple customer records for the same customer, and the invoice is matching the wrong one (the one with "HOUSE" as the salesman)

---

## Solutions

### Option 1: Update the Customer Record (Recommended for Permanent Fix)
**Action:** Change the `Salesman1` field in the customer record from "HOUSE" to "Kevin Buckman"

**Steps:**
1. Identify the customer record being matched (use the diagnostic query provided)
2. Update the customer record in the database:
   ```sql
   UPDATE ben002.Customer
   SET Salesman1 = 'Kevin Buckman'
   WHERE Number = '[customer_number]'
   ```
3. Re-run the commission report

**Pros:**
- Permanent fix for this customer
- All future invoices for this customer will be correctly assigned
- No manual intervention needed for future months

**Cons:**
- Requires database access
- May affect other invoices for this customer (which may be desired)

---

### Option 2: Manual Reassignment via Commission Settings (Quick Fix)
**Action:** Use the commission settings reassignment feature in the frontend to manually assign this invoice to Kevin Buckman

**Steps:**
1. Open the Sales Commission Report
2. Click "Show Details"
3. Find invoice 110000014 in the "Unassigned" section
4. Use the reassignment dropdown to assign it to Kevin Buckman
5. Click "Save Changes"

**Pros:**
- Can be done through the UI, no database access needed
- Immediate fix for this specific invoice
- Doesn't affect other invoices

**Cons:**
- Only fixes this one invoice
- Must be repeated for future invoices if the customer record isn't fixed
- Manual process each month

---

### Option 3: Fix the Invoice's BillTo Information (If Incorrect)
**Action:** If the invoice's `BillTo` number is pointing to the wrong customer record, update the invoice

**Steps:**
1. Verify the correct customer record for this sale
2. Update the invoice's `BillTo` field to point to the correct customer number
3. Re-run the commission report

**Pros:**
- Fixes the invoice data accuracy
- Commission assignment will be correct

**Cons:**
- Requires database access to invoices
- May affect accounting records
- Should only be done if the BillTo is genuinely incorrect

---

## Diagnostic Query

I've created a comprehensive diagnostic SQL query that will show you exactly why invoice 110000014 was assigned to House. This query will reveal:

1. The invoice's billing information
2. Which customer record was matched at each priority level
3. The salesman assigned to each matching customer record
4. The final assignment result and which priority level was used

**File:** `invoice_110000014_diagnostic.sql`

Run this query against your database to see the exact data causing the issue.

---

## Recommendations

1. **Immediate Action:** Use Option 2 (Manual Reassignment) to quickly fix this invoice for the current month
2. **Long-term Fix:** Use Option 1 (Update Customer Record) to prevent this issue from recurring
3. **Verification:** Run the diagnostic query to confirm which customer record is causing the issue
4. **Process Review:** Consider reviewing all customer records with `Salesman1 = "HOUSE"` to ensure they are correctly classified
5. **Data Audit:** Check if there are multiple customer records for the same customer with different salesman assignments

---

## Technical Details

**Code Location:**
- File: `/reporting-backend/src/routes/department_reports.py`
- Function: `get_sales_commission_details()`
- Lines: 7088-7210 (Salesman lookup logic)
- Lines: 7326-7450 (Unassigned invoices logic)

**Key SQL Logic:**
```sql
-- Priority-based lookup with ROW_NUMBER to select highest priority match
WITH SalesmanLookup AS (
    SELECT InvoiceNo, Salesman1
    FROM (
        SELECT InvoiceNo, Salesman1,
               ROW_NUMBER() OVER (PARTITION BY InvoiceNo ORDER BY Priority) as rn
        FROM [priority matching logic]
    ) AS RankedMatches
    WHERE rn = 1
)
```

**House Exclusion Filter:**
```sql
WHERE UPPER(sl.Salesman1) != 'HOUSE'
```

**Unassigned Section Inclusion:**
```sql
WHERE (sl.Salesman1 IS NULL OR sl.Salesman1 = '' OR UPPER(sl.Salesman1) = 'HOUSE')
```

---

## Conclusion

Invoice 110000014 was assigned to House because the **customer record** associated with the invoice's billing information has "HOUSE" as the assigned salesman. The commission system correctly followed its logic, but the underlying customer data is incorrect or the invoice is billing to the wrong customer record.

The recommended solution is to:
1. **Immediately:** Manually reassign the invoice to Kevin Buckman using the UI
2. **Permanently:** Update the customer record to have Kevin Buckman as the salesman
3. **Verify:** Run the diagnostic query to confirm the exact customer record causing the issue

This will ensure Kevin Buckman receives proper credit for this sale and prevent the issue from recurring in future months.
