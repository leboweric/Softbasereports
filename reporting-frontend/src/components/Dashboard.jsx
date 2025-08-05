import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
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
  ReferenceLine
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

  useEffect(() => {
    fetchDashboardData()
    
    // Set up auto-refresh every 5 minutes for real-time updates
    const interval = setInterval(() => {
      fetchForecastData() // Update forecast more frequently for real-time adjustments
    }, 5 * 60 * 1000) // 5 minutes
    
    return () => clearInterval(interval)
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
      <Tabs defaultValue="sales" className="space-y-4">
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
              <BarChart data={dashboardData?.monthly_sales || []} margin={{ top: 40, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                <Tooltip content={({ active, payload, label }) => {
                  if (active && payload && payload.length && dashboardData?.monthly_sales) {
                    const data = dashboardData.monthly_sales
                    const currentIndex = data.findIndex(item => item.month === label)
                    const currentValue = payload[0].value
                    const previousValue = currentIndex > 0 ? data[currentIndex - 1].amount : null
                    
                    return (
                      <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                        <p className="font-semibold mb-1">{label}</p>
                        <p className="text-green-600">
                          {formatCurrency(currentValue)}
                          {formatPercentage(calculatePercentageChange(currentValue, previousValue))}
                        </p>
                      </div>
                    )
                  }
                  return null
                }} />
                <Bar dataKey="amount" fill="#8884d8" shape={<CustomBar />} />
                {dashboardData?.monthly_sales && dashboardData.monthly_sales.length > 0 && (() => {
                  // Only calculate average for complete months (exclude current month - August)
                  const completeMonths = dashboardData.monthly_sales.slice(0, -1)
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
                <CardTitle>Monthly Sales (No Equipment)</CardTitle>
                <CardDescription>
                  Sales excluding new equipment
                </CardDescription>
              </div>
              {dashboardData?.monthly_sales_no_equipment && dashboardData.monthly_sales_no_equipment.length > 0 && (() => {
                const completeMonths = dashboardData.monthly_sales_no_equipment.slice(0, -1)
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
              <BarChart data={dashboardData?.monthly_sales_no_equipment || []} margin={{ top: 40, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="amount" fill="#10b981" shape={<CustomBarNoEquipment />} />
                {dashboardData?.monthly_sales_no_equipment && dashboardData.monthly_sales_no_equipment.length > 0 && (() => {
                  // Only calculate average for complete months (exclude current month - August)
                  const completeMonths = dashboardData.monthly_sales_no_equipment.slice(0, -1)
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
          </div>

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
          {/* Awaiting Invoice Alert */}
          {dashboardData?.awaiting_invoice_count > 0 && (
            <Card className={`border-2 ${dashboardData.awaiting_invoice_over_three > 0 ? 'border-orange-400 bg-orange-50' : 'border-yellow-400 bg-yellow-50'}`}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-lg">Service Work Orders Awaiting Invoice</CardTitle>
                    {dashboardData.awaiting_invoice_over_three > 0 && (
                      <AlertTriangle className="h-5 w-5 text-orange-600" />
                    )}
                  </div>
                  <Badge variant={dashboardData.awaiting_invoice_over_three > 0 ? "destructive" : "warning"}>
                    {dashboardData.awaiting_invoice_count} work orders
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Total Value</p>
                    <p className="font-semibold text-lg">{formatCurrency(dashboardData.awaiting_invoice_value)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Avg Days Waiting</p>
                    <p className="font-semibold text-lg flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {dashboardData.awaiting_invoice_avg_days.toFixed(1)} days
                    </p>
                  </div>
                </div>
                {dashboardData.awaiting_invoice_over_three > 0 && (
                  <div className="pt-2 border-t">
                    <div className="flex items-center gap-2 text-sm">
                      <AlertTriangle className="h-4 w-4 text-orange-600" />
                      <span className="text-orange-700">
                        <strong>{dashboardData.awaiting_invoice_over_three}</strong> orders waiting >3 days
                        {dashboardData.awaiting_invoice_over_five > 0 && (
                          <span> ({dashboardData.awaiting_invoice_over_five} over 5 days{dashboardData.awaiting_invoice_over_seven > 0 && `, ${dashboardData.awaiting_invoice_over_seven} over 7 days`})</span>
                        )}
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Work Order Metrics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Open Work Orders</CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${
                  dashboardData?.open_work_orders_change > 0 ? 'text-red-600' :
                  dashboardData?.open_work_orders_change < 0 ? 'text-green-600' :
                  'text-gray-900'
                }`}>
                  {formatCurrency(dashboardData?.open_work_orders_value || 0)}
                  {dashboardData?.open_work_orders_change !== undefined && dashboardData?.open_work_orders_change !== 0 && (
                    <span className={`ml-2 text-sm font-normal ${
                      dashboardData.open_work_orders_change > 0 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {dashboardData.open_work_orders_change > 0 ? '+' : ''}{formatCurrency(dashboardData.open_work_orders_change)}
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  Value of active work orders
                  {dashboardData?.open_work_orders_change_percent !== undefined && dashboardData?.open_work_orders_change_percent !== 0 && (
                    <span className={`ml-1 ${
                      dashboardData.open_work_orders_change_percent > 0 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      ({dashboardData.open_work_orders_change_percent > 0 ? '+' : ''}{dashboardData.open_work_orders_change_percent.toFixed(1)}% vs prev month end)
                    </span>
                  )}
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
                  Value of uninvoiced work orders
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Work Orders Charts */}
          <div className="grid gap-4 md:grid-cols-1">
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle>Average Days Waiting for Invoice</CardTitle>
                    <CardDescription>
                      Service work orders: Average days between completion and invoice since March 2025
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Target</p>
                    <p className="text-lg font-semibold text-green-600">3 days</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={350}>
                  <LineChart data={dashboardData?.monthly_invoice_delays || []} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis domain={[0, 'dataMax + 5']} />
                    <Tooltip content={({ active, payload, label }) => {
                      if (active && payload && payload.length && dashboardData?.monthly_invoice_delays) {
                        const data = dashboardData.monthly_invoice_delays.find(item => item.month === label);
                        return (
                          <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                            <p className="font-semibold mb-2">{label}</p>
                            <div className="space-y-1">
                              <p className={`font-bold ${payload[0].value > 3 ? 'text-red-600' : 'text-green-600'}`}>
                                Average: {payload[0].value} days
                              </p>
                              {data && (
                                <>
                                  <p className="text-sm text-gray-600">
                                    Completed WOs: {data.completed_count}
                                  </p>
                                  <p className="text-sm text-gray-600">
                                    Over 3 days: {data.over_three_days} ({Math.round((data.over_three_days / data.completed_count) * 100)}%)
                                  </p>
                                  <p className="text-sm text-gray-600">
                                    Over 7 days: {data.over_seven_days} ({Math.round((data.over_seven_days / data.completed_count) * 100)}%)
                                  </p>
                                </>
                              )}
                            </div>
                          </div>
                        )
                      }
                      return null
                    }} />
                    {/* Target line at 3 days */}
                    <ReferenceLine 
                      y={3} 
                      stroke="#22c55e" 
                      strokeDasharray="5 5"
                      strokeWidth={2}
                      label={{ value: "Target: 3 days", position: "left", style: { fill: '#22c55e', fontWeight: 'bold' } }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="avg_days" 
                      stroke="#f97316" 
                      strokeWidth={3}
                      name="Average Days"
                      dot={(props) => {
                        const { cx, cy, payload } = props;
                        const isAboveTarget = payload.avg_days > 3;
                        
                        return (
                          <g>
                            <circle 
                              cx={cx} 
                              cy={cy} 
                              r={6} 
                              fill={isAboveTarget ? "#dc2626" : "#22c55e"} 
                              stroke="#fff"
                              strokeWidth={2}
                            />
                            {/* Show warning icon if way above target */}
                            {payload.avg_days > 7 && (
                              <>
                                <rect 
                                  x={cx - 15} 
                                  y={cy - 30} 
                                  width={30} 
                                  height={20} 
                                  fill="#dc2626" 
                                  rx={3}
                                />
                                <text 
                                  x={cx} 
                                  y={cy - 16} 
                                  textAnchor="middle" 
                                  fill="white" 
                                  fontSize="12" 
                                  fontWeight="bold"
                                >
                                  {payload.avg_days}d
                                </text>
                              </>
                            )}
                          </g>
                        );
                      }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
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
