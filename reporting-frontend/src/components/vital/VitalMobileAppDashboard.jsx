import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  AreaChart,
  Area
} from 'recharts'
import {
  Smartphone,
  Users,
  TrendingUp,
  Activity,
  RefreshCw,
  AlertCircle,
  UserPlus,
  Clock,
  Layers,
  Target
} from 'lucide-react'
import { Button } from '@/components/ui/button'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#ff7300']
const PLATFORM_COLORS = { 'iOS': '#007AFF', 'Android': '#3DDC84', 'Windows': '#00A4EF', 'Other': '#6B7280' }

const VitalMobileAppDashboard = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [dashboardData, setDashboardData] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [dateRange, setDateRange] = useState('30') // days

  const fetchDashboardData = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/vital/mobile-app/dashboard?days=${dateRange}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch mobile app data')
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
  }, [dateRange])

  const formatNumber = (value) => {
    if (value === null || value === undefined) return '0'
    return new Intl.NumberFormat('en-US').format(value)
  }

  const formatPercent = (value) => {
    if (value === null || value === undefined) return '0%'
    return `${value.toFixed(1)}%`
  }

  const StatCard = ({ title, value, icon: Icon, color, subtitle, trend, trendLabel }) => (
    <Card className="shadow-lg hover:shadow-xl transition-shadow">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
        <div className={`p-2 rounded-lg`} style={{ backgroundColor: `${color}20` }}>
          <Icon className="h-5 w-5" style={{ color: color }} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-gray-900">{value}</div>
        {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
        {trend !== undefined && (
          <p className={`text-xs mt-2 ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(1)}% {trendLabel || 'vs previous period'}
          </p>
        )}
      </CardContent>
    </Card>
  )

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-96">
        <LoadingSpinner size={50} />
        <p className="mt-4 text-gray-500">Loading mobile app analytics...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col justify-center items-center h-96">
        <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
        <p className="text-red-600 font-medium">Error loading mobile app data</p>
        <p className="text-gray-500 text-sm mt-2">{error}</p>
        <Button onClick={fetchDashboardData} className="mt-4" variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    )
  }

  // Prepare data for charts
  const dailyTrend = dashboardData?.daily_trend || []
  const platformData = dashboardData?.platforms || []
  const topScreens = dashboardData?.top_screens || []
  const hourlyActivity = dashboardData?.hourly_activity || []
  const keyActions = dashboardData?.key_actions || []
  const weeklyTrend = dashboardData?.weekly_trend || []

  // Calculate stickiness color
  const stickiness = dashboardData?.stickiness || 0
  const stickinessColor = stickiness >= 20 ? '#00C49F' : stickiness >= 10 ? '#FFBB28' : '#FF8042'

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mobile App Analytics</h1>
          <p className="text-gray-500">VITAL WorkLife mobile app engagement metrics</p>
        </div>
        <div className="flex items-center gap-4">
          <select 
            value={dateRange} 
            onChange={(e) => setDateRange(e.target.value)}
            className="px-3 py-2 border rounded-md text-sm"
          >
            <option value="7">Last 7 days</option>
            <option value="14">Last 14 days</option>
            <option value="30">Last 30 days</option>
            <option value="60">Last 60 days</option>
          </select>
          {lastUpdated && (
            <span className="text-sm text-gray-500">Updated: {lastUpdated}</span>
          )}
          <Button onClick={fetchDashboardData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Metrics - Row 1 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Daily Active Users (DAU)"
          value={formatNumber(dashboardData?.dau || 0)}
          icon={Users}
          color="#0088FE"
          subtitle={`Avg: ${formatNumber(dashboardData?.avg_dau || 0)}`}
        />
        <StatCard
          title="Monthly Active Users (MAU)"
          value={formatNumber(dashboardData?.mau || 0)}
          icon={Smartphone}
          color="#8884d8"
          subtitle={`${formatNumber(dashboardData?.new_users || 0)} new users`}
        />
        <StatCard
          title="Stickiness (DAU/MAU)"
          value={formatPercent(dashboardData?.stickiness || 0)}
          icon={Target}
          color={stickinessColor}
          subtitle={`Goal: 20%+ | ${stickiness >= 20 ? '✓ Excellent' : stickiness >= 10 ? 'Good' : 'Needs work'}`}
        />
        <StatCard
          title="Total Sessions"
          value={formatNumber(dashboardData?.total_sessions || 0)}
          icon={Activity}
          color="#00C49F"
          subtitle={`${formatNumber(dashboardData?.sessions_per_user || 0)} per user`}
        />
      </div>

      {/* Key Metrics - Row 2 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="New Users"
          value={formatNumber(dashboardData?.new_users || 0)}
          icon={UserPlus}
          color="#FF8042"
          subtitle={`${formatPercent(dashboardData?.new_user_pct || 0)} of total`}
        />
        <StatCard
          title="Returning Users"
          value={formatNumber(dashboardData?.returning_users || 0)}
          icon={TrendingUp}
          color="#82ca9d"
          subtitle={`${formatPercent(dashboardData?.returning_user_pct || 0)} of total`}
        />
        <StatCard
          title="Avg Engagement"
          value={`${formatNumber(dashboardData?.avg_engagement_secs || 0)}s`}
          icon={Clock}
          color="#FFBB28"
          subtitle="Per session"
        />
        <StatCard
          title="Total Events"
          value={formatNumber(dashboardData?.total_events || 0)}
          icon={Layers}
          color="#6B7280"
          subtitle="User interactions"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* DAU Trend */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Daily Active Users Trend</CardTitle>
            <CardDescription>Users engaging with the app each day</CardDescription>
          </CardHeader>
          <CardContent>
            {dailyTrend.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={dailyTrend}>
                  <defs>
                    <linearGradient id="colorDau" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0088FE" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#0088FE" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 11 }}
                    tickFormatter={(val) => val.slice(5)} // Show MM-DD
                  />
                  <YAxis />
                  <Tooltip 
                    formatter={(value) => [formatNumber(value), 'DAU']}
                    labelFormatter={(label) => `Date: ${label}`}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="dau" 
                    stroke="#0088FE" 
                    fillOpacity={1} 
                    fill="url(#colorDau)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex justify-center items-center h-64 text-gray-500">
                No trend data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Platform Breakdown */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Platform Distribution</CardTitle>
            <CardDescription>Users by operating system</CardDescription>
          </CardHeader>
          <CardContent>
            {platformData.length > 0 ? (
              <div className="flex items-center">
                <ResponsiveContainer width="50%" height={250}>
                  <PieChart>
                    <Pie
                      data={platformData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="users"
                    >
                      {platformData.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={PLATFORM_COLORS[entry.platform] || COLORS[index % COLORS.length]} 
                        />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => [formatNumber(value), 'Users']} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="w-1/2 space-y-2">
                  {platformData.map((platform, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: PLATFORM_COLORS[platform.platform] || COLORS[index % COLORS.length] }}
                        />
                        <span className="font-medium">{platform.platform}</span>
                      </div>
                      <div className="text-right">
                        <span className="font-bold">{formatNumber(platform.users)}</span>
                        <span className="text-gray-500 text-sm ml-1">
                          ({formatPercent(platform.users / dashboardData.mau * 100)})
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex justify-center items-center h-64 text-gray-500">
                No platform data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Screens */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Top Screens</CardTitle>
            <CardDescription>Most viewed screens in the app</CardDescription>
          </CardHeader>
          <CardContent>
            {topScreens.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={topScreens} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis 
                    type="category" 
                    dataKey="screen" 
                    width={120} 
                    tick={{ fontSize: 11 }}
                  />
                  <Tooltip 
                    formatter={(value, name) => [formatNumber(value), name === 'views' ? 'Views' : 'Users']}
                  />
                  <Legend />
                  <Bar dataKey="views" fill="#0088FE" name="Views" radius={[0, 4, 4, 0]} />
                  <Bar dataKey="users" fill="#00C49F" name="Unique Users" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex justify-center items-center h-64 text-gray-500">
                No screen data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* User Activity by Hour */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Activity by Hour</CardTitle>
            <CardDescription>When users are most active (UTC)</CardDescription>
          </CardHeader>
          <CardContent>
            {hourlyActivity.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={hourlyActivity}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="hour" 
                    tickFormatter={(val) => `${val}:00`}
                    tick={{ fontSize: 10 }}
                  />
                  <YAxis />
                  <Tooltip 
                    formatter={(value) => [formatNumber(value), 'Users']}
                    labelFormatter={(label) => `${label}:00 UTC`}
                  />
                  <Bar dataKey="users" fill="#8884d8" radius={[4, 4, 0, 0]}>
                    {hourlyActivity.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.users > (dashboardData?.avg_hourly_users || 0) ? '#00C49F' : '#8884d8'} 
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex justify-center items-center h-64 text-gray-500">
                No hourly data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Key Actions & Weekly Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Key User Actions */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Key User Actions</CardTitle>
            <CardDescription>Important user behaviors tracked</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {keyActions.map((action, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium capitalize">{action.action.replace(/_/g, ' ')}</p>
                    <p className="text-sm text-gray-500">{formatNumber(action.unique_users)} unique users</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-gray-900">{formatNumber(action.count)}</p>
                    <p className="text-xs text-gray-500">total actions</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Weekly Trend */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Weekly Active Users</CardTitle>
            <CardDescription>WAU trend over recent weeks</CardDescription>
          </CardHeader>
          <CardContent>
            {weeklyTrend.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={weeklyTrend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="week" 
                    tick={{ fontSize: 10 }}
                  />
                  <YAxis />
                  <Tooltip 
                    formatter={(value, name) => [formatNumber(value), name === 'wau' ? 'WAU' : 'New Users']}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="wau" 
                    stroke="#0088FE" 
                    strokeWidth={2}
                    dot={{ fill: '#0088FE' }}
                    name="WAU"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="new_users" 
                    stroke="#00C49F" 
                    strokeWidth={2}
                    dot={{ fill: '#00C49F' }}
                    name="New Users"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex justify-center items-center h-64 text-gray-500">
                No weekly data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Retention Note */}
      <Card className="shadow-lg bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <TrendingUp className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-blue-900">Understanding Your Metrics</h3>
              <p className="text-sm text-blue-700 mt-1">
                <strong>DAU/MAU Ratio (Stickiness):</strong> A ratio of 20%+ indicates excellent engagement. 
                Your current ratio of {formatPercent(dashboardData?.stickiness || 0)} means users are 
                {stickiness >= 20 ? ' highly engaged with the app' : stickiness >= 10 ? ' moderately engaged' : ' visiting occasionally'}. 
                Industry benchmarks suggest 20-25% is excellent for utility apps.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default VitalMobileAppDashboard
