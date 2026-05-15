import type { AuthResponse, User } from '../types'
import { apiClient } from './client'

export const register = (data: { email: string; password: string; name: string }) =>
  apiClient.post<AuthResponse>('/api/auth/register', data).then((r) => r.data)

export const login = (data: { email: string; password: string }) =>
  apiClient.post<AuthResponse>('/api/auth/login', data).then((r) => r.data)

export const getMe = () =>
  apiClient.get<{ user: User }>('/api/auth/me').then((r) => r.data.user)
