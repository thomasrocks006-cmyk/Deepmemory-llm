"use client"

import { useState } from 'react'
import { AlertTriangle, CheckCircle, XCircle, Info, Loader2 } from 'lucide-react'

interface Discrepancy {
  type: 'self_contradiction' | 'cross_contradiction' | 'hallucination' | 'ambiguity'
  severity: 'minor' | 'moderate' | 'critical'
  location: {
    document_id: string
    section?: string
    excerpt: string
  }
  conflict_with?: {
    document_id: string
    excerpt: string
  }
  explanation: string
  suggested_resolution?: string
  requires_user_input: boolean
}

interface ValidationReport {
  summary: {
    total_issues: number
    critical: number
    moderate: number
    minor: number
    requires_user_action: number
  }
  by_severity: {
    critical: Discrepancy[]
    moderate: Discrepancy[]
    minor: Discrepancy[]
  }
  action_required: Discrepancy[]
  all_discrepancies: Discrepancy[]
}

interface Document {
  id: string
  content: string
  metadata?: Record<string, any>
}

export default function ValidationPanel({
  documents,
  onValidationComplete
}: {
  documents: Document[]
  onValidationComplete?: (report: ValidationReport) => void
}) {
  const [isValidating, setIsValidating] = useState(false)
  const [report, setReport] = useState<ValidationReport | null>(null)
  const [selectedDiscrepancy, setSelectedDiscrepancy] = useState<Discrepancy | null>(null)

  const handleValidate = async () => {
    setIsValidating(true)
    setReport(null)

    try {
      const response = await fetch('/api/validate/documents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          documents,
          check_against_existing: true
        })
      })

      const data = await response.json()
      
      if (data.status === 'success') {
        setReport(data.report)
        onValidationComplete?.(data.report)
      }
    } catch (error) {
      console.error('Validation error:', error)
    } finally {
      setIsValidating(false)
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'moderate':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />
      case 'minor':
        return <Info className="w-5 h-5 text-blue-500" />
      default:
        return <Info className="w-5 h-5 text-gray-500" />
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-50 border-red-200'
      case 'moderate':
        return 'bg-yellow-50 border-yellow-200'
      case 'minor':
        return 'bg-blue-50 border-blue-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  return (
    <div className="space-y-4">
      {/* Validation Button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Document Validation</h2>
          <p className="text-gray-600 mt-1">
            Check for contradictions, hallucinations, and discrepancies
          </p>
        </div>
        <button
          onClick={handleValidate}
          disabled={isValidating || documents.length === 0}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
        >
          {isValidating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Checking...
            </>
          ) : (
            <>
              <AlertTriangle className="w-5 h-5" />
              Check for Discrepancies
            </>
          )}
        </button>
      </div>

      {/* Validation Report */}
      {report && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-white border-2 border-gray-200 rounded-lg p-4">
              <div className="text-sm text-gray-600">Total Issues</div>
              <div className="text-3xl font-bold mt-1">{report.summary.total_issues}</div>
            </div>
            <div className="bg-white border-2 border-red-200 rounded-lg p-4">
              <div className="text-sm text-red-600">Critical</div>
              <div className="text-3xl font-bold text-red-600 mt-1">{report.summary.critical}</div>
            </div>
            <div className="bg-white border-2 border-yellow-200 rounded-lg p-4">
              <div className="text-sm text-yellow-600">Moderate</div>
              <div className="text-3xl font-bold text-yellow-600 mt-1">{report.summary.moderate}</div>
            </div>
            <div className="bg-white border-2 border-blue-200 rounded-lg p-4">
              <div className="text-sm text-blue-600">Minor</div>
              <div className="text-3xl font-bold text-blue-600 mt-1">{report.summary.minor}</div>
            </div>
          </div>

          {/* No Issues Found */}
          {report.summary.total_issues === 0 && (
            <div className="bg-green-50 border-2 border-green-200 rounded-lg p-6 flex items-center gap-3">
              <CheckCircle className="w-6 h-6 text-green-600" />
              <div>
                <div className="font-semibold text-green-900">No discrepancies found!</div>
                <div className="text-green-700 text-sm mt-1">
                  All documents are internally consistent and don't conflict with existing data.
                </div>
              </div>
            </div>
          )}

          {/* Critical Issues */}
          {report.summary.critical > 0 && (
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-red-700 flex items-center gap-2">
                <XCircle className="w-5 h-5" />
                Critical Issues ({report.summary.critical})
              </h3>
              {report.by_severity.critical.map((issue, idx) => (
                <DiscrepancyCard
                  key={idx}
                  discrepancy={issue}
                  onClick={() => setSelectedDiscrepancy(issue)}
                  isSelected={selectedDiscrepancy === issue}
                />
              ))}
            </div>
          )}

          {/* Moderate Issues */}
          {report.summary.moderate > 0 && (
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-yellow-700 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                Moderate Issues ({report.summary.moderate})
              </h3>
              {report.by_severity.moderate.map((issue, idx) => (
                <DiscrepancyCard
                  key={idx}
                  discrepancy={issue}
                  onClick={() => setSelectedDiscrepancy(issue)}
                  isSelected={selectedDiscrepancy === issue}
                />
              ))}
            </div>
          )}

          {/* Minor Issues */}
          {report.summary.minor > 0 && (
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-blue-700 flex items-center gap-2">
                <Info className="w-5 h-5" />
                Minor Issues ({report.summary.minor})
              </h3>
              {report.by_severity.minor.map((issue, idx) => (
                <DiscrepancyCard
                  key={idx}
                  discrepancy={issue}
                  onClick={() => setSelectedDiscrepancy(issue)}
                  isSelected={selectedDiscrepancy === issue}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Selected Discrepancy Detail Modal */}
      {selectedDiscrepancy && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-2">
                {getSeverityIcon(selectedDiscrepancy.severity)}
                <h3 className="text-xl font-bold capitalize">
                  {selectedDiscrepancy.severity} {selectedDiscrepancy.type.replace('_', ' ')}
                </h3>
              </div>
              <button
                onClick={() => setSelectedDiscrepancy(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <div className="font-semibold text-sm text-gray-600 mb-1">Location</div>
                <div className="bg-gray-50 p-3 rounded border text-sm">
                  <div className="font-mono text-xs text-gray-500 mb-1">
                    {selectedDiscrepancy.location.document_id}
                    {selectedDiscrepancy.location.section && ` - ${selectedDiscrepancy.location.section}`}
                  </div>
                  <div className="text-gray-900">{selectedDiscrepancy.location.excerpt}</div>
                </div>
              </div>

              {selectedDiscrepancy.conflict_with && (
                <div>
                  <div className="font-semibold text-sm text-gray-600 mb-1">Conflicts With</div>
                  <div className="bg-red-50 p-3 rounded border border-red-200 text-sm">
                    <div className="font-mono text-xs text-red-600 mb-1">
                      {selectedDiscrepancy.conflict_with.document_id}
                    </div>
                    <div className="text-gray-900">{selectedDiscrepancy.conflict_with.excerpt}</div>
                  </div>
                </div>
              )}

              <div>
                <div className="font-semibold text-sm text-gray-600 mb-1">Explanation</div>
                <div className="bg-blue-50 p-3 rounded border border-blue-200 text-sm">
                  {selectedDiscrepancy.explanation}
                </div>
              </div>

              {selectedDiscrepancy.suggested_resolution && (
                <div>
                  <div className="font-semibold text-sm text-gray-600 mb-1">Suggested Resolution</div>
                  <div className="bg-green-50 p-3 rounded border border-green-200 text-sm">
                    {selectedDiscrepancy.suggested_resolution}
                  </div>
                </div>
              )}

              {selectedDiscrepancy.requires_user_input && (
                <div className="bg-yellow-50 border border-yellow-200 p-4 rounded">
                  <div className="font-semibold text-yellow-900 mb-2">Action Required</div>
                  <div className="text-sm text-yellow-800">
                    This discrepancy requires your input to resolve. Please review and provide clarification.
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function DiscrepancyCard({
  discrepancy,
  onClick,
  isSelected
}: {
  discrepancy: Discrepancy
  onClick: () => void
  isSelected: boolean
}) {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-50 border-red-200 hover:bg-red-100'
      case 'moderate':
        return 'bg-yellow-50 border-yellow-200 hover:bg-yellow-100'
      case 'minor':
        return 'bg-blue-50 border-blue-200 hover:bg-blue-100'
      default:
        return 'bg-gray-50 border-gray-200 hover:bg-gray-100'
    }
  }

  return (
    <button
      onClick={onClick}
      className={`w-full text-left border-2 rounded-lg p-4 transition-all ${getSeverityColor(
        discrepancy.severity
      )} ${isSelected ? 'ring-2 ring-blue-500' : ''}`}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          {discrepancy.severity === 'critical' && <XCircle className="w-5 h-5 text-red-500" />}
          {discrepancy.severity === 'moderate' && <AlertTriangle className="w-5 h-5 text-yellow-500" />}
          {discrepancy.severity === 'minor' && <Info className="w-5 h-5 text-blue-500" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold capitalize mb-1">
            {discrepancy.type.replace('_', ' ')}
          </div>
          <div className="text-sm text-gray-700 mb-2 line-clamp-2">
            {discrepancy.explanation}
          </div>
          <div className="text-xs text-gray-500 font-mono">
            {discrepancy.location.document_id}
            {discrepancy.location.section && ` - ${discrepancy.location.section}`}
          </div>
          {discrepancy.requires_user_input && (
            <div className="mt-2 inline-block text-xs bg-yellow-200 text-yellow-900 px-2 py-1 rounded">
              Action Required
            </div>
          )}
        </div>
      </div>
    </button>
  )
}
