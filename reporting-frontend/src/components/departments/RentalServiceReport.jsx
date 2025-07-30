import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { DollarSign, Wrench, TrendingUp, FileText } from 'lucide-react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { apiUrl } from '@/lib/api'

const RentalServiceReport = () => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [summary, setSummary] = useState(null)
  const [workOrders, setWorkOrders] = useState([])
  const [monthlyTrend, setMonthlyTrend] = useState([])

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl('/api/reports/departments/rental/service-report'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch rental service report')
      }

      const data = await response.json()
      setSummary(data.summary)
      setWorkOrders(data.workOrders)
      setMonthlyTrend(data.monthlyTrend.reverse()) // Reverse to show oldest to newest
      setError(null)
    } catch (err) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value)
  }

  const getStatusBadge = (status) => {
    const variants = {
      'Open': 'destructive',
      'Completed': 'secondary',
      'Invoiced': 'default',
      'Closed': 'outline'
    }
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-red-600 text-center py-4">
        Error loading rental service report: {error}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Open Work Orders</CardTitle>
            <Wrench className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.totalWorkOrders || 0}</div>
            <p className="text-xs text-muted-foreground">
              Currently open
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Labor Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary?.totalLaborCost || 0)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Parts Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary?.totalPartsCost || 0)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Misc Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary?.totalMiscCost || 0)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary?.totalCost || 0)}</div>
            <p className="text-xs text-muted-foreground">
              Avg: {formatCurrency(summary?.averageCostPerWO || 0)}/WO
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Trend Chart */}
      {monthlyTrend.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Monthly Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={monthlyTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="monthName" />
                <YAxis />
                <Tooltip formatter={(value) => formatCurrency(value)} />
                <Legend />
                <Line type="monotone" dataKey="totalCost" stroke="#ef4444" name="Total Cost" />
                <Line type="monotone" dataKey="laborCost" stroke="#3b82f6" name="Labor Cost" />
                <Line type="monotone" dataKey="partsCost" stroke="#10b981" name="Parts Cost" />
                <Line type="monotone" dataKey="miscCost" stroke="#f59e0b" name="Misc Cost" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Work Orders Table */}
      <Card>
        <CardHeader>
          <CardTitle>Open Service Work Orders for Rental Department</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>WO#</TableHead>
                  <TableHead>Equipment</TableHead>
                  <TableHead>Make/Model</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Open Date</TableHead>
                  <TableHead className="text-right">Labor Cost</TableHead>
                  <TableHead className="text-right">Parts Cost</TableHead>
                  <TableHead className="text-right">Misc Cost</TableHead>
                  <TableHead className="text-right">Total Cost</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workOrders.map((wo) => (
                  <TableRow key={wo.woNumber}>
                    <TableCell className="font-medium">{wo.woNumber}</TableCell>
                    <TableCell>{wo.equipment || 'N/A'}</TableCell>
                    <TableCell>{wo.make && wo.model ? `${wo.make} ${wo.model}` : 'N/A'}</TableCell>
                    <TableCell>{getStatusBadge(wo.status)}</TableCell>
                    <TableCell>{wo.openDate}</TableCell>
                    <TableCell className="text-right">{formatCurrency(wo.laborCost)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(wo.partsCost)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(wo.miscCost)}</TableCell>
                    <TableCell className="text-right font-medium">{formatCurrency(wo.totalCost)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
              <TableRow className="bg-gray-50 font-bold">
                <TableCell colSpan={5}>Total</TableCell>
                <TableCell className="text-right">
                  {formatCurrency(summary?.totalLaborCost || 0)}
                </TableCell>
                <TableCell className="text-right">
                  {formatCurrency(summary?.totalPartsCost || 0)}
                </TableCell>
                <TableCell className="text-right">
                  {formatCurrency(summary?.totalMiscCost || 0)}
                </TableCell>
                <TableCell className="text-right">
                  {formatCurrency(summary?.totalCost || 0)}
                </TableCell>
              </TableRow>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Cost Breakdown Chart */}
      {workOrders.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Cost Breakdown by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={[
                  {
                    category: 'Labor',
                    cost: summary?.totalLaborCost || 0
                  },
                  {
                    category: 'Parts',
                    cost: summary?.totalPartsCost || 0
                  },
                  {
                    category: 'Misc',
                    cost: summary?.totalMiscCost || 0
                  }
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip formatter={(value) => formatCurrency(value)} />
                <Bar dataKey="cost" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default RentalServiceReport