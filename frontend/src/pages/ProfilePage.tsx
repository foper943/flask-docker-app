import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getUser } from '../api/users'
import { getReviews } from '../api/reviews'
import { useAuthStore } from '../store/authStore'
import Avatar from '../components/ui/Avatar'
import Badge from '../components/ui/Badge'
import Card from '../components/ui/Card'
import Spinner from '../components/ui/Spinner'
import StarRating from '../components/ui/StarRating'
import Button from '../components/ui/Button'

const ROLE_LABELS = { mentor: 'Ментор', learner: 'Ученик', both: 'Ментор и ученик' }
const ROLE_COLORS = { mentor: 'green', learner: 'indigo', both: 'yellow' } as const

export default function ProfilePage() {
  const { id } = useParams<{ id: string }>()
  const userId = Number(id)
  const currentUser = useAuthStore((s) => s.user)

  const { data: user, isLoading: loadingUser } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => getUser(userId),
  })

  const { data: reviewsData, isLoading: loadingReviews } = useQuery({
    queryKey: ['reviews', userId],
    queryFn: () => getReviews(userId),
  })

  if (loadingUser) return <Spinner className="mt-20" />

  if (!user)
    return <p className="mt-20 text-center text-gray-500">Пользователь не найден</p>

  const teaching = user.skills?.filter((s) => s.type === 'teaching') ?? []
  const learning = user.skills?.filter((s) => s.type === 'learning') ?? []
  const isOwn = currentUser?.id === userId

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Шапка профиля */}
      <Card>
        <div className="flex items-start gap-4">
          <Avatar name={user.name} src={user.avatar_url} size="lg" />
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-bold text-gray-900">{user.name}</h1>
              <Badge color={ROLE_COLORS[user.role]}>{ROLE_LABELS[user.role]}</Badge>
            </div>
            {reviewsData && reviewsData.count > 0 && (
              <div className="mt-1 flex items-center gap-2">
                <StarRating value={Math.round(reviewsData.average_rating ?? 0)} size="sm" />
                <span className="text-sm text-gray-500">
                  {reviewsData.average_rating?.toFixed(1)} ({reviewsData.count} отзывов)
                </span>
              </div>
            )}
            {user.bio && <p className="mt-2 text-sm text-gray-600">{user.bio}</p>}
          </div>
          {isOwn && (
            <Link to="/profile/edit">
              <Button variant="secondary" size="sm">Редактировать</Button>
            </Link>
          )}
        </div>
      </Card>

      {/* Навыки */}
      {(teaching.length > 0 || learning.length > 0) && (
        <Card>
          <h2 className="mb-3 font-semibold text-gray-900">Навыки</h2>
          {teaching.length > 0 && (
            <div className="mb-3">
              <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-400">Преподаёт</p>
              <div className="flex flex-wrap gap-2">
                {teaching.map((s) => (
                  <Link key={s.skill_id} to={`/skills/${s.skill_id}`}>
                    <Badge color="green">{s.skill_name}</Badge>
                  </Link>
                ))}
              </div>
            </div>
          )}
          {learning.length > 0 && (
            <div>
              <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-400">Изучает</p>
              <div className="flex flex-wrap gap-2">
                {learning.map((s) => (
                  <Link key={s.skill_id} to={`/skills/${s.skill_id}`}>
                    <Badge color="indigo">{s.skill_name}</Badge>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Отзывы */}
      <div>
        <h2 className="mb-3 font-semibold text-gray-900">Отзывы</h2>
        {loadingReviews ? (
          <Spinner />
        ) : reviewsData?.reviews.length === 0 ? (
          <p className="text-sm text-gray-500">Отзывов пока нет</p>
        ) : (
          <div className="space-y-3">
            {reviewsData?.reviews.map((r) => (
              <Card key={r.id}>
                <div className="flex items-center gap-3">
                  <Avatar name={r.reviewer_name} src={r.reviewer_avatar} size="sm" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{r.reviewer_name}</p>
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
    </div>
  )
}
