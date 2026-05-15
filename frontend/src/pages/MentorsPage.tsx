import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getMentors } from '../api/mentors'
import { getSkills } from '../api/skills'
import Avatar from '../components/ui/Avatar'
import Badge from '../components/ui/Badge'
import Card from '../components/ui/Card'
import Spinner from '../components/ui/Spinner'
import StarRating from '../components/ui/StarRating'

export default function MentorsPage() {
  const navigate = useNavigate()
  const [skillId, setSkillId] = useState<number | undefined>()
  const [minRating, setMinRating] = useState(0)

  const { data: mentors, isLoading } = useQuery({
    queryKey: ['mentors', skillId, minRating],
    queryFn: () => getMentors({ skill_id: skillId, min_rating: minRating }),
  })

  const { data: skillsData } = useQuery({
    queryKey: ['skills'],
    queryFn: () => getSkills(),
  })

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Менторы</h1>

      {/* Фильтры */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <select
          value={skillId ?? ''}
          onChange={(e) => setSkillId(e.target.value ? Number(e.target.value) : undefined)}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-primary-500 focus:outline-none"
        >
          <option value="">Все навыки</option>
          {skillsData?.skills.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        <select
          value={minRating}
          onChange={(e) => setMinRating(Number(e.target.value))}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-primary-500 focus:outline-none"
        >
          <option value={0}>Любой рейтинг</option>
          <option value={3}>От 3 звёзд</option>
          <option value={4}>От 4 звёзд</option>
          <option value={4.5}>От 4.5 звёзд</option>
        </select>
      </div>

      {isLoading ? (
        <Spinner className="mt-20" />
      ) : mentors?.length === 0 ? (
        <p className="text-center text-gray-500">Менторы не найдены</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {mentors?.map((m) => (
            <Card key={m.id} onClick={() => navigate(`/mentors/${m.id}`)}>
              <div className="flex gap-3">
                <Avatar name={m.name} src={m.avatar_url} />
                <div className="flex-1 overflow-hidden">
                  <p className="font-semibold text-gray-900">{m.name}</p>
                  {m.average_rating !== null ? (
                    <div className="flex items-center gap-1">
                      <StarRating value={Math.round(m.average_rating)} size="sm" />
                      <span className="text-xs text-gray-400">{m.average_rating?.toFixed(1)}</span>
                    </div>
                  ) : (
                    <p className="text-xs text-gray-400">Нет отзывов</p>
                  )}
                  {m.bio && (
                    <p className="mt-1 text-sm text-gray-500 line-clamp-2">{m.bio}</p>
                  )}
                  <div className="mt-2 flex flex-wrap gap-1">
                    {m.skills.slice(0, 3).map((s) => (
                      <Badge key={s.skill_id} color="indigo">{s.skill_name}</Badge>
                    ))}
                    {m.skills.length > 3 && (
                      <Badge color="gray">+{m.skills.length - 3}</Badge>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
