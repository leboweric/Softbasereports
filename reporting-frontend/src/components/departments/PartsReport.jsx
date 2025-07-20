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
      const response = await fetch(`${apiUrl}/api/reports/departments/parts`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setPartsData(data)
      }
    } catch (error) {
      console.error('Error fetching parts data:', error)
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
      totalInventoryValue: 1245680,
      totalParts: 8934,
      lowStockItems: 45,
      pendingOrders: 23,
      monthlySales: 187450,
      turnoverRate: 4.2
    },
    inventoryByCategory: [
      { category: 'Filters', value: 125000, count: 2340 },
      { category: 'Hydraulic Parts', value: 345000, count: 1256 },
      { category: 'Engine Parts', value: 425000, count: 987 },
      { category: 'Electrical', value: 185000, count: 1543 },
      { category: 'Tires & Tracks', value: 165680, count: 234 }
    ],
    topMovingParts: [
      { partNumber: 'FL-1234', description: 'Oil Filter - CAT 320', quantity: 145, monthlyUsage: 45 },
      { partNumber: 'HY-5678', description: 'Hydraulic Hose 3/4"', quantity: 89, monthlyUsage: 38 },
      { partNumber: 'EN-9012', description: 'Air Filter - Komatsu', quantity: 76, monthlyUsage: 32 },
      { partNumber: 'EL-3456', description: 'Alternator Belt', quantity: 234, monthlyUsage: 28 },
      { partNumber: 'TR-7890', description: 'Track Pad - 600mm', quantity: 45, monthlyUsage: 12 }
    ],
    lowStockAlerts: [
      { partNumber: 'FL-4567', description: 'Fuel Filter - Volvo', currentStock: 3, reorderPoint: 10, status: 'Critical' },
      { partNumber: 'HY-1234', description: 'Hydraulic Pump Seal', currentStock: 5, reorderPoint: 15, status: 'Low' },
      { partNumber: 'EN-5678', description: 'Turbo Gasket', currentStock: 2, reorderPoint: 8, status: 'Critical' },
      { partNumber: 'EL-9012', description: 'Starter Motor', currentStock: 1, reorderPoint: 5, status: 'Critical' },
      { partNumber: 'BR-3456', description: 'Brake Pads Set', currentStock: 8, reorderPoint: 20, status: 'Low' }
    ],
    monthlyTrend: [
      { month: 'Jan', sales: 156000, orders: 234 },
      { month: 'Feb', sales: 178000, orders: 256 },
      { month: 'Mar', sales: 165000, orders: 245 },
      { month: 'Apr', sales: 189000, orders: 278 },
      { month: 'May', sales: 195000, orders: 289 },
      { month: 'Jun', sales: 187450, orders: 267 }
    ],
    recentOrders: [
      { orderNumber: 'PO-2024-001', supplier: 'CAT Parts Direct', items: 15, value: 12450, status: 'Shipped', eta: '2 days' },
      { orderNumber: 'PO-2024-002', supplier: 'Komatsu Supply', items: 8, value: 8900, status: 'Processing', eta: '5 days' },
      { orderNumber: 'PO-2024-003', supplier: 'Universal Hydraulics', items: 23, value: 15670, status: 'Delivered', eta: '-' },
      { orderNumber: 'PO-2024-004', supplier: 'Filters Plus', items: 45, value: 4560, status: 'Shipped', eta: '1 day' },
      { orderNumber: 'PO-2024-005', supplier: 'Track & Tire Co', items: 6, value: 34500, status: 'Ordered', eta: '7 days' }
    ]
  }

  const data = partsData || mockData

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