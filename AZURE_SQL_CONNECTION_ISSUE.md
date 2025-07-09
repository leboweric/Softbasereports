# Azure SQL Connection Issue

## Problem
The Softbase Azure SQL database is configured with IP-based firewall rules. This means only whitelisted IP addresses can connect, even with valid credentials.

## Current Status
- Credentials are valid: `ben002user` / `g6O8CE5mT83mDYOW`
- Server: `evo1-sql-replica.database.windows.net`
- Database: `evo`
- Error: `40615` - Client IP not allowed to access server

## Railway's Dynamic IPs
Railway uses dynamic IP addresses that change:
- Previous IP: `162.220.234.43`
- Current IP: `162.220.234.11`

## Solutions

### 1. Ask Softbase to Enable "Allow Azure Services"
This is the easiest solution. Ask Softbase to:
- Go to Azure Portal → SQL Server → Networking
- Enable "Allow Azure services and resources to access this server"
- This allows connections from any Azure-hosted service

### 2. Use a Static IP Proxy Service
Services like QuotaGuard or Fixie provide static IPs:
- Set up a proxy service with a static IP
- Give that IP to Softbase for whitelisting
- Route database connections through the proxy

### 3. Use Softbase's API Instead
If Softbase has a REST API for data access, use that instead of direct SQL

### 4. Local Development Only
Run queries locally and cache results, but this defeats the purpose of real-time data

## Recommended Response to Softbase

"Hi Greg,

We're trying to connect from our cloud hosting provider (Railway), but we're getting error 40615 - IP address not allowed. Railway uses dynamic IP addresses that change frequently.

Could you please either:
1. Enable 'Allow Azure services and resources to access this server' in the firewall settings, OR
2. Provide an alternative connection method that doesn't require IP whitelisting (like an API endpoint)?

This would allow us to connect from our cloud environment without needing to constantly update IP addresses.

Thanks!"