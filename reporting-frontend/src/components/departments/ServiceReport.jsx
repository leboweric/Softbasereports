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
  Wrench,
  Clock,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Calendar,
  UserCheck,
  DollarSign,
  Download
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
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
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
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
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
            <CardTitle className="text-sm font-medium">Completed Today</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{serviceData.summary.completedToday}</div>
            <p className="text-xs text-muted-foreground">Work orders</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Repair Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{serviceData.summary.averageRepairTime}h</div>
            <p className="text-xs text-muted-foreground">Per work order</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Efficiency</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{serviceData.summary.technicianEfficiency}%</div>
            <p className="text-xs text-muted-foreground">Technician average</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${serviceData.summary.revenue.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Service income</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Customers Served</CardTitle>
            <UserCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{serviceData.summary.customersServed}</div>
            <p className="text-xs text-muted-foreground">This month</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Work Orders by Status */}
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Work Orders by Status</CardTitle>
            <CardDescription>Current distribution of work orders</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={serviceData.workOrdersByStatus}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, count }) => `${name}: ${count}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {serviceData.workOrdersByStatus.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Monthly Trend */}
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Service Trend</CardTitle>
            <CardDescription>Completed work orders and revenue over time</CardDescription>
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
                  label={{ value: 'Revenue ($)', angle: 90, position: 'insideRight' }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                />
                <Tooltip 
                  formatter={(value, name) => {
                    if (name === 'Revenue ($)') {
                      return [`$${value.toLocaleString()}`, name]
                    }
                    return [value, name]
                  }}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="completed"
                  stroke="#3b82f6"
                  name="Completed WOs"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6' }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="revenue"
                  stroke="#10b981"
                  name="Revenue ($)"
                  strokeWidth={2}
                  dot={{ fill: '#10b981' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Technician Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Technician Performance</CardTitle>
          <CardDescription>Top performing technicians this month</CardDescription>
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
              {openWODetails ? `${openWODetails.total_count} open work orders with labor service codes` : 'Loading...'}
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
  )
}

export default ServiceReport