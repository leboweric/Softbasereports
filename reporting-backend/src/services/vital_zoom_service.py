"""
VITAL Zoom Service
Provides access to Zoom Phone and Meeting data for call center analytics
Uses Server-to-Server OAuth for authentication
"""

import os
import logging
import requests
import base64
from datetime import datetime, timedelta
from functools import lru_cache
import time

logger = logging.getLogger(__name__)


class VitalZoomService:
    """Service class for VITAL Zoom data access"""
    
    BASE_URL = "https://api.zoom.us/v2"
    TOKEN_URL = "https://zoom.us/oauth/token"
    
    def __init__(self, account_id=None, client_id=None, client_secret=None):
        """Initialize with Zoom credentials"""
        self.account_id = account_id or os.environ.get('VITAL_ZOOM_ACCOUNT_ID')
        self.client_id = client_id or os.environ.get('VITAL_ZOOM_CLIENT_ID')
        self.client_secret = client_secret or os.environ.get('VITAL_ZOOM_CLIENT_SECRET')
        
        if not all([self.account_id, self.client_id, self.client_secret]):
            raise ValueError("Zoom credentials not fully configured")
        
        self._access_token = None
        self._token_expires_at = 0
    
    def _get_access_token(self):
        """Get OAuth access token using Server-to-Server OAuth"""
        # Return cached token if still valid
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token
        
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "account_credentials",
            "account_id": self.account_id
        }
        
        response = requests.post(self.TOKEN_URL, headers=headers, data=data, timeout=30)
        
        if response.status_code == 200:
            token_data = response.json()
            self._access_token = token_data.get('access_token')
            self._token_expires_at = time.time() + token_data.get('expires_in', 3600)
            return self._access_token
        else:
            logger.error(f"Failed to get Zoom access token: {response.text}")
            raise Exception(f"Failed to get Zoom access token: {response.status_code}")
    
    def _make_request(self, endpoint, params=None):
        """Make authenticated request to Zoom API"""
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.BASE_URL}{endpoint}"
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Zoom API error: {response.status_code} - {response.text}")
            raise Exception(f"Zoom API error: {response.status_code}")
    
    def test_connection(self):
        """Test Zoom API connectivity"""
        try:
            token = self._get_access_token()
            return {"status": "connected", "message": "Zoom API connection successful"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    # ==================== USER ENDPOINTS ====================
    
    def get_users(self, page_size=100):
        """Get list of Zoom users"""
        try:
            data = self._make_request("/users", {"page_size": page_size})
            return {
                "total": data.get('total_records', 0),
                "users": data.get('users', [])
            }
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
            raise
    
    def get_phone_users(self, page_size=100):
        """Get list of Zoom Phone users"""
        try:
            data = self._make_request("/phone/users", {"page_size": page_size})
            return {
                "total": data.get('total_records', 0),
                "users": data.get('users', [])
            }
        except Exception as e:
            logger.error(f"Error getting phone users: {str(e)}")
            raise
    
    # ==================== CALL CENTER ENDPOINTS ====================
    
    def get_call_logs(self, days=30, page_size=100):
        """Get call history/logs"""
        try:
            today = datetime.now()
            from_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
            to_date = today.strftime("%Y-%m-%d")
            
            data = self._make_request("/phone/call_history", {
                "from": from_date,
                "to": to_date,
                "page_size": page_size
            })
            
            return {
                "total": data.get('total_records', 0),
                "from_date": from_date,
                "to_date": to_date,
                "call_logs": data.get('call_logs', [])
            }
        except Exception as e:
            logger.error(f"Error getting call logs: {str(e)}")
            raise
    
    def get_call_queues(self):
        """Get call queues"""
        try:
            data = self._make_request("/phone/call_queues")
            return {
                "total": data.get('total_records', 0),
                "call_queues": data.get('call_queues', [])
            }
        except Exception as e:
            logger.error(f"Error getting call queues: {str(e)}")
            raise
    
    def get_call_queue_members(self, queue_id):
        """Get members of a specific call queue"""
        try:
            data = self._make_request(f"/phone/call_queues/{queue_id}/members")
            return {
                "total": data.get('total_records', 0),
                "members": data.get('members', [])
            }
        except Exception as e:
            logger.error(f"Error getting call queue members: {str(e)}")
            raise
    
    # ==================== MEETING ENDPOINTS ====================
    
    def get_daily_report(self, year=None, month=None):
        """Get daily usage report"""
        try:
            if not year:
                year = datetime.now().year
            if not month:
                month = datetime.now().month
            
            data = self._make_request("/report/daily", {
                "year": year,
                "month": month
            })
            
            dates = data.get('dates', [])
            total_meetings = sum(d.get('meetings', 0) for d in dates)
            total_participants = sum(d.get('participants', 0) for d in dates)
            total_minutes = sum(d.get('meeting_minutes', 0) for d in dates)
            
            return {
                "year": data.get('year'),
                "month": data.get('month'),
                "total_meetings": total_meetings,
                "total_participants": total_participants,
                "total_minutes": total_minutes,
                "daily_data": dates
            }
        except Exception as e:
            logger.error(f"Error getting daily report: {str(e)}")
            raise
    
    def get_meetings_dashboard(self, days=30):
        """Get meetings from dashboard metrics"""
        try:
            today = datetime.now()
            from_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
            to_date = today.strftime("%Y-%m-%d")
            
            data = self._make_request("/metrics/meetings", {
                "from": from_date,
                "to": to_date,
                "type": "past",
                "page_size": 100
            })
            
            return {
                "total": data.get('total_records', 0),
                "from_date": from_date,
                "to_date": to_date,
                "meetings": data.get('meetings', [])
            }
        except Exception as e:
            logger.error(f"Error getting meetings dashboard: {str(e)}")
            raise
    
    # ==================== RECORDINGS/TRANSCRIPTS ====================
    
    def get_recordings(self, days=30):
        """Get account recordings with transcripts"""
        try:
            today = datetime.now()
            from_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
            to_date = today.strftime("%Y-%m-%d")
            
            data = self._make_request("/accounts/me/recordings", {
                "from": from_date,
                "to": to_date
            })
            
            return {
                "total": data.get('total_records', 0),
                "from_date": from_date,
                "to_date": to_date,
                "meetings": data.get('meetings', [])
            }
        except Exception as e:
            logger.error(f"Error getting recordings: {str(e)}")
            raise
    
    # ==================== DASHBOARD AGGREGATION ====================
    
    def get_call_center_dashboard(self):
        """Get comprehensive call center dashboard data"""
        try:
            dashboard_data = {
                "last_updated": datetime.now().isoformat()
            }
            
            # Get phone users
            try:
                phone_users = self.get_phone_users()
                dashboard_data["phone_users"] = {
                    "total": phone_users.get('total', 0),
                    "active": len([u for u in phone_users.get('users', []) if u.get('status') == 'activate'])
                }
            except Exception as e:
                logger.warning(f"Could not get phone users: {str(e)}")
                dashboard_data["phone_users"] = {"total": 0, "active": 0, "error": str(e)}
            
            # Get call logs
            try:
                call_logs = self.get_call_logs(days=30)
                calls = call_logs.get('call_logs', [])
                
                inbound = len([c for c in calls if c.get('direction') == 'inbound'])
                outbound = len([c for c in calls if c.get('direction') == 'outbound'])
                total_duration = sum(c.get('duration', 0) for c in calls)
                avg_duration = total_duration / len(calls) if calls else 0
                
                dashboard_data["call_stats"] = {
                    "total_calls": call_logs.get('total', 0),
                    "inbound": inbound,
                    "outbound": outbound,
                    "total_duration_seconds": total_duration,
                    "avg_duration_seconds": round(avg_duration, 1),
                    "period": f"{call_logs.get('from_date')} to {call_logs.get('to_date')}"
                }
            except Exception as e:
                logger.warning(f"Could not get call logs: {str(e)}")
                dashboard_data["call_stats"] = {"total_calls": 0, "error": str(e)}
            
            # Get call queues
            try:
                queues = self.get_call_queues()
                dashboard_data["call_queues"] = {
                    "total": queues.get('total', 0),
                    "queues": queues.get('call_queues', [])[:10]  # Limit to 10
                }
            except Exception as e:
                logger.warning(f"Could not get call queues: {str(e)}")
                dashboard_data["call_queues"] = {"total": 0, "queues": [], "error": str(e)}
            
            # Get daily meeting report
            try:
                daily_report = self.get_daily_report()
                dashboard_data["meeting_stats"] = {
                    "total_meetings": daily_report.get('total_meetings', 0),
                    "total_participants": daily_report.get('total_participants', 0),
                    "total_minutes": daily_report.get('total_minutes', 0),
                    "month": daily_report.get('month'),
                    "year": daily_report.get('year')
                }
            except Exception as e:
                logger.warning(f"Could not get daily report: {str(e)}")
                dashboard_data["meeting_stats"] = {"total_meetings": 0, "error": str(e)}
            
            # Get recent calls for table
            try:
                call_logs = self.get_call_logs(days=7, page_size=50)
                recent_calls = []
                for call in call_logs.get('call_logs', [])[:20]:
                    recent_calls.append({
                        "direction": call.get('direction', 'unknown'),
                        "duration": call.get('duration', 0),
                        "date_time": call.get('date_time', ''),
                        "caller_name": call.get('caller_name', 'Unknown'),
                        "caller_number": call.get('caller_number', 'N/A'),
                        "callee_name": call.get('callee_name', 'Unknown'),
                        "callee_number": call.get('callee_number', 'N/A'),
                        "result": call.get('result', 'unknown')
                    })
                dashboard_data["recent_calls"] = recent_calls
            except Exception as e:
                logger.warning(f"Could not get recent calls: {str(e)}")
                dashboard_data["recent_calls"] = []
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting call center dashboard: {str(e)}")
            raise
