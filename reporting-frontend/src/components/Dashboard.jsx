import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
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
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import { 
  DollarSign, 
  TrendingUp, 
  Package, 
  Users,
  FileText,
  Download,
  RefreshCw
} from 'lucide-react'
import { apiUrl } from '@/lib/api'

const Dashboard = ({ user }) => {
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadTime, setLoadTime] = useState(null)
  const [fromCache, setFromCache] = useState(false)
  const [inventoryModalOpen, setInventoryModalOpen] = useState(false)
  const [inventoryDetails, setInventoryDetails] = useState(null)
  const [loadingInventory, setLoadingInventory] = useState(false)
  const [visibleWOTypes, setVisibleWOTypes] = useState({
    service: true,
    rental: true,
    parts: true,
    pm: true,
    shop: true,
    equipment: true
  })
  const [includeCurrentMonth, setIncludeCurrentMonth] = useState(false)
  const [includeCurrentMonthMargins, setIncludeCurrentMonthMargins] = useState(false)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async (forceRefresh = false) => {
    const startTime = Date.now()
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      // Try optimized endpoint first, fall back to regular if it fails
      const url = forceRefresh 
        ? apiUrl('/api/reports/dashboard/summary-optimized?refresh=true')
        : apiUrl('/api/reports/dashboard/summary-optimized')
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }).catch(() => {
        // If optimized endpoint fails, fall back to regular endpoint
        return fetch(apiUrl('/api/reports/dashboard/summary'), {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        })
      })

      if (response.ok) {
        const data = await response.json()
        setDashboardData(data)
        // Calculate load time
        const totalTime = (Date.now() - startTime) / 1000
        setLoadTime(data.query_time || totalTime)
        setFromCache(data.from_cache || false)
        // Log query time if available
        if (data.query_time) {
          const cacheStatus = data.from_cache ? 'from cache' : 'fresh data'
          console.log(`Dashboard loaded in ${data.query_time} seconds (${cacheStatus})`)
        }
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchInventoryDetails = async () => {
    setLoadingInventory(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/inventory-details'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setInventoryDetails(data)
      }
    } catch (error) {
      console.error('Failed to fetch inventory details:', error)
    } finally {
      setLoadingInventory(false)
    }
  }

  const handleInventoryClick = () => {
    setInventoryModalOpen(true)
    if (!inventoryDetails) {
      fetchInventoryDetails()
    }
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const getFilteredWOData = () => {
    if (!dashboardData?.monthly_work_orders_by_type) return []
    
    if (includeCurrentMonth) {
      return dashboardData.monthly_work_orders_by_type
    } else {
      // Exclude the last month (current month)
      return dashboardData.monthly_work_orders_by_type.slice(0, -1)
    }
  }

  const getFilteredMarginsData = () => {
    if (!dashboardData?.department_margins) return []
    
    if (includeCurrentMonthMargins) {
      return dashboardData.department_margins
    } else {
      // Exclude the last month (current month)
      return dashboardData.department_margins.slice(0, -1)
    }
  }

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

  // Custom tooltip for Monthly Sales (No Equipment)
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length && dashboardData?.monthly_sales_by_stream) {
      const monthData = dashboardData.monthly_sales_by_stream.find(item => item.month === label)
      const total = payload[0].value
      
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="font-semibold mb-2">{label}</p>
          <p className="font-semibold text-green-600 mb-2">Total: {formatCurrency(total)}</p>
          {monthData && (
            <div className="text-sm space-y-1 border-t pt-2">
              <div className="flex justify-between">
                <span>Parts:</span>
                <span className="ml-4">{formatCurrency(monthData.parts)}</span>
              </div>
              <div className="flex justify-between">
                <span>Labor:</span>
                <span className="ml-4">{formatCurrency(monthData.labor)}</span>
              </div>
              <div className="flex justify-between">
                <span>Rental:</span>
                <span className="ml-4">{formatCurrency(monthData.rental)}</span>
              </div>
              <div className="flex justify-between">
                <span>Misc:</span>
                <span className="ml-4">{formatCurrency(monthData.misc)}</span>
              </div>
            </div>
          )}
        </div>
      )
    }
    return null
  }

  if (loading) {
    return (
      <>
        <LoadingSpinner 
          title="Loading Dashboard" 
          description="Fetching your business data..."
          size="xlarge"
          showProgress={true}
        />
        {/* Skeleton preview */}
        <div className="px-8 pb-8">
          <div className="max-w-6xl mx-auto space-y-6 opacity-30">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {[...Array(4)].map((_, i) => (
                <Card key={i}>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <div className="h-4 bg-gray-200 rounded w-20 animate-pulse" />
                    <div className="h-4 w-4 bg-gray-200 rounded animate-pulse" />
                  </CardHeader>
                  <CardContent>
                    <div className="h-8 bg-gray-200 rounded w-24 animate-pulse mb-2" />
                    <div className="h-3 bg-gray-200 rounded w-32 animate-pulse" />
                  </CardContent>
                </Card>
              ))}
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <Card className="h-96">
                <CardHeader>
                  <div className="h-6 bg-gray-200 rounded w-32 animate-pulse" />
                  <div className="h-4 bg-gray-200 rounded w-48 animate-pulse mt-2" />
                </CardHeader>
              </Card>
              <Card className="h-96">
                <CardHeader>
                  <div className="h-6 bg-gray-200 rounded w-32 animate-pulse" />
                  <div className="h-4 bg-gray-200 rounded w-48 animate-pulse mt-2" />
                </CardHeader>
              </Card>
            </div>
          </div>
        </div>
      </>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back, {user?.first_name}! Here's what's happening with your business.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {loadTime && (
            <Badge 
              variant={fromCache ? "default" : "secondary"} 
              className="text-xs"
            >
              <TrendingUp className="mr-1 h-3 w-3" />
              {loadTime.toFixed(1)}s {fromCache && "(cached)"}
            </Badge>
          )}
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => fetchDashboardData(true)}
            disabled={loading}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Month Sales</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(dashboardData?.total_sales || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              {dashboardData?.period || 'Current Period'}
            </p>
          </CardContent>
        </Card>

        <Card 
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={handleInventoryClick}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rental Units Available</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardData?.inventory_count || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Units available • Click for details
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Customers</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardData?.active_customers || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Last 30 days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Uninvoiced Work Orders</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(dashboardData?.uninvoiced_work_orders || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              {dashboardData?.uninvoiced_count || 0} orders pending
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts - First Row */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Monthly Sales</CardTitle>
            <CardDescription>
              Total sales over the last 12 months
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={dashboardData?.monthly_sales || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value) => formatCurrency(value)} />
                <Bar dataKey="amount" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Monthly Sales (No Equipment)</CardTitle>
            <CardDescription>
              Sales excluding new equipment
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={dashboardData?.monthly_sales_no_equipment || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="amount" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Charts - Second Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Open Work Orders by Type</CardTitle>
            <CardDescription>
              {formatCurrency(dashboardData?.open_work_orders_value || 0)} in open/incomplete orders ({dashboardData?.open_work_orders_count || 0} total)
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <ResponsiveContainer width="100%" height={350}>
              <PieChart>
                <Pie
                  data={dashboardData?.work_order_types || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ type, percent }) => `${type} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="value"
                  nameKey="type"
                >
                  {(dashboardData?.work_order_types || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value, name) => [formatCurrency(value), name]}
                  contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Monthly Quotes</CardTitle>
            <CardDescription>
              Total value quoted per month (latest quote per customer per day)
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={dashboardData?.monthly_quotes || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value) => formatCurrency(value)} />
                <Bar dataKey="amount" fill="#f59e0b" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Charts - Third Row */}
      <div className="grid gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Department Gross Margins %</CardTitle>
            <CardDescription>
              Margin percentages by department over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2 mb-4">
              <Checkbox 
                id="current-month-margins-filter"
                checked={includeCurrentMonthMargins}
                onCheckedChange={setIncludeCurrentMonthMargins}
              />
              <label 
                htmlFor="current-month-margins-filter" 
                className="text-sm font-medium cursor-pointer"
              >
                Include Current Month
              </label>
            </div>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={getFilteredMarginsData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis 
                  domain={[0, 100]}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip 
                  formatter={(value) => `${value}%`}
                  labelFormatter={(label) => `Month: ${label}`}
                />
                <Line 
                  type="monotone" 
                  dataKey="parts_margin" 
                  stroke="#ef4444" 
                  name="Parts"
                  strokeWidth={2}
                />
                <Line 
                  type="monotone" 
                  dataKey="labor_margin" 
                  stroke="#3b82f6" 
                  name="Labor"
                  strokeWidth={2}
                />
                <Line 
                  type="monotone" 
                  dataKey="equipment_margin" 
                  stroke="#10b981" 
                  name="Equipment"
                  strokeWidth={2}
                />
                <Line 
                  type="monotone" 
                  dataKey="rental_margin" 
                  stroke="#a855f7" 
                  name="Rental"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Top 10 Customers */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Top 10 Customers</CardTitle>
            <CardDescription>
              By fiscal year-to-date sales
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboardData?.top_customers?.map((customer) => (
                <div key={customer.rank} className="flex items-center">
                  <div className="w-8 text-sm font-medium text-muted-foreground">
                    {customer.rank}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {customer.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {customer.invoice_count} invoices
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {formatCurrency(customer.sales)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {customer.percentage}%
                    </div>
                  </div>
                </div>
              )) || (
                <p className="text-sm text-gray-500">No customer data available</p>
              )}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Work Orders Trends by Type</CardTitle>
            <CardDescription>
              Dollar value of work orders opened by type since March
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4 mb-4">
              <div className="flex items-center space-x-2 pr-4 border-r">
                <Checkbox 
                  id="current-month-filter"
                  checked={includeCurrentMonth}
                  onCheckedChange={setIncludeCurrentMonth}
                />
                <label 
                  htmlFor="current-month-filter" 
                  className="text-sm font-medium cursor-pointer"
                >
                  Include Current Month
                </label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="service-filter"
                  checked={visibleWOTypes.service}
                  onCheckedChange={(checked) => 
                    setVisibleWOTypes(prev => ({ ...prev, service: checked }))
                  }
                />
                <label 
                  htmlFor="service-filter" 
                  className="text-sm font-medium cursor-pointer flex items-center gap-2"
                >
                  <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
                  Service
                </label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="rental-filter"
                  checked={visibleWOTypes.rental}
                  onCheckedChange={(checked) => 
                    setVisibleWOTypes(prev => ({ ...prev, rental: checked }))
                  }
                />
                <label 
                  htmlFor="rental-filter" 
                  className="text-sm font-medium cursor-pointer flex items-center gap-2"
                >
                  <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                  Rental
                </label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="parts-filter"
                  checked={visibleWOTypes.parts}
                  onCheckedChange={(checked) => 
                    setVisibleWOTypes(prev => ({ ...prev, parts: checked }))
                  }
                />
                <label 
                  htmlFor="parts-filter" 
                  className="text-sm font-medium cursor-pointer flex items-center gap-2"
                >
                  <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                  Parts
                </label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="pm-filter"
                  checked={visibleWOTypes.pm}
                  onCheckedChange={(checked) => 
                    setVisibleWOTypes(prev => ({ ...prev, pm: checked }))
                  }
                />
                <label 
                  htmlFor="pm-filter" 
                  className="text-sm font-medium cursor-pointer flex items-center gap-2"
                >
                  <span className="w-3 h-3 bg-yellow-500 rounded-full"></span>
                  Preventive Maint.
                </label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="shop-filter"
                  checked={visibleWOTypes.shop}
                  onCheckedChange={(checked) => 
                    setVisibleWOTypes(prev => ({ ...prev, shop: checked }))
                  }
                />
                <label 
                  htmlFor="shop-filter" 
                  className="text-sm font-medium cursor-pointer flex items-center gap-2"
                >
                  <span className="w-3 h-3 bg-purple-500 rounded-full"></span>
                  Shop
                </label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="equipment-filter"
                  checked={visibleWOTypes.equipment}
                  onCheckedChange={(checked) => 
                    setVisibleWOTypes(prev => ({ ...prev, equipment: checked }))
                  }
                />
                <label 
                  htmlFor="equipment-filter" 
                  className="text-sm font-medium cursor-pointer flex items-center gap-2"
                >
                  <span className="w-3 h-3 bg-pink-500 rounded-full"></span>
                  Equipment
                </label>
              </div>
            </div>
            
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={getFilteredWOData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip 
                  formatter={(value) => formatCurrency(value)}
                  labelFormatter={(label) => `Month: ${label}`}
                />
                {visibleWOTypes.service && (
                  <Line 
                    type="monotone" 
                    dataKey="service_value" 
                    stroke="#3b82f6" 
                    name="Service"
                    strokeWidth={2}
                  />
                )}
                {visibleWOTypes.rental && (
                  <Line 
                    type="monotone" 
                    dataKey="rental_value" 
                    stroke="#ef4444" 
                    name="Rental"
                    strokeWidth={2}
                  />
                )}
                {visibleWOTypes.parts && (
                  <Line 
                    type="monotone" 
                    dataKey="parts_value" 
                    stroke="#10b981" 
                    name="Parts"
                    strokeWidth={2}
                  />
                )}
                {visibleWOTypes.pm && (
                  <Line 
                    type="monotone" 
                    dataKey="pm_value" 
                    stroke="#f59e0b" 
                    name="Preventive Maint."
                    strokeWidth={2}
                  />
                )}
                {visibleWOTypes.shop && (
                  <Line 
                    type="monotone" 
                    dataKey="shop_value" 
                    stroke="#8b5cf6" 
                    name="Shop"
                    strokeWidth={2}
                  />
                )}
                {visibleWOTypes.equipment && (
                  <Line 
                    type="monotone" 
                    dataKey="equipment_value" 
                    stroke="#ec4899" 
                    name="Equipment"
                    strokeWidth={2}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common tasks and reports
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Button variant="outline" className="h-20 flex-col">
              <FileText className="h-6 w-6 mb-2" />
              Sales Report
            </Button>
            <Button variant="outline" className="h-20 flex-col">
              <Package className="h-6 w-6 mb-2" />
              Inventory Report
            </Button>
            <Button variant="outline" className="h-20 flex-col">
              <Users className="h-6 w-6 mb-2" />
              Customer Report
            </Button>
            <Button variant="outline" className="h-20 flex-col">
              <TrendingUp className="h-6 w-6 mb-2" />
              Financial Summary
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Inventory Details Modal */}
      <Dialog open={inventoryModalOpen} onOpenChange={setInventoryModalOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Available Inventory Details</DialogTitle>
            <DialogDescription>
              Equipment currently available for rent
            </DialogDescription>
          </DialogHeader>
          
          {loadingInventory ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
          ) : inventoryDetails && inventoryDetails.equipment ? (
            <div className="mt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Unit #</TableHead>
                    <TableHead>Make</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Year</TableHead>
                    <TableHead>Serial #</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead className="text-right">Hours</TableHead>
                    <TableHead className="text-right">Cost</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {inventoryDetails.equipment.map((item, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{item.unitNo}</TableCell>
                      <TableCell>{item.make}</TableCell>
                      <TableCell>{item.model}</TableCell>
                      <TableCell>{item.year || '-'}</TableCell>
                      <TableCell>{item.serialNo}</TableCell>
                      <TableCell>{item.location || '-'}</TableCell>
                      <TableCell className="text-right">{item.hours.toFixed(0)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(item.cost)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              <div className="mt-4 text-sm text-muted-foreground">
                Total: {inventoryDetails.total} units available
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No inventory data available
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default Dashboard

