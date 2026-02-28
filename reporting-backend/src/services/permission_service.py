"""
Permission checking service for dynamic RBAC
"""
from src.config.rbac_config import ROLE_PERMISSIONS, RESOURCES, NAVIGATION_CONFIG

class PermissionService:
    @staticmethod
    def _get_valid_roles(user):
        """Get only roles that belong to the user's organization (prevents cross-org privilege escalation)"""
        if not user or not user.roles:
            return []
        return [role for role in user.roles 
                if role.organization_id == user.organization_id or role.organization_id is None]
    
    @staticmethod
    def user_has_permission(user, resource, action='view'):
        """Check if user has permission for resource/action"""
        if not user or not user.roles:
            return False
        
        for role in PermissionService._get_valid_roles(user):
            role_perms = ROLE_PERMISSIONS.get(role.name, {})
            
            # Check if role has access to this resource
            if resource in role_perms.get('resources', []):
                # Check if role can perform this action
                if action in role_perms.get('actions', []):
                    return True
        
        return False
    
    @staticmethod
    def get_user_resources(user):
        """Get all resources user has access to"""
        if not user or not user.roles:
            return []
        
        resources = set()
        for role in PermissionService._get_valid_roles(user):
            role_perms = ROLE_PERMISSIONS.get(role.name, {})
            resources.update(role_perms.get('resources', []))
        
        return list(resources)
    
    @staticmethod
    def get_user_actions(user, resource):
        """Get all actions user can perform on a resource"""
        if not user or not user.roles:
            return []
        
        actions = set()
        for role in PermissionService._get_valid_roles(user):
            role_perms = ROLE_PERMISSIONS.get(role.name, {})
            
            # Check if role has access to this resource
            if resource in role_perms.get('resources', []):
                # Add all actions this role can perform
                actions.update(role_perms.get('actions', []))
        
        return list(actions)
    
    @staticmethod
    def _get_visibility_settings(org_id):
        """Get report visibility settings from PostgreSQL for an organization."""
        try:
            from src.models.user import db
            from sqlalchemy import text
            result = db.session.execute(
                text("SELECT page_id, tab_id, is_visible FROM report_visibility WHERE organization_id = :org_id"),
                {'org_id': org_id}
            )
            settings = {}
            for row in result:
                page_id, tab_id, is_visible = row[0], row[1], row[2]
                if page_id not in settings:
                    settings[page_id] = {'visible': True, 'tabs': {}}
                if tab_id is None:
                    settings[page_id]['visible'] = is_visible
                else:
                    settings[page_id]['tabs'][tab_id] = is_visible
            return settings
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error loading visibility settings for org {org_id}: {e}")
            return {}

    @staticmethod
    def get_user_navigation(user):
        """Get navigation items user can access"""
        # Fallback for users without RBAC roles (legacy support)
        if not user or not user.roles:
            # Check legacy role field for admin users
            if user and user.role == 'admin':
                # Return all navigation items for legacy admin users
                return {nav_id: nav_config for nav_id, nav_config in NAVIGATION_CONFIG.items() 
                       if nav_id not in {'ai-query'}}
            else:
                return {}
        
        user_resources = set(PermissionService.get_user_resources(user))
        accessible_nav = {}
        
        # Load visibility settings for this org
        visibility = PermissionService._get_visibility_settings(user.organization_id) if user.organization_id else {}
        
        # Explicitly exclude removed navigation items
        excluded_nav_items = {'ai-query'}
        
        for nav_id, nav_config in NAVIGATION_CONFIG.items():
            # Skip excluded items
            if nav_id in excluded_nav_items:
                continue
                
            # Check if user has access to main nav item
            required_resource = nav_config.get('required_resource')
            
            # If there's a required resource, check if user has access
            if required_resource and required_resource not in user_resources:
                continue
            
            # Multi-tenancy check: VITAL-specific resources should only be visible to VITAL Worklife
            if required_resource and required_resource.startswith('vital_'):
                if user.organization.name != 'VITAL Worklife':
                    continue
            
            # Minitrac is only available for Bennett Material Handling
            if required_resource == 'minitrac':
                if user.organization.name != 'Bennett Material Handling':
                    continue
            
            # Ed's Dashboard is only available for IPS (ind004)
            if required_resource == 'eds_dashboard':
                if not user.organization.database_schema or user.organization.database_schema != 'ind004':
                    continue
            
            # Check page-level visibility from admin settings
            if nav_id in visibility and not visibility[nav_id].get('visible', True):
                continue
            
            # Filter tabs if they exist
            if 'tabs' in nav_config:
                accessible_tabs = {}
                for tab_id, tab_config in nav_config['tabs'].items():
                    if tab_config['resource'] in user_resources:
                        # Check tab-level visibility from admin settings
                        if nav_id in visibility:
                            tab_vis = visibility[nav_id].get('tabs', {})
                            if tab_id in tab_vis and not tab_vis[tab_id]:
                                continue
                        accessible_tabs[tab_id] = tab_config
                
                # Only include nav item if user has access to at least one tab
                if accessible_tabs:
                    accessible_nav[nav_id] = {**nav_config, 'tabs': accessible_tabs}
            else:
                # No tabs, include the nav item
                accessible_nav[nav_id] = nav_config
        
        return accessible_nav
    
    @staticmethod
    def get_user_permissions_summary(user):
        """Get comprehensive permissions summary for user"""
        if not user or not user.roles:
            return {
                'resources': [],
                'navigation': {},
                'role_names': [],
                'is_admin': False
            }
        
        resources = PermissionService.get_user_resources(user)
        navigation = PermissionService.get_user_navigation(user)
        valid_roles = PermissionService._get_valid_roles(user)
        role_names = [role.name for role in valid_roles]
        is_admin = any(role.name == 'Super Admin' for role in valid_roles)
        
        # Build resource-action mapping
        resource_actions = {}
        for resource in resources:
            resource_actions[resource] = PermissionService.get_user_actions(user, resource)
        
        return {
            'resources': resources,
            'resource_actions': resource_actions,
            'navigation': navigation,
            'role_names': role_names,
            'is_admin': is_admin
        }
    
    @staticmethod
    def is_super_admin(user):
        """Check if user is Super Admin"""
        if not user or not user.roles:
            return False
        
        return any(role.name == 'Super Admin' for role in PermissionService._get_valid_roles(user))
    
    @staticmethod
    def can_manage_users(user):
        """Check if user can manage other users"""
        return PermissionService.user_has_permission(user, 'user_management', 'view')
    
    @staticmethod
    def validate_resource_access(user, resource, action='view'):
        """Validate and raise exception if user doesn't have access"""
        if not PermissionService.user_has_permission(user, resource, action):
            from flask import jsonify
            return jsonify({
                'error': 'Access denied',
                'message': f'User does not have {action} permission for {resource}'
            }), 403
        return None