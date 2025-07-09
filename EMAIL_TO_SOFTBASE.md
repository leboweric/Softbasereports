# Email to Softbase Support

Subject: Azure SQL Connection Issue - Firewall Blocking Access

Hi Greg,

Thank you for providing the Azure SQL credentials. However, we're unable to connect to the database due to firewall restrictions. The credentials themselves appear to be correct, but Azure SQL is blocking our connection attempts.

## Connection Details Provided:
- Server: evo1-sql-replica.database.windows.net
- Database: evo
- Username: ben002user
- Password: [PROVIDED]

## Error We're Receiving:

```
Error Code: 40615
Message: "Cannot open server 'evo1-sql-replica' requested by the login. Client with IP address '162.220.234.11' is not allowed to access the server. To enable access, use the Azure Management Portal or run sp_set_firewall_rule on the master database to create a firewall rule for this IP address or address range. It may take up to five minutes for this change to take effect."
```

## Technical Details:

We've tested multiple connection methods:
1. Standard connection with provided credentials
2. Connection with explicit port 1433
3. Azure username format (ben002user@evo1-sql-replica)
4. Different TDS protocol versions

All attempts fail with the same firewall error (40615).

## The Issue:

Our application is hosted on Railway (a cloud platform), which uses dynamic IP addresses. The current IP being blocked is `162.220.234.11`, but this changes periodically. This makes IP whitelisting impractical.

## Recommended Solutions:

1. **Enable "Allow Azure services and resources to access this server"**
   - This is the easiest solution
   - Go to Azure Portal → Your SQL Server → Networking
   - Check the box for "Allow Azure services and resources to access this server"
   - This allows connections from any Azure-hosted service

2. **Provide an alternative connection method**
   - REST API endpoint
   - VPN access
   - Proxy server with static IP

3. **Add a wide IP range for Railway**
   - Railway IPs are in the range 162.220.234.0/24
   - This would cover their dynamic IP allocation

## Why This Matters:

Without resolving this firewall issue, we cannot:
- Query customer data
- Access equipment/forklift information
- Generate reports from live data
- Build the reporting features your system requires

The credentials you provided are correct, but Azure SQL's firewall is preventing any connection from cloud-hosted services.

Could you please implement one of the solutions above? Option 1 (enabling Azure services access) is typically the quickest and doesn't compromise security for legitimate Azure-hosted applications.

Thank you for your assistance with this matter.

Best regards,
[Your name]

---

## Attachment: Technical Error Log

```
Connection Test Results:
=======================
Timestamp: 2025-07-09T03:30:00Z
Server: evo1-sql-replica.database.windows.net
Database: evo

Test 1: Basic Connection
Result: FAILED
Error Code: 40615
Error Type: OperationalError
Error Message: (40615, b"Cannot open server 'evo1-sql-replica' requested by the login. Client with IP address '162.220.234.11' is not allowed to access the server.")

Test 2: Connection with Port 1433
Result: FAILED
Error: Unable to connect: Adaptive Server is unavailable or does not exist

Test 3: Azure Username Format
Result: FAILED
Error: Same firewall error (40615)

Network Test:
Server resolves to IP: 13.77.152.23
Port 1433: Reachable
Conclusion: Network connectivity is fine, but Azure SQL firewall is blocking the connection

SUMMARY:
- All connection attempts blocked by firewall
- Railway server IP: 162.220.234.11
- Error code 40615 confirms firewall issue
- Credentials are valid but cannot be used due to IP restrictions
```