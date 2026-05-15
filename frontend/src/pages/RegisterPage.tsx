import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { register } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import Button from '../components/ui/Button'

export default function RegisterPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (form.password.length < 6) {
      toast.error('Пароль должен быть не менее 6 символов')
      return
    }
    setLoading(true)
    try {
      const data = await register(form)
      setAuth(data.token, data.user)
      navigate('/profile/edit')
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Ошибка регистрации'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-sm">
        <h1 className="mb-1 text-center text-2xl font-bold text-gray-900">PeerLearn</h1>
        <p className="mb-8 text-center text-gray-500">Создайте аккаунт</p>

        <div className="rounded-2xl bg-white p-8 shadow-sm">
          <h2 className="mb-6 text-lg font-semibold">Регистрация</h2>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {(['name', 'email', 'password'] as const).map((field) => (
              <div key={field}>
                <label className="mb-1 block text-sm font-medium text-gray-700 capitalize">
                  {field === 'name' ? 'Имя' : field === 'email' ? 'Email' : 'Пароль'}
                </label>
                <input
                  type={field === 'email' ? 'email' : field === 'password' ? 'password' : 'text'}
                  required
                  value={form[field]}
                  onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
            ))}
            <Button type="submit" loading={loading} className="mt-2 w-full">
              Зарегистрироваться
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-gray-500">
            Уже есть аккаунт?{' '}
            <Link to="/login" className="font-medium text-primary-600 hover:text-primary-700">
              Войти
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
