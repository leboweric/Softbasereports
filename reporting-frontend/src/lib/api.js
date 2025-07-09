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