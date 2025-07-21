import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
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
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import { 
  Wrench,
  Clock,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Calendar,
  UserCheck,
  DollarSign,
  Download,
  Info
} from 'lucide-react'
import { apiUrl } from '@/lib/api'

const ServiceReport = ({ user, onNavigate }) => {
  const [serviceData, setServiceData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [openWOModalOpen, setOpenWOModalOpen] = useState(false)
  const [openWODetails, setOpenWODetails] = useState(null)
  const [loadingWODetails, setLoadingWODetails] = useState(false)

  useEffect(() => {
    fetchServiceData()
  }, [])

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
      }
    } catch (error) {
      console.error('Error fetching service data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchOpenWODetails = async () => {
    setLoadingWODetails(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/open-work-orders-detail'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setOpenWODetails(data)
      }
    } catch (error) {
      console.error('Failed to fetch work order details:', error)
    } finally {
      setLoadingWODetails(false)
    }
  }

  const handleOpenWOClick = () => {
    setOpenWOModalOpen(true)
    if (!openWODetails) {
      fetchOpenWODetails()
    }
  }

  const exportToCSV = () => {
    if (!openWODetails || !openWODetails.work_orders) return

    const headers = ['WO#', 'Sale Code', 'Customer', 'Serial#', 'Make', 'Model', 'Unit#', 'Type', 'Technician', 'Writer', 'Open Date', 'Dept', 'Branch', 'PO#', 'Comments']
    const rows = openWODetails.work_orders.map(wo => [
      wo.WONo || '',
      wo.SaleCode || '',
      wo.CustomerSale || '',
      wo.SerialNo || '',
      wo.Make || '',
      wo.Model || '',
      wo.UnitNo || '',
      wo.Type || '',
      wo.Technician || '',
      wo.Writer || '',
      wo.OpenDate ? new Date(wo.OpenDate).toLocaleDateString() : '',
      wo.SaleDept || '',
      wo.SaleBranch || '',
      wo.PONo || '',
      (wo.Comments || '').replace(/,/g, ';').replace(/\n/g, ' ')
    ])

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `open_work_orders_${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <LoadingSpinner 
        title="Loading Service Department" 
        description="Fetching work orders and technician data..."
        size="large"
      />
    )
  }

  if (!serviceData) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">
          <AlertCircle className="h-12 w-12 mx-auto mb-4" />
          <p>Unable to load service data. Please try again later.</p>
        </div>
      </div>
    )
  }

  return (
    <TooltipProvider>
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Service Department</h1>
          <p className="text-muted-foreground">Monitor service operations and technician performance</p>
        </div>
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => onNavigate && onNavigate('invoice-explorer')}
        >
          Explore Invoice Columns
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card 
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={handleOpenWOClick}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Open Work Orders</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{serviceData.summary.openWorkOrders}</div>
            <p className="text-xs text-muted-foreground">Click to view details</p>
          </CardContent>
        </Card>


        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              Shop Avg Repair Time
              <Tooltip>
                <TooltipTrigger>
                  <Info className="h-3 w-3 text-muted-foreground cursor-help" />
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  <p className="font-semibold mb-1">Calculation:</p>
                  <p className="text-sm">Average days between OpenDate and ClosedDate for all SHPCST work orders completed this month.</p>
                  <p className="text-sm mt-1">Formula: AVG(ClosedDate - OpenDate) in days</p>
                </TooltipContent>
              </Tooltip>
            </CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{serviceData.summary.shopAvgRepairTime || 0} days</div>
            <p className="text-xs text-muted-foreground">SHPCST per work order</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              Road Avg Repair Time
              <Tooltip>
                <TooltipTrigger>
                  <Info className="h-3 w-3 text-muted-foreground cursor-help" />
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  <p className="font-semibold mb-1">Calculation:</p>
                  <p className="text-sm">Average days between OpenDate and ClosedDate for all RDCST work orders completed this month.</p>
                  <p className="text-sm mt-1">Formula: AVG(ClosedDate - OpenDate) in days</p>
                </TooltipContent>
              </Tooltip>
            </CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{serviceData.summary.roadAvgRepairTime || 0} days</div>
            <p className="text-xs text-muted-foreground">RDCST per work order</p>
          </CardContent>
        </Card>

      </div>

      {/* Work Orders by Status - Split into Shop and Road */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Shop Work Orders by Status */}
        <Card>
          <CardHeader>
            <CardTitle>Shop Work Orders by Status (SHPCST)</CardTitle>
            <CardDescription>Distribution of shop work orders</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={serviceData.shopWorkOrdersByStatus || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, count }) => `${name}: ${count}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {(serviceData.shopWorkOrdersByStatus || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Road Work Orders by Status */}
        <Card>
          <CardHeader>
            <CardTitle>Road Work Orders by Status (RDCST)</CardTitle>
            <CardDescription>Distribution of road work orders</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={serviceData.roadWorkOrdersByStatus || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, count }) => `${name}: ${count}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {(serviceData.roadWorkOrdersByStatus || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Service Trends - Side by Side */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Shop Trend (SHPCST) */}
        <Card>
          <CardHeader>
            <CardTitle>Shop Service Trend (SHPCST)</CardTitle>
            <CardDescription>Completed work orders and average days to close</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={serviceData.monthlyTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis 
                  yAxisId="left"
                  label={{ value: 'Completed Work Orders', angle: -90, position: 'insideLeft' }}
                />
                <YAxis 
                  yAxisId="right"
                  orientation="right"
                  label={{ value: 'Avg Days to Close', angle: 90, position: 'insideRight' }}
                />
                <RechartsTooltip />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="shop_completed"
                  stroke="#3b82f6"
                  name="Completed"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6' }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="shop_avg_days"
                  stroke="#10b981"
                  name="Avg Days"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={{ fill: '#10b981' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Road Service Trend */}
        <Card>
        <CardHeader>
          <CardTitle>Road Service Trend (RDCST)</CardTitle>
          <CardDescription>Completed work orders and average days to close</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={serviceData.monthlyTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis 
                yAxisId="left"
                label={{ value: 'Completed Work Orders', angle: -90, position: 'insideLeft' }}
              />
              <YAxis 
                yAxisId="right"
                orientation="right"
                label={{ value: 'Avg Days to Close', angle: 90, position: 'insideRight' }}
              />
              <RechartsTooltip />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="road_completed"
                stroke="#ef4444"
                name="Completed"
                strokeWidth={2}
                dot={{ fill: '#ef4444' }}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="road_avg_days"
                stroke="#f59e0b"
                name="Avg Days"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ fill: '#f59e0b' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      </div>

      {/* Monthly Sales Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Sales Trend</CardTitle>
          <CardDescription>Combined SHPCST and RDCST sales revenue over time</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={serviceData.salesTrend || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis 
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                label={{ value: 'Revenue ($)', angle: -90, position: 'insideLeft' }}
              />
              <RechartsTooltip 
                formatter={(value) => [`$${value.toLocaleString()}`, '']}
                labelFormatter={(label) => `Month: ${label}`}
              />
              <Line
                type="monotone"
                dataKey="shop_sales"
                stroke="#3b82f6"
                name="Shop Sales (SHPCST)"
                strokeWidth={2}
                dot={{ fill: '#3b82f6' }}
              />
              <Line
                type="monotone"
                dataKey="road_sales"
                stroke="#ef4444"
                name="Road Sales (RDCST)"
                strokeWidth={2}
                dot={{ fill: '#ef4444' }}
              />
              <Line
                type="monotone"
                dataKey="total_sales"
                stroke="#10b981"
                name="Total Sales"
                strokeWidth={3}
                strokeDasharray="5 5"
                dot={{ fill: '#10b981' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Technician Performance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Technician Performance
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-3 w-3 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="font-semibold mb-1">Performance Metrics:</p>
                <p className="text-sm">• Completed WOs: Work orders completed in last 30 days</p>
                <p className="text-sm">• Efficiency: (Completed last 30 days) / (Completed last 30 days + Currently Open) × 100</p>
                <p className="text-sm mt-1">Only shows technicians with completed work orders in the last 30 days</p>
              </TooltipContent>
            </Tooltip>
          </CardTitle>
          <CardDescription>Top performing technicians (last 30 days)</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Technician</TableHead>
                <TableHead className="text-right">Completed WOs</TableHead>
                <TableHead className="text-right">Efficiency</TableHead>
                <TableHead>Performance</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {serviceData.technicianPerformance.map((tech) => (
                <TableRow key={tech.name}>
                  <TableCell className="font-medium">{tech.name}</TableCell>
                  <TableCell className="text-right">{tech.completed}</TableCell>
                  <TableCell className="text-right">{tech.efficiency}%</TableCell>
                  <TableCell>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${tech.efficiency}%` }}
                      />
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Recent Work Orders */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Work Orders</CardTitle>
          <CardDescription>Latest service requests and their status</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Work Order</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Equipment</TableHead>
                <TableHead>Technician</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {serviceData.recentWorkOrders.map((wo) => (
                <TableRow key={wo.id}>
                  <TableCell className="font-medium">{wo.id}</TableCell>
                  <TableCell>{wo.customer}</TableCell>
                  <TableCell>{wo.equipment}</TableCell>
                  <TableCell>{wo.technician}</TableCell>
                  <TableCell>
                    <Badge 
                      variant={wo.priority === 'High' ? 'destructive' : wo.priority === 'Medium' ? 'default' : 'secondary'}
                    >
                      {wo.priority}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge 
                      variant={
                        wo.status === 'Completed' ? 'success' : 
                        wo.status === 'In Progress' ? 'default' : 
                        wo.status === 'On Hold' ? 'destructive' : 'secondary'
                      }
                    >
                      {wo.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Open Work Orders Modal */}
      <Dialog open={openWOModalOpen} onOpenChange={setOpenWOModalOpen}>
        <DialogContent className="max-w-7xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Open Work Orders Detail</DialogTitle>
            <DialogDescription>
              {openWODetails ? `${openWODetails.total_count} open work orders (RDCST and SHPCST only)` : 'Loading...'}
            </DialogDescription>
          </DialogHeader>
          
          {loadingWODetails ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
          ) : openWODetails ? (
            <div className="flex-1 overflow-hidden flex flex-col">
              {/* Summary by SaleCode */}
              {openWODetails.summary_by_salecode && (
                <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                  <h3 className="font-semibold mb-2">Summary by Sale Code:</h3>
                  <div className="flex flex-wrap gap-3">
                    {openWODetails.summary_by_salecode.map((item) => (
                      <Badge key={item.SaleCode} variant="secondary" className="text-sm">
                        {item.SaleCode}: {item.count}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Export Button */}
              <div className="mb-4">
                <Button onClick={exportToCSV} size="sm" variant="outline">
                  <Download className="mr-2 h-4 w-4" />
                  Export to CSV
                </Button>
              </div>
              
              {/* Table */}
              <div className="flex-1 overflow-auto">
                <Table>
                  <TableHeader className="sticky top-0 bg-white z-10">
                    <TableRow>
                      <TableHead>WO#</TableHead>
                      <TableHead>Sale Code</TableHead>
                      <TableHead>Customer</TableHead>
                      <TableHead>Equipment</TableHead>
                      <TableHead>Serial#</TableHead>
                      <TableHead>Technician</TableHead>
                      <TableHead>Writer</TableHead>
                      <TableHead>Open Date</TableHead>
                      <TableHead>PO#</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {openWODetails.work_orders.map((wo) => (
                      <TableRow key={wo.WONo}>
                        <TableCell className="font-medium">{wo.WONo}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-xs">
                            {wo.SaleCode}
                          </Badge>
                        </TableCell>
                        <TableCell>{wo.CustomerSale}</TableCell>
                        <TableCell>{wo.Make} {wo.Model}</TableCell>
                        <TableCell>{wo.SerialNo}</TableCell>
                        <TableCell>{wo.Technician || '-'}</TableCell>
                        <TableCell>{wo.Writer || '-'}</TableCell>
                        <TableCell>
                          {wo.OpenDate ? new Date(wo.OpenDate).toLocaleDateString() : '-'}
                        </TableCell>
                        <TableCell>{wo.PONo || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No data available
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
    </TooltipProvider>
  )
}

export default ServiceReport