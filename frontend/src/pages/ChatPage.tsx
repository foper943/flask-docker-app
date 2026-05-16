import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { io, Socket } from 'socket.io-client'
import { getMessages } from '../api/chat'
import { getUser } from '../api/users'
import { useAuthStore } from '../store/authStore'
import Avatar from '../components/ui/Avatar'
import Spinner from '../components/ui/Spinner'
import type { ChatMessage } from '../types'

const WS_URL = import.meta.env.VITE_WS_URL ?? ''

export default function ChatPage() {
  const { userId } = useParams<{ userId: string }>()
  const otherId = Number(userId)
  const currentUser = useAuthStore((s) => s.user)
  const token = useAuthStore((s) => s.token)
  const qc = useQueryClient()
  const [text, setText] = useState('')
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([])
  const [connected, setConnected] = useState(false)
  const socketRef = useRef<Socket | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  const { data: other } = useQuery({
    queryKey: ['user', otherId],
    queryFn: () => getUser(otherId),
  })

  // Загружаем историю один раз при открытии
  const { data: history, isLoading } = useQuery({
    queryKey: ['messages', otherId],
    queryFn: () => getMessages(otherId),
  })

  useEffect(() => {
    if (history) setLocalMessages(history)
  }, [history])

  // WebSocket-соединение
  useEffect(() => {
    const socket = io(WS_URL, {
      auth: { token },
      transports: ['websocket'],
    })
    socketRef.current = socket

    socket.on('connect', () => setConnected(true))
    socket.on('disconnect', () => setConnected(false))
    socket.on('connect_error', () => {
      toast.error('Нет соединения с сервером')
      setConnected(false)
    })

    socket.on('new_message', (msg: ChatMessage) => {
      const isRelevant =
        (msg.sender_id === currentUser?.id && msg.receiver_id === otherId) ||
        (msg.sender_id === otherId && msg.receiver_id === currentUser?.id)

      if (isRelevant) {
        setLocalMessages((prev) => {
          if (prev.find((m) => m.id === msg.id)) return prev
          return [...prev, msg]
        })
        qc.invalidateQueries({ queryKey: ['dialogs'] })
      }
    })

    socket.on('error', (err: { message: string }) => {
      toast.error(err.message ?? 'Ошибка WebSocket')
    })

    return () => {
      socket.disconnect()
    }
  }, [token, otherId, currentUser?.id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [localMessages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = text.trim()
    if (!trimmed || !socketRef.current) return

    socketRef.current.emit('send_message', {
      token,
      receiver_id: otherId,
      text: trimmed,
    })
    setText('')
  }

  if (isLoading) return <Spinner className="mt-20" />

  return (
    <div className="mx-auto flex h-[calc(100vh-140px)] max-w-2xl flex-col">
      {/* Шапка */}
      <div className="flex items-center gap-3 rounded-t-xl border border-b-0 border-gray-200 bg-white p-4">
        {other && <Avatar name={other.name} src={other.avatar_url} />}
        <div className="flex-1">
          <p className="font-semibold text-gray-900">{other?.name ?? '...'}</p>
        </div>
        <span
          className={`h-2 w-2 rounded-full ${connected ? 'bg-green-500' : 'bg-gray-400'}`}
          title={connected ? 'Соединение активно' : 'Нет соединения'}
        />
      </div>

      {/* Сообщения */}
      <div className="flex-1 overflow-y-auto border border-gray-200 bg-gray-50 p-4">
        {localMessages.length === 0 ? (
          <p className="text-center text-sm text-gray-400">Начните диалог</p>
        ) : (
          <div className="space-y-3">
            {localMessages.map((msg) => {
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
          disabled={!text.trim() || !connected}
          className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
        >
          →
        </button>
      </form>
    </div>
  )
}
