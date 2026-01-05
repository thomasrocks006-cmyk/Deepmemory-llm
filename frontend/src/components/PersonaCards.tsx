'use client'

import { useQuery } from '@tanstack/react-query'
import { profiles } from '@/lib/api'
import { User, Heart, Target, AlertTriangle, TrendingUp } from 'lucide-react'
import { useState } from 'react'

export default function PersonaCards() {
  const [selectedPerson, setSelectedPerson] = useState<string | null>(null)

  const { data: personaList } = useQuery({
    queryKey: ['personas'],
    queryFn: () => profiles.list(),
    refetchInterval: 30000, // Refresh every 30s
  })

  const { data: selectedPersona } = useQuery({
    queryKey: ['persona', selectedPerson],
    queryFn: () => profiles.get(selectedPerson!),
    enabled: !!selectedPerson,
  })

  return (
    <div className="h-full bg-white dark:bg-gray-800">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <User className="w-5 h-5" />
          Persona Profiles
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Psychological understanding
        </p>
      </div>

      {/* Persona List */}
      <div className="p-4 space-y-2">
        {personaList && personaList.length > 0 ? (
          personaList.map((name: string) => (
            <button
              key={name}
              onClick={() => setSelectedPerson(name === selectedPerson ? null : name)}
              className={`w-full text-left px-4 py-3 rounded-lg transition-all ${
                selectedPerson === name
                  ? 'bg-primary-50 dark:bg-primary-900/20 border-2 border-primary-600'
                  : 'bg-gray-50 dark:bg-gray-700 border-2 border-transparent hover:border-gray-300'
              }`}
            >
              <div className="font-medium text-gray-900 dark:text-white">
                {name}
              </div>
            </button>
          ))
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <User className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No personas yet</p>
            <p className="text-xs mt-1">Upload conversations to build profiles</p>
          </div>
        )}
      </div>

      {/* Selected Persona Details */}
      {selectedPersona && (
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 space-y-4 max-h-96 overflow-y-auto">
          {/* Core Values */}
          {selectedPersona.core_values && selectedPersona.core_values.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Heart className="w-4 h-4 text-red-500" />
                <h3 className="font-semibold text-sm text-gray-900 dark:text-white">
                  Core Values
                </h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {selectedPersona.core_values.map((value: string, idx: number) => (
                  <span
                    key={idx}
                    className="px-2 py-1 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-xs rounded"
                  >
                    {value}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Goals */}
          {selectedPersona.goals && selectedPersona.goals.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-4 h-4 text-green-500" />
                <h3 className="font-semibold text-sm text-gray-900 dark:text-white">
                  Goals & Aspirations
                </h3>
              </div>
              <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
                {selectedPersona.goals.map((goal: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-green-500 mt-1">•</span>
                    <span>{goal}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Fears */}
          {selectedPersona.fears && selectedPersona.fears.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-yellow-500" />
                <h3 className="font-semibold text-sm text-gray-900 dark:text-white">
                  Fears & Concerns
                </h3>
              </div>
              <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
                {selectedPersona.fears.map((fear: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-yellow-500 mt-1">•</span>
                    <span>{fear}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Personality Traits (Big Five) */}
          {selectedPersona.traits && Object.keys(selectedPersona.traits).length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-blue-500" />
                <h3 className="font-semibold text-sm text-gray-900 dark:text-white">
                  Personality Traits
                </h3>
              </div>
              <div className="space-y-2">
                {Object.entries(selectedPersona.traits).map(([trait, value]) => (
                  <div key={trait}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-gray-700 dark:text-gray-300 capitalize">
                        {trait}
                      </span>
                      <span className="text-gray-500">{String(value)}/100</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all"
                        style={{ width: `${value}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Conflicts */}
          {selectedPersona.conflicts && selectedPersona.conflicts.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-orange-500" />
                <h3 className="font-semibold text-sm text-gray-900 dark:text-white">
                  Internal Conflicts
                </h3>
              </div>
              <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
                {selectedPersona.conflicts.map((conflict: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-orange-500 mt-1">•</span>
                    <span>{conflict}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
