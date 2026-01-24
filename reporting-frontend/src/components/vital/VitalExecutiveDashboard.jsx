import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { apiUrl } from '@/lib/api'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  LineChart,
  Line,
  Area,
  AreaChart
} from 'recharts'
import {
  DollarSign,
  Smartphone,
  Phone,
  TrendingUp,
  TrendingDown,
  Users,
  Target,
  RefreshCw,
  Activity
} from 'lucide-react'

// CEO Dashboard with real data from Finance, Mobile App, and Call Center
const VitalExecutiveDashboard = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  
  // Data states
  const [financeData, setFinanceData] = useState(null)
  const [mobileAppData, setMobileAppData] = useState(null)
  const [callCenterData, setCallCenterData] = useState(null)
  const [errors, setErrors] = useState({})

  const fetchAllData = async () => {
    setLoading(true)
    const token = localStorage.getItem('token')
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
    
    const newErrors = {}

    // Fetch Finance data (annual revenue)
    try {
      const financeRes = await fetch(apiUrl('/api/vital/finance/billing/summary?year=2026'), { headers })
      if (financeRes.ok) {
        const data = await financeRes.json()
        setFinanceData(data)
      }
    } catch (err) {
      newErrors.finance = err.message
    }

    // Fetch Mobile App data
    try {
      const mobileRes = await fetch(apiUrl('/api/vital/mobile-app/dashboard?days=30'), { headers })
      if (mobileRes.ok) {
        const result = await mobileRes.json()
        if (result.success) {
          setMobileAppData(result.data)
        }
      }
    } catch (err) {
      newErrors.mobileApp = err.message
    }

    // Fetch Call Center data
    try {
      const callRes = await fetch(apiUrl('/api/vital/zoom/dashboard'), { headers })
      if (callRes.ok) {
        const result = await callRes.json()
        if (result.success) {
          setCallCenterData(result.data)
        }
      }
    } catch (err) {
      newErrors.callCenter = err.message
    }

    setErrors(newErrors)
    setLastUpdated(new Date().toLocaleTimeString())
    setLoading(false)
  }

  useEffect(() => {
    fetchAllData()
  }, [])

  // Format helpers
  const formatCurrency = (value) => {
    if (!value) return '$0'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  const formatNumber = (value) => {
    if (!value) return '0'
    return new Intl.NumberFormat('en-US').format(Math.round(value))
  }

  const formatPercent = (value) => {
    if (!value) return '0%'
    return `${value.toFixed(1)}%`
  }

  // CEO KPI Card Component
  const CEOCard = ({ title, value, subtitle, icon: Icon, color, trend, trendDirection }) => (
    <Card className="shadow-lg hover:shadow-xl transition-shadow">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
        <div className={`p-2 rounded-lg bg-${color}-100`}>
          <Icon className={`h-5 w-5 text-${color}-600`} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-gray-900">{value}</div>
        <div className="flex items-center mt-1">
          {trend && (
            <span className={`flex items-center text-sm ${trendDirection === 'up' ? 'text-green-600' : trendDirection === 'down' ? 'text-red-600' : 'text-gray-500'}`}>
              {trendDirection === 'up' && <TrendingUp className="h-4 w-4 mr-1" />}
              {trendDirection === 'down' && <TrendingDown className="h-4 w-4 mr-1" />}
              {trend}
            </span>
          )}
          {!trend && subtitle && (
            <span className="text-sm text-gray-500">{subtitle}</span>
          )}
        </div>
      </CardContent>
    </Card>
  )

  // Calculate metrics
  const annualRevenue = financeData?.total_annual || financeData?.annual_revenue || 0
  const mau = mobileAppData?.mau || 0
  const stickiness = mobileAppData?.stickiness || 0
  const totalCalls = callCenterData?.call_stats?.total_calls || 0
  const avgCallDuration = callCenterData?.call_stats?.avg_duration_seconds || 0

  // Prepare trend data for Mobile App
  const dailyTrend = mobileAppData?.daily_trend || []
  const weeklyTrend = mobileAppData?.weekly_trend || []

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full min-h-[400px]">
        <LoadingSpinner size={50} />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">CEO Dashboard</h1>
          <p className="text-gray-600">
            Welcome back, {user?.first_name || 'User'}! Here's your business at a glance.
          </p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <span className="text-sm text-gray-500">Updated: {lastUpdated}</span>
          )}
          <Button onClick={fetchAllData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Main KPI Cards - One from each department */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Finance: Annual Revenue */}
        <CEOCard
          title="Annual Revenue (2026)"
          value={formatCurrency(annualRevenue)}
          icon={DollarSign}
          color="green"
          subtitle="From billing data"
        />

        {/* Mobile App: MAU */}
        <CEOCard
          title="Monthly Active Users"
          value={formatNumber(mau)}
          icon={Smartphone}
          color="blue"
          subtitle={`${formatPercent(stickiness)} stickiness`}
        />

        {/* Call Center: Total Calls */}
        <CEOCard
          title="Call Center Volume (30d)"
          value={formatNumber(totalCalls)}
          icon={Phone}
          color="purple"
          subtitle={avgCallDuration ? `Avg: ${Math.round(avgCallDuration / 60)}m per call` : 'Last 30 days'}
        />
      </div>

      {/* Secondary Metrics Row */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">New Users</p>
                <p className="text-2xl font-bold">{formatNumber(mobileAppData?.new_users || 0)}</p>
              </div>
              <Users className="h-8 w-8 text-blue-500 opacity-50" />
            </div>
            <p className="text-xs text-gray-400 mt-1">Last 30 days</p>
          </CardContent>
        </Card>

        <Card className="shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">App Stickiness</p>
                <p className="text-2xl font-bold">{formatPercent(stickiness)}</p>
              </div>
              <Target className="h-8 w-8 text-orange-500 opacity-50" />
            </div>
            <p className="text-xs text-gray-400 mt-1">Goal: 20%+</p>
          </CardContent>
        </Card>

        <Card className="shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Daily Active Users</p>
                <p className="text-2xl font-bold">{formatNumber(mobileAppData?.dau || mobileAppData?.avg_dau || 0)}</p>
              </div>
              <Activity className="h-8 w-8 text-green-500 opacity-50" />
            </div>
            <p className="text-xs text-gray-400 mt-1">Today's engagement</p>
          </CardContent>
        </Card>

        <Card className="shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Total Sessions</p>
                <p className="text-2xl font-bold">{formatNumber(mobileAppData?.total_sessions || 0)}</p>
              </div>
              <Smartphone className="h-8 w-8 text-purple-500 opacity-50" />
            </div>
            <p className="text-xs text-gray-400 mt-1">{formatNumber(mobileAppData?.sessions_per_user || 0)} per user</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Mobile App Daily Trend */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Mobile App Daily Active Users</CardTitle>
            <CardDescription>User engagement trend over the last 30 days</CardDescription>
          </CardHeader>
          <CardContent>
            {dailyTrend.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={dailyTrend}>
                  <defs>
                    <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => {
                      const date = new Date(value)
                      return `${date.getMonth() + 1}/${date.getDate()}`
                    }}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    formatter={(value) => [formatNumber(value), 'Users']}
                    labelFormatter={(label) => new Date(label).toLocaleDateString()}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="users" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    fillOpacity={1} 
                    fill="url(#colorUsers)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[250px] text-gray-400">
                No trend data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Weekly Active Users Trend */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Weekly Active Users Trend</CardTitle>
            <CardDescription>WAU and new user growth over 8 weeks</CardDescription>
          </CardHeader>
          <CardContent>
            {weeklyTrend.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={weeklyTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="week_start" 
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => {
                      const date = new Date(value)
                      return `${date.getMonth() + 1}/${date.getDate()}`
                    }}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    formatter={(value, name) => [formatNumber(value), name === 'wau' ? 'Weekly Active' : 'New Users']}
                    labelFormatter={(label) => `Week of ${new Date(label).toLocaleDateString()}`}
                  />
                  <Legend />
                  <Bar dataKey="wau" fill="#3b82f6" name="Weekly Active" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="new_users" fill="#10b981" name="New Users" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[250px] text-gray-400">
                No weekly data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Data Source Status */}
      <Card className="shadow">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Data Sources</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${financeData ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm text-gray-600">Finance</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${mobileAppData ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm text-gray-600">Mobile App (BigQuery)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${callCenterData ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm text-gray-600">Call Center (Zoom)</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default VitalExecutiveDashboard
