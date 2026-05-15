import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getDialogs } from '../api/chat'
import Avatar from '../components/ui/Avatar'
import Spinner from '../components/ui/Spinner'

export default function MessagesPage() {
  const navigate = useNavigate()

  const { data: dialogs, isLoading } = useQuery({
    queryKey: ['dialogs'],
    queryFn: getDialogs,
    refetchInterval: 3000,
  })

  if (isLoading) return <Spinner className="mt-20" />

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Сообщения</h1>

      {dialogs?.length === 0 ? (
        <p className="text-center text-gray-500">Нет диалогов</p>
      ) : (
        <div className="divide-y divide-gray-100 rounded-xl border border-gray-200 bg-white">
          {dialogs?.map((d) => (
            <button
              key={d.user_id}
              onClick={() => navigate(`/messages/${d.user_id}`)}
              className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-gray-50"
            >
              <div className="relative">
                <Avatar name={d.user_name} src={d.user_avatar} />
                {d.unread_count > 0 && (
                  <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">
                    {d.unread_count > 9 ? '9+' : d.unread_count}
                  </span>
                )}
              </div>
              <div className="flex-1 overflow-hidden">
                <div className="flex items-baseline justify-between">
                  <p className={`text-sm font-medium ${d.unread_count > 0 ? 'text-gray-900' : 'text-gray-700'}`}>
                    {d.user_name}
                  </p>
                  <p className="text-xs text-gray-400">
                    {new Date(d.last_message_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                <p className={`truncate text-sm ${d.unread_count > 0 ? 'font-medium text-gray-800' : 'text-gray-500'}`}>
                  {d.last_message}
                </p>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
