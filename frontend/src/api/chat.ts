import type { ChatMessage, Dialog } from '../types'
import { apiClient } from './client'

export const getDialogs = () =>
  apiClient.get<{ dialogs: Dialog[] }>('/api/chat').then((r) => r.data.dialogs)

export const getMessages = (userId: number) =>
  apiClient
    .get<{ messages: ChatMessage[] }>(`/api/chat/${userId}`)
    .then((r) => r.data.messages)

export const sendMessage = (userId: number, text: string) =>
  apiClient
    .post<{ message: ChatMessage }>(`/api/chat/${userId}`, { text })
    .then((r) => r.data.message)
