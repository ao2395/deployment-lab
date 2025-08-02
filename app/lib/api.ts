import axios from 'axios'
import Cookies from 'js-cookie'

const API_URL = process.env.NEXT_PUBLIC_API_URL || '/api'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = Cookies.get('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface User {
  id: string
  username: string
  is_active: boolean
}

export interface Deployment {
  id: string
  name: string
  github_url: string
  subdomain: string
  port: number
  status: 'pending' | 'building' | 'running' | 'failed' | 'stopped'
  created_at: string
  updated_at: string
}

export interface DeploymentCreate {
  github_url: string
  subdomain: string
  env_vars?: Record<string, string>
}

export interface LogEntry {
  id: string
  message: string
  log_level: string
  timestamp: string
}

// Auth API
export const authAPI = {
  login: (credentials: LoginRequest) => api.post<LoginResponse>('/auth/login', credentials),
  verify: () => api.get<User>('/auth/verify'),
  logout: () => api.post('/auth/logout'),
}

// Deployments API
export const deploymentsAPI = {
  list: () => api.get<Deployment[]>('/deployments/'),
  create: (deployment: DeploymentCreate) => api.post<Deployment>('/deployments/', deployment),
  get: (id: string) => api.get<Deployment>(`/deployments/${id}`),
  delete: (id: string) => api.delete(`/deployments/${id}`),
  getLogs: (id: string) => api.get<LogEntry[]>(`/deployments/${id}/logs`),
  getStatus: (id: string) => api.get<{id: string, status: string, updated_at: string}>(`/deployments/${id}/status`),
}