import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
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
  Area,
  AreaChart,
  Legend,
  ReferenceLine,
  Cell,
  ComposedChart,
  Line
} from 'recharts'
import {
  DollarSign,
  Smartphone,
  Phone,
  Users,
  Target,
  RefreshCw,
  Activity,
  Clock,
  PhoneIncoming,
  PhoneOutgoing,
  Building2,
  AlertTriangle,
  Calendar,
  TrendingUp,
  ChevronDown
} from 'lucide-react'

// CEO Dashboard organized by department sections
const VitalExecutiveDashboard = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [timeframe, setTimeframe] = useState(30) // Default 30 days
  const [showTimeframeDropdown, setShowTimeframeDropdown] = useState(false)
  
  // Data states
  const [financeData, setFinanceData] = useState(null)
  const [financeSummary, setFinanceSummary] = useState(null)
  const [clients, setClients] = useState([])
  const [renewals, setRenewals] = useState([])
  const [mobileAppData, setMobileAppData] = useState(null)
  const [callCenterData, setCallCenterData] = useState(null)
  const [callVolumeTrend, setCallVolumeTrend] = useState(null)
  const [atRiskRenewals, setAtRiskRenewals] = useState([])
  const [showRenewalsModal, setShowRenewalsModal] = useState(false)
  const [showAtRiskModal, setShowAtRiskModal] = useState(false)

  const timeframeOptions = [
    { value: 7, label: 'Last 7 days' },
    { value: 14, label: 'Last 14 days' },
    { value: 30, label: 'Last 30 days' },
    { value: 60, label: 'Last 60 days' },
    { value: 90, label: 'Last 90 days' },
  ]

  const fetchAllData = async () => {
    setLoading(true)
    const token = localStorage.getItem('token')
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }

    const currentYear = new Date().getFullYear()

    // Fetch Finance summary (includes monthly data, at_risk)
    try {
      const summaryRes = await fetch(apiUrl(`/api/vital/finance/billing/summary?year=${currentYear}`), { headers })
      if (summaryRes.ok) {
        const data = await summaryRes.json()
        setFinanceSummary(data)
      }
    } catch (err) {
      console.error('Finance summary fetch error:', err)
    }

    // Fetch Finance clients
    try {
      const clientsRes = await fetch(apiUrl('/api/vital/finance/clients'), { headers })
      if (clientsRes.ok) {
        const data = await clientsRes.json()
        setClients(data.clients || [])
      }
    } catch (err) {
      console.error('Clients fetch error:', err)
    }

    // Fetch Renewals (6 months for upcoming)
    try {
      const renewalsRes = await fetch(apiUrl('/api/vital/finance/renewals?months=6'), { headers })
      if (renewalsRes.ok) {
        const data = await renewalsRes.json()
        setRenewals(data.renewals || [])
      }
    } catch (err) {
      console.error('Renewals fetch error:', err)
    }

    // Fetch At-Risk Renewals (3 months)
    try {
      const atRiskRes = await fetch(apiUrl('/api/vital/finance/renewals?months=3'), { headers })
      if (atRiskRes.ok) {
        const data = await atRiskRes.json()
        setAtRiskRenewals(data.renewals || [])
      }
    } catch (err) {
      console.error('At-risk renewals fetch error:', err)
    }

    // Fetch spreadsheet data for total annual
    try {
      const spreadsheetRes = await fetch(apiUrl(`/api/vital/finance/billing/spreadsheet?year=${currentYear}&type=revrec`), { headers })
      if (spreadsheetRes.ok) {
        const data = await spreadsheetRes.json()
        setFinanceData(data)
      }
    } catch (err) {
      console.error('Finance spreadsheet fetch error:', err)
    }

    // Fetch Mobile App data with timeframe
    try {
      const mobileRes = await fetch(apiUrl(`/api/vital/mobile-app/dashboard?days=${timeframe}`), { headers })
      if (mobileRes.ok) {
        const result = await mobileRes.json()
        if (result.success) {
          setMobileAppData(result.data)
        }
      }
    } catch (err) {
      console.error('Mobile app fetch error:', err)
    }

    // Fetch Call Center data (basic stats)
    try {
      const callRes = await fetch(apiUrl('/api/vital/zoom/dashboard'), { headers })
      if (callRes.ok) {
        const result = await callRes.json()
        if (result.success) {
          setCallCenterData(result.data)
        }
      }
    } catch (err) {
      console.error('Call center fetch error:', err)
    }

    // Fetch Call Volume Trend with timeframe (this has accurate inbound/outbound)
    try {
      const trendRes = await fetch(apiUrl(`/api/vital/zoom/call-volume-trend?days=${timeframe}`), { headers })
      if (trendRes.ok) {
        const result = await trendRes.json()
        if (result.success) {
          setCallVolumeTrend(result.data)
        }
      }
    } catch (err) {
      console.error('Call volume trend fetch error:', err)
    }

    setLastUpdated(new Date().toLocaleTimeString())
    setLoading(false)
  }

  useEffect(() => {
    fetchAllData()
  }, [timeframe]) // Re-fetch when timeframe changes

  // Format helpers
  const formatCurrency = (value) => {
    if (!value) return '$0'
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`
    }
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`
    }
    return `$${value.toFixed(0)}`
  }

  const formatCurrencyFull = (value) => {
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

  const formatDuration = (seconds) => {
    if (!seconds) return '0m'
    const mins = Math.floor(seconds / 60)
    return `${mins}m`
  }

  // Section Header Component
  const SectionHeader = ({ title, icon: Icon, color, status }) => (
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="h-5 w-5 text-white" />
        </div>
        <h2 className="text-xl font-semibold text-gray-800">{title}</h2>
      </div>
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${status ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="text-xs text-gray-500">{status ? 'Connected' : 'Disconnected'}</span>
      </div>
    </div>
  )

  // Metric Card Component
  const MetricCard = ({ label, value, sublabel, icon: Icon, valueColor, onClick }) => (
    <div 
      className={`bg-white rounded-lg p-4 border border-gray-100 ${onClick ? 'cursor-pointer hover:bg-gray-50 hover:border-gray-200 transition-colors' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-500">{label}</span>
        {Icon && <Icon className="h-4 w-4 text-gray-400" />}
      </div>
      <div className={`text-2xl font-bold ${valueColor || 'text-gray-900'}`}>{value}</div>
      {sublabel && <div className="text-xs text-gray-400 mt-1">{sublabel}</div>}
      {onClick && <div className="text-xs text-blue-500 mt-2">Click to view details →</div>}
    </div>
  )

  // Finance Data
  const activeClients = clients.filter(c => c.status === 'active').length
  const totalClients = clients.length
  const atRiskRevenue = financeSummary?.at_risk?.annual_at_risk || 0
  const atRiskCount = financeSummary?.at_risk?.at_risk_count || 0
  const renewalsValue = renewals.reduce((sum, r) => sum + (parseFloat(r.annual_value) || 0), 0)
  const annualRevenue = financeData?.total_annual || 0

  // Prepare monthly revenue chart data
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const monthlyData = monthNames.map((month, idx) => {
    const monthNum = idx + 1
    const monthData = financeSummary?.monthly?.find(m => m.billing_month === monthNum)
    return {
      month,
      revenue: monthData?.total_revrec || 0,
    }
  })

  // Mobile App Data
  const mau = mobileAppData?.mau || 0
  const dau = mobileAppData?.dau || mobileAppData?.avg_dau || 0
  const stickiness = mobileAppData?.stickiness || 0
  const newUsers = mobileAppData?.new_users || 0
  const rawDailyTrend = mobileAppData?.daily_trend || []
  
  // Calculate 7-day moving average for Mobile App
  const dailyTrend = rawDailyTrend.map((day, idx, arr) => {
    const start = Math.max(0, idx - 6)
    const window = arr.slice(start, idx + 1)
    const ma7 = window.reduce((sum, d) => sum + (d.dau || 0), 0) / window.length
    return { ...day, ma7: Math.round(ma7 * 10) / 10 }
  })
  
  // Call Center Data - Use callVolumeTrend for accurate inbound/outbound
  const callTrend = callVolumeTrend?.trend || []
  const totalCalls = callVolumeTrend?.total_calls || 0
  
  // Calculate accurate inbound/outbound from trend data
  const inboundCalls = callTrend.reduce((sum, day) => sum + (day.inbound || 0), 0)
  const outboundCalls = callTrend.reduce((sum, day) => sum + (day.outbound || 0), 0)
  
  // Get avg duration from dashboard data (this is still accurate)
  const avgDuration = callCenterData?.call_stats?.avg_duration_seconds || 0

  // Call Volume Trend Data with 7-day moving average
  const avgCallsPerDay = callTrend.length > 0 ? callTrend[0]?.avg || 0 : 0
  const spikeCount = callTrend.filter(d => d.is_spike).length
  const spikeThreshold = Math.round(avgCallsPerDay * 1.5)
  
  // Calculate 7-day moving average for Call Center
  const callTrendWithMA = callTrend.map((day, idx, arr) => {
    const start = Math.max(0, idx - 6)
    const window = arr.slice(start, idx + 1)
    const ma7 = window.reduce((sum, d) => sum + (d.total || 0), 0) / window.length
    return { ...day, ma7: Math.round(ma7 * 10) / 10 }
  })

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full min-h-[400px]">
        <LoadingSpinner size={50} />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-8 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">CEO Dashboard</h1>
          <p className="text-gray-600">
            Welcome back, {user?.first_name || 'User'}! Here's your business at a glance.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Timeframe Selector */}
          <div className="relative">
            <button
              onClick={() => setShowTimeframeDropdown(!showTimeframeDropdown)}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <Calendar className="h-4 w-4" />
              {timeframeOptions.find(t => t.value === timeframe)?.label}
              <ChevronDown className="h-4 w-4" />
            </button>
            {showTimeframeDropdown && (
              <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                {timeframeOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => {
                      setTimeframe(option.value)
                      setShowTimeframeDropdown(false)
                    }}
                    className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg ${
                      timeframe === option.value ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <span className="text-sm text-gray-500">Updated: {lastUpdated}</span>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={fetchAllData}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* FINANCE SECTION */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <SectionHeader 
          title="Finance" 
          icon={DollarSign} 
          color="bg-green-500" 
          status={!!financeData || !!financeSummary}
        />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <MetricCard 
            label="Active Clients" 
            value={formatNumber(activeClients)} 
            sublabel={`${totalClients} total`}
            icon={Building2}
          />
          <MetricCard 
            label="Upcoming Renewals" 
            value={formatNumber(renewals.length)} 
            sublabel={`${formatCurrency(renewalsValue)} in next 6 months`}
            icon={Calendar}
            onClick={() => setShowRenewalsModal(true)}
          />
          <MetricCard 
            label="At Risk Revenue" 
            value={formatCurrency(atRiskRevenue)} 
            sublabel={`${atRiskCount} clients renewing in 3 months`}
            icon={AlertTriangle}
            valueColor="text-amber-500"
            onClick={() => setShowAtRiskModal(true)}
          />
          <MetricCard 
            label="Annual Revenue" 
            value={formatCurrency(annualRevenue)} 
            sublabel={`${new Date().getFullYear()} RevRec`}
            icon={DollarSign}
          />
        </div>
        
        {/* Monthly Revenue Chart */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-4">Monthly Revenue (2026)</h3>
          {monthlyData.some(m => m.revenue > 0) ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis 
                  tick={{ fontSize: 11 }} 
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
                />
                <Tooltip 
                  formatter={(value) => [formatCurrencyFull(value), 'Revenue']}
                />
                <Bar dataKey="revenue" fill="#10b981" name="Revenue" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[220px] text-gray-400">
              No monthly revenue data available
            </div>
          )}
        </div>
      </div>

      {/* MOBILE APP SECTION */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <SectionHeader 
          title="Mobile App" 
          icon={Smartphone} 
          color="bg-blue-500" 
          status={!!mobileAppData}
        />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <MetricCard 
            label="Monthly Active Users" 
            value={formatNumber(mau)} 
            sublabel={`Last ${timeframe} days`}
            icon={Users}
          />
          <MetricCard 
            label="Daily Active Users" 
            value={formatNumber(dau)} 
            sublabel="Average"
            icon={Activity}
          />
          <MetricCard 
            label="Stickiness (DAU/MAU)" 
            value={formatPercent(stickiness)} 
            sublabel="Goal: 20%+"
            icon={Target}
          />
          <MetricCard 
            label="New Users" 
            value={formatNumber(newUsers)} 
            sublabel={`Last ${timeframe} days`}
            icon={Users}
          />
        </div>
        
        {/* Mobile App Chart */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-4">Daily Active Users Trend</h3>
          {dailyTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <ComposedChart data={dailyTrend}>
                <defs>
                  <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 11 }}
                  tickFormatter={(value) => {
                    const date = new Date(value)
                    return `${date.getMonth() + 1}/${date.getDate()}`
                  }}
                />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip 
                  formatter={(value, name) => [formatNumber(value), name === 'ma7' ? '7-Day Avg' : 'Daily Users']}
                  labelFormatter={(label) => new Date(label).toLocaleDateString()}
                />
                <Area 
                  type="monotone" 
                  dataKey="dau" 
                  stroke="#93c5fd" 
                  strokeWidth={1}
                  fillOpacity={1} 
                  fill="url(#colorUsers)" 
                  name="Daily Users"
                />
                <Line 
                  type="monotone" 
                  dataKey="ma7" 
                  stroke="#1d4ed8" 
                  strokeWidth={3}
                  dot={false}
                  name="7-Day Avg"
                />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[220px] text-gray-400">
              No trend data available
            </div>
          )}
          <div className="flex justify-center gap-6 mt-2 text-xs text-gray-500">
            <span className="flex items-center gap-1"><span className="w-3 h-3 bg-blue-200 rounded"></span> Daily Users</span>
            <span className="flex items-center gap-1"><span className="w-8 h-0.5 bg-blue-700"></span> 7-Day Moving Avg</span>
          </div>
        </div>
      </div>

      {/* CALL CENTER / CUSTOMER SERVICE SECTION */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <SectionHeader 
          title="Call Center / Customer Service" 
          icon={Phone} 
          color="bg-purple-500" 
          status={!!callVolumeTrend}
        />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <MetricCard 
            label={`Total Calls (${timeframe}d)`}
            value={formatNumber(totalCalls)} 
            sublabel="All call types"
            icon={Phone}
          />
          <MetricCard 
            label="Inbound Calls" 
            value={formatNumber(inboundCalls)} 
            sublabel={totalCalls > 0 ? `${Math.round(inboundCalls / totalCalls * 100)}% of total` : '0% of total'}
            icon={PhoneIncoming}
          />
          <MetricCard 
            label="Outbound Calls" 
            value={formatNumber(outboundCalls)} 
            sublabel={totalCalls > 0 ? `${Math.round(outboundCalls / totalCalls * 100)}% of total` : '0% of total'}
            icon={PhoneOutgoing}
          />
          <MetricCard 
            label="Avg Call Duration" 
            value={formatDuration(avgDuration)} 
            sublabel="Per call"
            icon={Clock}
          />
        </div>
        
        {/* Call Volume Chart */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-700">Daily Call Volume (Last {timeframe} Days)</h3>
            {spikeCount > 0 && (
              <span className="text-sm text-red-500 flex items-center gap-1">
                <AlertTriangle className="h-4 w-4" />
                {spikeCount} spikes detected
                <span className="text-gray-400">(above {spikeThreshold} calls)</span>
              </span>
            )}
          </div>
          {callTrendWithMA.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={220}>
                <ComposedChart data={callTrendWithMA}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 10 }}
                    tickFormatter={(value) => {
                      const date = new Date(value)
                      return `${date.getMonth() + 1}/${date.getDate()}`
                    }}
                  />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip 
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload
                        return (
                          <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                            <p className="font-medium text-gray-900">{new Date(label).toLocaleDateString()}</p>
                            <p className="text-sm text-gray-600">Total: {data.total} calls</p>
                            <p className="text-sm text-gray-600">Inbound: {data.inbound}</p>
                            <p className="text-sm text-gray-600">Outbound: {data.outbound}</p>
                            <p className="text-sm text-purple-600">7-Day Avg: {data.ma7}</p>
                            {data.is_spike && (
                              <p className="text-sm text-red-500 font-medium mt-1">⚠️ Volume Spike</p>
                            )}
                          </div>
                        )
                      }
                      return null
                    }}
                  />
                  <Bar dataKey="total" name="Calls" radius={[2, 2, 0, 0]}>
                    {callTrendWithMA.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.is_spike ? '#ef4444' : '#c4b5fd'} 
                      />
                    ))}
                  </Bar>
                  <Line 
                    type="monotone" 
                    dataKey="ma7" 
                    stroke="#7c3aed" 
                    strokeWidth={3}
                    dot={false}
                    name="7-Day Avg"
                  />
                </ComposedChart>
              </ResponsiveContainer>
              {/* Legend */}
              <div className="flex items-center justify-center gap-6 mt-3 text-xs text-gray-500">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-purple-300" />
                  <span>Daily Volume</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-red-500" />
                  <span>Spike (&gt;1.5x avg)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-0.5 bg-purple-600" />
                  <span>7-Day Moving Avg</span>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-[220px] text-gray-400">
              No call volume data available
            </div>
          )}
        </div>
      </div>

      {/* Upcoming Renewals Modal */}
      {showRenewalsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowRenewalsModal(false)}>
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full mx-4 max-h-[80vh] overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-gray-900">Upcoming Renewals</h2>
                <p className="text-sm text-gray-500">Clients renewing in the next 6 months</p>
              </div>
              <button onClick={() => setShowRenewalsModal(false)} className="text-gray-400 hover:text-gray-600">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <div className="mb-4 flex items-center justify-between">
                <span className="text-sm text-gray-600">{renewals.length} renewals totaling {formatCurrency(renewalsValue)}</span>
              </div>
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Client</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Renewal Date</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Solution</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tier</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Annual Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {renewals.sort((a, b) => new Date(a.renewal_date) - new Date(b.renewal_date)).map((renewal, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{renewal.billing_name}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {new Date(renewal.renewal_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">{renewal.solution_type}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          renewal.tier === 'A' ? 'bg-green-100 text-green-800' :
                          renewal.tier === 'B' ? 'bg-blue-100 text-blue-800' :
                          renewal.tier === 'C' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {renewal.tier}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-right font-medium text-gray-900">
                        {formatCurrencyFull(parseFloat(renewal.annual_value))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* At Risk Revenue Modal */}
      {showAtRiskModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowAtRiskModal(false)}>
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full mx-4 max-h-[80vh] overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-200 flex items-center justify-between bg-amber-50">
              <div>
                <h2 className="text-xl font-bold text-amber-800 flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5" />
                  At Risk Revenue
                </h2>
                <p className="text-sm text-amber-600">Clients renewing in the next 3 months requiring attention</p>
              </div>
              <button onClick={() => setShowAtRiskModal(false)} className="text-amber-400 hover:text-amber-600">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <div className="mb-4 p-4 bg-amber-50 rounded-lg border border-amber-200">
                <div className="flex items-center justify-between">
                  <span className="text-amber-800 font-medium">{atRiskRenewals.length} clients at risk</span>
                  <span className="text-2xl font-bold text-amber-600">
                    {formatCurrency(atRiskRenewals.reduce((sum, r) => sum + (parseFloat(r.annual_value) || 0), 0))}
                  </span>
                </div>
                <p className="text-sm text-amber-600 mt-1">Total revenue at risk in the next 3 months</p>
              </div>
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Client</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Renewal Date</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Solution</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tier</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Annual Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {atRiskRenewals.sort((a, b) => new Date(a.renewal_date) - new Date(b.renewal_date)).map((renewal, idx) => (
                    <tr key={idx} className="hover:bg-amber-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{renewal.billing_name}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        <span className="text-amber-600 font-medium">
                          {new Date(renewal.renewal_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">{renewal.solution_type}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          renewal.tier === 'A' ? 'bg-green-100 text-green-800' :
                          renewal.tier === 'B' ? 'bg-blue-100 text-blue-800' :
                          renewal.tier === 'C' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {renewal.tier}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-right font-bold text-amber-600">
                        {formatCurrencyFull(parseFloat(renewal.annual_value))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default VitalExecutiveDashboard
