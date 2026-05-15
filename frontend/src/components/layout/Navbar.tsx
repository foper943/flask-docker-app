import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../store/authStore'
import { getDialogs } from '../../api/chat'
import Avatar from '../ui/Avatar'

export default function Navbar() {
  const { user, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  const { data: dialogs } = useQuery({
    queryKey: ['dialogs'],
    queryFn: getDialogs,
    refetchInterval: 5000,
    enabled: !!user,
  })

  const unread = dialogs?.reduce((acc, d) => acc + d.unread_count, 0) ?? 0

  const logout = () => {
    clearAuth()
    navigate('/login')
  }

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `text-sm font-medium transition-colors ${
      isActive ? 'text-primary-600' : 'text-gray-600 hover:text-gray-900'
    }`

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
        <Link to="/skills" className="text-lg font-bold text-primary-600">
          PeerLearn
        </Link>

        <nav className="flex flex-1 items-center gap-4 overflow-x-auto">
          <NavLink to="/skills" className={linkClass}>Навыки</NavLink>
          <NavLink to="/mentors" className={linkClass}>Менторы</NavLink>
          <NavLink to="/sessions" className={linkClass}>Сессии</NavLink>
          <NavLink to="/messages" className={linkClass}>
            <span className="relative">
              Сообщения
              {unread > 0 && (
                <span className="absolute -right-3 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-xs text-white">
                  {unread > 9 ? '9+' : unread}
                </span>
              )}
            </span>
          </NavLink>
        </nav>

        {user && (
          <div className="flex items-center gap-3">
            <Link to={`/profile/${user.id}`} className="flex items-center gap-2">
              <Avatar name={user.name} src={user.avatar_url} size="sm" />
              <span className="hidden text-sm font-medium text-gray-700 sm:block">{user.name}</span>
            </Link>
            <button
              onClick={logout}
              className="text-sm text-gray-500 hover:text-gray-900"
            >
              Выйти
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
