import axios from "axios";

// Simple fix: Always use localhost for now
export const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1'
});
