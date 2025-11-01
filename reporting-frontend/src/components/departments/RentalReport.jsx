import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
  ComposedChart,
  Legend,
  ReferenceLine
} from 'recharts'
import { 
  Truck,
  DollarSign,
  Calendar,
  TrendingUp,
  TrendingDown,
  Users,
  Package,
  Clock,
  AlertCircle,
  Download,
  PauseCircle
} from 'lucide-react'
import { apiUrl } from '@/lib/api'
import RentalServiceReport from './RentalServiceReport'
import RentalAvailability from './RentalAvailability'

// Utility function to calculate linear regression trendline
const calculateLinearTrend = (data, xKey, yKey, excludeCurrentMonth = true) => {
  if (!data || data.length < 2) return data || []

  // Find the index of the first month with actual data
  const firstDataIndex = data.findIndex(item => item[yKey] > 0)

  // If no data or only one data point, no trendline can be calculated
  if (firstDataIndex === -1) {
    return data.map(item => ({ ...item, trendValue: null }))
  }

  // Slice the data to start from the first month with actual data
  const validData = data.slice(firstDataIndex)

  if (validData.length < 2) {
    return data.map(item => ({ ...item, trendValue: null }))
  }

  // Determine which data to use for trendline calculation
  let trendData = validData
  if (excludeCurrentMonth && validData.length > 1) {
    trendData = validData.slice(0, -1)
  }

  if (trendData.length < 2) {
    return data.map(item => ({ ...item, trendValue: null }))
  }

  // Calculate linear regression using trendData
  const n = trendData.length
  const sumX = trendData.reduce((sum, _, index) => sum + index, 0)
  const sumY = trendData.reduce((sum, item) => sum + item[yKey], 0)
  const sumXY = trendData.reduce((sum, item, index) => sum + (index * item[yKey]), 0)
  const sumXX = trendData.reduce((sum, _, index) => sum + (index * index), 0)

  const denominator = (n * sumXX - sumX * sumX)
  if (denominator === 0) {
    return data.map(item => ({ ...item, trendValue: null }))
  }

  const slope = (n * sumXY - sumX * sumY) / denominator
  const intercept = (sumY - slope * sumX) / n

  // Apply trendline to all data points, starting from the first month with data
  return data.map((item, index) => {
    if (index < firstDataIndex) {
      return { ...item, trendValue: null }
    }
    return {
      ...item,
      trendValue: slope * (index - firstDataIndex) + intercept
    }
  })
}


const RentalReport = ({ user }) => {
  const [rentalData, setRentalData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [inventoryCount, setInventoryCount] = useState(0)
  const [monthlyRevenueData, setMonthlyRevenueData] = useState(null)
  const [topCustomers, setTopCustomers] = useState(null)
  const [downloadingForklifts, setDownloadingForklifts] = useState(false)
  const [downloadingUnitsOnRent, setDownloadingUnitsOnRent] = useState(false)
  const [downloadingUnitsOnHold, setDownloadingUnitsOnHold] = useState(false)
  const [unitsOnRent, setUnitsOnRent] = useState(0)
  const [unitsOnHold, setUnitsOnHold] = useState(0)
  const [paceData, setPaceData] = useState(null)
  
  // Sort monthly revenue data chronologically for correct trendline calculation
  const sortedMonthlyRevenue = React.useMemo(() => {
    if (!monthlyRevenueData) {
      return [];
    }

    const monthOrder = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];

    return [...monthlyRevenueData].sort((a, b) => {
      return monthOrder.indexOf(a.month) - monthOrder.indexOf(b.month);
    });
  }, [monthlyRevenueData]);

  useEffect(() => {
    fetchRentalData()
    fetchInventoryCount()
    fetchMonthlyRevenueData()
    fetchTopCustomers()
    fetchUnitsOnRent()
    fetchUnitsOnHold()
    fetchPaceData()
  }, [])

  const fetchRentalData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/rental'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setRentalData(data)
      }
    } catch (error) {
      console.error('Error fetching rental data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchInventoryCount = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/dashboard/summary-optimized'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setInventoryCount(data.inventory_count || 0)
      }
    } catch (error) {
      console.error('Error fetching inventory count:', error)
    }
  }

  const fetchMonthlyRevenueData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/rental/monthly-revenue'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setMonthlyRevenueData(data.monthlyRentalRevenue || [])
      }
    } catch (error) {
      console.error('Error fetching monthly revenue data:', error)
      setMonthlyRevenueData([])
    }
  }

  const fetchTopCustomers = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/rental/top-customers'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setTopCustomers(data)
      }
    } catch (error) {
      console.error('Error fetching top customers:', error)
      setTopCustomers(null)
    }
  }

  const fetchUnitsOnRent = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/rental/units-on-rent'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setUnitsOnRent(data.units_on_rent || 0)
      }
    } catch (error) {
      console.error('Error fetching units on rent:', error)
    }
  }

  const fetchUnitsOnHold = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/rental/units-on-hold'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setUnitsOnHold(data.units_on_hold || 0)
      }
    } catch (error) {
      console.error('Error fetching units on hold:', error)
    }
  }

  const fetchPaceData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/rental/pace'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setPaceData(data)
      }
    } catch (error) {
      console.error('Error fetching rental pace data:', error)
    }
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

  const handleDownloadForklifts = async () => {
    setDownloadingForklifts(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/rental/available-forklifts'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        
        // Convert to CSV
        const headers = ['Unit No', 'Serial No', 'Make', 'Model', 'Model Year', 'Cost', 'List Price', 'Location', 'Day Rate', 'Week Rate', 'Month Rate', 'Rental Status']
        const rows = data.forklifts.map(forklift => [
          forklift.unit_no,
          forklift.serial_no,
          forklift.make,
          forklift.model,
          forklift.model_year || '',
          forklift.cost,
          forklift.list_price,
          forklift.location || '',
          forklift.day_rent || 0,
          forklift.week_rent || 0,
          forklift.month_rent || 0,
          forklift.rental_status
        ])
        
        const csvContent = [
          headers.join(','),
          ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
        ].join('\n')
        
        // Download file
        const blob = new Blob([csvContent], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `available_rental_equipment_${new Date().toISOString().split('T')[0]}.csv`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Error downloading forklift data:', error)
    } finally {
      setDownloadingForklifts(false)
    }
  }

  const handleDownloadUnitsOnRent = async () => {
    setDownloadingUnitsOnRent(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/rental/units-on-rent-detail'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        
        // Convert to CSV
        const headers = ['Customer Name', 'Customer No', 'Unit No', 'Serial No', 'Make', 'Model', 'Model Year', 'Location', 'Days Rented', 'Rent Amount', 'Day Rate', 'Week Rate', 'Month Rate']
        const rows = data.units.map(unit => [
          unit.customer_name,
          unit.customer_no,
          unit.unit_no,
          unit.serial_no,
          unit.make,
          unit.model,
          unit.model_year || '',
          unit.location || '',
          unit.days_rented,
          unit.rent_amount,
          unit.day_rent || 0,
          unit.week_rent || 0,
          unit.month_rent || 0
        ])
        
        const csvContent = [
          headers.join(','),
          ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
        ].join('\n')
        
        // Download file
        const blob = new Blob([csvContent], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `units_on_rent_${new Date().toISOString().split('T')[0]}.csv`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Error downloading units on rent data:', error)
    } finally {
      setDownloadingUnitsOnRent(false)
    }
  }

  const handleDownloadUnitsOnHold = async () => {
    setDownloadingUnitsOnHold(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/rental/units-on-hold-detail'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        
        // Convert to CSV
        const headers = ['Unit No', 'Serial No', 'Make', 'Model', 'Model Year', 'Location', 'Cost', 'List Price', 'Day Rate', 'Week Rate', 'Month Rate', 'Status', 'Customer No', 'Customer Name']
        const rows = data.units.map(unit => [
          unit.unit_no,
          unit.serial_no,
          unit.make,
          unit.model,
          unit.model_year || '',
          unit.location || '',
          unit.cost,
          unit.list_price,
          unit.day_rent || 0,
          unit.week_rent || 0,
          unit.month_rent || 0,
          unit.rental_status,
          unit.customer_no,
          unit.customer_name
        ])
        
        const csvContent = [
          headers.join(','),
          ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
        ].join('\n')
        
        // Download file
        const blob = new Blob([csvContent], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `units_on_hold_${new Date().toISOString().split('T')[0]}.csv`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Error downloading units on hold data:', error)
    } finally {
      setDownloadingUnitsOnHold(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  const mockData = {
    summary: {
      totalFleetSize: 145,
      unitsOnRent: 98,
      utilizationRate: 67.6,
      monthlyRevenue: 485750,
      overdueReturns: 5,
      maintenanceDue: 12
    },
    fleetByCategory: [
      { category: 'Excavators', total: 45, onRent: 32, available: 13 },
      { category: 'Loaders', total: 30, onRent: 24, available: 6 },
      { category: 'Dozers', total: 25, onRent: 18, available: 7 },
      { category: 'Compactors', total: 20, onRent: 14, available: 6 },
      { category: 'Generators', total: 25, onRent: 10, available: 15 }
    ],
    rentalsByDuration: [
      { duration: 'Daily', count: 15, revenue: 45000 },
      { duration: 'Weekly', count: 35, revenue: 125000 },
      { duration: 'Monthly', count: 38, revenue: 215750 },
      { duration: 'Long-term', count: 10, revenue: 100000 }
    ],
    activeRentals: [
      { contractNumber: 'RC-2024-001', customer: 'ABC Construction', equipment: 'CAT 320D Excavator', startDate: '2024-06-01', endDate: '2024-07-01', dailyRate: 850, status: 'Active' },
      { contractNumber: 'RC-2024-002', customer: 'XYZ Builders', equipment: 'Komatsu WA320 Loader', startDate: '2024-06-15', endDate: '2024-06-22', dailyRate: 650, status: 'Due Soon' },
      { contractNumber: 'RC-2024-003', customer: 'DEF Contractors', equipment: 'CAT D6 Dozer', startDate: '2024-05-15', endDate: '2024-06-15', dailyRate: 1200, status: 'Overdue' },
      { contractNumber: 'RC-2024-004', customer: 'GHI Mining', equipment: 'Volvo EC350 Excavator', startDate: '2024-06-10', endDate: '2024-08-10', dailyRate: 950, status: 'Active' },
      { contractNumber: 'RC-2024-005', customer: 'JKL Paving', equipment: 'BOMAG BW213 Compactor', startDate: '2024-06-18', endDate: '2024-06-25', dailyRate: 450, status: 'Active' }
    ],
    monthlyTrend: [
      { month: 'Jan', revenue: 385000, utilization: 58 },
      { month: 'Feb', revenue: 412000, utilization: 62 },
      { month: 'Mar', revenue: 445000, utilization: 65 },
      { month: 'Apr', revenue: 468000, utilization: 68 },
      { month: 'May', revenue: 475000, utilization: 69 },
      { month: 'Jun', revenue: 485750, utilization: 67.6 }
    ],
    topCustomers: [
      { name: 'ABC Construction', activeRentals: 8, totalRevenue: 45000, avgDuration: 25 },
      { name: 'XYZ Builders', activeRentals: 5, totalRevenue: 32000, avgDuration: 15 },
      { name: 'DEF Contractors', activeRentals: 6, totalRevenue: 38000, avgDuration: 30 },
      { name: 'GHI Mining', activeRentals: 4, totalRevenue: 28000, avgDuration: 60 },
      { name: 'JKL Paving', activeRentals: 3, totalRevenue: 18000, avgDuration: 10 }
    ]
  }

  const data = rentalData || mockData

  const utilizationColor = data.summary.utilizationRate > 80 ? '#ef4444' : 
                          data.summary.utilizationRate > 60 ? '#10b981' : '#f59e0b'

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Rental Department</h1>
        <p className="text-muted-foreground">Fleet management and rental analytics</p>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="availability">Availability</TabsTrigger>
          <TabsTrigger value="service-report">Service Report</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Rental Pace Analysis Card */}
          {paceData?.adaptive_comparisons && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <Truck className="h-5 w-5" />
                  Rental Revenue Pace Analysis
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

          {/* Top section with small cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {/* Rental Units Available Card */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Rental Units Available</CardTitle>
                <Package className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{inventoryCount}</div>
                <p className="text-xs text-muted-foreground mb-3">
                  Units ready to rent
                </p>
                <Button 
                  onClick={handleDownloadForklifts}
                  disabled={downloadingForklifts}
                  size="sm"
                  variant="outline"
                  className="w-full"
                >
                  <Download className="mr-2 h-4 w-4" />
                  {downloadingForklifts ? 'Downloading...' : 'Download Available Equipment'}
                </Button>
              </CardContent>
            </Card>


            {/* Units on Hold Card */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Units on Hold</CardTitle>
                <PauseCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{unitsOnHold}</div>
                <p className="text-xs text-muted-foreground mb-3">
                  Reserved or maintenance
                </p>
                <Button 
                  onClick={handleDownloadUnitsOnHold}
                  disabled={downloadingUnitsOnHold}
                  size="sm"
                  variant="outline"
                  className="w-full"
                >
                  <Download className="mr-2 h-4 w-4" />
                  {downloadingUnitsOnHold ? 'Downloading...' : 'Download On Hold Equipment'}
                </Button>
              </CardContent>
            </Card>

            {/* Number of Units on Rent Card */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Number of Units on Rent</CardTitle>
                <Truck className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{unitsOnRent}</div>
                <p className="text-xs text-muted-foreground mb-3">
                  Currently rented out
                </p>
                <Button 
                  onClick={handleDownloadUnitsOnRent}
                  disabled={downloadingUnitsOnRent}
                  size="sm"
                  variant="outline"
                  className="w-full"
                >
                  <Download className="mr-2 h-4 w-4" />
                  {downloadingUnitsOnRent ? 'Downloading...' : 'Download Rental Details'}
                </Button>
              </CardContent>
            </Card>
          </div>

      {/* Monthly Revenue & Margin */}
      <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle>Monthly Rental Revenue</CardTitle>
                <CardDescription>Rental revenue over the last 12 months</CardDescription>
              </div>
              {monthlyRevenueData && monthlyRevenueData.length > 0 && (() => {
                // Only include historical months (before current month)
                const currentDate = new Date()
                const currentMonthIndex = currentDate.getMonth()
                const currentYear = currentDate.getFullYear()
                
                // Month names in order
                const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                const currentMonthName = monthNames[currentMonthIndex]
                
                // Get index of current month in the data
                const currentMonthDataIndex = monthlyRevenueData.findIndex(item => item.month === currentMonthName)
                
                // Filter to only include months before current month with positive revenue
                const historicalMonths = currentMonthDataIndex > 0 
                  ? monthlyRevenueData.slice(0, currentMonthDataIndex).filter(item => item.amount > 0)
                  : monthlyRevenueData.filter(item => item.amount > 0 && item.month !== currentMonthName)
                
                const avgRevenue = historicalMonths.length > 0 ? 
                  historicalMonths.reduce((sum, item) => sum + item.amount, 0) / historicalMonths.length : 0
                
                return (
                  <div className="text-right">
                    <div className="mb-2">
                      <p className="text-sm text-muted-foreground">Avg Revenue</p>
                      <p className="text-lg font-semibold">{formatCurrency(avgRevenue)}</p>
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
                <Tooltip 
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length && monthlyRevenueData) {
                      const data = monthlyRevenueData
                      const currentIndex = data.findIndex(item => item.month === label)
                      const currentData = data[currentIndex]
                      const previousData = currentIndex > 0 ? data[currentIndex - 1] : null
                      
                      // Safety check for currentData
                      if (!currentData) return null
                      
                      return (
                        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                          <p className="font-semibold mb-2">{label}</p>
                          <div className="space-y-1">
                            <p className="text-purple-600">
                              Revenue: {formatCurrency(currentData.amount || 0)}
                              {formatPercentage(calculatePercentageChange(currentData.amount || 0, previousData?.amount))}
                            </p>
                          </div>
                        </div>
                      )
                    }
                    return null
                  }}
                />
                <Bar dataKey="amount" fill="#9333ea" shape={<CustomBar />} />
                <Line type="monotone" dataKey="trendValue" stroke="#8b5cf6" strokeWidth={2} strokeDasharray="5 5" name="Revenue Trend" dot={false} />
                {monthlyRevenueData && monthlyRevenueData.length > 0 && (() => {
                  // Only calculate average for complete months (exclude current month - August)
                  const completeMonths = monthlyRevenueData.slice(0, -1)
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

      {/* Top 10 Rental Customers */}
      <Card>
        <CardHeader>
          <CardTitle>Top 10 Rental Customers</CardTitle>
          <CardDescription>By YTD rental revenue</CardDescription>
        </CardHeader>
        <CardContent>
          {topCustomers?.top_customers ? (
            <div className="space-y-3">
              {topCustomers.top_customers.map((customer) => (
                <div key={customer.rank} className="flex items-center">
                  <div className="w-8 text-sm font-medium text-muted-foreground">
                    {customer.rank}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {customer.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {customer.invoice_count} invoices
                      {customer.units_on_rent > 0 && (
                        <span className="ml-1 text-purple-600">
                          • {customer.units_on_rent} units on rent
                        </span>
                      )}
                      {customer.days_since_last > 30 && (
                        <span className="ml-1 text-orange-600">
                          • {customer.days_since_last}d ago
                        </span>
                      )}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {formatCurrency(customer.revenue)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {customer.percentage}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No customer data available</p>
          )}
        </CardContent>
      </Card>
        </TabsContent>

        <TabsContent value="service-report">
          <RentalServiceReport />
        </TabsContent>

        <TabsContent value="availability" className="space-y-6">
          <RentalAvailability />
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default RentalReport