import React, { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tooltip as UITooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ReferenceLine,
  Legend
} from 'recharts'
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Package,
  Users,
  FileText,
  Download,
  RefreshCw,
  AlertTriangle,
  Wrench,
  ShoppingCart,
  Brain,
  Clock,
  HelpCircle
} from 'lucide-react'
import { apiUrl } from '@/lib/api'
import WorkOrderTypes from './WorkOrderTypes'
import ForecastAccuracy from './ForecastAccuracy'
import CustomerDetailModal from './CustomerDetailModal'

// Simple Executive Dashboard for VITAL Worklife (with seeded data)
const VitalExecutiveDashboard = ({ user }) => {
  // Sample data for visualizations
  const caseVolumeData = [
    { month: 'Jan', cases: 45, resolved: 42 },
    { month: 'Feb', cases: 52, resolved: 48 },
    { month: 'Mar', cases: 48, resolved: 46 },
    { month: 'Apr', cases: 61, resolved: 58 },
    { month: 'May', cases: 55, resolved: 52 },
    { month: 'Jun', cases: 67, resolved: 64 },
  ];

  const conversionData = [
    { stage: 'Leads', value: 1200 },
    { stage: 'Prospects', value: 850 },
    { stage: 'Qualified', value: 620 },
    { stage: 'Closed', value: 380 },
  ];

  const openCases = [
    { id: 'CS-001', client: 'Acme Corp', status: 'In Progress', daysOpen: 12, priority: 'High' },
    { id: 'CS-002', client: 'TechStart Inc', status: 'Pending Review', daysOpen: 8, priority: 'Medium' },
    { id: 'CS-003', client: 'Global Solutions', status: 'In Progress', daysOpen: 5, priority: 'High' },
    { id: 'CS-004', client: 'Innovation Labs', status: 'Awaiting Client', daysOpen: 3, priority: 'Low' },
    { id: 'CS-005', client: 'Enterprise Group', status: 'In Progress', daysOpen: 15, priority: 'Critical' },
  ];

  const getPriorityColor = (priority) => {
    switch(priority) {
      case 'Critical': return 'text-red-600 bg-red-50';
      case 'High': return 'text-orange-600 bg-orange-50';
      case 'Medium': return 'text-yellow-600 bg-yellow-50';
      case 'Low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const StatCard = ({ title, value, icon: Icon, color, trend }) => (
    <Card className="shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={`h-4 w-4 text-${color}-500`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-gray-500">{trend || '+20.1% from last month'}</p>
      </CardContent>
    </Card>
  );

  return (
    <div className="p-6 space-y-6">
      <div className="mb-6">
        <h1 className="text-4xl font-bold tracking-tight mb-2">AI Operations Platform</h1>
        <p className="text-lg text-gray-600">
          Welcome back, {user?.first_name || 'User'}! Here's what's happening with your business.
        </p>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard 
          title="Total Cases Closed" 
          value="1,250" 
          icon={FileText} 
          color="blue"
          trend="+8.2% from last month"
        />
        <StatCard 
          title="Avg. Resolution Time" 
          value="4.5 Days" 
          icon={Clock} 
          color="red"
          trend="↓ 12% improvement"
        />
        <StatCard 
          title="New Clients (HubSpot)" 
          value="+12" 
          icon={Users} 
          color="purple"
          trend="+5 from last month"
        />
        <StatCard 
          title="Monthly Revenue" 
          value="$150K" 
          icon={DollarSign} 
          color="green"
          trend="+15.3% from last month"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Case Volume Trend</CardTitle>
            <CardDescription>Monthly cases and resolutions</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={caseVolumeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="cases" fill="#3b82f6" name="Total Cases" />
                <Bar dataKey="resolved" fill="#10b981" name="Resolved" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Marketing Funnel Conversion</CardTitle>
            <CardDescription>Lead to close conversion rates</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={conversionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="stage" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8b5cf6" name="Count" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle>Top 5 Open Cases</CardTitle>
          <CardDescription>Active cases requiring attention</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Case ID</TableHead>
                  <TableHead>Client</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Days Open</TableHead>
                  <TableHead>Priority</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {openCases.map((caseItem) => (
                  <TableRow key={caseItem.id}>
                    <TableCell className="font-medium">{caseItem.id}</TableCell>
                    <TableCell>{caseItem.client}</TableCell>
                    <TableCell>{caseItem.status}</TableCell>
                    <TableCell>{caseItem.daysOpen}</TableCell>
                    <TableCell>
                      <Badge className={getPriorityColor(caseItem.priority)}>
                        {caseItem.priority}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const Dashboard = ({ user }) => {
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [paceData, setPaceData] = useState(null)
  const [forecastData, setForecastData] = useState(null)
  const [forecastLastUpdated, setForecastLastUpdated] = useState(null)
  const [customerRiskData, setCustomerRiskData] = useState(null)
  const [loadTime, setLoadTime] = useState(null)
  const [fromCache, setFromCache] = useState(false)
  // AI Predictions state
  const [workOrderPrediction, setWorkOrderPrediction] = useState(null)
  const [workOrderPredictionLoading, setWorkOrderPredictionLoading] = useState(false)
  const [customerChurnPrediction, setCustomerChurnPrediction] = useState(null)
  const [customerChurnLoading, setCustomerChurnLoading] = useState(false)
  const [partsDemandPrediction, setPartsDemandPrediction] = useState(null)
  const [partsDemandLoading, setPartsDemandLoading] = useState(false)
  // Invoice delay analysis
  const [invoiceDelayData, setInvoiceDelayData] = useState(null)
  const [invoiceDelayLoading, setInvoiceDelayLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('sales')
  // Customer search and filter
  const [customerSearchTerm, setCustomerSearchTerm] = useState('')
  const [customerRiskFilter, setCustomerRiskFilter] = useState('all') // 'all', 'at-risk', 'healthy'
  const [monthlyExpenses, setMonthlyExpenses] = useState([])
  // Customer detail modal
  const [selectedCustomer, setSelectedCustomer] = useState(null)
  const [customerDetailModalOpen, setCustomerDetailModalOpen] = useState(false)

  const isMountedRef = useRef(true)

  // Utility function to calculate linear regression trendline (omitted for brevity, assume it's here)
  // ... (original calculateLinearTrend function)

  // Memoized data (omitted for brevity, assume it's here)
  // ... (original useMemo blocks)

  // Filtered customers (omitted for brevity, assume it's here)
  // ... (original filteredCustomers useMemo)

  useEffect(() => {
    fetchDashboardData()

    // Set up auto-refresh every 5 minutes for real-time updates
    const interval = setInterval(() => {
      // Only fetch if component is still mounted
      if (isMountedRef.current) {
        fetchForecastData()
      }
    }, 5 * 60 * 1000) // 5 minutes

    return () => {
      isMountedRef.current = false
      clearInterval(interval)
    }
  }, [])

  useEffect(() => {
    // Fetch invoice delay analysis when Work Orders tab is selected
    if (activeTab === 'workorders' && !invoiceDelayData) {
      fetchInvoiceDelayAnalysis()
    }
  }, [activeTab, invoiceDelayData])

  const fetchDashboardData = async (forceRefresh = false) => {
    // Skip fetching data for VITAL Worklife users
    if (user?.organization?.name === 'VITAL Worklife') {
      setLoading(false);
      return;
    }

    const startTime = Date.now()
    setLoading(true)
    try {
      const token = localStorage.getItem('token')

      // Try optimized endpoint first
      const optimizedUrl = forceRefresh
        ? apiUrl('/api/reports/dashboard/summary-optimized?refresh=true')
        : apiUrl('/api/reports/dashboard/summary-optimized')

      let response = await fetch(optimizedUrl, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      // Only fall back if we get a 404 (endpoint doesn't exist)
      // Don't fall back for network errors or other HTTP errors
      if (!response.ok && response.status === 404) {
        console.log('Optimized endpoint not found (404), falling back to regular endpoint')
        response = await fetch(apiUrl('/api/reports/dashboard/summary'), {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        })
      }

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

        // Fetch supplementary data in parallel for better performance
        await Promise.allSettled([
          fetchPaceData(),
          fetchForecastData(),
          fetchCustomerRiskData()
        ])
      } else {
        console.error('Dashboard API failed:', response.status, response.statusText)
        // Optionally set an error state here for user feedback
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      // This catches network errors, JSON parsing errors, etc.
    } finally {
      setLoading(false)
    }
  }

  // ... (original fetchPaceData, fetchForecastData, fetchCustomerRiskData, AI Prediction, formatCurrency, getMonthName, getCustomerRisk, fetchInvoiceDelayAnalysis, fetchExpenseData, downloadActiveCustomers functions)

  if (user?.organization?.name === 'VITAL Worklife') {
    return <VitalExecutiveDashboard user={user} />;
  }

  // Render the complex Bennett Dashboard
  return (
    <div className="p-6">
      <div className="mb-6">
        <p className="text-sm text-gray-600 mb-2">AI Operations Platform</p>
        <p className="text-lg text-gray-700 mb-4">
          Welcome back, {user?.first_name || 'User'}! Here's what's happening with your business.
        </p>
      </div>
      {loading && (
        <div className="flex justify-center items-center h-full">
          <LoadingSpinner size={50} />
        </div>
      )}
      {/* Main Dashboard Content */}
      {!loading && dashboardData && (
        <div className="space-y-6">
          {/* Header and Refresh Button */}
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold tracking-tight">Executive Dashboard</h1>
            <div className="flex space-x-2">
              <UITooltip>
                <TooltipTrigger asChild>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => fetchDashboardData(true)}
                    disabled={loading}
                  >
                    <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Force Refresh Data</p>
                </TooltipContent>
              </UITooltip>
            </div>
          </div>

          {/* Data Load Info */}
          <div className="text-sm text-gray-500">
            Data loaded in {loadTime} seconds {fromCache && '(from cache)'}
          </div>

          {/* Tabs for different views */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList>
              <TabsTrigger value="sales">Sales & Finance</TabsTrigger>
              <TabsTrigger value="parts">Parts</TabsTrigger>
              <TabsTrigger value="service">Service & Work Orders</TabsTrigger>
              <TabsTrigger value="customers">Customers & AI</TabsTrigger>
              <TabsTrigger value="accuracy">Forecast Accuracy</TabsTrigger>
            </TabsList>
            
            {/* Sales & Finance Tab */}
            <TabsContent value="sales" className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Sales Pace</CardTitle>
                    <DollarSign className="h-4 w-4 text-gray-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.sales_pace_ytd_formatted}</div>
                    <p className="text-xs text-gray-500">Target: {dashboardData.sales_pace_target_formatted}</p>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Parts Pace</CardTitle>
                    <Package className="h-4 w-4 text-gray-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.parts_pace_ytd_formatted}</div>
                    <p className="text-xs text-gray-500">Target: {dashboardData.parts_pace_target_formatted}</p>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Service Pace</CardTitle>
                    <Wrench className="h-4 w-4 text-gray-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.service_pace_ytd_formatted}</div>
                    <p className="text-xs text-gray-500">Target: {dashboardData.service_pace_target_formatted}</p>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Rental Pace</CardTitle>
                    <ShoppingCart className="h-4 w-4 text-gray-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.rental_pace_ytd_formatted}</div>
                    <p className="text-xs text-gray-500">Target: {dashboardData.rental_pace_target_formatted}</p>
                  </CardContent>
                </Card>
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Sales Pace Trend</CardTitle>
                    <CardDescription>YTD Sales Pace vs. Target</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <ComposedChart data={paceData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
                        <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                        <Tooltip />
                        <Legend />
                        <Bar yAxisId="left" dataKey="ytd_sales" fill="#8884d8" name="YTD Sales" />
                        <Line yAxisId="right" type="monotone" dataKey="target" stroke="#82ca9d" name="Target" />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Monthly Sales Forecast</CardTitle>
                    <CardDescription>Next 3 Months Forecast (Last Updated: {forecastLastUpdated})</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={forecastData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="forecast" fill="#ffc658" name="Forecast" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Sales by Department</CardTitle>
                    <CardDescription>YTD Sales by Department</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={dashboardData.sales_by_department}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          outerRadius={100}
                          fill="#8884d8"
                          label
                        >
                          {dashboardData.sales_by_department.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={['#0088FE', '#00C49F', '#FFBB28', '#FF8042'][index % 4]} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Top 5 Sales Reps</CardTitle>
                    <CardDescription>YTD Sales</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={dashboardData.top_sales_reps}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="sales" fill="#8884d8" name="Sales" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Parts Tab */}
            <TabsContent value="parts" className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Parts Sales YTD</CardTitle>
                    <Package className="h-4 w-4 text-gray-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.parts_sales_ytd_formatted}</div>
                    <p className="text-xs text-gray-500">Target: {dashboardData.parts_sales_target_formatted}</p>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Inventory Value</CardTitle>
                    <DollarSign className="h-4 w-4 text-gray-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.inventory_value_formatted}</div>
                    <p className="text-xs text-gray-500">Turnover: {dashboardData.inventory_turnover}</p>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Top Selling Parts</CardTitle>
                    <TrendingUp className="h-4 w-4 text-gray-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.top_selling_part}</div>
                    <p className="text-xs text-gray-500">Units Sold: {dashboardData.top_selling_part_units}</p>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Parts Fill Rate</CardTitle>
                    <Badge className="h-4 w-4 text-gray-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.parts_fill_rate}</div>
                    <p className="text-xs text-gray-500">Target: 95%</p>
                  </CardContent>
                </Card>
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Parts Sales Trend</CardTitle>
                    <CardDescription>Monthly Parts Sales</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={dashboardData.parts_sales_trend}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="sales" stroke="#82ca9d" name="Parts Sales" />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Inventory Breakdown</CardTitle>
                    <CardDescription>Value by Category</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={dashboardData.inventory_breakdown}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          outerRadius={100}
                          fill="#8884d8"
                          label
                        >
                          {dashboardData.inventory_breakdown.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={['#FF8042', '#FFBB28', '#00C49F', '#0088FE'][index % 4]} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Service Tab */}
            <TabsContent value="service" className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Service Sales YTD</CardTitle>
                    <Wrench className="h-4 w-4 text-gray-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.service_sales_ytd_formatted}</div>
                    <p className="text-xs text-gray-500">Target: {dashboardData.service_sales_target_formatted}</p>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Work Order Count</CardTitle>
                    <FileText className="h-4 w-4 text-gray-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.work_order_count}</div>
                    <p className="text-xs text-gray-500">Open: {dashboardData.open_work_orders}</p>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Avg. Repair Time</CardTitle>
                    <Clock className="h-4 w-4 text-gray-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.avg_repair_time}</div>
                    <p className="text-xs text-gray-500">Target: 4.0 Days</p>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Customer Satisfaction</CardTitle>
                    <Badge className="h-4 w-4 text-gray-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.csat_score}</div>
                    <p className="text-xs text-gray-500">Target: 95%</p>
                  </CardContent>
                </Card>
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Work Order Types</CardTitle>
                    <CardDescription>Breakdown by Type</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <WorkOrderTypes workOrderTypes={dashboardData.work_order_types} />
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Invoice Delay Analysis</CardTitle>
                    <CardDescription>Days between completion and invoicing</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={invoiceDelayData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="days" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="count" fill="#8884d8" name="Work Orders" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Customers & AI Tab */}
            <TabsContent value="customers" className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Customers</CardTitle>
                    <Users className="h-4 w-4 text-gray-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.total_customers}</div>
                    <p className="text-xs text-gray-500">Active: {dashboardData.active_customers}</p>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Customer Risk Score</CardTitle>
                    <AlertTriangle className="h-4 w-4 text-red-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.avg_customer_risk}</div>
                    <p className="text-xs text-gray-500">High Risk: {dashboardData.high_risk_customers}</p>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">AI Prediction Accuracy</CardTitle>
                    <Brain className="h-4 w-4 text-green-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{dashboardData.ai_accuracy}</div>
                    <p className="text-xs text-gray-500">Model: {dashboardData.ai_model}</p>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Download Active Customers</CardTitle>
                    <Download className="h-4 w-4 text-blue-500" />
                  </CardHeader>
                  <CardContent>
                    <Button onClick={downloadActiveCustomers} className="w-full">
                      Download CSV
                    </Button>
                    <p className="text-xs text-gray-500">Last Export: {dashboardData.last_export}</p>
                  </CardContent>
                </Card>
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Customer Risk Distribution</CardTitle>
                    <CardDescription>Breakdown by Risk Level</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={customerRiskData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="risk_level" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="count" fill="#ff7300" name="Customers" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle>Top 5 High-Risk Customers</CardTitle>
                    <CardDescription>Click to view details</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Customer</TableHead>
                          <TableHead>Risk Score</TableHead>
                          <TableHead>Last Order</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {dashboardData.high_risk_customers_list.map((customer) => (
                          <TableRow 
                            key={customer.id} 
                            onClick={() => {
                              setSelectedCustomer(customer)
                              setCustomerDetailModalOpen(true)
                            }}
                            className="cursor-pointer hover:bg-gray-50"
                          >
                            <TableCell className="font-medium">{customer.name}</TableCell>
                            <TableCell className="text-red-500">{customer.risk_score}</TableCell>
                            <TableCell>{customer.last_order}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Forecast Accuracy Tab */}
            <TabsContent value="accuracy" className="space-y-4">
              <ForecastAccuracy />
            </TabsContent>
          </Tabs>
        </div>
      )}
      {/* Customer Detail Modal */}
      <CustomerDetailModal 
        customer={selectedCustomer}
        isOpen={customerDetailModalOpen}
        onClose={() => {
          setCustomerDetailModalOpen(false)
          setSelectedCustomer(null)
        }}
      />
    </div>
  )
}

export default Dashboard
