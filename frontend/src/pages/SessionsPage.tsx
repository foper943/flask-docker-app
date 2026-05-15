import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { getSessions, updateSessionStatus } from '../api/sessions'
import { createReview } from '../api/reviews'
import { useAuthStore } from '../store/authStore'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Modal from '../components/ui/Modal'
import Spinner from '../components/ui/Spinner'
import StarRating from '../components/ui/StarRating'
import type { Session } from '../types'

const STATUS_LABELS = {
  pending:   { text: 'Ожидает',      color: 'yellow' },
  confirmed: { text: 'Подтверждено', color: 'green'  },
  completed: { text: 'Завершено',    color: 'gray'   },
  cancelled: { text: 'Отменено',     color: 'red'    },
} as const

type Tab = 'pending' | 'upcoming' | 'past'

export default function SessionsPage() {
  const currentUser = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('pending')
  const [reviewTarget, setReviewTarget] = useState<Session | null>(null)
  const [review, setReview] = useState({ rating: 0, comment: '' })

  const { data, isLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: getSessions,
  })

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: Session['status'] }) =>
      updateSessionStatus(id, status),
    onSuccess: () => {
      toast.success('Статус обновлён')
      qc.invalidateQueries({ queryKey: ['sessions'] })
    },
    onError: () => toast.error('Ошибка обновления статуса'),
  })

  const reviewMutation = useMutation({
    mutationFn: () =>
      createReview({
        reviewee_id: currentUser!.id === reviewTarget!.mentor_id
          ? reviewTarget!.learner_id
          : reviewTarget!.mentor_id,
        session_id: reviewTarget!.id,
        rating: review.rating,
        comment: review.comment,
      }),
    onSuccess: () => {
      toast.success('Отзыв оставлен')
      setReviewTarget(null)
      setReview({ rating: 0, comment: '' })
    },
    onError: () => toast.error('Ошибка при сохранении отзыва'),
  })

  if (isLoading) return <Spinner className="mt-20" />

  const sessions: Session[] = (tab === 'pending' ? data?.pending : tab === 'upcoming' ? data?.upcoming : data?.past) ?? []

  const tabs: { key: Tab; label: string; count: number }[] = [
    { key: 'pending',  label: 'Ожидают',      count: data?.pending.length  ?? 0 },
    { key: 'upcoming', label: 'Предстоящие',   count: data?.upcoming.length ?? 0 },
    { key: 'past',     label: 'Прошедшие',     count: data?.past.length     ?? 0 },
  ]

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Мои сессии</h1>

      {/* Табы */}
      <div className="mb-6 flex gap-1 rounded-xl bg-gray-100 p-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              tab === t.key
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
            {t.count > 0 && (
              <span className="ml-1.5 rounded-full bg-primary-100 px-1.5 py-0.5 text-xs text-primary-700">
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {sessions.length === 0 ? (
        <p className="text-center text-gray-500">Сессий нет</p>
      ) : (
        <div className="space-y-3">
          {sessions.map((s) => {
            const isMentor = currentUser?.id === s.mentor_id
            const label = STATUS_LABELS[s.status]
            return (
              <Card key={s.id}>
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold text-gray-900">{s.topic}</p>
                    <p className="mt-0.5 text-sm text-gray-500">
                      {isMentor ? `Ученик: ${s.learner_name}` : `Ментор: ${s.mentor_name}`}
                      {' · '}{s.skill_name}
                    </p>
                    <p className="mt-0.5 text-sm text-gray-400">
                      {new Date(s.scheduled_at).toLocaleString('ru-RU')}
                    </p>
                  </div>
                  <Badge color={label.color}>{label.text}</Badge>
                </div>

                {/* Действия */}
                <div className="mt-3 flex flex-wrap gap-2">
                  {s.status === 'pending' && isMentor && (
                    <>
                      <Button
                        size="sm"
                        onClick={() => statusMutation.mutate({ id: s.id, status: 'confirmed' })}
                        loading={statusMutation.isPending}
                      >
                        Подтвердить
                      </Button>
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() => statusMutation.mutate({ id: s.id, status: 'cancelled' })}
                        loading={statusMutation.isPending}
                      >
                        Отклонить
                      </Button>
                    </>
                  )}
                  {s.status === 'confirmed' && isMentor && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => statusMutation.mutate({ id: s.id, status: 'completed' })}
                      loading={statusMutation.isPending}
                    >
                      Отметить завершённой
                    </Button>
                  )}
                  {s.status === 'confirmed' && !isMentor && (
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => statusMutation.mutate({ id: s.id, status: 'cancelled' })}
                      loading={statusMutation.isPending}
                    >
                      Отменить
                    </Button>
                  )}
                  {s.status === 'completed' && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setReviewTarget(s)}
                    >
                      Оставить отзыв
                    </Button>
                  )}
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {/* Модальное окно отзыва */}
      <Modal
        open={reviewTarget !== null}
        onClose={() => setReviewTarget(null)}
        title="Оставить отзыв"
      >
        <div className="space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">Оценка</label>
            <StarRating value={review.rating} onChange={(v) => setReview((r) => ({ ...r, rating: v }))} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Комментарий</label>
            <textarea
              rows={3}
              value={review.comment}
              onChange={(e) => setReview((r) => ({ ...r, comment: e.target.value }))}
              placeholder="Поделитесь впечатлениями..."
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
            />
          </div>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setReviewTarget(null)} className="flex-1">
              Отмена
            </Button>
            <Button
              onClick={() => reviewMutation.mutate()}
              disabled={review.rating === 0}
              loading={reviewMutation.isPending}
              className="flex-1"
            >
              Отправить
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
