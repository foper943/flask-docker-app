import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { login } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import Button from '../components/ui/Button'

export default function LoginPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const data = await login(form)
      setAuth(data.token, data.user)
      navigate('/skills')
    } catch {
      toast.error('Неверный email или пароль')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-sm">
        <h1 className="mb-1 text-center text-2xl font-bold text-gray-900">PeerLearn</h1>
        <p className="mb-8 text-center text-gray-500">Платформа взаимного обучения</p>

        <div className="rounded-2xl bg-white p-8 shadow-sm">
          <h2 className="mb-6 text-lg font-semibold">Войти</h2>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Пароль</label>
              <input
                type="password"
                required
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
            <Button type="submit" loading={loading} className="mt-2 w-full">
              Войти
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-gray-500">
            Нет аккаунта?{' '}
            <Link to="/register" className="font-medium text-primary-600 hover:text-primary-700">
              Зарегистрироваться
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
