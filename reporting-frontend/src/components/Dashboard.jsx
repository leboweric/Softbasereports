import { useState, useRef, useEffect } from 'react'
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
    { stage: 'Leads', value: 1200, fill: '#3b82f6' },
    { stage: 'Prospects', value: 850, fill: '#8b5cf6' },
    { stage: 'Qualified', value: 620, fill: '#ec4899' },
    { stage: 'Closed', value: 380, fill: '#10b981' },
  ];

  const openCases = [
    { id: 'CS-001', client: 'Acme Corp', status: 'In Progress', daysOpen: 12, priority: 'High' },
    { id: 'CS-002', client: 'TechStart Inc', status: 'Pending Review', daysOpen: 8, priority: 'Medium' },
    { id: 'CS-003', client: 'Global Solutions', status: 'In Progress', daysOpen: 5, priority: 'High' },
    { id: 'CS-004', client: 'Innovation Labs', status: 'Awaiting Client', daysOpen: 3, priority: 'Low' },
    { id: 'CS-005', client: 'Enterprise Group', status: 'In Progress', daysOpen: 15, priority: 'Critical' },
  ];

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

  const getPriorityColor = (priority) => {
    switch(priority) {
      case 'Critical': return 'text-red-600 bg-red-50';
      case 'High': return 'text-orange-600 bg-orange-50';
      case 'Medium': return 'text-yellow-600 bg-yellow-50';
      case 'Low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

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

  // ... (original fetchPaceData, fetchForecastData, fetchCustomerRiskData, AI Prediction, formatCurrency, getMonthName, getCustomerRisk, fetchInvoiceDelayAnalysis, downloadActiveCustomers functions)

  if (user?.organization?.name === 'VITAL Worklife') {
    return <VitalExecutiveDashboard user={user} />;
  }

  // Render the complex Bennett Dashboard
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-4xl font-bold tracking-tight mb-2">AI Operations Platform</h1>
        <p className="text-lg text-gray-600">
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
                  <Button variant="outline" size="sm" onClick={() => fetchDashboardData(true)}>
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Refresh dashboard data</TooltipContent>
              </UITooltip>
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* Metric cards would go here */}
          </div>

          {/* Main Content Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
            <TabsList>
              <TabsTrigger value="sales">Sales</TabsTrigger>
              <TabsTrigger value="service">Service</TabsTrigger>
              <TabsTrigger value="parts">Parts</TabsTrigger>
              <TabsTrigger value="workorders">Work Orders</TabsTrigger>
            </TabsList>

            <TabsContent value="sales" className="space-y-4">
              {/* Sales content */}
            </TabsContent>

            <TabsContent value="service" className="space-y-4">
              {/* Service content */}
            </TabsContent>

            <TabsContent value="parts" className="space-y-4">
              {/* Parts content */}
            </TabsContent>

            <TabsContent value="workorders" className="space-y-4">
              {/* Work Orders content */}
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  )
}

export default Dashboard
