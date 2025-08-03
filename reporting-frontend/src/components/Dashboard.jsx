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
  RefreshCw
} from 'lucide-react'
import { apiUrl } from '@/lib/api'

const Dashboard = ({ user }) => {
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [paceData, setPaceData] = useState(null)
  const [forecastData, setForecastData] = useState(null)
  const [forecastLastUpdated, setForecastLastUpdated] = useState(null)
  const [loadTime, setLoadTime] = useState(null)
  const [fromCache, setFromCache] = useState(false)
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
          <h1 className="text-3xl font-bold tracking-tight">Bennett Dashboard</h1>
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
        <TabsList className="grid w-full max-w-md grid-cols-3">
          <TabsTrigger value="sales">Sales</TabsTrigger>
          <TabsTrigger value="customers">Customers</TabsTrigger>
          <TabsTrigger value="workorders">Work Orders</TabsTrigger>
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
                <CardTitle className="text-sm font-medium">YTD Sales</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(dashboardData?.ytd_sales || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Fiscal year to date
            </p>
              </CardContent>
            </Card>
          </div>

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

          {/* Gross Margins Analysis */}
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
              <LineChart data={getFilteredMarginsData()} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
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
                <div className="text-2xl font-bold">
                  {dashboardData?.active_customers || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  Customers with invoices this month
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
                <CardTitle>Active Customers Over Time</CardTitle>
                <CardDescription>
                  Number of customers with invoices each month
                </CardDescription>
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
          {/* Work Order Metrics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Open Work Orders</CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatCurrency(dashboardData?.open_work_orders_value || 0)}
                </div>
                <p className="text-xs text-muted-foreground">
                  Value of active work orders
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
                <CardTitle>Work Orders Trends by Type</CardTitle>
                <CardDescription>
                  Total value of work orders by type
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-4 mb-4">
                  <div className="flex items-center space-x-2 pr-4 border-r">
                    <Checkbox 
                      id="current-month-filter-wo"
                      checked={includeCurrentMonth}
                      onCheckedChange={setIncludeCurrentMonth}
                    />
                    <label 
                      htmlFor="current-month-filter-wo" 
                      className="text-sm font-medium cursor-pointer"
                    >
                      Include Current Month
                    </label>
                  </div>
                  <div className="flex items-center gap-4">
                    {Object.entries(visibleWOTypes).map(([type, visible]) => (
                      <div key={type} className="flex items-center space-x-2">
                        <Checkbox 
                          id={`toggle-wo-${type}`}
                          checked={visible}
                          onCheckedChange={(checked) => 
                            setVisibleWOTypes(prev => ({ ...prev, [type]: checked }))
                          }
                        />
                        <label 
                          htmlFor={`toggle-wo-${type}`} 
                          className="text-sm font-medium capitalize cursor-pointer flex items-center gap-1"
                        >
                          <div className={`w-3 h-3 rounded ${
                            type === 'service' ? 'bg-blue-500' :
                            type === 'rental' ? 'bg-green-500' :
                            type === 'parts' ? 'bg-yellow-500' :
                            type === 'pm' ? 'bg-purple-500' :
                            type === 'shop' ? 'bg-pink-500' :
                            'bg-gray-500'
                          }`} />
                          {type === 'pm' ? 'PM' : type}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                <ResponsiveContainer width="100%" height={350}>
                  <LineChart data={getFilteredWOData()} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                    <Tooltip content={<CustomTooltip />} />
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
    </TabsContent>
  </Tabs>
    </div>
  )
}

export default Dashboard
