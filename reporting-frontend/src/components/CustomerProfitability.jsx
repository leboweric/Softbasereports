import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { CheckCircle, XCircle, TrendingUp, TrendingDown, DollarSign, AlertTriangle, Users, Target, Flame } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { apiUrl } from '@/lib/api'

const CustomerProfitability = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sortField, setSortField] = useState('margin_percent')
  const [sortDirection, setSortDirection] = useState('asc') // Show worst first
  const [healthFilter, setHealthFilter] = useState('all') // 'all', 'healthy', 'warning', 'critical'
  const [showFireList, setShowFireList] = useState(false)
  const [dateFilterType, setDateFilterType] = useState('trailing') // 'trailing', 'range'
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const formatPercent = (value) => {
    return `${value.toFixed(1)}%`
  }

  useEffect(() => {
    fetchProfitabilityData()
  }, [])

  const fetchProfitabilityData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      // Build query params based on date filter type
      let queryParams = ''
      if (dateFilterType === 'range' && startDate && endDate) {
        queryParams = `?start_date=${startDate}&end_date=${endDate}`
      }
      // If 'trailing', no params needed (default 12 months)
      
      const response = await fetch(apiUrl(`/api/reports/departments/customer-profitability${queryParams}`), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const result = await response.json()
        if (result.success) {
          setData(result)
        } else {
          setError(result.error || 'Failed to load data')
        }
      } else {
        setError('Failed to fetch profitability data')
      }
    } catch (err) {
      console.error('Error fetching profitability data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const getFilteredAndSortedCustomers = () => {
    if (!data?.customers) return []

    let filtered = data.customers

    // Apply health filter
    if (healthFilter !== 'all') {
      filtered = filtered.filter(c => c.health_status === healthFilter)
    }

    // Sort
    return [...filtered].sort((a, b) => {
      let aVal = a[sortField]
      let bVal = b[sortField]

      // Handle string vs number sorting
      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase()
        bVal = bVal.toLowerCase()
      }

      if (sortDirection === 'asc') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })
  }

  const SortHeader = ({ field, children }) => (
    <TableHead
      className="cursor-pointer hover:bg-gray-100 select-none"
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center gap-1">
        {children}
        {sortField === field && (
          <span className="text-xs">{sortDirection === 'asc' ? '↑' : '↓'}</span>
        )}
      </div>
    </TableHead>
  )

  const getHealthBadge = (status) => {
    const variants = {
      healthy: { variant: 'success', icon: CheckCircle, text: 'Healthy' },
      warning: { variant: 'warning', icon: AlertTriangle, text: 'Warning' },
      critical: { variant: 'destructive', icon: XCircle, text: 'Critical' }
    }
    
    const config = variants[status] || variants.warning
    const Icon = config.icon
    
    return (
      <Badge variant={config.variant} className="flex items-center gap-1 w-fit">
        <Icon className="h-3 w-3" />
        {config.text}
      </Badge>
    )
  }

  const getActionBadge = (action) => {
    const colors = {
      'Maintain': 'bg-green-100 text-green-800 border-green-300',
      'Monitor': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'Raise Prices': 'bg-orange-100 text-orange-800 border-orange-300',
      'Urgent - Raise Prices': 'bg-red-100 text-red-800 border-red-300',
      'Consider Termination': 'bg-gray-100 text-gray-800 border-gray-300'
    }
    
    return (
      <Badge className={`${colors[action] || colors['Monitor']} border`}>
        {action}
      </Badge>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800">Error: {error}</p>
      </div>
    )
  }

  if (!data) {
    return <div>No data available</div>
  }

  const { summary, customers, fire_list } = data
  const filteredCustomers = getFilteredAndSortedCustomers()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Customer Profitability Analysis</h1>
        <p className="text-muted-foreground mt-2">
          Comprehensive profitability analysis with actionable recommendations
        </p>
      </div>

      {/* Date Filter Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Date Range</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-end">
            <div>
              <label className="block text-sm font-medium mb-2">Filter Type</label>
              <select
                value={dateFilterType}
                onChange={(e) => setDateFilterType(e.target.value)}
                className="border rounded px-3 py-2"
              >
                <option value="trailing">Trailing 12 Months</option>
                <option value="range">Custom Range</option>
              </select>
            </div>

            {dateFilterType === 'range' && (
              <>
                <div>
                  <label className="block text-sm font-medium mb-2">Start Date</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">End Date</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                </div>
              </>
            )}

            <Button onClick={fetchProfitabilityData}>
              Apply Filter
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Executive Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Customers</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.total_customers}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {summary.healthy_pct}% Healthy · {summary.warning_pct}% Warning · {summary.critical_pct}% Critical
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary.total_revenue)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {formatCurrency(summary.total_cost)} in costs
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Margin</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${summary.overall_margin >= 30 ? 'text-green-600' : summary.overall_margin >= 0 ? 'text-yellow-600' : 'text-red-600'}`}>
              {formatPercent(summary.overall_margin)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {formatCurrency(summary.total_profit)} profit
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Revenue at Risk</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{formatCurrency(summary.revenue_at_risk)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              From {summary.critical_count} unprofitable customers
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Health Status Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Customer Health Distribution</CardTitle>
          <CardDescription>Breakdown by profitability status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center justify-center gap-2 mb-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span className="font-semibold text-green-800">Healthy</span>
              </div>
              <div className="text-3xl font-bold text-green-600">{summary.healthy_count}</div>
              <p className="text-sm text-green-700 mt-1">Margin ≥ 30%</p>
            </div>

            <div className="text-center p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <div className="flex items-center justify-center gap-2 mb-2">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                <span className="font-semibold text-yellow-800">Warning</span>
              </div>
              <div className="text-3xl font-bold text-yellow-600">{summary.warning_count}</div>
              <p className="text-sm text-yellow-700 mt-1">Margin 0-30%</p>
            </div>

            <div className="text-center p-4 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-center justify-center gap-2 mb-2">
                <XCircle className="h-5 w-5 text-red-600" />
                <span className="font-semibold text-red-800">Critical</span>
              </div>
              <div className="text-3xl font-bold text-red-600">{summary.critical_count}</div>
              <p className="text-sm text-red-700 mt-1">Margin &lt; 0%</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Fire List Alert */}
      {fire_list && fire_list.length > 0 && (
        <Card className="border-red-300 bg-red-50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Flame className="h-5 w-5 text-red-600" />
                <CardTitle className="text-red-800">Termination Candidates</CardTitle>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowFireList(!showFireList)}
              >
                {showFireList ? 'Hide' : 'Show'} {fire_list.length} Customers
              </Button>
            </div>
            <CardDescription className="text-red-700">
              Unprofitable small accounts (Revenue &lt; $10,000, Negative Margin)
            </CardDescription>
          </CardHeader>
          {showFireList && (
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Customer</TableHead>
                    <TableHead className="text-right">Revenue</TableHead>
                    <TableHead className="text-right">Cost</TableHead>
                    <TableHead className="text-right">Loss</TableHead>
                    <TableHead className="text-right">Margin</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {fire_list.map((customer) => (
                    <TableRow key={customer.customer_number}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{customer.customer_name}</div>
                          <div className="text-sm text-muted-foreground">#{customer.customer_number}</div>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">{formatCurrency(customer.total_revenue)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(customer.total_cost)}</TableCell>
                      <TableCell className="text-right text-red-600 font-semibold">
                        {formatCurrency(customer.gross_profit)}
                      </TableCell>
                      <TableCell className="text-right text-red-600 font-semibold">
                        {formatPercent(customer.margin_percent)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          )}
        </Card>
      )}

      {/* Customer Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Customer Profitability Details</CardTitle>
              <CardDescription>
                {filteredCustomers.length} customers shown
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant={healthFilter === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setHealthFilter('all')}
              >
                All
              </Button>
              <Button
                variant={healthFilter === 'healthy' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setHealthFilter('healthy')}
              >
                Healthy
              </Button>
              <Button
                variant={healthFilter === 'warning' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setHealthFilter('warning')}
              >
                Warning
              </Button>
              <Button
                variant={healthFilter === 'critical' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setHealthFilter('critical')}
              >
                Critical
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <SortHeader field="customer_name">Customer</SortHeader>
                  <SortHeader field="total_revenue">Revenue</SortHeader>
                  <SortHeader field="total_cost">Cost</SortHeader>
                  <SortHeader field="gross_profit">Profit</SortHeader>
                  <SortHeader field="margin_percent">Margin</SortHeader>
                  <TableHead>Health</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Recommendation</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCustomers.map((customer) => (
                  <TableRow key={customer.customer_number}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{customer.customer_name}</div>
                        <div className="text-sm text-muted-foreground">
                          #{customer.customer_number} · {customer.invoice_count} invoices
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {formatCurrency(customer.total_revenue)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(customer.total_cost)}
                      <div className="text-xs text-muted-foreground">
                        {customer.total_hours}h
                      </div>
                    </TableCell>
                    <TableCell className={`text-right font-semibold ${customer.gross_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(customer.gross_profit)}
                    </TableCell>
                    <TableCell className={`text-right font-semibold ${customer.margin_percent >= 30 ? 'text-green-600' : customer.margin_percent >= 0 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {formatPercent(customer.margin_percent)}
                    </TableCell>
                    <TableCell>
                      {getHealthBadge(customer.health_status)}
                    </TableCell>
                    <TableCell>
                      {getActionBadge(customer.action)}
                    </TableCell>
                    <TableCell className="max-w-xs">
                      <div className="text-sm">
                        {customer.message}
                        {customer.recommended_increase_pct && (
                          <div className="text-xs text-muted-foreground mt-1">
                            Increase: {formatCurrency(customer.recommended_increase)} ({formatPercent(customer.recommended_increase_pct)})
                          </div>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Notes */}
      <Card>
        <CardHeader>
          <CardTitle>Report Notes</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm text-muted-foreground">
            <p><strong>Revenue:</strong> {data.notes.revenue}</p>
            <p><strong>Costs:</strong> {data.notes.costs}</p>
            <p><strong>Healthy:</strong> {data.notes.health_healthy}</p>
            <p><strong>Warning:</strong> {data.notes.health_warning}</p>
            <p><strong>Critical:</strong> {data.notes.health_critical}</p>
            <p><strong>Fire List Criteria:</strong> {data.notes.fire_list_criteria}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CustomerProfitability
