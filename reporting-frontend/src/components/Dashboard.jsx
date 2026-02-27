import React, { useState, useEffect, useRef, useMemo } from 'react'
import VitalExecutiveDashboard from './vital/VitalExecutiveDashboard'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tooltip as UITooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
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
  HelpCircle,
  Target,
  Activity,
  Gauge,
  ChevronRight,
  AlertCircle,
  CheckCircle,
  ArrowRight,
  Info
} from 'lucide-react'
import { apiUrl } from '@/lib/api'
import { MetricTooltip } from '@/components/ui/metric-tooltip'
import { IPS_METRICS } from '@/config/ipsMetricDefinitions'
import { MethodologyPanel } from '@/components/ui/methodology-panel'
import { SALES_DASHBOARD_METHODOLOGY } from '@/config/ipsPageMethodology'
import WorkOrderTypes from './WorkOrderTypes'
import ForecastAccuracy from './ForecastAccuracy'
import CustomerDetailModal from './CustomerDetailModal'

// Utility function to calculate linear regression trendline
const calculateLinearTrend = (data, xKey, yKey, excludeCurrentMonth = true, fiscalYearStartMonth = null) => {
  if (!data || data.length === 0) return []

  // Ensure all data has a numeric value for the yKey, otherwise default to 0
  const cleanedData = data.map(item => ({
    ...item,
    [yKey]: parseFloat(item[yKey]) || 0
  }))

  // Determine the start index for the trend line
  let trendStartIndex
  if (fiscalYearStartMonth) {
    // Find the index of the fiscal year start month
    // Data items have month_number (1-12) and year fields
    const now = new Date()
    const currentMonth = now.getMonth() + 1
    const fyStartYear = currentMonth >= fiscalYearStartMonth ? now.getFullYear() : now.getFullYear() - 1
    
    trendStartIndex = cleanedData.findIndex(item => {
      if (item.month_number && item.year) {
        return item.year > fyStartYear || (item.year === fyStartYear && item.month_number >= fiscalYearStartMonth)
      }
      // Fallback: parse month string like "Nov '25"
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
      const monthStr = item[xKey]
      if (!monthStr) return false
      const monthAbbr = monthStr.split(' ')[0].replace("'", '')
      const parsedMonth = monthNames.indexOf(monthAbbr) + 1
      const yearMatch = monthStr.match(/'(\d{2})/)
      const parsedYear = yearMatch ? 2000 + parseInt(yearMatch[1]) : null
      if (parsedMonth && parsedYear) {
        return parsedYear > fyStartYear || (parsedYear === fyStartYear && parsedMonth >= fiscalYearStartMonth)
      }
      return false
    })
    
    // If fiscal year start not found in data, fall back to first month with data
    if (trendStartIndex === -1) {
      trendStartIndex = cleanedData.findIndex(item => item[yKey] > 0)
    }
  } else {
    // Default: start from the first month with actual data
    trendStartIndex = cleanedData.findIndex(item => item[yKey] > 0)
  }

  if (trendStartIndex === -1) {
    return cleanedData.map(item => ({ ...item, trendValue: null }))
  }

  // Get data from the trend start point
  const dataFromStart = cleanedData.slice(trendStartIndex)

  let trendData = dataFromStart
  if (excludeCurrentMonth && dataFromStart.length > 1) {
    trendData = dataFromStart.slice(0, -1)
  }

  if (trendData.length < 2) {
    return cleanedData.map(item => ({ ...item, trendValue: null }))
  }

  const n = trendData.length
  const sumX = trendData.reduce((sum, _, index) => sum + index, 0)
  const sumY = trendData.reduce((sum, item) => sum + item[yKey], 0)
  const sumXY = trendData.reduce((sum, item, index) => sum + (index * item[yKey]), 0)
  const sumXX = trendData.reduce((sum, _, index) => sum + (index * index), 0)

  const denominator = (n * sumXX - sumX * sumX)
  if (denominator === 0) {
    return cleanedData.map(item => ({ ...item, trendValue: null }))
  }

  const slope = (n * sumXY - sumX * sumY) / denominator
  const intercept = (sumY - slope * sumX) / n

  return cleanedData.map((item, index) => {
    if (index < trendStartIndex) {
      return { ...item, trendValue: null }
    }
    const adjustedIndex = index - trendStartIndex
    return {
      ...item,
      trendValue: slope * adjustedIndex + intercept
    }
  })
}

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
  // Include current month toggle (defaults to OFF to exclude partial month)
  const [includeCurrentMonth, setIncludeCurrentMonth] = useState(false)

  const isMountedRef = useRef(true)

  // Helper to get current month string in the format used by backend (e.g. "Feb '26")
  const currentMonthStr = React.useMemo(() => {
    const now = new Date()
    return now.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }).replace(' ', " '")
  }, [])

  // Filter function that respects includeCurrentMonth toggle
  const filterCurrentMonth = React.useCallback((data) => {
    if (!data) return []
    if (includeCurrentMonth) return data
    return data.filter(item => item.month !== currentMonthStr)
  }, [includeCurrentMonth, currentMonthStr])

  // Backend already returns data in chronological order (ORDER BY year, month)
  const sortedMonthlySales = React.useMemo(() => {
    return filterCurrentMonth(dashboardData?.monthly_sales || []);
  }, [dashboardData, filterCurrentMonth]);

  const sortedMonthlySalesNoEquipment = React.useMemo(() => {
    return filterCurrentMonth(dashboardData?.monthly_sales_no_equipment || []);
  }, [dashboardData, filterCurrentMonth]);

  const sortedMonthlyQuotes = React.useMemo(() => {
    return filterCurrentMonth(dashboardData?.monthly_quotes || []);
  }, [dashboardData, filterCurrentMonth]);

  const sortedMonthlyEquipmentSales = React.useMemo(() => {
    return filterCurrentMonth(dashboardData?.monthly_equipment_sales || []);
  }, [dashboardData, filterCurrentMonth]);

  // Filter customers based on search
  const filteredCustomers = React.useMemo(() => {
    if (!dashboardData?.top_customers) return [];

    let filtered = dashboardData.top_customers;

    // Apply search filter
    if (customerSearchTerm) {
      filtered = filtered.filter(customer =>
        customer.name.toLowerCase().includes(customerSearchTerm.toLowerCase())
      );
    }

    return filtered;
  }, [dashboardData, customerSearchTerm]);

  useEffect(() => {
    // Skip API calls for VITAL Worklife users - they use different data sources
    if (user?.organization?.name === 'VITAL Worklife') {
      setLoading(false)
      return
    }

    fetchDashboardData()
    fetchExpenseData()

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
  }, [user])

  useEffect(() => {
    // Skip for VITAL users
    if (user?.organization?.name === 'VITAL Worklife') return
    
    // Fetch invoice delay analysis when Work Orders tab is selected
    if (activeTab === 'workorders' && !invoiceDelayData) {
      fetchInvoiceDelayAnalysis()
    }
  }, [activeTab, invoiceDelayData, user])

  const fetchDashboardData = async (forceRefresh = false) => {
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

        // Show dashboard immediately, then fetch supplementary data in background
        // This prevents the loading spinner from blocking while pace/forecast/risk load
        setLoading(false)
        
        // Fetch supplementary data in parallel (non-blocking)
        Promise.allSettled([
          fetchPaceData(),
          fetchForecastData(),
          fetchCustomerRiskData()
        ])
        return // Exit early since we already set loading to false
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
        setPaceData(null) // Let the UI handle the null state gracefully
      }
    } catch (error) {
      console.error('Error fetching pace data:', error)
      setPaceData(null) // Let the UI handle the null state gracefully
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

        // Only update state if component is still mounted
        if (isMountedRef.current) {
          setForecastData(data)
          setForecastLastUpdated(new Date())
        }
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
      return null
    }
    const risk = customerRiskData.customers.find(c => c.customer_name === customerName)
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

  const fetchExpenseData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/accounting'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setMonthlyExpenses(data.monthly_expenses || [])
      } else {
        console.error('Failed to fetch expense data')
      }
    } catch (error) {
      console.error('Error fetching expense data:', error)
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
    const { fill, x, y, width, height, payload, background } = props
    const currentMonth = new Date().getMonth() + 1
    const currentYear = new Date().getFullYear()

    // Check if this is the current month
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    const isCurrentMonth = payload &&
      payload.month === monthNames[currentMonth - 1] &&
      payload.year === currentYear &&
      paceData

    // Ghost bar for prior year - only for current month
    const priorYearAmount = payload?.prior_year_amount || 0
    const currentAmount = payload?.amount || 0
    let ghostBarHeight = 0
    let ghostBarY = y + height
    if (isCurrentMonth && priorYearAmount > 0 && currentAmount > 0 && height > 0) {
      const ratio = priorYearAmount / currentAmount
      ghostBarHeight = height * ratio
      ghostBarY = y + height - ghostBarHeight
    } else if (isCurrentMonth && priorYearAmount > 0 && background) {
      ghostBarHeight = Math.min(background.height * 0.3, 50)
      ghostBarY = background.y + background.height - ghostBarHeight
    }

    return (
      <g>
        {/* Ghost bar for prior year - current month only */}
        {isCurrentMonth && priorYearAmount > 0 && ghostBarHeight > 0 && (
          <rect
            x={x - 2}
            y={ghostBarY}
            width={width + 4}
            height={ghostBarHeight}
            fill={fill}
            fillOpacity={0.12}
            rx={4}
            ry={4}
            stroke={fill}
            strokeOpacity={0.25}
            strokeWidth={1}
            strokeDasharray="4 2"
          />
        )}
        {/* Current year bar */}
        <rect x={x} y={y} width={width} height={height} fill={fill} rx={4} ry={4} />
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

  // Custom bar shape for Aftermarket Sales chart
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
        <rect x={x} y={y} width={width} height={height} fill={fill} rx={4} ry={4} />
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
        <rect x={x} y={y} width={width} height={height} fill={fill} rx={4} ry={4} />
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
      const total = payload[0].value

      // Calculate prior year total from prior_parts, prior_labor, prior_rental
      const priorYearTotal = monthData ?
        (monthData.prior_parts || 0) + (monthData.prior_labor || 0) + (monthData.prior_rental || 0) : null

      // Calculate blended margin (weighted average based on revenue)
      let blendedMargin = null
      let priorBlendedMargin = null

      if (monthData && total > 0) {
        const partsGP = monthData.parts - (monthData.parts * (1 - (monthData.parts_margin || 0) / 100))
        const laborGP = monthData.labor - (monthData.labor * (1 - (monthData.labor_margin || 0) / 100))
        const rentalGP = monthData.rental - (monthData.rental * (1 - (monthData.rental_margin || 0) / 100))

        // Simpler calculation: use margin percentages directly weighted by revenue
        const totalRevenue = monthData.parts + monthData.labor + monthData.rental
        if (totalRevenue > 0) {
          blendedMargin = (
            (monthData.parts / totalRevenue) * (monthData.parts_margin || 0) +
            (monthData.labor / totalRevenue) * (monthData.labor_margin || 0) +
            (monthData.rental / totalRevenue) * (monthData.rental_margin || 0)
          )
        }
      }

      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="font-semibold mb-2">{label}</p>
          <div className="space-y-1">
            <div className="flex justify-between items-center">
              <span>Total Sales:</span>
              <span className="ml-4 font-semibold">
                {formatCurrency(total)}
                {priorYearTotal > 0 && formatPercentage(calculatePercentageChange(total, priorYearTotal))}
              </span>
            </div>
            {blendedMargin !== null && (
              <div className="flex justify-between items-center">
                <span>Blended Margin:</span>
                <span className="ml-4 font-semibold">
                  {blendedMargin.toFixed(1)}%
                </span>
              </div>
            )}
          </div>
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
            <div className="grid gap-4 md:grid-cols-5">
              {[...Array(5)].map((_, i) => (
                <Card key={i} className="border-l-4 border-l-gray-300">
                  <CardContent className="pt-4 pb-3 px-4">
                    <div className="h-3 bg-gray-200 rounded w-16 animate-pulse mb-2" />
                    <div className="h-7 bg-gray-200 rounded w-20 animate-pulse mb-1" />
                    <div className="h-3 bg-gray-200 rounded w-24 animate-pulse" />
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

  // Render VITAL dashboard if user is from VITAL Worklife organization
  if (user?.organization?.name === 'VITAL Worklife') {
    return <VitalExecutiveDashboard user={user} />
  }

  // Render Bennett Dashboard for all other organizations
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Sales Dashboard</h1>
          <p className="text-muted-foreground text-sm md:text-base">
            Welcome back, {user?.first_name}! Here's what's happening with your business.
          </p>
        </div>
        <div className="flex items-center space-x-2 flex-wrap gap-y-2">
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
            <span className="hidden sm:inline">Refresh</span>
          </Button>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            <span className="hidden sm:inline">Export Report</span>
          </Button>
          <MethodologyPanel {...SALES_DASHBOARD_METHODOLOGY} />
        </div>
      </div>

      {/* Tabbed Interface */}
      <Tabs defaultValue="sales" value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="flex flex-wrap md:grid md:w-full md:max-w-3xl md:grid-cols-5 gap-1">
          <TabsTrigger value="sales">Sales</TabsTrigger>
          <TabsTrigger value="customers">Customers</TabsTrigger>
          <TabsTrigger value="workorders">Work Orders</TabsTrigger>
          <TabsTrigger value="forecast">AI Sales Forecast</TabsTrigger>
          <TabsTrigger value="accuracy">AI Forecast Accuracy</TabsTrigger>
        </TabsList>

        {/* Sales Tab */}
        <TabsContent value="sales" className="space-y-4">
          {/* Row 1: Glanceable KPI Cards */}
          <div className="grid gap-4 md:grid-cols-5">
            {/* MTD Sales */}
            <Card className="border-l-4 border-l-green-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <DollarSign className="h-4 w-4 text-green-500" />
                  <span className="text-xs font-medium text-muted-foreground">MTD Sales</span>
                  <MetricTooltip {...IPS_METRICS.dashboard_mtd_sales} />
                </div>
                <div className="text-2xl font-bold">
                  {formatCurrency(dashboardData?.total_sales || 0)}
                  {paceData?.adaptive_comparisons?.performance_indicators?.is_best_month_ever && (
                    <span className="ml-1 text-sm">⭐</span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {paceData?.adaptive_comparisons?.vs_same_month_last_year?.data_unavailable ? (
                    <span className="text-muted-foreground">No PY data (pre-cutover)</span>
                  ) : paceData?.adaptive_comparisons?.vs_same_month_last_year?.percentage !== null && paceData?.adaptive_comparisons?.vs_same_month_last_year?.percentage !== undefined ? (
                    <span className={paceData.adaptive_comparisons.vs_same_month_last_year.percentage > 0 ? 'text-green-600' : paceData.adaptive_comparisons.vs_same_month_last_year.percentage < 0 ? 'text-red-600' : ''}>
                      {paceData.adaptive_comparisons.vs_same_month_last_year.percentage > 0 ? '+' : ''}{paceData.adaptive_comparisons.vs_same_month_last_year.percentage}% vs PY
                    </span>
                  ) : (
                    dashboardData?.period || `Through day ${new Date().getDate()}`
                  )}
                </p>
              </CardContent>
            </Card>

            {/* YTD Sales */}
            <Card className="border-l-4 border-l-blue-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="h-4 w-4 text-blue-500" />
                  <span className="text-xs font-medium text-muted-foreground">FY26 YTD Sales</span>
                  <MetricTooltip {...IPS_METRICS.dashboard_ytd_sales} />
                </div>
                <div className="text-2xl font-bold">
                  {formatCurrency(dashboardData?.ytd_sales || 0)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {dashboardData?.prior_year_ytd_sales > 0 ? (() => {
                    const change = ((dashboardData.ytd_sales - dashboardData.prior_year_ytd_sales) / dashboardData.prior_year_ytd_sales * 100).toFixed(1)
                    return (
                      <span className={change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : ''}>
                        {change > 0 ? '+' : ''}{change}% vs PY
                      </span>
                    )
                  })() : 'Nov 2025 – Present'}
                </p>
              </CardContent>
            </Card>

            {/* Blended GP% */}
            <Card className="border-l-4 border-l-purple-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <Gauge className="h-4 w-4 text-purple-500" />
                  <span className="text-xs font-medium text-muted-foreground">Blended GP%</span>
                  <MetricTooltip {...IPS_METRICS.dashboard_blended_gp} />
                </div>
                <div className={`text-2xl font-bold ${dashboardData?.ytd_margin >= 25 ? 'text-green-600' : dashboardData?.ytd_margin > 0 ? 'text-red-600' : ''}`}>
                  {dashboardData?.ytd_margin > 0 ? `${dashboardData.ytd_margin}%` : '—'}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {dashboardData?.prior_year_ytd_margin > 0 ? (() => {
                    const diff = (dashboardData.ytd_margin - dashboardData.prior_year_ytd_margin).toFixed(1)
                    return (
                      <span className={diff > 0 ? 'text-green-600' : diff < 0 ? 'text-red-600' : ''}>
                        {diff > 0 ? '+' : ''}{diff} pts vs PY
                      </span>
                    )
                  })() : 'YTD blended margin'}
                </p>
              </CardContent>
            </Card>

            {/* Equipment Units Sold FY */}
            <Card className="border-l-4 border-l-cyan-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <Package className="h-4 w-4 text-cyan-500" />
                  <span className="text-xs font-medium text-muted-foreground">Equip. Units (FY)</span>
                  <MetricTooltip label="Equipment Units (FY)" formula="Count of Linde new truck units invoiced in the current fiscal year (Nov–Oct). Counted from invoices with SaleCode 'LINDEN' in the Invoice Register." accounts={[]} />
                </div>
                <div className="text-2xl font-bold">
                  {(() => {
                    if (!dashboardData?.monthly_equipment_sales) return '—'
                    const fyStartMonth = dashboardData?.fiscal_year_start_month || 11
                    const now = new Date()
                    const fyStartYear = now.getMonth() + 1 >= fyStartMonth ? now.getFullYear() : now.getFullYear() - 1
                    return dashboardData.monthly_equipment_sales
                      .filter(item => item.year > fyStartYear || (item.year === fyStartYear && item.month_number >= fyStartMonth))
                      .reduce((sum, item) => sum + (item.unit_count || 0), 0)
                  })()}
                </div>
                <p className="text-xs text-muted-foreground mt-1">Linde new trucks sold</p>
              </CardContent>
            </Card>

            {/* Active Customers */}
            <Card className="border-l-4 border-l-amber-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <Users className="h-4 w-4 text-amber-500" />
                  <span className="text-xs font-medium text-muted-foreground">Active Customers</span>
                  <MetricTooltip label="Active Customers" formula="Count of distinct customers invoiced in the last 30 days. The +/− change compares to the prior 30-day window (31–60 days ago). Excludes internal accounts." accounts={[]} />
                </div>
                <div className="text-2xl font-bold">
                  {dashboardData?.active_customers || '—'}
                  {dashboardData?.active_customers_change !== undefined && dashboardData?.active_customers_change !== 0 && (
                    <span className={`ml-1 text-sm ${dashboardData.active_customers_change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {dashboardData.active_customers_change > 0 ? '+' : ''}{dashboardData.active_customers_change}
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground mt-1">Last 30 days</p>
              </CardContent>
            </Card>
          </div>

          {/* Row 2: YTD Performance Summary + Action Items */}
          <div className="grid gap-4 md:grid-cols-3">
            {/* YTD Performance Summary - 2/3 width */}
            <Card className="md:col-span-2">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  YTD Performance Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-6 md:grid-cols-3">
                  <div className="space-y-2">
                    <h4 className="font-medium text-xs text-muted-foreground uppercase tracking-wide">YTD Blended GP%</h4>
                    <div className="flex items-baseline gap-2">
                      <span className={`text-3xl font-bold ${dashboardData?.ytd_margin >= 25 ? 'text-green-600' : 'text-red-600'}`}>
                        {dashboardData?.ytd_margin > 0 ? `${dashboardData.ytd_margin}%` : '—'}
                      </span>
                      <span className="text-sm text-muted-foreground">/ 25%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${dashboardData?.ytd_margin >= 25 ? 'bg-green-500' : 'bg-red-500'}`}
                        style={{ width: `${Math.min((dashboardData?.ytd_margin || 0) / 25 * 100, 100)}%` }} />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium text-xs text-muted-foreground uppercase tracking-wide">Aftermarket Avg/Mo</h4>
                    <div className="text-3xl font-bold text-emerald-600">
                      {dashboardData?.monthly_sales_no_equipment && dashboardData.monthly_sales_no_equipment.length > 1 ? 
                        formatCurrency(dashboardData.monthly_sales_no_equipment.slice(0, -1).reduce((sum, item) => sum + item.amount, 0) / dashboardData.monthly_sales_no_equipment.slice(0, -1).length)
                        : '—'}
                    </div>
                    <p className="text-xs text-muted-foreground">Parts + Service + Rental</p>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium text-xs text-muted-foreground uppercase tracking-wide">Sales Pace</h4>
                    <div className={`text-3xl font-bold ${paceData?.pace?.percentage > 0 ? 'text-green-600' : paceData?.pace?.percentage < 0 ? 'text-red-600' : ''}`}>
                      {paceData?.pace?.percentage !== undefined ? `${paceData.pace.percentage > 0 ? '+' : ''}${paceData.pace.percentage}%` : '—'}
                    </div>
                    <p className="text-xs text-muted-foreground">vs prior month pace</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Action Items - 1/3 width */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-orange-500" />
                  Action Items
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {/* Declining sales trend */}
                  {dashboardData?.monthly_sales && dashboardData.monthly_sales.length >= 3 && (() => {
                    const recent = dashboardData.monthly_sales.slice(-3, -1) // last 2 complete months
                    if (recent.length >= 2 && recent[1].amount < recent[0].amount) {
                      const decline = ((recent[0].amount - recent[1].amount) / recent[0].amount * 100).toFixed(1)
                      return (
                        <div className="flex items-center gap-3 p-2 rounded-lg bg-red-50">
                          <TrendingDown className="h-5 w-5 text-red-600 flex-shrink-0" />
                          <div>
                            <p className="text-sm font-medium text-red-800">Sales Declining</p>
                            <p className="text-xs text-red-600">-{decline}% month-over-month</p>
                          </div>
                        </div>
                      )
                    }
                    return null
                  })()}

                  {/* GP below target */}
                  {dashboardData?.ytd_margin > 0 && dashboardData.ytd_margin < 25 && (
                    <div className="flex items-center gap-3 p-2 rounded-lg bg-yellow-50">
                      <Gauge className="h-5 w-5 text-yellow-600 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-yellow-800">GP% Below Target</p>
                        <p className="text-xs text-yellow-600">{dashboardData.ytd_margin}% — target 25%</p>
                      </div>
                    </div>
                  )}

                  {/* At-risk customers */}
                  {customerRiskData?.at_risk_count > 0 && (
                    <button
                      onClick={() => setActiveTab('customers')}
                      className="w-full flex items-center gap-3 p-2 rounded-lg bg-orange-50 hover:bg-orange-100 transition-colors text-left"
                    >
                      <Users className="h-5 w-5 text-orange-600 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-orange-800">{customerRiskData.at_risk_count} At-Risk Customers</p>
                        <p className="text-xs text-orange-600">Declining activity detected</p>
                      </div>
                      <ChevronRight className="h-4 w-4 text-orange-400 ml-auto" />
                    </button>
                  )}

                  {/* Invoice delays */}
                  {invoiceDelayData?.totals?.count > 0 && invoiceDelayData.totals.avg_days > 3 && (
                    <button
                      onClick={() => setActiveTab('workorders')}
                      className="w-full flex items-center gap-3 p-2 rounded-lg bg-purple-50 hover:bg-purple-100 transition-colors text-left"
                    >
                      <Clock className="h-5 w-5 text-purple-600 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-purple-800">Invoice Delays</p>
                        <p className="text-xs text-purple-600">Avg {invoiceDelayData.totals.avg_days} days, {formatCurrency(invoiceDelayData.totals.value)} pending</p>
                      </div>
                      <ChevronRight className="h-4 w-4 text-purple-400 ml-auto" />
                    </button>
                  )}

                  {/* All clear state */}
                  {(!dashboardData?.monthly_sales || dashboardData.monthly_sales.length < 3 || (() => {
                    const recent = dashboardData.monthly_sales.slice(-3, -1)
                    return recent.length < 2 || recent[1].amount >= recent[0].amount
                  })()) &&
                   (!dashboardData?.ytd_margin || dashboardData.ytd_margin >= 25) &&
                   (!customerRiskData?.at_risk_count || customerRiskData.at_risk_count === 0) &&
                   (!invoiceDelayData?.totals?.count || invoiceDelayData.totals.avg_days <= 3) && (
                    <div className="text-center py-4 text-green-600">
                      <CheckCircle className="h-8 w-8 mx-auto mb-2" />
                      <p className="text-sm font-medium">All Clear</p>
                      <p className="text-xs text-muted-foreground">No items need attention</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Include Current Month Toggle */}
          <div className="flex items-center justify-end gap-2">
            <Switch
              id="include-current-month"
              checked={includeCurrentMonth}
              onCheckedChange={setIncludeCurrentMonth}
            />
            <Label htmlFor="include-current-month" className="text-sm text-muted-foreground cursor-pointer">
              Include current month
            </Label>
          </div>

          {/* Row 3: Primary Chart - Monthly Sales (full width) */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle>Monthly Sales</CardTitle>
                  <CardDescription>Total revenue including equipment and aftermarket</CardDescription>
                </div>
                  {sortedMonthlySales.length > 0 && (() => {
                    const avgRevenue = sortedMonthlySales.reduce((sum, item) => sum + item.amount, 0) / sortedMonthlySales.length
                    const marginsOnly = sortedMonthlySales.filter(item => item.margin !== null && item.margin !== undefined)
                    const avgMargin = marginsOnly.length > 0 ? marginsOnly.reduce((sum, item) => sum + item.margin, 0) / marginsOnly.length : 0
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
                  <ComposedChart data={calculateLinearTrend(sortedMonthlySales, 'month', 'amount', false, dashboardData?.fiscal_year_start_month)} margin={{ top: 40, right: 60, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis yAxisId="left" tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                    <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => `${value}%`} />
                    <Tooltip content={({ active, payload, label }) => {
                      if (active && payload && payload.length && dashboardData?.monthly_sales) {
                        const data = dashboardData.monthly_sales
                        const currentIndex = data.findIndex(item => item.month === label)
                        const monthData = data[currentIndex]

                        // Use prior_year_amount for year-over-year comparison
                        const priorYearValue = monthData?.prior_year_amount || null

                        return (
                          <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                            <p className="font-semibold mb-1">{label}</p>
                            <p className="text-green-600">
                              Revenue: {formatCurrency(monthData?.amount || 0)}
                              {priorYearValue && priorYearValue > 0 && (
                                <span className="text-sm ml-2">
                                  ({formatPercentage(calculatePercentageChange(monthData?.amount, priorYearValue))} vs PY)
                                </span>
                              )}
                            </p>
                            {priorYearValue && priorYearValue > 0 && (
                              <p className="text-gray-400 text-sm">
                                Prior Year: {formatCurrency(priorYearValue)}
                              </p>
                            )}
                            {monthData?.margin !== null && monthData?.margin !== undefined && (
                              <p className="text-blue-600">
                                Blended Margin: {monthData.margin.toFixed(1)}%
                                {monthData.prior_year_margin !== null && monthData.prior_year_margin !== undefined && (
                                  <span className={`text-sm ml-2 ${monthData.margin > monthData.prior_year_margin ? 'text-green-600' : monthData.margin < monthData.prior_year_margin ? 'text-red-600' : 'text-gray-500'}`}>
                                    ({monthData.margin > monthData.prior_year_margin ? '+' : ''}{(monthData.margin - monthData.prior_year_margin).toFixed(1)} pts vs last year)
                                  </span>
                                )}
                              </p>
                            )}
                          </div>
                        )
                      }
                      return null
                    }} />
                    <Legend content={({ payload }) => (
                      <div className="flex justify-center gap-4 mt-2 text-sm">
                        {payload?.map((entry, index) => (
                          <span key={index} className="flex items-center gap-1">
                            {entry.value === 'Prior Year' ? (
                              <svg width="14" height="14"><rect width="14" height="14" fill="#8884d8" fillOpacity="0.15" stroke="#8884d8" strokeOpacity="0.3" strokeWidth="1" strokeDasharray="3 2" rx="2" /></svg>
                            ) : (
                              <svg width="14" height="14">
                                {entry.type === 'line' ? (
                                  <line x1="0" y1="7" x2="14" y2="7" stroke={entry.color} strokeWidth="2" strokeDasharray={entry.value === 'Revenue Trend' ? '4 3' : '0'} />
                                ) : (
                                  <rect width="14" height="14" fill={entry.color} rx="2" />
                                )}
                              </svg>
                            )}
                            <span className="text-gray-600">{entry.value}</span>
                          </span>
                        ))}
                      </div>
                    )} />
                    <Bar yAxisId="left" dataKey="amount" fill="#8884d8" name="Revenue" shape={<CustomBar />} />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="margin"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={{ fill: '#10b981' }}
                      name="Gross Margin %"
                      connectNulls={false}
                      data={includeCurrentMonth 
                        ? sortedMonthlySales.map((item, index) =>
                            index === sortedMonthlySales.length - 1 ? { ...item, margin: null } : item
                          )
                        : sortedMonthlySales
                      }
                    />
                    <Line yAxisId="left" type="monotone" dataKey="trendValue" stroke="#8b5cf6" strokeWidth={2} strokeDasharray="5 5" name="Revenue Trend" dot={false} />
                    {sortedMonthlySales.length > 0 && (() => {
                      const average = sortedMonthlySales.reduce((sum, item) => sum + item.amount, 0) / sortedMonthlySales.length
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

          {/* Row 4: Supporting Charts - 3 across */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-base">Aftermarket Sales</CardTitle>
                    <CardDescription>
                      Service, Parts, Rental & Transportation
                    </CardDescription>
                  </div>
                  {dashboardData?.monthly_sales_no_equipment && dashboardData.monthly_sales_no_equipment.length > 0 && (() => {
                    const completeMonths = dashboardData.monthly_sales_no_equipment.slice(0, -1)
                    const avgRevenue = completeMonths.reduce((sum, item) => sum + item.amount, 0) / completeMonths.length
                    return (
                      <div className="text-right">
                        <p className="text-xs text-muted-foreground">Avg</p>
                        <p className="text-sm font-semibold">{formatCurrency(avgRevenue)}</p>
                      </div>
                    )
                  })()}
                </div>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <ComposedChart data={calculateLinearTrend(sortedMonthlySalesNoEquipment, 'month', 'amount', false, dashboardData?.fiscal_year_start_month)} margin={{ top: 20, right: 50, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis yAxisId="left" tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                    <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => `${value}%`} />
                    <Tooltip content={({ active, payload, label }) => {
                      if (active && payload && dashboardData?.monthly_sales_no_equipment) {
                        const data = dashboardData.monthly_sales_no_equipment
                        const currentIndex = data.findIndex(item => item.month === label)
                        const monthData = data[currentIndex]

                        // Use prior_year_amount for year-over-year comparison
                        const priorYearValue = monthData?.prior_year_amount || null
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
                              {priorYearValue && priorYearValue > 0 && (
                                <span className="text-sm ml-2">
                                  ({formatPercentage(calculatePercentageChange(monthData?.amount, priorYearValue))} vs last year)
                                </span>
                              )}
                            </p>
                            {monthData?.margin !== null && monthData?.margin !== undefined && (
                              <p className="text-blue-600">
                                Blended Margin: {monthData.margin.toFixed(1)}%
                                {monthData.prior_year_margin !== null && monthData.prior_year_margin !== undefined && (
                                  <span className={`text-sm ml-2 ${monthData.margin > monthData.prior_year_margin ? 'text-green-600' : monthData.margin < monthData.prior_year_margin ? 'text-red-600' : 'text-gray-500'}`}>
                                    ({monthData.margin > monthData.prior_year_margin ? '+' : ''}{(monthData.margin - monthData.prior_year_margin).toFixed(1)} pts vs last year)
                                  </span>
                                )}
                              </p>
                            )}
                          </div>
                        )
                      }
                      return null
                    }} />
                    <Legend />
                    <Bar yAxisId="left" dataKey="amount" fill="#10b981" name="Revenue" shape={<CustomBarNoEquipment />} />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="margin"
                      stroke="#f59e0b"
                      strokeWidth={2}
                      dot={{ fill: '#f59e0b' }}
                      name="Gross Margin %"
                      connectNulls={false}
                      data={includeCurrentMonth
                        ? sortedMonthlySalesNoEquipment.map((item, index) =>
                            index === sortedMonthlySalesNoEquipment.length - 1 ? { ...item, margin: null } : item
                          )
                        : sortedMonthlySalesNoEquipment
                      }
                    />
                    <Line yAxisId="left" type="monotone" dataKey="trendValue" stroke="#8b5cf6" strokeWidth={2} strokeDasharray="5 5" name="Revenue Trend" dot={false} />
                    {sortedMonthlySalesNoEquipment.length > 0 && (() => {
                      const average = sortedMonthlySalesNoEquipment.reduce((sum, item) => sum + item.amount, 0) / sortedMonthlySalesNoEquipment.length
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
                    <CardTitle className="text-base">Monthly Quotes</CardTitle>
                    <CardDescription>Quote activity through February {new Date().getFullYear() + 1}</CardDescription>
                  </div>
                  {dashboardData?.monthly_quotes?.length > 1 && (() => {
                    const completeMonths = dashboardData.monthly_quotes.slice(0, -1)
                    const average = completeMonths.reduce((sum, item) => sum + item.amount, 0) / completeMonths.length
                    return (
                      <div className="text-right">
                        <p className="text-xs text-muted-foreground">Avg</p>
                        <p className="text-sm font-semibold">{formatCurrency(average)}</p>
                      </div>
                    )
                  })()}
                </div>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <ComposedChart data={calculateLinearTrend(sortedMonthlyQuotes, 'month', 'amount', false)} margin={{ top: 20, right: 20, left: 10, bottom: 5 }}>
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
                    <Line type="monotone" dataKey="trendValue" stroke="#8b5cf6" strokeWidth={2} strokeDasharray="5 5" name="Quotes Trend" dot={false} />
                    {sortedMonthlyQuotes.length > 0 && (() => {
                      const average = sortedMonthlyQuotes.reduce((sum, item) => sum + item.amount, 0) / sortedMonthlyQuotes.length
                      return (
                        <ReferenceLine
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
                    <CardTitle className="text-base">Linde New Equipment Sales</CardTitle>
                    <CardDescription>
                      Linde new truck revenue and gross margin
                    </CardDescription>
                  </div>
                  {dashboardData?.monthly_equipment_sales && dashboardData.monthly_equipment_sales.length > 0 && (() => {
                    const completeMonths = dashboardData.monthly_equipment_sales.slice(0, -1)
                    const avgRevenue = completeMonths.reduce((sum, item) => sum + item.amount, 0) / completeMonths.length
                    return (
                      <div className="text-right">
                        <p className="text-xs text-muted-foreground">Avg</p>
                        <p className="text-sm font-semibold">{formatCurrency(avgRevenue)}</p>
                      </div>
                    )
                  })()}
                </div>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <ComposedChart data={calculateLinearTrend(sortedMonthlyEquipmentSales, 'month', 'amount', false, dashboardData?.fiscal_year_start_month)} margin={{ top: 20, right: 50, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis yAxisId="left" tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                    <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => `${value}%`} />
                    <Tooltip content={({ active, payload, label }) => {
                      if (active && payload && dashboardData?.monthly_equipment_sales) {
                        const data = dashboardData.monthly_equipment_sales
                        const currentIndex = data.findIndex(item => item.month === label)
                        const monthData = data[currentIndex]

                        // Use prior_year_amount for year-over-year comparison
                        const priorYearValue = monthData?.prior_year_amount || null

                        return (
                          <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                            <p className="font-semibold mb-2">{label}</p>
                            <p className="font-semibold text-green-600">
                              Revenue: {formatCurrency(monthData?.amount || 0)}
                              {priorYearValue && priorYearValue > 0 && (
                                <span className="text-sm ml-2">
                                  ({formatPercentage(calculatePercentageChange(monthData?.amount, priorYearValue))} vs last year)
                                </span>
                              )}
                            </p>
                            {monthData?.unit_count !== null && monthData?.unit_count !== undefined && monthData?.unit_count > 0 && (
                              <p className="text-purple-600">
                                Units Sold: {monthData.unit_count}
                              </p>
                            )}
                            {monthData?.margin !== null && monthData?.margin !== undefined && (
                              <p className="text-blue-600">
                                Margin: {monthData.margin.toFixed(1)}%
                                {monthData.prior_year_margin !== null && monthData.prior_year_margin !== undefined && (
                                  <span className={`text-sm ml-2 ${monthData.margin > monthData.prior_year_margin ? 'text-green-600' : monthData.margin < monthData.prior_year_margin ? 'text-red-600' : 'text-gray-500'}`}>
                                    ({monthData.margin > monthData.prior_year_margin ? '+' : ''}{(monthData.margin - monthData.prior_year_margin).toFixed(1)} pts vs last year)
                                  </span>
                                )}
                              </p>
                            )}
                          </div>
                        )
                      }
                      return null
                    }} />
                    <Legend />
                    <Bar yAxisId="left" dataKey="amount" fill="#06b6d4" name="Revenue" radius={[4, 4, 0, 0]} />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="margin"
                      stroke="#f59e0b"
                      strokeWidth={2}
                      dot={{ fill: '#f59e0b' }}
                      name="Gross Margin %"
                      connectNulls={false}
                      data={includeCurrentMonth
                        ? sortedMonthlyEquipmentSales.map((item, index) =>
                            index === sortedMonthlyEquipmentSales.length - 1 ? { ...item, margin: null } : item
                          )
                        : sortedMonthlyEquipmentSales
                      }
                    />
                    <Line yAxisId="left" type="monotone" dataKey="trendValue" stroke="#8b5cf6" strokeWidth={2} strokeDasharray="5 5" name="Revenue Trend" dot={false} />
                    {sortedMonthlyEquipmentSales.length > 0 && (() => {
                      const average = sortedMonthlyEquipmentSales.reduce((sum, item) => sum + item.amount, 0) / sortedMonthlyEquipmentSales.length
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

        </TabsContent>

        {/* Customers Tab */}
        <TabsContent value="customers" className="space-y-4">
          {/* Customer Metrics */}
          <div className="mb-2 text-xs text-gray-500">
            As of {dashboardData?.last_updated ? new Date(dashboardData.last_updated).toLocaleString() : 'Loading...'}
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Customers</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${dashboardData?.active_customers_change > 0 ? 'text-green-600' :
                  dashboardData?.active_customers_change < 0 ? 'text-red-600' :
                    'text-gray-900'
                  }`}>
                  {dashboardData?.active_customers || 0}
                  {dashboardData?.active_customers_change !== undefined && dashboardData?.active_customers_change !== 0 && (
                    <span className={`ml-2 text-sm font-normal ${dashboardData?.active_customers_change > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                      {dashboardData?.active_customers_change > 0 ? '+' : ''}{dashboardData?.active_customers_change}
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  Customers with invoices in last 30 days
                  {dashboardData?.active_customers_change_percent !== undefined && dashboardData?.active_customers_change_percent !== 0 && (
                    <span className={`ml-1 ${dashboardData?.active_customers_change_percent > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                      ({dashboardData?.active_customers_change_percent > 0 ? '+' : ''}{dashboardData?.active_customers_change_percent?.toFixed(1)}% vs prev month)
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
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle>Top 10 Customers</CardTitle>
                    <CardDescription>
                      By all-time sales
                    </CardDescription>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => downloadActiveCustomers()}
                    className="h-8 px-2 ml-2"
                    title="Export top customers"
                  >
                    <Download className="h-3 w-3 mr-1" />
                    Export
                  </Button>
                </div>

                {/* Search */}
                <div className="flex gap-2 mt-4">
                  <div className="flex-1">
                    <Input
                      placeholder="Search customers..."
                      value={customerSearchTerm}
                      onChange={(e) => setCustomerSearchTerm(e.target.value)}
                      className="h-9"
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {filteredCustomers.length > 0 ? filteredCustomers.map((customer) => {
                    return (
                      <div key={customer.rank} className="flex items-center">
                        <div className="w-8 text-sm font-medium text-muted-foreground">
                          {customer.rank}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate text-gray-900">
                            <button
                              onClick={() => {
                                setSelectedCustomer(customer)
                                setCustomerDetailModalOpen(true)
                              }}
                              className="hover:underline cursor-pointer text-left"
                            >
                              {customer.name}
                            </button>
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
                    )
                  }) : (
                    <div className="flex flex-col items-center justify-center py-8 text-center">
                      <Users className="h-12 w-12 text-gray-300 mb-3" />
                      <p className="text-sm font-medium text-gray-900 mb-1">
                        {customerSearchTerm
                          ? 'No customers match your search'
                          : 'No customer data available'
                        }
                      </p>
                      <p className="text-xs text-gray-500">
                        {customerSearchTerm
                          ? 'Try adjusting your search'
                          : 'Customer data will appear here once invoices are processed'
                        }
                      </p>
                      {customerSearchTerm && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="mt-3"
                          onClick={() => {
                            setCustomerSearchTerm('')
                          }}
                        >
                          Clear Search
                        </Button>
                      )}
                    </div>
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
                  <LineChart data={calculateLinearTrend(dashboardData?.monthly_active_customers?.slice(0, -1) || [], 'month', 'customers')} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
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
                    <Line
                      type="monotone"
                      dataKey="trendValue"
                      stroke="#8b5cf6"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name="Customer Trend"
                      dot={false}
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
                          <Bar dataKey="percentage" fill="#8884d8" radius={[4, 4, 0, 0]}>
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
                          <div className={`mt-1 w-2 h-2 rounded-full ${factor.impact === 'positive' ? 'bg-green-500' :
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
                          className={`h-full transition-all duration-500 ${(forecastData.analysis?.actual_pct_of_forecast || 0) > 100 ? 'bg-green-500' : 'bg-blue-500'
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

        {/* Forecast Accuracy Tab */}
        <TabsContent value="accuracy" className="space-y-4">
          <ForecastAccuracy />
        </TabsContent>
      </Tabs>

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
