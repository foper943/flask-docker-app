export interface User {
  id: number
  email: string
  name: string
  bio: string | null
  avatar_url: string | null
  role: 'mentor' | 'learner' | 'both'
  created_at: string
  skills?: UserSkill[]
}

export interface Skill {
  id: number
  name: string
  category: string
  description: string | null
  mentor_count: number
  created_at: string
}

export interface UserSkill {
  skill_id: number
  skill_name: string
  skill_category: string
  type: 'teaching' | 'learning'
}

export interface Mentor {
  id: number
  name: string
  bio: string | null
  avatar_url: string | null
  role: 'mentor' | 'learner' | 'both'
  skills: UserSkill[]
  average_rating: number | null
  review_count: number
}

export interface Session {
  id: number
  mentor_id: number
  mentor_name: string
  learner_id: number
  learner_name: string
  skill_id: number
  skill_name: string
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled'
  scheduled_at: string
  topic: string
  created_at: string
}

export interface ChatMessage {
  id: number
  sender_id: number
  receiver_id: number
  text: string
  is_read: boolean
  created_at: string
}

export interface Dialog {
  user_id: number
  user_name: string
  user_avatar: string | null
  last_message: string
  last_message_at: string
  unread_count: number
}

export interface Review {
  id: number
  reviewer_id: number
  reviewer_name: string
  reviewer_avatar: string | null
  reviewee_id: number
  session_id: number
  rating: number
  comment: string | null
  created_at: string
}

export interface AuthResponse {
  token: string
  user: User
}

export interface SessionsResponse {
  upcoming: Session[]
  past: Session[]
  pending: Session[]
}

export interface ReviewsResponse {
  reviews: Review[]
  average_rating: number | null
  count: number
}
