import { useState, useEffect } from 'react'
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

const PartsReport = ({ user, onNavigate }) => {
  const [partsData, setPartsData] = useState(null)
  const [fillRateData, setFillRateData] = useState(null)
  const [reorderAlertData, setReorderAlertData] = useState(null)
  const [velocityData, setVelocityData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [fillRateLoading, setFillRateLoading] = useState(true)
  const [reorderAlertLoading, setReorderAlertLoading] = useState(true)
  const [velocityLoading, setVelocityLoading] = useState(true)
  const [forecastData, setForecastData] = useState(null)
  const [forecastLoading, setForecastLoading] = useState(true)
  const [top10Data, setTop10Data] = useState(null)
  const [top10Loading, setTop10Loading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [categoryModalOpen, setCategoryModalOpen] = useState(false)

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
  }, [])

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

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="stock-alerts">Stock Alerts</TabsTrigger>
          <TabsTrigger value="velocity">Velocity</TabsTrigger>
          <TabsTrigger value="forecast">Forecast</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
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
                <ComposedChart data={(() => {
                  const data = partsData?.monthlyPartsRevenue || []
                  
                  // Calculate averages for reference lines
                  if (data.length > 0) {
                    const currentDate = new Date()
                    const currentMonthIndex = currentDate.getMonth()
                    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    const currentMonthName = monthNames[currentMonthIndex]
                    const currentMonthDataIndex = data.findIndex(item => item.month === currentMonthName)
                    
                    const historicalMonths = currentMonthDataIndex > 0 
                      ? data.slice(0, currentMonthDataIndex).filter(item => item.amount > 0)
                      : data.filter(item => item.amount > 0 && item.month !== currentMonthName)
                    
                    const avgRevenue = historicalMonths.length > 0 ? 
                      historicalMonths.reduce((sum, item) => sum + item.amount, 0) / historicalMonths.length : 0
                    const avgMargin = historicalMonths.length > 0 ? 
                      historicalMonths.reduce((sum, item) => sum + (item.margin || 0), 0) / historicalMonths.length : 0
                    
                    // Add average values to each data point for reference line rendering
                    return data.map(item => ({
                      ...item,
                      avgRevenue: avgRevenue,
                      avgMargin: avgMargin
                    }))
                  }
                  
                  return data
                })()}  margin={{ top: 20, right: 70, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis 
                    yAxisId="revenue"
                    orientation="left"
                    tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                  />
                  <YAxis
                    yAxisId="margin"
                    orientation="right"
                    domain={[0, 100]}
                    tickFormatter={(value) => `${value}%`}
                  />
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
                  <Legend />
                  <Bar yAxisId="revenue" dataKey="amount" fill="#10b981" name="Revenue" />
                  {/* Average Revenue Line */}
                  <Line 
                    yAxisId="revenue"
                    type="monotone"
                    dataKey="avgRevenue"
                    stroke="#666"
                    strokeDasharray="5 5"
                    strokeWidth={2}
                    name="Avg Revenue"
                    dot={false}
                    legendType="none"
                  />
                  {/* Add ReferenceLine for the label */}
                  {partsData?.monthlyPartsRevenue && partsData.monthlyPartsRevenue.length > 0 && (() => {
                    const currentDate = new Date()
                    const currentMonthIndex = currentDate.getMonth()
                    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    const currentMonthName = monthNames[currentMonthIndex]
                    const currentMonthDataIndex = partsData.monthlyPartsRevenue.findIndex(item => item.month === currentMonthName)
                    const historicalMonths = currentMonthDataIndex > 0 
                      ? partsData.monthlyPartsRevenue.slice(0, currentMonthDataIndex).filter(item => item.amount > 0)
                      : partsData.monthlyPartsRevenue.filter(item => item.amount > 0 && item.month !== currentMonthName)
                    const avgRevenue = historicalMonths.length > 0 ? 
                      historicalMonths.reduce((sum, item) => sum + item.amount, 0) / historicalMonths.length : 0
                    
                    if (avgRevenue > 0) {
                      return (
                        <ReferenceLine 
                          yAxisId="revenue"
                          y={avgRevenue} 
                          stroke="none"
                          label={{ value: "Average", position: "insideTopRight" }}
                        />
                      )
                    }
                    return null
                  })()}
                  <Line 
                    yAxisId="margin" 
                    type="monotone" 
                    dataKey="margin" 
                    stroke="#f59e0b" 
                    strokeWidth={3}
                    name="Gross Margin %"
                    dot={(props) => {
                      const { payload } = props;
                      // Only render dots for months with actual margin data
                      if (payload.margin !== null && payload.margin !== undefined) {
                        return <circle {...props} fill="#f59e0b" r={4} />;
                      }
                      return null;
                    }}
                    connectNulls={false}
                  />
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