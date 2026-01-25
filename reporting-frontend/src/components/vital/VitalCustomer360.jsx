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
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
  Area,
  AreaChart,
  ComposedChart
} from 'recharts'
import {
  Building2,
  Users,
  Activity,
  TrendingUp,
  Clock,
  Star,
  Heart,
  Smartphone,
  Globe,
  CheckCircle,
  AlertTriangle,
  ChevronDown,
  Search,
  RefreshCw,
  ArrowLeft
} from 'lucide-react'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#a4de6c', '#d0ed57']

const VitalCustomer360 = ({ user, onBack }) => {
  const [loading, setLoading] = useState(true)
  const [organizations, setOrganizations] = useState([])
  const [selectedOrg, setSelectedOrg] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)
  const [timeframe, setTimeframe] = useState(365)
  const [showTimeframeDropdown, setShowTimeframeDropdown] = useState(false)
  
  // Data states
  const [overview, setOverview] = useState(null)
  const [services, setServices] = useState(null)
  const [trends, setTrends] = useState(null)
  const [outcomes, setOutcomes] = useState(null)
  const [dataLoading, setDataLoading] = useState(false)

  const timeframeOptions = [
    { value: 90, label: 'Last 90 days' },
    { value: 180, label: 'Last 6 months' },
    { value: 365, label: 'Last 12 months' },
    { value: 730, label: 'Last 2 years' },
    { value: 1825, label: 'Last 5 years' },
  ]

  // Fetch organizations on mount
  useEffect(() => {
    fetchOrganizations()
  }, [])

  // Fetch customer data when org or timeframe changes
  useEffect(() => {
    if (selectedOrg) {
      fetchCustomerData()
    }
  }, [selectedOrg, timeframe])

  const fetchOrganizations = async () => {
    setLoading(true)
    const token = localStorage.getItem('token')
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }

    try {
      const res = await fetch(apiUrl('/api/vital/azure-sql/organizations'), { headers })
      if (res.ok) {
        const result = await res.json()
        if (result.success) {
          setOrganizations(result.data || [])
        }
      }
    } catch (err) {
      console.error('Organizations fetch error:', err)
    }
    setLoading(false)
  }

  const fetchCustomerData = async () => {
    if (!selectedOrg) return
    
    setDataLoading(true)
    const token = localStorage.getItem('token')
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }

    const orgParam = encodeURIComponent(selectedOrg)

    // Fetch all customer data in parallel
    try {
      const [overviewRes, servicesRes, trendsRes, outcomesRes] = await Promise.all([
        fetch(apiUrl(`/api/vital/azure-sql/customer/overview?organization=${orgParam}&days=${timeframe}`), { headers }),
        fetch(apiUrl(`/api/vital/azure-sql/customer/services?organization=${orgParam}&days=${timeframe}`), { headers }),
        fetch(apiUrl(`/api/vital/azure-sql/customer/trends?organization=${orgParam}&days=${timeframe}`), { headers }),
        fetch(apiUrl(`/api/vital/azure-sql/customer/outcomes?organization=${orgParam}&days=${timeframe}`), { headers })
      ])

      if (overviewRes.ok) {
        const data = await overviewRes.json()
        if (data.success) setOverview(data.data)
      }
      if (servicesRes.ok) {
        const data = await servicesRes.json()
        if (data.success) setServices(data.data)
      }
      if (trendsRes.ok) {
        const data = await trendsRes.json()
        if (data.success) setTrends(data.data)
      }
      if (outcomesRes.ok) {
        const data = await outcomesRes.json()
        if (data.success) setOutcomes(data.data)
      }
    } catch (err) {
      console.error('Customer data fetch error:', err)
    }
    setDataLoading(false)
  }

  const formatNumber = (num) => {
    if (!num) return '0'
    return num.toLocaleString()
  }

  const formatPercent = (num) => {
    if (!num) return '0%'
    return `${num}%`
  }

  const filteredOrgs = organizations.filter(org => 
    org.organization.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // Metric Card Component
  const MetricCard = ({ label, value, sublabel, icon: Icon, valueColor, trend }) => (
    <div className="bg-white rounded-lg p-4 border border-gray-100 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-500">{label}</span>
        {Icon && <Icon className="h-4 w-4 text-gray-400" />}
      </div>
      <div className={`text-2xl font-bold ${valueColor || 'text-gray-900'}`}>{value}</div>
      {sublabel && <div className="text-xs text-gray-400 mt-1">{sublabel}</div>}
      {trend !== undefined && (
        <div className={`text-xs mt-1 ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% vs prev period
        </div>
      )}
    </div>
  )

  // Section Header Component
  const SectionHeader = ({ title, icon: Icon, color }) => (
    <div className="flex items-center gap-3 mb-4">
      <div className={`p-2 rounded-lg ${color}`}>
        <Icon className="h-5 w-5 text-white" />
      </div>
      <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
    </div>
  )

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full min-h-[400px]">
        <LoadingSpinner size={50} />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-4">
          {onBack && (
            <button 
              onClick={onBack}
              className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600" />
            </button>
          )}
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-gray-900">Customer 360</h1>
            <p className="text-gray-600">
              Deep dive into customer utilization, engagement, and outcomes
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Timeframe Selector */}
          <div className="relative">
            <button
              onClick={() => setShowTimeframeDropdown(!showTimeframeDropdown)}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Clock className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium">
                {timeframeOptions.find(t => t.value === timeframe)?.label}
              </span>
              <ChevronDown className="h-4 w-4 text-gray-400" />
            </button>
            {showTimeframeDropdown && (
              <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                {timeframeOptions.map(option => (
                  <button
                    key={option.value}
                    onClick={() => {
                      setTimeframe(option.value)
                      setShowTimeframeDropdown(false)
                    }}
                    className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-50 ${
                      timeframe === option.value ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <Button 
            onClick={fetchCustomerData} 
            variant="outline" 
            size="sm"
            disabled={!selectedOrg}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Customer Selector */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search and select a customer..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value)
                setShowDropdown(true)
              }}
              onFocus={() => setShowDropdown(true)}
              className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            {showDropdown && searchTerm && (
              <div className="absolute w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto">
                {filteredOrgs.length > 0 ? (
                  filteredOrgs.slice(0, 20).map((org, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setSelectedOrg(org.organization)
                        setSearchTerm(org.organization)
                        setShowDropdown(false)
                      }}
                      className="w-full px-4 py-3 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                    >
                      <div className="font-medium text-gray-900">{org.organization}</div>
                      <div className="text-sm text-gray-500">
                        {formatNumber(org.case_count)} cases • Last activity: {org.last_case_date ? new Date(org.last_case_date).toLocaleDateString() : 'N/A'}
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="px-4 py-3 text-gray-500">No customers found</div>
                )}
              </div>
            )}
          </div>
          {selectedOrg && (
            <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-lg">
              <Building2 className="h-4 w-4 text-blue-600" />
              <span className="font-medium text-blue-900">{selectedOrg}</span>
              <button 
                onClick={() => {
                  setSelectedOrg(null)
                  setSearchTerm('')
                  setOverview(null)
                  setServices(null)
                  setTrends(null)
                  setOutcomes(null)
                }}
                className="ml-2 text-blue-600 hover:text-blue-800"
              >
                ×
              </button>
            </div>
          )}
        </div>
      </div>

      {/* No Customer Selected State */}
      {!selectedOrg && (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <Building2 className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">Select a Customer</h3>
          <p className="text-gray-500">Search and select a customer above to view their detailed analytics</p>
        </div>
      )}

      {/* Loading State */}
      {selectedOrg && dataLoading && (
        <div className="flex justify-center items-center py-12">
          <LoadingSpinner size={40} />
          <span className="ml-3 text-gray-600">Loading customer data...</span>
        </div>
      )}

      {/* Customer Dashboard */}
      {selectedOrg && !dataLoading && overview && (
        <>
          {/* Overview Section */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <SectionHeader title="Customer Overview" icon={Building2} color="bg-blue-500" />
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              <MetricCard 
                label="Total Cases" 
                value={formatNumber(overview.cases_in_period)} 
                sublabel={`${timeframeOptions.find(t => t.value === timeframe)?.label}`}
                icon={Activity}
              />
              <MetricCard 
                label="Open Cases" 
                value={formatNumber(overview.open_cases)} 
                sublabel="Current backlog"
                icon={AlertTriangle}
                valueColor={overview.open_cases > 0 ? 'text-amber-600' : 'text-green-600'}
              />
              <MetricCard 
                label="Closed Cases" 
                value={formatNumber(overview.closed_cases)} 
                sublabel="Resolved"
                icon={CheckCircle}
                valueColor="text-green-600"
              />
              <MetricCard 
                label="Avg Satisfaction" 
                value={overview.avg_satisfaction?.toFixed(1) || 'N/A'} 
                sublabel="Out of 5.0"
                icon={Star}
                valueColor={overview.avg_satisfaction >= 4 ? 'text-green-600' : overview.avg_satisfaction >= 3 ? 'text-amber-600' : 'text-red-600'}
              />
              <MetricCard 
                label="NPS Score" 
                value={overview.avg_nps?.toFixed(0) || 'N/A'} 
                sublabel="Net Promoter"
                icon={TrendingUp}
                valueColor={overview.avg_nps >= 50 ? 'text-green-600' : overview.avg_nps >= 0 ? 'text-amber-600' : 'text-red-600'}
              />
              <MetricCard 
                label="Population" 
                value={formatNumber(overview.population)} 
                sublabel={overview.industry || 'Unknown'}
                icon={Users}
              />
            </div>
            
            {/* Additional Metrics Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mt-4">
              <MetricCard 
                label="Total Sessions" 
                value={formatNumber(overview.total_sessions)} 
                sublabel={`Avg ${overview.avg_sessions_per_case?.toFixed(1) || 0} per case`}
                icon={Activity}
              />
              <MetricCard 
                label="Avg Time to Close" 
                value={`${overview.avg_tat_to_close?.toFixed(1) || 0}d`} 
                sublabel="Days"
                icon={Clock}
              />
              <MetricCard 
                label="Avg Time to 1st Session" 
                value={`${overview.avg_tat_to_first_session?.toFixed(1) || 0}d`} 
                sublabel="Days"
                icon={Clock}
              />
              <MetricCard 
                label="Web Logins" 
                value={formatNumber(overview.total_web_logins)} 
                sublabel="Digital engagement"
                icon={Globe}
              />
              <MetricCard 
                label="Mobile App Usage" 
                value={formatNumber(overview.total_mobile_app_usage)} 
                sublabel="App interactions"
                icon={Smartphone}
              />
              <MetricCard 
                label="Well-Being Impact" 
                value={overview.avg_wellbeing_impact?.toFixed(1) || 'N/A'} 
                sublabel="Avg improvement"
                icon={Heart}
                valueColor="text-teal-600"
              />
            </div>
          </div>

          {/* Service Utilization Section */}
          {services && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Cases by Type */}
              <div className="bg-white rounded-xl shadow-sm p-6">
                <SectionHeader title="Cases by Type" icon={Activity} color="bg-indigo-500" />
                {services.by_case_type?.length > 0 ? (
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={services.by_case_type.slice(0, 8)}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={2}
                          dataKey="count"
                          nameKey="name"
                          label={({ name, percentage }) => `${name}: ${percentage}%`}
                          labelLine={false}
                        >
                          {services.by_case_type.slice(0, 8).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => formatNumber(value)} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-80 flex items-center justify-center text-gray-500">No data available</div>
                )}
              </div>

              {/* Top Presenting Problems */}
              <div className="bg-white rounded-xl shadow-sm p-6">
                <SectionHeader title="Top Presenting Problems" icon={AlertTriangle} color="bg-amber-500" />
                {services.top_presenting_problems?.length > 0 ? (
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart 
                        data={services.top_presenting_problems.slice(0, 8)} 
                        layout="vertical"
                        margin={{ left: 20, right: 20 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" />
                        <YAxis 
                          type="category" 
                          dataKey="name" 
                          width={150}
                          tick={{ fontSize: 11 }}
                        />
                        <Tooltip formatter={(value) => formatNumber(value)} />
                        <Bar dataKey="count" fill="#f59e0b" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-80 flex items-center justify-center text-gray-500">No data available</div>
                )}
              </div>
            </div>
          )}

          {/* Trends Section */}
          {trends && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Monthly Case Volume */}
              <div className="bg-white rounded-xl shadow-sm p-6">
                <SectionHeader title="Monthly Case Volume" icon={TrendingUp} color="bg-green-500" />
                {trends.monthly_case_trend?.length > 0 ? (
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={trends.monthly_case_trend}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month_label" tick={{ fontSize: 11 }} />
                        <YAxis yAxisId="left" />
                        <YAxis yAxisId="right" orientation="right" domain={[0, 5]} />
                        <Tooltip />
                        <Legend />
                        <Bar yAxisId="left" dataKey="case_count" name="Cases" fill="#22c55e" radius={[4, 4, 0, 0]} />
                        <Line yAxisId="right" type="monotone" dataKey="avg_satisfaction" name="Avg Satisfaction" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-72 flex items-center justify-center text-gray-500">No data available</div>
                )}
              </div>

              {/* Digital Engagement Trend */}
              <div className="bg-white rounded-xl shadow-sm p-6">
                <SectionHeader title="Digital Engagement" icon={Globe} color="bg-purple-500" />
                {trends.engagement_trend?.length > 0 ? (
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={trends.engagement_trend}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month_label" tick={{ fontSize: 11 }} />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Area type="monotone" dataKey="web_logins" name="Web Logins" stackId="1" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
                        <Area type="monotone" dataKey="mobile_app" name="Mobile App" stackId="1" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.6} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-72 flex items-center justify-center text-gray-500">No data available</div>
                )}
              </div>
            </div>
          )}

          {/* Outcomes Section */}
          {outcomes && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Session Modality */}
              <div className="bg-white rounded-xl shadow-sm p-6">
                <SectionHeader title="Session Modality" icon={Users} color="bg-teal-500" />
                {outcomes.modality_breakdown?.length > 0 && (outcomes.modality_breakdown[0].count > 0 || outcomes.modality_breakdown[1].count > 0) ? (
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={outcomes.modality_breakdown}
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={80}
                          paddingAngle={5}
                          dataKey="count"
                          nameKey="name"
                          label={({ name, percentage }) => `${name}: ${percentage}%`}
                        >
                          <Cell fill="#14b8a6" />
                          <Cell fill="#8b5cf6" />
                        </Pie>
                        <Tooltip formatter={(value) => formatNumber(value)} />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-64 flex items-center justify-center text-gray-500">No session data available</div>
                )}
              </div>

              {/* Case Outcomes */}
              <div className="bg-white rounded-xl shadow-sm p-6">
                <SectionHeader title="Case Outcomes" icon={CheckCircle} color="bg-emerald-500" />
                {outcomes.by_disposition?.length > 0 ? (
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={outcomes.by_disposition.slice(0, 6)} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" />
                        <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
                        <Tooltip formatter={(value) => formatNumber(value)} />
                        <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-64 flex items-center justify-center text-gray-500">No outcome data available</div>
                )}
              </div>
            </div>
          )}

          {/* Pre/Post Outcomes */}
          {outcomes?.pre_post_scores && (
            <div className="bg-white rounded-xl shadow-sm p-6">
              <SectionHeader title="Pre/Post Outcomes Comparison" icon={Heart} color="bg-rose-500" />
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Well-Being */}
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-700 mb-3">Well-Being Score</h4>
                  <div className="flex justify-center items-center gap-4">
                    <div>
                      <div className="text-2xl font-bold text-gray-500">{outcomes.pre_post_scores.wellbeing.pre || 'N/A'}</div>
                      <div className="text-xs text-gray-400">Pre</div>
                    </div>
                    <div className="text-2xl text-gray-300">→</div>
                    <div>
                      <div className="text-2xl font-bold text-green-600">{outcomes.pre_post_scores.wellbeing.post || 'N/A'}</div>
                      <div className="text-xs text-gray-400">Post</div>
                    </div>
                  </div>
                </div>
                
                {/* Burnout */}
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-700 mb-3">Burnout Score</h4>
                  <div className="flex justify-center items-center gap-4">
                    <div>
                      <div className="text-2xl font-bold text-red-500">{outcomes.pre_post_scores.burnout.pre || 'N/A'}</div>
                      <div className="text-xs text-gray-400">Pre</div>
                    </div>
                    <div className="text-2xl text-gray-300">→</div>
                    <div>
                      <div className="text-2xl font-bold text-green-600">{outcomes.pre_post_scores.burnout.post || 'N/A'}</div>
                      <div className="text-xs text-gray-400">Post</div>
                    </div>
                  </div>
                </div>
                
                {/* Retention */}
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-700 mb-3">Retention Score</h4>
                  <div className="flex justify-center items-center gap-4">
                    <div>
                      <div className="text-2xl font-bold text-gray-500">{outcomes.pre_post_scores.retention.pre || 'N/A'}</div>
                      <div className="text-xs text-gray-400">Pre</div>
                    </div>
                    <div className="text-2xl text-gray-300">→</div>
                    <div>
                      <div className="text-2xl font-bold text-green-600">{outcomes.pre_post_scores.retention.post || 'N/A'}</div>
                      <div className="text-xs text-gray-400">Post</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default VitalCustomer360
