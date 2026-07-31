import axios from "axios";
import { supabase } from './supabase'
import { apiBaseUrl } from './config'

export const api = axios.create({
  baseURL: apiBaseUrl
});

// getSession returns Supabase's latest refreshed session when one exists.
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.set('Authorization', `Bearer ${session.access_token}`)
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && error.config?.headers?.Authorization) {
      await supabase.auth.signOut()
      window.dispatchEvent(new CustomEvent('chopurl:session-expired'))
    }
    return Promise.reject(error)
  }
)
