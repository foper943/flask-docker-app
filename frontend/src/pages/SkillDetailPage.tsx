import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getSkill } from '../api/skills'
import Avatar from '../components/ui/Avatar'
import Badge from '../components/ui/Badge'
import Card from '../components/ui/Card'
import Spinner from '../components/ui/Spinner'
import StarRating from '../components/ui/StarRating'

export default function SkillDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data, isLoading } = useQuery({
    queryKey: ['skill', Number(id)],
    queryFn: () => getSkill(Number(id)),
  })

  if (isLoading) return <Spinner className="mt-20" />
  if (!data) return <p className="mt-20 text-center text-gray-500">Навык не найден</p>

  const { skill, mentors } = data

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">{skill.name}</h1>
          <Badge color="gray">{skill.category}</Badge>
        </div>
        {skill.description && (
          <p className="mt-2 text-gray-600">{skill.description}</p>
        )}
        <p className="mt-1 text-sm text-gray-400">
          {skill.mentor_count} {skill.mentor_count === 1 ? 'ментор' : 'менторов'}
        </p>
      </div>

      <div>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Менторы по этому навыку</h2>
        {mentors.length === 0 ? (
          <p className="text-gray-500">Менторов пока нет</p>
        ) : (
          <div className="space-y-3">
            {mentors.map((m) => (
              <Card key={m.id} onClick={() => navigate(`/mentors/${m.id}`)}>
                <div className="flex items-center gap-3">
                  <Avatar name={m.name} src={m.avatar_url} />
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{m.name}</p>
                    {m.average_rating && (
                      <div className="flex items-center gap-1">
                        <StarRating value={Math.round(m.average_rating)} size="sm" />
                        <span className="text-xs text-gray-400">
                          {m.average_rating.toFixed(1)} ({m.review_count})
                        </span>
                      </div>
                    )}
                    {m.bio && (
                      <p className="mt-1 text-sm text-gray-500 line-clamp-2">{m.bio}</p>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
