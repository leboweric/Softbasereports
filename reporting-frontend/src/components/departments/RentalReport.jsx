import { useState, useEffect } from 'react'
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
  Users,
  Package,
  Clock,
  AlertCircle
} from 'lucide-react'
import { apiUrl } from '@/lib/api'
import RentalServiceReport from './RentalServiceReport'

const RentalReport = ({ user }) => {
  const [rentalData, setRentalData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [inventoryCount, setInventoryCount] = useState(0)
  const [monthlyRevenueData, setMonthlyRevenueData] = useState(null)
  const [topCustomers, setTopCustomers] = useState(null)

  useEffect(() => {
    fetchRentalData()
    fetchInventoryCount()
    fetchMonthlyRevenueData()
    fetchTopCustomers()
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
          <TabsTrigger value="service-report">Service Report</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">

      {/* Rental Units Available Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Rental Units Available</CardTitle>
          <Package className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{inventoryCount}</div>
          <p className="text-xs text-muted-foreground">
            Units ready to rent
          </p>
        </CardContent>
      </Card>

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
              <ComposedChart data={(() => {
                const data = monthlyRevenueData || []
                
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
                  
                  // Add average values to each data point for reference line rendering
                  return data.map(item => ({
                    ...item,
                    avgRevenue: avgRevenue
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
                <Tooltip 
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length && monthlyRevenueData) {
                      const data = monthlyRevenueData
                      const currentIndex = data.findIndex(item => item.month === label)
                      const currentData = data[currentIndex]
                      const previousData = currentIndex > 0 ? data[currentIndex - 1] : null
                      
                      return (
                        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                          <p className="font-semibold mb-2">{label}</p>
                          <div className="space-y-1">
                            <p className="text-purple-600">
                              Revenue: {formatCurrency(currentData.amount)}
                              {formatPercentage(calculatePercentageChange(currentData.amount, previousData?.amount))}
                            </p>
                          </div>
                        </div>
                      )
                    }
                    return null
                  }}
                />
                <Legend />
                <Bar yAxisId="revenue" dataKey="amount" fill="#9333ea" name="Revenue" maxBarSize={60} />
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
                {monthlyRevenueData && monthlyRevenueData.length > 0 && (() => {
                  const currentDate = new Date()
                  const currentMonthIndex = currentDate.getMonth()
                  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                  const currentMonthName = monthNames[currentMonthIndex]
                  const currentMonthDataIndex = monthlyRevenueData.findIndex(item => item.month === currentMonthName)
                  const historicalMonths = currentMonthDataIndex > 0 
                    ? monthlyRevenueData.slice(0, currentMonthDataIndex).filter(item => item.amount > 0)
                    : monthlyRevenueData.filter(item => item.amount > 0 && item.month !== currentMonthName)
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
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
      </Card>

      {/* Top 10 Rental Customers */}
      <Card>
        <CardHeader>
          <CardTitle>Top 10 Rental Customers</CardTitle>
          <CardDescription>By total rental revenue</CardDescription>
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
      </Tabs>
    </div>
  )
}

export default RentalReport