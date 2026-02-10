import { useState, useEffect } from 'react'
import { apiUrl } from '../lib/api'
import {
  Ticket, Bug, Lightbulb, HelpCircle, Clock, CheckCircle,
  AlertCircle, XCircle, ChevronDown, ChevronUp, RefreshCw,
  Filter, Search
} from 'lucide-react'

export default function SupportTicketsPage({ user }) {
  const [tickets, setTickets] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filters
  const [statusFilter, setStatusFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  // Expanded ticket
  const [expandedTicketId, setExpandedTicketId] = useState(null)

  // Update state
  const [updating, setUpdating] = useState(null)

  const token = localStorage.getItem('token')

  useEffect(() => {
    loadData()
  }, [statusFilter, typeFilter])

  const loadData = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (statusFilter) params.set('status', statusFilter)
      if (typeFilter) params.set('type', typeFilter)

      const [ticketsRes, statsRes] = await Promise.all([
        fetch(apiUrl(`/api/support-tickets?${params.toString()}`), {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(apiUrl('/api/support-tickets/stats'), {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ])

      if (!ticketsRes.ok || !statsRes.ok) throw new Error('Failed to load tickets')

      const ticketsData = await ticketsRes.json()
      const statsData = await statsRes.json()

      setTickets(ticketsData.tickets || [])
      setStats(statsData)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load tickets')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateTicket = async (id, updates) => {
    try {
      setUpdating(id)
      const body = {
        ...updates,
        resolved_by: (updates.status === 'resolved' || updates.status === 'closed')
          ? (user?.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : user?.username)
          : undefined
      }

      const res = await fetch(apiUrl(`/api/support-tickets/${id}`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(body)
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.error || 'Failed to update ticket')
      }

      await loadData()
    } catch (err) {
      alert(err.message || 'Failed to update ticket')
    } finally {
      setUpdating(null)
    }
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'bug': return <Bug className="h-4 w-4 text-red-600" />
      case 'enhancement': return <Lightbulb className="h-4 w-4 text-amber-600" />
      case 'question': return <HelpCircle className="h-4 w-4 text-blue-600" />
      default: return <Ticket className="h-4 w-4" />
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'open': return <AlertCircle className="h-4 w-4 text-red-600" />
      case 'in_progress': return <Clock className="h-4 w-4 text-amber-600" />
      case 'resolved': return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'closed': return <XCircle className="h-4 w-4 text-gray-500" />
      default: return null
    }
  }

  const getStatusBadge = (status) => {
    const styles = {
      open: 'bg-red-100 text-red-800',
      in_progress: 'bg-amber-100 text-amber-800',
      resolved: 'bg-green-100 text-green-800',
      closed: 'bg-gray-100 text-gray-800'
    }
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${styles[status] || ''}`}>
        {getStatusIcon(status)}
        {status.replace('_', ' ')}
      </span>
    )
  }

  const getPriorityBadge = (priority) => {
    const styles = {
      critical: 'bg-red-600 text-white',
      high: 'bg-orange-500 text-white',
      medium: 'bg-yellow-500 text-white',
      low: 'bg-gray-400 text-white'
    }
    return (
      <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles[priority] || ''}`}>
        {priority}
      </span>
    )
  }

  const filteredTickets = tickets.filter(ticket => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      ticket.ticket_number?.toLowerCase().includes(query) ||
      ticket.subject?.toLowerCase().includes(query) ||
      ticket.message?.toLowerCase().includes(query) ||
      ticket.submitted_by_name?.toLowerCase().includes(query) ||
      ticket.submitted_by_email?.toLowerCase().includes(query)
    )
  })

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Support Tickets</h1>
          <p className="text-gray-600">Manage bug reports, enhancement requests, and questions</p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
            <div className="text-sm text-gray-500">Total Tickets</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-red-500">
            <div className="text-2xl font-bold text-red-600">{stats.open}</div>
            <div className="text-sm text-gray-500">Open</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-amber-500">
            <div className="text-2xl font-bold text-amber-600">{stats.in_progress}</div>
            <div className="text-sm text-gray-500">In Progress</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
            <div className="text-2xl font-bold text-green-600">{stats.resolved}</div>
            <div className="text-sm text-gray-500">Resolved</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-gray-400">
            <div className="text-2xl font-bold text-gray-600">{stats.closed}</div>
            <div className="text-sm text-gray-500">Closed</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Filters:</span>
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-gray-500"
          >
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-gray-500"
          >
            <option value="">All Types</option>
            <option value="bug">Bug Reports</option>
            <option value="enhancement">Enhancements</option>
            <option value="question">Questions</option>
          </select>

          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search tickets..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-gray-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && !tickets.length && (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Loading tickets...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && !filteredTickets.length && (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <Ticket className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No tickets found</p>
        </div>
      )}

      {/* Tickets List */}
      <div className="space-y-4">
        {filteredTickets.map((ticket) => (
          <div key={ticket.id} className="bg-white rounded-lg shadow overflow-hidden">
            {/* Ticket Header */}
            <div
              className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
              onClick={() => setExpandedTicketId(expandedTicketId === ticket.id ? null : ticket.id)}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="mt-1">{getTypeIcon(ticket.type)}</div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-sm text-gray-500">{ticket.ticket_number}</span>
                      {getStatusBadge(ticket.status)}
                      {getPriorityBadge(ticket.priority)}
                    </div>
                    <h3 className="font-medium text-gray-900">{ticket.subject}</h3>
                    <div className="text-sm text-gray-500 mt-1">
                      {ticket.submitted_by_name || 'Unknown'} &bull; {new Date(ticket.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
                <div>
                  {expandedTicketId === ticket.id ? (
                    <ChevronUp className="h-5 w-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-gray-400" />
                  )}
                </div>
              </div>
            </div>

            {/* Expanded Details */}
            {expandedTicketId === ticket.id && (
              <div className="border-t bg-gray-50 p-4">
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Left Column - Details */}
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Message</h4>
                      <div className="bg-white p-3 rounded border text-sm whitespace-pre-wrap">
                        {ticket.message}
                      </div>
                    </div>

                    {ticket.page_url && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-1">Page URL</h4>
                        <a
                          href={ticket.page_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:underline break-all"
                        >
                          {ticket.page_url}
                        </a>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Submitted by:</span>
                        <div className="font-medium">{ticket.submitted_by_name || 'Unknown'}</div>
                        {ticket.submitted_by_email && (
                          <div className="text-gray-500">{ticket.submitted_by_email}</div>
                        )}
                      </div>
                      <div>
                        <span className="text-gray-500">Created:</span>
                        <div className="font-medium">{new Date(ticket.created_at).toLocaleString()}</div>
                      </div>
                    </div>

                    {/* Attachments */}
                    {ticket.attachments && ticket.attachments.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-1">Attachments</h4>
                        <div className="space-y-1">
                          {ticket.attachments.map((att) => (
                            <div key={att.id} className="text-sm text-gray-600 flex items-center gap-2">
                              <span>{att.filename}</span>
                              <span className="text-gray-400">({(att.size / 1024).toFixed(1)} KB)</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {ticket.resolution_notes && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-1">Resolution Notes</h4>
                        <div className="bg-green-50 p-3 rounded border border-green-200 text-sm">
                          {ticket.resolution_notes}
                          {ticket.resolved_by && (
                            <div className="text-gray-500 mt-2">&mdash; {ticket.resolved_by}</div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Right Column - Actions */}
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Update Status
                      </label>
                      <select
                        value={ticket.status}
                        onChange={(e) => handleUpdateTicket(ticket.id, { status: e.target.value })}
                        disabled={updating === ticket.id}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500"
                      >
                        <option value="open">Open</option>
                        <option value="in_progress">In Progress</option>
                        <option value="resolved">Resolved</option>
                        <option value="closed">Closed</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Priority
                      </label>
                      <select
                        value={ticket.priority}
                        onChange={(e) => handleUpdateTicket(ticket.id, { priority: e.target.value })}
                        disabled={updating === ticket.id}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500"
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="critical">Critical</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Resolution Notes
                      </label>
                      <textarea
                        defaultValue={ticket.resolution_notes || ''}
                        placeholder="Add notes about the resolution..."
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 text-sm"
                        onBlur={(e) => {
                          if (e.target.value !== (ticket.resolution_notes || '')) {
                            handleUpdateTicket(ticket.id, { resolution_notes: e.target.value })
                          }
                        }}
                        disabled={updating === ticket.id}
                      />
                    </div>

                    {updating === ticket.id && (
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        Updating...
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
