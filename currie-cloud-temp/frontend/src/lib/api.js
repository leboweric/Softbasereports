/**
 * API Configuration and Helper Functions
 * IMPORTANT: Never hardcode URLs - always use these functions
 */

// API base URL - uses environment variable in production
const API_BASE = import.meta.env.VITE_API_URL || ''

/**
 * Construct API URL for an endpoint
 * @param {string} endpoint - API endpoint path (e.g., '/api/auth/login')
 * @returns {string} Full API URL
 */
export function apiUrl(endpoint) {
  return `${API_BASE}${endpoint}`
}

/**
 * Get auth token from localStorage
 */
export function getToken() {
  return localStorage.getItem('access_token')
}

/**
 * Set auth token in localStorage
 */
export function setToken(token) {
  localStorage.setItem('access_token', token)
}

/**
 * Remove auth token from localStorage
 */
export function clearToken() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

/**
 * Make authenticated API request
 * @param {string} endpoint - API endpoint
 * @param {object} options - Fetch options
 * @returns {Promise<Response>}
 */
export async function fetchApi(endpoint, options = {}) {
  const token = getToken()

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(apiUrl(endpoint), {
    ...options,
    headers,
  })

  // Handle 401 - token expired
  if (response.status === 401 && token) {
    clearToken()
    window.location.href = '/login'
  }

  return response
}

/**
 * GET request helper
 */
export async function get(endpoint) {
  const response = await fetchApi(endpoint)
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`)
  }
  return response.json()
}

/**
 * POST request helper
 */
export async function post(endpoint, data) {
  const response = await fetchApi(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Request failed' }))
    throw new Error(error.error || `API Error: ${response.status}`)
  }
  return response.json()
}

/**
 * PUT request helper
 */
export async function put(endpoint, data) {
  const response = await fetchApi(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`)
  }
  return response.json()
}

/**
 * DELETE request helper
 */
export async function del(endpoint) {
  const response = await fetchApi(endpoint, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`)
  }
  return response.json()
}
