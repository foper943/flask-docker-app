import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { getMentor } from '../api/mentors'
import { createSession } from '../api/sessions'
import { useAuthStore } from '../store/authStore'
import Avatar from '../components/ui/Avatar'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Modal from '../components/ui/Modal'
import Spinner from '../components/ui/Spinner'
import StarRating from '../components/ui/StarRating'

export default function MentorDetailPage() {
  const { id } = useParams<{ id: string }>()
  const mentorId = Number(id)
  const currentUser = useAuthStore((s) => s.user)
  const navigate = useNavigate()
  const qc = useQueryClient()

  const [bookingOpen, setBookingOpen] = useState(false)
  const [booking, setBooking] = useState({ skill_id: '', scheduled_at: '', topic: '' })

  const { data: mentor, isLoading } = useQuery({
    queryKey: ['mentor', mentorId],
    queryFn: () => getMentor(mentorId),
  })

  const sessionMutation = useMutation({
    mutationFn: () =>
      createSession({
        mentor_id: mentorId,
        skill_id: Number(booking.skill_id),
        scheduled_at: booking.scheduled_at,
        topic: booking.topic,
      }),
    onSuccess: () => {
      toast.success('Запрос на сессию отправлен!')
      setBookingOpen(false)
      qc.invalidateQueries({ queryKey: ['sessions'] })
    },
    onError: () => toast.error('Ошибка при записи на сессию'),
  })

  if (isLoading) return <Spinner className="mt-20" />
  if (!mentor) return <p className="mt-20 text-center text-gray-500">Ментор не найден</p>

  const teachingSkills = mentor.skills.filter((s) => s.type === 'teaching')
  const isOwnProfile = currentUser?.id === mentorId

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Профиль */}
      <Card>
        <div className="flex items-start gap-4">
          <Avatar name={mentor.name} src={mentor.avatar_url} size="lg" />
          <div className="flex-1">
            <h1 className="text-xl font-bold text-gray-900">{mentor.name}</h1>
            {mentor.average_rating !== null ? (
              <div className="mt-1 flex items-center gap-2">
                <StarRating value={Math.round(mentor.average_rating)} size="sm" />
                <span className="text-sm text-gray-500">
                  {mentor.average_rating.toFixed(1)} ({mentor.review_count} отзывов)
                </span>
              </div>
            ) : (
              <p className="mt-1 text-sm text-gray-400">Нет отзывов</p>
            )}
            {mentor.bio && <p className="mt-2 text-sm text-gray-600">{mentor.bio}</p>}

            <div className="mt-3 flex flex-wrap gap-1.5">
              {teachingSkills.map((s) => (
                <Badge key={s.skill_id} color="green">{s.skill_name}</Badge>
              ))}
            </div>
          </div>
          {!isOwnProfile && (
            <div className="flex flex-col gap-2">
              <Button onClick={() => setBookingOpen(true)}>Записаться</Button>
              <Button variant="secondary" onClick={() => navigate(`/messages/${mentorId}`)}>
                Написать
              </Button>
            </div>
          )}
        </div>
      </Card>

      {/* Отзывы */}
      <div>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">Отзывы</h2>
        {mentor.reviews.length === 0 ? (
          <p className="text-sm text-gray-500">Отзывов пока нет</p>
        ) : (
          <div className="space-y-3">
            {mentor.reviews.map((r) => (
              <Card key={r.id}>
                <div className="flex items-center gap-3">
                  <Avatar name={r.reviewer_name} src={r.reviewer_avatar} size="sm" />
                  <div>
                    <p className="text-sm font-medium">{r.reviewer_name}</p>
                    <StarRating value={r.rating} size="sm" />
                  </div>
                  <span className="ml-auto text-xs text-gray-400">
                    {new Date(r.created_at).toLocaleDateString('ru-RU')}
                  </span>
                </div>
                {r.comment && <p className="mt-2 text-sm text-gray-600">{r.comment}</p>}
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Модальное окно записи */}
      <Modal open={bookingOpen} onClose={() => setBookingOpen(false)} title="Записаться на сессию">
        <form
          onSubmit={(e) => { e.preventDefault(); sessionMutation.mutate() }}
          className="space-y-4"
        >
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Навык</label>
            <select
              required
              value={booking.skill_id}
              onChange={(e) => setBooking((b) => ({ ...b, skill_id: e.target.value }))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
            >
              <option value="">Выберите навык...</option>
              {teachingSkills.map((s) => (
                <option key={s.skill_id} value={s.skill_id}>{s.skill_name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Дата и время</label>
            <input
              type="datetime-local"
              required
              value={booking.scheduled_at}
              onChange={(e) => setBooking((b) => ({ ...b, scheduled_at: e.target.value }))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Тема сессии</label>
            <textarea
              required
              rows={2}
              value={booking.topic}
              onChange={(e) => setBooking((b) => ({ ...b, topic: e.target.value }))}
              placeholder="Что хотите изучить или обсудить?"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
            />
          </div>
          <div className="flex gap-3">
            <Button type="button" variant="secondary" onClick={() => setBookingOpen(false)} className="flex-1">
              Отмена
            </Button>
            <Button type="submit" loading={sessionMutation.isPending} className="flex-1">
              Записаться
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
