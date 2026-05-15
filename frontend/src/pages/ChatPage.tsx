import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { getMessages, sendMessage } from '../api/chat'
import { getUser } from '../api/users'
import { useAuthStore } from '../store/authStore'
import Avatar from '../components/ui/Avatar'
import Spinner from '../components/ui/Spinner'

export default function ChatPage() {
  const { userId } = useParams<{ userId: string }>()
  const otherId = Number(userId)
  const currentUser = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const [text, setText] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  const { data: other } = useQuery({
    queryKey: ['user', otherId],
    queryFn: () => getUser(otherId),
  })

  const { data: messages, isLoading } = useQuery({
    queryKey: ['messages', otherId],
    queryFn: () => getMessages(otherId),
    // Поллинг каждые 3 секунды вместо WebSocket
    refetchInterval: 3000,
  })

  const sendMutation = useMutation({
    mutationFn: (msg: string) => sendMessage(otherId, msg),
    onSuccess: () => {
      setText('')
      qc.invalidateQueries({ queryKey: ['messages', otherId] })
      qc.invalidateQueries({ queryKey: ['dialogs'] })
    },
    onError: () => toast.error('Ошибка отправки сообщения'),
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return
    sendMutation.mutate(text.trim())
  }

  if (isLoading) return <Spinner className="mt-20" />

  return (
    <div className="mx-auto flex h-[calc(100vh-140px)] max-w-2xl flex-col">
      {/* Шапка */}
      <div className="flex items-center gap-3 rounded-t-xl border border-b-0 border-gray-200 bg-white p-4">
        {other && <Avatar name={other.name} src={other.avatar_url} />}
        <p className="font-semibold text-gray-900">{other?.name ?? '...'}</p>
      </div>

      {/* Сообщения */}
      <div className="flex-1 overflow-y-auto border border-gray-200 bg-gray-50 p-4">
        {messages?.length === 0 ? (
          <p className="text-center text-sm text-gray-400">Начните диалог</p>
        ) : (
          <div className="space-y-3">
            {messages?.map((msg) => {
              const isOwn = msg.sender_id === currentUser?.id
              return (
                <div key={msg.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[75%] rounded-2xl px-4 py-2 text-sm ${
                      isOwn
                        ? 'rounded-tr-sm bg-primary-600 text-white'
                        : 'rounded-tl-sm bg-white text-gray-800 shadow-sm'
                    }`}
                  >
                    <p>{msg.text}</p>
                    <p className={`mt-1 text-xs ${isOwn ? 'text-primary-200' : 'text-gray-400'}`}>
                      {new Date(msg.created_at).toLocaleTimeString('ru-RU', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                </div>
              )
            })}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Ввод */}
      <form
        onSubmit={handleSubmit}
        className="flex gap-2 rounded-b-xl border border-t-0 border-gray-200 bg-white p-3"
      >
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Введите сообщение..."
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        />
        <button
          type="submit"
          disabled={!text.trim() || sendMutation.isPending}
          className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
        >
          →
        </button>
      </form>
    </div>
  )
}
