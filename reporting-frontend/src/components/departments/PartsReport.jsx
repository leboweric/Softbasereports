import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
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
  LineChart,
  Line,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  ReferenceLine,
  ComposedChart,
  Legend
} from 'recharts'
import { TrendingUp, TrendingDown, Package, AlertTriangle, Clock, ShoppingCart, Info, Zap, Turtle, Download } from 'lucide-react'
import { apiUrl } from '@/lib/api'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import PartsEmployeePerformance from './PartsEmployeePerformance'
import PartsInventoryByLocation from './PartsInventoryByLocation'
import PartsInventoryTurns from './PartsInventoryTurns'
import { usePermissions, getAccessibleTabs } from '../../contexts/PermissionsContext'

// Utility function to calculate linear regression trendline
const calculateLinearTrend = (data, xKey, yKey, excludeCurrentMonth = true) => {
  if (!data || data.length < 2) return data || []
  
  const validData = data.filter(item => item[yKey] !== null && item[yKey] !== undefined)
  if (validData.length < 2) return data
  
  // Determine which data to use for trendline calculation
  let trendData = validData
  
  if (excludeCurrentMonth && validData.length > 1) {
    // Exclude the last data point (assumed to be current incomplete month)
    trendData = validData.slice(0, -1)
  }
  
  // Need at least 2 points for a trendline
  if (trendData.length < 2) {
    return data.map(item => ({
      ...item,
      trendValue: null
    }))
  }
  
  // Calculate linear regression using trendData (excluding current month)
  const n = trendData.length
  const sumX = trendData.reduce((sum, _, index) => sum + index, 0)
  const sumY = trendData.reduce((sum, item) => sum + item[yKey], 0)
  const sumXY = trendData.reduce((sum, item, index) => sum + (index * item[yKey]), 0)
  const sumXX = trendData.reduce((sum, _, index) => sum + (index * index), 0)
  
  const denominator = (n * sumXX - sumX * sumX)
  if (denominator === 0) {
    return data.map(item => ({
      ...item,
      trendValue: null
    }))
  }
  
  const slope = (n * sumXY - sumX * sumY) / denominator
  const intercept = (sumY - slope * sumX) / n
  
  // Apply trendline to ALL data points (including current month)
  // This extends the trendline through the current month
  return data.map((item, index) => ({
    ...item,
    trendValue: slope * index + intercept
  }))
}


const PartsReport = ({ user, onNavigate }) => {
  const { navigation } = usePermissions()
  
  // Get accessible tabs from user's navigation config
  const accessibleTabs = getAccessibleTabs(user, 'parts')
  
  // Build tabs array from config with desired order
  const tabOrder = ['overview', 'work-orders', 'inventory-location', 'stock-alerts', 'forecast', 'employee-performance', 'velocity', 'inventory-turns']
  const tabs = tabOrder
    .filter(id => accessibleTabs[id]) // Only include tabs user has access to
    .map(id => ({
      value: id,
      label: accessibleTabs[id].label,
      resource: accessibleTabs[id].resource,
    }))
  const [partsData, setPartsData] = useState(null)
  const [fillRateData, setFillRateData] = useState(null)
  const [reorderAlertData, setReorderAlertData] = useState(null)
  const [velocityData, setVelocityData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [openWorkOrdersData, setOpenWorkOrdersData] = useState(null)
  const [openWorkOrdersDetails, setOpenWorkOrdersDetails] = useState(null)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [paceData, setPaceData] = useState(null)
  const [fillRateLoading, setFillRateLoading] = useState(true)
  const [reorderAlertLoading, setReorderAlertLoading] = useState(true)
  const [velocityLoading, setVelocityLoading] = useState(true)
  const [forecastData, setForecastData] = useState(null)
  const [forecastLoading, setForecastLoading] = useState(true)
  const [top10Data, setTop10Data] = useState(null)
  const [top10Loading, setTop10Loading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [categoryModalOpen, setCategoryModalOpen] = useState(false)
  
  // Default to first available tab (should be overview if accessible)
  const [activeTab, setActiveTab] = useState(tabs[0]?.value || 'overview')

  // Sort monthly revenue data chronologically for correct trendline calculation
  const sortedMonthlyRevenue = React.useMemo(() => {
    if (!partsData?.monthlyPartsRevenue) {
      return [];
    }

    const monthOrder = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];

    return [...partsData.monthlyPartsRevenue].sort((a, b) => {
      return monthOrder.indexOf(a.month) - monthOrder.indexOf(b.month);
    });
  }, [partsData]);

  // Helper function to calculate percentage change
  const calculatePercentageChange = (current, previous) => {
    if (!previous || previous === 0) return null
    const change = ((current - previous) / previous) * 100
    return change
  }

  // Helper function to format percentage with color
  const formatPercentage = (percentage) => {
    if (percentage === null) return ''
    const sign = percentage >= 0 ? '+' : ''
    const color = percentage >= 0 ? 'text-green-600' : 'text-red-600'
    return <span className={`ml-2 ${color}`}>({sign}{percentage.toFixed(1)}%)</span>
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  useEffect(() => {
    fetchPartsData()
    fetchFillRateData()
    fetchReorderAlertData()
    fetchVelocityData()
    fetchForecastData()
    fetchTop10Data()
    fetchPaceData()
    fetchOpenWorkOrdersData()
  }, [])

  useEffect(() => {
    // Fetch work order details when switching to work orders tab
    if (activeTab === 'work-orders' && !openWorkOrdersDetails) {
      fetchOpenWorkOrdersDetails()
    }
  }, [activeTab])

  const fetchPartsData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setPartsData(data)
      } else {
        console.error('Failed to fetch parts data:', response.status)
        // Set default empty data structure
        setPartsData({
          monthlyPartsRevenue: []
        })
      }
    } catch (error) {
      console.error('Error fetching parts data:', error)
      // Set default empty data structure on error
      setPartsData({
        monthlyPartsRevenue: []
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchFillRateData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts/fill-rate'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setFillRateData(data)
      } else {
        console.error('Failed to fetch fill rate data:', response.status)
        setFillRateData(null)
      }
    } catch (error) {
      console.error('Error fetching fill rate data:', error)
      setFillRateData(null)
    } finally {
      setFillRateLoading(false)
    }
  }

  const fetchReorderAlertData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts/reorder-alert'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setReorderAlertData(data)
      } else {
        console.error('Failed to fetch reorder alert data:', response.status)
        setReorderAlertData(null)
      }
    } catch (error) {
      console.error('Error fetching reorder alert data:', error)
      setReorderAlertData(null)
    } finally {
      setReorderAlertLoading(false)
    }
  }

  const fetchVelocityData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts/velocity'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setVelocityData(data)
      } else {
        console.error('Failed to fetch velocity data:', response.status)
        setVelocityData(null)
      }
    } catch (error) {
      console.error('Error fetching velocity data:', error)
      setVelocityData(null)
    } finally {
      setVelocityLoading(false)
    }
  }

  const fetchForecastData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts/forecast'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setForecastData(data)
      } else {
        console.error('Failed to fetch forecast data:', response.status)
        setForecastData(null)
      }
    } catch (error) {
      console.error('Error fetching forecast data:', error)
      setForecastData(null)
    } finally {
      setForecastLoading(false)
    }
  }

  const fetchTop10Data = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts/top10'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setTop10Data(data)
      } else {
        console.error('Failed to fetch top 10 parts data:', response.status)
        setTop10Data(null)
      }
    } catch (error) {
      console.error('Error fetching top 10 parts data:', error)
      setTop10Data(null)
    } finally {
      setTop10Loading(false)
    }
  }

  const fetchPaceData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts/pace'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setPaceData(data)
      }
    } catch (error) {
      console.error('Error fetching parts pace data:', error)
    }
  }

  const fetchOpenWorkOrdersData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts/open-work-orders'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setOpenWorkOrdersData(data)
      }
    } catch (error) {
      console.error('Error fetching open parts work orders data:', error)
    }
  }

  const fetchOpenWorkOrdersDetails = async () => {
    try {
      setDetailsLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts/open-work-orders-details'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setOpenWorkOrdersDetails(data)
      }
    } catch (error) {
      console.error('Error fetching open work order details:', error)
    } finally {
      setDetailsLoading(false)
    }
  }

  const exportToCSV = () => {
    if (!openWorkOrdersDetails) return
    
    const headers = ['WO#', 'Opened', 'Days Open', 'Customer', 'Parts Count', 'Part Numbers', 'Parts Value', 'Misc', 'Total']
    const rows = openWorkOrdersDetails.work_orders.map(wo => [
      wo.wo_number,
      wo.open_date,
      wo.days_open,
      wo.customer_name,
      wo.parts_count,
      wo.parts_list,
      wo.parts_total.toFixed(2),
      wo.misc_total.toFixed(2),
      wo.total_value.toFixed(2)
    ])
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => {
        const cellStr = String(cell)
        if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
          return `"${cellStr.replace(/"/g, '""')}"`
        }
        return cellStr
      }).join(','))
    ].join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    const today = new Date().toISOString().split('T')[0]
    link.setAttribute('href', url)
    link.setAttribute('download', `parts_open_work_orders_${today}.csv`)
    link.style.visibility = 'hidden'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
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
              fill={paceData.pace_percentage > 0 ? '#10b981' : '#ef4444'}
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
              {paceData.pace_percentage > 0 ? '+' : ''}{paceData.pace_percentage}%
            </text>
            {/* Arrow icon */}
            {paceData.pace_percentage !== 0 && (
              <text 
                x={x + width / 2} 
                y={y - 25} 
                textAnchor="middle" 
                fill={paceData.pace_percentage > 0 ? '#10b981' : '#ef4444'}
                fontSize="16"
              >
                {paceData.pace_percentage > 0 ? '↑' : '↓'}
              </text>
            )}
          </g>
        )}
      </g>
    )
  }

  const downloadForecast = () => {
    if (!forecastData || !forecastData.forecasts) return

    // Prepare CSV content
    const headers = [
      'Part Number',
      'Description',
      'Demand Trend',
      'Current Stock',
      'On Order',
      'Avg Monthly Demand',
      'Forecast Demand (90 days)',
      'Safety Stock',
      'Order Recommendation',
      'Unit Cost',
      'Forecast Value',
      'Equipment Count'
    ]

    const rows = forecastData.forecasts.map(part => [
      part.partNo,
      part.description,
      part.demandTrend,
      Math.round(part.currentStock),
      Math.round(part.onOrder),
      part.avgMonthlyDemand.toFixed(1),
      part.forecastDemand,
      part.safetyStock,
      part.orderRecommendation,
      part.unitCost.toFixed(2),
      part.forecastValue.toFixed(2),
      part.equipmentCount
    ])

    // Create CSV content
    const csvContent = [
      headers.join(','),
      ...rows.map(row => 
        row.map(cell => 
          typeof cell === 'string' && cell.includes(',') 
            ? `"${cell}"` 
            : cell
        ).join(',')
      )
    ].join('\n')

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    link.setAttribute('href', url)
    link.setAttribute('download', `parts_demand_forecast_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const downloadReorderAlerts = () => {
    if (!reorderAlertData || !reorderAlertData.alerts) return

    // Prepare CSV content
    const headers = [
      'Part Number',
      'Description',
      'Alert Level',
      'Current Stock',
      'On Order',
      'Days of Stock',
      'Avg Daily Usage',
      'Reorder Point',
      'Suggested Order Qty',
      'Unit Cost',
      'List Price',
      'Orders Last 90 Days'
    ]

    const rows = reorderAlertData.alerts.map(alert => [
      alert.partNo,
      alert.description,
      alert.alertLevel,
      Math.round(alert.currentStock),
      Math.round(alert.onOrder),
      alert.daysOfStock === 999 ? 'Unlimited' : alert.daysOfStock,
      alert.avgDailyUsage.toFixed(2),
      alert.suggestedReorderPoint,
      alert.suggestedOrderQty,
      alert.cost.toFixed(2),
      alert.listPrice.toFixed(2),
      alert.ordersLast90Days
    ])

    // Create CSV content
    const csvContent = [
      headers.join(','),
      ...rows.map(row => 
        row.map(cell => 
          typeof cell === 'string' && cell.includes(',') 
            ? `"${cell}"` 
            : cell
        ).join(',')
      )
    ].join('\n')

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    link.setAttribute('href', url)
    link.setAttribute('download', `parts_reorder_alerts_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }


  if (loading) {
    return (
      <LoadingSpinner 
        title="Loading Parts Department" 
        description="Fetching parts data..."
        size="large"
      />
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Parts Department</h1>
        <p className="text-muted-foreground">Monitor parts sales and inventory performance</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList>
          {tabs.map(tab => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {tabs.some(tab => tab.value === 'overview') && (
          <TabsContent value="overview" className="space-y-6">
          {/* Parts Pace Analysis Card */}
          {paceData?.adaptive_comparisons && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  Parts Sales Pace Analysis
                  {paceData.adaptive_comparisons.performance_indicators?.is_best_month_ever && (
                    <Badge variant="success" className="ml-2">Best Month Ever! 🏆</Badge>
                  )}
                </CardTitle>
                <CardDescription>
                  Multiple comparison perspectives ({paceData.adaptive_comparisons.available_months_count} months of data available)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-3">
                  {/* Previous Month Comparison */}
                  <div className="space-y-2">
                    <h4 className="font-medium text-sm text-muted-foreground">vs Previous Month</h4>
                    <div className="flex items-center gap-2">
                      <div className={`text-2xl font-bold ${paceData.pace_percentage > 0 ? 'text-green-600' : paceData.pace_percentage < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                        {paceData.pace_percentage > 0 ? '+' : ''}{paceData.pace_percentage}%
                      </div>
                      {paceData.pace_percentage > 0 ? (
                        <TrendingUp className="h-4 w-4 text-green-600" />
                      ) : paceData.pace_percentage < 0 ? (
                        <TrendingDown className="h-4 w-4 text-red-600" />
                      ) : null}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {paceData.comparison_base === 'full_previous_month' ? 'vs Full Previous Month' : 'vs Same Day Previous Month'}
                    </p>
                  </div>

                  {/* Available Average Comparison */}
                  {paceData.adaptive_comparisons.vs_available_average?.percentage !== null && (
                    <div className="space-y-2">
                      <h4 className="font-medium text-sm text-muted-foreground">vs Average Performance</h4>
                      <div className="flex items-center gap-2">
                        <div className={`text-2xl font-bold ${paceData.adaptive_comparisons.vs_available_average.percentage > 0 ? 'text-green-600' : paceData.adaptive_comparisons.vs_available_average.percentage < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                          {paceData.adaptive_comparisons.vs_available_average.percentage > 0 ? '+' : ''}{paceData.adaptive_comparisons.vs_available_average.percentage}%
                        </div>
                        {paceData.adaptive_comparisons.vs_available_average.percentage > 0 ? (
                          <TrendingUp className="h-4 w-4 text-green-600" />
                        ) : paceData.adaptive_comparisons.vs_available_average.percentage < 0 ? (
                          <TrendingDown className="h-4 w-4 text-red-600" />
                        ) : null}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Avg: {formatCurrency(paceData.adaptive_comparisons.vs_available_average.average_monthly_sales)}
                      </p>
                    </div>
                  )}

                  {/* Same Month Last Year or Performance Indicators */}
                  <div className="space-y-2">
                    {paceData.adaptive_comparisons.vs_same_month_last_year?.percentage !== null ? (
                      <>
                        <h4 className="font-medium text-sm text-muted-foreground">vs Same Month Last Year</h4>
                        <div className="flex items-center gap-2">
                          <div className={`text-2xl font-bold ${paceData.adaptive_comparisons.vs_same_month_last_year.percentage > 0 ? 'text-green-600' : paceData.adaptive_comparisons.vs_same_month_last_year.percentage < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                            {paceData.adaptive_comparisons.vs_same_month_last_year.percentage > 0 ? '+' : ''}{paceData.adaptive_comparisons.vs_same_month_last_year.percentage}%
                          </div>
                          {paceData.adaptive_comparisons.vs_same_month_last_year.percentage > 0 ? (
                            <TrendingUp className="h-4 w-4 text-green-600" />
                          ) : paceData.adaptive_comparisons.vs_same_month_last_year.percentage < 0 ? (
                            <TrendingDown className="h-4 w-4 text-red-600" />
                          ) : null}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Last Year: {formatCurrency(paceData.adaptive_comparisons.vs_same_month_last_year.last_year_sales)}
                        </p>
                      </>
                    ) : (
                      <>
                        <h4 className="font-medium text-sm text-muted-foreground">Performance Range</h4>
                        <div className="space-y-1">
                          {paceData.adaptive_comparisons.performance_indicators?.vs_best_percentage !== null && (
                            <div className="text-sm">
                              <span className="text-muted-foreground">vs Best:</span>
                              <span className={`ml-2 font-medium ${paceData.adaptive_comparisons.performance_indicators.vs_best_percentage > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {paceData.adaptive_comparisons.performance_indicators.vs_best_percentage > 0 ? '+' : ''}{paceData.adaptive_comparisons.performance_indicators.vs_best_percentage}%
                              </span>
                            </div>
                          )}
                          {paceData.adaptive_comparisons.performance_indicators?.vs_worst_percentage !== null && (
                            <div className="text-sm">
                              <span className="text-muted-foreground">vs Worst:</span>
                              <span className="ml-2 font-medium text-green-600">
                                +{paceData.adaptive_comparisons.performance_indicators.vs_worst_percentage}%
                              </span>
                            </div>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Monthly Parts Revenue */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle>Monthly Parts Revenue & Margin</CardTitle>
                  <CardDescription>Parts revenue and gross margin % over the last 12 months</CardDescription>
                </div>
                {partsData?.monthlyPartsRevenue && partsData.monthlyPartsRevenue.length > 0 && (() => {
                  // Only include historical months (before current month)
                  const currentDate = new Date()
                  const currentMonthIndex = currentDate.getMonth()
                  const currentYear = currentDate.getFullYear()
                  
                  // Month names in order
                  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                  const currentMonthName = monthNames[currentMonthIndex]
                  
                  // Get index of current month in the data
                  const currentMonthDataIndex = partsData.monthlyPartsRevenue.findIndex(item => item.month === currentMonthName)
                  
                  // Filter to only include months before current month with positive revenue
                  const historicalMonths = currentMonthDataIndex > 0 
                    ? partsData.monthlyPartsRevenue.slice(0, currentMonthDataIndex).filter(item => item.amount > 0)
                    : partsData.monthlyPartsRevenue.filter(item => item.amount > 0 && item.month !== currentMonthName)
                  
                  const avgRevenue = historicalMonths.length > 0 ? 
                    historicalMonths.reduce((sum, item) => sum + item.amount, 0) / historicalMonths.length : 0
                  const avgMargin = historicalMonths.length > 0 ? 
                    historicalMonths.reduce((sum, item) => sum + (item.margin || 0), 0) / historicalMonths.length : 0
                  
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
                <ComposedChart data={calculateLinearTrend(sortedMonthlyRevenue, 'month', 'amount')} margin={{ top: 40, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                  <RechartsTooltip 
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length && partsData?.monthlyPartsRevenue) {
                        const data = partsData.monthlyPartsRevenue
                        const currentIndex = data.findIndex(item => item.month === label)
                        const currentData = data[currentIndex]
                        const previousData = currentIndex > 0 ? data[currentIndex - 1] : null
                        
                        return (
                          <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                            <p className="font-semibold mb-2">{label}</p>
                            <div className="space-y-1">
                              <p className="text-green-600">
                                Revenue: {formatCurrency(currentData.amount)}
                                {formatPercentage(calculatePercentageChange(currentData.amount, previousData?.amount))}
                              </p>
                              {currentData.margin !== null && currentData.margin !== undefined && (
                                <p className="text-amber-600">
                                  Margin: {currentData.margin}%
                                  {previousData && previousData.margin !== null && previousData.margin !== undefined && (
                                    <span className={`ml-2 text-sm ${currentData.margin > previousData.margin ? 'text-green-600' : 'text-red-600'}`}>
                                      ({currentData.margin > previousData.margin ? '+' : ''}{(currentData.margin - previousData.margin).toFixed(1)}pp)
                                    </span>
                                  )}
                                </p>
                              )}
                            </div>
                          </div>
                        )
                      }
                      return null
                    }}
                  />
                  <Bar dataKey="amount" fill="#10b981" shape={<CustomBar />} />
                  <Line type="monotone" dataKey="trendValue" stroke="#8b5cf6" strokeWidth={2} strokeDasharray="5 5" name="Revenue Trend" dot={false} />
                  {partsData?.monthlyPartsRevenue && partsData.monthlyPartsRevenue.length > 0 && (() => {
                    // Only calculate average for complete months (exclude current month - August)
                    const completeMonths = partsData.monthlyPartsRevenue.slice(0, -1)
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
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Top 10 Parts */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Top 10 Parts by Quantity (excluding fluids)
              </CardTitle>
              <CardDescription>
                {top10Data?.period || 'Last 30 days'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {top10Loading ? (
                <LoadingSpinner />
              ) : top10Data && top10Data.topParts && top10Data.topParts.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[50px]">Rank</TableHead>
                      <TableHead>Part Number</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Qty Sold</TableHead>
                      <TableHead className="text-center">Orders</TableHead>
                      <TableHead className="text-right">Revenue</TableHead>
                      <TableHead className="text-center">Stock Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {top10Data.topParts.map((part, index) => (
                      <TableRow key={part.partNo}>
                        <TableCell className="font-medium">#{index + 1}</TableCell>
                        <TableCell className="font-medium">{part.partNo}</TableCell>
                        <TableCell>{part.description}</TableCell>
                        <TableCell className="text-right font-medium text-lg">{Math.round(part.totalQuantity).toLocaleString()}</TableCell>
                        <TableCell className="text-center">{part.orderCount}</TableCell>
                        <TableCell className="text-right">
                          ${part.totalRevenue.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge 
                            variant={
                              part.stockStatus === 'Out of Stock' ? 'destructive' :
                              part.stockStatus === 'Low Stock' ? 'secondary' : 'outline'
                            }
                            className={
                              part.stockStatus === 'Low Stock' ? 'bg-yellow-500 hover:bg-yellow-600' : ''
                            }
                          >
                            {part.stockStatus}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No parts data available for this period
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        )}

        {tabs.some(tab => tab.value === 'work-orders') && (
          <TabsContent value="work-orders" className="space-y-6">
          {/* Open Parts Work Orders Card */}
          {openWorkOrdersData && openWorkOrdersData.count > 0 && (
            <Card className="border-2 border-blue-400 bg-blue-50">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-lg">Open Parts Work Orders</CardTitle>
                    <Package className="h-5 w-5 text-blue-600" />
                  </div>
                  <Badge variant="default" className="bg-blue-600">
                    {openWorkOrdersData.count} work orders
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Value</p>
                    <p className="text-2xl font-bold text-blue-900">{formatCurrency(openWorkOrdersData.total_value)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Avg Days Open</p>
                    <p className="text-2xl font-bold flex items-center gap-1 text-blue-900">
                      <Clock className="h-5 w-5" />
                      {openWorkOrdersData.avg_days_open.toFixed(0)} days
                    </p>
                  </div>
                </div>
                {openWorkOrdersData.avg_days_open > 7 && (
                  <div className="pt-3 border-t">
                    <div className="flex items-center gap-2 text-sm">
                      <AlertTriangle className="h-4 w-4 text-amber-600" />
                      <span className="text-amber-700">
                        Average work order has been open for over a week
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Open Work Orders Details Report */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Open Work Orders Details</CardTitle>
                  <CardDescription>Detailed list of all open Parts work orders</CardDescription>
                </div>
                {openWorkOrdersDetails && (
                  <Button onClick={exportToCSV} size="sm" variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Export to CSV
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {detailsLoading ? (
                <div className="flex items-center justify-center h-64">
                  <LoadingSpinner />
                </div>
              ) : openWorkOrdersDetails ? (
                <div className="space-y-4">
                  {/* Summary Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Total WOs</p>
                      <p className="text-xl font-bold">{openWorkOrdersDetails.summary.count}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Total Value</p>
                      <p className="text-xl font-bold">{formatCurrency(openWorkOrdersDetails.summary.total_value)}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Avg Days</p>
                      <p className="text-xl font-bold text-amber-600">{openWorkOrdersDetails.summary.avg_days_open}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">&gt;7 Days</p>
                      <p className="text-xl font-bold text-orange-600">{openWorkOrdersDetails.summary.over_7_days}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">&gt;14 Days</p>
                      <p className="text-xl font-bold text-red-600">{openWorkOrdersDetails.summary.over_14_days}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">&gt;30 Days</p>
                      <p className="text-xl font-bold text-red-900">{openWorkOrdersDetails.summary.over_30_days}</p>
                    </div>
                  </div>

                  {/* Table */}
                  <div className="overflow-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>WO#</TableHead>
                          <TableHead>Opened</TableHead>
                          <TableHead className="text-center">Days Open</TableHead>
                          <TableHead>Customer</TableHead>
                          <TableHead className="text-center">Parts Count</TableHead>
                          <TableHead>Part Numbers</TableHead>
                          <TableHead className="text-right">Parts Value</TableHead>
                          <TableHead className="text-right">Misc</TableHead>
                          <TableHead className="text-right">Total</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {openWorkOrdersDetails.work_orders.map((wo) => (
                          <TableRow 
                            key={wo.wo_number}
                            className={wo.days_open > 30 ? 'bg-red-50' : wo.days_open > 14 ? 'bg-orange-50' : wo.days_open > 7 ? 'bg-yellow-50' : ''}
                          >
                            <TableCell className="font-medium">{wo.wo_number}</TableCell>
                            <TableCell>{wo.open_date}</TableCell>
                            <TableCell className="text-center">
                              <Badge 
                                variant={wo.days_open > 30 ? "destructive" : wo.days_open > 14 ? "warning" : wo.days_open > 7 ? "secondary" : "outline"}
                                className="font-mono"
                              >
                                {wo.days_open}d
                              </Badge>
                            </TableCell>
                            <TableCell className="max-w-[200px] truncate" title={wo.customer_name}>
                              {wo.customer_name}
                            </TableCell>
                            <TableCell className="text-center">
                              <Badge variant="outline">
                                {wo.parts_count}
                              </Badge>
                            </TableCell>
                            <TableCell className="max-w-[300px] truncate" title={wo.parts_list}>
                              {wo.parts_list}
                            </TableCell>
                            <TableCell className="text-right">{formatCurrency(wo.parts_total)}</TableCell>
                            <TableCell className="text-right">{formatCurrency(wo.misc_total)}</TableCell>
                            <TableCell className="text-right font-medium">{formatCurrency(wo.total_value)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Loading work order details...
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        )}

        {tabs.some(tab => tab.value === 'stock-alerts') && (
        <TabsContent value="stock-alerts" className="space-y-6">
          {/* Parts Fill Rate Card */}
          {fillRateData && (
            <Card>
              <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Linde Parts Fill Rate
              </span>
              <Badge variant={fillRateData.summary?.fillRate >= 90 ? "success" : "destructive"}>
                {fillRateData.summary?.fillRate?.toFixed(1)}%
              </Badge>
            </CardTitle>
            <CardDescription>
              {fillRateData.period} - Target: 90% fill rate
            </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{fillRateData.summary?.totalOrders || 0}</p>
                <p className="text-sm text-muted-foreground">Total Orders</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{fillRateData.summary?.filledOrders || 0}</p>
                <p className="text-sm text-muted-foreground">Filled Orders</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{fillRateData.summary?.unfilledOrders || 0}</p>
                <p className="text-sm text-muted-foreground">Stockouts</p>
              </div>
            </div>

            {/* Fill Rate Trend */}
            {fillRateData.fillRateTrend && fillRateData.fillRateTrend.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Fill Rate Trend</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={fillRateData.fillRateTrend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis domain={[0, 100]} />
                    <RechartsTooltip 
                      formatter={(value, name) => {
                        if (name === 'fillRate') return `${value.toFixed(1)}%`
                        return value
                      }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="fillRate" 
                      stroke="#10b981" 
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Problem Parts Table */}
            {fillRateData.problemParts && fillRateData.problemParts.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Parts Frequently Out of Stock</h4>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Part Number</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Stockouts</TableHead>
                      <TableHead className="text-right">Current Stock</TableHead>
                      <TableHead className="text-right">Stockout Rate</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fillRateData.problemParts.map((part) => (
                      <TableRow key={part.partNo}>
                        <TableCell className="font-medium">{part.partNo}</TableCell>
                        <TableCell>{part.description}</TableCell>
                        <TableCell className="text-right">
                          {part.stockoutCount} / {part.totalOrders}
                        </TableCell>
                        <TableCell className="text-right">{Math.round(part.currentStock)}</TableCell>
                        <TableCell className="text-right">
                          <Badge variant={part.stockoutRate > 20 ? "destructive" : "secondary"}>
                            {part.stockoutRate.toFixed(1)}%
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
            </Card>
          )}

          {/* Reorder Alert Card */}
          {reorderAlertData && (
            <Card>
              <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Parts Reorder Alerts
              </span>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="default"
                  onClick={downloadReorderAlerts}
                  className="bg-green-600 hover:bg-green-700"
                  title="Download to Excel"
                >
                  <Download className="h-4 w-4 mr-1" />
                  Excel
                </Button>
                <Badge variant="destructive" className="flex items-center gap-1">
                  <span className="text-xs">Out of Stock</span>
                  <span className="font-bold">{reorderAlertData.summary?.outOfStock || 0}</span>
                </Badge>
                <Badge variant="destructive" className="bg-orange-500 flex items-center gap-1">
                  <span className="text-xs">Critical</span>
                  <span className="font-bold">{reorderAlertData.summary?.critical || 0}</span>
                </Badge>
                <Badge variant="secondary" className="flex items-center gap-1">
                  <span className="text-xs">Low</span>
                  <span className="font-bold">{reorderAlertData.summary?.low || 0}</span>
                </Badge>
              </div>
            </CardTitle>
            <CardDescription>
              Parts needing reorder based on {reorderAlertData.analysisInfo?.period} usage • Lead time: {reorderAlertData.leadTimeAssumption} days
            </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
            {/* Alert Summary Stats */}
            <div className="grid grid-cols-5 gap-4 text-center">
              <div>
                <p className="text-sm text-muted-foreground">Tracked Parts</p>
                <p className="text-2xl font-bold">{reorderAlertData.summary?.totalTracked || 0}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Out of Stock</p>
                <p className="text-2xl font-bold text-red-600">{reorderAlertData.summary?.outOfStock || 0}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Critical (&lt;7 days)</p>
                <p className="text-2xl font-bold text-orange-600">{reorderAlertData.summary?.critical || 0}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Low (&lt;14 days)</p>
                <p className="text-2xl font-bold text-yellow-600">{reorderAlertData.summary?.low || 0}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Need Reorder</p>
                <p className="text-2xl font-bold text-blue-600">{reorderAlertData.summary?.needsReorder || 0}</p>
              </div>
            </div>

            {/* Reorder Alerts Table */}
            {reorderAlertData.alerts && reorderAlertData.alerts.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Parts Requiring Immediate Attention</h4>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Part Number</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-center">Alert</TableHead>
                      <TableHead className="text-right">Stock</TableHead>
                      <TableHead className="text-right">Days Left</TableHead>
                      <TableHead className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          Daily Usage
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger>
                                <Info className="h-3 w-3 text-muted-foreground" />
                              </TooltipTrigger>
                              <TooltipContent className="max-w-xs">
                                <p>Average quantity consumed per day over the last 90 days. Calculated by dividing total quantity used by the number of days in the period.</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                      </TableHead>
                      <TableHead className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          Reorder Point
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger>
                                <Info className="h-3 w-3 text-muted-foreground" />
                              </TooltipTrigger>
                              <TooltipContent className="max-w-xs">
                                <p>The inventory level that triggers a new order. Calculated as: (14 days lead time + 7 days safety stock) × Average Daily Usage. When stock drops below this point, it's time to reorder.</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                      </TableHead>
                      <TableHead className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          Order Qty
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger>
                                <Info className="h-3 w-3 text-muted-foreground" />
                              </TooltipTrigger>
                              <TooltipContent className="max-w-xs">
                                <p>Suggested order quantity to maintain adequate stock. Calculated as 30 days × Average Daily Usage, providing approximately one month of inventory after considering lead time.</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reorderAlertData.alerts.map((alert) => (
                      <TableRow key={alert.partNo}>
                        <TableCell className="font-medium">{alert.partNo}</TableCell>
                        <TableCell>{alert.description}</TableCell>
                        <TableCell className="text-center">
                          <Badge 
                            variant={
                              alert.alertLevel === 'Out of Stock' ? 'destructive' :
                              alert.alertLevel === 'Critical' ? 'destructive' :
                              alert.alertLevel === 'Low' ? 'secondary' : 'default'
                            }
                            className={
                              alert.alertLevel === 'Critical' ? 'bg-orange-500' :
                              alert.alertLevel === 'Low' ? 'bg-yellow-500' : ''
                            }
                          >
                            {alert.alertLevel}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          {Math.round(alert.currentStock)}
                          {alert.onOrder > 0 && (
                            <span className="text-sm text-muted-foreground ml-1">
                              (+{Math.round(alert.onOrder)})
                            </span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <span className={alert.daysOfStock < 7 ? 'text-red-600 font-bold' : ''}>
                            {alert.daysOfStock === 999 ? '∞' : alert.daysOfStock}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">{alert.avgDailyUsage.toFixed(1)}</TableCell>
                        <TableCell className="text-right">{alert.suggestedReorderPoint}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1">
                            <ShoppingCart className="h-4 w-4 text-muted-foreground" />
                            {alert.suggestedOrderQty}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}

            {/* Calculation Info */}
            <div className="text-sm text-muted-foreground border-t pt-4">
              <p><strong>Reorder Formula:</strong> {reorderAlertData.analysisInfo?.reorderFormula}</p>
              <p className="mt-1">Safety Stock: {reorderAlertData.safetyStockDays} days • Lead Time: {reorderAlertData.leadTimeAssumption} days</p>
            </div>
          </CardContent>
            </Card>
          )}
        </TabsContent>
        )}

        {tabs.some(tab => tab.value === 'velocity') && (
        <TabsContent value="velocity" className="space-y-6">
          {/* Parts Velocity Analysis */}
          {velocityData && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  Parts Velocity Analysis
                </CardTitle>
                <CardDescription>
                  Inventory turnover and movement patterns • {velocityData.analysisInfo?.period}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Velocity Summary Cards */}
                <div className="grid grid-cols-4 gap-4">
                  {Object.entries(velocityData.summary || {}).map(([category, data]) => {
                    const getCategoryColor = (cat) => {
                      if (cat === 'Very Fast' || cat === 'Fast') return 'text-green-600'
                      if (cat === 'Medium') return 'text-blue-600'
                      if (cat === 'Slow' || cat === 'Very Slow') return 'text-yellow-600'
                      if (cat === 'Dead Stock' || cat === 'No Movement') return 'text-red-600'
                      return 'text-gray-600'
                    }
                    
                    const getCategoryIcon = (cat) => {
                      if (cat === 'Very Fast' || cat === 'Fast') return <Zap className="h-4 w-4" />
                      if (cat === 'Dead Stock' || cat === 'No Movement') return <Turtle className="h-4 w-4" />
                      return <Clock className="h-4 w-4" />
                    }
                    
                    return (
                      <div 
                        key={category} 
                        className="border rounded-lg p-3 cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={() => {
                          setSelectedCategory(category)
                          setCategoryModalOpen(true)
                        }}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className={`flex items-center gap-1 text-sm font-medium ${getCategoryColor(category)}`}>
                            {getCategoryIcon(category)}
                            {category}
                          </span>
                          <Badge variant="secondary">{data.partCount}</Badge>
                        </div>
                        <p className="text-lg font-bold">${(data.totalValue / 1000).toFixed(1)}k</p>
                        <p className="text-xs text-muted-foreground">
                          {data.avgTurnoverRate > 0 ? `${data.avgTurnoverRate.toFixed(1)}x/yr` : 'No turnover'}
                        </p>
                      </div>
                    )
                  })}
                </div>

                {/* Movement Trend Chart */}
                {velocityData.movementTrend && velocityData.movementTrend.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2">Monthly Parts Movement Trend</h4>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={velocityData.movementTrend}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis yAxisId="left" orientation="left" />
                        <YAxis yAxisId="right" orientation="right" />
                        <RechartsTooltip />
                        <Line 
                          yAxisId="left"
                          type="monotone" 
                          dataKey="totalQuantity" 
                          stroke="#10b981" 
                          name="Total Quantity"
                        />
                        <Line 
                          yAxisId="right"
                          type="monotone" 
                          dataKey="uniqueParts" 
                          stroke="#3b82f6" 
                          name="Unique Parts"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Parts List Table */}
                {velocityData.parts && velocityData.parts.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">High Value Inventory Analysis</h4>
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger>
                            <Info className="h-4 w-4 text-muted-foreground" />
                          </TooltipTrigger>
                          <TooltipContent className="max-w-md">
                            <div className="space-y-2">
                              <p className="font-semibold">Velocity Categories:</p>
                              {Object.entries(velocityData.analysisInfo?.velocityCategories || {}).map(([cat, desc]) => (
                                <p key={cat} className="text-sm">
                                  <span className="font-medium">{cat}:</span> {desc}
                                </p>
                              ))}
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Part Number</TableHead>
                          <TableHead>Description</TableHead>
                          <TableHead className="text-center">Velocity</TableHead>
                          <TableHead className="text-center">Health</TableHead>
                          <TableHead className="text-right">Stock</TableHead>
                          <TableHead className="text-right">Value</TableHead>
                          <TableHead className="text-right">Turnover</TableHead>
                          <TableHead className="text-right">Last Move</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {velocityData.parts.slice(0, 20).map((part) => (
                          <TableRow key={part.partNo}>
                            <TableCell className="font-medium">{part.partNo}</TableCell>
                            <TableCell>{part.description}</TableCell>
                            <TableCell className="text-center">
                              <Badge 
                                variant={
                                  part.velocityCategory === 'Very Fast' || part.velocityCategory === 'Fast' ? 'success' :
                                  part.velocityCategory === 'Medium' ? 'default' :
                                  part.velocityCategory === 'Dead Stock' || part.velocityCategory === 'No Movement' ? 'destructive' :
                                  'secondary'
                                }
                              >
                                {part.velocityCategory}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-center">
                              <Badge 
                                variant={
                                  part.stockHealth === 'Normal' ? 'outline' :
                                  part.stockHealth === 'Stockout Risk' ? 'destructive' :
                                  'secondary'
                                }
                                className={
                                  part.stockHealth === 'Obsolete Risk' ? 'bg-orange-500' :
                                  part.stockHealth === 'Overstock Risk' ? 'bg-yellow-500' : ''
                                }
                              >
                                {part.stockHealth}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">{Math.round(part.currentStock)}</TableCell>
                            <TableCell className="text-right">${part.inventoryValue.toFixed(0)}</TableCell>
                            <TableCell className="text-right">
                              {part.annualTurnoverRate > 0 ? `${part.annualTurnoverRate.toFixed(1)}x` : '-'}
                            </TableCell>
                            <TableCell className="text-right">
                              {part.daysSinceLastMovement !== null ? `${part.daysSinceLastMovement}d` : 'Never'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>
        )}

        {tabs.some(tab => tab.value === 'forecast') && (
        <TabsContent value="forecast" className="space-y-6">
          {/* Parts Demand Forecast */}
          {forecastLoading ? (
            <LoadingSpinner 
              title="Loading Forecast Data" 
              description="Analyzing demand patterns..."
            />
          ) : forecastData ? (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Order Now</p>
                        <p className="text-2xl font-bold text-red-600">{forecastData.summary?.orderNowCount || 0}</p>
                        <p className="text-xs text-muted-foreground mt-1">Critical items</p>
                      </div>
                      <AlertTriangle className="h-8 w-8 text-red-600 opacity-20" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Order Soon</p>
                        <p className="text-2xl font-bold text-orange-600">{forecastData.summary?.orderSoonCount || 0}</p>
                        <p className="text-xs text-muted-foreground mt-1">Within {forecastData.forecastDays || 90} days</p>
                      </div>
                      <Clock className="h-8 w-8 text-orange-600 opacity-20" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Total Parts</p>
                        <p className="text-2xl font-bold">{forecastData.summary?.totalParts || 0}</p>
                        <p className="text-xs text-muted-foreground mt-1">Tracked items</p>
                      </div>
                      <Package className="h-8 w-8 text-blue-600 opacity-20" />
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Forecast Value</p>
                        <p className="text-2xl font-bold">${((forecastData.summary?.totalForecastValue || 0) / 1000).toFixed(1)}k</p>
                        <p className="text-xs text-muted-foreground mt-1">Next {forecastData.forecastDays || 90} days</p>
                      </div>
                      <TrendingUp className="h-8 w-8 text-green-600 opacity-20" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Forecast Table */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Parts Demand Forecast</span>
                    <div className="flex items-center gap-2 text-sm font-normal">
                      <Button
                        size="sm"
                        variant="default"
                        onClick={downloadForecast}
                        className="bg-green-600 hover:bg-green-700"
                        title="Download to Excel"
                      >
                        <Download className="h-4 w-4 mr-1" />
                        Excel
                      </Button>
                      <Badge variant="outline">Lead Time: {forecastData.leadTimeAssumption} days</Badge>
                      <Badge variant="outline">Forecast: {forecastData.forecastDays} days</Badge>
                    </div>
                  </CardTitle>
                  <CardDescription>
                    {forecastData.analysisInfo?.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {forecastData.forecasts && forecastData.forecasts.length > 0 ? (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Part Number</TableHead>
                          <TableHead>Description</TableHead>
                          <TableHead className="text-center">Trend</TableHead>
                          <TableHead className="text-right">Current Stock</TableHead>
                          <TableHead className="text-right">Avg Monthly</TableHead>
                          <TableHead className="text-right">Forecast Demand</TableHead>
                          <TableHead className="text-right">Safety Stock</TableHead>
                          <TableHead className="text-center">Recommendation</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {forecastData.forecasts.map((part) => (
                          <TableRow key={part.partNo}>
                            <TableCell className="font-medium">{part.partNo}</TableCell>
                            <TableCell>{part.description}</TableCell>
                            <TableCell className="text-center">
                              {part.demandTrend === 'Growing' || part.demandTrend === 'Strong Growth' ? (
                                <TrendingUp className="h-4 w-4 text-green-600 inline" />
                              ) : part.demandTrend === 'Declining' || part.demandTrend === 'Declining Fast' ? (
                                <TrendingDown className="h-4 w-4 text-red-600 inline" />
                              ) : (
                                <span className="text-muted-foreground">—</span>
                              )}
                            </TableCell>
                            <TableCell className="text-right">{Math.round(part.currentStock)}</TableCell>
                            <TableCell className="text-right">{part.avgMonthlyDemand.toFixed(1)}</TableCell>
                            <TableCell className="text-right">{part.forecastDemand}</TableCell>
                            <TableCell className="text-right">{part.safetyStock}</TableCell>
                            <TableCell className="text-center">
                              <Badge 
                                variant={
                                  part.orderRecommendation === 'Order Now' ? 'destructive' :
                                  part.orderRecommendation === 'Order Soon' ? 'secondary' : 'outline'
                                }
                                className={
                                  part.orderRecommendation === 'Order Soon' ? 'bg-orange-500 hover:bg-orange-600' : ''
                                }
                              >
                                {part.orderRecommendation}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No parts require forecasting at this time
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <AlertTriangle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-lg font-medium">Unable to load forecast data</p>
                  <p className="text-sm text-muted-foreground mt-2">Please try refreshing the page</p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
        )}

        {tabs.some(tab => tab.value === 'employee-performance') && (
        <TabsContent value="employee-performance" className="space-y-6">
          <PartsEmployeePerformance />
        </TabsContent>
        )}

        {tabs.some(tab => tab.value === 'inventory-location') && (
        <TabsContent value="inventory-location" className="space-y-6">
          <PartsInventoryByLocation />
        </TabsContent>
        )}
        {tabs.some(tab => tab.value === 'inventory-turns') && (
        <TabsContent value="inventory-turns" className="space-y-6">
          <PartsInventoryTurns user={user} />
        </TabsContent>
        )}
      </Tabs>

      {/* Category Parts Modal */}
      <Dialog open={categoryModalOpen} onOpenChange={setCategoryModalOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedCategory && (
                <>
                  {selectedCategory === 'Very Fast' || selectedCategory === 'Fast' ? <Zap className="h-5 w-5 text-green-600" /> :
                   selectedCategory === 'Dead Stock' || selectedCategory === 'No Movement' ? <Turtle className="h-5 w-5 text-red-600" /> :
                   <Clock className="h-5 w-5 text-yellow-600" />}
                  {selectedCategory} Parts
                </>
              )}
            </DialogTitle>
            <DialogDescription>
              {velocityData?.summary[selectedCategory] && (
                <span>
                  {velocityData.summary[selectedCategory].partCount} parts • 
                  ${(velocityData.summary[selectedCategory].totalValue / 1000).toFixed(1)}k total value
                  {velocityData.summary[selectedCategory].avgTurnoverRate > 0 && 
                    ` • ${velocityData.summary[selectedCategory].avgTurnoverRate.toFixed(1)}x average turnover`
                  }
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          
          <div className="mt-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Part Number</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Stock</TableHead>
                  <TableHead className="text-right">Value</TableHead>
                  <TableHead className="text-right">Turnover</TableHead>
                  <TableHead className="text-right">Last Movement</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {velocityData?.parts
                  .filter(part => part.velocityCategory === selectedCategory)
                  .map((part) => (
                    <TableRow key={part.partNo}>
                      <TableCell className="font-medium">{part.partNo}</TableCell>
                      <TableCell>{part.description}</TableCell>
                      <TableCell className="text-right">{Math.round(part.currentStock)}</TableCell>
                      <TableCell className="text-right">${part.inventoryValue.toFixed(0)}</TableCell>
                      <TableCell className="text-right">
                        {part.annualTurnoverRate > 0 ? `${part.annualTurnoverRate.toFixed(1)}x` : '-'}
                      </TableCell>
                      <TableCell className="text-right">
                        {part.daysSinceLastMovement !== null ? `${part.daysSinceLastMovement}d ago` : 'Never'}
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </div>
        </DialogContent>
      </Dialog>

    </div>
  )
}

export default PartsReport