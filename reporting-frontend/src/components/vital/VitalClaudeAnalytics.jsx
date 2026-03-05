import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { apiUrl } from '@/lib/api'
import {
  Brain,
  Sparkles,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  Lightbulb,
  ShieldAlert,
  MessageSquare,
  Send,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'

// ---------------------------------------------------------------------------
// Helper – authenticated POST to a VITAL Claude endpoint
// ---------------------------------------------------------------------------
async function claudePost(path, body) {
  const token = localStorage.getItem('token')
  const res = await fetch(apiUrl(path), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.error || `Request failed (${res.status})`)
  }
  return res.json()
}

// ---------------------------------------------------------------------------
// InsightCard – renders a single structured insight block
// ---------------------------------------------------------------------------
function InsightCard({ insights }) {
  if (!insights) return null

  // If Claude returned raw text instead of structured JSON
  if (insights.raw) {
    return (
      <Card className="mt-4 border-purple-200 bg-purple-50">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-purple-800 flex items-center gap-2">
            <Brain className="h-4 w-4" /> Claude Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-700 whitespace-pre-wrap">{insights.raw}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4 mt-4">
      {/* Summary */}
      {insights.summary && (
        <Card className="border-purple-200 bg-purple-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-purple-800 flex items-center gap-2">
              <Brain className="h-4 w-4" /> Executive Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-700">{insights.summary}</p>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Key Findings */}
        {insights.key_findings?.length > 0 && (
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold text-blue-800 flex items-center gap-2">
                <TrendingUp className="h-4 w-4" /> Key Findings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-1">
                {insights.key_findings.map((f, i) => (
                  <li key={i} className="text-sm text-gray-700 flex gap-2">
                    <CheckCircle className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Trends */}
        {insights.trends?.length > 0 && (
          <Card className="border-green-200 bg-green-50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold text-green-800 flex items-center gap-2">
                <Sparkles className="h-4 w-4" /> Trends
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-1">
                {insights.trends.map((t, i) => (
                  <li key={i} className="text-sm text-gray-700 flex gap-2">
                    <TrendingUp className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                    <span>{t}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Recommendations */}
        {insights.recommendations?.length > 0 && (
          <Card className="border-amber-200 bg-amber-50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold text-amber-800 flex items-center gap-2">
                <Lightbulb className="h-4 w-4" /> Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-1">
                {insights.recommendations.map((r, i) => (
                  <li key={i} className="text-sm text-gray-700 flex gap-2">
                    <Lightbulb className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Risk Flags */}
        {insights.risk_flags?.length > 0 && (
          <Card className="border-red-200 bg-red-50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold text-red-800 flex items-center gap-2">
                <ShieldAlert className="h-4 w-4" /> Risk Flags
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-1">
                {insights.risk_flags.map((r, i) => (
                  <li key={i} className="text-sm text-gray-700 flex gap-2">
                    <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Sentiment-specific fields */}
      {insights.overall_sentiment && (
        <Card className="border-purple-200 bg-purple-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-purple-800 flex items-center gap-2">
              <MessageSquare className="h-4 w-4" /> Sentiment Overview
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-3">
              <Badge
                variant={
                  insights.overall_sentiment === 'positive'
                    ? 'default'
                    : insights.overall_sentiment === 'negative'
                    ? 'destructive'
                    : 'secondary'
                }
                className="capitalize"
              >
                {insights.overall_sentiment}
              </Badge>
              {insights.sentiment_score !== undefined && (
                <span className="text-sm text-gray-600">
                  Score: {Number(insights.sentiment_score).toFixed(2)}
                </span>
              )}
            </div>

            {insights.top_themes?.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Top Themes</p>
                <div className="flex flex-wrap gap-2">
                  {insights.top_themes.map((t, i) => (
                    <Badge key={i} variant="outline" className="text-xs">
                      {t.theme} · {t.frequency}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {insights.recommended_actions?.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase mb-1">
                  Recommended Actions
                </p>
                <ul className="space-y-1">
                  {insights.recommended_actions.map((a, i) => (
                    <li key={i} className="text-sm text-gray-700 flex gap-2">
                      <CheckCircle className="h-4 w-4 text-purple-500 mt-0.5 shrink-0" />
                      <span>{a}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
const VitalClaudeAnalytics = ({ user }) => {
  const isAdmin =
    user?.role === 'admin' ||
    user?.role === 'hr_admin' ||
    user?.role === 'owner' ||
    user?.role === 'super_admin'

  // Tab state: 'cases' | 'sentiment' | 'ask'
  const [activeTab, setActiveTab] = useState('cases')

  // Case analysis state
  const [caseStats, setCaseStats] = useState('')
  const [caseResult, setCaseResult] = useState(null)
  const [caseLoading, setCaseLoading] = useState(false)
  const [caseError, setCaseError] = useState(null)

  // Sentiment analysis state
  const [comments, setComments] = useState('')
  const [sentimentResult, setSentimentResult] = useState(null)
  const [sentimentLoading, setSentimentLoading] = useState(false)
  const [sentimentError, setSentimentError] = useState(null)

  // Free-form ask state (admin only)
  const [askPrompt, setAskPrompt] = useState('')
  const [askResult, setAskResult] = useState(null)
  const [askLoading, setAskLoading] = useState(false)
  const [askError, setAskError] = useState(null)

  // Token usage accordion
  const [showTokens, setShowTokens] = useState(false)

  // ------------------------------------------------------------------
  // Handlers
  // ------------------------------------------------------------------

  const handleAnalyzeCases = async () => {
    setCaseError(null)
    setCaseResult(null)
    setCaseLoading(true)
    try {
      let stats
      try {
        stats = JSON.parse(caseStats)
      } catch {
        throw new Error('Invalid JSON – please paste valid JSON statistics.')
      }
      const data = await claudePost('/api/vital/claude/analyze-cases', { stats })
      setCaseResult(data)
    } catch (err) {
      setCaseError(err.message)
    } finally {
      setCaseLoading(false)
    }
  }

  const handleAnalyzeSentiment = async () => {
    setSentimentError(null)
    setSentimentResult(null)
    setSentimentLoading(true)
    try {
      const lines = comments
        .split('\n')
        .map((l) => l.trim())
        .filter(Boolean)
      if (lines.length === 0) throw new Error('Please enter at least one comment.')
      const data = await claudePost('/api/vital/claude/analyze-sentiment', {
        comments: lines,
      })
      setSentimentResult(data)
    } catch (err) {
      setSentimentError(err.message)
    } finally {
      setSentimentLoading(false)
    }
  }

  const handleAsk = async () => {
    setAskError(null)
    setAskResult(null)
    setAskLoading(true)
    try {
      if (!askPrompt.trim()) throw new Error('Please enter a prompt.')
      const data = await claudePost('/api/vital/claude/ask', { prompt: askPrompt })
      setAskResult(data)
    } catch (err) {
      setAskError(err.message)
    } finally {
      setAskLoading(false)
    }
  }

  // ------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------

  const tabs = [
    { id: 'cases', label: 'Case Analytics', icon: TrendingUp },
    { id: 'sentiment', label: 'Sentiment Analysis', icon: MessageSquare },
    ...(isAdmin ? [{ id: 'ask', label: 'Ask Claude', icon: Brain }] : []),
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Brain className="h-6 w-6 text-purple-600" />
            Claude AI Analytics
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Powered by Anthropic Claude · VITAL Worklife
          </p>
        </div>
        <Badge variant="outline" className="text-purple-700 border-purple-300 bg-purple-50">
          <Sparkles className="h-3 w-3 mr-1" />
          Claude 3.5 Sonnet
        </Badge>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 pb-0">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === id
                ? 'border-purple-600 text-purple-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {/* ── Case Analytics Tab ── */}
      {activeTab === 'cases' && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Analyse Case Statistics</CardTitle>
              <CardDescription>
                Paste aggregated, de-identified case metrics as JSON. Claude will identify trends,
                key findings, and recommendations.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder={`{\n  "total_cases": 1240,\n  "avg_resolution_days": 4.2,\n  "case_types": {"counselling": 620, "financial": 310, "legal": 180, "other": 130},\n  "nps_avg": 8.1,\n  "satisfaction_avg": 4.3\n}`}
                value={caseStats}
                onChange={(e) => setCaseStats(e.target.value)}
                rows={8}
                className="font-mono text-sm"
              />
              <Button
                onClick={handleAnalyzeCases}
                disabled={caseLoading || !caseStats.trim()}
                className="bg-purple-600 hover:bg-purple-700 text-white"
              >
                {caseLoading ? (
                  <>
                    <LoadingSpinner className="h-4 w-4 mr-2" /> Analysing…
                  </>
                ) : (
                  <>
                    <Brain className="h-4 w-4 mr-2" /> Analyse with Claude
                  </>
                )}
              </Button>

              {caseError && (
                <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {caseError}
                </div>
              )}
            </CardContent>
          </Card>

          {caseResult && (
            <div>
              <InsightCard insights={caseResult.insights} />
              <TokenUsage result={caseResult} show={showTokens} onToggle={() => setShowTokens(!showTokens)} />
            </div>
          )}
        </div>
      )}

      {/* ── Sentiment Analysis Tab ── */}
      {activeTab === 'sentiment' && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Satisfaction Comment Analysis</CardTitle>
              <CardDescription>
                Paste de-identified satisfaction comments (one per line, max 200). Claude will
                identify themes, sentiment, and recommended actions.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder={
                  'The counsellor was very understanding and helped me through a difficult time.\n' +
                  'Waited too long for a callback – very frustrating.\n' +
                  'Excellent service, would recommend to colleagues.'
                }
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                rows={10}
              />
              <Button
                onClick={handleAnalyzeSentiment}
                disabled={sentimentLoading || !comments.trim()}
                className="bg-purple-600 hover:bg-purple-700 text-white"
              >
                {sentimentLoading ? (
                  <>
                    <LoadingSpinner className="h-4 w-4 mr-2" /> Analysing…
                  </>
                ) : (
                  <>
                    <MessageSquare className="h-4 w-4 mr-2" /> Analyse Sentiment
                  </>
                )}
              </Button>

              {sentimentError && (
                <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {sentimentError}
                </div>
              )}
            </CardContent>
          </Card>

          {sentimentResult && (
            <div>
              <InsightCard insights={sentimentResult.insights} />
              <TokenUsage
                result={sentimentResult}
                show={showTokens}
                onToggle={() => setShowTokens(!showTokens)}
                extra={`${sentimentResult.comments_analyzed} comments analysed`}
              />
            </div>
          )}
        </div>
      )}

      {/* ── Ask Claude Tab (admin only) ── */}
      {activeTab === 'ask' && isAdmin && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Free-Form Analytics Prompt</CardTitle>
              <CardDescription>
                Ask Claude any analytics question. You can optionally paste supporting data below
                your question.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="What are the key drivers of low NPS scores this quarter, and what actions should we prioritise?"
                value={askPrompt}
                onChange={(e) => setAskPrompt(e.target.value)}
                rows={5}
              />
              <Button
                onClick={handleAsk}
                disabled={askLoading || !askPrompt.trim()}
                className="bg-purple-600 hover:bg-purple-700 text-white"
              >
                {askLoading ? (
                  <>
                    <LoadingSpinner className="h-4 w-4 mr-2" /> Thinking…
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" /> Ask Claude
                  </>
                )}
              </Button>

              {askError && (
                <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {askError}
                </div>
              )}
            </CardContent>
          </Card>

          {askResult && (
            <Card className="border-purple-200 bg-purple-50">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold text-purple-800 flex items-center gap-2">
                  <Brain className="h-4 w-4" /> Claude's Response
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-800 whitespace-pre-wrap">{askResult.response}</p>
                <TokenUsage
                  result={askResult}
                  show={showTokens}
                  onToggle={() => setShowTokens(!showTokens)}
                />
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Small helper: token usage accordion
// ---------------------------------------------------------------------------
function TokenUsage({ result, show, onToggle, extra }) {
  if (!result?.tokens_used && !result?.model) return null
  return (
    <div className="mt-2">
      <button
        onClick={onToggle}
        className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors"
      >
        {show ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        Usage details
      </button>
      {show && (
        <div className="mt-1 text-xs text-gray-500 space-x-4">
          {result.model && <span>Model: {result.model}</span>}
          {result.tokens_used !== undefined && <span>Tokens: {result.tokens_used}</span>}
          {result.cached && <Badge variant="outline" className="text-xs">Cached</Badge>}
          {extra && <span>{extra}</span>}
        </div>
      )}
    </div>
  )
}

export default VitalClaudeAnalytics
