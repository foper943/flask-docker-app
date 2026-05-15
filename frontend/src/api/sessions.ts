import type { Session, SessionsResponse } from '../types'
import { apiClient } from './client'

interface CreateSessionPayload {
  mentor_id: number
  skill_id: number
  scheduled_at: string
  topic: string
}

export const getSessions = () =>
  apiClient.get<SessionsResponse>('/api/sessions').then((r) => r.data)

export const createSession = (payload: CreateSessionPayload) =>
  apiClient.post<{ session: Session }>('/api/sessions', payload).then((r) => r.data.session)

export const updateSessionStatus = (id: number, status: Session['status']) =>
  apiClient
    .put<{ session: Session }>(`/api/sessions/${id}`, { status })
    .then((r) => r.data.session)
