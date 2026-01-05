'use client'

import { useState } from 'react'
import { ingest } from '@/lib/api'
import { Upload, X, FileText, Loader2, CheckCircle } from 'lucide-react'

interface FolderManagerProps {
  onClose: () => void
  onUploadSuccess?: () => void
}

export default function FolderManager({ onClose, onUploadSuccess }: FolderManagerProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [source, setSource] = useState<'chatgpt' | 'gemini' | 'grok' | 'text' | 'manual'>('chatgpt')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [manualText, setManualText] = useState('')
  const [uploadResult, setUploadResult] = useState<any>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setUploadSuccess(false)
      setError(null)
    }
  }

  const handleSourceChange = (newSource: 'chatgpt' | 'gemini' | 'grok' | 'text' | 'manual') => {
    setSource(newSource)
    setSelectedFile(null)
    setManualText('')
    setError(null)
    setUploadSuccess(false)
  }

  const handleUpload = async () => {
    if (source === 'manual' && !manualText.trim()) {
      setError('Please enter conversation text')
      return
    }
    if (source !== 'manual' && !selectedFile) {
      setError('Please select a file')
      return
    }

    setIsUploading(true)
    setError(null)

    try {
      let result;
      if (source === 'manual') {
        // Create a file from the manual text
        const blob = new Blob([manualText], { type: 'text/plain' })
        const file = new File([blob], 'manual-conversation.txt', { type: 'text/plain' })
        result = await ingest.upload({ file })
      } else {
        // Upload selected file
        result = await ingest.upload({ file: selectedFile! })
      }
      setUploadResult(result)
      setUploadSuccess(true)
      
      // Trigger haptic feedback if available
      if (navigator.vibrate) {
        navigator.vibrate([100, 50, 100])
      }
      
      // Notify parent to refresh data
      if (onUploadSuccess) {
        onUploadSuccess()
      }
      
      setTimeout(() => {
        onClose()
      }, 3000) // Give more time to see the result
    } catch (err: any) {
      console.error('Upload error:', err)
      const errorMsg = err.response?.data?.detail || err.message || 'Upload failed. Please try again.'
      setError(errorMsg)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Upload Conversations
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Source Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Conversation Source
            </label>
            <div className="grid grid-cols-3 gap-3">
              {[{id: 'chatgpt', label: 'ChatGPT'}, {id: 'gemini', label: 'Gemini'}, {id: 'grok', label: 'Grok'}].map((type) => (
                <button
                  key={type.id}
                  onClick={() => handleSourceChange(type.id as any)}
                  className={`px-3 py-2 rounded-lg border-2 transition-all ${
                    source === type.id
                      ? 'border-primary-600 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="text-sm font-medium">
                    {type.label}
                  </span>
                </button>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-3 mt-3">
              {[{id: 'text', label: 'Text File'}, {id: 'manual', label: 'Paste Text'}].map((type) => (
                <button
                  key={type.id}
                  onClick={() => handleSourceChange(type.id as any)}
                  className={`px-3 py-2 rounded-lg border-2 transition-all ${
                    source === type.id
                      ? 'border-primary-600 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="text-sm font-medium">
                    {type.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* File Upload or Manual Text Input */}
          {source === 'manual' ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Paste Conversation Text
              </label>
              <textarea
                value={manualText}
                onChange={(e) => setManualText(e.target.value)}
                placeholder="Paste your conversation here...&#10;&#10;Format example:&#10;User: Hello, how are you?&#10;Assistant: I'm doing well, thank you!&#10;&#10;User: What's the weather like?&#10;Assistant: I can help you check the weather..."
                className="w-full h-64 px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-600 focus:border-transparent resize-none font-mono text-sm"
              />
              <p className="text-xs text-gray-500 mt-2">
                {manualText.length} characters • Will be processed as a conversation
              </p>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Select File
              </label>
              <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center relative">
                {selectedFile ? (
                  <div className="flex items-center justify-center gap-3">
                    <FileText className="w-8 h-8 text-primary-600" />
                    <div className="text-left">
                      <p className="font-medium text-gray-900 dark:text-white">
                        {selectedFile.name}
                      </p>
                      <p className="text-sm text-gray-500">
                        {(selectedFile.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                ) : (
                  <div>
                    <Upload className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                    <p className="text-gray-600 dark:text-gray-400">
                      Click to upload or drag and drop
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      JSON, ZIP, or TXT files
                    </p>
                  </div>
                )}
                <input
                  type="file"
                  onChange={handleFileChange}
                  accept=".json,.zip,.txt"
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
              </div>
            </div>
          )}

          {/* Instructions */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
            <h3 className="font-medium text-blue-900 dark:text-blue-300 mb-2">
              Export Instructions
            </h3>
            <ul className="text-sm text-blue-800 dark:text-blue-400 space-y-1">
              {source === 'chatgpt' && (
                <>
                  <li>• Go to ChatGPT Settings → Data Controls</li>
                  <li>• Click "Export data"</li>
                  <li>• Upload the conversations.json file</li>
                </>
              )}
              {source === 'gemini' && (
                <>
                  <li>• Go to Google Takeout</li>
                  <li>• Select "Gemini Apps Activity"</li>
                  <li>• Upload the exported ZIP or JSON</li>
                </>
              )}
              {source === 'grok' && (
                <>
                  <li>• Go to Grok Settings or Profile</li>
                  <li>• Export your conversation history</li>
                  <li>• Upload the exported file</li>
                </>
              )}
              {source === 'text' && (
                <>
                  <li>• Upload any text file (.txt) with conversations</li>
                  <li>• System will auto-detect conversation format</li>
                  <li>• Supports various transcript formats</li>
                </>
              )}
              {source === 'manual' && (
                <>
                  <li>• Paste your conversation in the text area above</li>
                  <li>• Format: "User: message" then "Assistant: response"</li>
                  <li>• Separate exchanges with blank lines</li>
                  <li>• Click Upload to process the conversation</li>
                </>
              )}
            </ul>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <p className="text-red-800 dark:text-red-300">{error}</p>
            </div>
          )}

          {/* Success */}
          {uploadSuccess && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 animate-pulse">
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle className="w-6 h-6 text-green-600" />
                <p className="text-lg font-semibold text-green-800 dark:text-green-300">
                  Upload Successful!
                </p>
              </div>
              {uploadResult && (
                <div className="mt-3 pl-9 space-y-1 text-sm text-green-700 dark:text-green-400">
                  <p>✓ Files processed: {uploadResult.files_processed || 1}</p>
                  {uploadResult.reports?.map((report: any, idx: number) => (
                    <div key={idx} className="mt-2 p-2 bg-green-100 dark:bg-green-900/30 rounded">
                      <p>• Conversations: {report.conversations_imported || 0}</p>
                      <p>• Messages: {report.messages_imported || 0}</p>
                      <p>• Entities: {report.entities_extracted || 0}</p>
                    </div>
                  ))}
                </div>
              )}
              <p className="mt-3 text-xs text-green-600 dark:text-green-500 pl-9">
                Closing in 3 seconds...
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={(source === 'manual' ? !manualText.trim() : !selectedFile) || isUploading || uploadSuccess}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Uploading...
              </>
            ) : (
              'Upload'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
