# Database Connectivity Guide
## Softbase Evolution vs. Legacy Platform

This guide explains how your BI Reporting tool connects to Softbase databases and what information you need from customers to establish connectivity.

---

## Table of Contents

1. [Current Setup: Softbase Evolution](#current-setup-softbase-evolution)
2. [How Evolution Connectivity Works](#how-evolution-connectivity-works)
3. [Softbase Legacy Platform Overview](#softbase-legacy-platform-overview)
4. [Legacy Database Architecture](#legacy-database-architecture)
5. [Information Needed from Customers](#information-needed-from-customers)
6. [Connection Testing Procedures](#connection-testing-procedures)
7. [Troubleshooting Guide](#troubleshooting-guide)

---

## Current Setup: Softbase Evolution

### What is Softbase Evolution?

**Softbase Evolution** is the modern, cloud-based version of Softbase's dealership management system. It uses **Microsoft Azure SQL Database** as its backend.

### Your Current Evolution Customer

**Customer:** ABC Forklift Dealership

**Database Details:**
- **Platform:** Azure SQL Database (Microsoft SQL Server in the cloud)
- **Server:** `evo1-sql-replica.database.windows.net`
- **Database Name:** `evo`
- **Username:** `ben002user`
- **Password:** `[encrypted and stored securely]`
- **Connection Type:** Read-only replica
- **Port:** 1433 (default SQL Server port)

### How the Replica Works

```
┌─────────────────────────────────────────────────┐
│  Softbase Evolution (Vendor-Managed)            │
│                                                  │
│  ┌──────────────────────────────────┐           │
│  │  Primary Azure SQL Database      │           │
│  │  (Production - Read/Write)       │           │
│  └──────────────┬───────────────────┘           │
│                 │                                │
│                 │ Continuous Replication         │
│                 ↓                                │
│  ┌──────────────────────────────────┐           │
│  │  Read-Only Replica               │←──────────┼─── Your BI Tool Connects Here
│  │  (For reporting/analytics)       │           │
│  └──────────────────────────────────┘           │
└─────────────────────────────────────────────────┘
```

**Key Points:**
- You connect to a **read-only replica**, not the production database
- The replica is continuously updated from the primary database (usually < 1 minute lag)
- You can only run `SELECT` queries (no `INSERT`, `UPDATE`, `DELETE`)
- Softbase manages the replica (backups, maintenance, scaling)
- Each customer has their own isolated database

---

## How Evolution Connectivity Works

### Connection String Format

Your Python code connects using this format:

```python
connection_string = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"Connection Timeout=30;"
)
```

### What Each Parameter Means

| Parameter | Example | Description |
|-----------|---------|-------------|
| `SERVER` | `evo1-sql-replica.database.windows.net` | Azure SQL server hostname |
| `DATABASE` | `evo` | Database name on that server |
| `UID` | `ben002user` | Username for authentication |
| `PWD` | `[password]` | Password for authentication |
| `Encrypt` | `yes` | Forces encrypted connection (required for Azure SQL) |
| `TrustServerCertificate` | `no` | Validates SSL certificate (security best practice) |
| `Connection Timeout` | `30` | Seconds to wait before timing out |

### Security Features

✅ **SSL/TLS Encryption** - All data is encrypted in transit  
✅ **Azure AD Integration** - Can use Azure Active Directory authentication  
✅ **Firewall Rules** - Azure SQL has IP-based firewall protection  
✅ **Read-Only Access** - Replica prevents accidental data modification  

---

## Softbase Legacy Platform Overview

### What is Softbase Legacy?

**Softbase Legacy** is the older, on-premises version of Softbase's dealership management system. It typically runs on **Microsoft SQL Server** installed on the customer's own servers.

### Key Differences from Evolution

| Feature | Evolution | Legacy |
|---------|-----------|--------|
| **Hosting** | Cloud (Azure) | On-premises (customer's server) |
| **Database** | Azure SQL Database | SQL Server 2008-2019 (varies) |
| **Access** | Internet (public endpoint) | VPN or direct connection required |
| **Management** | Softbase manages | Customer manages |
| **Replica** | Provided by Softbase | Customer must create |
| **Updates** | Automatic | Manual |
| **Version** | Always latest | Varies by customer |

---

## Legacy Database Architecture

### Typical Legacy Setup

```
┌─────────────────────────────────────────────────────────┐
│  Customer's Data Center / Server Room                   │
│                                                          │
│  ┌──────────────────────────────────────┐              │
│  │  SQL Server (Production)             │              │
│  │  - Version: 2008-2019                │              │
│  │  - Database: SoftbaseLegacy          │              │
│  │  - Read/Write access                 │              │
│  └──────────────┬───────────────────────┘              │
│                 │                                        │
│                 │ Replication (if configured)           │
│                 ↓                                        │
│  ┌──────────────────────────────────────┐              │
│  │  SQL Server (Replica - Optional)     │              │
│  │  - Read-only for reporting           │              │
│  └──────────────┬───────────────────────┘              │
│                 │                                        │
└─────────────────┼────────────────────────────────────────┘
                  │
                  │ VPN or Port Forwarding
                  ↓
         ┌────────────────────┐
         │  Your BI Tool      │
         │  (Cloud-hosted)    │
         └────────────────────┘
```

### Connection Challenges with Legacy

1. **Network Access**
   - Legacy databases are behind corporate firewalls
   - Requires VPN, port forwarding, or direct connection
   - May need IT department involvement

2. **Replica Setup**
   - Customer may not have a replica configured
   - They may need to set one up (or you connect to production)
   - Replication setup varies by SQL Server version

3. **Version Differences**
   - Different customers may have different SQL Server versions
   - Schema differences between versions
   - Some features may not be available in older versions

4. **Security Concerns**
   - Customers may be hesitant to expose their database to the internet
   - May require additional security measures (VPN, IP whitelisting)
   - Compliance requirements (HIPAA, PCI, etc.)

---

## Information Needed from Customers

### For Softbase Evolution Customers

When onboarding a new Evolution customer, you need:

#### 1. Database Connection Details

```
✅ Server Hostname: _________________________________
   Example: evo1-sql-replica.database.windows.net

✅ Database Name: ___________________________________
   Example: evo

✅ Username: ________________________________________
   Example: customer123user

✅ Password: ________________________________________
   (Will be encrypted before storage)

✅ Port: ____________________________________________
   Default: 1433 (usually not needed to specify)
```

#### 2. Verification Questions

- [ ] Is this a **read-only replica** or the production database?
- [ ] What is the expected data latency? (usually < 1 minute for replicas)
- [ ] Are there any IP restrictions or firewall rules we need to be aware of?
- [ ] What is the database timezone? (for date/time calculations)

#### 3. Test Query

Ask them to verify connectivity by running this test query:

```sql
SELECT 
    @@VERSION as SQLServerVersion,
    DB_NAME() as DatabaseName,
    GETDATE() as CurrentDateTime,
    COUNT(*) as InvoiceCount
FROM InvoiceReg
WHERE InvoiceDate >= DATEADD(month, -1, GETDATE());
```

This confirms:
- ✅ Connection works
- ✅ Correct database
- ✅ Has data
- ✅ InvoiceReg table exists

---

### For Softbase Legacy Customers

When onboarding a Legacy customer, you need **more information** because the setup is more complex.

#### 1. Database Connection Details

```
✅ Server Hostname/IP: ______________________________
   Example: 192.168.1.100 or sql.dealership.com

✅ Port: ____________________________________________
   Default: 1433 (may be different if customized)

✅ Database Name: ___________________________________
   Example: SoftbaseLegacy or Softbase

✅ SQL Server Version: ______________________________
   Example: SQL Server 2016 Standard

✅ Username: ________________________________________
   Example: reporting_user

✅ Password: ________________________________________
   (Will be encrypted before storage)

✅ Instance Name (if applicable): ___________________
   Example: SQLEXPRESS or MSSQLSERVER
```

#### 2. Network Access Method

Choose one:

- [ ] **Option A: Direct Connection**
  - Server is publicly accessible on the internet
  - Requires: Public IP address and port forwarding
  - Security: Firewall rules to whitelist your IP

- [ ] **Option B: VPN Connection**
  - You connect to their network via VPN
  - Requires: VPN credentials and configuration
  - Security: More secure, but more complex setup

- [ ] **Option C: SSH Tunnel**
  - Connect through an SSH jump host
  - Requires: SSH server access
  - Security: Good balance of security and simplicity

- [ ] **Option D: Azure Data Gateway**
  - Use Microsoft's on-premises data gateway
  - Requires: Gateway installation on their network
  - Security: Secure, but requires software installation

#### 3. Replica Configuration

- [ ] Do they have a **read-only replica** configured?
  - **Yes** → Great! Connect to the replica
  - **No** → Options:
    - Connect to production (not ideal, but sometimes necessary)
    - Help them set up a replica
    - Use SQL Server's built-in replication features

#### 4. Schema Information

Legacy databases may have **different schemas** than Evolution. You need to know:

```
✅ Invoice Table Name: ______________________________
   Evolution: InvoiceReg
   Legacy: Could be Invoice, InvoiceHeader, etc.

✅ Work Order Table Name: ___________________________
   Evolution: WO
   Legacy: Could be WorkOrder, WO, ServiceOrder, etc.

✅ Customer Table Name: _____________________________
   Evolution: Customer
   Legacy: Could be Customers, CustomerMaster, etc.

✅ Equipment Table Name: ____________________________
   Evolution: Equipment
   Legacy: Could be Equipment, Units, Machines, etc.
```

Ask them to provide:
- [ ] List of all table names
- [ ] Sample data from key tables
- [ ] Database schema diagram (if available)

#### 5. Security and Compliance

- [ ] Are there any compliance requirements? (HIPAA, PCI-DSS, SOC 2, etc.)
- [ ] Do they require a Business Associate Agreement (BAA)?
- [ ] Are there specific IP addresses we need to connect from?
- [ ] Do they require multi-factor authentication (MFA)?
- [ ] Are there specific hours when we can/cannot connect?

#### 6. IT Contact Information

```
✅ IT Contact Name: _________________________________

✅ IT Contact Email: ________________________________

✅ IT Contact Phone: ________________________________

✅ Preferred communication method: __________________
```

---

## Connection Testing Procedures

### Step 1: Test Basic Connectivity

Before storing credentials in your system, test the connection manually.

#### For Evolution (Azure SQL):

```python
import pyodbc

# Test connection
server = "evo1-sql-replica.database.windows.net"
database = "evo"
username = "testuser"
password = "testpassword"

connection_string = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
)

try:
    conn = pyodbc.connect(connection_string, timeout=10)
    print("✅ Connection successful!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()[0]
    print(f"SQL Server Version: {version}")
    
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
```

#### For Legacy (On-Premises SQL Server):

```python
import pyodbc

# Test connection
server = "192.168.1.100"  # or hostname
database = "SoftbaseLegacy"
username = "reporting_user"
password = "password123"

connection_string = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    f"Encrypt=no;"  # May need to be 'no' for older SQL Server versions
    f"TrustServerCertificate=yes;"  # May need to be 'yes' for self-signed certs
)

try:
    conn = pyodbc.connect(connection_string, timeout=10)
    print("✅ Connection successful!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()[0]
    print(f"SQL Server Version: {version}")
    
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
```

### Step 2: Test Data Access

Once connected, verify you can access the required tables:

```python
# Test queries
test_queries = [
    ("InvoiceReg", "SELECT COUNT(*) FROM InvoiceReg"),
    ("WO", "SELECT COUNT(*) FROM WO"),
    ("Customer", "SELECT COUNT(*) FROM Customer"),
    ("Equipment", "SELECT COUNT(*) FROM Equipment"),
]

for table_name, query in test_queries:
    try:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        print(f"✅ {table_name}: {count} records")
    except Exception as e:
        print(f"❌ {table_name}: {str(e)}")
```

### Step 3: Test Performance

Run a typical dashboard query to check performance:

```python
import time

query = """
SELECT 
    FORMAT(InvoiceDate, 'MMM') as month,
    SUM(LaborTaxable + LaborNonTax + PartsTaxable + PartsNonTax) as total_sales
FROM InvoiceReg
WHERE InvoiceDate >= DATEADD(month, -12, GETDATE())
GROUP BY FORMAT(InvoiceDate, 'MMM'), MONTH(InvoiceDate)
ORDER BY MONTH(InvoiceDate)
"""

start_time = time.time()
cursor.execute(query)
results = cursor.fetchall()
end_time = time.time()

print(f"Query returned {len(results)} rows in {end_time - start_time:.2f} seconds")
```

**Expected Performance:**
- Evolution (Azure SQL): 0.5-3 seconds
- Legacy (On-Premises): Varies widely (0.1-10+ seconds depending on hardware)

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: "Login failed for user"

**Cause:** Incorrect username or password

**Solutions:**
- Verify credentials with the customer
- Check for typos (especially in password)
- Ensure username includes domain if required (e.g., `DOMAIN\username`)

#### Issue 2: "Cannot open server"

**Cause:** Network connectivity issue

**Solutions:**
- Verify server hostname/IP is correct
- Check firewall rules (port 1433 must be open)
- Verify VPN is connected (for Legacy)
- Test with `telnet server 1433` or `nc -zv server 1433`

#### Issue 3: "SSL Security error"

**Cause:** SSL/TLS configuration mismatch

**Solutions:**
- For Azure SQL: Use `Encrypt=yes; TrustServerCertificate=no;`
- For Legacy: Try `Encrypt=no;` or `TrustServerCertificate=yes;`
- Verify SQL Server has valid SSL certificate

#### Issue 4: "Database does not exist"

**Cause:** Wrong database name

**Solutions:**
- Verify database name with customer
- Try connecting without specifying database, then list databases:
  ```sql
  SELECT name FROM sys.databases
  ```

#### Issue 5: "Invalid object name 'InvoiceReg'"

**Cause:** Table doesn't exist or has different name (common in Legacy)

**Solutions:**
- List all tables:
  ```sql
  SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'
  ```
- Ask customer for correct table names
- Check if tables are in a different schema (e.g., `dbo.InvoiceReg`)

#### Issue 6: "Connection timeout"

**Cause:** Slow network or overloaded server

**Solutions:**
- Increase connection timeout: `Connection Timeout=60;`
- Check network latency
- Verify server isn't overloaded
- For Legacy: Check if replica is available instead of production

---

## Summary Checklist

### For Evolution Customers

- [ ] Server hostname
- [ ] Database name
- [ ] Username
- [ ] Password
- [ ] Test connection
- [ ] Verify data access
- [ ] Check performance

### For Legacy Customers

- [ ] Server hostname/IP
- [ ] Port (if not 1433)
- [ ] Database name
- [ ] SQL Server version
- [ ] Username
- [ ] Password
- [ ] Network access method (direct, VPN, SSH, gateway)
- [ ] Replica availability
- [ ] Table names (may differ from Evolution)
- [ ] Test connection
- [ ] Verify data access
- [ ] Check performance
- [ ] IT contact information
- [ ] Security/compliance requirements

---

## Next Steps

Once you have this information from a Legacy customer:

1. **Test connectivity** using the procedures above
2. **Document any schema differences** (table names, column names)
3. **Implement LegacyService** in your platform abstraction layer
4. **Create schema mapping** (Evolution table names → Legacy table names)
5. **Test all reports** with Legacy data
6. **Onboard the customer** using your multi-tenant architecture

---

**Questions?** Feel free to ask for clarification on any of these topics!
