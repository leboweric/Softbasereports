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
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Tooltip as UITooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip'
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
  PauseCircle,
  Target,
  Activity,
  CheckCircle,
  ArrowRight,
  Gauge,
  HelpCircle
} from 'lucide-react'
import { apiUrl } from '@/lib/api'
import RentalServiceReport from './RentalServiceReport'
import RentalAvailability from './RentalAvailability'
import DepreciationRolloff from './DepreciationRolloff'
import { MetricTooltip } from '@/components/ui/metric-tooltip'
import { MethodologyPanel } from '@/components/ui/methodology-panel'
import { RENTAL_METHODOLOGY } from '@/config/ipsPageMethodology'
import { IPS_METRICS } from '@/config/ipsMetricDefinitions'

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


const RentalReport = ({ user }) => {
  const [rentalData, setRentalData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [totalFleet, setTotalFleet] = useState(0)
  const [inventoryCount, setInventoryCount] = useState(0)
  const [monthlyRevenueData, setMonthlyRevenueData] = useState(null)
  const [topCustomers, setTopCustomers] = useState(null)
  const [downloadingForklifts, setDownloadingForklifts] = useState(false)
  const [downloadingUnitsOnRent, setDownloadingUnitsOnRent] = useState(false)
  const [downloadingUnitsOnHold, setDownloadingUnitsOnHold] = useState(false)
  const [unitsOnRent, setUnitsOnRent] = useState(0)
  const [unitsOnHold, setUnitsOnHold] = useState(0)
  const [benchmarkData, setBenchmarkData] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [includeCurrentMonth, setIncludeCurrentMonth] = useState(false)
  const [rawMonthlyRevenueData, setRawMonthlyRevenueData] = useState(null)
  
  // Re-filter monthly revenue data when toggle changes
  useEffect(() => {
    if (rawMonthlyRevenueData && rawMonthlyRevenueData.length > 0) {
      const now = new Date()
      const currentMonthStr = now.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }).replace(' ', " '")
      const filteredData = rawMonthlyRevenueData.filter(item => {
        if (!includeCurrentMonth && item.month === currentMonthStr) return false
        return true
      })
      setMonthlyRevenueData(filteredData)
    }
  }, [includeCurrentMonth, rawMonthlyRevenueData])

  // Sort monthly revenue data chronologically for correct trendline calculation
  const sortedMonthlyRevenue = React.useMemo(() => {
    if (!monthlyRevenueData) {
      return [];
    }

    const monthOrder = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];

    const parseMonth = (m) => {
      const parts = m.match(/^(\w+)\s*'?(\d{2})?$/);
      if (!parts) return monthOrder.indexOf(m);
      const monthIdx = monthOrder.indexOf(parts[1]);
      const year = parts[2] ? parseInt(parts[2]) : 0;
      return year * 12 + monthIdx;
    };

    return [...monthlyRevenueData].sort((a, b) => {
      return parseMonth(a.month) - parseMonth(b.month);
    });
  }, [monthlyRevenueData]);

  useEffect(() => {
    fetchRentalData()
    fetchFleetSummary()
    fetchMonthlyRevenueData()
    fetchTopCustomers()
    fetchBenchmarkData()
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

  const fetchFleetSummary = async () => {
    try {
      const token = localStorage.getItem('token')
      // Use the same /availability endpoint as the Availability tab
      // This is the proven source of truth for fleet metrics (949 total, 732 on rent, 217 available)
      const response = await fetch(apiUrl('/api/reports/departments/rental/availability'), {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      
      if (response.ok) {
        const data = await response.json()
        const summary = data.summary || {}
        setTotalFleet(summary.totalUnits || 0)
        setInventoryCount(summary.totalUnits || 0)
        setUnitsOnRent(summary.onRentUnits || 0)
        setUnitsOnHold(summary.onHoldUnits || 0)
      }
    } catch (error) {
      console.error('Error fetching fleet summary:', error)
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
        const rawData = data.monthlyRentalRevenue || []
        setRawMonthlyRevenueData(rawData)
        // Apply initial filter (exclude current month by default)
        const now = new Date()
        const currentMonthStr = now.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }).replace(' ', " '")
        const filteredData = rawData.filter(item => {
          if (!includeCurrentMonth && item.month === currentMonthStr) return false
          return true
        })
        setMonthlyRevenueData(filteredData)
      }
    } catch (error) {
      console.error('Error fetching monthly revenue data:', error)
      setRawMonthlyRevenueData([])
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

  // fetchUnitsOnRent and fetchUnitsOnHold are now handled by fetchFleetSummary

  const fetchBenchmarkData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/rental/currie-benchmarks'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setBenchmarkData(data)
      }
    } catch (error) {
      console.error('Error fetching rental currie benchmarks:', error)
    }
  }

  // Custom bar shape
  const CustomBar = (props) => {
    const { fill, x, y, width, height } = props
    return (
      <g>
        <rect x={x} y={y} width={width} height={height} fill={fill} rx={4} ry={4} />
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Rental Department</h1>
          <p className="text-muted-foreground">Fleet management and rental analytics</p>
        </div>
        <MethodologyPanel {...RENTAL_METHODOLOGY} />
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="availability">Availability</TabsTrigger>
          <TabsTrigger value="depreciation">Depreciation</TabsTrigger>
          <TabsTrigger value="service-report">Service Report</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Row 1: Glanceable KPI Cards */}
          <div className="grid gap-4 md:grid-cols-5">
            {/* Fleet Utilization */}
            <Card className="border-l-4 border-l-purple-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <Gauge className="h-4 w-4 text-purple-500" />
                  <span className="text-xs font-medium text-muted-foreground">Fleet Utilization</span>
                  <MetricTooltip {...IPS_METRICS.rental_utilization} />
                </div>
                <div className="text-2xl font-bold">
                  {totalFleet > 0 ? `${((unitsOnRent / totalFleet) * 100).toFixed(1)}%` : '—'}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {unitsOnRent} of {totalFleet} units
                </p>
              </CardContent>
            </Card>

            {/* Units on Rent */}
            <Card className="border-l-4 border-l-green-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <Activity className="h-4 w-4 text-green-500" />
                  <span className="text-xs font-medium text-muted-foreground">Units on Rent</span>
                  <MetricTooltip label="Units on Rent" formula="Count of rental fleet units with active rental contracts (from equipment master)" accounts={[]} />
                </div>
                <div className="text-2xl font-bold text-green-600">{unitsOnRent}</div>
                <p className="text-xs text-muted-foreground mt-1">Currently deployed</p>
              </CardContent>
            </Card>

            {/* Units Available */}
            <Card className="border-l-4 border-l-blue-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <CheckCircle className="h-4 w-4 text-blue-500" />
                  <span className="text-xs font-medium text-muted-foreground">Available</span>
                </div>
                <div className="text-2xl font-bold text-blue-600">
                  {Math.max(0, totalFleet - unitsOnRent - unitsOnHold)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">Ready to rent</p>
              </CardContent>
            </Card>

            {/* Units on Hold */}
            <Card className={`border-l-4 ${unitsOnHold > 0 ? 'border-l-orange-500' : 'border-l-gray-300'}`}>
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <PauseCircle className="h-4 w-4 text-orange-500" />
                  <span className="text-xs font-medium text-muted-foreground">On Hold</span>
                  <TooltipProvider>
                    <UITooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="h-3.5 w-3.5 text-muted-foreground/50 cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-xs">
                        <p className="text-xs">Units with RentalStatus set to "Hold" in Softbase. These are rental fleet units temporarily unavailable for rent due to maintenance, damage, pending inspection, or other reasons.</p>
                      </TooltipContent>
                    </UITooltip>
                  </TooltipProvider>
                </div>
                <div className={`text-2xl font-bold ${unitsOnHold > 0 ? 'text-orange-600' : ''}`}>
                  {unitsOnHold}
                </div>
                <p className="text-xs text-muted-foreground mt-1">Maintenance / other</p>
              </CardContent>
            </Card>

            {/* Avg Monthly Revenue */}
            <Card className="border-l-4 border-l-emerald-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <DollarSign className="h-4 w-4 text-emerald-500" />
                  <span className="text-xs font-medium text-muted-foreground">Avg Revenue / Mo</span>
                  <MetricTooltip {...IPS_METRICS.rental_avg_rate} />
                </div>
                <div className="text-2xl font-bold">
                  {monthlyRevenueData && monthlyRevenueData.length > 0 ? 
                    formatCurrency(monthlyRevenueData.filter(m => m.amount > 0).reduce((sum, m) => sum + m.amount, 0) / Math.max(1, monthlyRevenueData.filter(m => m.amount > 0).length)) 
                    : '—'}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {includeCurrentMonth ? 'Including current month' : 'Excluding current month'}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Row 2: Currie Benchmark + Action Items */}
          <div className="grid gap-4 md:grid-cols-3">
            {/* Currie Benchmark - Compact */}
            <Card className="md:col-span-2">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Currie Benchmarks
                  {benchmarkData?.current_month?.gp_margin >= benchmarkData?.currie_gp_target && (
                    <Badge className="ml-2 bg-green-100 text-green-800">Meeting Target</Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {benchmarkData ? (
                  <div className="grid gap-6 md:grid-cols-3">
                    <div className="space-y-2">
                      <h4 className="font-medium text-xs text-muted-foreground uppercase tracking-wide">Current Month GP%</h4>
                      <div className="flex items-baseline gap-2">
                        <span className={`text-3xl font-bold ${benchmarkData.current_month?.gp_margin >= benchmarkData.currie_gp_target ? 'text-green-600' : 'text-red-600'}`}>
                          {benchmarkData.current_month?.gp_margin || 0}%
                        </span>
                        <span className="text-sm text-muted-foreground">/ {benchmarkData.currie_gp_target}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className={`h-2 rounded-full ${benchmarkData.current_month?.gp_margin >= benchmarkData.currie_gp_target ? 'bg-green-500' : 'bg-red-500'}`}
                          style={{ width: `${Math.min((benchmarkData.current_month?.gp_margin || 0) / benchmarkData.currie_gp_target * 100, 100)}%` }} />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <h4 className="font-medium text-xs text-muted-foreground uppercase tracking-wide">Trailing {benchmarkData.trailing_average?.months || 12}mo Avg</h4>
                      <div className="flex items-baseline gap-2">
                        <span className={`text-3xl font-bold ${benchmarkData.trailing_average?.gp_margin >= benchmarkData.currie_gp_target ? 'text-green-600' : 'text-red-600'}`}>
                          {benchmarkData.trailing_average?.gp_margin || 0}%
                        </span>
                        <span className="text-sm text-muted-foreground">/ {benchmarkData.currie_gp_target}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className={`h-2 rounded-full ${benchmarkData.trailing_average?.gp_margin >= benchmarkData.currie_gp_target ? 'bg-green-500' : 'bg-red-500'}`}
                          style={{ width: `${Math.min((benchmarkData.trailing_average?.gp_margin || 0) / benchmarkData.currie_gp_target * 100, 100)}%` }} />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <h4 className="font-medium text-xs text-muted-foreground uppercase tracking-wide">GP$ This Month</h4>
                      <div className="text-3xl font-bold text-blue-600">
                        {formatCurrency(benchmarkData.current_month?.gross_profit || 0)}
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground pt-1 border-t">
                        <span>GP Target: {benchmarkData.currie_gp_target}%</span>
                        <span>OP Target: {benchmarkData.currie_op_target}%</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Loading benchmark data...</p>
                )}
              </CardContent>
            </Card>

            {/* Action Items */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-orange-500" />
                  Action Items
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {/* Units on Hold */}
                  {unitsOnHold > 0 && (
                    <button 
                      onClick={() => setActiveTab('availability')}
                      className="w-full flex items-center gap-3 p-2 rounded-lg bg-orange-50 hover:bg-orange-100 transition-colors text-left"
                    >
                      <PauseCircle className="h-5 w-5 text-orange-600 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-orange-800">{unitsOnHold} Units on Hold</p>
                        <p className="text-xs text-orange-600">Not generating revenue</p>
                      </div>
                      <ArrowRight className="h-4 w-4 text-orange-400 ml-auto" />
                    </button>
                  )}

                  {/* Low Utilization Warning */}
                  {totalFleet > 0 && ((unitsOnRent / totalFleet) * 100) < 65 && (
                    <div className="flex items-center gap-3 p-2 rounded-lg bg-yellow-50">
                      <Gauge className="h-5 w-5 text-yellow-600 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-yellow-800">Low Fleet Utilization</p>
                        <p className="text-xs text-yellow-600">{((unitsOnRent / totalFleet) * 100).toFixed(1)}% — target 65-75%</p>
                      </div>
                    </div>
                  )}

                  {/* GP Below Target */}
                  {benchmarkData?.current_month?.vs_target < 0 && (
                    <div className="flex items-center gap-3 p-2 rounded-lg bg-red-50">
                      <TrendingDown className="h-5 w-5 text-red-600 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-red-800">GP Below Currie Target</p>
                        <p className="text-xs text-red-600">{benchmarkData.current_month?.vs_target}pp below {benchmarkData.currie_gp_target}%</p>
                      </div>
                    </div>
                  )}

                  {/* All clear state */}
                  {unitsOnHold === 0 && 
                   (totalFleet === 0 || ((unitsOnRent / totalFleet) * 100) >= 65) &&
                   (!benchmarkData?.current_month?.vs_target || benchmarkData?.current_month?.vs_target >= 0) && (
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

          {/* Row 3: Revenue Trend Chart */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle>Monthly Rental Revenue</CardTitle>
                  <CardDescription>Revenue trend over the last 12 months</CardDescription>
                  <div className="flex items-center gap-2 mt-2">
                    <Switch
                      id="include-current-month-rental"
                      checked={includeCurrentMonth}
                      onCheckedChange={setIncludeCurrentMonth}
                    />
                    <Label htmlFor="include-current-month-rental" className="text-sm text-muted-foreground cursor-pointer">
                      Include current month
                    </Label>
                  </div>
                </div>
                {monthlyRevenueData && monthlyRevenueData.length > 0 && (() => {
                  const monthsWithRevenue = monthlyRevenueData.filter(item => item.amount > 0)
                  const avgRevenue = monthsWithRevenue.length > 0 ? 
                    monthsWithRevenue.reduce((sum, item) => sum + item.amount, 0) / monthsWithRevenue.length : 0
                  return (
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">Avg Revenue</p>
                      <p className="text-lg font-semibold">{formatCurrency(avgRevenue)}</p>
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
                  const completeMonths = data.filter(item => item.amount > 0)
                  let trendSlope = 0, trendIntercept = 0
                  if (completeMonths.length >= 2) {
                    const n = completeMonths.length
                    const sumX = completeMonths.reduce((sum, _, i) => sum + i, 0)
                    const sumY = completeMonths.reduce((sum, item) => sum + item.amount, 0)
                    const meanX = sumX / n, meanY = sumY / n
                    let numerator = 0, denominator = 0
                    completeMonths.forEach((item, i) => {
                      numerator += (i - meanX) * (item.amount - meanY)
                      denominator += (i - meanX) * (i - meanX)
                    })
                    trendSlope = denominator !== 0 ? numerator / denominator : 0
                    trendIntercept = meanY - trendSlope * meanX
                  }
                  return data.map((item) => {
                    const isComplete = completeMonths.some(cm => cm.month === item.month)
                    const completeIndex = completeMonths.findIndex(cm => cm.month === item.month)
                    return { ...item, trendline: isComplete && completeIndex >= 0 ? trendSlope * completeIndex + trendIntercept : null }
                  })
                })()} margin={{ top: 40, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                  <Tooltip content={({ active, payload, label }) => {
                    if (active && payload && payload.length && monthlyRevenueData) {
                      const currentIndex = monthlyRevenueData.findIndex(item => item.month === label)
                      const currentData = monthlyRevenueData[currentIndex]
                      const previousData = currentIndex > 0 ? monthlyRevenueData[currentIndex - 1] : null
                      if (!currentData) return null
                      return (
                        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                          <p className="font-semibold mb-2">{label}</p>
                          <p className="text-purple-600">
                            Revenue: {formatCurrency(currentData.amount || 0)}
                            {formatPercentage(calculatePercentageChange(currentData.amount || 0, previousData?.amount))}
                          </p>
                        </div>
                      )
                    }
                    return null
                  }} />
                  <Legend />
                  <Bar dataKey="amount" fill="#9333ea" shape={<CustomBar />} name="Revenue" />
                  <Line type="monotone" dataKey="trendline" stroke="#7c3aed" strokeWidth={2} name="Trend" dot={false} connectNulls={false} />
                  {monthlyRevenueData && monthlyRevenueData.length > 0 && (() => {
                    const monthsWithRevenue = monthlyRevenueData.filter(item => item.amount > 0)
                    if (monthsWithRevenue.length === 0) return null
                    const average = monthsWithRevenue.reduce((sum, item) => sum + item.amount, 0) / monthsWithRevenue.length
                    return <ReferenceLine y={average} stroke="#666" strokeDasharray="3 3" label={{ value: "Average", position: "insideTopRight" }} />
                  })()}
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Row 4: Fleet Status + Top Customers */}
          <div className="grid gap-4 md:grid-cols-2">
            {/* Fleet Status Donut */}
            <Card>
              <CardHeader>
                <CardTitle>Fleet Status</CardTitle>
                <CardDescription>Current fleet allocation</CardDescription>
              </CardHeader>
              <CardContent>
                {totalFleet > 0 ? (
                  <div className="flex items-center gap-6">
                    <ResponsiveContainer width="50%" height={220}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'On Rent', value: unitsOnRent, color: '#10b981' },
                            { name: 'Available', value: Math.max(0, totalFleet - unitsOnRent - unitsOnHold), color: '#3b82f6' },
                            { name: 'On Hold', value: unitsOnHold, color: '#f59e0b' }
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={55}
                          outerRadius={85}
                          paddingAngle={3}
                          dataKey="value"
                        >
                          {[
                            { name: 'On Rent', value: unitsOnRent, color: '#10b981' },
                            { name: 'Available', value: Math.max(0, totalFleet - unitsOnRent - unitsOnHold), color: '#3b82f6' },
                            { name: 'On Hold', value: unitsOnHold, color: '#f59e0b' }
                          ].map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => [`${value} units`, '']} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="space-y-4 flex-1">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-green-500" />
                          <span className="text-sm">On Rent</span>
                        </div>
                        <span className="text-sm font-bold">{unitsOnRent}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-blue-500" />
                          <span className="text-sm">Available</span>
                        </div>
                        <span className="text-sm font-bold">{Math.max(0, totalFleet - unitsOnRent - unitsOnHold)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-yellow-500" />
                          <span className="text-sm">On Hold</span>
                        </div>
                        <span className="text-sm font-bold">{unitsOnHold}</span>
                      </div>
                      <div className="pt-2 border-t">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Total Fleet</span>
                          <span className="text-sm font-bold">{totalFleet}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No fleet data available</p>
                )}
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
                          <p className="text-sm font-medium truncate">{customer.name}</p>
                          <p className="text-xs text-gray-500">
                            {customer.invoice_count} invoices
                            {customer.units_on_rent > 0 && (
                              <span className="ml-1 text-purple-600">• {customer.units_on_rent} on rent</span>
                            )}
                            {customer.days_since_last > 30 && (
                              <span className="ml-1 text-orange-600">• {customer.days_since_last}d ago</span>
                            )}
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium text-gray-900">{formatCurrency(customer.revenue)}</div>
                          <div className="text-xs text-gray-500">{customer.percentage}%</div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No customer data available</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="service-report">
          <RentalServiceReport />
        </TabsContent>

        <TabsContent value="availability" className="space-y-6">
          <RentalAvailability />
        </TabsContent>

        <TabsContent value="depreciation" className="space-y-6">
          <DepreciationRolloff />
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default RentalReport