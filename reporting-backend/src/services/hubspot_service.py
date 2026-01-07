"""
HubSpot Integration Service for VITAL WorkLife
Provides methods to fetch and aggregate data from HubSpot CRM API
"""

import os
import requests
from datetime import datetime, timedelta
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class HubSpotService:
    """Service class for interacting with HubSpot CRM API"""
    
    BASE_URL = "https://api.hubapi.com"
    
    def __init__(self, access_token=None):
        """Initialize with access token from environment or parameter"""
        self.access_token = access_token or os.environ.get('VITAL_HUBSPOT_TOKEN')
        if not self.access_token:
            raise ValueError("HubSpot access token not configured")
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method, endpoint, params=None, json_data=None):
        """Make authenticated request to HubSpot API"""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"HubSpot API error: {str(e)}")
            raise
    
    # ==================== CONTACTS ====================
    
    def get_contacts_count(self):
        """Get total number of contacts"""
        data = self._make_request("POST", "/crm/v3/objects/contacts/search", json_data={"limit": 0})
        return data.get("total", 0)
    
    def get_contacts_by_lifecycle_stage(self):
        """Get contacts grouped by lifecycle stage"""
        stages = ["subscriber", "lead", "marketingqualifiedlead", "salesqualifiedlead", 
                  "opportunity", "customer", "evangelist", "other"]
        results = {}
        
        for stage in stages:
            data = self._make_request("POST", "/crm/v3/objects/contacts/search", json_data={
                "limit": 0,
                "filterGroups": [{
                    "filters": [{
                        "propertyName": "lifecyclestage",
                        "operator": "EQ",
                        "value": stage
                    }]
                }]
            })
            results[stage] = data.get("total", 0)
        
        return results
    
    def get_new_contacts_trend(self, days=90):
        """Get new contacts created over the past N days, grouped by month"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        data = self._make_request("POST", "/crm/v3/objects/contacts/search", json_data={
            "limit": 100,
            "properties": ["createdate"],
            "filterGroups": [{
                "filters": [{
                    "propertyName": "createdate",
                    "operator": "GTE",
                    "value": start_date.strftime("%Y-%m-%d")
                }]
            }],
            "sorts": [{"propertyName": "createdate", "direction": "DESCENDING"}]
        })
        
        return {
            "total_new": data.get("total", 0),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
    
    # ==================== COMPANIES ====================
    
    def get_companies_count(self):
        """Get total number of companies"""
        data = self._make_request("POST", "/crm/v3/objects/companies/search", json_data={"limit": 0})
        return data.get("total", 0)
    
    def get_recent_companies(self, limit=10):
        """Get recently created companies"""
        data = self._make_request("GET", "/crm/v3/objects/companies", params={
            "limit": limit,
            "properties": "name,domain,createdate,industry,numberofemployees"
        })
        return data.get("results", [])
    
    # ==================== DEALS ====================
    
    def get_deals_count(self):
        """Get total number of deals"""
        data = self._make_request("POST", "/crm/v3/objects/deals/search", json_data={"limit": 0})
        return data.get("total", 0)
    
    def get_pipelines(self):
        """Get all deal pipelines and their stages"""
        data = self._make_request("GET", "/crm/v3/pipelines/deals")
        return data.get("results", [])
    
    def get_deals_by_stage(self, pipeline_id=None):
        """Get deals grouped by stage with total values"""
        # First get pipelines to map stage IDs to names
        pipelines = self.get_pipelines()
        stage_map = {}
        for pipeline in pipelines:
            for stage in pipeline.get("stages", []):
                stage_map[stage["id"]] = {
                    "label": stage["label"],
                    "pipeline": pipeline["label"],
                    "is_closed": stage.get("metadata", {}).get("isClosed") == "true"
                }
        
        # Get all deals with stage and amount
        all_deals = []
        after = None
        
        for _ in range(10):  # Limit to 1000 deals for performance
            params = {
                "limit": 100,
                "properties": "dealstage,amount,dealname,closedate,pipeline"
            }
            if after:
                params["after"] = after
            
            data = self._make_request("GET", "/crm/v3/objects/deals", params=params)
            all_deals.extend(data.get("results", []))
            
            paging = data.get("paging", {})
            if "next" in paging:
                after = paging["next"].get("after")
            else:
                break
        
        # Aggregate by stage
        stage_totals = {}
        for deal in all_deals:
            props = deal.get("properties", {})
            stage_id = props.get("dealstage")
            amount = float(props.get("amount") or 0)
            
            if stage_id not in stage_totals:
                stage_info = stage_map.get(stage_id, {"label": "Unknown", "pipeline": "Unknown", "is_closed": False})
                stage_totals[stage_id] = {
                    "stage_name": stage_info["label"],
                    "pipeline": stage_info["pipeline"],
                    "is_closed": stage_info["is_closed"],
                    "count": 0,
                    "total_value": 0
                }
            
            stage_totals[stage_id]["count"] += 1
            stage_totals[stage_id]["total_value"] += amount
        
        return list(stage_totals.values())
    
    def get_deals_summary(self):
        """Get summary statistics for deals"""
        deals_by_stage = self.get_deals_by_stage()
        
        total_deals = sum(s["count"] for s in deals_by_stage)
        total_value = sum(s["total_value"] for s in deals_by_stage)
        
        open_deals = [s for s in deals_by_stage if not s["is_closed"]]
        closed_won = [s for s in deals_by_stage if s["is_closed"] and "won" in s["stage_name"].lower()]
        closed_lost = [s for s in deals_by_stage if s["is_closed"] and "lost" in s["stage_name"].lower()]
        
        pipeline_value = sum(s["total_value"] for s in open_deals)
        won_value = sum(s["total_value"] for s in closed_won)
        won_count = sum(s["count"] for s in closed_won)
        lost_count = sum(s["count"] for s in closed_lost)
        
        win_rate = (won_count / (won_count + lost_count) * 100) if (won_count + lost_count) > 0 else 0
        avg_deal_size = total_value / total_deals if total_deals > 0 else 0
        
        return {
            "total_deals": total_deals,
            "total_value": total_value,
            "pipeline_value": pipeline_value,
            "won_value": won_value,
            "won_count": won_count,
            "lost_count": lost_count,
            "win_rate": round(win_rate, 1),
            "avg_deal_size": round(avg_deal_size, 2),
            "deals_by_stage": deals_by_stage
        }
    
    # ==================== OWNERS ====================
    
    def get_owners(self):
        """Get all HubSpot owners/users"""
        data = self._make_request("GET", "/crm/v3/owners")
        return data.get("results", [])
    
    # ==================== DASHBOARD AGGREGATES ====================
    
    def get_dashboard_summary(self):
        """Get all key metrics for the dashboard in one call"""
        try:
            contacts_count = self.get_contacts_count()
            companies_count = self.get_companies_count()
            deals_summary = self.get_deals_summary()
            new_contacts = self.get_new_contacts_trend(days=30)
            
            return {
                "contacts": {
                    "total": contacts_count,
                    "new_last_30_days": new_contacts["total_new"]
                },
                "companies": {
                    "total": companies_count
                },
                "deals": deals_summary,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching dashboard summary: {str(e)}")
            raise
