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
  Cell
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
import Check145Debug from './Check145Debug'

const RentalReport = ({ user }) => {
  const [rentalData, setRentalData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchRentalData()
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
          <TabsTrigger value="check-145">Check 145 Debug</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Fleet</CardTitle>
            <Truck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.summary.totalFleetSize}</div>
            <p className="text-xs text-muted-foreground">Equipment units</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">On Rent</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.summary.unitsOnRent}</div>
            <p className="text-xs text-muted-foreground">Active rentals</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Utilization</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold" style={{ color: utilizationColor }}>
              {data.summary.utilizationRate}%
            </div>
            <p className="text-xs text-muted-foreground">Fleet utilization</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${data.summary.monthlyRevenue.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Rental income</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overdue</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{data.summary.overdueReturns}</div>
            <p className="text-xs text-muted-foreground">Returns overdue</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Maintenance</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{data.summary.maintenanceDue}</div>
            <p className="text-xs text-muted-foreground">Units due service</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Fleet by Category */}
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Fleet by Category</CardTitle>
            <CardDescription>Equipment availability by type</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.fleetByCategory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="onRent" stackId="a" fill="#3b82f6" name="On Rent" />
                <Bar dataKey="available" stackId="a" fill="#10b981" name="Available" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Revenue Trend */}
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Revenue & Utilization Trend</CardTitle>
            <CardDescription>Monthly rental performance metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.monthlyTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="revenue"
                  stroke="#3b82f6"
                  name="Revenue ($)"
                  strokeWidth={2}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="utilization"
                  stroke="#10b981"
                  name="Utilization (%)"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Rentals by Duration */}
      <Card>
        <CardHeader>
          <CardTitle>Rentals by Duration</CardTitle>
          <CardDescription>Distribution of rental contracts by duration type</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data.rentalsByDuration} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="duration" />
              <YAxis yAxisId="left" orientation="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Bar yAxisId="left" dataKey="count" fill="#3b82f6" name="Count" />
              <Bar yAxisId="right" dataKey="revenue" fill="#10b981" name="Revenue ($)" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Active Rentals */}
        <Card>
          <CardHeader>
            <CardTitle>Active Rentals</CardTitle>
            <CardDescription>Current rental contracts</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Contract</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Equipment</TableHead>
                  <TableHead>Daily Rate</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.activeRentals.map((rental) => (
                  <TableRow key={rental.contractNumber}>
                    <TableCell className="font-medium">{rental.contractNumber}</TableCell>
                    <TableCell>{rental.customer}</TableCell>
                    <TableCell className="max-w-[200px] truncate">{rental.equipment}</TableCell>
                    <TableCell>${rental.dailyRate}</TableCell>
                    <TableCell>
                      <Badge 
                        variant={
                          rental.status === 'Overdue' ? 'destructive' : 
                          rental.status === 'Due Soon' ? 'default' : 'success'
                        }
                      >
                        {rental.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Top Customers */}
        <Card>
          <CardHeader>
            <CardTitle>Top Customers</CardTitle>
            <CardDescription>Most active rental customers</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer</TableHead>
                  <TableHead className="text-right">Active</TableHead>
                  <TableHead className="text-right">Revenue</TableHead>
                  <TableHead className="text-right">Avg Days</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.topCustomers.map((customer) => (
                  <TableRow key={customer.name}>
                    <TableCell className="font-medium">{customer.name}</TableCell>
                    <TableCell className="text-right">{customer.activeRentals}</TableCell>
                    <TableCell className="text-right">${customer.totalRevenue.toLocaleString()}</TableCell>
                    <TableCell className="text-right">{customer.avgDuration}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
        </TabsContent>

        <TabsContent value="service-report">
          <RentalServiceReport />
        </TabsContent>

        <TabsContent value="check-145">
          <Check145Debug />
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default RentalReport