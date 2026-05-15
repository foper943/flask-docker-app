import type { Mentor, Review, UserSkill } from '../types'
import { apiClient } from './client'

interface MentorDetailResponse {
  mentor: Mentor & { skills: UserSkill[]; reviews: Review[] }
}

export const getMentors = (params?: { skill_id?: number; min_rating?: number }) =>
  apiClient
    .get<{ mentors: Mentor[] }>('/api/mentors', { params })
    .then((r) => r.data.mentors)

export const getMentor = (id: number) =>
  apiClient.get<MentorDetailResponse>(`/api/mentors/${id}`).then((r) => r.data.mentor)
