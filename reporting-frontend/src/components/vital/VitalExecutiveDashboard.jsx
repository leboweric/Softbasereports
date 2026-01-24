import React, { useState, useEffect } from 'react'
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
  TrendingUp
} from 'lucide-react'

// CEO Dashboard organized by department sections
const VitalExecutiveDashboard = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  
  // Data states
  const [financeData, setFinanceData] = useState(null)
  const [financeSummary, setFinanceSummary] = useState(null)
  const [clients, setClients] = useState([])
  const [renewals, setRenewals] = useState([])
  const [mobileAppData, setMobileAppData] = useState(null)
  const [callCenterData, setCallCenterData] = useState(null)
  const [callVolumeTrend, setCallVolumeTrend] = useState(null)

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

    // Fetch Renewals
    try {
      const renewalsRes = await fetch(apiUrl('/api/vital/finance/renewals?months=6'), { headers })
      if (renewalsRes.ok) {
        const data = await renewalsRes.json()
        setRenewals(data.renewals || [])
      }
    } catch (err) {
      console.error('Renewals fetch error:', err)
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
      console.error('Mobile app fetch error:', err)
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
      console.error('Call center fetch error:', err)
    }

    // Fetch Call Volume Trend
    try {
      const trendRes = await fetch(apiUrl('/api/vital/zoom/call-volume-trend?days=30'), { headers })
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
  }, [])

  // Format helpers
  const formatCurrency = (value) => {
    if (!value) return '$0'
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`
    }
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
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
    const minutes = Math.round(seconds / 60)
    return `${minutes}m`
  }

  // Section Header Component
  const SectionHeader = ({ title, icon: Icon, color, status }) => (
    <div className="flex items-center justify-between mb-4">
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
  const MetricCard = ({ label, value, sublabel, icon: Icon, valueColor }) => (
    <div className="bg-white rounded-lg p-4 border border-gray-100">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-500">{label}</span>
        {Icon && <Icon className="h-4 w-4 text-gray-400" />}
      </div>
      <div className={`text-2xl font-bold ${valueColor || 'text-gray-900'}`}>{value}</div>
      {sublabel && <div className="text-xs text-gray-400 mt-1">{sublabel}</div>}
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
  const dailyTrend = mobileAppData?.daily_trend || []
  
  // Call Center Data
  const callStats = callCenterData?.call_stats || {}
  const totalCalls = callStats.total_calls || 0
  const inboundCalls = callStats.inbound || 0
  const outboundCalls = callStats.outbound || 0
  const avgDuration = callStats.avg_duration_seconds || 0

  // Call Volume Trend Data
  const callTrend = callVolumeTrend?.trend || []
  const avgCallsPerDay = callTrend.length > 0 ? callTrend[0]?.avg || 0 : 0
  const spikeCount = callTrend.filter(d => d.is_spike).length

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

      {/* FINANCE SECTION */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <SectionHeader 
          title="Finance" 
          icon={DollarSign} 
          color="bg-green-500" 
          status={!!financeSummary || !!financeData}
        />
        
        {/* Finance Metric Cards */}
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
          />
          <MetricCard 
            label="At Risk Revenue" 
            value={formatCurrency(atRiskRevenue)} 
            sublabel={`${atRiskCount} clients renewing in 3 months`}
            icon={AlertTriangle}
            valueColor="text-yellow-600"
          />
          <MetricCard 
            label="Annual Revenue" 
            value={formatCurrency(annualRevenue)} 
            sublabel="2026 RevRec"
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
            sublabel="Last 30 days"
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
            sublabel="Last 30 days"
            icon={Users}
          />
        </div>
        
        {/* Mobile App Chart */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-4">Daily Active Users Trend</h3>
          {dailyTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={dailyTrend}>
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
            <div className="flex items-center justify-center h-[200px] text-gray-400">
              No trend data available
            </div>
          )}
        </div>
      </div>

      {/* CALL CENTER / CUSTOMER SERVICE SECTION */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <SectionHeader 
          title="Call Center / Customer Service" 
          icon={Phone} 
          color="bg-purple-500" 
          status={!!callCenterData}
        />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <MetricCard 
            label="Total Calls (30d)" 
            value={formatNumber(totalCalls)} 
            sublabel="All call types"
            icon={Phone}
          />
          <MetricCard 
            label="Inbound Calls" 
            value={formatNumber(inboundCalls)} 
            sublabel={totalCalls ? `${Math.round((inboundCalls/totalCalls)*100)}% of total` : ''}
            icon={PhoneIncoming}
          />
          <MetricCard 
            label="Outbound Calls" 
            value={formatNumber(outboundCalls)} 
            sublabel={totalCalls ? `${Math.round((outboundCalls/totalCalls)*100)}% of total` : ''}
            icon={PhoneOutgoing}
          />
          <MetricCard 
            label="Avg Call Duration" 
            value={formatDuration(avgDuration)} 
            sublabel="Per call"
            icon={Clock}
          />
        </div>

        {/* Call Volume Trend Chart with Spike Detection */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-700">Daily Call Volume (Last 30 Days)</h3>
            {spikeCount > 0 && (
              <div className="flex items-center gap-2 text-sm">
                <AlertTriangle className="h-4 w-4 text-red-500" />
                <span className="text-red-600 font-medium">{spikeCount} spike{spikeCount > 1 ? 's' : ''} detected</span>
                <span className="text-gray-400">(above {formatNumber(avgCallsPerDay * 1.5)} calls)</span>
              </div>
            )}
          </div>
          {callTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <ComposedChart data={callTrend}>
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
                  formatter={(value, name) => {
                    if (name === 'avg') return [formatNumber(value), 'Daily Average']
                    return [formatNumber(value), name === 'total' ? 'Total Calls' : name]
                  }}
                  labelFormatter={(label) => new Date(label).toLocaleDateString()}
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload
                      return (
                        <div className="bg-white p-3 border rounded-lg shadow-lg">
                          <p className="font-medium">{new Date(label).toLocaleDateString()}</p>
                          <p className="text-sm">Total: <span className="font-bold">{data.total}</span></p>
                          <p className="text-sm text-blue-600">Inbound: {data.inbound}</p>
                          <p className="text-sm text-green-600">Outbound: {data.outbound}</p>
                          {data.is_spike && (
                            <p className="text-sm text-red-600 font-medium mt-1">⚠️ Volume Spike</p>
                          )}
                        </div>
                      )
                    }
                    return null
                  }}
                />
                <ReferenceLine 
                  y={avgCallsPerDay} 
                  stroke="#9ca3af" 
                  strokeDasharray="5 5" 
                  label={{ value: 'Avg', position: 'right', fontSize: 10, fill: '#9ca3af' }}
                />
                <ReferenceLine 
                  y={avgCallsPerDay * 1.5} 
                  stroke="#ef4444" 
                  strokeDasharray="3 3" 
                  label={{ value: 'Spike Threshold', position: 'right', fontSize: 10, fill: '#ef4444' }}
                />
                <Bar dataKey="total" name="total" radius={[4, 4, 0, 0]}>
                  {callTrend.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.is_spike ? '#ef4444' : '#8b5cf6'} 
                    />
                  ))}
                </Bar>
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[220px] text-gray-400">
              No call volume data available
            </div>
          )}
          {callTrend.length > 0 && (
            <div className="flex items-center gap-6 mt-3 text-xs text-gray-500">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-purple-500"></div>
                <span>Normal Volume</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-red-500"></div>
                <span>Spike (>1.5x avg)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 border-t-2 border-dashed border-gray-400"></div>
                <span>Daily Average ({formatNumber(avgCallsPerDay)})</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default VitalExecutiveDashboard
