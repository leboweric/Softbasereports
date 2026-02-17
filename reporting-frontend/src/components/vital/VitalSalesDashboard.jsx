import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tooltip as UITooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip'
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
  PieChart,
  Pie,
  Cell,
  ComposedChart,
  Line,
  FunnelChart,
  Funnel,
  LabelList
} from 'recharts'
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Target,
  RefreshCw,
  Activity,
  Clock,
  Award,
  BarChart3,
  PieChart as PieChartIcon,
  ArrowLeft,
  ChevronDown,
  CheckCircle,
  XCircle,
  Filter,
  Info
} from 'lucide-react'

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#84cc16']

const VitalSalesDashboard = ({ user, onBack }) => {
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [timeframe, setTimeframe] = useState(365) // Default 1 year for sales
  const [showTimeframeDropdown, setShowTimeframeDropdown] = useState(false)
  
  // Data states
  const [salesOverview, setSalesOverview] = useState(null)
  const [winLossData, setWinLossData] = useState(null)
  const [topDeals, setTopDeals] = useState([])
  const [selectedPipeline, setSelectedPipeline] = useState('all')
  const [showPipelineDropdown, setShowPipelineDropdown] = useState(false)

  const timeframeOptions = [
    { value: 90, label: 'Last 90 days' },
    { value: 180, label: 'Last 6 months' },
    { value: 365, label: 'Last 12 months' },
    { value: 730, label: 'Last 2 years' },
  ]

  const fetchAllData = async () => {
    setLoading(true)
    const token = localStorage.getItem('token')
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }

    // Fetch Sales Overview
    try {
      const overviewRes = await fetch(apiUrl(`/api/vital/sales/overview`), { headers })
      if (overviewRes.ok) {
        const data = await overviewRes.json()
        if (data.success) {
          setSalesOverview(data.data)
        }
      }
    } catch (err) {
      console.error('Sales overview fetch error:', err)
    }

    // Fetch Win/Loss Analysis
    try {
      const winLossRes = await fetch(apiUrl(`/api/vital/sales/win-loss-analysis?days=${timeframe}`), { headers })
      if (winLossRes.ok) {
        const data = await winLossRes.json()
        if (data.success) {
          setWinLossData(data.data)
        }
      }
    } catch (err) {
      console.error('Win/loss analysis fetch error:', err)
    }

    // Fetch Top Deals
    try {
      const topDealsRes = await fetch(apiUrl(`/api/vital/sales/top-deals?limit=10&status=open`), { headers })
      if (topDealsRes.ok) {
        const data = await topDealsRes.json()
        if (data.success) {
          setTopDeals(data.data.deals || [])
        }
      }
    } catch (err) {
      console.error('Top deals fetch error:', err)
    }

    setLastUpdated(new Date())
    setLoading(false)
  }

  useEffect(() => {
    fetchAllData()
  }, [timeframe])

  const formatCurrency = (value) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`
    }
    return `$${value?.toFixed(0) || 0}`
  }

  const formatNumber = (value) => {
    if (!value) return '0'
    return value.toLocaleString()
  }

  // Metric Card Component
  const MetricCard = ({ title, value, subtitle, icon: Icon, trend, trendValue, color = 'blue', onClick, tooltip }) => (
    <Card 
      className={`${onClick ? 'cursor-pointer hover:shadow-lg transition-shadow' : ''}`}
      onClick={onClick}
    >
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-1">
              <p className="text-sm font-medium text-gray-500">{title}</p>
              {tooltip && (
                <TooltipProvider>
                  <UITooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-3.5 w-3.5 text-gray-400 cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="max-w-xs text-left">
                      <p>{tooltip}</p>
                    </TooltipContent>
                  </UITooltip>
                </TooltipProvider>
              )}
            </div>
            <p className="text-2xl font-bold mt-1">{value}</p>
            <p className="text-xs text-gray-400 mt-1">{subtitle}</p>
          </div>
          <div className={`p-3 rounded-full bg-${color}-100`}>
            <Icon className={`h-6 w-6 text-${color}-600`} />
          </div>
        </div>
        {trend && (
          <div className={`flex items-center mt-2 text-sm ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
            {trend === 'up' ? <TrendingUp className="h-4 w-4 mr-1" /> : <TrendingDown className="h-4 w-4 mr-1" />}
            {trendValue}
          </div>
        )}
      </CardContent>
    </Card>
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-500">Loading sales data...</span>
      </div>
    )
  }

  const summary = salesOverview?.summary || {}
  const dealsByPipeline = salesOverview?.deals_by_pipeline || []
  const monthlyTrend = salesOverview?.monthly_trend || []
  const winLossSummary = winLossData?.summary || {}
  const winLossTrend = winLossData?.monthly_trend || []

  // Prepare funnel data from deals by stage
  const dealsByStage = salesOverview?.deals_by_stage || []
  const openStages = dealsByStage.filter(s => !s.is_closed).sort((a, b) => b.total_value - a.total_value)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {onBack && (
            <Button variant="ghost" size="sm" onClick={onBack}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          )}
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Sales Dashboard</h1>
            <p className="text-gray-500">Pipeline, revenue, and sales performance metrics</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Timeframe Selector */}
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowTimeframeDropdown(!showTimeframeDropdown)}
              className="flex items-center gap-2"
            >
              <Clock className="h-4 w-4" />
              {timeframeOptions.find(o => o.value === timeframe)?.label}
              <ChevronDown className="h-4 w-4" />
            </Button>
            {showTimeframeDropdown && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border">
                {timeframeOptions.map(option => (
                  <button
                    key={option.value}
                    className={`block w-full text-left px-4 py-2 text-sm hover:bg-gray-100 ${
                      timeframe === option.value ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
                    }`}
                    onClick={() => {
                      setTimeframe(option.value)
                      setShowTimeframeDropdown(false)
                    }}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          <Button variant="outline" size="sm" onClick={fetchAllData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          {lastUpdated && (
            <span className="text-xs text-gray-400">
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Pipeline Value"
          value={formatCurrency(summary.pipeline_value)}
          subtitle="Open opportunities"
          icon={Target}
          color="blue"
          tooltip="Total dollar value of all currently open (non-closed) deals across all HubSpot pipelines. Represents potential revenue in the sales funnel."
        />
        <MetricCard
          title="Won Revenue (YTD)"
          value={formatCurrency(summary.won_value_ytd)}
          subtitle={`${summary.won_count_ytd || 0} deals closed YTD`}
          icon={DollarSign}
          color="green"
          tooltip="Total revenue from deals marked as 'Won' with a close date in the current calendar year. Only includes deals with a close date in the current year."
        />
        <MetricCard
          title="Win Rate"
          value={`${summary.win_rate || 0}%`}
          subtitle={`${summary.won_count || 0}W / ${summary.lost_count || 0}L`}
          icon={Award}
          color="purple"
          tooltip="Percentage of closed deals that were won. Calculated as: Won Deals ÷ (Won + Lost) × 100. Uses all-time deal history for a stable, long-term measure."
        />
        <MetricCard
          title="Avg Deal Size"
          value={formatCurrency(summary.avg_deal_size)}
          subtitle="Won deals average (YTD)"
          icon={BarChart3}
          color="amber"
          tooltip="Average dollar value of deals won this year. Calculated as: YTD Won Revenue ÷ Number of YTD Won Deals. Reflects current-year deal sizing trends."
        />
        <MetricCard
          title="Avg Sales Cycle"
          value={`${Math.round(summary.avg_sales_cycle_days || 0)} days`}
          subtitle="Create to close"
          icon={Clock}
          color="cyan"
          tooltip="Average number of days from deal creation to close for all won deals. Calculated as the mean of (Close Date − Create Date) across all historically won deals."
        />
      </div>

      {/* Pipeline by Source and Monthly Revenue Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pipeline by Source */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChartIcon className="h-5 w-5 text-blue-500" />
              Pipeline by Source
            </CardTitle>
            <CardDescription>Open deal value by pipeline</CardDescription>
          </CardHeader>
          <CardContent>
            {dealsByPipeline.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={dealsByPipeline.filter(p => p.open_value > 0)}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="open_value"
                      nameKey="pipeline"
                      label={({ pipeline, percent }) => `${pipeline}: ${(percent * 100).toFixed(0)}%`}
                    >
                      {dealsByPipeline.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => formatCurrency(value)} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-400">
                No pipeline data available
              </div>
            )}
            {/* Legend */}
            <div className="mt-4 grid grid-cols-2 gap-2">
              {dealsByPipeline.map((p, i) => (
                <div key={p.pipeline} className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                  <span className="truncate">{p.pipeline}</span>
                  <span className="text-gray-400 ml-auto">{formatCurrency(p.open_value)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Monthly Revenue Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-500" />
              Monthly Won Revenue
            </CardTitle>
            <CardDescription>Revenue closed by month</CardDescription>
          </CardHeader>
          <CardContent>
            {monthlyTrend.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={monthlyTrend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey="month" 
                      tick={{ fontSize: 12 }}
                      tickFormatter={(val) => {
                        const [year, month] = val.split('-')
                        return `${month}/${year.slice(2)}`
                      }}
                    />
                    <YAxis 
                      yAxisId="left"
                      tick={{ fontSize: 12 }}
                      tickFormatter={(val) => formatCurrency(val)}
                    />
                    <YAxis 
                      yAxisId="right"
                      orientation="right"
                      tick={{ fontSize: 12 }}
                    />
                    <Tooltip 
                      formatter={(value, name) => {
                        if (name === 'value') return [formatCurrency(value), 'Revenue']
                        return [value, 'Deals']
                      }}
                    />
                    <Legend />
                    <Bar yAxisId="left" dataKey="value" name="Revenue" fill="#10b981" radius={[4, 4, 0, 0]} />
                    <Line yAxisId="right" type="monotone" dataKey="count" name="Deals" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-400">
                No monthly data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Win/Loss Analysis and Top Opportunities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Win/Loss Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-purple-500" />
              Win/Loss Trend
            </CardTitle>
            <CardDescription>Monthly win rate over time</CardDescription>
          </CardHeader>
          <CardContent>
            {winLossTrend.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={winLossTrend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey="month" 
                      tick={{ fontSize: 12 }}
                      tickFormatter={(val) => {
                        const [year, month] = val.split('-')
                        return `${month}/${year.slice(2)}`
                      }}
                    />
                    <YAxis 
                      yAxisId="left"
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis 
                      yAxisId="right"
                      orientation="right"
                      tick={{ fontSize: 12 }}
                      domain={[0, 100]}
                      tickFormatter={(val) => `${val}%`}
                    />
                    <Tooltip />
                    <Legend />
                    <Bar yAxisId="left" dataKey="won_count" name="Won" fill="#10b981" stackId="a" />
                    <Bar yAxisId="left" dataKey="lost_count" name="Lost" fill="#ef4444" stackId="a" />
                    <Line yAxisId="right" type="monotone" dataKey="win_rate" name="Win Rate %" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 4 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-400">
                No win/loss data available
              </div>
            )}
            {/* Summary Stats */}
            <div className="mt-4 grid grid-cols-3 gap-4 pt-4 border-t">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{winLossSummary.total_won || 0}</p>
                <p className="text-xs text-gray-500">Total Won</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{winLossSummary.total_lost || 0}</p>
                <p className="text-xs text-gray-500">Total Lost</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-600">{winLossSummary.overall_win_rate || 0}%</p>
                <p className="text-xs text-gray-500">Overall Win Rate</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Top Open Opportunities */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5 text-amber-500" />
              Top Open Opportunities
            </CardTitle>
            <CardDescription>Largest deals in pipeline</CardDescription>
          </CardHeader>
          <CardContent>
            {topDeals.length > 0 ? (
              <div className="space-y-3">
                {topDeals.slice(0, 8).map((deal, index) => (
                  <div key={deal.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="text-lg font-bold text-gray-400">#{index + 1}</span>
                      <div>
                        <p className="font-medium text-gray-900 truncate max-w-[200px]">{deal.name}</p>
                        <p className="text-xs text-gray-500">{deal.stage}</p>
                      </div>
                    </div>
                    <span className="font-bold text-green-600">{formatCurrency(deal.amount)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-400">
                No open deals available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Pipeline Stages */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-blue-500" />
            Pipeline Stages
          </CardTitle>
          <CardDescription>Deal count and value by stage (open deals only)</CardDescription>
        </CardHeader>
        <CardContent>
          {openStages.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={openStages} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis type="number" tickFormatter={(val) => formatCurrency(val)} />
                  <YAxis 
                    type="category" 
                    dataKey="stage_name" 
                    width={150}
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip 
                    formatter={(value, name) => {
                      if (name === 'total_value') return [formatCurrency(value), 'Value']
                      return [value, 'Count']
                    }}
                  />
                  <Legend />
                  <Bar dataKey="total_value" name="Value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-80 flex items-center justify-center text-gray-400">
              No stage data available
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default VitalSalesDashboard
