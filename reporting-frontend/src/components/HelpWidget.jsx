import { useState, useCallback, useRef } from 'react'
import { apiUrl } from '../lib/api'
import {
  HelpCircle, X, Send, Bug, Lightbulb, HelpCircle as QuestionIcon,
  Loader2, CheckCircle, AlertCircle, Upload, Image, FileText, Trash2
} from 'lucide-react'

const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100MB
const ALLOWED_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
const ALLOWED_DOC_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain'
]

export default function HelpWidget({ user, className = '' }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const fileInputRef = useRef(null)

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

  const validateFile = (file) => {
    if (file.size > MAX_FILE_SIZE) {
      return `File "${file.name}" is too large. Maximum size is 100MB.`
    }
    const isImage = ALLOWED_IMAGE_TYPES.includes(file.type)
    const isDoc = ALLOWED_DOC_TYPES.includes(file.type)
    if (!isImage && !isDoc) {
      return `File "${file.name}" is not a supported format. Please upload images (PNG, JPG, GIF, WebP) or documents (PDF, DOC, DOCX, TXT).`
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

      const token = localStorage.getItem('token')
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
    } catch (err) {
      setError(err.message || 'Failed to submit ticket. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      setIsOpen(false)
      setError(null)
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
          <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b bg-gray-900 text-white rounded-t-xl">
              <h2 className="text-lg font-semibold">How can we help?</h2>
              <button
                onClick={handleClose}
                className="p-1 hover:bg-gray-700 rounded transition-colors"
                disabled={isSubmitting}
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Content */}
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
                    <p className="font-medium">Ticket submitted successfully!</p>
                    <p>Your ticket number is: <strong>{success.ticketNumber}</strong></p>
                  </div>
                </div>
              )}

              {!success && (
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

                  {/* Message */}
                  <div className="space-y-1">
                    <label htmlFor="ticket-message" className="block text-sm font-medium text-gray-700">
                      {type === 'bug' ? 'Describe the Issue' :
                       type === 'enhancement' ? 'Describe Your Idea' :
                       'Your Question'}
                    </label>
                    <textarea
                      id="ticket-message"
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder={
                        type === 'bug'
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

                  {/* File Upload Area */}
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
                        accept="image/png,image/jpeg,image/gif,image/webp,.pdf,.doc,.docx,.txt"
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

                  {/* Info text */}
                  <p className="text-xs text-gray-500">
                    Current page URL will be included automatically
                  </p>

                  {/* User Info Display */}
                  {user && (
                    <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                      Submitting as: {user.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : user.username} ({user.email || 'no email'})
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
                      disabled={isSubmitting || !subject || !message}
                      className="flex items-center gap-2 px-4 py-2 bg-gray-900 hover:bg-black text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isSubmitting ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Submitting...
                        </>
                      ) : (
                        <>
                          <Send className="h-4 w-4" />
                          Submit Ticket
                        </>
                      )}
                    </button>
                  </div>
                </>
              )}
            </form>
          </div>
        </div>
      )}
    </>
  )
}
