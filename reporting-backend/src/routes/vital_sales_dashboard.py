"""
VITAL Sales Dashboard Routes
Provides API endpoints for comprehensive sales metrics from HubSpot
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime, timedelta
from src.services.cache_service import cache_service

logger = logging.getLogger(__name__)

# Cache TTL for sales data (5 minutes)
CACHE_TTL = 300

vital_sales_dashboard_bp = Blueprint('vital_sales_dashboard', __name__)


def get_hubspot_service():
    """Get HubSpot service instance"""
    from src.services.hubspot_service import HubSpotService
    return HubSpotService()


def is_vital_user():
    """Check if current user belongs to VITAL organization"""
    try:
        from src.models.user import User, Organization
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.organization_id:
            return False
        
        org = Organization.query.get(user.organization_id)
        if org and org.name:
            return 'vital' in org.name.lower()
        return False
    except Exception as e:
        logger.error(f"Error checking VITAL user: {str(e)}")
        return False


# ==================== HEALTH CHECK ====================

@vital_sales_dashboard_bp.route('/api/vital/sales/health', methods=['GET'])
def sales_health_check():
    """Check HubSpot API connectivity"""
    try:
        service = get_hubspot_service()
        # Simple test - get pipelines
        pipelines = service.get_pipelines()
        return jsonify({
            "status": "healthy",
            "message": "HubSpot API connection successful",
            "pipelines_count": len(pipelines)
        })
    except ValueError as e:
        return jsonify({
            "status": "not_configured",
            "error": str(e)
        }), 503
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ==================== SALES DASHBOARD ENDPOINTS ====================

@vital_sales_dashboard_bp.route('/api/vital/sales/overview', methods=['GET'])
@jwt_required()
def get_sales_overview():
    """Get comprehensive sales overview with all key metrics"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        cache_key = "vital_sales_overview"
        
        # Check cache first
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                logger.info("Cache HIT for sales overview")
                return jsonify({
                    "success": True,
                    "data": cached,
                    "from_cache": True
                })
        
        logger.info("Cache MISS for sales overview, fetching from HubSpot")
        service = get_hubspot_service()
        
        # Get all deals with detailed properties
        all_deals = []
        after = None
        
        for _ in range(50):  # Up to 5000 deals
            params = {
                "limit": 100,
                "properties": "dealstage,amount,dealname,closedate,createdate,pipeline,hs_deal_stage_probability"
            }
            if after:
                params["after"] = after
            
            data = service._make_request("GET", "/crm/v3/objects/deals", params=params)
            all_deals.extend(data.get("results", []))
            
            paging = data.get("paging", {})
            if "next" in paging:
                after = paging["next"].get("after")
            else:
                break
        
        # Get pipelines for stage mapping
        pipelines = service.get_pipelines()
        stage_map = {}
        pipeline_map = {}
        for pipeline in pipelines:
            pipeline_map[pipeline["id"]] = pipeline["label"]
            for stage in pipeline.get("stages", []):
                stage_map[stage["id"]] = {
                    "label": stage["label"],
                    "pipeline": pipeline["label"],
                    "pipeline_id": pipeline["id"],
                    "is_closed": stage.get("metadata", {}).get("isClosed") == "true",
                    "is_won": "won" in stage["label"].lower(),
                    "probability": float(stage.get("metadata", {}).get("probability", 0))
                }
        
        # Calculate metrics
        today = datetime.now()
        current_year = today.year
        current_month = today.month
        
        total_deals = len(all_deals)
        total_value = 0
        pipeline_value = 0
        won_value_ytd = 0
        won_value_mtd = 0
        won_count = 0
        won_count_ytd = 0
        lost_count = 0
        deals_by_stage = {}
        deals_by_pipeline = {}
        monthly_won = {}
        sales_cycle_days = []
        
        for deal in all_deals:
            props = deal.get("properties", {})
            stage_id = props.get("dealstage")
            pipeline_id = props.get("pipeline")
            amount = float(props.get("amount") or 0)
            close_date_str = props.get("closedate")
            create_date_str = props.get("createdate")
            
            total_value += amount
            
            stage_info = stage_map.get(stage_id, {"label": "Unknown", "is_closed": False, "is_won": False})
            
            # Pipeline value (open deals)
            if not stage_info["is_closed"]:
                pipeline_value += amount
            
            # Won/Lost tracking
            if stage_info["is_won"]:
                won_count += 1
                if close_date_str:
                    try:
                        close_date = datetime.fromisoformat(close_date_str.replace('Z', '+00:00'))
                        # YTD
                        if close_date.year == current_year:
                            won_value_ytd += amount
                            won_count_ytd += 1
                            # MTD
                            if close_date.month == current_month:
                                won_value_mtd += amount
                        
                        # Monthly breakdown
                        month_key = close_date.strftime("%Y-%m")
                        if month_key not in monthly_won:
                            monthly_won[month_key] = {"count": 0, "value": 0}
                        monthly_won[month_key]["count"] += 1
                        monthly_won[month_key]["value"] += amount
                        
                        # Sales cycle calculation
                        if create_date_str:
                            create_date = datetime.fromisoformat(create_date_str.replace('Z', '+00:00'))
                            cycle_days = (close_date - create_date).days
                            if cycle_days >= 0:
                                sales_cycle_days.append(cycle_days)
                    except:
                        pass
            elif stage_info["is_closed"]:
                lost_count += 1
            
            # Aggregate by stage
            if stage_id not in deals_by_stage:
                deals_by_stage[stage_id] = {
                    "stage_name": stage_info["label"],
                    "pipeline": stage_info.get("pipeline", "Unknown"),
                    "is_closed": stage_info["is_closed"],
                    "is_won": stage_info["is_won"],
                    "count": 0,
                    "total_value": 0
                }
            deals_by_stage[stage_id]["count"] += 1
            deals_by_stage[stage_id]["total_value"] += amount
            
            # Aggregate by pipeline
            pipeline_name = pipeline_map.get(pipeline_id, "Unknown")
            if pipeline_name not in deals_by_pipeline:
                deals_by_pipeline[pipeline_name] = {"count": 0, "total_value": 0, "open_value": 0}
            deals_by_pipeline[pipeline_name]["count"] += 1
            deals_by_pipeline[pipeline_name]["total_value"] += amount
            if not stage_info["is_closed"]:
                deals_by_pipeline[pipeline_name]["open_value"] += amount
        
        # Calculate win rate and avg deal size
        win_rate = (won_count / (won_count + lost_count) * 100) if (won_count + lost_count) > 0 else 0
        avg_deal_size = won_value_ytd / won_count_ytd if won_count_ytd > 0 else 0
        avg_sales_cycle = sum(sales_cycle_days) / len(sales_cycle_days) if sales_cycle_days else 0
        
        # Sort monthly data
        monthly_trend = [
            {"month": k, "count": v["count"], "value": v["value"]}
            for k, v in sorted(monthly_won.items())
        ][-12:]  # Last 12 months
        
        result = {
            "summary": {
                "total_deals": total_deals,
                "total_value": round(total_value, 2),
                "pipeline_value": round(pipeline_value, 2),
                "won_value_ytd": round(won_value_ytd, 2),
                "won_value_mtd": round(won_value_mtd, 2),
                "won_count": won_count,
                "won_count_ytd": won_count_ytd,
                "lost_count": lost_count,
                "win_rate": round(win_rate, 1),
                "avg_deal_size": round(avg_deal_size, 2),
                "avg_sales_cycle_days": round(avg_sales_cycle, 1)
            },
            "deals_by_stage": list(deals_by_stage.values()),
            "deals_by_pipeline": [
                {"pipeline": k, **v} for k, v in deals_by_pipeline.items()
            ],
            "monthly_trend": monthly_trend,
            "pipelines": [{"id": p["id"], "name": p["label"]} for p in pipelines],
            "last_updated": datetime.now().isoformat()
        }
        
        # Cache the result
        cache_service.set(cache_key, result, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": result,
            "from_cache": False
        })
    except ValueError as e:
        logger.warning(f"Sales overview not available: {str(e)}")
        return jsonify({
            "success": True,
            "data": {
                "summary": {},
                "deals_by_stage": [],
                "deals_by_pipeline": [],
                "monthly_trend": [],
                "error": "HubSpot not configured"
            }
        })
    except Exception as e:
        logger.error(f"Sales overview error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_sales_dashboard_bp.route('/api/vital/sales/pipeline-funnel', methods=['GET'])
@jwt_required()
def get_pipeline_funnel():
    """Get pipeline funnel data for visualization"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        pipeline_id = request.args.get('pipeline_id')
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        cache_key = f"vital_sales_funnel:{pipeline_id or 'all'}"
        
        # Check cache first
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                return jsonify({"success": True, "data": cached, "from_cache": True})
        
        service = get_hubspot_service()
        
        # Get pipelines and stages
        pipelines = service.get_pipelines()
        
        # Filter to specific pipeline if requested
        if pipeline_id:
            pipelines = [p for p in pipelines if p["id"] == pipeline_id]
        
        funnel_data = []
        for pipeline in pipelines:
            stages = sorted(pipeline.get("stages", []), key=lambda x: x.get("displayOrder", 0))
            
            pipeline_funnel = {
                "pipeline_id": pipeline["id"],
                "pipeline_name": pipeline["label"],
                "stages": []
            }
            
            for stage in stages:
                # Get deals in this stage
                data = service._make_request("POST", "/crm/v3/objects/deals/search", json_data={
                    "limit": 0,
                    "filterGroups": [{
                        "filters": [
                            {"propertyName": "dealstage", "operator": "EQ", "value": stage["id"]},
                            {"propertyName": "pipeline", "operator": "EQ", "value": pipeline["id"]}
                        ]
                    }]
                })
                
                pipeline_funnel["stages"].append({
                    "stage_id": stage["id"],
                    "stage_name": stage["label"],
                    "order": stage.get("displayOrder", 0),
                    "count": data.get("total", 0),
                    "is_closed": stage.get("metadata", {}).get("isClosed") == "true"
                })
            
            funnel_data.append(pipeline_funnel)
        
        # Cache the result
        cache_service.set(cache_key, funnel_data, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": funnel_data,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"Pipeline funnel error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_sales_dashboard_bp.route('/api/vital/sales/top-deals', methods=['GET'])
@jwt_required()
def get_top_deals():
    """Get top deals by value"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        limit = request.args.get('limit', 10, type=int)
        status = request.args.get('status', 'open')  # open, won, all
        
        service = get_hubspot_service()
        
        # Get pipelines for stage mapping
        pipelines = service.get_pipelines()
        stage_map = {}
        for pipeline in pipelines:
            for stage in pipeline.get("stages", []):
                stage_map[stage["id"]] = {
                    "label": stage["label"],
                    "is_closed": stage.get("metadata", {}).get("isClosed") == "true",
                    "is_won": "won" in stage["label"].lower()
                }
        
        # Build filter based on status
        filter_groups = []
        if status == 'open':
            # Get all open stage IDs
            open_stages = [sid for sid, info in stage_map.items() if not info["is_closed"]]
            if open_stages:
                filter_groups = [{
                    "filters": [{"propertyName": "dealstage", "operator": "IN", "values": open_stages}]
                }]
        elif status == 'won':
            won_stages = [sid for sid, info in stage_map.items() if info["is_won"]]
            if won_stages:
                filter_groups = [{
                    "filters": [{"propertyName": "dealstage", "operator": "IN", "values": won_stages}]
                }]
        
        # Get deals sorted by amount
        search_body = {
            "limit": limit,
            "properties": ["dealname", "amount", "dealstage", "closedate", "hubspot_owner_id", "pipeline"],
            "sorts": [{"propertyName": "amount", "direction": "DESCENDING"}]
        }
        if filter_groups:
            search_body["filterGroups"] = filter_groups
        
        data = service._make_request("POST", "/crm/v3/objects/deals/search", json_data=search_body)
        
        deals = []
        for deal in data.get("results", []):
            props = deal.get("properties", {})
            stage_id = props.get("dealstage")
            stage_info = stage_map.get(stage_id, {"label": "Unknown"})
            
            deals.append({
                "id": deal["id"],
                "name": props.get("dealname", "Unnamed"),
                "amount": float(props.get("amount") or 0),
                "stage": stage_info["label"],
                "close_date": props.get("closedate"),
                "owner_id": props.get("hubspot_owner_id")
            })
        
        return jsonify({
            "success": True,
            "data": {
                "deals": deals,
                "total": data.get("total", 0)
            }
        })
    except Exception as e:
        logger.error(f"Top deals error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@vital_sales_dashboard_bp.route('/api/vital/sales/win-loss-analysis', methods=['GET'])
@jwt_required()
def get_win_loss_analysis():
    """Get win/loss analysis with trends"""
    try:
        if not is_vital_user():
            return jsonify({"error": "Access denied. VITAL users only."}), 403
        
        days = request.args.get('days', 365, type=int)
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        cache_key = f"vital_sales_win_loss:{days}"
        
        # Check cache first
        if not force_refresh:
            cached = cache_service.get(cache_key)
            if cached:
                return jsonify({"success": True, "data": cached, "from_cache": True})
        
        service = get_hubspot_service()
        
        # Get pipelines for stage mapping
        pipelines = service.get_pipelines()
        won_stages = []
        lost_stages = []
        for pipeline in pipelines:
            for stage in pipeline.get("stages", []):
                if stage.get("metadata", {}).get("isClosed") == "true":
                    if "won" in stage["label"].lower():
                        won_stages.append(stage["id"])
                    elif "lost" in stage["label"].lower():
                        lost_stages.append(stage["id"])
        
        # Get closed deals in the time period
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        all_closed_deals = []
        after = None
        
        for _ in range(20):
            search_body = {
                "limit": 100,
                "properties": ["dealstage", "amount", "closedate", "pipeline"],
                "filterGroups": [{
                    "filters": [
                        {"propertyName": "closedate", "operator": "GTE", "value": start_date}
                    ]
                }]
            }
            if after:
                search_body["after"] = after
            
            data = service._make_request("POST", "/crm/v3/objects/deals/search", json_data=search_body)
            all_closed_deals.extend(data.get("results", []))
            
            paging = data.get("paging", {})
            if "next" in paging:
                after = paging["next"].get("after")
            else:
                break
        
        # Analyze by month
        monthly_analysis = {}
        for deal in all_closed_deals:
            props = deal.get("properties", {})
            stage_id = props.get("dealstage")
            amount = float(props.get("amount") or 0)
            close_date_str = props.get("closedate")
            
            if not close_date_str:
                continue
            
            try:
                close_date = datetime.fromisoformat(close_date_str.replace('Z', '+00:00'))
                month_key = close_date.strftime("%Y-%m")
            except:
                continue
            
            if month_key not in monthly_analysis:
                monthly_analysis[month_key] = {
                    "won_count": 0, "won_value": 0,
                    "lost_count": 0, "lost_value": 0
                }
            
            if stage_id in won_stages:
                monthly_analysis[month_key]["won_count"] += 1
                monthly_analysis[month_key]["won_value"] += amount
            elif stage_id in lost_stages:
                monthly_analysis[month_key]["lost_count"] += 1
                monthly_analysis[month_key]["lost_value"] += amount
        
        # Calculate monthly win rates
        trend_data = []
        for month, data in sorted(monthly_analysis.items()):
            total = data["won_count"] + data["lost_count"]
            win_rate = (data["won_count"] / total * 100) if total > 0 else 0
            trend_data.append({
                "month": month,
                "won_count": data["won_count"],
                "won_value": round(data["won_value"], 2),
                "lost_count": data["lost_count"],
                "lost_value": round(data["lost_value"], 2),
                "win_rate": round(win_rate, 1)
            })
        
        # Overall totals
        total_won = sum(d["won_count"] for d in trend_data)
        total_lost = sum(d["lost_count"] for d in trend_data)
        total_won_value = sum(d["won_value"] for d in trend_data)
        total_lost_value = sum(d["lost_value"] for d in trend_data)
        overall_win_rate = (total_won / (total_won + total_lost) * 100) if (total_won + total_lost) > 0 else 0
        
        result = {
            "summary": {
                "total_won": total_won,
                "total_lost": total_lost,
                "total_won_value": round(total_won_value, 2),
                "total_lost_value": round(total_lost_value, 2),
                "overall_win_rate": round(overall_win_rate, 1)
            },
            "monthly_trend": trend_data,
            "period_days": days
        }
        
        # Cache the result
        cache_service.set(cache_key, result, CACHE_TTL)
        
        return jsonify({
            "success": True,
            "data": result,
            "from_cache": False
        })
    except Exception as e:
        logger.error(f"Win/loss analysis error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
