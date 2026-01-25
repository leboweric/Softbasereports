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
  PieChart,
  Pie,
  Cell,
  ComposedChart,
  Line,
  RadialBarChart,
  RadialBar
} from 'recharts'
import {
  Users,
  Heart,
  Clock,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Smile,
  Frown,
  Meh,
  Smartphone,
  Monitor,
  Phone,
  AlertTriangle,
  Activity,
  ArrowLeft,
  ChevronDown,
  Star,
  ThumbsUp,
  MessageSquare
} from 'lucide-react'

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#84cc16']
const NPS_COLORS = { Promoter: '#10b981', Passive: '#f59e0b', Detractor: '#ef4444' }

const VitalMemberExperienceDashboard = ({ user, onBack }) => {
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [timeframe, setTimeframe] = useState(90) // Default 90 days
  const [showTimeframeDropdown, setShowTimeframeDropdown] = useState(false)
  
  // Data states
  const [overview, setOverview] = useState(null)
  const [demographics, setDemographics] = useState(null)
  const [accessTimes, setAccessTimes] = useState(null)
  const [satisfaction, setSatisfaction] = useState(null)
  const [digitalAdoption, setDigitalAdoption] = useState(null)
  const [crisisData, setCrisisData] = useState(null)

  const timeframeOptions = [
    { value: 30, label: 'Last 30 days' },
    { value: 60, label: 'Last 60 days' },
    { value: 90, label: 'Last 90 days' },
    { value: 180, label: 'Last 6 months' },
    { value: 365, label: 'Last 12 months' },
  ]

  const fetchAllData = async () => {
    setLoading(true)
    const token = localStorage.getItem('token')
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }

    // Fetch all data in parallel
    const endpoints = [
      { url: `/api/vital/member-experience/overview?days=${timeframe}`, setter: setOverview },
      { url: `/api/vital/member-experience/utilization-by-demographics?days=${timeframe}`, setter: setDemographics },
      { url: `/api/vital/member-experience/access-times?days=${timeframe}`, setter: setAccessTimes },
      { url: `/api/vital/member-experience/satisfaction-analysis?days=${timeframe}`, setter: setSatisfaction },
      { url: `/api/vital/member-experience/digital-adoption?days=${timeframe}`, setter: setDigitalAdoption },
      { url: `/api/vital/member-experience/crisis-management?days=${timeframe}`, setter: setCrisisData },
    ]

    await Promise.all(endpoints.map(async ({ url, setter }) => {
      try {
        const res = await fetch(apiUrl(url), { headers })
        if (res.ok) {
          const data = await res.json()
          if (data.success) {
            setter(data.data)
          }
        }
      } catch (err) {
        console.error(`Fetch error for ${url}:`, err)
      }
    }))

    setLastUpdated(new Date())
    setLoading(false)
  }

  useEffect(() => {
    fetchAllData()
  }, [timeframe])

  const formatNumber = (value) => {
    if (!value) return '0'
    return value.toLocaleString()
  }

  // Metric Card Component
  const MetricCard = ({ title, value, subtitle, icon: Icon, color = 'blue', trend, trendValue }) => (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">{title}</p>
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
        <span className="ml-3 text-gray-500">Loading member experience data...</span>
      </div>
    )
  }

  const overviewData = overview || {}
  const satisfactionData = satisfaction || {}
  const accessData = accessTimes || {}
  const digitalData = digitalAdoption || {}
  const crisisInfo = crisisData || {}
  const demographicsData = demographics || {}

  // NPS gauge data
  const npsScore = satisfactionData.nps_score || 0
  const npsGaugeData = [
    { name: 'NPS', value: Math.max(0, npsScore + 100), fill: npsScore >= 50 ? '#10b981' : npsScore >= 0 ? '#f59e0b' : '#ef4444' }
  ]

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
            <h1 className="text-2xl font-bold text-gray-900">Member Experience Dashboard</h1>
            <p className="text-gray-500">Service delivery, satisfaction, and utilization metrics</p>
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
                      timeframe === option.value ? 'bg-purple-50 text-purple-600' : 'text-gray-700'
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        <MetricCard
          title="Total Cases"
          value={formatNumber(overviewData.total_cases)}
          subtitle={`${formatNumber(overviewData.open_cases)} open`}
          icon={Users}
          color="blue"
        />
        <MetricCard
          title="Avg Satisfaction"
          value={`${overviewData.avg_satisfaction || 0}/5`}
          subtitle="Member rating"
          icon={Star}
          color="amber"
        />
        <MetricCard
          title="NPS Score"
          value={satisfactionData.nps_score || 0}
          subtitle={`${satisfactionData.promoter_pct || 0}% promoters`}
          icon={ThumbsUp}
          color="green"
        />
        <MetricCard
          title="Avg Time to 1st Session"
          value={`${overviewData.avg_time_to_first_session || 0} days`}
          subtitle="From contact"
          icon={Clock}
          color="purple"
        />
        <MetricCard
          title="High Acuity Cases"
          value={formatNumber(overviewData.high_acuity_cases)}
          subtitle="Crisis/Urgent"
          icon={AlertTriangle}
          color="red"
        />
        <MetricCard
          title="Total Sessions"
          value={formatNumber(overviewData.total_sessions)}
          subtitle="Completed"
          icon={MessageSquare}
          color="cyan"
        />
      </div>

      {/* Satisfaction Analysis and NPS Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Satisfaction Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Star className="h-5 w-5 text-amber-500" />
              Satisfaction Trend
            </CardTitle>
            <CardDescription>Monthly average satisfaction and NPS</CardDescription>
          </CardHeader>
          <CardContent>
            {satisfactionData.monthly_trend?.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={satisfactionData.monthly_trend}>
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
                      domain={[0, 5]}
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis 
                      yAxisId="right"
                      orientation="right"
                      domain={[0, 10]}
                      tick={{ fontSize: 12 }}
                    />
                    <Tooltip />
                    <Legend />
                    <Bar yAxisId="left" dataKey="avg_satisfaction" name="Satisfaction" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                    <Line yAxisId="right" type="monotone" dataKey="avg_nps" name="NPS" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-400">
                No satisfaction data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* NPS Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ThumbsUp className="h-5 w-5 text-green-500" />
              NPS Distribution
            </CardTitle>
            <CardDescription>Promoters, Passives, and Detractors</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-8">
              {/* NPS Score Display */}
              <div className="text-center">
                <div className={`text-5xl font-bold ${npsScore >= 50 ? 'text-green-600' : npsScore >= 0 ? 'text-amber-600' : 'text-red-600'}`}>
                  {npsScore}
                </div>
                <p className="text-sm text-gray-500 mt-2">NPS Score</p>
                <p className="text-xs text-gray-400">
                  {npsScore >= 50 ? 'Excellent' : npsScore >= 0 ? 'Good' : 'Needs Improvement'}
                </p>
              </div>
              {/* Distribution Chart */}
              <div className="flex-1 h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={satisfactionData.nps_distribution || []}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={70}
                      paddingAngle={5}
                      dataKey="count"
                      nameKey="category"
                    >
                      {(satisfactionData.nps_distribution || []).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={NPS_COLORS[entry.category] || COLORS[index]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
            {/* Legend */}
            <div className="flex justify-center gap-6 mt-4 pt-4 border-t">
              {(satisfactionData.nps_distribution || []).map((item) => (
                <div key={item.category} className="flex items-center gap-2">
                  {item.category === 'Promoter' && <Smile className="h-5 w-5 text-green-500" />}
                  {item.category === 'Passive' && <Meh className="h-5 w-5 text-amber-500" />}
                  {item.category === 'Detractor' && <Frown className="h-5 w-5 text-red-500" />}
                  <span className="text-sm">{item.category}: {formatNumber(item.count)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Access Times and Digital Adoption */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Access Times Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-purple-500" />
              Access & Wait Times
            </CardTitle>
            <CardDescription>Time to first session and resolution by month</CardDescription>
          </CardHeader>
          <CardContent>
            {accessData.monthly_trend?.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={accessData.monthly_trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey="month" 
                      tick={{ fontSize: 12 }}
                      tickFormatter={(val) => {
                        const [year, month] = val.split('-')
                        return `${month}/${year.slice(2)}`
                      }}
                    />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="avg_time_to_first_session" name="To 1st Session (days)" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 4 }} />
                    <Line type="monotone" dataKey="avg_time_to_resolution" name="To Resolution (days)" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-400">
                No access time data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Digital vs Telephonic */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Smartphone className="h-5 w-5 text-cyan-500" />
              Digital Adoption
            </CardTitle>
            <CardDescription>Virtual vs In-Person sessions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-cyan-50 rounded-lg p-4 text-center">
                <Monitor className="h-8 w-8 text-cyan-600 mx-auto mb-2" />
                <p className="text-2xl font-bold text-cyan-700">{formatNumber(digitalData.session_types?.virtual || 0)}</p>
                <p className="text-sm text-cyan-600">Virtual Sessions</p>
              </div>
              <div className="bg-amber-50 rounded-lg p-4 text-center">
                <Users className="h-8 w-8 text-amber-600 mx-auto mb-2" />
                <p className="text-2xl font-bold text-amber-700">{formatNumber(digitalData.session_types?.in_person || 0)}</p>
                <p className="text-sm text-amber-600">In-Person Sessions</p>
              </div>
            </div>
            {/* Digital engagement trend */}
            {digitalData.monthly_trend?.length > 0 && (
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={digitalData.monthly_trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey="month" 
                      tick={{ fontSize: 10 }}
                      tickFormatter={(val) => {
                        const [year, month] = val.split('-')
                        return `${month}/${year.slice(2)}`
                      }}
                    />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Area type="monotone" dataKey="web_logins" name="Web Logins" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} />
                    <Area type="monotone" dataKey="mobile_app_usage" name="Mobile App" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.6} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Utilization by Demographics and Crisis Management */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* By Presenting Problem */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-500" />
              Top Presenting Problems
            </CardTitle>
            <CardDescription>Cases by primary issue</CardDescription>
          </CardHeader>
          <CardContent>
            {demographicsData.by_presenting_problem?.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={demographicsData.by_presenting_problem.slice(0, 8)} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis type="number" />
                    <YAxis 
                      type="category" 
                      dataKey="problem" 
                      width={120}
                      tick={{ fontSize: 11 }}
                      tickFormatter={(val) => val.length > 18 ? val.substring(0, 18) + '...' : val}
                    />
                    <Tooltip />
                    <Bar dataKey="case_count" name="Cases" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-400">
                No demographic data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Crisis/High Acuity */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              Crisis & High Acuity Cases
            </CardTitle>
            <CardDescription>Cases by triage tier</CardDescription>
          </CardHeader>
          <CardContent>
            {crisisInfo.by_triage_tier?.length > 0 ? (
              <>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={crisisInfo.by_triage_tier}
                        cx="50%"
                        cy="50%"
                        outerRadius={70}
                        dataKey="case_count"
                        nameKey="triage_tier"
                        label={({ triage_tier, percent }) => `${triage_tier}: ${(percent * 100).toFixed(0)}%`}
                      >
                        {crisisInfo.by_triage_tier.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={
                              entry.triage_tier?.toLowerCase().includes('crisis') || entry.triage_tier?.toLowerCase().includes('high') 
                                ? '#ef4444' 
                                : entry.triage_tier?.toLowerCase().includes('urgent') 
                                  ? '#f59e0b' 
                                  : COLORS[index % COLORS.length]
                            } 
                          />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                {/* Triage tier breakdown */}
                <div className="mt-4 space-y-2">
                  {crisisInfo.by_triage_tier.slice(0, 5).map((tier, i) => (
                    <div key={tier.triage_tier} className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">{tier.triage_tier}</span>
                      <div className="flex items-center gap-4">
                        <span className="font-medium">{formatNumber(tier.case_count)} cases</span>
                        <span className="text-gray-400">{tier.avg_response_time} days avg response</span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-400">
                No crisis data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Utilization by Client Type */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5 text-green-500" />
            Utilization by Client Type
          </CardTitle>
          <CardDescription>Case distribution and satisfaction by client category</CardDescription>
        </CardHeader>
        <CardContent>
          {demographicsData.by_client_type?.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={demographicsData.by_client_type}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="client_type" 
                    tick={{ fontSize: 11 }}
                    tickFormatter={(val) => val.length > 12 ? val.substring(0, 12) + '...' : val}
                  />
                  <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
                  <YAxis yAxisId="right" orientation="right" domain={[0, 5]} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="case_count" name="Cases" fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Line yAxisId="right" type="monotone" dataKey="avg_satisfaction" name="Satisfaction" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              No client type data available
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default VitalMemberExperienceDashboard
