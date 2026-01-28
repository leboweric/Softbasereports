"""
VITAL Teams Service
Provides access to Microsoft Teams data for High Fives recognition tracking
Uses Microsoft Graph API with Client Credentials OAuth flow
"""

import os
import logging
import requests
import re
from datetime import datetime, timedelta
from functools import lru_cache
import time

logger = logging.getLogger(__name__)


class VitalTeamsService:
    """Service class for VITAL Microsoft Teams data access"""
    
    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
    GRAPH_BETA_URL = "https://graph.microsoft.com/beta"
    TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    # Class-level cache for channel info (shared across instances)
    _channel_cache = None
    _channel_cache_time = 0
    CHANNEL_CACHE_TTL = 3600  # 1 hour
    
    # Class-level cache for user departments
    _user_cache = None
    _user_cache_time = 0
    USER_CACHE_TTL = 3600  # 1 hour
    
    def __init__(self, tenant_id=None, client_id=None, client_secret=None):
        """Initialize with Microsoft Azure AD credentials"""
        self.tenant_id = tenant_id or os.environ.get('VITAL_TEAMS_TENANT_ID')
        self.client_id = client_id or os.environ.get('VITAL_TEAMS_CLIENT_ID')
        self.client_secret = client_secret or os.environ.get('VITAL_TEAMS_CLIENT_SECRET')
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("Microsoft Teams credentials not fully configured")
        
        self._access_token = None
        self._token_expires_at = 0
    
    def _get_access_token(self):
        """Get OAuth access token using Client Credentials flow"""
        # Return cached token if still valid
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token
        
        token_url = self.TOKEN_URL.format(tenant_id=self.tenant_id)
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default"
        }
        
        response = requests.post(token_url, data=data, timeout=30)
        
        if response.status_code == 200:
            token_data = response.json()
            self._access_token = token_data.get('access_token')
            self._token_expires_at = time.time() + token_data.get('expires_in', 3600)
            return self._access_token
        else:
            logger.error(f"Failed to get Teams access token: {response.text}")
            raise Exception(f"Failed to get Teams access token: {response.status_code}")
    
    def _make_request(self, endpoint, params=None, use_beta=False):
        """Make authenticated request to Microsoft Graph API"""
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        base_url = self.GRAPH_BETA_URL if use_beta else self.GRAPH_BASE_URL
        url = f"{base_url}{endpoint}"
        
        response = requests.get(url, headers=headers, params=params, timeout=60)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Graph API error: {response.status_code} - {response.text}")
            raise Exception(f"Graph API error: {response.status_code}")
    
    def test_connection(self):
        """Test Microsoft Graph API connectivity"""
        try:
            token = self._get_access_token()
            return {"status": "connected", "message": "Microsoft Teams API connection successful"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    # ==================== TEAMS ENDPOINTS ====================
    
    def get_teams(self):
        """Get list of all teams in the organization"""
        try:
            data = self._make_request("/groups", {
                "$filter": "resourceProvisioningOptions/Any(x:x eq 'Team')",
                "$select": "id,displayName,description"
            })
            return {
                "total": len(data.get('value', [])),
                "teams": data.get('value', [])
            }
        except Exception as e:
            logger.error(f"Error getting teams: {str(e)}")
            raise
    
    def get_team_channels(self, team_id):
        """Get channels for a specific team"""
        try:
            data = self._make_request(f"/teams/{team_id}/channels")
            return {
                "total": len(data.get('value', [])),
                "channels": data.get('value', [])
            }
        except Exception as e:
            logger.error(f"Error getting channels: {str(e)}")
            raise
    
    def get_channel_messages(self, team_id, channel_id, top=50):
        """Get messages from a specific channel (requires beta API)"""
        try:
            data = self._make_request(
                f"/teams/{team_id}/channels/{channel_id}/messages",
                {"$top": top},
                use_beta=True
            )
            return {
                "total": len(data.get('value', [])),
                "messages": data.get('value', [])
            }
        except Exception as e:
            logger.error(f"Error getting channel messages: {str(e)}")
            raise
    
    def find_high_fives_channel(self, force_refresh=False):
        """Find the High Fives channel across all teams (with caching)"""
        # Check class-level cache first
        if not force_refresh and VitalTeamsService._channel_cache:
            if time.time() - VitalTeamsService._channel_cache_time < self.CHANNEL_CACHE_TTL:
                logger.info("Using cached High Fives channel info")
                return VitalTeamsService._channel_cache
        
        try:
            logger.info("Searching for High Fives channel...")
            teams = self.get_teams()
            
            for team in teams.get('teams', []):
                team_id = team.get('id')
                team_name = team.get('displayName')
                
                channels = self.get_team_channels(team_id)
                
                for channel in channels.get('channels', []):
                    channel_name = channel.get('displayName', '')
                    # Look for High Fives channel (may have emoji)
                    if 'high five' in channel_name.lower() or '🙏' in channel_name:
                        result = {
                            "found": True,
                            "team_id": team_id,
                            "team_name": team_name,
                            "channel_id": channel.get('id'),
                            "channel_name": channel_name
                        }
                        # Cache the result
                        VitalTeamsService._channel_cache = result
                        VitalTeamsService._channel_cache_time = time.time()
                        logger.info(f"Found High Fives channel: {channel_name} in team {team_name}")
                        return result
            
            return {"found": False, "message": "High Fives channel not found"}
        except Exception as e:
            logger.error(f"Error finding High Fives channel: {str(e)}")
            raise
    
    # ==================== RECOGNITION PARSING ====================
    
    def extract_mentions_from_message(self, message):
        """Extract @mentioned people from a Teams message"""
        mentions = []
        body = message.get('body', {})
        content = body.get('content', '')
        
        # Parse HTML content for <at> tags
        # Format: <at id="0">FirstName</at> <at id="1">LastName</at>
        at_pattern = r'<at[^>]*>([^<]+)</at>'
        matches = re.findall(at_pattern, content)
        
        if matches:
            # Combine consecutive name parts (first name + last name)
            combined_names = []
            i = 0
            while i < len(matches):
                name = matches[i].strip()
                # Check if next match could be a last name (no space in current, next exists)
                if i + 1 < len(matches) and ' ' not in name:
                    next_name = matches[i + 1].strip()
                    # If next is also a single word, combine them
                    if ' ' not in next_name:
                        combined_names.append(f"{name} {next_name}")
                        i += 2
                        continue
                combined_names.append(name)
                i += 1
            
            mentions = combined_names
        
        return mentions
    
    def parse_recognition_message(self, message):
        """Parse a Teams message to extract recognition data"""
        from_user = message.get('from', {}).get('user', {})
        giver_name = from_user.get('displayName', 'Unknown')
        
        mentions = self.extract_mentions_from_message(message)
        
        # Filter out the giver from mentions (they might mention themselves)
        receivers = [m for m in mentions if m.lower() != giver_name.lower()]
        
        created_at = message.get('createdDateTime', '')
        message_id = message.get('id', '')
        
        # Get plain text content
        body = message.get('body', {})
        content = body.get('content', '')
        # Strip HTML tags for plain text
        plain_text = re.sub(r'<[^>]+>', '', content).strip()
        
        return {
            "message_id": message_id,
            "giver_name": giver_name,
            "receivers": receivers,
            "message_preview": plain_text[:200] if plain_text else "",
            "created_at": created_at
        }
    
    def get_high_fives_recognitions(self, team_id=None, channel_id=None, days=90):
        """Get all recognition data from the High Fives channel"""
        try:
            # Find channel if not provided (uses cache)
            if not team_id or not channel_id:
                channel_info = self.find_high_fives_channel()
                if not channel_info.get('found'):
                    return {"error": "High Fives channel not found", "recognitions": [], "total": 0}
                team_id = channel_info['team_id']
                channel_id = channel_info['channel_id']
            
            # Get messages
            messages_data = self.get_channel_messages(team_id, channel_id, top=100)
            messages = messages_data.get('messages', [])
            
            # Parse recognitions
            recognitions = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for msg in messages:
                created_at_str = msg.get('createdDateTime', '')
                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        if created_at.replace(tzinfo=None) < cutoff_date:
                            continue
                    except:
                        pass
                
                recognition = self.parse_recognition_message(msg)
                
                # Only include messages that have receivers (actual recognitions)
                if recognition['receivers']:
                    recognitions.append(recognition)
            
            return {
                "total": len(recognitions),
                "team_id": team_id,
                "channel_id": channel_id,
                "recognitions": recognitions
            }
        except Exception as e:
            logger.error(f"Error getting High Fives recognitions: {str(e)}")
            raise
    
    # ==================== USER/DEPARTMENT LOOKUP ====================
    
    def get_user_by_name(self, display_name):
        """Look up a user by display name to get their department"""
        try:
            # Search for user by display name
            data = self._make_request("/users", {
                "$filter": f"displayName eq '{display_name}'",
                "$select": "id,displayName,department,jobTitle,mail"
            })
            users = data.get('value', [])
            if users:
                return users[0]
            return None
        except Exception as e:
            logger.warning(f"Could not look up user {display_name}: {str(e)}")
            return None
    
    def get_all_users_with_departments(self, force_refresh=False):
        """Get all users with their department information (with caching)"""
        # Check class-level cache first
        if not force_refresh and VitalTeamsService._user_cache:
            if time.time() - VitalTeamsService._user_cache_time < self.USER_CACHE_TTL:
                logger.info("Using cached user department info")
                return VitalTeamsService._user_cache
        
        try:
            logger.info("Fetching user department info from Graph API...")
            data = self._make_request("/users", {
                "$select": "id,displayName,department,jobTitle,mail",
                "$top": 999
            })
            users = data.get('value', [])
            # Create a lookup dict by display name
            result = {user.get('displayName', ''): user for user in users if user.get('displayName')}
            
            # Cache the result
            VitalTeamsService._user_cache = result
            VitalTeamsService._user_cache_time = time.time()
            
            return result
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
            return {}
    
    # ==================== RECOGNITION ANALYTICS ====================
    
    def get_recognition_summary(self, days=30, recognitions=None):
        """Get summary statistics for recognitions"""
        try:
            # Use provided recognitions or fetch them
            if recognitions is None:
                data = self.get_high_fives_recognitions(days=days)
                recognitions = data.get('recognitions', [])
            else:
                # Filter by days if recognitions provided
                cutoff_date = datetime.now() - timedelta(days=days)
                filtered = []
                for rec in recognitions:
                    created_at_str = rec.get('created_at', '')
                    if created_at_str:
                        try:
                            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            if created_at.replace(tzinfo=None) >= cutoff_date:
                                filtered.append(rec)
                        except:
                            filtered.append(rec)
                    else:
                        filtered.append(rec)
                recognitions = filtered
            
            # Count by giver
            giver_counts = {}
            receiver_counts = {}
            
            for rec in recognitions:
                giver = rec['giver_name']
                giver_counts[giver] = giver_counts.get(giver, 0) + 1
                
                for receiver in rec['receivers']:
                    receiver_counts[receiver] = receiver_counts.get(receiver, 0) + 1
            
            # Sort by count
            top_givers = sorted(giver_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            top_receivers = sorted(receiver_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "period_days": days,
                "total_recognitions": len(recognitions),
                "unique_givers": len(giver_counts),
                "unique_receivers": len(receiver_counts),
                "top_givers": [{"name": name, "count": count} for name, count in top_givers],
                "top_receivers": [{"name": name, "count": count} for name, count in top_receivers]
            }
        except Exception as e:
            logger.error(f"Error getting recognition summary: {str(e)}")
            raise
    
    def get_monthly_recognition_report(self, year=None, month=None, recognitions=None, user_lookup=None):
        """Get recognition report for a specific month with team and employee breakdowns"""
        try:
            if not year:
                year = datetime.now().year
            if not month:
                month = datetime.now().month
            
            # Use provided recognitions or fetch them
            if recognitions is None:
                data = self.get_high_fives_recognitions(days=90)
                recognitions = data.get('recognitions', [])
            
            # Use provided user lookup or fetch it
            if user_lookup is None:
                user_lookup = self.get_all_users_with_departments()
            
            # Filter to specific month
            month_recognitions = []
            for rec in recognitions:
                created_at_str = rec.get('created_at', '')
                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        if created_at.year == year and created_at.month == month:
                            month_recognitions.append(rec)
                    except:
                        pass
            
            # Count by giver and receiver
            giver_counts = {}
            receiver_counts = {}
            team_given = {}
            team_received = {}
            
            for rec in month_recognitions:
                giver = rec['giver_name']
                giver_counts[giver] = giver_counts.get(giver, 0) + 1
                
                # Get giver's department
                giver_info = user_lookup.get(giver, {})
                giver_dept = giver_info.get('department', 'Unknown')
                team_given[giver_dept] = team_given.get(giver_dept, 0) + 1
                
                for receiver in rec['receivers']:
                    receiver_counts[receiver] = receiver_counts.get(receiver, 0) + 1
                    
                    # Get receiver's department
                    receiver_info = user_lookup.get(receiver, {})
                    receiver_dept = receiver_info.get('department', 'Unknown')
                    team_received[receiver_dept] = team_received.get(receiver_dept, 0) + 1
            
            # Sort by count
            top_givers = sorted(giver_counts.items(), key=lambda x: x[1], reverse=True)
            top_receivers = sorted(receiver_counts.items(), key=lambda x: x[1], reverse=True)
            top_teams_given = sorted(team_given.items(), key=lambda x: x[1], reverse=True)
            top_teams_received = sorted(team_received.items(), key=lambda x: x[1], reverse=True)
            
            # Build giver details with departments
            giver_details = []
            for name, count in top_givers:
                user_info = user_lookup.get(name, {})
                giver_details.append({
                    "name": name,
                    "count": count,
                    "department": user_info.get('department', 'Unknown')
                })
            
            # Build receiver details with departments
            receiver_details = []
            for name, count in top_receivers:
                user_info = user_lookup.get(name, {})
                receiver_details.append({
                    "name": name,
                    "count": count,
                    "department": user_info.get('department', 'Unknown')
                })
            
            return {
                "year": year,
                "month": month,
                "total_recognitions": len(month_recognitions),
                "unique_givers": len(giver_counts),
                "unique_receivers": len(receiver_counts),
                "top_givers": giver_details[:10],
                "top_receivers": receiver_details[:10],
                "all_givers": giver_details,
                "all_receivers": receiver_details,
                "by_team_given": [{"team": team, "count": count} for team, count in top_teams_given],
                "by_team_received": [{"team": team, "count": count} for team, count in top_teams_received]
            }
        except Exception as e:
            logger.error(f"Error getting monthly recognition report: {str(e)}")
            raise
