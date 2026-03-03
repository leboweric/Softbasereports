import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Button } from '@/components/ui/button'
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
  Phone,
  PhoneIncoming,
  PhoneOutgoing,
  Users,
  Clock,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Video,
  Headphones
} from 'lucide-react'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d']

const VitalZoomDashboard = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [dashboardData, setDashboardData] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [activeTab, setActiveTab] = useState('calls') // 'calls', 'meetings', 'queues'

  const fetchDashboardData = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/vital/zoom/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to fetch Zoom data')
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

  const formatNumber = (value) => {
    return new Intl.NumberFormat('en-US').format(value || 0)
  }

  const formatDuration = (seconds) => {
    if (!seconds) return '0:00'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  const formatDateTime = (dateStr) => {
    if (!dateStr) return 'N/A'
    try {
      return new Date(dateStr).toLocaleString()
    } catch {
      return dateStr
    }
  }

  const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
    <Card className="shadow-lg hover:shadow-xl transition-shadow">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
        <div className={`p-2 rounded-lg bg-${color}-100`}>
          <Icon className={`h-5 w-5 text-${color}-600`} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-gray-900">{value}</div>
        {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
      </CardContent>
    </Card>
  )

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-96">
        <LoadingSpinner size={50} />
        <p className="mt-4 text-gray-500">Loading Zoom Call Center data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col justify-center items-center h-96">
        <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
        <p className="text-red-600 font-medium">Error loading Zoom data</p>
        <p className="text-gray-500 text-sm mt-2 max-w-md text-center">{error}</p>
        <Button onClick={fetchDashboardData} className="mt-4" variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    )
  }

  const callStats = dashboardData?.call_stats || {}
  const phoneUsers = dashboardData?.phone_users || {}
  const meetingStats = dashboardData?.meeting_stats || {}
  const callQueues = dashboardData?.call_queues || {}
  const recentCalls = dashboardData?.recent_calls || []

  // Prepare chart data
  const callDirectionData = [
    { name: 'Inbound', value: callStats.inbound || 0, fill: '#0088FE' },
    { name: 'Outbound', value: callStats.outbound || 0, fill: '#00C49F' }
  ]

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Call Center Dashboard</h1>
          <p className="text-gray-500">Zoom Phone analytics for VITAL WorkLife</p>
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

      {/* Connection Status */}
      <Card className="bg-green-50 border-green-200">
        <CardContent className="flex items-center gap-3 py-4">
          <CheckCircle className="h-5 w-5 text-green-600" />
          <span className="text-green-700 font-medium">Connected to Zoom</span>
          <Badge variant="outline" className="ml-2 bg-white">
            {callStats.period || 'Last 30 days'}
          </Badge>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Calls"
          value={formatNumber(callStats.total_calls)}
          icon={Phone}
          color="blue"
          subtitle="Last 30 days"
        />
        <StatCard
          title="Inbound Calls"
          value={formatNumber(callStats.inbound)}
          icon={PhoneIncoming}
          color="green"
          subtitle={`${callStats.total_calls ? Math.round((callStats.inbound / callStats.total_calls) * 100) : 0}% of total`}
        />
        <StatCard
          title="Outbound Calls"
          value={formatNumber(callStats.outbound)}
          icon={PhoneOutgoing}
          color="purple"
          subtitle={`${callStats.total_calls ? Math.round((callStats.outbound / callStats.total_calls) * 100) : 0}% of total`}
        />
        <StatCard
          title="Avg Call Duration"
          value={formatDuration(Math.round(callStats.avg_duration_seconds || 0))}
          icon={Clock}
          color="yellow"
          subtitle={`Total: ${formatDuration(callStats.total_duration_seconds || 0)}`}
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Phone Users"
          value={formatNumber(phoneUsers.total)}
          icon={Headphones}
          color="indigo"
          subtitle={`${phoneUsers.active || 0} active`}
        />
        <StatCard
          title="Meetings This Month"
          value={formatNumber(meetingStats.total_meetings)}
          icon={Video}
          color="pink"
          subtitle={`${formatNumber(meetingStats.total_participants || 0)} participants`}
        />
        <StatCard
          title="Call Queues"
          value={formatNumber(callQueues.total)}
          icon={Users}
          color="orange"
          subtitle="Active queues"
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('calls')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'calls'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Recent Calls
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'analytics'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Analytics
        </button>
        <button
          onClick={() => setActiveTab('queues')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'queues'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Call Queues
        </button>
      </div>

      {activeTab === 'calls' && (
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Recent Calls</CardTitle>
            <CardDescription>Last 7 days of call activity</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Direction</TableHead>
                    <TableHead>Date/Time</TableHead>
                    <TableHead>Caller</TableHead>
                    <TableHead>Callee</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Result</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentCalls.length > 0 ? (
                    recentCalls.map((call, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Badge variant={call.direction === 'inbound' ? 'default' : 'secondary'}>
                            {call.direction === 'inbound' ? (
                              <PhoneIncoming className="h-3 w-3 mr-1" />
                            ) : (
                              <PhoneOutgoing className="h-3 w-3 mr-1" />
                            )}
                            {call.direction}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm">{formatDateTime(call.date_time)}</TableCell>
                        <TableCell>
                          <div className="text-sm font-medium">{call.caller_name || 'Unknown'}</div>
                          <div className="text-xs text-gray-500">{call.caller_number || 'N/A'}</div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm font-medium">{call.callee_name || 'Unknown'}</div>
                          <div className="text-xs text-gray-500">{call.callee_number || 'N/A'}</div>
                        </TableCell>
                        <TableCell>{formatDuration(call.duration)}</TableCell>
                        <TableCell>
                          <Badge variant={call.result === 'call_connected' ? 'success' : 'outline'}>
                            {call.result || 'unknown'}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-gray-500 py-8">
                        No recent calls found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'analytics' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Call Direction Pie Chart */}
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Call Direction</CardTitle>
              <CardDescription>Inbound vs Outbound calls</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={callDirectionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${formatNumber(value)}`}
                  >
                    {callDirectionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Meeting Stats */}
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Meeting Statistics</CardTitle>
              <CardDescription>{meetingStats.month}/{meetingStats.year}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-4 bg-blue-50 rounded-lg">
                  <div>
                    <p className="text-sm text-gray-600">Total Meetings</p>
                    <p className="text-2xl font-bold text-blue-600">{formatNumber(meetingStats.total_meetings)}</p>
                  </div>
                  <Video className="h-8 w-8 text-blue-400" />
                </div>
                <div className="flex justify-between items-center p-4 bg-green-50 rounded-lg">
                  <div>
                    <p className="text-sm text-gray-600">Total Participants</p>
                    <p className="text-2xl font-bold text-green-600">{formatNumber(meetingStats.total_participants)}</p>
                  </div>
                  <Users className="h-8 w-8 text-green-400" />
                </div>
                <div className="flex justify-between items-center p-4 bg-purple-50 rounded-lg">
                  <div>
                    <p className="text-sm text-gray-600">Total Minutes</p>
                    <p className="text-2xl font-bold text-purple-600">{formatNumber(meetingStats.total_minutes)}</p>
                  </div>
                  <Clock className="h-8 w-8 text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'queues' && (
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Call Queues</CardTitle>
            <CardDescription>Active call queues and their status</CardDescription>
          </CardHeader>
          <CardContent>
            {callQueues.queues && callQueues.queues.length > 0 ? (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Queue Name</TableHead>
                      <TableHead>Extension</TableHead>
                      <TableHead>Members</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {callQueues.queues.map((queue, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-medium">{queue.name || 'Unnamed Queue'}</TableCell>
                        <TableCell>{queue.extension_number || 'N/A'}</TableCell>
                        <TableCell>{queue.members_count || 0}</TableCell>
                        <TableCell>
                          <Badge variant={queue.status === 'active' ? 'success' : 'secondary'}>
                            {queue.status || 'unknown'}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                {callQueues.error ? (
                  <p>Unable to load call queues: {callQueues.error}</p>
                ) : (
                  <p>No call queues configured</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default VitalZoomDashboard
