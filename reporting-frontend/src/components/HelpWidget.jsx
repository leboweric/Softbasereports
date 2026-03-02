import { useState, useCallback, useRef, useEffect } from 'react'
import { apiUrl } from '../lib/api'
import {
  MessageCircle, X, Send, Loader2, CheckCircle, AlertCircle, Upload, Image, FileText, Trash2,
  Paperclip, ChevronLeft, Clock, Ticket, MessageSquare
} from 'lucide-react'

const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100MB
const ALLOWED_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
const ALLOWED_DOC_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'text/plain'
]

// Auto-detect ticket type from message content
function detectTicketType(message) {
  const lower = message.toLowerCase()
  const bugKeywords = ['bug', 'broken', 'error', 'crash', 'not working', 'doesn\'t work', 'won\'t load', 'failed', 'issue', 'wrong', 'fix', 'problem']
  const enhancementKeywords = ['feature', 'add', 'would be nice', 'enhancement', 'improve', 'suggest', 'request', 'could you', 'can you add', 'new report', 'wish', 'idea']

  if (bugKeywords.some(kw => lower.includes(kw))) return 'bug'
  if (enhancementKeywords.some(kw => lower.includes(kw))) return 'enhancement'
  return 'question'
}

// Generate a subject from the message (first ~60 chars, trimmed to word boundary)
function generateSubject(message) {
  const cleaned = message.replace(/\s+/g, ' ').trim()
  if (cleaned.length <= 60) return cleaned
  const truncated = cleaned.substring(0, 60)
  const lastSpace = truncated.lastIndexOf(' ')
  return (lastSpace > 30 ? truncated.substring(0, lastSpace) : truncated) + '...'
}

export default function HelpWidget({ user, className = '' }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  // Mode: 'chat', 'my-tickets', or 'followup'
  const [mode, setMode] = useState('chat')
  const [followupTicket, setFollowupTicket] = useState(null)
  const [isLoadingTicket, setIsLoadingTicket] = useState(false)

  // My Tickets state
  const [myTickets, setMyTickets] = useState([])
  const [isLoadingMyTickets, setIsLoadingMyTickets] = useState(false)

  // Chat state
  const [message, setMessage] = useState('')
  const [files, setFiles] = useState([])
  const [isDragging, setIsDragging] = useState(false)

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)

  const token = localStorage.getItem('token')

  // Auto-scroll to bottom of conversation
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (mode === 'followup' && followupTicket) {
      scrollToBottom()
    }
  }, [followupTicket?.comments, mode])

  // Check URL for ticket_followup or ticket_close parameter on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const followupTicketNumber = params.get('ticket_followup')
    const closeTicketNumber = params.get('ticket_close')

    if (followupTicketNumber) {
      loadTicketForFollowup(followupTicketNumber)
      setIsOpen(true)
    } else if (closeTicketNumber) {
      closeTicketByNumber(closeTicketNumber)
    }
  }, [])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px'
    }
  }, [message])

  const loadMyTickets = async () => {
    if (!user?.email && !user?.id) return
    setIsLoadingMyTickets(true)
    setError(null)

    try {
      const params = new URLSearchParams()
      if (user.email) params.append('email', user.email)
      if (user.id) params.append('user_id', user.id)

      const res = await fetch(apiUrl(`/api/support-tickets/my-tickets?${params.toString()}`), {
        headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
      })
      if (!res.ok) throw new Error('Failed to load tickets')
      const data = await res.json()
      setMyTickets(data.tickets || [])
    } catch (err) {
      console.error('Error loading my tickets:', err)
      setError('Failed to load your tickets. Please try again.')
    } finally {
      setIsLoadingMyTickets(false)
    }
  }

  const loadTicketForFollowup = async (ticketNumberOrId) => {
    setIsLoadingTicket(true)
    setError(null)

    try {
      let ticketId = ticketNumberOrId

      // If it's a ticket number (string like TKT-xxxx), find the ID first
      if (typeof ticketNumberOrId === 'string' && ticketNumberOrId.startsWith('TKT')) {
        const ticketsRes = await fetch(apiUrl('/api/support-tickets'), {
          headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
        })
        if (!ticketsRes.ok) throw new Error('Failed to load tickets')
        const ticketsData = await ticketsRes.json()
        const ticket = ticketsData.tickets?.find(t => t.ticket_number === ticketNumberOrId)

        if (!ticket) {
          setError(`Ticket ${ticketNumberOrId} not found`)
          setMode('chat')
          return
        }
        ticketId = ticket.id
      }

      // Load ticket with comments
      const detailRes = await fetch(apiUrl(`/api/support-tickets/${ticketId}/with-comments`), {
        headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
      })
      if (!detailRes.ok) throw new Error('Failed to load ticket details')
      const detailData = await detailRes.json()

      // Load attachments
      try {
        const attRes = await fetch(apiUrl(`/api/support-tickets/${ticketId}/attachments`), {
          headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
        })
        if (attRes.ok) {
          const attData = await attRes.json()
          detailData.attachments = attData.attachments || []
        }
      } catch (err) {
        console.error('Error loading attachments:', err)
        detailData.attachments = []
      }

      setFollowupTicket(detailData)
      setMode('followup')

      // Clear URL parameter if present
      const url = new URL(window.location.href)
      if (url.searchParams.has('ticket_followup')) {
        url.searchParams.delete('ticket_followup')
        window.history.replaceState({}, '', url.toString())
      }
    } catch (err) {
      console.error('Error loading ticket:', err)
      setError('Failed to load ticket. Please try again.')
      setMode('chat')
    } finally {
      setIsLoadingTicket(false)
    }
  }

  const closeTicketByNumber = async (ticketNumber) => {
    try {
      const ticketsRes = await fetch(apiUrl('/api/support-tickets'), {
        headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
      })
      if (!ticketsRes.ok) throw new Error('Failed to load tickets')
      const ticketsData = await ticketsRes.json()
      const ticket = ticketsData.tickets?.find(t => t.ticket_number === ticketNumber)

      if (!ticket) {
        alert(`Ticket ${ticketNumber} not found`)
        return
      }

      const closeRes = await fetch(apiUrl(`/api/support-tickets/${ticket.id}/close`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }
      })
      if (!closeRes.ok) throw new Error('Failed to close ticket')

      alert(`Ticket ${ticketNumber} has been marked as closed. Thank you for confirming the fix worked!`)

      const url = new URL(window.location.href)
      url.searchParams.delete('ticket_close')
      window.history.replaceState({}, '', url.toString())
    } catch (err) {
      console.error('Error closing ticket:', err)
      alert('Failed to close ticket. Please try again or contact support.')

      const url = new URL(window.location.href)
      url.searchParams.delete('ticket_close')
      window.history.replaceState({}, '', url.toString())
    }
  }

  const validateFile = (file) => {
    if (file.size > MAX_FILE_SIZE) {
      return `File "${file.name}" is too large. Maximum size is 100MB.`
    }
    const isImage = ALLOWED_IMAGE_TYPES.includes(file.type)
    const isDoc = ALLOWED_DOC_TYPES.includes(file.type)
    if (!isImage && !isDoc) {
      return `File "${file.name}" is not a supported format.`
    }
    return null
  }

  const processFiles = useCallback((fileList) => {
    const newFiles = []
    const errors = []

    Array.from(fileList).forEach(file => {
      const validationError = validateFile(file)
      if (validationError) {
        errors.push(validationError)
        return
      }
      const isImage = ALLOWED_IMAGE_TYPES.includes(file.type)
      const uploadedFile = { file, type: isImage ? 'image' : 'document' }
      if (isImage) uploadedFile.preview = URL.createObjectURL(file)
      newFiles.push(uploadedFile)
    })

    if (errors.length > 0) setError(errors.join(' '))
    if (newFiles.length > 0) setFiles(prev => [...prev, ...newFiles])
  }, [])

  const handleDragOver = useCallback((e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true) }, [])
  const handleDragLeave = useCallback((e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false) }, [])
  const handleDrop = useCallback((e) => {
    e.preventDefault(); e.stopPropagation(); setIsDragging(false); setError(null)
    if (e.dataTransfer.files?.length > 0) processFiles(e.dataTransfer.files)
  }, [processFiles])
  const handleFileSelect = useCallback((e) => {
    setError(null)
    if (e.target.files?.length > 0) processFiles(e.target.files)
    e.target.value = ''
  }, [processFiles])
  const removeFile = useCallback((index) => {
    setFiles(prev => {
      const newFiles = [...prev]
      const removed = newFiles.splice(index, 1)[0]
      if (removed.preview) URL.revokeObjectURL(removed.preview)
      return newFiles
    })
  }, [])

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  const getStatusBadge = (status) => {
    const styles = {
      open: 'bg-amber-100 text-amber-700',
      in_progress: 'bg-blue-100 text-blue-700',
      resolved: 'bg-green-100 text-green-700',
      closed: 'bg-gray-100 text-gray-700'
    }
    const labels = {
      open: 'Open',
      in_progress: 'In Progress',
      resolved: 'Resolved',
      closed: 'Closed'
    }
    return (
      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${styles[status] || styles.open}`}>
        {labels[status] || status?.replace('_', ' ')}
      </span>
    )
  }

  const handleSendMessage = async (e) => {
    e?.preventDefault()
    if (!message.trim() || isSubmitting) return
    setError(null)
    setIsSubmitting(true)

    try {
      if (mode === 'followup' && followupTicket) {
        // Add comment to existing ticket
        const userName = user?.first_name
          ? `${user.first_name} ${user.last_name || ''}`.trim()
          : user?.username

        const commentRes = await fetch(apiUrl(`/api/support-tickets/${followupTicket.id}/comments`), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
          },
          body: JSON.stringify({
            message,
            comment_type: 'user_comment',
            created_by_name: userName,
            created_by_email: user?.email,
            created_by_user_id: user?.id,
            is_internal: false
          })
        })

        if (!commentRes.ok) {
          const errData = await commentRes.json().catch(() => ({}))
          throw new Error(errData.error || 'Failed to add comment')
        }

        const commentData = await commentRes.json()

        // Update the followup ticket with new comments
        if (commentData.comments) {
          setFollowupTicket(prev => ({ ...prev, comments: commentData.comments }))
        } else {
          const detailRes = await fetch(apiUrl(`/api/support-tickets/${followupTicket.id}/with-comments`), {
            headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
          })
          if (detailRes.ok) {
            const detailData = await detailRes.json()
            setFollowupTicket(prev => ({ ...prev, comments: detailData.comments || [] }))
          }
        }

        setMessage('')
      } else {
        // Create new ticket from chat message
        const detectedType = detectTicketType(message)
        const generatedSubject = generateSubject(message)
        const pageContext = {
          url: window.location.href,
          pathname: window.location.pathname,
          title: document.title
        }

        const formData = new FormData()
        formData.append('type', detectedType)
        formData.append('subject', generatedSubject)
        formData.append('message', message)
        formData.append('page_url', pageContext.url)

        if (user) {
          formData.append('user', JSON.stringify({
            id: user.id,
            name: user.first_name
              ? `${user.first_name} ${user.last_name || ''}`.trim()
              : user.username,
            username: user.username,
            email: user.email,
            organization_id: user.organization_id
          }))
        }

        files.forEach((uploadedFile) => {
          formData.append('attachments', uploadedFile.file)
        })

        const response = await fetch(apiUrl('/api/support-tickets/submit'), {
          method: 'POST',
          headers: {
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
          },
          body: formData
        })

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}))
          throw new Error(errData.error || 'Failed to submit ticket')
        }

        const data = await response.json()

        // Clean up file previews
        files.forEach(f => { if (f.preview) URL.revokeObjectURL(f.preview) })

        setMessage('')
        setFiles([])
        setSuccessMessage(`Ticket ${data.ticket_number} created! We'll get back to you soon.`)

        // Clear success after 5 seconds
        setTimeout(() => setSuccessMessage(null), 5000)
      }
    } catch (err) {
      setError(err.message || 'Failed to send. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      setIsOpen(false)
      setError(null)
      setMode('chat')
      setFollowupTicket(null)
      setSuccessMessage(null)
    }
  }

  const handleOpenMyTickets = () => {
    setMode('my-tickets')
    setError(null)
    setSuccessMessage(null)
    loadMyTickets()
  }

  const handleOpenTicketDetail = (ticket) => {
    loadTicketForFollowup(ticket.id)
  }

  const handleBackFromFollowup = () => {
    setFollowupTicket(null)
    setError(null)
    setSuccessMessage(null)
    setMessage('')
    setMode('my-tickets')
    loadMyTickets()
  }

  const getUserName = () => {
    if (user?.first_name) return `${user.first_name} ${user.last_name || ''}`.trim()
    return user?.username || 'You'
  }

  return (
    <>
      {/* Floating Chat Button */}
      <div className={`fixed bottom-6 right-6 z-50 ${className}`}>
        <button
          onClick={() => setIsOpen(true)}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          className="relative h-14 w-14 rounded-full shadow-xl hover:shadow-2xl transition-all duration-200 bg-gradient-to-r from-gray-800 to-gray-900 hover:from-gray-900 hover:to-black text-white hover:scale-110 border-2 border-white flex items-center justify-center"
          title="Get Help"
        >
          <MessageCircle className="h-7 w-7" />
        </button>

        {/* Tooltip */}
        {isHovered && !isOpen && (
          <div className="absolute bottom-full right-0 mb-2 whitespace-nowrap">
            <div className="bg-gray-900 text-white text-sm py-2 px-3 rounded-lg shadow-lg">
              Need help? Chat with us
              <div className="absolute bottom-0 right-6 transform translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
            </div>
          </div>
        )}
      </div>

      {/* Chat Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:justify-end sm:p-6">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/40" onClick={handleClose} />

          {/* Chat Window */}
          <div className="relative bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl w-full sm:w-[420px] sm:max-w-[420px] h-[85vh] sm:h-[600px] flex flex-col overflow-hidden">

            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-gray-900 text-white">
              <div className="flex items-center gap-3">
                {mode === 'followup' && (
                  <button
                    onClick={handleBackFromFollowup}
                    className="p-1 hover:bg-gray-700 rounded transition-colors"
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </button>
                )}
                <div>
                  <h2 className="text-sm font-semibold">
                    {mode === 'followup' ? followupTicket?.ticket_number || 'Loading...' :
                     mode === 'my-tickets' ? 'My Tickets' :
                     'Support'}
                  </h2>
                  {mode === 'followup' && followupTicket && (
                    <p className="text-xs text-gray-400 truncate max-w-[200px]">{followupTicket.subject}</p>
                  )}
                  {mode === 'chat' && (
                    <p className="text-xs text-gray-400">Describe what you need help with</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1">
                {mode !== 'my-tickets' && (
                  <button
                    onClick={handleOpenMyTickets}
                    className="p-2 hover:bg-gray-700 rounded transition-colors text-gray-300 hover:text-white"
                    title="My Tickets"
                  >
                    <Ticket className="h-4 w-4" />
                  </button>
                )}
                {mode === 'my-tickets' && (
                  <button
                    onClick={() => { setMode('chat'); setError(null) }}
                    className="p-2 hover:bg-gray-700 rounded transition-colors text-gray-300 hover:text-white"
                    title="New Message"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                )}
                <button
                  onClick={handleClose}
                  className="p-2 hover:bg-gray-700 rounded transition-colors"
                  disabled={isSubmitting}
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* ==================== MY TICKETS VIEW ==================== */}
            {mode === 'my-tickets' && (
              <div className="flex-1 overflow-y-auto">
                {error && (
                  <div className="mx-4 mt-3 flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                    <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                    <span className="text-sm">{error}</span>
                  </div>
                )}

                {isLoadingMyTickets ? (
                  <div className="flex items-center justify-center p-12">
                    <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                  </div>
                ) : myTickets.length === 0 ? (
                  <div className="text-center py-16 px-6">
                    <Ticket className="h-10 w-10 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500 font-medium text-sm">No tickets yet</p>
                    <p className="text-xs text-gray-400 mt-1">Send a message to create your first ticket</p>
                    <button
                      onClick={() => setMode('chat')}
                      className="mt-4 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-black transition-colors text-sm"
                    >
                      Send a Message
                    </button>
                  </div>
                ) : (
                  <div className="p-2 space-y-1">
                    {myTickets.map((ticket) => (
                      <button
                        key={ticket.id}
                        onClick={() => handleOpenTicketDetail(ticket)}
                        className="w-full text-left px-3 py-3 rounded-lg hover:bg-gray-50 transition-colors group"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-0.5">
                              {getStatusBadge(ticket.status)}
                              <span className="text-xs text-gray-400">{formatDate(ticket.created_at)}</span>
                            </div>
                            <p className="text-sm text-gray-900 truncate">{ticket.subject}</p>
                            {ticket.comment_count > 0 && (
                              <p className="text-xs text-gray-400 mt-0.5 flex items-center gap-1">
                                <MessageSquare className="h-3 w-3" />
                                {ticket.comment_count} reply{ticket.comment_count !== 1 ? 'ies' : ''}
                              </p>
                            )}
                          </div>
                          <ChevronLeft className="h-4 w-4 text-gray-300 rotate-180 flex-shrink-0 mt-1 group-hover:text-gray-500" />
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ==================== LOADING VIEW ==================== */}
            {isLoadingTicket && (
              <div className="flex-1 flex items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            )}

            {/* ==================== CHAT / FOLLOWUP VIEW ==================== */}
            {!isLoadingTicket && mode !== 'my-tickets' && (
              <>
                {/* Messages Area */}
                <div
                  className="flex-1 overflow-y-auto px-4 py-4 space-y-3"
                  onDragOver={mode === 'chat' ? handleDragOver : undefined}
                  onDragLeave={mode === 'chat' ? handleDragLeave : undefined}
                  onDrop={mode === 'chat' ? handleDrop : undefined}
                >
                  {/* Drag overlay */}
                  {isDragging && (
                    <div className="absolute inset-0 bg-blue-50/90 z-10 flex items-center justify-center border-2 border-dashed border-blue-300 rounded-2xl m-1">
                      <div className="text-center">
                        <Upload className="h-8 w-8 text-blue-500 mx-auto mb-2" />
                        <p className="text-sm font-medium text-blue-700">Drop files here</p>
                      </div>
                    </div>
                  )}

                  {/* Welcome message for new chat */}
                  {mode === 'chat' && (
                    <div className="flex gap-3">
                      <div className="h-8 w-8 rounded-full bg-gray-900 flex items-center justify-center flex-shrink-0">
                        <MessageCircle className="h-4 w-4 text-white" />
                      </div>
                      <div className="bg-gray-100 rounded-2xl rounded-tl-md px-4 py-3 max-w-[85%]">
                        <p className="text-sm text-gray-700">
                          Hi{user?.first_name ? ` ${user.first_name}` : ''}! How can we help you today?
                        </p>
                        <p className="text-xs text-gray-500 mt-2">
                          Just describe your issue, question, or idea and we'll create a ticket for you automatically.
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          Currently viewing: <span className="font-medium">{document.title || window.location.pathname}</span>
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Followup mode: show conversation thread as chat bubbles */}
                  {mode === 'followup' && followupTicket && (
                    <>
                      {/* Status bar */}
                      <div className="flex items-center justify-center gap-2 py-1">
                        {getStatusBadge(followupTicket.status)}
                        <span className="text-xs text-gray-400">
                          {formatDate(followupTicket.created_at)}
                        </span>
                      </div>

                      {/* Original message - user bubble */}
                      <div className="flex gap-3 justify-end">
                        <div className="bg-gray-900 text-white rounded-2xl rounded-tr-md px-4 py-3 max-w-[85%]">
                          <p className="text-sm font-medium mb-1">{followupTicket.subject}</p>
                          <p className="text-sm whitespace-pre-wrap opacity-90">{followupTicket.message}</p>
                          {followupTicket.attachments?.length > 0 && (
                            <div className="mt-2 pt-2 border-t border-gray-700 space-y-1">
                              {followupTicket.attachments.map((att) => (
                                <a
                                  key={att.id}
                                  href={apiUrl(`/api/support-tickets/${followupTicket.id}/attachments/${att.id}/download`)}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-1 text-xs text-blue-300 hover:text-blue-200"
                                >
                                  <Paperclip className="h-3 w-3" />
                                  {att.filename}
                                </a>
                              ))}
                            </div>
                          )}
                          <p className="text-xs opacity-50 mt-1">{formatDate(followupTicket.created_at)}</p>
                        </div>
                        <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                          <span className="text-xs font-semibold text-blue-600">
                            {followupTicket.submitted_by_name?.charAt(0) || '?'}
                          </span>
                        </div>
                      </div>

                      {/* Comments as chat bubbles */}
                      {followupTicket.comments?.map((comment) => {
                        const isUser = comment.comment_type === 'user_comment' &&
                          (comment.created_by_email === user?.email || comment.created_by_user_id === user?.id)
                        const isSystem = comment.comment_type === 'system_resolution' || comment.comment_type === 'system_note'

                        if (isSystem) {
                          return (
                            <div key={comment.id} className="flex items-center justify-center py-1">
                              <div className="bg-green-50 border border-green-200 rounded-full px-4 py-1.5">
                                <p className="text-xs text-green-700 font-medium">
                                  {comment.comment_type === 'system_resolution' ? 'Ticket Resolved' : 'System Note'}
                                </p>
                                {comment.message && (
                                  <p className="text-xs text-green-600 mt-0.5">{comment.message}</p>
                                )}
                              </div>
                            </div>
                          )
                        }

                        if (isUser) {
                          // User's own message - right aligned
                          return (
                            <div key={comment.id} className="flex gap-3 justify-end">
                              <div className="bg-gray-900 text-white rounded-2xl rounded-tr-md px-4 py-3 max-w-[85%]">
                                <p className="text-sm whitespace-pre-wrap">{comment.message}</p>
                                <p className="text-xs opacity-50 mt-1">{formatDate(comment.created_at)}</p>
                              </div>
                              <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                                <span className="text-xs font-semibold text-blue-600">
                                  {comment.created_by_name?.charAt(0) || '?'}
                                </span>
                              </div>
                            </div>
                          )
                        }

                        // Support team message - left aligned
                        return (
                          <div key={comment.id} className="flex gap-3">
                            <div className="h-8 w-8 rounded-full bg-gray-900 flex items-center justify-center flex-shrink-0">
                              <MessageCircle className="h-4 w-4 text-white" />
                            </div>
                            <div className="bg-gray-100 rounded-2xl rounded-tl-md px-4 py-3 max-w-[85%]">
                              <p className="text-xs font-medium text-gray-500 mb-1">
                                {comment.created_by_name || 'Support Team'}
                              </p>
                              <p className="text-sm text-gray-700 whitespace-pre-wrap">{comment.message}</p>
                              <p className="text-xs text-gray-400 mt-1">{formatDate(comment.created_at)}</p>
                            </div>
                          </div>
                        )
                      })}

                      {/* Mark as Closed (if resolved) */}
                      {followupTicket.status === 'resolved' && (
                        <div className="flex items-center justify-center py-2">
                          <button
                            onClick={async () => {
                              if (confirm('Mark this ticket as closed?')) {
                                try {
                                  await fetch(apiUrl(`/api/support-tickets/${followupTicket.id}/close`), {
                                    method: 'POST',
                                    headers: {
                                      'Content-Type': 'application/json',
                                      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                                    }
                                  })
                                  alert(`Ticket closed. Thank you!`)
                                  handleBackFromFollowup()
                                } catch (err) {
                                  alert('Failed to close ticket.')
                                }
                              }
                            }}
                            className="px-4 py-2 bg-green-600 text-white rounded-full text-sm font-medium hover:bg-green-700 transition-colors"
                          >
                            <CheckCircle className="h-4 w-4 inline mr-1" />
                            Fix Worked — Close Ticket
                          </button>
                        </div>
                      )}

                      <div ref={messagesEndRef} />
                    </>
                  )}

                  {/* Success message */}
                  {successMessage && (
                    <div className="flex gap-3">
                      <div className="h-8 w-8 rounded-full bg-green-600 flex items-center justify-center flex-shrink-0">
                        <CheckCircle className="h-4 w-4 text-white" />
                      </div>
                      <div className="bg-green-50 border border-green-200 rounded-2xl rounded-tl-md px-4 py-3 max-w-[85%]">
                        <p className="text-sm text-green-700">{successMessage}</p>
                      </div>
                    </div>
                  )}

                  {/* Error message */}
                  {error && (
                    <div className="flex gap-3">
                      <div className="h-8 w-8 rounded-full bg-red-600 flex items-center justify-center flex-shrink-0">
                        <AlertCircle className="h-4 w-4 text-white" />
                      </div>
                      <div className="bg-red-50 border border-red-200 rounded-2xl rounded-tl-md px-4 py-3 max-w-[85%]">
                        <p className="text-sm text-red-700">{error}</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* File Previews (above input) */}
                {files.length > 0 && (
                  <div className="px-4 pb-2 flex gap-2 overflow-x-auto">
                    {files.map((uploadedFile, index) => (
                      <div key={index} className="relative flex-shrink-0">
                        {uploadedFile.type === 'image' && uploadedFile.preview ? (
                          <img src={uploadedFile.preview} alt={uploadedFile.file.name} className="h-16 w-16 object-cover rounded-lg border" />
                        ) : (
                          <div className="h-16 w-16 bg-gray-100 rounded-lg border flex flex-col items-center justify-center">
                            <FileText className="h-5 w-5 text-gray-400" />
                            <span className="text-[10px] text-gray-500 mt-0.5 truncate max-w-[56px] px-1">
                              {uploadedFile.file.name.split('.').pop()}
                            </span>
                          </div>
                        )}
                        <button
                          onClick={() => removeFile(index)}
                          className="absolute -top-1 -right-1 h-5 w-5 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Input Area */}
                <div className="border-t bg-white px-3 py-3">
                  <div className="flex items-end gap-2">
                    {/* Attach button (only for new tickets) */}
                    {mode === 'chat' && (
                      <>
                        <input
                          ref={fileInputRef}
                          type="file"
                          multiple
                          accept="image/png,image/jpeg,image/gif,image/webp,.pdf,.doc,.docx,.xls,.xlsx,.txt"
                          onChange={handleFileSelect}
                          className="hidden"
                          disabled={isSubmitting}
                        />
                        <button
                          type="button"
                          onClick={() => fileInputRef.current?.click()}
                          className="p-2 text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0"
                          title="Attach file"
                        >
                          <Paperclip className="h-5 w-5" />
                        </button>
                      </>
                    )}

                    {/* Text input */}
                    <textarea
                      ref={textareaRef}
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder={
                        mode === 'followup'
                          ? "Type a reply..."
                          : "Describe your issue, question, or idea..."
                      }
                      rows={1}
                      className="flex-1 resize-none border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 focus:border-transparent max-h-[120px] bg-gray-50"
                      disabled={isSubmitting}
                    />

                    {/* Send button */}
                    <button
                      onClick={handleSendMessage}
                      disabled={!message.trim() || isSubmitting}
                      className="p-2.5 bg-gray-900 text-white rounded-xl hover:bg-black transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
                    >
                      {isSubmitting ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                    </button>
                  </div>

                  {/* Context hint */}
                  {mode === 'chat' && (
                    <p className="text-[10px] text-gray-400 mt-1.5 px-1">
                      Page context auto-captured · Press Enter to send
                    </p>
                  )}
                  {mode === 'followup' && (
                    <p className="text-[10px] text-gray-400 mt-1.5 px-1">
                      Shift+Enter for new line · Enter to send
                    </p>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </>
  )
}
