import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, Clock, Download } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  ReferenceLine,
  ComposedChart,
  Line,
  Legend
} from 'recharts'
import { apiUrl } from '@/lib/api'
import ServiceInvoiceBilling from '../ServiceInvoiceBilling'

const ServiceReport = ({ user, onNavigate }) => {
  const [serviceData, setServiceData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [paceData, setPaceData] = useState(null)
  const [awaitingInvoiceData, setAwaitingInvoiceData] = useState(null)
  const [awaitingInvoiceDetails, setAwaitingInvoiceDetails] = useState(null)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [woLookup, setWoLookup] = useState('')
  const [woDetail, setWoDetail] = useState(null)
  const [loadingWoDetail, setLoadingWoDetail] = useState(false)
  const [notes, setNotes] = useState({})
  const [savingNotes, setSavingNotes] = useState({})

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
    fetchServiceData()
    fetchPaceData()
    fetchAwaitingInvoiceData()
  }, [])

  useEffect(() => {
    // Fetch awaiting invoice details when switching to work orders tab
    if (activeTab === 'work-orders' && !awaitingInvoiceDetails) {
      fetchAwaitingInvoiceDetails()
    }
  }, [activeTab])

  const fetchServiceData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/service'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setServiceData(data)
      } else {
        console.error('Failed to fetch service data:', response.status)
        // Set default empty data structure
        setServiceData({
          monthlyLaborRevenue: []
        })
      }
    } catch (error) {
      console.error('Error fetching service data:', error)
      // Set default empty data structure on error
      setServiceData({
        monthlyLaborRevenue: []
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchPaceData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/service/pace'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setPaceData(data)
      }
    } catch (error) {
      console.error('Error fetching service pace data:', error)
    }
  }

  const fetchAwaitingInvoiceData = async () => {
    try {
      const token = localStorage.getItem('token')
      // Fetch the optimized dashboard data to get awaiting invoice info
      const response = await fetch(apiUrl('/api/reports/dashboard/summary-optimized'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        // Extract just the awaiting invoice data (already filtered for Service in the backend)
        setAwaitingInvoiceData({
          count: data.awaiting_invoice_count,
          value: data.awaiting_invoice_value,
          avg_days: data.awaiting_invoice_avg_days,
          over_three: data.awaiting_invoice_over_three,
          over_five: data.awaiting_invoice_over_five,
          over_seven: data.awaiting_invoice_over_seven
        })
      }
    } catch (error) {
      console.error('Error fetching awaiting invoice data:', error)
    }
  }

  const fetchAwaitingInvoiceDetails = async () => {
    try {
      setDetailsLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/service/awaiting-invoice-details'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setAwaitingInvoiceDetails(data)
        
        // Fetch notes for all work orders
        if (data.work_orders && data.work_orders.length > 0) {
          fetchNotesForWorkOrders(data.work_orders.map(wo => wo.wo_number))
        }
      }
    } catch (error) {
      console.error('Error fetching awaiting invoice details:', error)
    } finally {
      setDetailsLoading(false)
    }
  }
  
  const fetchNotesForWorkOrders = async (woNumbers) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/work-orders/notes/batch'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ wo_numbers: woNumbers })
      })
      
      if (response.ok) {
        const notesData = await response.json()
        setNotes(notesData)
      }
    } catch (error) {
      console.error('Error fetching notes:', error)
    }
  }
  
  const saveNote = async (woNumber, noteText) => {
    setSavingNotes(prev => ({ ...prev, [woNumber]: true }))
    
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/work-orders/notes'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          wo_number: woNumber,
          note: noteText
        })
      })
      
      if (response.ok) {
        const savedNote = await response.json()
        setNotes(prev => ({
          ...prev,
          [woNumber]: {
            note: savedNote.note,
            updated_at: savedNote.updated_at,
            updated_by: savedNote.updated_by
          }
        }))
      }
    } catch (error) {
      console.error('Error saving note:', error)
    } finally {
      setSavingNotes(prev => ({ ...prev, [woNumber]: false }))
    }
  }
  
  const handleNoteChange = (woNumber, value) => {
    // Update local state immediately
    setNotes(prev => ({
      ...prev,
      [woNumber]: {
        ...prev[woNumber],
        note: value
      }
    }))
    
    // Debounce the save
    clearTimeout(window.noteSaveTimeout?.[woNumber])
    if (!window.noteSaveTimeout) {
      window.noteSaveTimeout = {}
    }
    window.noteSaveTimeout[woNumber] = setTimeout(() => {
      saveNote(woNumber, value)
    }, 1000) // Auto-save after 1 second of no typing
  }

  const lookupWorkOrder = async () => {
    if (!woLookup.trim()) return
    
    try {
      setLoadingWoDetail(true)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl(`/api/reports/departments/rental/wo-detail/${woLookup.trim()}`), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        if (response.status === 404) {
          setWoDetail({ error: 'Work order not found' })
        } else {
          throw new Error('Failed to fetch work order details')
        }
      } else {
        const data = await response.json()
        setWoDetail(data)
      }
    } catch (err) {
      setWoDetail({ error: err.message || 'An error occurred' })
    } finally {
      setLoadingWoDetail(false)
    }
  }

  const exportToCSV = () => {
    if (!awaitingInvoiceDetails) return
    
    const headers = ['WO#', 'Customer', 'Unit', 'Make/Model', 'Completed', 'Days Waiting', 'Labor', 'Parts', 'Misc', 'Total', 'Notes']
    const rows = awaitingInvoiceDetails.work_orders.map(wo => [
      wo.wo_number,
      wo.customer_name,
      wo.unit_no || '',
      wo.make && wo.model ? `${wo.make} ${wo.model}` : '',
      wo.completed_date,
      wo.days_waiting,
      wo.labor_total.toFixed(2),
      wo.parts_total.toFixed(2),
      wo.misc_total.toFixed(2),
      wo.total_value.toFixed(2),
      notes[wo.wo_number]?.note || ''
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
    link.setAttribute('download', `service_awaiting_invoice_${today}.csv`)
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
      paceData && paceData.pace_percentage !== undefined
    
    return (
      <g>
        <rect x={x} y={y} width={width} height={height} fill={fill} />
        {isCurrentMonth && (
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

  if (loading) {
    return (
      <LoadingSpinner 
        title="Loading Service Department" 
        description="Fetching service data..."
        size="large"
      />
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Service Department</h1>
        <p className="text-muted-foreground">Monitor service operations</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="work-orders">Work Orders</TabsTrigger>
          <TabsTrigger value="invoice-billing">Grede Billing</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Monthly Labor Revenue */}
          <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle>Monthly Labor Revenue & Margin</CardTitle>
              <CardDescription>Labor revenue and gross margin % over the last 12 months</CardDescription>
            </div>
            {serviceData?.monthlyLaborRevenue && serviceData.monthlyLaborRevenue.length > 0 && (() => {
              // Only include historical months (before current month)
              const currentDate = new Date()
              const currentMonthIndex = currentDate.getMonth()
              const currentYear = currentDate.getFullYear()
              
              // Month names in order
              const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
              const currentMonthName = monthNames[currentMonthIndex]
              
              // Get index of current month in the data
              const currentMonthDataIndex = serviceData.monthlyLaborRevenue.findIndex(item => item.month === currentMonthName)
              
              // Filter to only include months before current month with positive revenue
              const historicalMonths = currentMonthDataIndex > 0 
                ? serviceData.monthlyLaborRevenue.slice(0, currentMonthDataIndex).filter(item => item.amount > 0)
                : serviceData.monthlyLaborRevenue.filter(item => item.amount > 0 && item.month !== currentMonthName)
              
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
              const data = serviceData?.monthlyLaborRevenue || []
              
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
                  if (active && payload && payload.length && serviceData?.monthlyLaborRevenue) {
                    const data = serviceData.monthlyLaborRevenue
                    const currentIndex = data.findIndex(item => item.month === label)
                    const currentData = data[currentIndex]
                    const previousData = currentIndex > 0 ? data[currentIndex - 1] : null
                    
                    return (
                      <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                        <p className="font-semibold mb-2">{label}</p>
                        <div className="space-y-1">
                          <p className="text-blue-600">
                            Revenue: {formatCurrency(currentData.amount)}
                            {formatPercentage(calculatePercentageChange(currentData.amount, previousData?.amount))}
                          </p>
                          {currentData.margin !== null && currentData.margin !== undefined && (
                            <p className="text-green-600">
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
              <Bar yAxisId="revenue" dataKey="amount" fill="#3b82f6" name="Revenue" shape={<CustomBar />} />
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
              {serviceData?.monthlyLaborRevenue && serviceData.monthlyLaborRevenue.length > 0 && (() => {
                const currentDate = new Date()
                const currentMonthIndex = currentDate.getMonth()
                const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                const currentMonthName = monthNames[currentMonthIndex]
                const currentMonthDataIndex = serviceData.monthlyLaborRevenue.findIndex(item => item.month === currentMonthName)
                const historicalMonths = currentMonthDataIndex > 0 
                  ? serviceData.monthlyLaborRevenue.slice(0, currentMonthDataIndex).filter(item => item.amount > 0)
                  : serviceData.monthlyLaborRevenue.filter(item => item.amount > 0 && item.month !== currentMonthName)
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
                stroke="#10b981" 
                strokeWidth={3}
                name="Gross Margin %"
                dot={(props) => {
                  const { payload } = props;
                  // Only render dots for months with actual margin data
                  if (payload.margin !== null && payload.margin !== undefined) {
                    return <circle {...props} fill="#10b981" r={4} />;
                  }
                  return null;
                }}
                connectNulls={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="work-orders" className="space-y-6">
          {/* Temporary PostgreSQL diagnostic */}
          
          {/* Service, Shop & PM Work Orders Awaiting Invoice Card */}
          {awaitingInvoiceData && awaitingInvoiceData.count > 0 && (
            <Card 
              className={`border-2 ${awaitingInvoiceData.over_three > 0 ? 'border-orange-400 bg-orange-50' : 'border-yellow-400 bg-yellow-50'}`}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-lg">Service, Shop & PM Work Orders Awaiting Invoice</CardTitle>
                    {awaitingInvoiceData.over_three > 0 && (
                      <AlertTriangle className="h-5 w-5 text-orange-600" />
                    )}
                  </div>
                  <Badge variant={awaitingInvoiceData.over_three > 0 ? "destructive" : "warning"}>
                    {awaitingInvoiceData.count} work orders
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Total Value</p>
                    <p className="font-semibold text-lg">{formatCurrency(awaitingInvoiceData.value)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Avg Days Waiting</p>
                    <p className="font-semibold text-lg flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {awaitingInvoiceData.avg_days.toFixed(1)} days
                    </p>
                  </div>
                </div>
                {awaitingInvoiceData.over_three > 0 && (
                  <div className="pt-2 border-t">
                    <div className="flex items-center gap-2 text-sm">
                      <AlertTriangle className="h-4 w-4 text-orange-600" />
                      <span className="text-orange-700">
                        <strong>{awaitingInvoiceData.over_three}</strong> orders waiting &gt;3 days
                        {awaitingInvoiceData.over_five > 0 && (
                          <span> ({awaitingInvoiceData.over_five} over 5 days)</span>
                        )}
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Awaiting Invoice Details Report */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Work Orders Awaiting Invoice Details</CardTitle>
                  <CardDescription>Detailed list of all completed work orders that have not been invoiced</CardDescription>
                </div>
                {awaitingInvoiceDetails && (
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
              ) : awaitingInvoiceDetails ? (
                <div className="space-y-4">
                  {/* Summary Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Total WOs</p>
                      <p className="text-xl font-bold">{awaitingInvoiceDetails.summary.count}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Total Value</p>
                      <p className="text-xl font-bold">{formatCurrency(awaitingInvoiceDetails.summary.total_value)}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Avg Days</p>
                      <p className="text-xl font-bold text-red-600">{awaitingInvoiceDetails.summary.avg_days_waiting}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">&gt;3 Days</p>
                      <p className="text-xl font-bold text-orange-600">{awaitingInvoiceDetails.summary.over_3_days}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">&gt;5 Days</p>
                      <p className="text-xl font-bold text-red-600">{awaitingInvoiceDetails.summary.over_5_days}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">&gt;7 Days</p>
                      <p className="text-xl font-bold text-red-900">{awaitingInvoiceDetails.summary.over_7_days}</p>
                    </div>
                  </div>

                  {/* Table */}
                  <div className="overflow-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>WO#</TableHead>
                          <TableHead>Customer</TableHead>
                          <TableHead>Unit</TableHead>
                          <TableHead>Make/Model</TableHead>
                          <TableHead>Completed</TableHead>
                          <TableHead className="text-center">Days</TableHead>
                          <TableHead className="text-right">Labor</TableHead>
                          <TableHead className="text-right">Parts</TableHead>
                          <TableHead className="text-right">Misc</TableHead>
                          <TableHead className="text-right">Total</TableHead>
                          <TableHead>Notes</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {awaitingInvoiceDetails.work_orders.map((wo) => (
                          <TableRow 
                            key={wo.wo_number}
                            className={wo.days_waiting > 7 ? 'bg-red-50' : wo.days_waiting > 3 ? 'bg-orange-50' : ''}
                          >
                            <TableCell className="font-medium">{wo.wo_number}</TableCell>
                            <TableCell className="max-w-[200px] truncate" title={wo.customer_name}>
                              {wo.customer_name}
                            </TableCell>
                            <TableCell>{wo.unit_no || '-'}</TableCell>
                            <TableCell className="max-w-[150px] truncate" title={wo.make && wo.model ? `${wo.make} ${wo.model}` : '-'}>
                              {wo.make && wo.model ? `${wo.make} ${wo.model}` : '-'}
                            </TableCell>
                            <TableCell>{wo.completed_date}</TableCell>
                            <TableCell className="text-center">
                              <Badge 
                                variant={wo.days_waiting > 7 ? "destructive" : wo.days_waiting > 3 ? "warning" : "secondary"}
                                className="font-mono"
                              >
                                {wo.days_waiting}d
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">{formatCurrency(wo.labor_total)}</TableCell>
                            <TableCell className="text-right">{formatCurrency(wo.parts_total)}</TableCell>
                            <TableCell className="text-right">{formatCurrency(wo.misc_total)}</TableCell>
                            <TableCell className="text-right font-medium">{formatCurrency(wo.total_value)}</TableCell>
                            <TableCell className="min-w-[200px]">
                              <div className="relative">
                                <textarea
                                  className={`w-full px-2 py-1 text-sm border rounded resize-none ${
                                    savingNotes[wo.wo_number] ? 'bg-yellow-50' : ''
                                  }`}
                                  placeholder="Add notes..."
                                  value={notes[wo.wo_number]?.note || ''}
                                  onChange={(e) => handleNoteChange(wo.wo_number, e.target.value)}
                                  rows={2}
                                />
                                {savingNotes[wo.wo_number] && (
                                  <div className="absolute top-1 right-1 text-xs text-yellow-600">
                                    Saving...
                                  </div>
                                )}
                                {notes[wo.wo_number]?.updated_by && (
                                  <div className="text-xs text-gray-500 mt-1">
                                    Last updated by {notes[wo.wo_number].updated_by}
                                  </div>
                                )}
                              </div>
                            </TableCell>
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

          {/* Work Order Lookup */}
          <Card>
            <CardHeader>
              <CardTitle>Work Order Detail Lookup</CardTitle>
              <CardDescription>
                Look up specific work order details to compare with invoices
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  placeholder="Enter Work Order Number (e.g. S123456)"
                  value={woLookup}
                  onChange={(e) => setWoLookup(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && lookupWorkOrder()}
                  className="flex-1 px-3 py-2 border rounded-md"
                />
                <Button 
                  onClick={lookupWorkOrder}
                  disabled={loadingWoDetail || !woLookup.trim()}
                >
                  {loadingWoDetail ? 'Loading...' : 'Look Up'}
                </Button>
              </div>

              {woDetail && (
                <div className="space-y-4">
                  {woDetail.error ? (
                    <div className="text-red-600">{woDetail.error}</div>
                  ) : (
                    <>
                      {/* Work Order Header */}
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-semibold mb-2">Work Order: {woDetail.workOrder.number}</h4>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>Bill To: {woDetail.workOrder.billTo} - {woDetail.workOrder.customerName}</div>
                          <div>Unit: {woDetail.workOrder.unitNo || 'N/A'}</div>
                          <div>Make/Model: {woDetail.workOrder.make} {woDetail.workOrder.model}</div>
                          <div>Sale Code: {woDetail.workOrder.saleCode}</div>
                        </div>
                      </div>

                      {/* Cost Breakdown */}
                      <div className="space-y-4">
                        {/* Labor */}
                        <div>
                          <h5 className="font-semibold mb-2">Labor Details</h5>
                          {(woDetail.labor.details.length > 0 || woDetail.labor.quoteItems?.length > 0) ? (
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead>Mechanic</TableHead>
                                  <TableHead>Date</TableHead>
                                  <TableHead className="text-right">Hours</TableHead>
                                  <TableHead className="text-right">Cost</TableHead>
                                  <TableHead className="text-right">Sell</TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {woDetail.labor.details.map((item, idx) => (
                                  <TableRow key={idx}>
                                    <TableCell>{item.MechanicName}</TableCell>
                                    <TableCell>{item.DateOfLabor ? new Date(item.DateOfLabor).toLocaleDateString() : 'N/A'}</TableCell>
                                    <TableCell className="text-right">{item.Hours || 0}</TableCell>
                                    <TableCell className="text-right">{formatCurrency(item.Cost || 0)}</TableCell>
                                    <TableCell className="text-right">{formatCurrency(item.Sell || 0)}</TableCell>
                                  </TableRow>
                                ))}
                                {/* Show flat rate labor from quotes */}
                                {woDetail.labor.quoteItems?.map((item, idx) => (
                                  <TableRow key={`quote-${idx}`} className="bg-yellow-50">
                                    <TableCell>Flat Rate Labor</TableCell>
                                    <TableCell>Quote</TableCell>
                                    <TableCell className="text-right">-</TableCell>
                                    <TableCell className="text-right">-</TableCell>
                                    <TableCell className="text-right">{formatCurrency(item.Amount || 0)}</TableCell>
                                  </TableRow>
                                ))}
                                <TableRow className="font-semibold">
                                  <TableCell colSpan={3}>Total Labor</TableCell>
                                  <TableCell className="text-right">{formatCurrency(woDetail.labor.costTotal)}</TableCell>
                                  <TableCell className="text-right">{formatCurrency(woDetail.labor.sellTotal)}</TableCell>
                                </TableRow>
                              </TableBody>
                            </Table>
                          ) : (
                            <p className="text-gray-500">No labor charges</p>
                          )}
                        </div>

                        {/* Parts */}
                        <div>
                          <h5 className="font-semibold mb-2">Parts Details</h5>
                          {woDetail.parts.details.length > 0 ? (
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead>Part #</TableHead>
                                  <TableHead>Description</TableHead>
                                  <TableHead className="text-right">Qty</TableHead>
                                  <TableHead className="text-right">Cost Each</TableHead>
                                  <TableHead className="text-right">Sell Each</TableHead>
                                  <TableHead className="text-right">Extended Sell</TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {woDetail.parts.details.map((item, idx) => (
                                  <TableRow key={idx}>
                                    <TableCell>{item.PartNo}</TableCell>
                                    <TableCell>{item.Description}</TableCell>
                                    <TableCell className="text-right">{item.Qty || 0}</TableCell>
                                    <TableCell className="text-right">{formatCurrency(item.Cost || 0)}</TableCell>
                                    <TableCell className="text-right">{formatCurrency(item.Sell || 0)}</TableCell>
                                    <TableCell className="text-right">{formatCurrency(item.ExtendedSell || 0)}</TableCell>
                                  </TableRow>
                                ))}
                                <TableRow className="font-semibold">
                                  <TableCell colSpan={5}>Total Parts</TableCell>
                                  <TableCell className="text-right">{formatCurrency(woDetail.parts.sellTotal)}</TableCell>
                                </TableRow>
                              </TableBody>
                            </Table>
                          ) : (
                            <p className="text-gray-500">No parts charges</p>
                          )}
                        </div>

                        {/* Misc */}
                        <div>
                          <h5 className="font-semibold mb-2">Misc/Freight Details</h5>
                          {woDetail.misc.details.length > 0 ? (
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead>Description</TableHead>
                                  <TableHead className="text-right">Cost</TableHead>
                                  <TableHead className="text-right">Sell</TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {woDetail.misc.details.map((item, idx) => (
                                  <TableRow key={idx}>
                                    <TableCell>{item.Description}</TableCell>
                                    <TableCell className="text-right">{formatCurrency(item.Cost || 0)}</TableCell>
                                    <TableCell className="text-right">{formatCurrency(item.Sell || 0)}</TableCell>
                                  </TableRow>
                                ))}
                                <TableRow className="font-semibold">
                                  <TableCell>Total Misc</TableCell>
                                  <TableCell className="text-right">{formatCurrency(woDetail.misc.costTotal)}</TableCell>
                                  <TableCell className="text-right">{formatCurrency(woDetail.misc.sellTotal)}</TableCell>
                                </TableRow>
                              </TableBody>
                            </Table>
                          ) : (
                            <p className="text-gray-500">No misc charges</p>
                          )}
                        </div>

                        {/* Summary */}
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                          <h5 className="font-semibold mb-2">Cost vs Sell Comparison</h5>
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span>Total Cost (what we show in report):</span>
                              <span className="font-semibold">{formatCurrency(woDetail.totals.totalCost)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Total Sell Price (what customer is charged):</span>
                              <span className="font-semibold">{formatCurrency(woDetail.totals.totalSell)}</span>
                            </div>
                            <div className="flex justify-between text-red-600">
                              <span>Difference:</span>
                              <span className="font-semibold">
                                {formatCurrency(woDetail.totals.totalSell - woDetail.totals.totalCost)}
                              </span>
                            </div>
                          </div>
                          <p className="text-sm mt-3 text-yellow-800">
                            <strong>Note:</strong> Our report shows internal COST, not the SELL price charged to customers. 
                            This explains why the invoice total ({formatCurrency(woDetail.totals.totalSell)}) 
                            differs from our report total ({formatCurrency(woDetail.totals.totalCost)}).
                          </p>
                        </div>

                        {/* Invoice Data if Available */}
                        {woDetail.invoice && woDetail.invoice.length > 0 && (
                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <h5 className="font-semibold mb-2">Associated Invoice</h5>
                            {woDetail.invoice.map((inv, idx) => (
                              <div key={idx} className="text-sm space-y-1">
                                <p>Invoice #: {inv.InvoiceNo}</p>
                                <p>Date: {new Date(inv.InvoiceDate).toLocaleDateString()}</p>
                                <p>Grand Total: {formatCurrency(inv.GrandTotal)}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="invoice-billing" className="space-y-6">
          <ServiceInvoiceBilling />
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default ServiceReport