from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.report_creator import ReportCreator
from src.middleware.tenant_middleware import TenantMiddleware
import json
from datetime import datetime

custom_reports_bp = Blueprint('custom_reports', __name__)
report_creator = ReportCreator()

@custom_reports_bp.route('/create', methods=['POST'])
@TenantMiddleware.require_organization
def create_custom_report():
    """Create a custom report from natural language description"""
    try:
        data = request.get_json()
        description = data.get('description', '')
        save_template = data.get('save_template', False)
        
        if not description:
            return jsonify({
                "success": False,
                "error": "Description is required"
            }), 400
        
        # Get organization ID from middleware
        organization_id = g.current_organization.id if hasattr(g, 'current_organization') else 1
        
        # Create the report
        result = report_creator.create_report_from_description(description, organization_id)
        
        if not result['success']:
            return jsonify(result), 400
        
        # Save as template if requested
        if save_template and result['success']:
            template_result = report_creator.save_custom_report(result['config'], organization_id)
            result['template_saved'] = template_result['success']
            result['template_id'] = template_result.get('template', {}).get('id')
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to create custom report"
        }), 500

@custom_reports_bp.route('/examples', methods=['GET'])
@TenantMiddleware.require_organization
def get_report_examples():
    """Get example report descriptions to help users"""
    examples = [
        {
            "category": "Work Orders",
            "examples": [
                "Show me all work orders that are complete but haven't been invoiced",
                "Create a report of all open work orders with their estimated completion dates",
                "List all work orders for ABC Manufacturing in the last 30 days",
                "Show work orders by technician with total hours and revenue"
            ]
        },
        {
            "category": "Parts & Inventory",
            "examples": [
                "Create a report that shows all Service and Parts WIP with a total $ value",
                "Show me all parts that are out of stock or below minimum levels",
                "List all Linde parts ordered in the last week",
                "Create an inventory report showing parts usage by customer"
            ]
        },
        {
            "category": "Customer Analysis",
            "examples": [
                "Show customers who haven't placed an order in the last 60 days",
                "Create a report of top 10 customers by revenue this year",
                "List all customers with overdue invoices",
                "Show customer equipment rental status and next service dates"
            ]
        },
        {
            "category": "Financial Reports",
            "examples": [
                "Create a revenue report by service type for this month",
                "Show all unpaid invoices older than 30 days",
                "List all warranty work performed this quarter",
                "Create a profitability report by customer"
            ]
        },
        {
            "category": "Equipment & Fleet",
            "examples": [
                "Give me the serial numbers of all forklifts that Polaris rents from us",
                "Show all equipment due for maintenance in the next 30 days",
                "Create a utilization report for rental fleet",
                "List all equipment by model and current location"
            ]
        }
    ]
    
    return jsonify({
        "success": True,
        "examples": examples
    })

@custom_reports_bp.route('/templates', methods=['GET'])
@TenantMiddleware.require_organization
def get_custom_templates():
    """Get saved custom report templates for the organization"""
    try:
        # In a real implementation, this would query the database
        # For now, return some sample templates
        organization_id = g.current_organization.id if hasattr(g, 'current_organization') else 1
        
        sample_templates = [
            {
                "id": "custom_20240115_143022",
                "name": "Complete Work Orders Not Invoiced",
                "description": "Show me all work orders that are complete but haven't been invoiced",
                "created_at": "2024-01-15T14:30:22Z",
                "last_used": "2024-01-20T09:15:00Z",
                "usage_count": 5
            },
            {
                "id": "custom_20240118_101545",
                "name": "Service and Parts WIP Report",
                "description": "Create a report that shows all Service and Parts WIP with a total $ value",
                "created_at": "2024-01-18T10:15:45Z",
                "last_used": "2024-01-22T16:30:00Z",
                "usage_count": 3
            },
            {
                "id": "custom_20240120_084512",
                "name": "Polaris Rental Equipment",
                "description": "Give me the serial numbers of all forklifts that Polaris rents from us",
                "created_at": "2024-01-20T08:45:12Z",
                "last_used": "2024-01-25T11:20:00Z",
                "usage_count": 2
            }
        ]
        
        return jsonify({
            "success": True,
            "templates": sample_templates
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@custom_reports_bp.route('/templates/<template_id>/run', methods=['POST'])
@TenantMiddleware.require_organization
def run_custom_template(template_id):
    """Run a saved custom report template"""
    try:
        # In a real implementation, this would load the template from database
        # For now, simulate running a saved template
        
        organization_id = g.current_organization.id if hasattr(g, 'current_organization') else 1
        
        # Mock template data based on template_id
        if "complete_work_orders" in template_id or "143022" in template_id:
            description = "Show me all work orders that are complete but haven't been invoiced"
        elif "service_parts_wip" in template_id or "101545" in template_id:
            description = "Create a report that shows all Service and Parts WIP with a total $ value"
        elif "polaris_rental" in template_id or "084512" in template_id:
            description = "Give me the serial numbers of all forklifts that Polaris rents from us"
        else:
            description = "Custom report template"
        
        # Create the report using the template description
        result = report_creator.create_report_from_description(description, organization_id)
        
        if result['success']:
            result['template_id'] = template_id
            result['run_at'] = datetime.utcnow().isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@custom_reports_bp.route('/suggestions', methods=['POST'])
@TenantMiddleware.require_organization
def get_report_suggestions():
    """Get AI-powered suggestions for report creation"""
    try:
        data = request.get_json()
        partial_description = data.get('description', '')
        
        if len(partial_description) < 3:
            return jsonify({
                "success": True,
                "suggestions": []
            })
        
        # Generate suggestions based on partial input
        suggestions = []
        
        # Work order related suggestions
        if any(word in partial_description.lower() for word in ['work', 'order', 'wo', 'service']):
            suggestions.extend([
                "Show me all work orders that are complete but haven't been invoiced",
                "Create a report of all open work orders with their estimated completion dates",
                "List work orders by technician with total hours and revenue",
                "Show work orders for a specific customer in the last 30 days"
            ])
        
        # Parts related suggestions
        if any(word in partial_description.lower() for word in ['part', 'inventory', 'stock', 'wip']):
            suggestions.extend([
                "Create a report that shows all Service and Parts WIP with a total $ value",
                "Show me all parts that are out of stock or below minimum levels",
                "List all parts ordered from a specific supplier",
                "Create an inventory report showing parts usage by customer"
            ])
        
        # Customer related suggestions
        if any(word in partial_description.lower() for word in ['customer', 'client', 'account']):
            suggestions.extend([
                "Show customers who haven't placed an order in the last 60 days",
                "Create a report of top 10 customers by revenue this year",
                "List all customers with overdue invoices",
                "Show customer equipment rental status and next service dates"
            ])
        
        # Equipment related suggestions
        if any(word in partial_description.lower() for word in ['equipment', 'forklift', 'serial', 'rental']):
            suggestions.extend([
                "Give me the serial numbers of all forklifts that Polaris rents from us",
                "Show all equipment due for maintenance in the next 30 days",
                "Create a utilization report for rental fleet",
                "List all equipment by model and current location"
            ])
        
        # Remove duplicates and limit to 5 suggestions
        unique_suggestions = list(dict.fromkeys(suggestions))[:5]
        
        return jsonify({
            "success": True,
            "suggestions": unique_suggestions
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@custom_reports_bp.route('/validate', methods=['POST'])
@TenantMiddleware.require_organization
def validate_report_description():
    """Validate a report description before creating the report"""
    try:
        data = request.get_json()
        description = data.get('description', '')
        
        if not description:
            return jsonify({
                "success": False,
                "error": "Description is required"
            }), 400
        
        # Basic validation
        validation_result = {
            "is_valid": True,
            "confidence": "high",
            "warnings": [],
            "suggestions": []
        }
        
        # Check for common issues
        if len(description.split()) < 5:
            validation_result["warnings"].append("Description might be too short for accurate report generation")
            validation_result["confidence"] = "medium"
        
        # Check for specific data sources
        has_data_source = any(word in description.lower() for word in [
            'work order', 'invoice', 'part', 'customer', 'equipment', 'forklift'
        ])
        
        if not has_data_source:
            validation_result["warnings"].append("Consider specifying what type of data you want (work orders, parts, customers, etc.)")
            validation_result["suggestions"].append("Try: 'Show me work orders...' or 'Create a parts report...'")
        
        # Check for time periods
        has_time_period = any(word in description.lower() for word in [
            'last week', 'this month', 'yesterday', 'today', 'year', 'quarter'
        ])
        
        if not has_time_period:
            validation_result["suggestions"].append("Consider adding a time period like 'in the last 30 days' or 'this month'")
        
        return jsonify({
            "success": True,
            "validation": validation_result
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

