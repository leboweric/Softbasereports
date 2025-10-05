import { createContext, useContext } from 'react';

export const PermissionsContext = createContext(null);

export function usePermissions() {
  const context = useContext(PermissionsContext);
  if (!context) {
    throw new Error('usePermissions must be used within PermissionsProvider');
  }
  return context;
}

// Permission helper functions
export function hasResource(user, resource) {
  if (!user?.resources) return false;
  return user.resources.includes(resource);
}

export function hasPermission(user, resource, action = 'view') {
  if (!user?.permissions_summary?.resource_actions) return false;
  const resourceActions = user.permissions_summary.resource_actions[resource];
  if (!resourceActions) return false;
  return resourceActions.includes(action);
}

export function getAccessibleNavigation(user) {
  return user?.navigation || {};
}

export function getAccessibleTabs(user, section) {
  const navigation = getAccessibleNavigation(user);
  return navigation[section]?.tabs || {};
}

export function isAdmin(user) {
  return user?.permissions_summary?.is_admin || false;
}

export function getUserRoles(user) {
  return user?.permissions_summary?.role_names || [];
}

export function canAccessResource(user, resource) {
  return hasResource(user, resource);
}