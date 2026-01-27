import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts'
import {
  MessageSquare,
  TrendingUp,
  AlertCircle,
  RefreshCw,
  Send,
  CheckCircle,
  Clock,
  Archive,
  Eye,
  Lightbulb,
  Brain,
  BarChart3,
  FileQuestion
} from 'lucide-react'

const COLORS = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444', '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1']

const VitalAnonymousQuestionsDashboard = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState(null)
  const [dashboardData, setDashboardData] = useState(null)
  const [trendAnalysis, setTrendAnalysis] = useState(null)
  const [categories, setCategories] = useState([])
  const [activeTab, setActiveTab] = useState('submit') // 'submit', 'overview', 'questions', 'trends'
  
  // Form state
  const [questionText, setQuestionText] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [submitSuccess, setSubmitSuccess] = useState(false)

  const isAdmin = user?.role === 'admin' || user?.role === 'hr_admin' || user?.role === 'owner'

  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/vital/questions/categories')
      if (response.ok) {
        const result = await response.json()
        setCategories(result.categories || [])
      }
    } catch (err) {
      console.error('Error fetching categories:', err)
    }
  }

  const fetchDashboardData = async () => {
    if (!isAdmin) return
    
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/vital/questions/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to fetch dashboard data')
      }
      
      const result = await response.json()
      if (result.success) {
        setDashboardData(result.data)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchTrendAnalysis = async () => {
    if (!isAdmin) return
    
    setAnalyzing(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/vital/questions/analyze-trends', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (response.ok) {
        const result = await response.json()
        if (result.success) {
          setTrendAnalysis(result.data)
        }
      }
    } catch (err) {
      console.error('Error fetching trend analysis:', err)
    } finally {
      setAnalyzing(false)
    }
  }

  const handleSubmitQuestion = async () => {
    if (!questionText.trim() || questionText.length < 10) {
      setError('Please enter a question with at least 10 characters')
      return
    }
    
    setSubmitting(true)
    setError(null)
    setSubmitSuccess(false)
    
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/vital/questions/submit', {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question: questionText,
          category: selectedCategory || null
        })
      })
      
      const result = await response.json()
      
      if (result.success) {
        setSubmitSuccess(true)
        setQuestionText('')
        setSelectedCategory('')
        // Refresh dashboard if admin
        if (isAdmin) {
          fetchDashboardData()
        }
      } else {
        throw new Error(result.error || 'Failed to submit question')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const updateQuestionStatus = async (questionId, status) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/vital/questions/update-status', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question_id: questionId,
          status: status
        })
      })
      
      if (response.ok) {
        fetchDashboardData()
      }
    } catch (err) {
      console.error('Error updating status:', err)
    }
  }

  useEffect(() => {
    fetchCategories()
    if (isAdmin) {
      fetchDashboardData()
    } else {
      setLoading(false)
    }
  }, [isAdmin])

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A'
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    } catch {
      return dateStr
    }
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { color: 'bg-yellow-100 text-yellow-700', icon: Clock },
      reviewed: { color: 'bg-blue-100 text-blue-700', icon: Eye },
      addressed: { color: 'bg-green-100 text-green-700', icon: CheckCircle },
      archived: { color: 'bg-gray-100 text-gray-700', icon: Archive }
    }
    const config = statusConfig[status] || statusConfig.pending
    const Icon = config.icon
    return (
      <Badge className={`${config.color} flex items-center gap-1`}>
        <Icon className="h-3 w-3" />
        {status}
      </Badge>
    )
  }

  const getConcernBadge = (level) => {
    const colors = {
      High: 'bg-red-100 text-red-700',
      Medium: 'bg-yellow-100 text-yellow-700',
      Low: 'bg-green-100 text-green-700'
    }
    return <Badge className={colors[level] || colors.Medium}>{level}</Badge>
  }

  const getPriorityBadge = (priority) => {
    const colors = {
      High: 'bg-red-100 text-red-700 border-red-200',
      Medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      Low: 'bg-blue-100 text-blue-700 border-blue-200'
    }
    return <Badge variant="outline" className={colors[priority] || colors.Medium}>{priority} Priority</Badge>
  }

  // Prepare chart data
  const categoryChartData = dashboardData?.stats?.by_category?.map((item, index) => ({
    name: item.category,
    value: item.count,
    fill: COLORS[index % COLORS.length]
  })) || []

  const weeklyChartData = dashboardData?.stats?.weekly_trend || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <FileQuestion className="h-7 w-7 text-purple-600" />
            Anonymous Questions
          </h2>
          <p className="text-gray-500 mt-1">Submit questions anonymously and get answers from HR</p>
        </div>
        {isAdmin && (
          <Button onClick={() => { fetchDashboardData(); fetchTrendAnalysis(); }} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('submit')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'submit' 
              ? 'text-purple-600 border-b-2 border-purple-600' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <Send className="h-4 w-4 inline mr-2" />
          Submit Question
        </button>
        {isAdmin && (
          <>
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'overview' 
                  ? 'text-purple-600 border-b-2 border-purple-600' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <BarChart3 className="h-4 w-4 inline mr-2" />
              Overview
            </button>
            <button
              onClick={() => setActiveTab('questions')}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'questions' 
                  ? 'text-purple-600 border-b-2 border-purple-600' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <MessageSquare className="h-4 w-4 inline mr-2" />
              Questions
            </button>
            <button
              onClick={() => { setActiveTab('trends'); if (!trendAnalysis) fetchTrendAnalysis(); }}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'trends' 
                  ? 'text-purple-600 border-b-2 border-purple-600' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Brain className="h-4 w-4 inline mr-2" />
              AI Insights
            </button>
          </>
        )}
      </div>

      {/* Submit Question Tab */}
      {activeTab === 'submit' && (
        <Card className="shadow-lg max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Send className="h-5 w-5 text-purple-600" />
              Ask a Question Anonymously
            </CardTitle>
            <CardDescription>
              Your question will be submitted anonymously. HR will review and may address it in company communications.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {submitSuccess && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-2 text-green-700">
                <CheckCircle className="h-5 w-5" />
                <span>Your question has been submitted anonymously. Thank you!</span>
              </div>
            )}
            
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2 text-red-700">
                <AlertCircle className="h-5 w-5" />
                <span>{error}</span>
              </div>
            )}
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Your Question</label>
              <Textarea
                placeholder="Type your question here... (minimum 10 characters)"
                value={questionText}
                onChange={(e) => setQuestionText(e.target.value)}
                rows={4}
                className="resize-none"
                maxLength={2000}
              />
              <p className="text-xs text-gray-500 text-right">{questionText.length}/2000 characters</p>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Category (Optional)</label>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a category or leave blank for auto-detection" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((cat) => (
                    <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <Button 
              onClick={handleSubmitQuestion} 
              disabled={submitting || questionText.length < 10}
              className="w-full bg-purple-600 hover:bg-purple-700"
            >
              {submitting ? (
                <>
                  <LoadingSpinner size={16} className="mr-2" />
                  Submitting...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Submit Anonymously
                </>
              )}
            </Button>
            
            <p className="text-xs text-gray-500 text-center">
              🔒 Your identity is protected. Questions are reviewed by HR and may be addressed in company-wide communications.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Overview Tab (Admin Only) */}
      {activeTab === 'overview' && isAdmin && (
        <>
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <LoadingSpinner size={40} />
            </div>
          ) : (
            <div className="space-y-6">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="shadow-lg">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500">Total Questions</p>
                        <p className="text-3xl font-bold">{dashboardData?.stats?.total_questions || 0}</p>
                      </div>
                      <MessageSquare className="h-10 w-10 text-purple-200" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card className="shadow-lg">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500">Pending Review</p>
                        <p className="text-3xl font-bold text-yellow-600">{dashboardData?.pending_count || 0}</p>
                      </div>
                      <Clock className="h-10 w-10 text-yellow-200" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card className="shadow-lg">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500">Categories</p>
                        <p className="text-3xl font-bold">{dashboardData?.stats?.by_category?.length || 0}</p>
                      </div>
                      <BarChart3 className="h-10 w-10 text-blue-200" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card className="shadow-lg">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500">This Week</p>
                        <p className="text-3xl font-bold text-green-600">
                          {weeklyChartData[weeklyChartData.length - 1]?.count || 0}
                        </p>
                      </div>
                      <TrendingUp className="h-10 w-10 text-green-200" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Category Distribution */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Questions by Category</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {categoryChartData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={categoryChartData}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={100}
                            paddingAngle={2}
                            dataKey="value"
                            label={({ name, value }) => `${name}: ${value}`}
                          >
                            {categoryChartData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.fill} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="text-center text-gray-500 py-8">No data available</p>
                    )}
                  </CardContent>
                </Card>

                {/* Weekly Trend */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Weekly Trend</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {weeklyChartData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={weeklyChartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="week" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="count" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="text-center text-gray-500 py-8">No data available</p>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </>
      )}

      {/* Questions Tab (Admin Only) */}
      {activeTab === 'questions' && isAdmin && (
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-purple-600" />
              Recent Questions
            </CardTitle>
            <CardDescription>Review and manage anonymous employee questions</CardDescription>
          </CardHeader>
          <CardContent>
            {dashboardData?.recent_questions?.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="max-w-md">Question</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dashboardData.recent_questions.map((q) => (
                    <TableRow key={q.id}>
                      <TableCell className="text-gray-600 whitespace-nowrap">
                        {formatDate(q.submitted_at)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{q.category}</Badge>
                      </TableCell>
                      <TableCell className="max-w-md">
                        <p className="truncate">{q.question_text}</p>
                      </TableCell>
                      <TableCell>{getStatusBadge(q.status)}</TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {q.status === 'pending' && (
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => updateQuestionStatus(q.id, 'reviewed')}
                            >
                              <Eye className="h-3 w-3" />
                            </Button>
                          )}
                          {q.status === 'reviewed' && (
                            <Button 
                              size="sm" 
                              variant="outline"
                              className="text-green-600"
                              onClick={() => updateQuestionStatus(q.id, 'addressed')}
                            >
                              <CheckCircle className="h-3 w-3" />
                            </Button>
                          )}
                          <Button 
                            size="sm" 
                            variant="outline"
                            className="text-gray-500"
                            onClick={() => updateQuestionStatus(q.id, 'archived')}
                          >
                            <Archive className="h-3 w-3" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <p className="text-center text-gray-500 py-8">No questions submitted yet</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* AI Insights Tab (Admin Only) */}
      {activeTab === 'trends' && isAdmin && (
        <div className="space-y-6">
          {analyzing ? (
            <div className="flex flex-col justify-center items-center h-64">
              <Brain className="h-12 w-12 text-purple-500 animate-pulse mb-4" />
              <p className="text-gray-500">Analyzing questions with AI...</p>
            </div>
          ) : trendAnalysis ? (
            <>
              {/* Analysis Summary */}
              <Card className="shadow-lg bg-purple-50 border-purple-200">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-4">
                    <Brain className="h-10 w-10 text-purple-600" />
                    <div>
                      <h3 className="font-semibold text-purple-900">AI Analysis Complete</h3>
                      <p className="text-purple-700">
                        Analyzed {trendAnalysis.total_questions_analyzed} questions from the past {trendAnalysis.period_days} days
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Sentiment Overview */}
              {trendAnalysis.sentiment && (
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-purple-600" />
                      Employee Sentiment
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-500 mb-1">Overall Sentiment</p>
                        <Badge className={`text-lg ${
                          trendAnalysis.sentiment.overall === 'Positive' ? 'bg-green-100 text-green-700' :
                          trendAnalysis.sentiment.overall === 'Concerned' ? 'bg-yellow-100 text-yellow-700' :
                          trendAnalysis.sentiment.overall === 'Negative' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {trendAnalysis.sentiment.overall}
                        </Badge>
                      </div>
                      <div className="p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-500 mb-2">Key Concerns</p>
                        <div className="flex flex-wrap gap-1">
                          {trendAnalysis.sentiment.key_concerns?.map((concern, i) => (
                            <Badge key={i} variant="outline" className="text-red-600 border-red-200">{concern}</Badge>
                          ))}
                        </div>
                      </div>
                      <div className="p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-500 mb-2">Positive Themes</p>
                        <div className="flex flex-wrap gap-1">
                          {trendAnalysis.sentiment.positive_themes?.map((theme, i) => (
                            <Badge key={i} variant="outline" className="text-green-600 border-green-200">{theme}</Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Identified Trends */}
              {trendAnalysis.trends?.length > 0 && (
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-purple-600" />
                      Identified Trends
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {trendAnalysis.trends.map((trend, index) => (
                        <div key={index} className="p-4 border rounded-lg">
                          <div className="flex items-start justify-between mb-2">
                            <h4 className="font-semibold text-gray-900">{trend.trend}</h4>
                            {getConcernBadge(trend.concern_level)}
                          </div>
                          <p className="text-gray-600 text-sm">{trend.description}</p>
                          {trend.question_count && (
                            <p className="text-xs text-gray-500 mt-2">
                              Related to {trend.question_count} questions
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Suggested Actions */}
              {trendAnalysis.suggested_actions?.length > 0 && (
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-yellow-500" />
                      Suggested Actions
                    </CardTitle>
                    <CardDescription>AI-recommended actions based on question analysis</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {trendAnalysis.suggested_actions.map((action, index) => (
                        <div key={index} className="p-4 border rounded-lg bg-yellow-50 border-yellow-200">
                          <div className="flex items-start justify-between mb-2">
                            <h4 className="font-semibold text-gray-900">{action.action}</h4>
                            {getPriorityBadge(action.priority)}
                          </div>
                          <p className="text-gray-600 text-sm">{action.rationale}</p>
                          {action.addresses_trends?.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              <span className="text-xs text-gray-500">Addresses:</span>
                              {action.addresses_trends.map((trend, i) => (
                                <Badge key={i} variant="outline" className="text-xs">{trend}</Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Refresh Analysis Button */}
              <div className="flex justify-center">
                <Button onClick={fetchTrendAnalysis} variant="outline">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh AI Analysis
                </Button>
              </div>
            </>
          ) : (
            <Card className="shadow-lg">
              <CardContent className="py-12 text-center">
                <Brain className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-700 mb-2">No Analysis Available</h3>
                <p className="text-gray-500 mb-4">Click below to generate AI-powered insights from employee questions</p>
                <Button onClick={fetchTrendAnalysis} className="bg-purple-600 hover:bg-purple-700">
                  <Brain className="h-4 w-4 mr-2" />
                  Generate AI Analysis
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

export default VitalAnonymousQuestionsDashboard
