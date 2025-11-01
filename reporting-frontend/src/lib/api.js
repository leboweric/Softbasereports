// API configuration
const API_URL = import.meta.env.VITE_API_URL || '';

export const apiUrl = (path) => {
  // In development, the proxy handles /api routes
  // In production, we need to use the full URL
  if (import.meta.env.DEV) {
    return path;
  }
  
  // If no API_URL is set, log an error
  if (!API_URL) {
    console.error('VITE_API_URL is not set! API calls will fail.');
    console.log('Current env:', import.meta.env);
  }
  
  return `${API_URL}${path}`;
};

export const fetchApi = async (path, options = {}) => {
  const url = apiUrl(path);
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || `HTTP error! status: ${response.status}`);
  }
  
  return response;
};

// Helper function to get JWT token
const getToken = () => localStorage.getItem('token');

// Admin API functions for tenant management
export const adminApi = {
  async getOrganizations() {
    const res = await fetch(apiUrl('/api/admin/organizations'), {
      headers: { 'Authorization': `Bearer ${getToken()}` },
    });
    if (!res.ok) throw new Error('Failed to fetch organizations');
    return res.json();
  },

  async createOrganization(data) {
    const res = await fetch(apiUrl('/api/admin/organizations'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.message || 'Failed to create organization');
    }
    return res.json();
  },

  async updateOrganization(id, data) {
    const res = await fetch(apiUrl(`/api/admin/organizations/${id}`), {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.message || 'Failed to update organization');
    }
    return res.json();
  },

  async getOrganization(id) {
    const res = await fetch(apiUrl(`/api/admin/organizations/${id}`), {
      headers: { 'Authorization': `Bearer ${getToken()}` },
    });
    if (!res.ok) throw new Error('Failed to fetch organization');
    return res.json();
  },

  async deleteOrganization(id) {
    const res = await fetch(apiUrl(`/api/admin/organizations/${id}`), {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${getToken()}` },
    });
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.message || 'Failed to delete organization');
    }
    return res.json();
  },

  async getOrganizationUsers(id) {
    const res = await fetch(apiUrl(`/api/admin/organizations/${id}/users`), {
      headers: { 'Authorization': `Bearer ${getToken()}` },
    });
    if (!res.ok) throw new Error('Failed to fetch organization users');
    return res.json();
  },

  async testConnection(id) {
    const res = await fetch(apiUrl(`/api/admin/organizations/${id}/test-connection`), {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${getToken()}` },
    });
    // Don't throw error on non-ok, as 500 is a valid test result
    return res.json();
  },

  async getSupportedPlatforms() {
    const res = await fetch(apiUrl('/api/admin/platforms'), {
      headers: { 'Authorization': `Bearer ${getToken()}` },
    });
    if (!res.ok) throw new Error('Failed to fetch supported platforms');
    return res.json();
  },
};