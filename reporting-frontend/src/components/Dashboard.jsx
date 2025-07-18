import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
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
  Cell
} from 'recharts'
import { 
  DollarSign, 
  TrendingUp, 
  Package, 
  Users,
  FileText,
  Download
} from 'lucide-react'
import { apiUrl } from '@/lib/api'

const Dashboard = ({ user }) => {
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [inventoryModalOpen, setInventoryModalOpen] = useState(false)
  const [inventoryDetails, setInventoryDetails] = useState(null)
  const [loadingInventory, setLoadingInventory] = useState(false)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/dashboard/summary'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setDashboardData(data)
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchInventoryDetails = async () => {
    setLoadingInventory(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/inventory-details'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setInventoryDetails(data)
      }
    } catch (error) {
      console.error('Failed to fetch inventory details:', error)
    } finally {
      setLoadingInventory(false)
    }
  }

  const handleInventoryClick = () => {
    setInventoryModalOpen(true)
    if (!inventoryDetails) {
      fetchInventoryDetails()
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

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

  if (loading) {
    return (
      <div className="space-y-6">
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
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back, {user?.first_name}! Here's what's happening with your business.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
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

        <Card 
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={handleInventoryClick}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rental Units Available</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardData?.inventory_count || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Units available • Click for details
            </p>
          </CardContent>
        </Card>

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
              Last 30 days
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
              {dashboardData?.uninvoiced_count || 0} orders pending
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts - First Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Monthly Sales</CardTitle>
            <CardDescription>
              Sales performance over the last 12 months
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={dashboardData?.monthly_sales || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value) => formatCurrency(value)} />
                <Bar dataKey="amount" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Monthly Gross Profit</CardTitle>
            <CardDescription>
              Sales minus Cost of Sales over the last 12 months
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={dashboardData?.monthly_gross_profit || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value) => formatCurrency(value)} />
                <Bar dataKey="amount" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Charts - Second Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Monthly Quotes</CardTitle>
            <CardDescription>
              Total dollar value quoted each month since March
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={dashboardData?.monthly_quotes || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value) => formatCurrency(value)} />
                <Bar dataKey="amount" fill="#f59e0b" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Department Gross Margins %</CardTitle>
            <CardDescription>
              Margin percentages by department over time
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={dashboardData?.department_margins || []}>
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
      </div>

      {/* Top 10 Customers */}
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
                  <div className="text-sm font-medium text-gray-900">
                    {formatCurrency(customer.sales)}
                  </div>
                </div>
              )) || (
                <p className="text-sm text-gray-500">No customer data available</p>
              )}
            </div>
          </CardContent>
        </Card>
        
        {/* Placeholder for future card */}
        <div />
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common tasks and reports
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Button variant="outline" className="h-20 flex-col">
              <FileText className="h-6 w-6 mb-2" />
              Sales Report
            </Button>
            <Button variant="outline" className="h-20 flex-col">
              <Package className="h-6 w-6 mb-2" />
              Inventory Report
            </Button>
            <Button variant="outline" className="h-20 flex-col">
              <Users className="h-6 w-6 mb-2" />
              Customer Report
            </Button>
            <Button variant="outline" className="h-20 flex-col">
              <TrendingUp className="h-6 w-6 mb-2" />
              Financial Summary
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Inventory Details Modal */}
      <Dialog open={inventoryModalOpen} onOpenChange={setInventoryModalOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Available Inventory Details</DialogTitle>
            <DialogDescription>
              Equipment currently available for rent
            </DialogDescription>
          </DialogHeader>
          
          {loadingInventory ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
          ) : inventoryDetails && inventoryDetails.equipment ? (
            <div className="mt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Unit #</TableHead>
                    <TableHead>Make</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Year</TableHead>
                    <TableHead>Serial #</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead className="text-right">Hours</TableHead>
                    <TableHead className="text-right">Cost</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {inventoryDetails.equipment.map((item, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{item.unitNo}</TableCell>
                      <TableCell>{item.make}</TableCell>
                      <TableCell>{item.model}</TableCell>
                      <TableCell>{item.year || '-'}</TableCell>
                      <TableCell>{item.serialNo}</TableCell>
                      <TableCell>{item.location || '-'}</TableCell>
                      <TableCell className="text-right">{item.hours.toFixed(0)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(item.cost)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              <div className="mt-4 text-sm text-muted-foreground">
                Total: {inventoryDetails.total} units available
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No inventory data available
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default Dashboard

