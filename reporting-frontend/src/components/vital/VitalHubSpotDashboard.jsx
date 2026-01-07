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
  FunnelChart,
  Funnel,
  LabelList
} from 'recharts'
import {
  Users,
  Building2,
  DollarSign,
  TrendingUp,
  Target,
  Award,
  RefreshCw,
  AlertCircle
} from 'lucide-react'
import { Button } from '@/components/ui/button'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#ff7300']

const VitalHubSpotDashboard = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [dashboardData, setDashboardData] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetchDashboardData = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/vital/hubspot/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch HubSpot data')
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

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  const formatNumber = (value) => {
    return new Intl.NumberFormat('en-US').format(value)
  }

  const StatCard = ({ title, value, icon: Icon, color, subtitle, trend }) => (
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
        {trend && (
          <p className={`text-xs mt-2 ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% from last period
          </p>
        )}
      </CardContent>
    </Card>
  )

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-96">
        <LoadingSpinner size={50} />
        <p className="mt-4 text-gray-500">Loading HubSpot data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col justify-center items-center h-96">
        <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
        <p className="text-red-600 font-medium">Error loading HubSpot data</p>
        <p className="text-gray-500 text-sm mt-2">{error}</p>
        <Button onClick={fetchDashboardData} className="mt-4" variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    )
  }

  // Prepare pipeline data for funnel chart
  const pipelineData = dashboardData?.deals?.deals_by_stage
    ?.filter(s => !s.is_closed)
    ?.sort((a, b) => b.total_value - a.total_value)
    ?.slice(0, 6)
    ?.map((stage, index) => ({
      name: stage.stage_name,
      value: stage.total_value,
      count: stage.count,
      fill: COLORS[index % COLORS.length]
    })) || []

  // Prepare closed deals data for pie chart
  const closedDealsData = [
    { 
      name: 'Won', 
      value: dashboardData?.deals?.won_count || 0,
      fill: '#00C49F'
    },
    { 
      name: 'Lost', 
      value: dashboardData?.deals?.lost_count || 0,
      fill: '#FF8042'
    }
  ]

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">HubSpot CRM Dashboard</h1>
          <p className="text-gray-500">Real-time data from VITAL WorkLife HubSpot</p>
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

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Contacts"
          value={formatNumber(dashboardData?.contacts?.total || 0)}
          icon={Users}
          color="blue"
          subtitle={`${formatNumber(dashboardData?.contacts?.new_last_30_days || 0)} new in last 30 days`}
        />
        <StatCard
          title="Total Companies"
          value={formatNumber(dashboardData?.companies?.total || 0)}
          icon={Building2}
          color="purple"
        />
        <StatCard
          title="Pipeline Value"
          value={formatCurrency(dashboardData?.deals?.pipeline_value || 0)}
          icon={Target}
          color="green"
          subtitle={`${formatNumber(dashboardData?.deals?.total_deals || 0)} total deals`}
        />
        <StatCard
          title="Win Rate"
          value={`${dashboardData?.deals?.win_rate || 0}%`}
          icon={Award}
          color="yellow"
          subtitle={`Avg deal: ${formatCurrency(dashboardData?.deals?.avg_deal_size || 0)}`}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pipeline Funnel */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Sales Pipeline</CardTitle>
            <CardDescription>Open deals by stage (top 6 by value)</CardDescription>
          </CardHeader>
          <CardContent>
            {pipelineData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={pipelineData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
                  <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 12 }} />
                  <Tooltip 
                    formatter={(value) => [formatCurrency(value), 'Value']}
                    labelFormatter={(label) => `Stage: ${label}`}
                  />
                  <Bar dataKey="value" fill="#0088FE" radius={[0, 4, 4, 0]}>
                    {pipelineData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex justify-center items-center h-64 text-gray-500">
                No pipeline data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Win/Loss Ratio */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Deal Outcomes</CardTitle>
            <CardDescription>Won vs Lost deals</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={closedDealsData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {closedDealsData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-4 text-center">
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-2xl font-bold text-green-600">{formatCurrency(dashboardData?.deals?.won_value || 0)}</p>
                <p className="text-sm text-green-700">Total Won Value</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-gray-600">{formatCurrency(dashboardData?.deals?.total_value || 0)}</p>
                <p className="text-sm text-gray-700">Total Deal Value</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Deals by Stage Table */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle>All Pipeline Stages</CardTitle>
          <CardDescription>Complete breakdown of deals by stage</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left p-3 font-medium">Stage</th>
                  <th className="text-left p-3 font-medium">Pipeline</th>
                  <th className="text-right p-3 font-medium">Deals</th>
                  <th className="text-right p-3 font-medium">Total Value</th>
                  <th className="text-center p-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {dashboardData?.deals?.deals_by_stage?.map((stage, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="p-3 font-medium">{stage.stage_name}</td>
                    <td className="p-3 text-gray-600">{stage.pipeline}</td>
                    <td className="p-3 text-right">{formatNumber(stage.count)}</td>
                    <td className="p-3 text-right font-medium">{formatCurrency(stage.total_value)}</td>
                    <td className="p-3 text-center">
                      <Badge variant={stage.is_closed ? "secondary" : "default"}>
                        {stage.is_closed ? 'Closed' : 'Open'}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default VitalHubSpotDashboard
