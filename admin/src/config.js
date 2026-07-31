const localApiBaseUrl = 'http://localhost:8000/api/v1'

export const apiBaseUrl = import.meta.env.VITE_API_BASE_URL
  || (import.meta.env.DEV ? localApiBaseUrl : '/api/v1')
