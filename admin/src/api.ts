import axios from "axios";
import { supabase } from './supabase'
import { apiBaseUrl } from './config'

export const api = axios.create({
  baseURL: apiBaseUrl
});

// Attach auth token to every request
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})
