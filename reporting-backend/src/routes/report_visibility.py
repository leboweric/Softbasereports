"""
Report Visibility Admin API
Allows super admins to toggle visibility of sidebar pages and sub-tabs per organization.
Settings are stored in the report_visibility PostgreSQL table.
"""
from flask import Blueprint, request, jsonify, g
from src.middleware.tenant_middleware import TenantMiddleware
from src.models.user import Organization, db
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

report_visibility_bp = Blueprint('report_visibility', __name__)


# ============================================================================
# MASTER REPORT REGISTRY
# Defines all pages and their sub-tabs that can be toggled
# ============================================================================
REPORT_REGISTRY = {
    'dashboard': {
        'label': 'Sales',
        'icon': 'LayoutDashboard',
        'tabs': {
            'sales': {'label': 'Sales'},
            'sales-breakdown': {'label': 'Sales Breakdown'},
            'customers': {'label': 'Customers'},
            'workorders': {'label': 'Work Orders'},
            'forecast': {'label': 'AI Sales Forecast'},
            'accuracy': {'label': 'AI Forecast Accuracy'},
        }
    },
    'parts': {
        'label': 'Parts',
        'icon': 'Package',
        'tabs': {
            'overview': {'label': 'Overview'},
            'work-orders': {'label': 'Work Orders'},
            'inventory-location': {'label': 'Inventory by Location'},
            'stock-alerts': {'label': 'Stock Alerts'},
            'forecast': {'label': 'Forecast'},
            'employee-performance': {'label': 'Parts Contest'},
            'velocity': {'label': 'Velocity'},
            'inventory-turns': {'label': 'Inventory Turns'},
        }
    },
    'service': {
        'label': 'Service',
        'icon': 'Wrench',
        'tabs': {
            'overview': {'label': 'Overview'},
            'work-orders': {'label': 'Work Orders'},
        }
    },
    'rental': {
        'label': 'Rental',
        'icon': 'Truck',
        'tabs': {
            'overview': {'label': 'Overview'},
            'availability': {'label': 'Availability'},
        }
    },
    'accounting': {
        'label': 'Accounting',
        'icon': 'DollarSign',
        'tabs': {
            'overview': {'label': 'Overview'},
            'ar': {'label': 'Accounts Receivable'},
            'ap': {'label': 'Accounts Payable'},
            'commissions': {'label': 'Sales Commissions'},
            'control': {'label': 'Control Numbers'},
            'inventory': {'label': 'Inventory'},
        }
    },
    'customer-churn': {
        'label': 'Customers',
        'icon': 'TrendingDown',
        'tabs': {
            'sales-by-customer': {'label': 'Sales by Customer'},
            'customer-churn': {'label': 'Customer Churn'},
        }
    },
    'financial': {
        'label': 'Finance',
        'icon': 'FileSpreadsheet',
        'tabs': {}
    },
    'knowledge-base': {
        'label': 'Knowledge Base',
        'icon': 'Book',
        'tabs': {}
    },
    'qbr': {
        'label': 'QBR',
        'icon': 'FileBarChart',
        'tabs': {}
    },
    'my-commissions': {
        'label': 'My Commissions',
        'icon': 'TrendingUp',
        'tabs': {}
    },
    'minitrac': {
        'label': 'Minitrac',
        'icon': 'Search',
        'tabs': {}
    },
    'database-explorer': {
        'label': 'Database Explorer',
        'icon': 'Database',
        'tabs': {}
    },
    'schema-explorer': {
        'label': 'Schema Explorer',
        'icon': 'FileSearch',
        'tabs': {}
    },
    'user-management': {
        'label': 'User Management',
        'icon': 'Users',
        'tabs': {}
    },
    'gl-mapping': {
        'label': 'GL Account Mapping',
        'icon': 'Settings2',
        'tabs': {}
    },
    'rep-comp-admin': {
        'label': 'Rep Comp Admin',
        'icon': 'Settings',
        'tabs': {}
    },
}


def get_visibility_settings(org_id):
    """
    Get all visibility settings for an organization.
    Returns a dict: { 'page_id': { 'visible': bool, 'tabs': { 'tab_id': bool } } }
    Items not in the table default to visible (True).
    """
    try:
        result = db.session.execute(
            text("SELECT page_id, tab_id, is_visible FROM report_visibility WHERE organization_id = :org_id"),
            {'org_id': org_id}
        )
        
        settings = {}
        for row in result:
            page_id = row[0]
            tab_id = row[1]
            is_visible = row[2]
            
            if page_id not in settings:
                settings[page_id] = {'visible': True, 'tabs': {}}
            
            if tab_id is None:
                # Page-level visibility
                settings[page_id]['visible'] = is_visible
            else:
                # Tab-level visibility
                settings[page_id]['tabs'][tab_id] = is_visible
        
        return settings
    except Exception as e:
        logger.error(f"Error getting visibility settings for org {org_id}: {e}")
        return {}


def is_page_visible(org_id, page_id):
    """Check if a page is visible for an organization. Defaults to True."""
    settings = get_visibility_settings(org_id)
    if page_id in settings:
        return settings[page_id]['visible']
    return True


def is_tab_visible(org_id, page_id, tab_id):
    """Check if a tab is visible for an organization. Defaults to True."""
    settings = get_visibility_settings(org_id)
    if page_id in settings:
        if not settings[page_id]['visible']:
            return False  # Page is hidden, all tabs are hidden
        if tab_id in settings[page_id].get('tabs', {}):
            return settings[page_id]['tabs'][tab_id]
    return True


# ============================================================================
# GET REPORT REGISTRY (master list of all pages/tabs)
# ============================================================================
@report_visibility_bp.route('/report-visibility/registry', methods=['GET'])
@TenantMiddleware.require_organization
@TenantMiddleware.require_super_admin
def get_registry():
    """Get the master report registry with all available pages and tabs."""
    return jsonify(REPORT_REGISTRY), 200


# ============================================================================
# GET VISIBILITY SETTINGS FOR AN ORGANIZATION
# ============================================================================
@report_visibility_bp.route('/report-visibility/<int:org_id>', methods=['GET'])
@TenantMiddleware.require_organization
@TenantMiddleware.require_super_admin
def get_org_visibility(org_id):
    """Get visibility settings for a specific organization."""
    try:
        org = Organization.query.get(org_id)
        if not org:
            return jsonify({'message': 'Organization not found'}), 404
        
        settings = get_visibility_settings(org_id)
        
        # Build full response with defaults
        response = {}
        for page_id, page_config in REPORT_REGISTRY.items():
            page_settings = settings.get(page_id, {})
            page_visible = page_settings.get('visible', True)
            
            tab_visibility = {}
            for tab_id in page_config.get('tabs', {}):
                tab_visible = page_settings.get('tabs', {}).get(tab_id, True)
                tab_visibility[tab_id] = tab_visible
            
            response[page_id] = {
                'visible': page_visible,
                'tabs': tab_visibility
            }
        
        return jsonify({
            'organization': {'id': org.id, 'name': org.name},
            'visibility': response
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting visibility for org {org_id}: {e}")
        return jsonify({'message': 'Failed to get visibility settings', 'error': str(e)}), 500


# ============================================================================
# UPDATE VISIBILITY SETTINGS FOR AN ORGANIZATION
# ============================================================================
@report_visibility_bp.route('/report-visibility/<int:org_id>', methods=['PUT'])
@TenantMiddleware.require_organization
@TenantMiddleware.require_super_admin
def update_org_visibility(org_id):
    """
    Update visibility settings for a specific organization.
    Body: { "page_id": { "visible": bool, "tabs": { "tab_id": bool } } }
    """
    try:
        org = Organization.query.get(org_id)
        if not org:
            return jsonify({'message': 'Organization not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        current_user = g.get('current_user')
        updated_by = current_user.email if current_user else 'unknown'
        
        for page_id, page_settings in data.items():
            if page_id not in REPORT_REGISTRY:
                continue
            
            page_visible = page_settings.get('visible', True)
            
            # Upsert page-level visibility
            db.session.execute(
                text("""
                    INSERT INTO report_visibility (organization_id, page_id, tab_id, is_visible, updated_at, updated_by)
                    VALUES (:org_id, :page_id, NULL, :visible, NOW(), :updated_by)
                    ON CONFLICT (organization_id, page_id, COALESCE(tab_id, '__page__')) 
                    DO UPDATE SET is_visible = :visible, updated_at = NOW(), updated_by = :updated_by
                """),
                {'org_id': org_id, 'page_id': page_id, 'visible': page_visible, 'updated_by': updated_by}
            )
            
            # Upsert tab-level visibility
            tabs = page_settings.get('tabs', {})
            for tab_id, tab_visible in tabs.items():
                if tab_id not in REPORT_REGISTRY[page_id].get('tabs', {}):
                    continue
                
                db.session.execute(
                    text("""
                        INSERT INTO report_visibility (organization_id, page_id, tab_id, is_visible, updated_at, updated_by)
                        VALUES (:org_id, :page_id, :tab_id, :visible, NOW(), :updated_by)
                        ON CONFLICT (organization_id, page_id, COALESCE(tab_id, '__page__')) 
                        DO UPDATE SET is_visible = :visible, updated_at = NOW(), updated_by = :updated_by
                    """),
                    {'org_id': org_id, 'page_id': page_id, 'tab_id': tab_id, 'visible': tab_visible, 'updated_by': updated_by}
                )
        
        db.session.commit()
        
        logger.info(f"Report visibility updated for org {org_id} by {updated_by}")
        
        return jsonify({'message': 'Visibility settings updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating visibility for org {org_id}: {e}")
        return jsonify({'message': 'Failed to update visibility settings', 'error': str(e)}), 500


# ============================================================================
# GET VISIBILITY FOR CURRENT USER'S ORG (used by frontend to filter UI)
# ============================================================================
@report_visibility_bp.route('/report-visibility/me', methods=['GET'])
@TenantMiddleware.require_organization
def get_my_visibility():
    """
    Get visibility settings for the current user's organization.
    This is called by the frontend to determine which pages/tabs to show.
    No super admin required - any authenticated user can see their own org's settings.
    """
    try:
        current_user = g.get('current_user')
        if not current_user or not current_user.organization_id:
            return jsonify({'message': 'User or organization not found'}), 401
        
        org_id = current_user.organization_id
        settings = get_visibility_settings(org_id)
        
        # Build response - only include items that are explicitly hidden
        # Frontend defaults everything to visible, so we only need to send hidden items
        hidden = {}
        for page_id, page_settings in settings.items():
            page_hidden = not page_settings.get('visible', True)
            hidden_tabs = {tab_id: False for tab_id, visible in page_settings.get('tabs', {}).items() if not visible}
            
            if page_hidden or hidden_tabs:
                hidden[page_id] = {
                    'visible': page_settings.get('visible', True),
                    'hidden_tabs': list(hidden_tabs.keys())
                }
        
        return jsonify({'hidden': hidden}), 200
        
    except Exception as e:
        logger.error(f"Error getting visibility for current user: {e}")
        return jsonify({'message': 'Failed to get visibility settings', 'error': str(e)}), 500
