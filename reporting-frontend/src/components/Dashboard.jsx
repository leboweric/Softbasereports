import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import EquipmentDebug from './EquipmentDebug'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
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
  Clock
} from 'lucide-react'
import { apiUrl } from '@/lib/api'
import WorkOrderTypes from './WorkOrderTypes'

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

  useEffect(() => {
    fetchDashboardData()
    
    // Set up auto-refresh every 5 minutes for real-time updates
    const interval = setInterval(() => {
      fetchForecastData() // Update forecast more frequently for real-time adjustments
    }, 5 * 60 * 1000) // 5 minutes
    
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    // Fetch invoice delay analysis when Work Orders tab is selected
    if (activeTab === 'workorders' && !invoiceDelayData) {
      fetchInvoiceDelayAnalysis()
    }
  }, [activeTab])

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
        
        // Fetch pace data
        fetchPaceData()
        // Fetch forecast data
        fetchForecastData()
        // Fetch customer risk data
        fetchCustomerRiskData()
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchPaceData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/dashboard/sales-pace'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        console.log('Pace data fetched:', data)
        setPaceData(data)
      } else {
        console.error('Pace endpoint returned error:', response.status)
        // Set mock data for testing
        setPaceData({
          pace: {
            percentage: 5.2,
            percentage_no_equipment: 3.8,
            ahead_behind: 'ahead',
            ahead_behind_no_equipment: 'ahead'
          }
        })
      }
    } catch (error) {
      console.error('Error fetching pace data:', error)
      // Set mock data for testing
      setPaceData({
        pace: {
          percentage: 5.2,
          percentage_no_equipment: 3.8,
          ahead_behind: 'ahead',
          ahead_behind_no_equipment: 'ahead'
        }
      })
    }
  }

  const fetchForecastData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/dashboard/sales-forecast'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        console.log('Forecast data fetched:', data)
        setForecastData(data)
        setForecastLastUpdated(new Date())
      }
    } catch (error) {
      console.error('Error fetching forecast data:', error)
    }
  }

  const fetchCustomerRiskData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/dashboard/customer-risk-analysis'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        console.log('Customer risk data fetched:', data)
        console.log('Number of customers analyzed:', data.customers?.length)
        console.log('Customers with risk:', data.customers?.filter(c => c.risk_level !== 'none')?.length)
        setCustomerRiskData(data)
      } else {
        console.error('Customer risk API failed:', response.status, response.statusText)
      }
    } catch (error) {
      console.error('Error fetching customer risk data:', error)
    }
  }

  // AI Prediction Functions
  const fetchWorkOrderPrediction = async (forceRefresh = false) => {
    setWorkOrderPredictionLoading(true)
    try {
      const token = localStorage.getItem('token')
      const url = forceRefresh 
        ? apiUrl('/api/ai/predictions/work-orders?refresh=true')
        : apiUrl('/api/ai/predictions/work-orders')
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setWorkOrderPrediction(data)
      }
    } catch (error) {
      console.error('Error fetching work order prediction:', error)
    } finally {
      setWorkOrderPredictionLoading(false)
    }
  }

  const fetchCustomerChurnPrediction = async (forceRefresh = false) => {
    setCustomerChurnLoading(true)
    try {
      const token = localStorage.getItem('token')
      const url = forceRefresh 
        ? apiUrl('/api/ai/predictions/customer-churn?refresh=true')
        : apiUrl('/api/ai/predictions/customer-churn')
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setCustomerChurnPrediction(data)
      }
    } catch (error) {
      console.error('Error fetching customer churn prediction:', error)
    } finally {
      setCustomerChurnLoading(false)
    }
  }

  const fetchPartsDemandPrediction = async (forceRefresh = false) => {
    setPartsDemandLoading(true)
    try {
      const token = localStorage.getItem('token')
      const url = forceRefresh 
        ? apiUrl('/api/ai/predictions/parts-demand?refresh=true')
        : apiUrl('/api/ai/predictions/parts-demand')
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setPartsDemandPrediction(data)
      }
    } catch (error) {
      console.error('Error fetching parts demand prediction:', error)
    } finally {
      setPartsDemandLoading(false)
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

  const getMonthName = (monthNumber) => {
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 
                    'July', 'August', 'September', 'October', 'November', 'December']
    return months[monthNumber - 1] || 'Current Month'
  }

  const getCustomerRisk = (customerName) => {
    if (!customerRiskData?.customers) {
      console.log('No customer risk data available')
      return null
    }
    const risk = customerRiskData.customers.find(c => c.customer_name === customerName)
    if (!risk) {
      console.log(`No risk data found for customer: ${customerName}`)
    } else if (risk.risk_level !== 'none') {
      console.log(`Risk found for ${customerName}:`, risk.risk_level, risk.risk_factors)
    }
    return risk
  }

  const fetchInvoiceDelayAnalysis = async () => {
    setInvoiceDelayLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/dashboard/invoice-delay-analysis'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setInvoiceDelayData(data)
      } else {
        console.error('Failed to fetch invoice delay analysis')
      }
    } catch (error) {
      console.error('Error fetching invoice delay analysis:', error)
    } finally {
      setInvoiceDelayLoading(false)
    }
  }

  const downloadActiveCustomers = async (period = 'last30') => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/dashboard/active-customers-export?period=${period}`), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        
        // Convert to CSV
        const headers = [
          'Customer Name',
          'Invoice Count', 
          'First Invoice Date',
          'Last Invoice Date',
          'Total Sales',
          'Average Invoice Value'
        ]
        
        const csvContent = [
          headers.join(','),
          ...data.customers.map(customer => [
            `"${customer.customer_name}"`,
            customer.invoice_count,
            customer.first_invoice_date,
            customer.last_invoice_date,
            customer.total_sales.toFixed(2),
            customer.avg_invoice_value.toFixed(2)
          ].join(','))
        ].join('\n')
        
        // Create download
        const blob = new Blob([csvContent], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `active-customers-${data.period.toLowerCase().replace(/\s+/g, '-')}-${new Date().toISOString().split('T')[0]}.csv`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } else {
        console.error('Failed to download active customers data')
      }
    } catch (error) {
      console.error('Error downloading active customers:', error)
    }
  }



  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

  // Helper function to calculate percentage change
  const calculatePercentageChange = (current, previous) => {
    if (!previous || previous === 0) return null
    const change = ((current - previous) / previous) * 100
    return change
  }

  // Custom bar shape with pace indicator
  const CustomBar = (props) => {
    const { fill, x, y, width, height, payload } = props
    const currentMonth = new Date().getMonth() + 1
    const currentYear = new Date().getFullYear()
    
    // Check if this is the current month
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    const isCurrentMonth = payload && 
      payload.month === monthNames[currentMonth - 1] && 
      payload.year === currentYear &&
      paceData
    
    // Debug logging
    if (payload && payload.month === 'Aug') {
      console.log('August bar detected:', {
        payload,
        currentMonth,
        currentYear,
        isCurrentMonth,
        paceData: !!paceData
      })
    }
    
    return (
      <g>
        <rect x={x} y={y} width={width} height={height} fill={fill} />
        {isCurrentMonth && paceData && (
          <g>
            {/* Pace indicator */}
            <rect 
              x={x} 
              y={y - 20} 
              width={width} 
              height={18} 
              fill={paceData.pace.percentage > 0 ? '#10b981' : '#ef4444'}
              rx={4}
            />
            <text 
              x={x + width / 2} 
              y={y - 6} 
              textAnchor="middle" 
              fill="white" 
              fontSize="11" 
              fontWeight="bold"
            >
              {paceData.pace.percentage > 0 ? '+' : ''}{paceData.pace.percentage}%
            </text>
            {/* Arrow icon */}
            {paceData.pace.percentage !== 0 && (
              <text 
                x={x + width / 2} 
                y={y - 25} 
                textAnchor="middle" 
                fill={paceData.pace.percentage > 0 ? '#10b981' : '#ef4444'}
                fontSize="16"
              >
                {paceData.pace.percentage > 0 ? '↑' : '↓'}
              </text>
            )}
          </g>
        )}
      </g>
    )
  }

  // Custom bar shape for No Equipment chart
  const CustomBarNoEquipment = (props) => {
    const { fill, x, y, width, height, payload } = props
    const currentMonth = new Date().getMonth() + 1
    const currentYear = new Date().getFullYear()
    
    // Check if this is the current month
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    const isCurrentMonth = payload && 
      payload.month === monthNames[currentMonth - 1] && 
      payload.year === currentYear &&
      paceData
    
    return (
      <g>
        <rect x={x} y={y} width={width} height={height} fill={fill} />
        {isCurrentMonth && paceData && (
          <g>
            {/* Pace indicator */}
            <rect 
              x={x} 
              y={y - 20} 
              width={width} 
              height={18} 
              fill={paceData.pace.percentage_no_equipment > 0 ? '#10b981' : '#ef4444'}
              rx={4}
            />
            <text 
              x={x + width / 2} 
              y={y - 6} 
              textAnchor="middle" 
              fill="white" 
              fontSize="11" 
              fontWeight="bold"
            >
              {paceData.pace.percentage_no_equipment > 0 ? '+' : ''}{paceData.pace.percentage_no_equipment}%
            </text>
            {/* Arrow icon */}
            {paceData.pace.percentage_no_equipment !== 0 && (
              <text 
                x={x + width / 2} 
                y={y - 25} 
                textAnchor="middle" 
                fill={paceData.pace.percentage_no_equipment > 0 ? '#10b981' : '#ef4444'}
                fontSize="16"
              >
                {paceData.pace.percentage_no_equipment > 0 ? '↑' : '↓'}
              </text>
            )}
          </g>
        )}
      </g>
    )
  }

  // Custom bar shape for Quotes chart
  const CustomBarQuotes = (props) => {
    const { fill, x, y, width, height, payload } = props
    const currentMonth = new Date().getMonth() + 1
    const currentYear = new Date().getFullYear()
    
    // Check if this is the current month
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    const isCurrentMonth = payload && 
      payload.month === monthNames[currentMonth - 1] && 
      payload.year === currentYear &&
      paceData
    
    return (
      <g>
        <rect x={x} y={y} width={width} height={height} fill={fill} />
        {isCurrentMonth && paceData && paceData.quotes && (
          <g>
            {/* Pace indicator */}
            <rect 
              x={x} 
              y={y - 20} 
              width={width} 
              height={18} 
              fill={paceData.quotes.pace_percentage > 0 ? '#10b981' : '#ef4444'}
              rx={4}
            />
            <text 
              x={x + width / 2} 
              y={y - 6} 
              textAnchor="middle" 
              fill="white" 
              fontSize="11" 
              fontWeight="bold"
            >
              {paceData.quotes.pace_percentage > 0 ? '+' : ''}{paceData.quotes.pace_percentage}%
            </text>
            {/* Arrow icon */}
            {paceData.quotes.pace_percentage !== 0 && (
              <text 
                x={x + width / 2} 
                y={y - 25} 
                textAnchor="middle" 
                fill={paceData.quotes.pace_percentage > 0 ? '#10b981' : '#ef4444'}
                fontSize="16"
              >
                {paceData.quotes.pace_percentage > 0 ? '↑' : '↓'}
              </text>
            )}
          </g>
        )}
      </g>
    )
  }

  // Helper function to format percentage with color
  const formatPercentage = (percentage) => {
    if (percentage === null) return ''
    const sign = percentage >= 0 ? '+' : ''
    const color = percentage >= 0 ? 'text-green-600' : 'text-red-600'
    return <span className={`ml-2 ${color}`}>({sign}{percentage.toFixed(1)}%)</span>
  }

  // Custom tooltip for Monthly Sales (No Equipment)
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length && dashboardData?.monthly_sales_by_stream) {
      const data = dashboardData.monthly_sales_by_stream
      const currentIndex = data.findIndex(item => item.month === label)
      const monthData = data[currentIndex]
      const previousMonthData = currentIndex > 0 ? data[currentIndex - 1] : null
      const total = payload[0].value
      const previousTotal = previousMonthData ? 
        (previousMonthData.parts + previousMonthData.labor + previousMonthData.rental + previousMonthData.misc) : null
      
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="font-semibold mb-2">{label}</p>
          <p className="font-semibold text-green-600 mb-2">
            Total: {formatCurrency(total)}
            {formatPercentage(calculatePercentageChange(total, previousTotal))}
          </p>
          {monthData && (
            <div className="text-sm space-y-1 border-t pt-2">
              <div className="flex justify-between">
                <span>Parts:</span>
                <span className="ml-4">
                  {formatCurrency(monthData.parts)}
                  {previousMonthData && formatPercentage(calculatePercentageChange(monthData.parts, previousMonthData.parts))}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Labor:</span>
                <span className="ml-4">
                  {formatCurrency(monthData.labor)}
                  {previousMonthData && formatPercentage(calculatePercentageChange(monthData.labor, previousMonthData.labor))}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Rental:</span>
                <span className="ml-4">
                  {formatCurrency(monthData.rental)}
                  {previousMonthData && formatPercentage(calculatePercentageChange(monthData.rental, previousMonthData.rental))}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Misc:</span>
                <span className="ml-4">
                  {formatCurrency(monthData.misc)}
                  {previousMonthData && formatPercentage(calculatePercentageChange(monthData.misc, previousMonthData.misc))}
                </span>
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
          <h1 className="text-3xl font-bold tracking-tight">Bennett Business Intelligence</h1>
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
            onClick={() => {
              fetchDashboardData(true)
              fetchForecastData()
              fetchCustomerRiskData()
            }}
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

      {/* Tabbed Interface */}
      <Tabs defaultValue="sales" value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full max-w-lg grid-cols-4">
          <TabsTrigger value="sales">Sales</TabsTrigger>
          <TabsTrigger value="customers">Customers</TabsTrigger>
          <TabsTrigger value="workorders">Work Orders</TabsTrigger>
          <TabsTrigger value="forecast">AI Forecasts</TabsTrigger>
        </TabsList>

        {/* Sales Tab */}
        <TabsContent value="sales" className="space-y-4">
          {/* Key Sales Metrics */}
          <div className="grid gap-4 md:grid-cols-2">
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

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Fiscal YTD Sales</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(dashboardData?.ytd_sales || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Since March {new Date().getFullYear()}
            </p>
              </CardContent>
            </Card>
          </div>


          {/* Charts - First Row */}
          <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle>Monthly Sales</CardTitle>
                <CardDescription>
                  Total sales since March 2025
                </CardDescription>
              </div>
              {dashboardData?.monthly_sales && dashboardData.monthly_sales.length > 0 && (() => {
                const completeMonths = dashboardData.monthly_sales.slice(0, -1)
                const avgRevenue = completeMonths.reduce((sum, item) => sum + item.amount, 0) / completeMonths.length
                const avgMargin = completeMonths.filter(item => item.margin !== null && item.margin !== undefined)
                  .reduce((sum, item, _, arr) => sum + item.margin / arr.length, 0)
                return (
                  <div className="text-right">
                    <div className="mb-2">
                      <p className="text-sm text-muted-foreground">Avg Revenue</p>
                      <p className="text-lg font-semibold">{formatCurrency(avgRevenue)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Avg Margin</p>
                      <p className="text-lg font-semibold">{avgMargin.toFixed(1)}%</p>
                    </div>
                  </div>
                )
              })()}
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <ComposedChart data={dashboardData?.monthly_sales || []} margin={{ top: 40, right: 60, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis yAxisId="left" tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => `${value}%`} />
                <Tooltip content={({ active, payload, label }) => {
                  if (active && payload && payload.length && dashboardData?.monthly_sales) {
                    const data = dashboardData.monthly_sales
                    const currentIndex = data.findIndex(item => item.month === label)
                    const monthData = data[currentIndex]
                    const previousValue = currentIndex > 0 ? data[currentIndex - 1].amount : null
                    
                    return (
                      <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                        <p className="font-semibold mb-1">{label}</p>
                        <p className="text-green-600">
                          Revenue: {formatCurrency(monthData?.amount || 0)}
                          {formatPercentage(calculatePercentageChange(monthData?.amount, previousValue))}
                        </p>
                        {monthData?.margin !== null && monthData?.margin !== undefined && (
                          <p className="text-blue-600">
                            Margin: {monthData.margin.toFixed(1)}%
                          </p>
                        )}
                      </div>
                    )
                  }
                  return null
                }} />
                <Legend />
                <Bar yAxisId="left" dataKey="amount" fill="#8884d8" name="Revenue" shape={<CustomBar />} />
                <Line yAxisId="right" type="monotone" dataKey="margin" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981' }} name="Gross Margin %" />
                {dashboardData?.monthly_sales && dashboardData.monthly_sales.length > 0 && (() => {
                  // Only calculate average for complete months (exclude current month - August)
                  const completeMonths = dashboardData.monthly_sales.slice(0, -1)
                  const average = completeMonths.reduce((sum, item) => sum + item.amount, 0) / completeMonths.length
                  return (
                    <ReferenceLine 
                      yAxisId="left"
                      y={average} 
                      stroke="#666" 
                      strokeDasharray="3 3"
                      label={{ value: "Average", position: "insideTopRight" }}
                    />
                  )
                })()}
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle>Monthly Sales (No Equipment)</CardTitle>
                <CardDescription>
                  Sales excluding new equipment
                </CardDescription>
              </div>
              {dashboardData?.monthly_sales_no_equipment && dashboardData.monthly_sales_no_equipment.length > 0 && (() => {
                const completeMonths = dashboardData.monthly_sales_no_equipment.slice(0, -1)
                const avgRevenue = completeMonths.reduce((sum, item) => sum + item.amount, 0) / completeMonths.length
                const avgMargin = completeMonths.filter(item => item.margin !== null && item.margin !== undefined)
                  .reduce((sum, item, _, arr) => sum + item.margin / arr.length, 0)
                return (
                  <div className="text-right">
                    <div className="mb-2">
                      <p className="text-sm text-muted-foreground">Avg Revenue</p>
                      <p className="text-lg font-semibold">{formatCurrency(avgRevenue)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Avg Margin</p>
                      <p className="text-lg font-semibold">{avgMargin.toFixed(1)}%</p>
                    </div>
                  </div>
                )
              })()}
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <ComposedChart data={dashboardData?.monthly_sales_no_equipment || []} margin={{ top: 40, right: 60, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis yAxisId="left" tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => `${value}%`} />
                <Tooltip content={({ active, payload, label }) => {
                  if (active && payload && dashboardData?.monthly_sales_no_equipment) {
                    const data = dashboardData.monthly_sales_no_equipment
                    const currentIndex = data.findIndex(item => item.month === label)
                    const monthData = data[currentIndex]
                    const previousValue = currentIndex > 0 ? data[currentIndex - 1].amount : null
                    const previousMargin = currentIndex > 0 ? data[currentIndex - 1].margin : null
                    
                    // Also get the stream data for detailed breakdown if available
                    const streamData = dashboardData?.monthly_sales_by_stream
                    const streamMonthData = streamData ? streamData[currentIndex] : null
                    const previousStreamData = currentIndex > 0 && streamData ? streamData[currentIndex - 1] : null
                    
                    // Calculate margin change in percentage points
                    const marginChange = previousMargin !== null && monthData?.margin !== null 
                      ? monthData.margin - previousMargin 
                      : null
                    
                    return (
                      <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                        <p className="font-semibold mb-2">{label}</p>
                        <p className="font-semibold text-green-600">
                          Total: {formatCurrency(monthData?.amount || 0)}
                          {formatPercentage(calculatePercentageChange(monthData?.amount, previousValue))}
                        </p>
                        {monthData?.margin !== null && monthData?.margin !== undefined && (
                          <p className="text-blue-600 mb-2">
                            Margin: {monthData.margin.toFixed(1)}%
                            {marginChange !== null && (
                              <span className={`ml-2 text-sm ${marginChange > 0 ? 'text-green-600' : marginChange < 0 ? 'text-red-600' : 'text-gray-500'}`}>
                                ({marginChange > 0 ? '+' : ''}{marginChange.toFixed(1)} pts)
                              </span>
                            )}
                          </p>
                        )}
                        {streamMonthData && (
                          <div className="text-sm space-y-1 border-t pt-2">
                            <div className="flex justify-between">
                              <span>Parts:</span>
                              <span className="ml-4">
                                {formatCurrency(streamMonthData.parts)}
                                {previousStreamData && formatPercentage(calculatePercentageChange(streamMonthData.parts, previousStreamData.parts))}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span>Labor:</span>
                              <span className="ml-4">
                                {formatCurrency(streamMonthData.labor)}
                                {previousStreamData && formatPercentage(calculatePercentageChange(streamMonthData.labor, previousStreamData.labor))}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span>Rental:</span>
                              <span className="ml-4">
                                {formatCurrency(streamMonthData.rental)}
                                {previousStreamData && formatPercentage(calculatePercentageChange(streamMonthData.rental, previousStreamData.rental))}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span>Misc:</span>
                              <span className="ml-4">
                                {formatCurrency(streamMonthData.misc)}
                                {previousStreamData && formatPercentage(calculatePercentageChange(streamMonthData.misc, previousStreamData.misc))}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  }
                  return null
                }} />
                <Legend />
                <Bar yAxisId="left" dataKey="amount" fill="#10b981" name="Revenue" shape={<CustomBarNoEquipment />} />
                <Line yAxisId="right" type="monotone" dataKey="margin" stroke="#f59e0b" strokeWidth={2} dot={{ fill: '#f59e0b' }} name="Gross Margin %" />
                {dashboardData?.monthly_sales_no_equipment && dashboardData.monthly_sales_no_equipment.length > 0 && (() => {
                  // Only calculate average for complete months (exclude current month - August)
                  const completeMonths = dashboardData.monthly_sales_no_equipment.slice(0, -1)
                  const average = completeMonths.reduce((sum, item) => sum + item.amount, 0) / completeMonths.length
                  return (
                    <ReferenceLine 
                      yAxisId="left"
                      y={average} 
                      stroke="#666" 
                      strokeDasharray="3 3"
                      label={{ value: "Average", position: "insideTopRight" }}
                    />
                  )
                })()}
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
            </Card>
          </div>

          {/* Charts - Second Row */}
          <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle>Monthly Quotes</CardTitle>
                <CardDescription>
                  Latest quote value per work order each month
                </CardDescription>
              </div>
              {dashboardData?.monthly_quotes && dashboardData.monthly_quotes.length > 0 && (() => {
                const completeMonths = dashboardData.monthly_quotes.slice(0, -1)
                const average = completeMonths.reduce((sum, item) => sum + item.amount, 0) / completeMonths.length
                return (
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Average</p>
                    <p className="text-lg font-semibold">{formatCurrency(average)}</p>
                  </div>
                )
              })()}
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={dashboardData?.monthly_quotes || []} margin={{ top: 40, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                <Tooltip content={({ active, payload, label }) => {
                  if (active && payload && payload.length && dashboardData?.monthly_quotes) {
                    const data = dashboardData.monthly_quotes
                    const currentIndex = data.findIndex(item => item.month === label)
                    const currentValue = payload[0].value
                    const previousValue = currentIndex > 0 ? data[currentIndex - 1].amount : null
                    
                    return (
                      <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                        <p className="font-semibold mb-1">{label}</p>
                        <p className="text-yellow-600">
                          {formatCurrency(currentValue)}
                          {formatPercentage(calculatePercentageChange(currentValue, previousValue))}
                        </p>
                      </div>
                    )
                  }
                  return null
                }} />
                <Bar dataKey="amount" fill="#f59e0b" shape={<CustomBarQuotes />} />
                {dashboardData?.monthly_quotes && dashboardData.monthly_quotes.length > 0 && (() => {
                  // Only calculate average for complete months (exclude current month - August)
                  const completeMonths = dashboardData.monthly_quotes.slice(0, -1)
                  const average = completeMonths.reduce((sum, item) => sum + item.amount, 0) / completeMonths.length
                  return (
                    <ReferenceLine 
                      y={average} 
                      stroke="#666" 
                      strokeDasharray="3 3"
                      label={{ value: "Average", position: "insideTopRight" }}
                    />
                  )
                })()}
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle>New Equipment Sales</CardTitle>
                    <CardDescription>
                      New equipment revenue and gross margin
                    </CardDescription>
                  </div>
                  {dashboardData?.monthly_equipment_sales && dashboardData.monthly_equipment_sales.length > 0 && (() => {
                    const completeMonths = dashboardData.monthly_equipment_sales.slice(0, -1)
                    const avgRevenue = completeMonths.reduce((sum, item) => sum + item.amount, 0) / completeMonths.length
                    const avgMargin = completeMonths.filter(item => item.margin !== null && item.margin !== undefined)
                      .reduce((sum, item, _, arr) => sum + item.margin / arr.length, 0)
                    const avgUnits = completeMonths.reduce((sum, item) => sum + (item.units || 0), 0) / completeMonths.length
                    return (
                      <div className="text-right">
                        <div className="mb-2">
                          <p className="text-sm text-muted-foreground">Avg Revenue</p>
                          <p className="text-lg font-semibold">{formatCurrency(avgRevenue)}</p>
                        </div>
                        <div className="mb-2">
                          <p className="text-sm text-muted-foreground">Avg Units/Month</p>
                          <p className="text-lg font-semibold">{avgUnits.toFixed(1)}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Avg Margin</p>
                          <p className="text-lg font-semibold">{avgMargin.toFixed(1)}%</p>
                        </div>
                      </div>
                    )
                  })()}
                </div>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={350}>
                  <ComposedChart data={dashboardData?.monthly_equipment_sales || []} margin={{ top: 40, right: 60, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis yAxisId="left" tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                    <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => `${value}%`} />
                    <Tooltip content={({ active, payload, label }) => {
                      if (active && payload && dashboardData?.monthly_equipment_sales) {
                        const data = dashboardData.monthly_equipment_sales
                        const currentIndex = data.findIndex(item => item.month === label)
                        const monthData = data[currentIndex]
                        const previousValue = currentIndex > 0 ? data[currentIndex - 1].amount : null
                        const previousUnits = currentIndex > 0 ? data[currentIndex - 1].units : null
                        
                        return (
                          <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                            <p className="font-semibold mb-2">{label}</p>
                            <p className="font-semibold text-cyan-600">
                              Units Sold: {monthData?.units || 0}
                              {previousUnits !== null && previousUnits > 0 && (
                                <span className="text-xs ml-2">
                                  ({((monthData?.units - previousUnits) / previousUnits * 100).toFixed(0)}% vs prev)
                                </span>
                              )}
                            </p>
                            <p className="font-semibold text-green-600">
                              Revenue: {formatCurrency(monthData?.amount || 0)}
                              {formatPercentage(calculatePercentageChange(monthData?.amount, previousValue))}
                            </p>
                            {monthData?.margin !== null && monthData?.margin !== undefined && (
                              <p className="text-blue-600">
                                Margin: {monthData.margin.toFixed(1)}%
                              </p>
                            )}
                          </div>
                        )
                      }
                      return null
                    }} />
                    <Legend />
                    <Bar yAxisId="left" dataKey="amount" fill="#06b6d4" name="Revenue" />
                    <Line yAxisId="right" type="monotone" dataKey="margin" stroke="#f59e0b" strokeWidth={2} dot={{ fill: '#f59e0b' }} name="Gross Margin %" />
                    {dashboardData?.monthly_equipment_sales && dashboardData.monthly_equipment_sales.length > 0 && (() => {
                      const completeMonths = dashboardData.monthly_equipment_sales.slice(0, -1)
                      const average = completeMonths.reduce((sum, item) => sum + item.amount, 0) / completeMonths.length
                      return (
                        <ReferenceLine 
                          yAxisId="left"
                          y={average} 
                          stroke="#666" 
                          strokeDasharray="3 3"
                          label={{ value: "Average", position: "insideTopRight" }}
                        />
                      )
                    })()}
                  </ComposedChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Temporary debug component */}
          <EquipmentDebug />

        </TabsContent>

    {/* Customers Tab */}
    <TabsContent value="customers" className="space-y-4">
          {/* Customer Metrics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Customers</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${
                  dashboardData?.active_customers_change > 0 ? 'text-green-600' :
                  dashboardData?.active_customers_change < 0 ? 'text-red-600' :
                  'text-gray-900'
                }`}>
                  {dashboardData?.active_customers || 0}
                  {dashboardData?.active_customers_change !== undefined && dashboardData?.active_customers_change !== 0 && (
                    <span className={`ml-2 text-sm font-normal ${
                      dashboardData.active_customers_change > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {dashboardData.active_customers_change > 0 ? '+' : ''}{dashboardData.active_customers_change}
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  Customers with invoices in last 30 days
                  {dashboardData?.active_customers_change_percent !== undefined && dashboardData?.active_customers_change_percent !== 0 && (
                    <span className={`ml-1 ${
                      dashboardData.active_customers_change_percent > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      ({dashboardData.active_customers_change_percent > 0 ? '+' : ''}{dashboardData.active_customers_change_percent.toFixed(1)}% vs prev month)
                    </span>
                  )}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Customers</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboardData?.total_customers || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  All customers in database
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Customer Charts */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Top 10 Customers</CardTitle>
                <CardDescription>
                  By fiscal YTD sales (since March)
                  {customerRiskData && (
                    <span className="text-xs text-blue-600 block mt-1">
                      Risk analysis: {customerRiskData.customers?.length || 0} customers analyzed, 
                      {customerRiskData.customers?.filter(c => c.risk_level !== 'none')?.length || 0} at risk
                    </span>
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {dashboardData?.top_customers?.map((customer) => {
                    const riskData = getCustomerRisk(customer.name)
                    const riskLevel = riskData?.risk_level || 'none'
                    const riskFactors = riskData?.risk_factors || []
                    
                    return (
                      <div key={customer.rank} className="flex items-center relative group">
                        <div className="w-8 text-sm font-medium text-muted-foreground">
                          {customer.rank}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm font-medium truncate ${
                            riskLevel === 'high' ? 'text-red-600' :
                            riskLevel === 'medium' ? 'text-orange-600' :
                            riskLevel === 'low' ? 'text-yellow-600' :
                            'text-gray-900'
                          }`}>
                            {customer.name}
                            {riskLevel !== 'none' && (
                              <span className={`ml-1 inline-block w-2 h-2 rounded-full ${
                                riskLevel === 'high' ? 'bg-red-500' :
                                riskLevel === 'medium' ? 'bg-orange-500' :
                                'bg-yellow-500'
                              }`} />
                            )}
                          </p>
                          <p className="text-xs text-gray-500">
                            {customer.invoice_count} invoices
                            {riskData && riskData.days_since_last_invoice > 7 && (
                              <span className="ml-1 text-orange-600">
                                • {riskData.days_since_last_invoice}d ago
                              </span>
                            )}
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
                        
                        {/* Risk Tooltip */}
                        {riskLevel !== 'none' && riskFactors.length > 0 && (
                          <div className="absolute left-0 top-full mt-1 w-80 bg-white border border-gray-200 rounded-lg shadow-lg p-3 z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                            <div className="flex items-center mb-2">
                              <div className={`w-3 h-3 rounded-full mr-2 ${
                                riskLevel === 'high' ? 'bg-red-500' :
                                riskLevel === 'medium' ? 'bg-orange-500' :
                                'bg-yellow-500'
                              }`} />
                              <span className={`font-semibold text-sm ${
                                riskLevel === 'high' ? 'text-red-700' :
                                riskLevel === 'medium' ? 'text-orange-700' :
                                'text-yellow-700'
                              }`}>
                                {riskLevel.toUpperCase()} RISK
                              </span>
                            </div>
                            <div className="space-y-1">
                              {riskFactors.map((factor, index) => (
                                <p key={index} className="text-xs text-gray-600">
                                  • {factor}
                                </p>
                              ))}
                            </div>
                            {riskData && (
                              <div className="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-500">
                                <p>Recent 30d: {formatCurrency(riskData.recent_30_sales)}</p>
                                <p>Expected: {formatCurrency(riskData.expected_monthly_sales)}</p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  }) || (
                    <p className="text-sm text-gray-500">No customer data available</p>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle>Active Customers Over Time</CardTitle>
                    <CardDescription>
                      Number of customers with invoices each month
                    </CardDescription>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => downloadActiveCustomers()}
                    className="h-8 px-2"
                    title="Download active customers list"
                  >
                    <Download className="h-3 w-3 mr-1" />
                    CSV
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={350}>
                  <LineChart data={dashboardData?.monthly_active_customers?.slice(0, -1) || []} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                            <p className="font-semibold mb-1">{label}</p>
                            <p className="text-blue-600">
                              {payload[0].value} active customers
                            </p>
                          </div>
                        )
                      }
                      return null
                    }} />
                    <Line 
                      type="monotone" 
                      dataKey="customers" 
                      stroke="#3b82f6" 
                      strokeWidth={2}
                      name="Active Customers"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

    {/* Work Orders Tab */}
    <TabsContent value="workorders" className="space-y-4">
          {/* Temporary: Show all work order types */}
          <WorkOrderTypes />

          {/* Invoice Delay Analysis Report */}
          {invoiceDelayLoading ? (
            <Card>
              <CardContent className="flex items-center justify-center h-64">
                <LoadingSpinner />
              </CardContent>
            </Card>
          ) : invoiceDelayData ? (
            <div className="space-y-6">
              {/* Summary Card */}
              <Card>
                <CardHeader>
                  <CardTitle>Invoice Delay Analysis - All Departments</CardTitle>
                  <CardDescription>Breakdown of completed work orders awaiting invoice</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Total WOs</p>
                      <p className="text-2xl font-bold">{invoiceDelayData.totals.count}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Total Value</p>
                      <p className="text-2xl font-bold">{formatCurrency(invoiceDelayData.totals.value)}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Avg Days</p>
                      <p className="text-2xl font-bold text-red-600">{invoiceDelayData.totals.avg_days} days</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Within Target (≤3 days)</p>
                      <p className="text-2xl font-bold text-green-600">{invoiceDelayData.totals.within_target_pct}%</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Department Breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle>Department Performance</CardTitle>
                  <CardDescription>Invoice delay breakdown by department type</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Department</TableHead>
                          <TableHead className="text-right">Count</TableHead>
                          <TableHead className="text-right">Value</TableHead>
                          <TableHead className="text-right">Avg Days</TableHead>
                          <TableHead className="text-center">≤3 days</TableHead>
                          <TableHead className="text-center">&gt;3 days</TableHead>
                          <TableHead className="text-center">&gt;7 days</TableHead>
                          <TableHead className="text-center">&gt;14 days</TableHead>
                          <TableHead className="text-center">&gt;30 days</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {invoiceDelayData.departments.map((dept) => (
                          <TableRow key={dept.department}>
                            <TableCell className="font-medium">{dept.department}</TableCell>
                            <TableCell className="text-right">{dept.count}</TableCell>
                            <TableCell className="text-right">{formatCurrency(dept.value)}</TableCell>
                            <TableCell className={`text-right font-bold ${dept.avg_days > 3 ? 'text-red-600' : 'text-green-600'}`}>
                              {dept.avg_days}
                            </TableCell>
                            <TableCell className="text-center">
                              <Badge variant={dept.within_target_pct > 50 ? "success" : "secondary"}>
                                {dept.within_target} ({dept.within_target_pct}%)
                              </Badge>
                            </TableCell>
                            <TableCell className="text-center">
                              <Badge variant={dept.over_three_pct > 50 ? "warning" : "secondary"}>
                                {dept.over_three} ({dept.over_three_pct}%)
                              </Badge>
                            </TableCell>
                            <TableCell className="text-center">
                              <Badge variant={dept.over_seven_pct > 25 ? "destructive" : "secondary"}>
                                {dept.over_seven} ({dept.over_seven_pct}%)
                              </Badge>
                            </TableCell>
                            <TableCell className="text-center">
                              {dept.over_fourteen} ({dept.over_fourteen_pct}%)
                            </TableCell>
                            <TableCell className="text-center">
                              {dept.over_thirty} ({dept.over_thirty_pct}%)
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>

              <div className="grid gap-4 md:grid-cols-2">
                {/* Delay Distribution Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle>Delay Distribution</CardTitle>
                    <CardDescription>Percentage of work orders by delay period</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={[
                          { range: '≤3 days', percentage: invoiceDelayData.totals.within_target_pct },
                          { range: '4-7 days', percentage: invoiceDelayData.totals.over_three_pct - invoiceDelayData.totals.over_seven_pct },
                          { range: '8-14 days', percentage: invoiceDelayData.totals.over_seven_pct - invoiceDelayData.totals.over_fourteen_pct },
                          { range: '15-30 days', percentage: invoiceDelayData.totals.over_fourteen_pct - invoiceDelayData.totals.over_thirty_pct },
                          { range: '&gt;30 days', percentage: invoiceDelayData.totals.over_thirty_pct }
                        ]}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="range" />
                          <YAxis tickFormatter={(value) => `${value}%`} />
                          <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
                          <Bar dataKey="percentage" fill="#8884d8">
                            <Cell fill="#22c55e" />
                            <Cell fill="#fbbf24" />
                            <Cell fill="#f97316" />
                            <Cell fill="#ef4444" />
                            <Cell fill="#991b1b" />
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Worst Offenders */}
                <Card>
                  <CardHeader>
                    <CardTitle>Longest Waiting Work Orders</CardTitle>
                    <CardDescription>Top 10 work orders with longest delays</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {invoiceDelayData.worst_offenders.slice(0, 10).map((wo) => (
                        <div key={wo.wo_number} className={`p-2 rounded-lg border ${wo.days_waiting > 30 ? 'bg-red-50 border-red-200' : 'bg-gray-50'}`}>
                          <div className="flex justify-between items-start">
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <span className="font-medium">{wo.wo_number}</span>
                                <Badge variant="outline" className="text-xs">{wo.type}</Badge>
                              </div>
                              <p className="text-sm text-muted-foreground">{wo.customer}</p>
                              <p className="text-xs text-muted-foreground">Completed: {wo.completed_date}</p>
                            </div>
                            <div className="text-right">
                              <Badge variant={wo.days_waiting > 30 ? "destructive" : wo.days_waiting > 7 ? "warning" : "secondary"}>
                                {wo.days_waiting} days
                              </Badge>
                              <p className="text-sm font-medium mt-1">{formatCurrency(wo.value)}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          ) : null}
    </TabsContent>

        {/* AI Forecasts Tab */}
        <TabsContent value="forecast" className="space-y-4">
          {/* Sales Forecast Card */}
          {forecastData && (
            <Card className="border-2 border-blue-100 bg-blue-50/20">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-xl">{getMonthName(forecastData.current_month?.month)} Sales Forecast</CardTitle>
                <CardDescription>
                  AI-powered prediction based on historical patterns
                  {forecastLastUpdated && (
                    <span className="text-xs text-muted-foreground block mt-1">
                      Last updated: {forecastLastUpdated.toLocaleTimeString()}
                    </span>
                  )}
                </CardDescription>
              </div>
              <div className="text-right space-y-2">
                <div>
                  <p className="text-sm text-muted-foreground">Confidence Level</p>
                  <p className="text-lg font-semibold">{forecastData.forecast?.confidence_level || '68%'}</p>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={fetchForecastData}
                  className="h-8 px-2"
                  title="Refresh forecast"
                >
                  <RefreshCw className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-2">
              {/* Forecast Numbers */}
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Projected Month End Total</p>
                  <p className="text-3xl font-bold text-blue-600">
                    {formatCurrency(forecastData.forecast?.projected_total || 0)}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Range: {formatCurrency(forecastData.forecast?.forecast_low || 0)} - {formatCurrency(forecastData.forecast?.forecast_high || 0)}
                  </p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">MTD Sales</p>
                    <p className="text-xl font-semibold">{formatCurrency(forecastData.current_month?.mtd_sales || 0)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Days Remaining</p>
                    <p className="text-xl font-semibold">{forecastData.current_month?.days_remaining || 0}</p>
                  </div>
                </div>
                
                <div>
                  <p className="text-sm text-muted-foreground">Daily Run Rate Needed</p>
                  <p className="text-xl font-semibold">{formatCurrency(forecastData.analysis?.daily_run_rate_needed || 0)}/day</p>
                </div>
              </div>
              
              {/* Key Factors */}
              <div>
                <h4 className="font-semibold mb-3">Key Factors</h4>
                <div className="space-y-2">
                  {forecastData.factors?.map((factor, index) => (
                    <div key={index} className="flex items-start space-x-2">
                      <div className={`mt-1 w-2 h-2 rounded-full ${
                        factor.impact === 'positive' ? 'bg-green-500' : 
                        factor.impact === 'negative' ? 'bg-red-500' : 
                        'bg-gray-400'
                      }`} />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{factor.factor}</p>
                        <p className="text-xs text-muted-foreground">{factor.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Progress Indicator */}
                <div className="mt-4">
                  <div className="flex justify-between text-xs text-muted-foreground mb-1">
                    <span>Month Progress</span>
                    <span>{forecastData.current_month?.month_progress_pct || 0}%</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-500 transition-all duration-500"
                      style={{ width: `${forecastData.current_month?.month_progress_pct || 0}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>Sales vs Forecast</span>
                    <span>{forecastData.analysis?.actual_pct_of_forecast || 0}%</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-500 ${
                        (forecastData.analysis?.actual_pct_of_forecast || 0) > 100 ? 'bg-green-500' : 'bg-blue-500'
                      }`}
                      style={{ width: `${Math.min(100, forecastData.analysis?.actual_pct_of_forecast || 0)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
            </Card>
          )}

          {/* AI Predictions Section */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Brain className="h-5 w-5 text-purple-600" />
              AI-Powered Predictions
            </h3>
            
            <div className="grid gap-4 md:grid-cols-3">
              {/* Work Order Prediction Card */}
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <Wrench className="h-5 w-5 text-orange-600" />
                      <CardTitle className="text-sm font-medium">Work Order Forecast</CardTitle>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => fetchWorkOrderPrediction(true)}
                      disabled={workOrderPredictionLoading}
                      className="h-7 px-2"
                    >
                      <RefreshCw className={`h-3 w-3 ${workOrderPredictionLoading ? 'animate-spin' : ''}`} />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {workOrderPredictionLoading ? (
                    <div className="flex items-center justify-center h-32">
                      <LoadingSpinner />
                    </div>
                  ) : workOrderPrediction ? (
                    workOrderPrediction.prediction?.error ? (
                      <div className="space-y-2">
                        <p className="text-sm text-red-600 font-medium">Error generating prediction</p>
                        <p className="text-xs text-muted-foreground">{workOrderPrediction.prediction.error}</p>
                        {workOrderPrediction.prediction.raw_content && (
                          <details className="text-xs">
                            <summary className="cursor-pointer text-blue-600">Show details</summary>
                            <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto max-h-32">
                              {workOrderPrediction.prediction.raw_content}
                            </pre>
                          </details>
                        )}
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div>
                          <p className="text-xs text-muted-foreground">Expected Next Month</p>
                          <p className="text-xl font-bold">{workOrderPrediction.prediction?.expected_count || 'N/A'}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Value Range</p>
                          <p className="text-sm font-medium">{formatCurrency(workOrderPrediction.prediction?.value_low || 0)} - {formatCurrency(workOrderPrediction.prediction?.value_high || 0)}</p>
                        </div>
                        {workOrderPrediction.prediction?.distribution && (
                          <div className="text-xs space-y-1">
                            <p className="font-medium">Distribution:</p>
                            <p>Service: {workOrderPrediction.prediction.distribution.service}</p>
                            <p>Rental: {workOrderPrediction.prediction.distribution.rental}</p>
                            <p>Internal: {workOrderPrediction.prediction.distribution.internal}</p>
                          </div>
                        )}
                        <div className="pt-2 border-t">
                          <p className="text-xs text-muted-foreground">Confidence: {workOrderPrediction.prediction?.confidence || '0'}%</p>
                          {workOrderPrediction.generated_at && (
                            <p className="text-xs text-muted-foreground mt-1">
                              Updated: {new Date(workOrderPrediction.generated_at).toLocaleTimeString()}
                            </p>
                          )}
                        </div>
                        {(workOrderPrediction.prediction?.factors || workOrderPrediction.prediction?.recommendations) && (
                          <details className="text-xs pt-2 border-t">
                            <summary className="cursor-pointer text-blue-600 font-medium">View Insights</summary>
                            <div className="mt-2 space-y-2">
                              {workOrderPrediction.prediction.factors && (
                                <div>
                                  <p className="font-medium">Key Factors:</p>
                                  <ul className="list-disc list-inside space-y-1 text-gray-600">
                                    {workOrderPrediction.prediction.factors.map((factor, i) => (
                                      <li key={i}>{factor}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {workOrderPrediction.prediction.recommendations && (
                                <div>
                                  <p className="font-medium">Recommendation:</p>
                                  <p className="text-gray-600">{workOrderPrediction.prediction.recommendations}</p>
                                </div>
                              )}
                            </div>
                          </details>
                        )}
                      </div>
                    )
                  ) : (
                    <div className="flex flex-col items-center justify-center h-32 text-center">
                      <p className="text-sm text-muted-foreground mb-3">Generate AI prediction</p>
                      <Button size="sm" onClick={() => fetchWorkOrderPrediction()}>
                        Generate Forecast
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Customer Churn Prediction Card */}
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-red-600" />
                      <CardTitle className="text-sm font-medium">Customer Churn Risk</CardTitle>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => fetchCustomerChurnPrediction(true)}
                      disabled={customerChurnLoading}
                      className="h-7 px-2"
                    >
                      <RefreshCw className={`h-3 w-3 ${customerChurnLoading ? 'animate-spin' : ''}`} />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {customerChurnLoading ? (
                    <div className="flex items-center justify-center h-32">
                      <LoadingSpinner />
                    </div>
                  ) : customerChurnPrediction ? (
                    customerChurnPrediction.prediction?.error ? (
                      <div className="space-y-2">
                        <p className="text-sm text-red-600 font-medium">Error analyzing risk</p>
                        <p className="text-xs text-muted-foreground">{customerChurnPrediction.prediction.error}</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div>
                          <p className="text-xs text-muted-foreground">At-Risk Customers</p>
                          <p className="text-xl font-bold text-red-600">
                            {customerChurnPrediction.prediction?.at_risk_count || 0}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Overall Churn Risk</p>
                          <p className="text-sm font-medium">{customerChurnPrediction.prediction?.overall_risk || '0'}%</p>
                        </div>
                        <div className="pt-2 border-t">
                          <p className="text-xs text-muted-foreground">
                            Analyzed: {customerChurnPrediction.customers_analyzed || 0} customers
                          </p>
                          {customerChurnPrediction.generated_at && (
                            <p className="text-xs text-muted-foreground mt-1">
                              Updated: {new Date(customerChurnPrediction.generated_at).toLocaleTimeString()}
                            </p>
                          )}
                        </div>
                        {(customerChurnPrediction.prediction?.at_risk_customers || customerChurnPrediction.prediction?.patterns) && (
                          <details className="text-xs pt-2 border-t">
                            <summary className="cursor-pointer text-blue-600 font-medium">View Details</summary>
                            <div className="mt-2 space-y-2">
                              {customerChurnPrediction.prediction.at_risk_customers && (
                                <div>
                                  <p className="font-medium">At-Risk Customers:</p>
                                  <div className="space-y-2 mt-1">
                                    {customerChurnPrediction.prediction.at_risk_customers.slice(0, 5).map((customer, i) => (
                                      <div key={i} className="bg-red-50 p-2 rounded">
                                        <p className="font-medium text-red-800">{customer.name}</p>
                                        <p className="text-red-600">Risk: {customer.risk_level}</p>
                                        {customer.warning_signs && (
                                          <ul className="list-disc list-inside text-gray-600 mt-1">
                                            {customer.warning_signs.map((sign, j) => (
                                              <li key={j} className="text-xs">{sign}</li>
                                            ))}
                                          </ul>
                                        )}
                                        {customer.action && (
                                          <p className="text-xs font-medium text-blue-600 mt-1">Action: {customer.action}</p>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {customerChurnPrediction.prediction.patterns && (
                                <div>
                                  <p className="font-medium">Patterns:</p>
                                  <ul className="list-disc list-inside space-y-1 text-gray-600">
                                    {customerChurnPrediction.prediction.patterns.map((pattern, i) => (
                                      <li key={i}>{pattern}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          </details>
                        )}
                      </div>
                    )
                  ) : (
                    <div className="flex flex-col items-center justify-center h-32 text-center">
                      <p className="text-sm text-muted-foreground mb-3">Analyze customer risk</p>
                      <Button size="sm" onClick={() => fetchCustomerChurnPrediction()}>
                        Analyze Risk
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Parts Demand Prediction Card */}
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <Package className="h-5 w-5 text-blue-600" />
                      <CardTitle className="text-sm font-medium">Parts Demand Forecast</CardTitle>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => fetchPartsDemandPrediction(true)}
                      disabled={partsDemandLoading}
                      className="h-7 px-2"
                    >
                      <RefreshCw className={`h-3 w-3 ${partsDemandLoading ? 'animate-spin' : ''}`} />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {partsDemandLoading ? (
                    <div className="flex items-center justify-center h-32">
                      <LoadingSpinner />
                    </div>
                  ) : partsDemandPrediction ? (
                    partsDemandPrediction.prediction?.error ? (
                      <div className="space-y-2">
                        <p className="text-sm text-red-600 font-medium">Error generating forecast</p>
                        <p className="text-xs text-muted-foreground">{partsDemandPrediction.prediction.error}</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div>
                          <p className="text-xs text-muted-foreground">High Demand Parts</p>
                          <p className="text-xl font-bold">{partsDemandPrediction.prediction?.high_demand_count || 0}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Stockout Risk</p>
                          <p className="text-sm font-medium">{partsDemandPrediction.prediction?.stockout_risk_count || 0} parts</p>
                        </div>
                        <div className="pt-2 border-t">
                          <p className="text-xs text-muted-foreground">
                            Analyzed: {partsDemandPrediction.parts_analyzed || 0} parts
                          </p>
                          {partsDemandPrediction.generated_at && (
                            <p className="text-xs text-muted-foreground mt-1">
                              Updated: {new Date(partsDemandPrediction.generated_at).toLocaleTimeString()}
                            </p>
                          )}
                        </div>
                        {(partsDemandPrediction.prediction?.top_demand_parts || partsDemandPrediction.prediction?.stockout_risks || partsDemandPrediction.prediction?.patterns) && (
                          <details className="text-xs pt-2 border-t">
                            <summary className="cursor-pointer text-blue-600 font-medium">View Details</summary>
                            <div className="mt-2 space-y-2">
                              {partsDemandPrediction.prediction.top_demand_parts && (
                                <div>
                                  <p className="font-medium">High Demand Parts:</p>
                                  <div className="space-y-1 mt-1">
                                    {partsDemandPrediction.prediction.top_demand_parts.slice(0, 5).map((part, i) => (
                                      <div key={i} className="bg-blue-50 p-2 rounded">
                                        <p className="font-medium">{part.part_no} - {part.description}</p>
                                        <p className="text-gray-600">Predicted: {part.predicted_demand} units</p>
                                        <p className="text-gray-600">Reorder: {part.recommended_reorder} units</p>
                                        <p className="text-xs text-gray-500">Confidence: {part.confidence}%</p>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {partsDemandPrediction.prediction.stockout_risks && (
                                <div>
                                  <p className="font-medium text-red-600">Stockout Risks:</p>
                                  <ul className="list-disc list-inside space-y-1 text-red-600">
                                    {partsDemandPrediction.prediction.stockout_risks.map((part, i) => (
                                      <li key={i}>{part}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {partsDemandPrediction.prediction.patterns && (
                                <div>
                                  <p className="font-medium">Patterns:</p>
                                  <ul className="list-disc list-inside space-y-1 text-gray-600">
                                    {partsDemandPrediction.prediction.patterns.map((pattern, i) => (
                                      <li key={i}>{pattern}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          </details>
                        )}
                      </div>
                    )
                  ) : (
                    <div className="flex flex-col items-center justify-center h-32 text-center">
                      <p className="text-sm text-muted-foreground mb-3">Forecast parts demand</p>
                      <Button size="sm" onClick={() => fetchPartsDemandPrediction()}>
                        Generate Forecast
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
  </Tabs>
    </div>
  )
}

export default Dashboard
