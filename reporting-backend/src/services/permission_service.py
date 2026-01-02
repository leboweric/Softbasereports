"""
Permission checking service for dynamic RBAC
"""
from src.config.rbac_config import ROLE_PERMISSIONS, RESOURCES, NAVIGATION_CONFIG

class PermissionService:
    @staticmethod
    def user_has_permission(user, resource, action='view'):
        """Check if user has permission for resource/action"""
        if not user or not user.roles:
            return False
        
        for role in user.roles:
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
        for role in user.roles:
            role_perms = ROLE_PERMISSIONS.get(role.name, {})
            resources.update(role_perms.get('resources', []))
        
        return list(resources)
    
    @staticmethod
    def get_user_actions(user, resource):
        """Get all actions user can perform on a resource"""
        if not user or not user.roles:
            return []
        
        actions = set()
        for role in user.roles:
            role_perms = ROLE_PERMISSIONS.get(role.name, {})
            
            # Check if role has access to this resource
            if resource in role_perms.get('resources', []):
                # Add all actions this role can perform
                actions.update(role_perms.get('actions', []))
        
        return list(actions)
    
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
            
            # Filter tabs if they exist
            if 'tabs' in nav_config:
                accessible_tabs = {}
                for tab_id, tab_config in nav_config['tabs'].items():
                    if tab_config['resource'] in user_resources:
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
        role_names = [role.name for role in user.roles]
        is_admin = any(role.name == 'Super Admin' for role in user.roles)
        
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
        
        return any(role.name == 'Super Admin' for role in user.roles)
    
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