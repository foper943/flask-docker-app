import type { Mentor, Skill } from '../types'
import { apiClient } from './client'

interface SkillsResponse {
  skills: Skill[]
  categories: string[]
}

interface SkillDetailResponse {
  skill: Skill
  mentors: Mentor[]
}

export const getSkills = (search = '', category = '') =>
  apiClient
    .get<SkillsResponse>('/api/skills', { params: { search, category } })
    .then((r) => r.data)

export const getSkill = (id: number) =>
  apiClient.get<SkillDetailResponse>(`/api/skills/${id}`).then((r) => r.data)

export const createSkill = (data: { name: string; category: string; description: string }) =>
  apiClient.post<{ skill: Skill }>('/api/skills', data).then((r) => r.data.skill)
