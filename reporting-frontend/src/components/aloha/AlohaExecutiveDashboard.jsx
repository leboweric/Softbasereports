import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { apiUrl } from '@/lib/api'
import {
  Building2,
  DollarSign,
  Package,
  ShoppingCart,
  TrendingUp,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Settings,
  ArrowRight,
  BarChart3,
  Wallet,
  Globe
} from 'lucide-react'

const AlohaExecutiveDashboard = ({ user, onNavigate }) => {
  const [loading, setLoading] = useState(true)
  const [dashboardData, setDashboardData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchDashboard()
  }, [])

  const fetchDashboard = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/aloha/dashboard/summary'), {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setDashboardData(data)
      } else {
        setError('Failed to load dashboard data')
      }
    } catch (err) {
      console.error('Dashboard fetch error:', err)
      setError('Network error loading dashboard')
    }
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-3 text-gray-600">Loading dashboard...</span>
      </div>
    )
  }

  // Setup required state
  if (dashboardData?.status === 'setup_required') {
    return <SetupRequiredView data={dashboardData} onNavigate={onNavigate} />
  }

  // Active dashboard with data
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Globe className="h-7 w-7 text-teal-600" />
            Aloha Holdings — Executive Dashboard
          </h1>
          <p className="text-gray-500 mt-1">
            Consolidated view across {dashboardData?.total_subsidiaries || 3} subsidiary companies
          </p>
        </div>
        <Button variant="outline" onClick={fetchDashboard}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Subsidiary Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {dashboardData?.subsidiaries?.map((sub) => (
          <Card key={sub.id} className={`border-l-4 ${sub.connected ? 'border-l-green-500' : 'border-l-yellow-500'}`}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{sub.name}</CardTitle>
                <Badge variant={sub.connected ? 'default' : 'secondary'} className={sub.connected ? 'bg-green-100 text-green-800' : ''}>
                  {sub.connected ? 'Connected' : 'Pending'}
                </Badge>
              </div>
              <CardDescription className="text-xs">
                {sub.system_type !== 'Not configured' ? `SAP ${sub.system_type.toUpperCase()}` : 'SAP — Not configured'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {sub.connected ? (
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-gray-500">Revenue</p>
                    <p className="font-semibold">—</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Orders</p>
                    <p className="font-semibold">—</p>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-400">Awaiting SAP connection configuration</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Consolidated KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard
          title="Total Revenue"
          value={dashboardData?.consolidated?.total_revenue}
          icon={DollarSign}
          color="text-green-600"
          format="currency"
        />
        <KPICard
          title="Total Orders"
          value={dashboardData?.consolidated?.total_orders}
          icon={ShoppingCart}
          color="text-blue-600"
          format="number"
        />
        <KPICard
          title="Inventory Value"
          value={dashboardData?.consolidated?.total_inventory_value}
          icon={Package}
          color="text-purple-600"
          format="currency"
        />
        <KPICard
          title="Net Income"
          value={dashboardData?.consolidated?.net_income}
          icon={TrendingUp}
          color="text-teal-600"
          format="currency"
        />
      </div>

      {/* Placeholder for charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-500" />
              Revenue by Subsidiary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center h-48 text-gray-400">
              <div className="text-center">
                <BarChart3 className="h-12 w-12 mx-auto mb-2 opacity-30" />
                <p>Revenue comparison chart will appear once SAP data is synced</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Wallet className="h-5 w-5 text-green-500" />
              Consolidated P&L Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center h-48 text-gray-400">
              <div className="text-center">
                <Wallet className="h-12 w-12 mx-auto mb-2 opacity-30" />
                <p>Financial summary will appear once SAP data is synced</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Last sync info */}
      {dashboardData?.last_sync && (
        <p className="text-xs text-gray-400 text-right">
          Last synced: {new Date(dashboardData.last_sync).toLocaleString()}
        </p>
      )}
    </div>
  )
}

const KPICard = ({ title, value, icon: Icon, color, format }) => {
  const formatValue = (val) => {
    if (val === null || val === undefined) return '—'
    if (format === 'currency') return `$${val.toLocaleString()}`
    if (format === 'number') return val.toLocaleString()
    return val
  }

  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">{title}</p>
            <p className="text-2xl font-bold mt-1">{formatValue(value)}</p>
          </div>
          <Icon className={`h-8 w-8 ${color} opacity-60`} />
        </div>
      </CardContent>
    </Card>
  )
}

const SetupRequiredView = ({ data, onNavigate }) => {
  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="text-center py-8">
        <Globe className="h-16 w-16 text-teal-600 mx-auto mb-4" />
        <h1 className="text-3xl font-bold text-gray-900">Welcome to Aloha Holdings</h1>
        <p className="text-gray-500 mt-2 max-w-lg mx-auto">
          Your executive dashboard will display consolidated data from all 3 subsidiary SAP systems.
          Let's get started by configuring your data connections.
        </p>
      </div>

      {/* Subsidiary Connection Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
        {data.subsidiaries?.map((sub, idx) => (
          <Card key={sub.id} className="border-2 border-dashed border-gray-200 hover:border-teal-300 transition-colors">
            <CardHeader className="text-center pb-2">
              <div className="mx-auto w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-2">
                <Building2 className="h-6 w-6 text-gray-400" />
              </div>
              <CardTitle className="text-base">{sub.name}</CardTitle>
              <CardDescription>SAP ERP System</CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <Badge variant="secondary" className="mb-3">
                <XCircle className="h-3 w-3 mr-1" />
                Not Connected
              </Badge>
              <p className="text-xs text-gray-400">
                Configure connection in Data Sources
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Setup Steps */}
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Getting Started
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {data.setup_steps?.map((step, idx) => (
              <div key={idx} className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center text-sm font-medium">
                  {idx + 1}
                </div>
                <p className="text-sm text-gray-700 pt-0.5">{step}</p>
              </div>
            ))}
          </div>
          <div className="mt-6">
            <Button 
              className="w-full bg-teal-600 hover:bg-teal-700"
              onClick={() => onNavigate && onNavigate('aloha-data-sources')}
            >
              Configure Data Sources
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default AlohaExecutiveDashboard
