"""
QuickBooks Online Integration Service for VITAL WorkLife
Provides OAuth2 authentication and financial data retrieval
"""

import os
import requests
import base64
import json
from datetime import datetime, timedelta
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)


class QuickBooksService:
    """Service class for interacting with QuickBooks Online API"""
    
    # QuickBooks OAuth endpoints
    AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
    TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    REVOKE_URL = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
    
    # QuickBooks API base URL (production)
    API_BASE_URL = "https://quickbooks.api.intuit.com/v3/company"
    
    # Scopes needed for financial reports
    SCOPES = "com.intuit.quickbooks.accounting"
    
    def __init__(self, client_id=None, client_secret=None, redirect_uri=None):
        """Initialize with OAuth credentials"""
        self.client_id = client_id or os.environ.get('QB_CLIENT_ID')
        self.client_secret = client_secret or os.environ.get('QB_CLIENT_SECRET')
        self.redirect_uri = redirect_uri or os.environ.get('QB_REDIRECT_URI', 
            'https://softbasereports-production.up.railway.app/api/vital/quickbooks/callback')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("QuickBooks client_id and client_secret are required")
    
    # ==================== OAuth Methods ====================
    
    def get_authorization_url(self, state=None):
        """Generate the OAuth authorization URL"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'scope': self.SCOPES,
            'redirect_uri': self.redirect_uri,
            'state': state or 'vital_qb_auth'
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"
    
    def exchange_code_for_tokens(self, authorization_code):
        """Exchange authorization code for access and refresh tokens"""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri
        }
        
        response = requests.post(self.TOKEN_URL, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        
        tokens = response.json()
        return {
            'access_token': tokens.get('access_token'),
            'refresh_token': tokens.get('refresh_token'),
            'expires_in': tokens.get('expires_in'),
            'token_type': tokens.get('token_type'),
            'expires_at': (datetime.now() + timedelta(seconds=tokens.get('expires_in', 3600))).isoformat()
        }
    
    def refresh_access_token(self, refresh_token):
        """Refresh the access token using refresh token"""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        response = requests.post(self.TOKEN_URL, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        
        tokens = response.json()
        return {
            'access_token': tokens.get('access_token'),
            'refresh_token': tokens.get('refresh_token'),
            'expires_in': tokens.get('expires_in'),
            'expires_at': (datetime.now() + timedelta(seconds=tokens.get('expires_in', 3600))).isoformat()
        }
    
    def revoke_token(self, token):
        """Revoke an access or refresh token"""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        data = {'token': token}
        
        response = requests.post(self.REVOKE_URL, headers=headers, json=data, timeout=30)
        return response.status_code == 200
    
    # ==================== API Request Methods ====================
    
    def _make_api_request(self, access_token, realm_id, endpoint, params=None):
        """Make authenticated request to QuickBooks API"""
        url = f"{self.API_BASE_URL}/{realm_id}/{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=60)
        response.raise_for_status()
        return response.json()
    
    def _make_report_request(self, access_token, realm_id, report_name, params=None):
        """Make request for a QuickBooks report"""
        endpoint = f"reports/{report_name}"
        return self._make_api_request(access_token, realm_id, endpoint, params)
    
    # ==================== Company Info ====================
    
    def get_company_info(self, access_token, realm_id):
        """Get company information"""
        try:
            data = self._make_api_request(access_token, realm_id, f"companyinfo/{realm_id}")
            return data.get('CompanyInfo', {})
        except Exception as e:
            logger.error(f"Error getting company info: {str(e)}")
            raise
    
    # ==================== Financial Reports ====================
    
    def get_profit_and_loss(self, access_token, realm_id, start_date=None, end_date=None):
        """Get Profit and Loss report"""
        try:
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now().replace(day=1)).strftime('%Y-%m-%d')
            
            params = {
                'start_date': start_date,
                'end_date': end_date,
                'minorversion': '65'
            }
            
            data = self._make_report_request(access_token, realm_id, 'ProfitAndLoss', params)
            return self._parse_report(data)
        except Exception as e:
            logger.error(f"Error getting P&L report: {str(e)}")
            raise
    
    def get_balance_sheet(self, access_token, realm_id, as_of_date=None):
        """Get Balance Sheet report"""
        try:
            if not as_of_date:
                as_of_date = datetime.now().strftime('%Y-%m-%d')
            
            params = {
                'date_macro': 'Today',
                'minorversion': '65'
            }
            
            data = self._make_report_request(access_token, realm_id, 'BalanceSheet', params)
            return self._parse_report(data)
        except Exception as e:
            logger.error(f"Error getting Balance Sheet: {str(e)}")
            raise
    
    def get_cash_flow(self, access_token, realm_id, start_date=None, end_date=None):
        """Get Cash Flow Statement"""
        try:
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            
            params = {
                'start_date': start_date,
                'end_date': end_date,
                'minorversion': '65'
            }
            
            data = self._make_report_request(access_token, realm_id, 'CashFlow', params)
            return self._parse_report(data)
        except Exception as e:
            logger.error(f"Error getting Cash Flow: {str(e)}")
            raise
    
    def get_ar_aging_summary(self, access_token, realm_id):
        """Get Accounts Receivable Aging Summary"""
        try:
            params = {
                'minorversion': '65'
            }
            
            data = self._make_report_request(access_token, realm_id, 'AgedReceivables', params)
            return self._parse_aging_report(data)
        except Exception as e:
            logger.error(f"Error getting AR Aging: {str(e)}")
            raise
    
    def get_ap_aging_summary(self, access_token, realm_id):
        """Get Accounts Payable Aging Summary"""
        try:
            params = {
                'minorversion': '65'
            }
            
            data = self._make_report_request(access_token, realm_id, 'AgedPayables', params)
            return self._parse_aging_report(data)
        except Exception as e:
            logger.error(f"Error getting AP Aging: {str(e)}")
            raise
    
    # ==================== Queries ====================
    
    def get_invoices(self, access_token, realm_id, limit=100):
        """Get recent invoices"""
        try:
            query = f"SELECT * FROM Invoice ORDERBY TxnDate DESC MAXRESULTS {limit}"
            params = {'query': query, 'minorversion': '65'}
            data = self._make_api_request(access_token, realm_id, 'query', params)
            return data.get('QueryResponse', {}).get('Invoice', [])
        except Exception as e:
            logger.error(f"Error getting invoices: {str(e)}")
            raise
    
    def get_customers(self, access_token, realm_id, limit=100):
        """Get customers"""
        try:
            query = f"SELECT * FROM Customer MAXRESULTS {limit}"
            params = {'query': query, 'minorversion': '65'}
            data = self._make_api_request(access_token, realm_id, 'query', params)
            return data.get('QueryResponse', {}).get('Customer', [])
        except Exception as e:
            logger.error(f"Error getting customers: {str(e)}")
            raise
    
    def get_accounts(self, access_token, realm_id):
        """Get chart of accounts"""
        try:
            query = "SELECT * FROM Account"
            params = {'query': query, 'minorversion': '65'}
            data = self._make_api_request(access_token, realm_id, 'query', params)
            return data.get('QueryResponse', {}).get('Account', [])
        except Exception as e:
            logger.error(f"Error getting accounts: {str(e)}")
            raise
    
    # ==================== Dashboard Aggregates ====================
    
    def get_financial_dashboard(self, access_token, realm_id):
        """Get aggregated financial data for dashboard"""
        try:
            # Get current month P&L
            now = datetime.now()
            month_start = now.replace(day=1).strftime('%Y-%m-%d')
            month_end = now.strftime('%Y-%m-%d')
            
            # Get YTD P&L
            year_start = now.replace(month=1, day=1).strftime('%Y-%m-%d')
            
            # Fetch reports
            current_month_pl = self.get_profit_and_loss(access_token, realm_id, month_start, month_end)
            ytd_pl = self.get_profit_and_loss(access_token, realm_id, year_start, month_end)
            ar_aging = self.get_ar_aging_summary(access_token, realm_id)
            
            # Get company info
            company_info = self.get_company_info(access_token, realm_id)
            
            return {
                'company': {
                    'name': company_info.get('CompanyName'),
                    'legal_name': company_info.get('LegalName'),
                    'fiscal_year_start': company_info.get('FiscalYearStartMonth')
                },
                'current_month': current_month_pl,
                'year_to_date': ytd_pl,
                'ar_aging': ar_aging,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting financial dashboard: {str(e)}")
            raise
    
    # ==================== Report Parsing Helpers ====================
    
    def _parse_report(self, report_data):
        """Parse QuickBooks report into simplified structure"""
        if not report_data:
            return {}
        
        header = report_data.get('Header', {})
        rows = report_data.get('Rows', {}).get('Row', [])
        
        result = {
            'report_name': header.get('ReportName'),
            'start_period': header.get('StartPeriod'),
            'end_period': header.get('EndPeriod'),
            'currency': header.get('Currency'),
            'sections': []
        }
        
        for row in rows:
            section = self._parse_row(row)
            if section:
                result['sections'].append(section)
        
        return result
    
    def _parse_row(self, row, depth=0):
        """Recursively parse report rows"""
        if not row:
            return None
        
        row_type = row.get('type')
        
        if row_type == 'Section':
            header = row.get('Header', {})
            summary = row.get('Summary', {})
            
            section = {
                'type': 'section',
                'name': self._get_col_value(header.get('ColData', [])),
                'total': self._get_col_value(summary.get('ColData', []), 1),
                'rows': []
            }
            
            for sub_row in row.get('Rows', {}).get('Row', []):
                parsed = self._parse_row(sub_row, depth + 1)
                if parsed:
                    section['rows'].append(parsed)
            
            return section
        
        elif row_type == 'Data':
            col_data = row.get('ColData', [])
            return {
                'type': 'data',
                'name': self._get_col_value(col_data, 0),
                'value': self._get_col_value(col_data, 1)
            }
        
        return None
    
    def _get_col_value(self, col_data, index=0):
        """Safely get column value"""
        if col_data and len(col_data) > index:
            return col_data[index].get('value', '')
        return ''
    
    def _parse_aging_report(self, report_data):
        """Parse aging report into buckets"""
        if not report_data:
            return {}
        
        header = report_data.get('Header', {})
        columns = report_data.get('Columns', {}).get('Column', [])
        rows = report_data.get('Rows', {}).get('Row', [])
        
        # Get column headers (aging buckets)
        buckets = [col.get('ColTitle', '') for col in columns]
        
        result = {
            'report_name': header.get('ReportName'),
            'as_of_date': header.get('EndPeriod'),
            'buckets': buckets,
            'customers': [],
            'totals': {}
        }
        
        for row in rows:
            if row.get('type') == 'Data':
                col_data = row.get('ColData', [])
                customer_data = {
                    'name': self._get_col_value(col_data, 0)
                }
                for i, bucket in enumerate(buckets[1:], 1):
                    customer_data[bucket] = self._get_col_value(col_data, i)
                result['customers'].append(customer_data)
            
            elif row.get('type') == 'Section' and row.get('group') == 'GrandTotal':
                summary = row.get('Summary', {}).get('ColData', [])
                for i, bucket in enumerate(buckets[1:], 1):
                    if i < len(summary):
                        result['totals'][bucket] = summary[i].get('value', '0')
        
        return result
