import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Users, MessageSquare, TrendingUp, Activity,
  RefreshCw, AlertCircle, Calendar, Layers
} from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { apiUrl } from '@/lib/api'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const fmt = (n) => (n == null ? '—' : Number(n).toLocaleString())

const shortDate = (iso) => {
  if (!iso) return ''
  const [, m, d] = iso.split('-')
  return `${parseInt(m)}/${parseInt(d)}`
}

// ---------------------------------------------------------------------------
// Stat card
// ---------------------------------------------------------------------------

const StatCard = ({ icon: Icon, label, value, sub, color = 'blue' }) => {
  const colors = {
    blue:   'bg-blue-50 text-blue-600',
    green:  'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    orange: 'bg-orange-50 text-orange-600',
  }
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-gray-500 mb-1">{label}</p>
            <p className="text-3xl font-bold text-gray-900">{value}</p>
            {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
          </div>
          <div className={`p-2 rounded-lg ${colors[color]}`}>
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function VitalClaudeAnalytics({ user, organization }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [days, setDays] = useState(30)
  const [refreshing, setRefreshing] = useState(false)

  const fetchDashboard = useCallback(async (forceRefresh = false) => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const base = typeof apiUrl === 'function' ? apiUrl('/api/vital/claude-analytics/dashboard') : `${apiUrl}/api/vital/claude-analytics/dashboard`
      const url = `${base}?days=${days}${forceRefresh ? '&refresh=true' : ''}`
      const resp = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}))
        throw new Error(body.error || `HTTP ${resp.status}`)
      }
      const json = await resp.json()
      setData(json)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [days])

  useEffect(() => { fetchDashboard() }, [fetchDashboard])

  const handleRefresh = () => {
    setRefreshing(true)
    fetchDashboard(true)
  }

  // -------------------------------------------------------------------------
  // Loading state
  // -------------------------------------------------------------------------

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-purple-500 mx-auto mb-3" />
          <p className="text-gray-500">Loading Claude analytics…</p>
        </div>
      </div>
    )
  }

  // -------------------------------------------------------------------------
  // Error state
  // -------------------------------------------------------------------------

  if (error) {
    return (
      <div className="p-8">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-6 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium text-red-800">Could not load Claude analytics</p>
              <p className="text-sm text-red-600 mt-1">{error}</p>
              {error.includes('CLAUDE_ANALYTICS_API_KEY') && (
                <p className="text-sm text-red-600 mt-2">
                  Add <code className="bg-red-100 px-1 rounded">CLAUDE_ANALYTICS_API_KEY</code> to
                  Railway environment variables. Generate the key at{' '}
                  <a href="https://claude.ai/analytics/api-keys" target="_blank" rel="noreferrer"
                    className="underline">claude.ai/analytics/api-keys</a>.
                </p>
              )}
              <Button size="sm" variant="outline" className="mt-3" onClick={() => fetchDashboard()}>
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // -------------------------------------------------------------------------
  // Data
  // -------------------------------------------------------------------------

  const latest = data?.latest_summary || {}
  const summaries = data?.summaries || []
  const topProjects = data?.top_projects || []
  const topUsers = data?.top_users || []
  const skills = data?.skills || []
  const latestDate = data?.latest_date

  const chartData = summaries.map((s) => ({
    date: shortDate((s.starting_at || s.starting_date || '').substring(0, 10)),
    DAU: s.daily_active_user_count || 0,
    WAU: s.weekly_active_user_count || 0,
    MAU: s.monthly_active_user_count || 0,
  }))

  const adoptionRate = latest.assigned_seat_count
    ? Math.round(((latest.daily_active_user_count || 0) / latest.assigned_seat_count) * 100)
    : null

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Claude Analytics</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Usage &amp; adoption · VITAL Worklife
            {latestDate && (
              <span className="ml-2 text-gray-400">· Latest data: {latestDate}</span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex gap-1 border rounded-lg p-1 bg-white">
            {[7, 14, 30].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  days === d ? 'bg-purple-600 text-white' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={`h-4 w-4 mr-1.5 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {data?.cached && <Badge variant="secondary" className="text-xs">Cached</Badge>}
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Activity}
          label="Daily Active Users"
          value={fmt(latest.daily_active_user_count)}
          sub={adoptionRate != null ? `${adoptionRate}% of seats` : undefined}
          color="purple"
        />
        <StatCard
          icon={Users}
          label="Weekly Active Users"
          value={fmt(latest.weekly_active_user_count)}
          sub="7-day rolling"
          color="blue"
        />
        <StatCard
          icon={TrendingUp}
          label="Monthly Active Users"
          value={fmt(latest.monthly_active_user_count)}
          sub="30-day rolling"
          color="green"
        />
        <StatCard
          icon={Calendar}
          label="Assigned Seats"
          value={fmt(latest.assigned_seat_count)}
          sub={
            latest.pending_invite_count
              ? `${latest.pending_invite_count} pending invite${latest.pending_invite_count !== 1 ? 's' : ''}`
              : 'No pending invites'
          }
          color="orange"
        />
      </div>

      {/* Active users trend chart */}
      {chartData.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">
              Active Users — Last {days} Days
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="DAU" stroke="#7c3aed" strokeWidth={2} dot={false} name="Daily" />
                <Line type="monotone" dataKey="WAU" stroke="#2563eb" strokeWidth={2} dot={false} name="Weekly" />
                <Line type="monotone" dataKey="MAU" stroke="#16a34a" strokeWidth={2} dot={false} name="Monthly" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Projects + Top users */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Layers className="h-4 w-4 text-purple-500" />
              Top Chat Projects
            </CardTitle>
          </CardHeader>
          <CardContent>
            {topProjects.length === 0 ? (
              <p className="text-sm text-gray-400">No project data available.</p>
            ) : (
              <div className="space-y-2">
                {topProjects.slice(0, 8).map((p, i) => (
                  <div key={p.project_id || i} className="flex items-center justify-between text-sm">
                    <span className="truncate text-gray-700 max-w-[60%]" title={p.project_name}>
                      {p.project_name || 'Unnamed project'}
                    </span>
                    <div className="flex gap-3 text-gray-500 text-xs">
                      <span>{fmt(p.distinct_user_count)} users</span>
                      <span>{fmt(p.message_count)} msgs</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-blue-500" />
              Most Active Users
              <span className="text-xs font-normal text-gray-400">(admin only)</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {topUsers.length === 0 ? (
              <p className="text-sm text-gray-400">No user data available.</p>
            ) : (
              <div className="space-y-2">
                {topUsers.slice(0, 8).map((u, i) => {
                  const msgs = u.chat_metrics?.message_count || 0
                  const convos = u.chat_metrics?.distinct_conversation_count || 0
                  return (
                    <div key={u.user?.id || i} className="flex items-center justify-between text-sm">
                      <span className="truncate text-gray-700 max-w-[55%]" title={u.user?.email_address}>
                        {u.user?.email_address || 'Unknown'}
                      </span>
                      <div className="flex gap-3 text-gray-500 text-xs">
                        <span>{fmt(msgs)} msgs</span>
                        <span>{fmt(convos)} chats</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Skill usage chart */}
      {skills.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">Skill Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart
                data={skills.slice(0, 10).map((s) => ({
                  name: s.skill_name || 'Unknown',
                  users: s.distinct_user_count || 0,
                }))}
                margin={{ top: 5, right: 20, left: 0, bottom: 40 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="users" fill="#7c3aed" name="Unique users" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Non-fatal API errors */}
      {data?.errors?.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="p-4">
            <p className="text-sm font-medium text-yellow-800 mb-1">Some data could not be loaded:</p>
            <ul className="text-xs text-yellow-700 list-disc list-inside space-y-0.5">
              {data.errors.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
