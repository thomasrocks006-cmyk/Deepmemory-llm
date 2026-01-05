'use client'

import { useState, useRef, useEffect } from 'react'
import { useChatStore } from '@/store/chat'
import { chat } from '@/lib/api'
import { Send, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { formatDistanceToNow } from 'date-fns'

export default function ChatInterface() {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { messages, conversationId, isLoading, addMessage, setLoading, setConversationId } = useChatStore()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = { role: 'user' as const, content: input }
    addMessage(userMessage)
    setInput('')
    setLoading(true)

    try {
      const response = await chat.send(input, conversationId || undefined)
      
      // Update conversation ID if new
      if (!conversationId && response) {
        // In a real implementation, the backend would return the conversation_id
        // For now, we generate one
        setConversationId(Date.now().toString())
      }

      addMessage(response)
    } catch (error) {
      console.error('Chat error:', error)
      addMessage({
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-800">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-4">
              <h2 className="text-2xl font-semibold text-gray-700 dark:text-gray-300">
                Start a conversation
              </h2>
              <p className="text-gray-500 dark:text-gray-400">
                Your AI remembers everything and understands you deeply
              </p>
            </div>
          </div>
        ) : (
          messages.map((message: any, index: number) => (
            <div
              key={index}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-3xl rounded-lg px-6 py-4 ${
                  message.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                }`}
              >
                {/* Thinking Process (if available) */}
                {message.thinking && (
                  <details className="mb-4 opacity-70">
                    <summary className="cursor-pointer text-sm font-semibold mb-2">
                      💭 Thinking Process
                    </summary>
                    <div className="text-sm italic whitespace-pre-wrap">
                      {message.thinking}
                    </div>
                  </details>
                )}

                {/* Main Content */}
                <div className="markdown-content">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                </div>

                {/* Sources (if available) */}
                {message.sources && message.sources.length > 0 && (
                  <details className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
                    <summary className="cursor-pointer text-sm font-semibold mb-2">
                      📚 Sources ({message.sources.length})
                    </summary>
                    <div className="space-y-2 text-sm">
                      {message.sources.slice(0, 5).map((source: any, idx: number) => (
                        <div
                          key={idx}
                          className="p-2 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-600"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-semibold text-primary-600 dark:text-primary-400">
                              {source.type.toUpperCase()}
                            </span>
                            <span className="text-xs text-gray-500">
                              {(source.similarity * 100).toFixed(0)}% match
                            </span>
                          </div>
                          <p className="text-xs line-clamp-2">{source.content}</p>
                          {source.timestamp && (
                            <p className="text-xs text-gray-400 mt-1">
                              {formatDistanceToNow(new Date(source.timestamp), { addSuffix: true })}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-3xl rounded-lg px-6 py-4 bg-gray-100 dark:bg-gray-700">
              <Loader2 className="w-5 h-5 animate-spin text-primary-600" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-4xl mx-auto flex items-end gap-4">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything... I remember our entire history"
            className="flex-1 resize-none rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-3 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
            rows={3}
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <Send className="w-5 h-5" />
                Send
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
