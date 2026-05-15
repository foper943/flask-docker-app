import type { User } from '../types'
import { apiClient } from './client'

export const getUser = (id: number) =>
  apiClient.get<{ user: User }>(`/api/users/${id}`).then((r) => r.data.user)

interface UpdateUserPayload {
  name: string
  bio: string
  avatar_url: string
  role: string
  teaching_skills: number[]
  learning_skills: number[]
}

export const updateUser = (id: number, payload: UpdateUserPayload) =>
  apiClient.put<{ user: User }>(`/api/users/${id}`, payload).then((r) => r.data.user)
