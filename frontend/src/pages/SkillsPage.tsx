import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getSkills } from '../api/skills'
import { useDebounce } from '../hooks/useDebounce'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Spinner from '../components/ui/Spinner'

export default function SkillsPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const debouncedSearch = useDebounce(search, 300)

  const { data, isLoading } = useQuery({
    queryKey: ['skills', debouncedSearch, category],
    queryFn: () => getSkills(debouncedSearch, category),
  })

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Каталог навыков</h1>

      {/* Фильтры */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <input
          placeholder="Поиск навыка..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        />
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        >
          <option value="">Все категории</option>
          {data?.categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <Spinner className="mt-20" />
      ) : data?.skills.length === 0 ? (
        <p className="text-center text-gray-500">Навыки не найдены</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data?.skills.map((skill) => (
            <Card key={skill.id} onClick={() => navigate(`/skills/${skill.id}`)}>
              <div className="mb-2 flex items-start justify-between">
                <h3 className="font-semibold text-gray-900">{skill.name}</h3>
                <Badge color="gray">{skill.category}</Badge>
              </div>
              {skill.description && (
                <p className="mb-3 text-sm text-gray-500 line-clamp-2">{skill.description}</p>
              )}
              <p className="text-sm text-primary-600">
                {skill.mentor_count} {skill.mentor_count === 1 ? 'ментор' : 'менторов'}
              </p>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
