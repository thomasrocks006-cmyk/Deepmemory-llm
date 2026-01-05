'use client'

import { useQuery } from '@tanstack/react-query'
import { memory, conversations } from '@/lib/api'
import { Database, Layers, Activity, MessageSquare, Clock } from 'lucide-react'

export default function MemoryPanel() {
  const { data: stats } = useQuery({
    queryKey: ['memory-stats'],
    queryFn: () => memory.getStats(),
    refetchInterval: 10000, // Refresh every 10s
  })

  const { data: convData } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => conversations.list(10),
    refetchInterval: 10000, // Refresh every 10s
  })

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Unknown'
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="h-full bg-white dark:bg-gray-800">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <Database className="w-5 h-5" />
          Memory System
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Multi-tier context management
        </p>
      </div>

      <div className="p-4 space-y-6">
        {/* Overall Stats */}
        <div className="grid grid-cols-1 gap-4">
          <StatCard
            label="Total Conversations"
            value={stats?.total_conversations || 0}
            icon={<Activity className="w-5 h-5" />}
            color="blue"
          />
          <StatCard
            label="Total Messages"
            value={stats?.total_messages || 0}
            icon={<Database className="w-5 h-5" />}
            color="green"
          />
          <StatCard
            label="Personas"
            value={stats?.total_personas || 0}
            icon={<Database className="w-5 h-5" />}
            color="purple"
          />
        </div>

        {/* Memory Tiers */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Layers className="w-5 h-5 text-gray-700 dark:text-gray-300" />
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Memory Tiers
            </h3>
          </div>

          <div className="space-y-3">
            {/* Tier 1 - Active Context */}
            <TierCard
              tier={1}
              label="Active Context"
              description="Last 100k tokens"
              size={stats?.memory_tiers?.tier1_size || 0}
              maxSize={100000}
              color="emerald"
            />

            {/* Tier 2 - Cached Context */}
            <TierCard
              tier={2}
              label="Cached Context"
              description="Up to 1M tokens"
              size={stats?.memory_tiers?.tier2_size || 0}
              maxSize={1000000}
              color="blue"
            />

            {/* Tier 3 - Long-term */}
            <TierCard
              tier={3}
              label="Long-term Memory"
              description="Vector + Graph"
              size={stats?.memory_tiers?.tier3_size || 0}
              maxSize={null}
              color="purple"
            />
          </div>
        </div>

        {/* Recent Conversations */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <MessageSquare className="w-5 h-5 text-gray-700 dark:text-gray-300" />
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Uploaded Conversations
            </h3>
          </div>
          
          {convData?.conversations && convData.conversations.length > 0 ? (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {convData.conversations.map((conv) => (
                <div 
                  key={conv.id} 
                  className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {conv.title}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                          {conv.source}
                        </span>
                        <span className="text-xs text-gray-500">
                          {conv.total_messages} msgs
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center text-xs text-gray-400 ml-2">
                      <Clock className="w-3 h-3 mr-1" />
                      {formatDate(conv.ingestion_date)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6 bg-gray-50 dark:bg-gray-900 rounded-lg">
              <MessageSquare className="w-8 h-8 mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-gray-500 dark:text-gray-400">No conversations uploaded yet</p>
              <p className="text-xs text-gray-400 mt-1">Click "Upload Conversations" to get started</p>
            </div>
          )}
        </div>

        {/* Memory Features */}
        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
          <h3 className="font-semibold text-sm text-gray-900 dark:text-white mb-3">
            Active Features
          </h3>
          <div className="space-y-2 text-sm">
            <Feature label="Multi-vector Search" active />
            <Feature label="Knowledge Graph" active />
            <Feature label="Coreference Resolution" active />
            <Feature label="Psychological Profiling" active />
            <Feature label="Context Caching" active />
            <Feature label="Lateral Thinking" active />
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  icon,
  color,
}: {
  label: string
  value: number
  icon: React.ReactNode
  color: string
}) {
  const colorClasses = {
    blue: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
    green: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400',
    purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400',
  }

  return (
    <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            {value.toLocaleString()}
          </p>
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color as keyof typeof colorClasses]}`}>
          {icon}
        </div>
      </div>
    </div>
  )
}

function TierCard({
  tier,
  label,
  description,
  size,
  maxSize,
  color,
}: {
  tier: number
  label: string
  description: string
  size: number
  maxSize: number | null
  color: string
}) {
  const percentage = maxSize ? Math.min((size / maxSize) * 100, 100) : 0
  
  const colorClasses = {
    emerald: 'bg-emerald-500',
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
  }

  return (
    <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <div>
          <p className="text-sm font-semibold text-gray-900 dark:text-white">
            L{tier}: {label}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {description}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm font-medium text-gray-900 dark:text-white">
            {size.toLocaleString()}
          </p>
          {maxSize && (
            <p className="text-xs text-gray-500">
              {percentage.toFixed(0)}%
            </p>
          )}
        </div>
      </div>
      {maxSize && (
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${colorClasses[color as keyof typeof colorClasses]}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}
    </div>
  )
}

function Feature({ label, active }: { label: string; active: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={`w-2 h-2 rounded-full ${
          active ? 'bg-green-500 animate-pulse-slow' : 'bg-gray-300'
        }`}
      />
      <span className="text-gray-700 dark:text-gray-300">{label}</span>
    </div>
  )
}
