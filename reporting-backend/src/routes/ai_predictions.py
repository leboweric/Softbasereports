from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import logging
import json
from src.services.azure_sql_service import AzureSQLService
from src.services.cache_service import cache_service
from src.services.openai_service import OpenAIQueryService
from src.config.openai_config import OpenAIConfig
from decimal import Decimal
import openai

logger = logging.getLogger(__name__)

ai_predictions_bp = Blueprint('ai_predictions', __name__)

class AIPredictionService:
    """Service for generating AI-powered predictions"""
    
    def __init__(self, db):
        self.db = db
        self.current_date = datetime.now()
        self.client = openai.OpenAI(api_key=OpenAIConfig.OPENAI_API_KEY)
    
    def _decimal_to_float(self, obj):
        """Convert Decimal objects to float for JSON serialization"""
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, dict):
            return {k: self._decimal_to_float(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._decimal_to_float(i) for i in obj]
        return obj
    
    def get_work_order_history(self):
        """Get historical work order data for predictions"""
        try:
            query = """
            WITH WOCosts AS (
                SELECT 
                    w.WONo,
                    w.OpenDate,
                    w.ClosedDate,
                    w.Type,
                    COALESCE(l.LaborCost, 0) + COALESCE(p.PartsCost, 0) + COALESCE(m.MiscCost, 0) as TotalCost
                FROM ben002.WO w
                LEFT JOIN (
                    SELECT WONo, SUM(Sell) as LaborCost
                    FROM ben002.WOLabor
                    GROUP BY WONo
                ) l ON w.WONo = l.WONo
                LEFT JOIN (
                    SELECT WONo, SUM(Sell) as PartsCost
                    FROM ben002.WOParts
                    GROUP BY WONo
                ) p ON w.WONo = p.WONo
                LEFT JOIN (
                    SELECT WONo, SUM(Sell) as MiscCost
                    FROM ben002.WOMisc
                    GROUP BY WONo
                ) m ON w.WONo = m.WONo
                WHERE w.OpenDate >= DATEADD(MONTH, -12, GETDATE())
                AND w.OpenDate < GETDATE()
            ),
            MonthlyData AS (
                SELECT 
                    YEAR(OpenDate) as year,
                    MONTH(OpenDate) as month,
                    COUNT(*) as count,
                    SUM(TotalCost) as total_value,
                    AVG(DATEDIFF(day, OpenDate, CASE WHEN ClosedDate IS NULL THEN GETDATE() ELSE ClosedDate END)) as avg_completion_days,
                    COUNT(CASE WHEN Type = 'S' THEN 1 END) as service_count,
                    COUNT(CASE WHEN Type = 'R' THEN 1 END) as rental_count,
                    COUNT(CASE WHEN Type = 'I' THEN 1 END) as internal_count
                FROM WOCosts
                GROUP BY YEAR(OpenDate), MONTH(OpenDate)
            )
            SELECT * FROM MonthlyData
            ORDER BY year, month
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Work order history query failed: {str(e)}")
            return []
    
    def get_customer_behavior_data(self):
        """Get customer behavior data for churn predictions"""
        try:
            query = """
            WITH CustomerMetrics AS (
                SELECT 
                    i.BillToName as CustName,
                    COUNT(DISTINCT MONTH(i.InvoiceDate)) as active_months,
                    SUM(i.GrandTotal) as total_revenue,
                    CONVERT(varchar, MAX(i.InvoiceDate), 120) as last_invoice_date,
                    DATEDIFF(day, MAX(i.InvoiceDate), GETDATE()) as days_since_last_invoice,
                    AVG(i.GrandTotal) as avg_invoice_value,
                    COUNT(i.InvoiceNo) as invoice_count
                FROM ben002.InvoiceReg i
                WHERE i.InvoiceDate >= DATEADD(MONTH, -12, GETDATE())
                AND i.BillToName NOT LIKE '%Wells Fargo%'
                AND i.BillToName NOT LIKE '%Maintenance contract%'
                AND i.BillToName NOT LIKE '%Rental Fleet%'
                GROUP BY i.BillToName
                HAVING SUM(i.GrandTotal) > 0
            )
            SELECT TOP 50 * FROM CustomerMetrics
            ORDER BY total_revenue DESC
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Customer behavior query failed: {str(e)}")
            return []
    
    def get_parts_demand_history(self):
        """Get parts demand history for forecasting"""
        try:
            query = """
            WITH PartsHistory AS (
                SELECT 
                    wp.PartNo,
                    p.Description,
                    YEAR(w.OpenDate) as year,
                    MONTH(w.OpenDate) as month,
                    SUM(wp.Qty) as quantity_used,
                    COUNT(DISTINCT w.WONo) as order_count,
                    AVG(p.OnHand) as avg_on_hand
                FROM ben002.WOParts wp
                JOIN ben002.WO w ON wp.WONo = w.WONo
                LEFT JOIN ben002.Parts p ON wp.PartNo = p.PartNo
                WHERE w.OpenDate >= DATEADD(MONTH, -12, GETDATE())
                AND wp.PartNo NOT LIKE '%OIL%'
                AND wp.PartNo NOT LIKE '%GREASE%'
                AND wp.PartNo NOT LIKE '%COOLANT%'
                GROUP BY wp.PartNo, p.Description, YEAR(w.OpenDate), MONTH(w.OpenDate)
            )
            SELECT TOP 20 
                PartNo,
                Description,
                SUM(quantity_used) as total_quantity,
                AVG(quantity_used) as avg_monthly_quantity,
                COUNT(DISTINCT CONCAT(year, '-', month)) as months_active
            FROM PartsHistory
            GROUP BY PartNo, Description
            ORDER BY total_quantity DESC
            """
            return self.db.execute_query(query)
        except Exception as e:
            logger.error(f"Parts demand history query failed: {str(e)}")
            return []
    
    def generate_work_order_prediction(self, historical_data):
        """Generate work order predictions using OpenAI"""
        try:
            # Convert data for AI prompt
            data_summary = json.dumps(self._decimal_to_float(historical_data), indent=2)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in equipment service analytics. Analyze historical work order data and provide predictions."
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Based on this monthly work order data from the past 12 months:
                        {data_summary}
                        
                        Please provide predictions for the next month in this exact JSON format:
                        {{
                            "expected_count": "150-175",
                            "value_low": 250000,
                            "value_high": 300000,
                            "confidence": 85,
                            "distribution": {{
                                "service": 120,
                                "rental": 40,
                                "internal": 10
                            }},
                            "factors": [
                                "Seasonal trends show increased activity",
                                "Growing backlog from previous months"
                            ],
                            "recommendations": "Consider adding temporary staff"
                        }}
                        """
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Try to parse the response as JSON
            content = response.choices[0].message.content
            # Remove any markdown code blocks if present
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"AI work order prediction failed: {str(e)}")
            return None
    
    def generate_customer_churn_prediction(self, customer_data):
        """Generate customer churn risk predictions"""
        try:
            # Convert data for AI prompt
            data_summary = json.dumps(self._decimal_to_float(customer_data[:20]), indent=2)  # Top 20 customers
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in customer behavior analysis. Identify customers at risk of churning."
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Based on this customer activity data from the past 12 months:
                        {data_summary}
                        
                        Please analyze and provide predictions in this exact JSON format:
                        {{
                            "at_risk_count": 5,
                            "overall_risk": 12,
                            "at_risk_customers": [
                                {{
                                    "name": "Customer Name",
                                    "risk_level": "High",
                                    "warning_signs": ["No orders in 60 days", "50% revenue decline"],
                                    "action": "Schedule account review meeting"
                                }}
                            ],
                            "patterns": ["Seasonal slowdown", "Industry consolidation"]
                        }}
                        """
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Try to parse the response as JSON
            content = response.choices[0].message.content
            # Remove any markdown code blocks if present
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"AI customer churn prediction failed: {str(e)}")
            return None
    
    def generate_parts_demand_forecast(self, parts_data):
        """Generate parts demand forecast"""
        try:
            # Convert data for AI prompt
            data_summary = json.dumps(self._decimal_to_float(parts_data), indent=2)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in inventory management and demand forecasting."
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Based on this parts usage data from the past 12 months:
                        {data_summary}
                        
                        Please provide predictions in this exact JSON format:
                        {{
                            "high_demand_count": 10,
                            "stockout_risk_count": 3,
                            "top_demand_parts": [
                                {{
                                    "part_no": "L12345",
                                    "description": "Part Description",
                                    "predicted_demand": 150,
                                    "recommended_reorder": 200,
                                    "confidence": 85
                                }}
                            ],
                            "stockout_risks": ["L12345", "L67890"],
                            "patterns": ["Summer peak approaching", "New equipment deployments"]
                        }}
                        """
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Try to parse the response as JSON
            content = response.choices[0].message.content
            # Remove any markdown code blocks if present
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"AI parts demand forecast failed: {str(e)}")
            return None

@ai_predictions_bp.route('/api/ai/predictions/work-orders', methods=['GET'])
@jwt_required()
def predict_work_orders():
    """Get AI predictions for work orders"""
    try:
        # Check cache first
        cached_result = cache_service.get('ai_wo_prediction')
        if cached_result and not request.args.get('refresh'):
            return jsonify(cached_result)
        
        db = AzureSQLService()
        ai_service = AIPredictionService(db)
        
        # Get historical data
        historical_data = ai_service.get_work_order_history()
        
        if not historical_data:
            return jsonify({'error': 'No historical data available'}), 400
        
        # Generate prediction
        prediction = ai_service.generate_work_order_prediction(historical_data)
        
        if not prediction:
            return jsonify({'error': 'Failed to generate prediction'}), 500
        
        result = {
            'prediction': prediction,
            'generated_at': datetime.now().isoformat(),
            'data_points': len(historical_data)
        }
        
        # Cache for 24 hours
        cache_service.set('ai_wo_prediction', result, 86400)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Work order prediction endpoint failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_predictions_bp.route('/api/ai/predictions/customer-churn', methods=['GET'])
@jwt_required()
def predict_customer_churn():
    """Get AI predictions for customer churn risk"""
    try:
        # Check cache first
        cached_result = cache_service.get('ai_churn_prediction')
        if cached_result and not request.args.get('refresh'):
            return jsonify(cached_result)
        
        db = AzureSQLService()
        ai_service = AIPredictionService(db)
        
        # Get customer data
        customer_data = ai_service.get_customer_behavior_data()
        
        if not customer_data:
            return jsonify({'error': 'No customer data available'}), 400
        
        # Generate prediction
        prediction = ai_service.generate_customer_churn_prediction(customer_data)
        
        if not prediction:
            return jsonify({'error': 'Failed to generate prediction'}), 500
        
        result = {
            'prediction': prediction,
            'generated_at': datetime.now().isoformat(),
            'customers_analyzed': len(customer_data)
        }
        
        # Cache for 24 hours
        cache_service.set('ai_churn_prediction', result, 86400)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Customer churn prediction endpoint failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@ai_predictions_bp.route('/api/ai/predictions/parts-demand', methods=['GET'])
@jwt_required()
def predict_parts_demand():
    """Get AI predictions for parts demand"""
    try:
        # Check cache first
        cached_result = cache_service.get('ai_parts_prediction')
        if cached_result and not request.args.get('refresh'):
            return jsonify(cached_result)
        
        db = AzureSQLService()
        ai_service = AIPredictionService(db)
        
        # Get parts data
        parts_data = ai_service.get_parts_demand_history()
        
        if not parts_data:
            return jsonify({'error': 'No parts data available'}), 400
        
        # Generate prediction
        prediction = ai_service.generate_parts_demand_forecast(parts_data)
        
        if not prediction:
            return jsonify({'error': 'Failed to generate prediction'}), 500
        
        result = {
            'prediction': prediction,
            'generated_at': datetime.now().isoformat(),
            'parts_analyzed': len(parts_data)
        }
        
        # Cache for 24 hours
        cache_service.set('ai_parts_prediction', result, 86400)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Parts demand prediction endpoint failed: {str(e)}")
        return jsonify({'error': str(e)}), 500