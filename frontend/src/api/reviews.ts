import type { Review, ReviewsResponse } from '../types'
import { apiClient } from './client'

interface CreateReviewPayload {
  reviewee_id: number
  session_id: number
  rating: number
  comment: string
}

export const getReviews = (userId: number) =>
  apiClient.get<ReviewsResponse>(`/api/reviews/${userId}`).then((r) => r.data)

export const createReview = (payload: CreateReviewPayload) =>
  apiClient.post<{ review: Review }>('/api/reviews', payload).then((r) => r.data.review)
