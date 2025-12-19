import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, Clock, Download, FileText, TrendingUp, TrendingDown, Info } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
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
  Legend,
  Cell
} from 'recharts'
import { apiUrl } from '@/lib/api'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import ServiceInvoiceBilling from '../ServiceInvoiceBilling'
import WorkOrderTypes from '../WorkOrderTypes'
import PMReport from '../PMReport'
import PMRoutePlanner from '../PMRoutePlanner'
import PMTechnicianContest from './PMTechnicianContest'
import RevenueChart from './RevenueChart'
import MaintenanceContractProfitability from '../MaintenanceContractProfitability'
import CustomerProfitability from '../CustomerProfitability'
import UnitsRepairCost from '../UnitsRepairCost'

// Utility function to calculate linear regression trendline
const calculateLinearTrend = (data, xKey, yKey, excludeCurrentMonth = true) => {
  if (!data || data.length === 0) return []

  // Ensure all data has a numeric value for the yKey, otherwise default to 0
  const cleanedData = data.map(item => ({
    ...item,
    [yKey]: parseFloat(item[yKey]) || 0
  }))

  // Find the index of the first month with actual data
  const firstDataIndex = cleanedData.findIndex(item => item[yKey] > 0)

  if (firstDataIndex === -1) {
    return cleanedData.map(item => ({ ...item, trendValue: null }))
  }

  // Get data from the first month with actual revenue
  const dataFromFirstMonth = cleanedData.slice(firstDataIndex)

  let trendData = dataFromFirstMonth
  if (excludeCurrentMonth && dataFromFirstMonth.length > 1) {
    trendData = dataFromFirstMonth.slice(0, -1)
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
    if (index < firstDataIndex) {
      return { ...item, trendValue: null }
    }
    const adjustedIndex = index - firstDataIndex
    return {
      ...item,
      trendValue: slope * adjustedIndex + intercept
    }
  })
}


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
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedWorkOrder, setSelectedWorkOrder] = useState(null)
  const [modalNote, setModalNote] = useState('')
  // Invoice delay analysis state
  const [invoiceDelayData, setInvoiceDelayData] = useState(null)
  const [invoiceDelayLoading, setInvoiceDelayLoading] = useState(false)
  // Shop work orders state
  const [shopWorkOrders, setShopWorkOrders] = useState(null)
  const [shopWorkOrdersLoading, setShopWorkOrdersLoading] = useState(false)

  // Sort monthly revenue data chronologically for correct trendline calculation
  const sortedMonthlyRevenue = React.useMemo(() => {
    if (!serviceData?.monthlyLaborRevenue) {
      return [];
    }

    const monthOrder = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];

    return [...serviceData.monthlyLaborRevenue].sort((a, b) => {
      return monthOrder.indexOf(a.month) - monthOrder.indexOf(b.month);
    });
  }, [serviceData]);

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
    // Fetch shop work orders when switching to shop work orders tab
    if (activeTab === 'shop-work-orders' && !shopWorkOrders) {
      fetchShopWorkOrders()
    }
    // Fetch awaiting invoice details when switching to work orders tab
    if (activeTab === 'work-orders' && !awaitingInvoiceDetails) {
      fetchAwaitingInvoiceDetails()
    }
    // Fetch invoice delay analysis when switching to all work orders tab
    if (activeTab === 'all-work-orders' && !invoiceDelayData) {
      fetchInvoiceDelayAnalysis()
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
        body: JSON.stringify({ wo_numbers: woNumbers.map(String) })
      })
      
      if (response.ok) {
        const notesData = await response.json()
        console.log('Fetched notes for work orders:', notesData)
        setNotes(notesData)
      } else {
        console.error('Failed to fetch notes:', response.status, response.statusText)
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
          wo_number: String(woNumber),
          note: noteText
        })
      })
      
      if (response.ok) {
        const savedNote = await response.json()
        console.log('Note saved successfully:', savedNote)
        setNotes(prev => ({
          ...prev,
          [woNumber]: {
            note: savedNote.note,
            updated_at: savedNote.updated_at,
            updated_by: savedNote.updated_by
          }
        }))
      } else {
        console.error('Failed to save note:', response.status, response.statusText)
        const errorText = await response.text()
        console.error('Error response:', errorText)
      }
    } catch (error) {
      console.error('Error saving note:', error)
    } finally {
      setSavingNotes(prev => ({ ...prev, [woNumber]: false }))
    }
  }
  
  const openNotesModal = (workOrder) => {
    setSelectedWorkOrder(workOrder)
    setModalNote(notes[workOrder.wo_number]?.note || '')
    setModalOpen(true)
  }

  const handleModalNoteChange = (value) => {
    setModalNote(value)
    
    // Update local state immediately
    if (selectedWorkOrder) {
      setNotes(prev => ({
        ...prev,
        [selectedWorkOrder.wo_number]: {
          ...prev[selectedWorkOrder.wo_number],
          note: value
        }
      }))
      
      // Debounce the save
      if (window.noteSaveTimeout) {
        clearTimeout(window.noteSaveTimeout)
      }
      
      window.noteSaveTimeout = setTimeout(() => {
        saveNote(selectedWorkOrder.wo_number, value)
      }, 1000)
    }
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

  const fetchShopWorkOrders = async () => {
    setShopWorkOrdersLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/service/shop-work-orders'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setShopWorkOrders(data)
      } else {
        console.error('Failed to fetch shop work orders')
      }
    } catch (error) {
      console.error('Error fetching shop work orders:', error)
    } finally {
      setShopWorkOrdersLoading(false)
    }
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
          <TabsTrigger value="pms">PM's</TabsTrigger>
          <TabsTrigger value="pm-route-planner">PM Route Planner</TabsTrigger>
          <TabsTrigger value="pm-contest">PM Contest</TabsTrigger>
          <TabsTrigger value="shop-work-orders">Cash Burn</TabsTrigger>
          <TabsTrigger value="work-orders">Cash Stalled</TabsTrigger>
          <TabsTrigger value="all-work-orders">All Work Orders</TabsTrigger>
          <TabsTrigger value="invoice-billing">Customer Billing</TabsTrigger>
          <TabsTrigger value="maintenance-contracts">Maintenance Contract Profitability</TabsTrigger>
          <TabsTrigger value="customer-profitability">Customer Profitability</TabsTrigger>
          <TabsTrigger value="units-repair-cost">Units by Repair Cost</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Service Pace Analysis Card */}
          {paceData?.adaptive_comparisons && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Service Revenue Pace Analysis
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
                        Avg: {formatCurrency(paceData.adaptive_comparisons.vs_available_average.average_monthly_revenue)}
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
                          Last Year: {formatCurrency(paceData.adaptive_comparisons.vs_same_month_last_year.last_year_revenue)}
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

          {/* Monthly Labor Revenue Charts */}
          <RevenueChart
            data={serviceData?.monthlyLaborRevenue}
            title="Combined Service Revenue & Margin"
            description="Total external customer service revenue (Field + Shop) over the last 12 months"
            tooltipInfo={
              <>
                <p className="font-semibold mb-1">Includes:</p>
                <p className="text-xs mb-2">• Field service (GL 410004)<br/>• Shop service (GL 410005)</p>
                <p className="font-semibold mb-1">Excludes:</p>
                <p className="text-xs">• Internal repairs<br/>• Freight charges<br/>• PM contract labor<br/>• Sublet labor<br/>• Warranty labor<br/>• GM Service</p>
              </>
            }
            barColor="#3b82f6"
          />

          <RevenueChart
            data={serviceData?.monthlyFieldRevenue}
            title="Field Service (GL 410004)"
            description="On-site field service revenue over the last 12 months"
            barColor="#3b82f6"
          />

          <RevenueChart
            data={serviceData?.monthlyShopRevenue}
            title="Shop Service (GL 410005)"
            description="In-shop service revenue over the last 12 months"
            barColor="#1e40af"
          />

          {/* Placeholder Card (will be replaced) */}
          <Card style={{display: 'none'}}>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <CardTitle>Monthly Labor Revenue & Margin</CardTitle>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-sm">
                      <p className="font-semibold mb-1">Includes:</p>
                      <p className="text-xs mb-2">• Field service (GL 410004)<br/>• Shop service (GL 410005)</p>
                      <p className="font-semibold mb-1">Excludes:</p>
                      <p className="text-xs">• Internal repairs<br/>• Freight charges<br/>• PM contract labor<br/>• Sublet labor<br/>• Warranty labor<br/>• GM Service</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <CardDescription>External customer service revenue and gross margin % over the last 12 months</CardDescription>
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
              const data = sortedMonthlyRevenue || []
              
              if (data.length === 0) return data
              
              // Identify complete months (exclude current month)
              const currentDate = new Date()
              const currentMonthIndex = currentDate.getMonth()
              const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
              const currentMonthName = monthNames[currentMonthIndex]
              
              // Filter complete months with positive revenue
              const completeMonths = data.filter(item => 
                item.month !== currentMonthName && item.amount > 0
              )
              
              // Calculate linear regression for trendline
              let trendSlope = 0
              let trendIntercept = 0
              
              if (completeMonths.length >= 2) {
                // Map complete months to their indices in the full dataset
                const completeMonthsWithIndex = completeMonths.map(cm => {
                  const index = data.findIndex(d => d.month === cm.month)
                  return { ...cm, dataIndex: index }
                })
                
                // Calculate means
                const n = completeMonthsWithIndex.length
                const sumX = completeMonthsWithIndex.reduce((sum, item, i) => sum + i, 0)
                const sumY = completeMonthsWithIndex.reduce((sum, item) => sum + item.amount, 0)
                const meanX = sumX / n
                const meanY = sumY / n
                
                // Calculate slope and intercept
                let numerator = 0
                let denominator = 0
                completeMonthsWithIndex.forEach((item, i) => {
                  numerator += (i - meanX) * (item.amount - meanY)
                  denominator += (i - meanX) * (i - meanX)
                })
                
                trendSlope = denominator !== 0 ? numerator / denominator : 0
                trendIntercept = meanY - trendSlope * meanX
              }
              
              // Add trendline values to data
              return data.map((item, index) => {
                const isComplete = completeMonths.some(cm => cm.month === item.month)
                const completeIndex = completeMonths.findIndex(cm => cm.month === item.month)
                const trendValue = isComplete && completeIndex >= 0 ? trendSlope * completeIndex + trendIntercept : null
                
                return {
                  ...item,
                  trendline: trendValue
                }
              })
            })()} margin={{ top: 40, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
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
              <Bar dataKey="amount" fill="#3b82f6" shape={<CustomBar />} name="Revenue" />
              {/* Trendline */}
              <Line 
                type="monotone"
                dataKey="trendline"
                stroke="#2563eb"
                strokeWidth={2}
                name="Trend"
                dot={false}
                connectNulls={false}
              />
              {serviceData?.monthlyLaborRevenue && serviceData.monthlyLaborRevenue.length > 0 && (() => {
                // Only calculate average for complete months (exclude current month - August)
                const completeMonths = serviceData.monthlyLaborRevenue.slice(0, -1)
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
        </TabsContent>

        <TabsContent value="shop-work-orders" className="space-y-6">
          {/* Cash Burn Work Orders with Cost Overrun Alerts */}
          {shopWorkOrdersLoading ? (
            <Card>
              <CardContent className="flex items-center justify-center h-64">
                <LoadingSpinner />
              </CardContent>
            </Card>
          ) : shopWorkOrders ? (
            <>
              {/* Summary Cards */}
              <div className="grid gap-4 md:grid-cols-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Cash Burn WOs</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{shopWorkOrders.summary.total_work_orders}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Critical Alerts</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-red-600">{shopWorkOrders.summary.critical_count}</div>
                    <p className="text-xs text-muted-foreground">≥100% over budget</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Warnings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-orange-600">{shopWorkOrders.summary.warning_count}</div>
                    <p className="text-xs text-muted-foreground">80-99% of budget</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Hours at Risk</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-red-600">{shopWorkOrders.summary.hours_at_risk || 0}</div>
                    <div className="text-sm text-gray-600 mb-3">Total hours over budget</div>
                    
                    {/* Dollar value section */}
                    {shopWorkOrders.summary.unbillable_labor_value && (
                      <div className="mt-3 pt-3 border-t-2 border-red-200">
                        <div className="text-sm text-gray-600 mb-1">Unbillable Labor Value</div>
                        <div className="text-3xl font-bold text-red-600">
                          ${shopWorkOrders.summary.unbillable_labor_value.toLocaleString('en-US', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                          })}
                        </div>
                        <div className="text-xs text-gray-500">@ $189/hour labor rate</div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Work Orders Table */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-orange-600" />
                    Cash Burn Work Orders - Cost Overrun Alerts
                  </CardTitle>
                  <CardDescription>
                    Real-time monitoring of actual vs quoted labor hours to prevent cost overruns
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>WO#</TableHead>
                          <TableHead>Customer</TableHead>
                          <TableHead>Equipment</TableHead>
                          <TableHead>Open Date</TableHead>
                          <TableHead className="text-right">Quoted Hours</TableHead>
                          <TableHead className="text-right">Actual Hours</TableHead>
                          <TableHead className="text-center">% Used</TableHead>
                          <TableHead className="text-center">Alert</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {shopWorkOrders.work_orders.map((wo) => {
                          const getAlertBadge = (alertLevel, percentUsed) => {
                            switch (alertLevel) {
                              case 'CRITICAL':
                                return <Badge variant="destructive" className="gap-1">🚨 CRITICAL</Badge>
                              case 'RED':
                                return <Badge variant="destructive" className="gap-1">🔴 RED</Badge>
                              case 'YELLOW':
                                return <Badge variant="warning" className="gap-1">🟡 YELLOW</Badge>
                              case 'GREEN':
                                return <Badge variant="secondary" className="gap-1">✅ GREEN</Badge>
                              case 'NO_QUOTE':
                                return <Badge variant="outline" className="gap-1">⚪ NO QUOTE</Badge>
                              default:
                                return <Badge variant="outline">-</Badge>
                            }
                          }

                          const getRowClassName = (alertLevel) => {
                            switch (alertLevel) {
                              case 'CRITICAL':
                                return 'bg-red-100 border-red-300'
                              case 'RED':
                                return 'bg-red-50 border-red-200'
                              case 'YELLOW':
                                return 'bg-yellow-50 border-yellow-200'
                              default:
                                return ''
                            }
                          }

                          return (
                            <TableRow 
                              key={wo.wo_number}
                              className={getRowClassName(wo.alert_level)}
                            >
                              <TableCell className="font-medium">{wo.wo_number}</TableCell>
                              <TableCell className="max-w-[200px] truncate" title={wo.customer_name}>
                                {wo.customer_name}
                              </TableCell>
                              <TableCell className="max-w-[150px] truncate">
                                {wo.unit_no ? `${wo.unit_no}` : ''}
                                {wo.serial_no ? ` (${wo.serial_no})` : ''}
                              </TableCell>
                              <TableCell>{new Date(wo.open_date).toLocaleDateString()}</TableCell>
                              <TableCell className="text-right font-mono">
                                {wo.quoted_hours ? (
                                  <TooltipProvider>
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <span className="cursor-help underline decoration-dotted underline-offset-2">
                                          {Math.round(wo.quoted_hours)}
                                        </span>
                                      </TooltipTrigger>
                                      <TooltipContent className="max-w-xs">
                                        <div className="text-xs space-y-1">
                                          <p className="font-semibold border-b pb-1 mb-1">Quote Calculation</p>
                                          <p>Quoted Amount: <span className="font-mono">${wo.quoted_amount?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span></p>
                                          <p>Labor Rate: <span className="font-mono">${wo.labor_rate?.toFixed(2)}/hr</span></p>
                                          {wo.labor_discount > 0 && (
                                            <p>Discount: <span className="font-mono">{wo.labor_discount}%</span></p>
                                          )}
                                          <p className="border-t pt-1 mt-1 font-medium">
                                            ${wo.quoted_amount?.toLocaleString()} ÷ ${wo.labor_discount > 0
                                              ? `(${wo.labor_rate?.toFixed(0)} × ${(100 - wo.labor_discount) / 100})`
                                              : wo.labor_rate?.toFixed(0)} = <span className="font-bold">{Math.round(wo.quoted_hours)} hrs</span>
                                          </p>
                                        </div>
                                      </TooltipContent>
                                    </Tooltip>
                                  </TooltipProvider>
                                ) : '-'}
                              </TableCell>
                              <TableCell className="text-right font-mono">
                                {wo.actual_hours.toFixed(1)}
                              </TableCell>
                              <TableCell className="text-center font-mono">
                                {wo.percent_used ? `${wo.percent_used.toFixed(0)}%` : '-'}
                              </TableCell>
                              <TableCell className="text-center">
                                {getAlertBadge(wo.alert_level, wo.percent_used)}
                              </TableCell>
                            </TableRow>
                          )
                        })}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="text-center py-8 text-muted-foreground">
                No cash burn work orders data available
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="work-orders" className="space-y-6">
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
                  <CardTitle>Cash Stalled Work Orders Details</CardTitle>
                  <CardDescription>Detailed list of all completed work orders with stalled cash flow</CardDescription>
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
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {awaitingInvoiceDetails.work_orders.map((wo) => (
                          <TableRow 
                            key={wo.wo_number}
                            className={`${wo.days_waiting > 7 ? 'bg-red-50' : wo.days_waiting > 3 ? 'bg-orange-50' : ''} cursor-pointer hover:bg-gray-50`}
                            onClick={() => openNotesModal(wo)}
                          >
                            <TableCell className="font-medium">
                              <div className="flex items-center gap-2">
                                {wo.wo_number}
                                {notes[wo.wo_number]?.note && (
                                  <FileText className="w-4 h-4 text-blue-500" />
                                )}
                              </div>
                            </TableCell>
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

        <TabsContent value="all-work-orders" className="space-y-6">
          {/* Card 1: All Work Order Types */}
          <WorkOrderTypes />

          {/* Cards 2-5: Invoice Delay Analysis Report */}
          {invoiceDelayLoading ? (
            <Card>
              <CardContent className="flex items-center justify-center h-64">
                <LoadingSpinner />
              </CardContent>
            </Card>
          ) : invoiceDelayData ? (
            <div className="space-y-6">
              {/* Card 2: Summary Card */}
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

              {/* Card 3: Department Breakdown */}
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
                {/* Card 4: Delay Distribution Chart */}
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
                          <RechartsTooltip formatter={(value) => `${value.toFixed(1)}%`} />
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

                {/* Card 5: Worst Offenders */}
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
        
        <TabsContent value="pms" className="space-y-6">
          <PMReport user={user} />
        </TabsContent>

        <TabsContent value="pm-route-planner" className="space-y-6">
          <PMRoutePlanner user={user} />
        </TabsContent>

        <TabsContent value="pm-contest" className="space-y-6">
          <PMTechnicianContest />
        </TabsContent>

        <TabsContent value="invoice-billing" className="space-y-6">
          <ServiceInvoiceBilling />
        </TabsContent>

        <TabsContent value="maintenance-contracts" className="space-y-6">
          <MaintenanceContractProfitability />
        </TabsContent>

        <TabsContent value="customer-profitability" className="space-y-6">
          <CustomerProfitability />
        </TabsContent>

        <TabsContent value="units-repair-cost" className="space-y-6">
          <UnitsRepairCost />
        </TabsContent>
      </Tabs>

      {/* Notes Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              Work Order Notes - {selectedWorkOrder?.wo_number}
            </DialogTitle>
            <DialogDescription>
              {selectedWorkOrder?.customer_name && (
                <span className="text-sm">Customer: {selectedWorkOrder.customer_name}</span>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            <Textarea
              value={modalNote}
              onChange={(e) => handleModalNoteChange(e.target.value)}
              placeholder="Enter notes for this work order..."
              className="min-h-[300px] w-full"
            />
            {savingNotes[selectedWorkOrder?.wo_number] && (
              <div className="text-sm text-yellow-600 mt-2">
                Saving...
              </div>
            )}
            {notes[selectedWorkOrder?.wo_number]?.updated_by && (
              <div className="text-xs text-gray-500 mt-2">
                Last updated by {notes[selectedWorkOrder?.wo_number].updated_by}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default ServiceReport