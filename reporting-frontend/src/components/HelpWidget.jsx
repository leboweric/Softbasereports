import { useState, useCallback, useRef, useEffect } from 'react'
import { apiUrl } from '../lib/api'
import {
  HelpCircle, X, Send, Bug, Lightbulb, HelpCircle as QuestionIcon,
  Loader2, CheckCircle, AlertCircle, Upload, Image, FileText, Trash2,
  MessageSquare, Paperclip
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

export default function HelpWidget({ user, className = '' }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const fileInputRef = useRef(null)

  // Mode: 'new' or 'followup'
  const [mode, setMode] = useState('new')
  const [followupTicket, setFollowupTicket] = useState(null)
  const [isLoadingTicket, setIsLoadingTicket] = useState(false)

  // Form state
  const [type, setType] = useState('bug')
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [files, setFiles] = useState([])

  // Drag state
  const [isDragging, setIsDragging] = useState(false)

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const token = localStorage.getItem('token')

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

  const loadTicketForFollowup = async (ticketNumber) => {
    setIsLoadingTicket(true)
    setError(null)

    try {
      // Find ticket by ticket_number
      const ticketsRes = await fetch(apiUrl('/api/support-tickets'), {
        headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
      })
      if (!ticketsRes.ok) throw new Error('Failed to load tickets')
      const ticketsData = await ticketsRes.json()
      const ticket = ticketsData.tickets?.find(t => t.ticket_number === ticketNumber)

      if (!ticket) {
        setError(`Ticket ${ticketNumber} not found`)
        setMode('new')
        return
      }

      // Load ticket with comments
      const detailRes = await fetch(apiUrl(`/api/support-tickets/${ticket.id}/with-comments`), {
        headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
      })
      if (!detailRes.ok) throw new Error('Failed to load ticket details')
      const detailData = await detailRes.json()

      // Load attachments
      try {
        const attRes = await fetch(apiUrl(`/api/support-tickets/${ticket.id}/attachments`), {
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

      // Clear URL parameter
      const url = new URL(window.location.href)
      url.searchParams.delete('ticket_followup')
      window.history.replaceState({}, '', url.toString())
    } catch (err) {
      console.error('Error loading ticket:', err)
      setError('Failed to load ticket. Please try again.')
      setMode('new')
    } finally {
      setIsLoadingTicket(false)
    }
  }

  const closeTicketByNumber = async (ticketNumber) => {
    try {
      // Find ticket by ticket_number
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

      // Call close endpoint
      const closeRes = await fetch(apiUrl(`/api/support-tickets/${ticket.id}/close`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }
      })
      if (!closeRes.ok) throw new Error('Failed to close ticket')

      alert(`Ticket ${ticketNumber} has been marked as closed. Thank you for confirming the fix worked!`)

      // Clear URL parameter
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
      return `File "${file.name}" is not a supported format. Please upload images (PNG, JPG, GIF, WebP) or documents (PDF, DOC, DOCX, XLS, XLSX, TXT).`
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
      const uploadedFile = {
        file,
        type: isImage ? 'image' : 'document'
      }
      if (isImage) {
        uploadedFile.preview = URL.createObjectURL(file)
      }
      newFiles.push(uploadedFile)
    })

    if (errors.length > 0) {
      setError(errors.join(' '))
    }
    if (newFiles.length > 0) {
      setFiles(prev => [...prev, ...newFiles])
    }
  }, [])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    setError(null)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files)
    }
  }, [processFiles])

  const handleFileSelect = useCallback((e) => {
    setError(null)
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files)
    }
    e.target.value = ''
  }, [processFiles])

  const removeFile = useCallback((index) => {
    setFiles(prev => {
      const newFiles = [...prev]
      const removed = newFiles.splice(index, 1)[0]
      if (removed.preview) {
        URL.revokeObjectURL(removed.preview)
      }
      return newFiles
    })
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
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

        setSuccess({
          ticketNumber: followupTicket.ticket_number,
          message: 'Your comment has been added successfully!'
        })

        // Reset form after 3 seconds
        setTimeout(() => {
          setMessage('')
          setFiles([])
          setSuccess(null)
          setMode('new')
          setFollowupTicket(null)
          setIsOpen(false)
        }, 3000)
      } else {
        // Create new ticket with FormData for file uploads
        const formData = new FormData()
        formData.append('type', type)
        formData.append('subject', subject)
        formData.append('message', message)
        formData.append('page_url', window.location.href)

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
        setSuccess({ ticketNumber: data.ticket_number })

        // Clean up file previews
        files.forEach(f => {
          if (f.preview) URL.revokeObjectURL(f.preview)
        })

        // Reset form after 3 seconds
        setTimeout(() => {
          setType('bug')
          setSubject('')
          setMessage('')
          setFiles([])
          setSuccess(null)
          setIsOpen(false)
        }, 3000)
      }
    } catch (err) {
      setError(err.message || 'Failed to submit. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      setIsOpen(false)
      setError(null)
      setMode('new')
      setFollowupTicket(null)
    }
  }

  const typeOptions = [
    {
      value: 'bug',
      label: 'Bug Report',
      icon: Bug,
      description: "Something isn't working correctly"
    },
    {
      value: 'enhancement',
      label: 'Enhancement',
      icon: Lightbulb,
      description: 'Suggest a new feature or improvement'
    },
    {
      value: 'question',
      label: 'Question',
      icon: QuestionIcon,
      description: 'Ask for help or clarification'
    }
  ]

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
    if (diffMins < 60) return `${diffMins} min ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  return (
    <>
      {/* Floating Help Button */}
      <div className={`fixed bottom-6 right-6 z-50 ${className}`}>
        <button
          onClick={() => setIsOpen(true)}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          className="relative h-14 w-14 rounded-full shadow-xl hover:shadow-2xl transition-all duration-200 bg-gradient-to-r from-gray-800 to-gray-900 hover:from-gray-900 hover:to-black text-white hover:scale-110 border-2 border-white flex items-center justify-center"
          title="Get Help"
        >
          <HelpCircle className="h-7 w-7" />
          <span className="absolute -top-0.5 -right-0.5 h-5 w-5 bg-amber-500 rounded-full flex items-center justify-center text-xs font-bold shadow-md">
            ?
          </span>
        </button>

        {/* Tooltip */}
        {isHovered && !isOpen && (
          <div className="absolute bottom-full right-0 mb-2 whitespace-nowrap">
            <div className="bg-gray-900 text-white text-sm py-2 px-3 rounded-lg shadow-lg">
              Need help? Submit a ticket
              <div className="absolute bottom-0 right-6 transform translate-y-1/2 rotate-45 w-2 h-2 bg-gray-900"></div>
            </div>
          </div>
        )}
      </div>

      {/* Modal Overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50"
            onClick={handleClose}
          />

          {/* Modal */}
          <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b bg-gray-900 text-white rounded-t-xl">
              <h2 className="text-lg font-semibold">
                {mode === 'followup' ? `Follow-up: ${followupTicket?.ticket_number}` : 'How can we help?'}
              </h2>
              <button
                onClick={handleClose}
                className="p-1 hover:bg-gray-700 rounded transition-colors"
                disabled={isSubmitting}
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Content - Scrollable */}
            <div className="flex-1 overflow-y-auto">
              {isLoadingTicket ? (
                <div className="flex items-center justify-center p-8">
                  <Loader2 className="h-8 w-8 animate-spin text-gray-600" />
                  <span className="ml-3 text-gray-600">Loading ticket...</span>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="p-4 space-y-4">
                  {/* Error Alert */}
                  {error && (
                    <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                      <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                      <span className="text-sm">{error}</span>
                    </div>
                  )}

                  {/* Success Alert */}
                  {success && (
                    <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700">
                      <CheckCircle className="h-5 w-5 flex-shrink-0" />
                      <div className="text-sm">
                        <p className="font-medium">{success.message || 'Ticket submitted successfully!'}</p>
                        <p>Ticket number: <strong>{success.ticketNumber}</strong></p>
                      </div>
                    </div>
                  )}

                  {!success && (
                    <>
                      {/* Conversation Thread (Follow-up mode) */}
                      {mode === 'followup' && followupTicket && (
                        <div className="space-y-3 bg-gray-50 p-4 rounded-lg border border-gray-200">
                          <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
                            <MessageSquare className="h-4 w-4" />
                            Conversation History
                          </div>

                          {/* Original Ticket */}
                          <div className="bg-white p-3 rounded-lg border border-gray-200">
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                                  <span className="text-xs font-semibold text-blue-600">
                                    {followupTicket.submitted_by_name?.charAt(0) || '?'}
                                  </span>
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-900">{followupTicket.submitted_by_name}</p>
                                  <p className="text-xs text-gray-500">{formatDate(followupTicket.created_at)}</p>
                                </div>
                              </div>
                              <span className={`text-xs px-2 py-1 rounded-full ${
                                followupTicket.status === 'open' ? 'bg-amber-100 text-amber-700' :
                                followupTicket.status === 'in_progress' ? 'bg-blue-100 text-blue-700' :
                                followupTicket.status === 'resolved' ? 'bg-green-100 text-green-700' :
                                'bg-gray-100 text-gray-700'
                              }`}>
                                {followupTicket.status?.replace('_', ' ')}
                              </span>
                            </div>
                            <p className="text-sm font-medium text-gray-900 mb-1">{followupTicket.subject}</p>
                            <p className="text-sm text-gray-600 whitespace-pre-wrap">{followupTicket.message}</p>

                            {/* Attachments */}
                            {followupTicket.attachments && followupTicket.attachments.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-gray-200">
                                <p className="text-xs font-medium text-gray-700 mb-2">Attachments:</p>
                                <div className="space-y-1">
                                  {followupTicket.attachments.map((attachment) => (
                                    <a
                                      key={attachment.id}
                                      href={apiUrl(`/api/support-tickets/${followupTicket.id}/attachments/${attachment.id}/download`)}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="flex items-center gap-2 text-xs text-blue-600 hover:text-blue-800 hover:underline"
                                    >
                                      <Paperclip className="h-3 w-3" />
                                      {attachment.filename} ({formatFileSize(attachment.size)})
                                    </a>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>

                          {/* Comments */}
                          {followupTicket.comments && followupTicket.comments.length > 0 && (
                            <div className="space-y-2">
                              {followupTicket.comments.map((comment) => (
                                <div key={comment.id} className={`p-3 rounded-lg border ${
                                  comment.comment_type === 'system_resolution'
                                    ? 'bg-green-50 border-green-200'
                                    : 'bg-white border-gray-200'
                                }`}>
                                  <div className="flex items-start gap-2 mb-1">
                                    <div className={`h-6 w-6 rounded-full flex items-center justify-center text-xs font-semibold ${
                                      comment.comment_type === 'system_resolution' || comment.comment_type === 'system_note'
                                        ? 'bg-blue-100 text-blue-600'
                                        : 'bg-gray-100 text-gray-600'
                                    }`}>
                                      {comment.comment_type === 'system_resolution' || comment.comment_type === 'system_note' ? '🤖' :
                                       comment.created_by_name?.charAt(0) || '?'}
                                    </div>
                                    <div className="flex-1">
                                      <div className="flex items-center gap-2">
                                        <p className="text-xs font-medium text-gray-900">
                                          {comment.comment_type === 'system_resolution' ? 'System (Resolved)' :
                                           comment.comment_type === 'system_note' ? 'Support Team' :
                                           comment.created_by_name || 'User'}
                                        </p>
                                        <p className="text-xs text-gray-500">{formatDate(comment.created_at)}</p>
                                      </div>
                                      <p className="text-sm text-gray-600 whitespace-pre-wrap mt-1">{comment.message}</p>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Mark as Closed Button (if ticket is resolved) */}
                          {followupTicket.status === 'resolved' && (
                            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                              <p className="text-sm text-green-800 mb-2">
                                <strong>Fix Worked?</strong> If you've tested the fix and everything is working correctly, please mark this ticket as closed.
                              </p>
                              <button
                                type="button"
                                onClick={async () => {
                                  if (confirm('Are you sure you want to mark this ticket as closed?')) {
                                    try {
                                      await fetch(apiUrl(`/api/support-tickets/${followupTicket.id}/close`), {
                                        method: 'POST',
                                        headers: {
                                          'Content-Type': 'application/json',
                                          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                                        }
                                      })
                                      alert(`Ticket ${followupTicket.ticket_number} has been marked as closed. Thank you for confirming the fix worked!`)
                                      setIsOpen(false)
                                      setMode('new')
                                      setFollowupTicket(null)
                                    } catch (err) {
                                      console.error('Error closing ticket:', err)
                                      alert('Failed to close ticket. Please try again.')
                                    }
                                  }
                                }}
                                className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium text-sm"
                              >
                                Mark as Closed
                              </button>
                            </div>
                          )}
                        </div>
                      )}

                      {/* New Ticket Form (New mode) */}
                      {mode === 'new' && (
                        <>
                          {/* Type Selection */}
                          <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">
                              What type of request is this?
                            </label>
                            <div className="space-y-2">
                              {typeOptions.map((option) => {
                                const Icon = option.icon
                                return (
                                  <label
                                    key={option.value}
                                    className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                                      type === option.value
                                        ? 'border-gray-900 bg-gray-50'
                                        : 'border-gray-200 hover:bg-gray-50'
                                    }`}
                                  >
                                    <input
                                      type="radio"
                                      name="type"
                                      value={option.value}
                                      checked={type === option.value}
                                      onChange={(e) => setType(e.target.value)}
                                      className="mt-1 text-gray-900 focus:ring-gray-500"
                                      disabled={isSubmitting}
                                    />
                                    <div className="flex-1">
                                      <div className="flex items-center gap-2">
                                        <Icon className={`h-4 w-4 ${
                                          option.value === 'bug' ? 'text-red-600' :
                                          option.value === 'enhancement' ? 'text-amber-600' :
                                          'text-blue-600'
                                        }`} />
                                        <span className="font-medium text-gray-900">{option.label}</span>
                                      </div>
                                      <p className="text-sm text-gray-500 mt-0.5">{option.description}</p>
                                    </div>
                                  </label>
                                )
                              })}
                            </div>
                          </div>

                          {/* Subject */}
                          <div className="space-y-1">
                            <label htmlFor="ticket-subject" className="block text-sm font-medium text-gray-700">
                              Subject
                            </label>
                            <input
                              id="ticket-subject"
                              type="text"
                              value={subject}
                              onChange={(e) => setSubject(e.target.value)}
                              placeholder={
                                type === 'bug' ? 'Brief description of the issue' :
                                type === 'enhancement' ? 'Brief description of your idea' :
                                'What do you need help with?'
                              }
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
                              required
                              disabled={isSubmitting}
                            />
                          </div>
                        </>
                      )}

                      {/* Message (both modes) */}
                      <div className="space-y-1">
                        <label htmlFor="ticket-message" className="block text-sm font-medium text-gray-700">
                          {mode === 'followup' ? 'Add a comment' :
                           type === 'bug' ? 'Describe the Issue' :
                           type === 'enhancement' ? 'Describe Your Idea' :
                           'Your Question'}
                        </label>
                        <textarea
                          id="ticket-message"
                          value={message}
                          onChange={(e) => setMessage(e.target.value)}
                          placeholder={
                            mode === 'followup'
                              ? "Describe what's still not working or provide additional information..."
                              : type === 'bug'
                              ? 'Please describe what you were trying to do, what went wrong, and any error messages you saw...'
                              : type === 'enhancement'
                              ? 'Please describe your idea in detail, including how it would help you...'
                              : 'Please provide as much detail as possible so we can help you...'
                          }
                          rows={4}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 resize-none"
                          required
                          disabled={isSubmitting}
                        />
                      </div>

                      {/* File Upload Area (new tickets only) */}
                      {mode === 'new' && (
                        <div className="space-y-2">
                          <label className="block text-sm font-medium text-gray-700">
                            Attachments <span className="text-gray-400 font-normal">(optional)</span>
                          </label>

                          {/* Drop Zone */}
                          <div
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                            className={`relative border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
                              isDragging
                                ? 'border-gray-900 bg-gray-50'
                                : 'border-gray-300 hover:border-gray-400'
                            }`}
                          >
                            <input
                              ref={fileInputRef}
                              type="file"
                              multiple
                              accept="image/png,image/jpeg,image/gif,image/webp,.pdf,.doc,.docx,.xls,.xlsx,.txt"
                              onChange={handleFileSelect}
                              className="hidden"
                              disabled={isSubmitting}
                            />

                            <Upload className={`h-8 w-8 mx-auto mb-2 ${isDragging ? 'text-gray-900' : 'text-gray-400'}`} />
                            <p className="text-sm text-gray-600">
                              <span className="font-medium text-gray-900">Click to upload</span> or drag and drop
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                              Screenshots, images, or documents (max 100MB each)
                            </p>
                          </div>

                          {/* File Previews */}
                          {files.length > 0 && (
                            <div className="space-y-2">
                              {files.map((uploadedFile, index) => (
                                <div
                                  key={index}
                                  className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg border border-gray-200"
                                >
                                  {uploadedFile.type === 'image' && uploadedFile.preview ? (
                                    <img
                                      src={uploadedFile.preview}
                                      alt={uploadedFile.file.name}
                                      className="h-12 w-12 object-cover rounded"
                                    />
                                  ) : (
                                    <div className="h-12 w-12 bg-gray-200 rounded flex items-center justify-center">
                                      {uploadedFile.type === 'image' ? (
                                        <Image className="h-6 w-6 text-gray-500" />
                                      ) : (
                                        <FileText className="h-6 w-6 text-gray-500" />
                                      )}
                                    </div>
                                  )}

                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-gray-900 truncate">
                                      {uploadedFile.file.name}
                                    </p>
                                    <p className="text-xs text-gray-500">
                                      {formatFileSize(uploadedFile.file.size)}
                                    </p>
                                  </div>

                                  <button
                                    type="button"
                                    onClick={() => removeFile(index)}
                                    className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                                    disabled={isSubmitting}
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </button>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Info text */}
                      {mode === 'new' && (
                        <p className="text-xs text-gray-500">
                          Current page URL will be included automatically
                        </p>
                      )}

                      {/* User Info Display */}
                      {user && (
                        <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                          {mode === 'followup' ? 'Commenting' : 'Submitting'} as: {user.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : user.username} ({user.email || 'no email'})
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex justify-end gap-3 pt-2">
                        <button
                          type="button"
                          onClick={handleClose}
                          className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                          disabled={isSubmitting}
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={isSubmitting || !message || (mode === 'new' && !subject)}
                          className="flex items-center gap-2 px-4 py-2 bg-gray-900 hover:bg-black text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isSubmitting ? (
                            <>
                              <Loader2 className="h-4 w-4 animate-spin" />
                              {mode === 'followup' ? 'Adding comment...' : 'Submitting...'}
                            </>
                          ) : (
                            <>
                              <Send className="h-4 w-4" />
                              {mode === 'followup' ? 'Add Comment' : 'Submit Ticket'}
                            </>
                          )}
                        </button>
                      </div>
                    </>
                  )}
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
