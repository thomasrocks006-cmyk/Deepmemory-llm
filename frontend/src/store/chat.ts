import { create } from 'zustand'
import { Message } from '@/lib/api'

interface ChatState {
  messages: Message[]
  conversationId: string | null
  isLoading: boolean
  addMessage: (message: Message) => void
  setLoading: (loading: boolean) => void
  setConversationId: (id: string) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  conversationId: null,
  isLoading: false,
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message],
  })),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  setConversationId: (id) => set({ conversationId: id }),
  
  clearMessages: () => set({ messages: [], conversationId: null }),
}))
