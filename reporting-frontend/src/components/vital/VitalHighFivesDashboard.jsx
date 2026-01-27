import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
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
  LineChart,
  Line,
  Legend,
  ReferenceLine
} from 'recharts'
import {
  Heart,
  Award,
  Users,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  AlertCircle,
  Calendar,
  Trophy,
  Star,
  HandHeart
} from 'lucide-react'

const VitalHighFivesDashboard = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [dashboardData, setDashboardData] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [activeTab, setActiveTab] = useState('overview') // 'overview', 'leaderboard', 'recent'

  const fetchDashboardData = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/vital/high-fives/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to fetch High Fives data')
      }
      
      const result = await response.json()
      if (result.success) {
        setDashboardData(result.data)
        setLastUpdated(new Date().toLocaleTimeString())
      } else {
        throw new Error(result.error || 'Unknown error')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A'
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    } catch {
      return dateStr
    }
  }

  const getMonthName = (monthNum) => {
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 
                    'July', 'August', 'September', 'October', 'November', 'December']
    return months[monthNum - 1] || ''
  }

  const StatCard = ({ title, value, icon: Icon, color, subtitle, trend }) => (
    <Card className="shadow-lg hover:shadow-xl transition-shadow">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
        <div className={`p-2 rounded-lg ${color === 'green' ? 'bg-green-100' : color === 'blue' ? 'bg-blue-100' : color === 'purple' ? 'bg-purple-100' : color === 'yellow' ? 'bg-yellow-100' : 'bg-gray-100'}`}>
          <Icon className={`h-5 w-5 ${color === 'green' ? 'text-green-600' : color === 'blue' ? 'text-blue-600' : color === 'purple' ? 'text-purple-600' : color === 'yellow' ? 'text-yellow-600' : 'text-gray-600'}`} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-gray-900">{value}</div>
        {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
        {trend !== undefined && trend !== null && (
          <div className={`flex items-center mt-2 text-sm ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend >= 0 ? <TrendingUp className="h-4 w-4 mr-1" /> : <TrendingDown className="h-4 w-4 mr-1" />}
            {trend >= 0 ? '+' : ''}{trend.toFixed(1)}% vs last month
          </div>
        )}
      </CardContent>
    </Card>
  )

  const LeaderboardCard = ({ title, data, icon: Icon, color, type }) => (
    <Card className="shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className={`h-5 w-5 ${color === 'green' ? 'text-green-600' : 'text-blue-600'}`} />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {data && data.length > 0 ? (
          <div className="space-y-3">
            {data.map((item, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                    index === 0 ? 'bg-yellow-100 text-yellow-700' :
                    index === 1 ? 'bg-gray-100 text-gray-600' :
                    index === 2 ? 'bg-orange-100 text-orange-700' :
                    'bg-blue-50 text-blue-600'
                  }`}>
                    {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : index + 1}
                  </div>
                  <span className="font-medium text-gray-800">{item.name}</span>
                </div>
                <Badge variant="secondary" className={`${
                  color === 'green' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                }`}>
                  {item.count} {type === 'given' ? 'given' : 'received'}
                </Badge>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No data available</p>
        )}
      </CardContent>
    </Card>
  )

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-96">
        <LoadingSpinner size={50} />
        <p className="mt-4 text-gray-500">Loading High Fives recognition data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col justify-center items-center h-96">
        <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
        <p className="text-red-600 font-medium">Error loading High Fives data</p>
        <p className="text-gray-500 text-sm mt-2 max-w-md text-center">{error}</p>
        <Button onClick={fetchDashboardData} className="mt-4" variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    )
  }

  const currentMonth = dashboardData?.current_month || {}
  const previousMonth = dashboardData?.previous_month || {}
  const summary90Days = dashboardData?.summary_90_days || {}
  const recentRecognitions = dashboardData?.recent_recognitions || []
  const monthOverMonthChange = dashboardData?.month_over_month_change

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <HandHeart className="h-7 w-7 text-green-600" />
            High Fives Recognition
          </h2>
          <p className="text-gray-500 mt-1">Employee recognition tracking from Microsoft Teams</p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <span className="text-sm text-gray-500">Last updated: {lastUpdated}</span>
          )}
          <Button onClick={fetchDashboardData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'overview' 
              ? 'text-green-600 border-b-2 border-green-600' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('leaderboard')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'leaderboard' 
              ? 'text-green-600 border-b-2 border-green-600' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Leaderboard
        </button>
        <button
          onClick={() => setActiveTab('recent')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'recent' 
              ? 'text-green-600 border-b-2 border-green-600' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Recent Activity
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <>
          {/* Current Month Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title={`${getMonthName(currentMonth.month)} Recognitions`}
              value={currentMonth.total_recognitions || 0}
              icon={Heart}
              color="green"
              subtitle="High fives this month"
              trend={monthOverMonthChange}
            />
            <StatCard
              title="Unique Givers"
              value={currentMonth.unique_givers || 0}
              icon={Users}
              color="blue"
              subtitle="People giving recognition"
            />
            <StatCard
              title="Unique Receivers"
              value={currentMonth.unique_receivers || 0}
              icon={Award}
              color="purple"
              subtitle="People recognized"
            />
            <StatCard
              title="90-Day Total"
              value={summary90Days.total_recognitions || 0}
              icon={Trophy}
              color="yellow"
              subtitle="Last 3 months"
            />
          </div>

          {/* Top Performers This Month */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <LeaderboardCard
              title="Top Givers This Month"
              data={currentMonth.top_givers || []}
              icon={Star}
              color="green"
              type="given"
            />
            <LeaderboardCard
              title="Most Recognized This Month"
              data={currentMonth.top_receivers || []}
              icon={Award}
              color="blue"
              type="received"
            />
          </div>
        </>
      )}

      {/* Leaderboard Tab */}
      {activeTab === 'leaderboard' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <LeaderboardCard
            title="Top Givers (90 Days)"
            data={summary90Days.top_givers || []}
            icon={Star}
            color="green"
            type="given"
          />
          <LeaderboardCard
            title="Most Recognized (90 Days)"
            data={summary90Days.top_receivers || []}
            icon={Award}
            color="blue"
            type="received"
          />
        </div>
      )}

      {/* Recent Activity Tab */}
      {activeTab === 'recent' && (
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-green-600" />
              Recent Recognitions
            </CardTitle>
            <CardDescription>Last 7 days of High Fives</CardDescription>
          </CardHeader>
          <CardContent>
            {recentRecognitions.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>From</TableHead>
                    <TableHead>To</TableHead>
                    <TableHead>Message</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentRecognitions.map((rec, index) => (
                    <TableRow key={index}>
                      <TableCell className="text-gray-600">
                        {formatDate(rec.created_at)}
                      </TableCell>
                      <TableCell className="font-medium">
                        {rec.giver_name}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {rec.receivers?.map((receiver, i) => (
                            <Badge key={i} variant="secondary" className="bg-green-100 text-green-700">
                              {receiver}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-md truncate text-gray-600">
                        {rec.message_preview || '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <p className="text-gray-500 text-center py-8">No recent recognitions found</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Channel Info */}
      {dashboardData?.channel?.found && (
        <Card className="bg-green-50 border-green-200">
          <CardContent className="py-4">
            <div className="flex items-center gap-2 text-green-700">
              <HandHeart className="h-5 w-5" />
              <span className="font-medium">Connected to:</span>
              <span>{dashboardData.channel.team_name} → {dashboardData.channel.channel_name}</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default VitalHighFivesDashboard
