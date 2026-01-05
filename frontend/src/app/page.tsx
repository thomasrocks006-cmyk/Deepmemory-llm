'use client'

import ChatInterface from '@/components/ChatInterface'
import FolderManager from '@/components/FolderManager'
import MemoryPanel from '@/components/MemoryPanel'
import PersonaCards from '@/components/PersonaCards'
import { useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'

export default function Home() {
  const [showFolderManager, setShowFolderManager] = useState(false)
  const [uploadNotification, setUploadNotification] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const handleUploadSuccess = useCallback(() => {
    // Invalidate and refetch memory stats and personas
    queryClient.invalidateQueries({ queryKey: ['memory-stats'] })
    queryClient.invalidateQueries({ queryKey: ['personas'] })
    
    // Show notification
    setUploadNotification('Conversations uploaded successfully!')
    setTimeout(() => setUploadNotification(null), 5000)
  }, [queryClient])

  return (
    <main className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Upload Success Notification */}
      {uploadNotification && (
        <div className="fixed top-4 right-4 z-50 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg animate-bounce">
          ✓ {uploadNotification}
        </div>
      )}

      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              DeepMemory LLM
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Infinite context • Psychological profiling • Lateral thinking
            </p>
          </div>
          <button
            onClick={() => setShowFolderManager(!showFolderManager)}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            {showFolderManager ? 'Hide' : 'Upload'} Conversations
          </button>
        </div>
      </header>

      {/* Folder Manager Modal */}
      {showFolderManager && (
        <FolderManager 
          onClose={() => setShowFolderManager(false)} 
          onUploadSuccess={handleUploadSuccess}
        />
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Persona Cards */}
        <aside className="w-80 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
          <PersonaCards />
        </aside>

        {/* Center - Chat Interface */}
        <div className="flex-1 flex flex-col">
          <ChatInterface />
        </div>

        {/* Right Sidebar - Memory Panel */}
        <aside className="w-96 border-l border-gray-200 dark:border-gray-700 overflow-y-auto">
          <MemoryPanel />
        </aside>
      </div>
    </main>
  )
}
