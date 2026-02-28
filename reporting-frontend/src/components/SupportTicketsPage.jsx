import { useState, useEffect, useRef } from 'react'
import { apiUrl } from '../lib/api'
import {
  Ticket, Bug, Lightbulb, HelpCircle, Clock, CheckCircle,
  AlertCircle, XCircle, ChevronDown, RefreshCw,
  Filter, Search, Send, MessageSquare, Paperclip, Download,
  User, Bot, FileText, Image, ArrowLeft
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

  // Detail view
  const [selectedTicket, setSelectedTicket] = useState(null)
  const [ticketComments, setTicketComments] = useState([])
  const [ticketAttachments, setTicketAttachments] = useState([])
  const [loadingDetail, setLoadingDetail] = useState(false)

  // Reply form
  const [replyMessage, setReplyMessage] = useState('')
  const [submittingReply, setSubmittingReply] = useState(false)

  // Update state
  const [updating, setUpdating] = useState(null)

  // Scroll ref for conversation
  const conversationEndRef = useRef(null)

  const token = localStorage.getItem('token')

  useEffect(() => {
    loadData()
  }, [statusFilter, typeFilter])

  useEffect(() => {
    if (conversationEndRef.current) {
      conversationEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [ticketComments])

  const loadData = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (statusFilter) params.set('status', statusFilter)
      if (typeFilter) params.set('type', typeFilter)

      const [ticketsRes, statsRes] = await Promise.all([
        fetch(apiUrl(`/api/support-tickets?${params.toString()}`), {
          headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
        }),
        fetch(apiUrl('/api/support-tickets/stats'), {
          headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
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

  const loadTicketDetail = async (ticket) => {
    try {
      setLoadingDetail(true)
      setSelectedTicket(ticket)

      const [commentsRes, attachmentsRes] = await Promise.all([
        fetch(apiUrl(`/api/support-tickets/${ticket.id}/comments`), {
          headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
        }),
        fetch(apiUrl(`/api/support-tickets/${ticket.id}/attachments`), {
          headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
        })
      ])

      const commentsData = commentsRes.ok ? await commentsRes.json() : { comments: [] }
      const attachmentsData = attachmentsRes.ok ? await attachmentsRes.json() : { attachments: [] }

      setTicketComments(Array.isArray(commentsData) ? commentsData : (commentsData.comments || []))
      setTicketAttachments(Array.isArray(attachmentsData) ? attachmentsData : (attachmentsData.attachments || []))
    } catch (err) {
      console.error('Failed to load ticket details:', err)
    } finally {
      setLoadingDetail(false)
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
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(body)
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.error || 'Failed to update ticket')
      }

      await loadData()

      // Refresh the selected ticket if it's the one being updated
      if (selectedTicket && selectedTicket.id === id) {
        setSelectedTicket({ ...selectedTicket, ...updates })
      }
    } catch (err) {
      alert(err.message || 'Failed to update ticket')
    } finally {
      setUpdating(null)
    }
  }

  const handleResolveTicket = async (id) => {
    const resolutionNotes = prompt('Enter resolution notes (what was fixed, how to test):')
    if (!resolutionNotes) return

    try {
      setUpdating(id)
      const userName = user?.first_name
        ? `${user.first_name} ${user.last_name || ''}`.trim()
        : user?.username || 'Admin'

      const res = await fetch(apiUrl(`/api/support-tickets/${id}/resolve`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          resolution_notes: resolutionNotes,
          resolved_by: userName
        })
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.error || 'Failed to resolve ticket')
      }

      await loadData()

      if (selectedTicket && selectedTicket.id === id) {
        setSelectedTicket({ ...selectedTicket, status: 'resolved', resolution_notes: resolutionNotes, resolved_by: userName })
        // Reload comments
        const commentsRes = await fetch(apiUrl(`/api/support-tickets/${id}/comments`), {
          headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
        })
        if (commentsRes.ok) {
          const commentsData = await commentsRes.json()
          setTicketComments(Array.isArray(commentsData) ? commentsData : (commentsData.comments || []))
        }
      }
    } catch (err) {
      alert(err.message || 'Failed to resolve ticket')
    } finally {
      setUpdating(null)
    }
  }

  const handleSubmitReply = async () => {
    if (!selectedTicket || !replyMessage.trim()) return

    try {
      setSubmittingReply(true)
      const userName = user?.first_name
        ? `${user.first_name} ${user.last_name || ''}`.trim()
        : user?.username || 'Admin'

      const res = await fetch(apiUrl(`/api/support-tickets/${selectedTicket.id}/comments`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          message: replyMessage.trim(),
          comment_type: 'system_note',
          created_by_name: userName,
          created_by_email: user?.email,
          created_by_user_id: user?.id,
          is_internal: false
        })
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.error || 'Failed to submit reply')
      }

      setReplyMessage('')

      // Reload comments
      const commentsRes = await fetch(apiUrl(`/api/support-tickets/${selectedTicket.id}/comments`), {
        headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
      })
      if (commentsRes.ok) {
        const commentsData = await commentsRes.json()
        setTicketComments(Array.isArray(commentsData) ? commentsData : (commentsData.comments || []))
      }
    } catch (err) {
      alert(err.message || 'Failed to submit reply')
    } finally {
      setSubmittingReply(false)
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

  const getTypeLabel = (type) => {
    switch (type) {
      case 'bug': return 'Bug Report'
      case 'enhancement': return 'Enhancement'
      case 'question': return 'Question'
      default: return type
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
        {status?.replace('_', ' ')}
      </span>
    )
  }

  const getTypeBadge = (type) => {
    const styles = {
      bug: 'bg-red-100 text-red-700 border-red-200',
      enhancement: 'bg-amber-100 text-amber-700 border-amber-200',
      question: 'bg-blue-100 text-blue-700 border-blue-200'
    }
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${styles[type] || ''}`}>
        {getTypeIcon(type)}
        {getTypeLabel(type)}
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

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  const formatRelativeTime = (dateStr) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return 'just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return formatDate(dateStr)
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
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

  // ==================== DETAIL VIEW ====================
  if (selectedTicket) {
    return (
      <div className="max-w-5xl mx-auto">
        {/* Back button and header */}
        <div className="mb-4">
          <button
            onClick={() => { setSelectedTicket(null); setTicketComments([]); setTicketAttachments([]) }}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to all tickets
          </button>
        </div>

        {/* Ticket Header Card */}
        <div className="bg-white rounded-lg shadow mb-4">
          <div className="p-5">
            <div className="flex items-start justify-between gap-4 mb-3">
              <div>
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <span className="font-mono text-sm text-gray-500">{selectedTicket.ticket_number}</span>
                  {getStatusBadge(selectedTicket.status)}
                  {getPriorityBadge(selectedTicket.priority)}
                  {getTypeBadge(selectedTicket.type)}
                </div>
                <h1 className="text-xl font-bold text-gray-900">{selectedTicket.subject}</h1>
              </div>
            </div>

            <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-gray-600">
              <div className="flex items-center gap-1.5">
                <User className="h-3.5 w-3.5" />
                <span>{selectedTicket.submitted_by_name || 'Unknown'}</span>
                {selectedTicket.submitted_by_email && (
                  <span className="text-gray-400">({selectedTicket.submitted_by_email})</span>
                )}
              </div>
              <div>
                Submitted: {formatDate(selectedTicket.created_at)}
              </div>
              {selectedTicket.page_url && (
                <a
                  href={selectedTicket.page_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline truncate max-w-xs"
                >
                  {selectedTicket.page_url}
                </a>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Left: Conversation Flow (2/3 width) */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b">
                <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Conversation
                </h2>
              </div>

              <div className="p-4 space-y-4 max-h-[600px] overflow-y-auto">
                {/* Original message - always first */}
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <User className="h-4 w-4 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm text-gray-900">
                        {selectedTicket.submitted_by_name || 'User'}
                      </span>
                      <span className="text-xs text-gray-400">
                        {formatRelativeTime(selectedTicket.created_at)}
                      </span>
                      <span className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">
                        Original Message
                      </span>
                    </div>
                    <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 text-sm text-gray-800 whitespace-pre-wrap">
                      {selectedTicket.message}
                    </div>
                  </div>
                </div>

                {/* Attachments (shown after original message) */}
                {ticketAttachments.length > 0 && (
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                      <Paperclip className="h-4 w-4 text-gray-500" />
                    </div>
                    <div className="flex-1">
                      <div className="text-xs text-gray-500 mb-1.5">Attachments</div>
                      <div className="space-y-1.5">
                        {ticketAttachments.map((att) => (
                          <a
                            key={att.id}
                            href={apiUrl(`/api/support-tickets/${selectedTicket.id}/attachments/${att.id}/download`)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 p-2 bg-gray-50 border rounded-lg hover:bg-gray-100 transition-colors group"
                          >
                            {att.mimetype?.startsWith('image/') ? (
                              <Image className="h-4 w-4 text-blue-500" />
                            ) : (
                              <FileText className="h-4 w-4 text-gray-500" />
                            )}
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-gray-700 truncate">{att.filename}</div>
                              <div className="text-xs text-gray-400">{formatFileSize(att.size)}</div>
                            </div>
                            <Download className="h-4 w-4 text-gray-400 group-hover:text-blue-600" />
                          </a>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Comments / conversation thread */}
                {ticketComments.map((comment) => {
                  const isSystem = comment.comment_type === 'system_resolution' || comment.comment_type === 'system_note'
                  const isResolution = comment.comment_type === 'system_resolution'

                  return (
                    <div key={comment.id} className="flex gap-3">
                      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                        isSystem ? 'bg-green-100' : 'bg-blue-100'
                      }`}>
                        {isSystem ? (
                          <Bot className="h-4 w-4 text-green-600" />
                        ) : (
                          <User className="h-4 w-4 text-blue-600" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-sm text-gray-900">
                            {comment.created_by_name || (isSystem ? 'Support Team' : 'User')}
                          </span>
                          <span className="text-xs text-gray-400">
                            {formatRelativeTime(comment.created_at)}
                          </span>
                          {isResolution && (
                            <span className="text-xs bg-green-50 text-green-700 px-1.5 py-0.5 rounded font-medium">
                              Resolution
                            </span>
                          )}
                          {comment.is_internal && (
                            <span className="text-xs bg-yellow-50 text-yellow-700 px-1.5 py-0.5 rounded font-medium">
                              Internal
                            </span>
                          )}
                        </div>
                        <div className={`rounded-lg p-3 text-sm whitespace-pre-wrap ${
                          isResolution
                            ? 'bg-green-50 border border-green-200 text-gray-800'
                            : isSystem
                            ? 'bg-gray-50 border border-gray-200 text-gray-800'
                            : 'bg-blue-50 border border-blue-100 text-gray-800'
                        }`}>
                          {comment.message}
                        </div>
                      </div>
                    </div>
                  )
                })}

                {/* Resolution notes (legacy - shown if present and no system_resolution comment) */}
                {selectedTicket.resolution_notes && !ticketComments.some(c => c.comment_type === 'system_resolution') && (
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm text-gray-900">
                          {selectedTicket.resolved_by || 'Support Team'}
                        </span>
                        {selectedTicket.resolved_at && (
                          <span className="text-xs text-gray-400">
                            {formatRelativeTime(selectedTicket.resolved_at)}
                          </span>
                        )}
                        <span className="text-xs bg-green-50 text-green-700 px-1.5 py-0.5 rounded font-medium">
                          Resolution
                        </span>
                      </div>
                      <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-gray-800 whitespace-pre-wrap">
                        {selectedTicket.resolution_notes}
                      </div>
                    </div>
                  </div>
                )}

                {loadingDetail && (
                  <div className="flex justify-center py-4">
                    <RefreshCw className="h-5 w-5 animate-spin text-gray-400" />
                  </div>
                )}

                <div ref={conversationEndRef} />
              </div>

              {/* Reply Box */}
              <div className="border-t p-4">
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-green-600" />
                  </div>
                  <div className="flex-1">
                    <textarea
                      value={replyMessage}
                      onChange={(e) => setReplyMessage(e.target.value)}
                      placeholder="Type a reply..."
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 text-sm resize-none"
                      disabled={submittingReply}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                          handleSubmitReply()
                        }
                      }}
                    />
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs text-gray-400">Ctrl+Enter to send</span>
                      <button
                        onClick={handleSubmitReply}
                        disabled={!replyMessage.trim() || submittingReply}
                        className="flex items-center gap-2 px-4 py-1.5 bg-gray-900 hover:bg-black text-white rounded-lg text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {submittingReply ? (
                          <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <Send className="h-3.5 w-3.5" />
                        )}
                        Send Reply
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Admin Controls (1/3 width) */}
          <div className="space-y-4">
            {/* Ticket Type */}
            <div className="bg-white rounded-lg shadow p-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ticket Type
              </label>
              <select
                value={selectedTicket.type}
                onChange={(e) => {
                  const newType = e.target.value
                  handleUpdateTicket(selectedTicket.id, { type: newType })
                  setSelectedTicket({ ...selectedTicket, type: newType })
                }}
                disabled={updating === selectedTicket.id}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 text-sm"
              >
                <option value="bug">Bug Report</option>
                <option value="enhancement">Enhancement</option>
                <option value="question">Question</option>
              </select>
            </div>

            {/* Status */}
            <div className="bg-white rounded-lg shadow p-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <select
                value={selectedTicket.status}
                onChange={(e) => {
                  const newStatus = e.target.value
                  handleUpdateTicket(selectedTicket.id, { status: newStatus })
                  setSelectedTicket({ ...selectedTicket, status: newStatus })
                }}
                disabled={updating === selectedTicket.id}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 text-sm"
              >
                <option value="open">Open</option>
                <option value="in_progress">In Progress</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
            </div>

            {/* Priority */}
            <div className="bg-white rounded-lg shadow p-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Priority
              </label>
              <select
                value={selectedTicket.priority}
                onChange={(e) => {
                  const newPriority = e.target.value
                  handleUpdateTicket(selectedTicket.id, { priority: newPriority })
                  setSelectedTicket({ ...selectedTicket, priority: newPriority })
                }}
                disabled={updating === selectedTicket.id}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 text-sm"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            {/* Resolve Button */}
            {selectedTicket.status !== 'resolved' && selectedTicket.status !== 'closed' && (
              <div className="bg-white rounded-lg shadow p-4">
                <button
                  onClick={() => handleResolveTicket(selectedTicket.id)}
                  disabled={updating === selectedTicket.id}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm transition-colors disabled:opacity-50"
                >
                  <CheckCircle className="h-4 w-4" />
                  Resolve Ticket
                </button>
                <p className="text-xs text-gray-500 mt-2">
                  Resolving will send a notification email to the submitter with resolution details.
                </p>
              </div>
            )}

            {/* Resolution Notes */}
            <div className="bg-white rounded-lg shadow p-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Resolution Notes
              </label>
              <textarea
                defaultValue={selectedTicket.resolution_notes || ''}
                placeholder="Add notes about the resolution..."
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 text-sm resize-none"
                onBlur={(e) => {
                  if (e.target.value !== (selectedTicket.resolution_notes || '')) {
                    handleUpdateTicket(selectedTicket.id, { resolution_notes: e.target.value })
                    setSelectedTicket({ ...selectedTicket, resolution_notes: e.target.value })
                  }
                }}
                disabled={updating === selectedTicket.id}
              />
            </div>

            {/* Ticket Info */}
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Details</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Submitted by:</span>
                  <span className="font-medium text-gray-900">{selectedTicket.submitted_by_name || 'Unknown'}</span>
                </div>
                {selectedTicket.submitted_by_email && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Email:</span>
                    <span className="text-gray-700">{selectedTicket.submitted_by_email}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-500">Created:</span>
                  <span className="text-gray-700">{formatDate(selectedTicket.created_at)}</span>
                </div>
                {selectedTicket.updated_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Updated:</span>
                    <span className="text-gray-700">{formatDate(selectedTicket.updated_at)}</span>
                  </div>
                )}
                {selectedTicket.resolved_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Resolved:</span>
                    <span className="text-gray-700">{formatDate(selectedTicket.resolved_at)}</span>
                  </div>
                )}
                {selectedTicket.resolved_by && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Resolved by:</span>
                    <span className="font-medium text-gray-900">{selectedTicket.resolved_by}</span>
                  </div>
                )}
              </div>
            </div>

            {updating === selectedTicket.id && (
              <div className="flex items-center gap-2 text-sm text-gray-500 justify-center">
                <RefreshCw className="h-4 w-4 animate-spin" />
                Saving...
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // ==================== LIST VIEW ====================
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
      <div className="space-y-2">
        {filteredTickets.map((ticket) => (
          <div
            key={ticket.id}
            className="bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => loadTicketDetail(ticket)}
          >
            <div className="p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 min-w-0">
                  <div className="mt-1">{getTypeIcon(ticket.type)}</div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="font-mono text-sm text-gray-500">{ticket.ticket_number}</span>
                      {getStatusBadge(ticket.status)}
                      {getPriorityBadge(ticket.priority)}
                      {getTypeBadge(ticket.type)}
                    </div>
                    <h3 className="font-medium text-gray-900 truncate">{ticket.subject}</h3>
                    <div className="text-sm text-gray-500 mt-1">
                      {ticket.submitted_by_name || 'Unknown'} — {formatRelativeTime(ticket.created_at)}
                    </div>
                  </div>
                </div>
                <ChevronDown className="h-5 w-5 text-gray-400 flex-shrink-0 mt-1" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
