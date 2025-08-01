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
  Package,
  TrendingUp,
  AlertTriangle,
  DollarSign,
  ShoppingCart,
  Truck,
  BarChart3,
  Clock
} from 'lucide-react'
import { apiUrl } from '@/lib/api'

const PartsReport = ({ user }) => {
  const [partsData, setPartsData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPartsData()
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
          summary: {
            totalInventoryValue: 0,
            totalParts: 0,
            lowStockItems: 0,
            pendingOrders: 0,
            monthlySales: 0,
            turnoverRate: 0
          },
          inventoryByCategory: [],
          topMovingParts: [],
          lowStockAlerts: [],
          monthlyTrend: [],
          recentOrders: [],
          monthlyPartsRevenue: []
        })
      }
    } catch (error) {
      console.error('Error fetching parts data:', error)
      // Set default empty data structure on error
      setPartsData({
        summary: {
          totalInventoryValue: 0,
          totalParts: 0,
          lowStockItems: 0,
          pendingOrders: 0,
          monthlySales: 0,
          turnoverRate: 0
        },
        inventoryByCategory: [],
        topMovingParts: [],
        lowStockAlerts: [],
        monthlyTrend: [],
        recentOrders: [],
        monthlyPartsRevenue: []
      })
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

  const data = partsData || {
    summary: {
      totalInventoryValue: 0,
      totalParts: 0,
      lowStockItems: 0,
      pendingOrders: 0,
      monthlySales: 0,
      turnoverRate: 0
    },
    inventoryByCategory: [],
    topMovingParts: [],
    lowStockAlerts: [],
    monthlyTrend: [],
    recentOrders: [],
    monthlyPartsRevenue: []
  }

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Parts Department</h1>
        <p className="text-muted-foreground">Inventory management and parts sales analytics</p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Inventory Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${data.summary.totalInventoryValue.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Total stock value</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Parts</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.summary.totalParts.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">In inventory</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Low Stock</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{data.summary.lowStockItems}</div>
            <p className="text-xs text-muted-foreground">Items need reorder</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Orders</CardTitle>
            <ShoppingCart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.summary.pendingOrders}</div>
            <p className="text-xs text-muted-foreground">From suppliers</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Sales</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${data.summary.monthlySales.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Parts revenue</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Turnover Rate</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.summary.turnoverRate}x</div>
            <p className="text-xs text-muted-foreground">Annual average</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Inventory by Category */}
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Inventory by Category</CardTitle>
            <CardDescription>Value distribution across part categories</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={data.inventoryByCategory}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ category, value }) => `${category}: $${(value/1000).toFixed(0)}k`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {data.inventoryByCategory.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Monthly Sales Trend */}
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Sales Trend</CardTitle>
            <CardDescription>Monthly parts sales and order volume</CardDescription>
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
                  dataKey="sales"
                  stroke="#3b82f6"
                  name="Sales ($)"
                  strokeWidth={2}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="orders"
                  stroke="#10b981"
                  name="Orders"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Parts Revenue */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Parts Revenue</CardTitle>
          <CardDescription>Parts revenue over the last 12 months</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={partsData?.monthlyPartsRevenue || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis 
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip 
                formatter={(value) => `$${value.toLocaleString()}`}
              />
              <Bar dataKey="amount" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Top Moving Parts */}
        <Card>
          <CardHeader>
            <CardTitle>Top Moving Parts</CardTitle>
            <CardDescription>Fastest moving inventory items</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Part Number</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Stock</TableHead>
                  <TableHead className="text-right">Monthly Usage</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.topMovingParts.map((part) => (
                  <TableRow key={part.partNumber}>
                    <TableCell className="font-medium">{part.partNumber}</TableCell>
                    <TableCell>{part.description}</TableCell>
                    <TableCell className="text-right">{part.quantity}</TableCell>
                    <TableCell className="text-right">{part.monthlyUsage}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Low Stock Alerts */}
        <Card>
          <CardHeader>
            <CardTitle>Low Stock Alerts</CardTitle>
            <CardDescription>Parts requiring immediate attention</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Part Number</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Stock</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.lowStockAlerts.map((part) => (
                  <TableRow key={part.partNumber}>
                    <TableCell className="font-medium">{part.partNumber}</TableCell>
                    <TableCell>{part.description}</TableCell>
                    <TableCell className="text-right">{part.currentStock}/{part.reorderPoint}</TableCell>
                    <TableCell>
                      <Badge variant={part.status === 'Critical' ? 'destructive' : 'default'}>
                        {part.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Recent Orders */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Purchase Orders</CardTitle>
          <CardDescription>Incoming parts orders from suppliers</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Order Number</TableHead>
                <TableHead>Supplier</TableHead>
                <TableHead className="text-right">Items</TableHead>
                <TableHead className="text-right">Value</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>ETA</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.recentOrders.map((order) => (
                <TableRow key={order.orderNumber}>
                  <TableCell className="font-medium">{order.orderNumber}</TableCell>
                  <TableCell>{order.supplier}</TableCell>
                  <TableCell className="text-right">{order.items}</TableCell>
                  <TableCell className="text-right">${order.value.toLocaleString()}</TableCell>
                  <TableCell>
                    <Badge 
                      variant={
                        order.status === 'Delivered' ? 'success' : 
                        order.status === 'Shipped' ? 'default' : 
                        order.status === 'Processing' ? 'secondary' : 'outline'
                      }
                    >
                      {order.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      {order.eta !== '-' && <Clock className="h-3 w-3" />}
                      {order.eta}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

export default PartsReport