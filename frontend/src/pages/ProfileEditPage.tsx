import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { getUser, updateUser } from '../api/users'
import { getSkills } from '../api/skills'
import { useAuthStore } from '../store/authStore'
import Button from '../components/ui/Button'
import Spinner from '../components/ui/Spinner'
import type { Skill } from '../types'

type Role = 'mentor' | 'learner' | 'both'

export default function ProfileEditPage() {
  const currentUser = useAuthStore((s) => s.user)
  const setAuth = useAuthStore((s) => s.setAuth)
  const token = useAuthStore((s) => s.token)
  const navigate = useNavigate()
  const qc = useQueryClient()

  const [form, setForm] = useState({ name: '', bio: '', avatar_url: '', role: 'learner' as Role })
  const [teachingIds, setTeachingIds] = useState<number[]>([])
  const [learningIds, setLearningIds] = useState<number[]>([])

  const { data: user, isLoading: loadingUser } = useQuery({
    queryKey: ['user', currentUser?.id],
    queryFn: () => getUser(currentUser!.id),
    enabled: !!currentUser,
  })

  const { data: skillsData, isLoading: loadingSkills } = useQuery({
    queryKey: ['skills'],
    queryFn: () => getSkills(),
  })

  useEffect(() => {
    if (!user) return
    setForm({ name: user.name, bio: user.bio ?? '', avatar_url: user.avatar_url ?? '', role: user.role })
    setTeachingIds(user.skills?.filter((s) => s.type === 'teaching').map((s) => s.skill_id) ?? [])
    setLearningIds(user.skills?.filter((s) => s.type === 'learning').map((s) => s.skill_id) ?? [])
  }, [user])

  const mutation = useMutation({
    mutationFn: () =>
      updateUser(currentUser!.id, {
        ...form,
        teaching_skills: teachingIds,
        learning_skills: learningIds,
      }),
    onSuccess: (updated) => {
      setAuth(token!, updated)
      qc.invalidateQueries({ queryKey: ['user', currentUser?.id] })
      toast.success('Профиль обновлён')
      navigate(`/profile/${currentUser?.id}`)
    },
    onError: () => toast.error('Ошибка при сохранении'),
  })

  const toggleSkill = (id: number, list: number[], setList: (v: number[]) => void) => {
    setList(list.includes(id) ? list.filter((x) => x !== id) : [...list, id])
  }

  if (loadingUser || loadingSkills) return <Spinner className="mt-20" />

  const skills: Skill[] = skillsData?.skills ?? []
  const categories = [...new Set(skills.map((s) => s.category))]

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-xl font-bold text-gray-900">Редактировать профиль</h1>

      <form
        onSubmit={(e) => { e.preventDefault(); mutation.mutate() }}
        className="space-y-6"
      >
        {/* Основные поля */}
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <h2 className="mb-4 font-semibold text-gray-900">Основное</h2>
          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Имя *</label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">О себе</label>
              <textarea
                rows={3}
                value={form.bio}
                onChange={(e) => setForm((f) => ({ ...f, bio: e.target.value }))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Ссылка на аватар</label>
              <input
                type="url"
                value={form.avatar_url}
                onChange={(e) => setForm((f) => ({ ...f, avatar_url: e.target.value }))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Роль</label>
              <select
                value={form.role}
                onChange={(e) => setForm((f) => ({ ...f, role: e.target.value as Role }))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                <option value="learner">Ученик</option>
                <option value="mentor">Ментор</option>
                <option value="both">Ментор и ученик</option>
              </select>
            </div>
          </div>
        </div>

        {/* Навыки */}
        {categories.map((cat) => (
          <div key={cat} className="rounded-xl border border-gray-200 bg-white p-5">
            <h2 className="mb-3 font-semibold text-gray-900">{cat}</h2>
            <div className="space-y-2">
              {skills.filter((s) => s.category === cat).map((skill) => (
                <div key={skill.id} className="flex items-center gap-6">
                  <span className="w-40 text-sm text-gray-700">{skill.name}</span>
                  <label className="flex cursor-pointer items-center gap-1.5 text-sm text-green-700">
                    <input
                      type="checkbox"
                      checked={teachingIds.includes(skill.id)}
                      onChange={() => toggleSkill(skill.id, teachingIds, setTeachingIds)}
                      className="accent-green-600"
                    />
                    Преподаю
                  </label>
                  <label className="flex cursor-pointer items-center gap-1.5 text-sm text-indigo-700">
                    <input
                      type="checkbox"
                      checked={learningIds.includes(skill.id)}
                      onChange={() => toggleSkill(skill.id, learningIds, setLearningIds)}
                      className="accent-indigo-600"
                    />
                    Изучаю
                  </label>
                </div>
              ))}
            </div>
          </div>
        ))}

        <Button type="submit" loading={mutation.isPending} className="w-full">
          Сохранить
        </Button>
      </form>
    </div>
  )
}
