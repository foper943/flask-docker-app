import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Layout from './components/layout/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ProfilePage from './pages/ProfilePage'
import ProfileEditPage from './pages/ProfileEditPage'
import SkillsPage from './pages/SkillsPage'
import SkillDetailPage from './pages/SkillDetailPage'
import MentorsPage from './pages/MentorsPage'
import MentorDetailPage from './pages/MentorDetailPage'
import SessionsPage from './pages/SessionsPage'
import MessagesPage from './pages/MessagesPage'
import ChatPage from './pages/ChatPage'

export default function App() {
  const user = useAuthStore((s) => s.user)

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/skills" replace />} />
          <Route path="/profile/:id" element={<ProfilePage />} />
          <Route path="/profile/edit" element={<ProfileEditPage />} />
          <Route path="/skills" element={<SkillsPage />} />
          <Route path="/skills/:id" element={<SkillDetailPage />} />
          <Route path="/mentors" element={<MentorsPage />} />
          <Route path="/mentors/:id" element={<MentorDetailPage />} />
          <Route path="/sessions" element={<SessionsPage />} />
          <Route path="/messages" element={<MessagesPage />} />
          <Route path="/messages/:userId" element={<ChatPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to={user ? '/skills' : '/login'} replace />} />
    </Routes>
  )
}
