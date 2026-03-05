import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { CheckCircle, XCircle, TrendingUp, TrendingDown, DollarSign, AlertTriangle, Users, Target, Flame, ChevronDown, ChevronRight, X } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { apiUrl } from '@/lib/api'

const CustomerProfitability = ({ department = 'all' }) => {
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
  const [drillDownCustomer, setDrillDownCustomer] = useState(null) // { customer_number, customer_name }
  const [drillDownData, setDrillDownData] = useState(null)
  const [drillDownLoading, setDrillDownLoading] = useState(false)
  const [drillDownError, setDrillDownError] = useState(null)
  const [expandedWOs, setExpandedWOs] = useState(new Set())

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
      
      // Add department filter if specified (e.g., 'service' for Service page)
      const deptParam = department !== 'all' ? `${queryParams ? '&' : '?'}department=${department}` : ''
      const response = await fetch(apiUrl(`/api/reports/departments/customer-profitability${queryParams}${deptParam}`), {
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

  const fetchDrillDown = async (customerNumber) => {
    setDrillDownLoading(true)
    setDrillDownError(null)
    setDrillDownData(null)
    setExpandedWOs(new Set())
    try {
      const token = localStorage.getItem('token')
      let params = `customer_number=${customerNumber}&department=${department}`
      if (dateFilterType === 'range' && startDate && endDate) {
        params += `&start_date=${startDate}&end_date=${endDate}`
      }
      const response = await fetch(apiUrl(`/api/reports/departments/customer-profitability/wo-detail?${params}`), {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const result = await response.json()
        if (result.success) {
          setDrillDownData(result)
        } else {
          setDrillDownError(result.error || 'Failed to load WO detail')
        }
      } else {
        setDrillDownError('Failed to fetch WO detail')
      }
    } catch (err) {
      setDrillDownError(err.message)
    } finally {
      setDrillDownLoading(false)
    }
  }

  const openDrillDown = (customer) => {
    setDrillDownCustomer(customer)
    fetchDrillDown(customer.customer_number.split(' ')[0]) // Handle "QUA001 (+1 more)" format
  }

  const toggleWOExpand = (woNumber) => {
    setExpandedWOs(prev => {
      const next = new Set(prev)
      if (next.has(woNumber)) next.delete(woNumber)
      else next.add(woNumber)
      return next
    })
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

      {/* Top 5 and Bottom 5 Customers */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Top 5 Most Profitable */}
        <Card className="border-green-300 bg-green-50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              <CardTitle className="text-green-800">Top 5 Most Profitable</CardTitle>
            </div>
            <CardDescription className="text-green-700">
              Customers with highest profit margins
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data?.customers
                ?.slice()
                .sort((a, b) => b.gross_profit - a.gross_profit)
                .slice(0, 5)
                .map((customer, index) => (
                  <div key={customer.customer_number} className="flex items-center justify-between p-3 bg-white rounded-lg border border-green-200">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-green-100 text-green-700 font-bold text-sm">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-medium text-sm">{customer.customer_name}</div>
                        <div className="text-xs text-muted-foreground">#{customer.customer_number}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-green-600">{formatCurrency(customer.gross_profit)}</div>
                      <div className="text-xs text-green-700">{formatPercent(customer.margin_percent)}</div>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>

        {/* Bottom 5 Least Profitable */}
        <Card className="border-red-300 bg-red-50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingDown className="h-5 w-5 text-red-600" />
              <CardTitle className="text-red-800">Bottom 5 Least Profitable</CardTitle>
            </div>
            <CardDescription className="text-red-700">
              Customers with lowest profit margins
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data?.customers
                ?.slice()
                .sort((a, b) => a.gross_profit - b.gross_profit)
                .slice(0, 5)
                .map((customer, index) => (
                  <div key={customer.customer_number} className="flex items-center justify-between p-3 bg-white rounded-lg border border-red-200">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-red-100 text-red-700 font-bold text-sm">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-medium text-sm">{customer.customer_name}</div>
                        <div className="text-xs text-muted-foreground">#{customer.customer_number}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-red-600">{formatCurrency(customer.gross_profit)}</div>
                      <div className="text-xs text-red-700">{formatPercent(customer.margin_percent)}</div>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      </div>

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
                  <TableHead className="w-16">Detail</TableHead>
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
                    <TableCell className="w-16">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openDrillDown(customer)}
                        className="text-xs"
                      >
                        WOs
                      </Button>
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
                      <div className="text-sm truncate" title={customer.message}>
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

      {/* WO Drill-Down Modal */}
      {drillDownCustomer && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center overflow-y-auto pt-8 pb-8">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl mx-4">
            <div className="flex items-center justify-between p-4 border-b">
              <div>
                <h2 className="text-lg font-bold">{drillDownCustomer.customer_name}</h2>
                <p className="text-sm text-muted-foreground">#{drillDownCustomer.customer_number} — Work Order Cost Breakdown</p>
              </div>
              <button onClick={() => setDrillDownCustomer(null)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-4">
              {drillDownLoading && (
                <div className="flex items-center justify-center h-32"><LoadingSpinner /></div>
              )}
              {drillDownError && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">{drillDownError}</div>
              )}
              {drillDownData && (
                <>
                  {/* Summary */}
                  <div className="grid grid-cols-4 gap-4 mb-4">
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <div className="text-xs text-muted-foreground">Work Orders</div>
                      <div className="text-xl font-bold">{drillDownData.wo_count}</div>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-3 text-center">
                      <div className="text-xs text-muted-foreground">Labor Cost</div>
                      <div className="text-xl font-bold text-blue-700">{formatCurrency(drillDownData.total_labor_cost)}</div>
                    </div>
                    <div className="bg-orange-50 rounded-lg p-3 text-center">
                      <div className="text-xs text-muted-foreground">Parts Cost</div>
                      <div className="text-xl font-bold text-orange-700">{formatCurrency(drillDownData.total_parts_cost)}</div>
                    </div>
                    <div className="bg-purple-50 rounded-lg p-3 text-center">
                      <div className="text-xs text-muted-foreground">Total Cost</div>
                      <div className="text-xl font-bold text-purple-700">{formatCurrency(drillDownData.total_cost)}</div>
                    </div>
                  </div>
                  {/* WO List */}
                  <div className="space-y-2 max-h-[60vh] overflow-y-auto">
                    {drillDownData.work_orders.map((wo) => (
                      <div key={wo.wo_number} className="border rounded-lg">
                        <div
                          className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50"
                          onClick={() => toggleWOExpand(wo.wo_number)}
                        >
                          <div className="flex items-center gap-3">
                            {expandedWOs.has(wo.wo_number)
                              ? <ChevronDown className="h-4 w-4 text-gray-400" />
                              : <ChevronRight className="h-4 w-4 text-gray-400" />}
                            <div>
                              <span className="font-mono font-medium text-sm">{wo.wo_number}</span>
                              <span className="ml-2 text-xs text-muted-foreground">{wo.type} · {wo.date}</span>
                              {wo.unit_no && <span className="ml-2 text-xs text-muted-foreground">Unit: {wo.unit_no}</span>}
                              {wo.technician && <span className="ml-2 text-xs text-muted-foreground">Tech: {wo.technician}</span>}
                            </div>
                          </div>
                          <div className="flex items-center gap-4 text-sm">
                            <span className="text-blue-700">Labor: {formatCurrency(wo.labor_cost)}</span>
                            <span className="text-orange-700">Parts: {formatCurrency(wo.parts_cost)}</span>
                            <span className="font-semibold">Total: {formatCurrency(wo.total_cost)}</span>
                          </div>
                        </div>
                        {expandedWOs.has(wo.wo_number) && wo.parts_lines.length > 0 && (
                          <div className="border-t bg-gray-50 p-3">
                            <p className="text-xs font-semibold text-muted-foreground mb-2">Parts Used ({wo.parts_lines.length} lines)</p>
                            <table className="w-full text-xs">
                              <thead>
                                <tr className="text-muted-foreground">
                                  <th className="text-left pb-1">Part #</th>
                                  <th className="text-left pb-1">Description</th>
                                  <th className="text-right pb-1">Qty</th>
                                  <th className="text-right pb-1">Unit Cost</th>
                                  <th className="text-right pb-1">Unit Sell</th>
                                  <th className="text-right pb-1">Ext. Cost</th>
                                  <th className="text-right pb-1">Ext. Sell</th>
                                </tr>
                              </thead>
                              <tbody>
                                {wo.parts_lines.map((p, i) => (
                                  <tr key={i} className="border-t border-gray-200">
                                    <td className="py-1 font-mono">{p.part_no}</td>
                                    <td className="py-1">{p.description}</td>
                                    <td className="py-1 text-right">{p.qty}</td>
                                    <td className="py-1 text-right">{formatCurrency(p.unit_cost)}</td>
                                    <td className="py-1 text-right">{formatCurrency(p.unit_sell)}</td>
                                    <td className="py-1 text-right font-medium">{formatCurrency(p.extended_cost)}</td>
                                    <td className="py-1 text-right font-medium">{formatCurrency(p.extended_sell)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                        {expandedWOs.has(wo.wo_number) && wo.parts_lines.length === 0 && (
                          <div className="border-t bg-gray-50 p-3 text-xs text-muted-foreground">No parts lines on this WO.</div>
                        )}
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-muted-foreground mt-3">{drillDownData.notes.parts_cost_source}</p>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Notes */}
      <Card>
        <CardHeader>
          <CardTitle>Report Notes</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            {/* Standard cost warning — prominent yellow banner */}
            <div className="flex gap-2 rounded-md border border-yellow-300 bg-yellow-50 p-3">
              <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-semibold text-yellow-800">Parts Cost Accuracy Note</p>
                <p className="text-yellow-700 mt-0.5">{data.notes.standard_cost_warning || 'Parts costs use WOParts.Cost (standard cost from Softbase item master). If a customer shows unexpectedly high parts costs vs. their invoices, verify the standard cost rates for those parts in Softbase — stale standard costs are a common source of discrepancy.'}</p>
              </div>
            </div>
            <div className="space-y-2 text-muted-foreground">
              <p><strong>Revenue:</strong> {data.notes.revenue}</p>
              <p><strong>Costs:</strong> {data.notes.costs}</p>
              <p><strong>Healthy:</strong> {data.notes.health_healthy}</p>
              <p><strong>Warning:</strong> {data.notes.health_warning}</p>
              <p><strong>Critical:</strong> {data.notes.health_critical}</p>
              <p><strong>Fire List Criteria:</strong> {data.notes.fire_list_criteria}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CustomerProfitability
