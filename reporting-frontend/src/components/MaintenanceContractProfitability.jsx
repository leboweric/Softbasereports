import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { CheckCircle, XCircle, TrendingUp, TrendingDown, DollarSign, Wrench, AlertTriangle, ChevronDown, ChevronRight, Truck } from 'lucide-react'
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
  ComposedChart,
  Line,
  Legend,
  Cell
} from 'recharts'
import { apiUrl } from '@/lib/api'

const MaintenanceContractProfitability = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sortField, setSortField] = useState('true_profit')
  const [sortDirection, setSortDirection] = useState('desc')
  const [expandedCustomers, setExpandedCustomers] = useState({})
  const [equipmentSortField, setEquipmentSortField] = useState('total_cost')
  const [equipmentSortDirection, setEquipmentSortDirection] = useState('desc')
  const [selectedCustomerFilter, setSelectedCustomerFilter] = useState('all')

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  useEffect(() => {
    fetchProfitabilityData()
  }, [])

  const fetchProfitabilityData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/guaranteed-maintenance/profitability'), {
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

  const getSortedCustomers = () => {
    if (!data?.by_customer) return []

    return [...data.by_customer].sort((a, b) => {
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

  const toggleCustomerExpanded = (customerNumber) => {
    setExpandedCustomers(prev => ({
      ...prev,
      [customerNumber]: !prev[customerNumber]
    }))
  }

  const handleEquipmentSort = (field) => {
    if (equipmentSortField === field) {
      setEquipmentSortDirection(equipmentSortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setEquipmentSortField(field)
      setEquipmentSortDirection('desc')
    }
  }

  const getEquipmentForCustomer = (customerNumber) => {
    if (!data?.by_equipment) return []
    return data.by_equipment.filter(eq => eq.customer_number === customerNumber)
  }

  const getSortedEquipment = () => {
    if (!data?.by_equipment) return []

    let equipment = [...data.by_equipment]

    // Filter by customer if selected
    if (selectedCustomerFilter !== 'all') {
      equipment = equipment.filter(eq => eq.customer_number === selectedCustomerFilter)
    }

    return equipment.sort((a, b) => {
      let aVal = a[equipmentSortField]
      let bVal = b[equipmentSortField]

      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase()
        bVal = bVal.toLowerCase()
      }

      if (equipmentSortDirection === 'asc') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })
  }

  const EquipmentSortHeader = ({ field, children }) => (
    <TableHead
      className="cursor-pointer hover:bg-gray-100 select-none text-xs"
      onClick={() => handleEquipmentSort(field)}
    >
      <div className="flex items-center gap-1">
        {children}
        {equipmentSortField === field && (
          <span className="text-xs">{equipmentSortDirection === 'asc' ? '↑' : '↓'}</span>
        )}
      </div>
    </TableHead>
  )

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <LoadingSpinner />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="text-center py-8 text-red-600">
          Error: {error}
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="text-center py-8 text-muted-foreground">
          No profitability data available
        </CardContent>
      </Card>
    )
  }

  const { summary, by_customer, by_equipment, monthly } = data

  // Prepare chart data (reverse to show oldest first)
  const chartData = [...monthly].reverse().map(m => ({
    ...m,
    month: m.month_name
  }))

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Contract Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {formatCurrency(summary.total_contract_revenue)}
            </div>
            <p className="text-xs text-muted-foreground">
              {summary.total_invoices} invoices
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Service Costs</CardTitle>
            <Wrench className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatCurrency(summary.total_service_cost)}
            </div>
            <p className="text-xs text-muted-foreground">
              {summary.total_work_orders} work orders
            </p>
          </CardContent>
        </Card>

        <Card className={summary.overall_profitable ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">True Profit</CardTitle>
            {summary.overall_profitable ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${summary.overall_profitable ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(summary.true_profit)}
            </div>
            <p className="text-xs text-muted-foreground">
              Revenue - Service Costs
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Margin</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${summary.margin_percent >= 50 ? 'text-green-600' : summary.margin_percent >= 25 ? 'text-yellow-600' : 'text-red-600'}`}>
              {summary.margin_percent}%
            </div>
            <p className="text-xs text-muted-foreground">
              Gross margin
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Customers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold text-green-600">{summary.profitable_customers}</span>
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span className="text-muted-foreground">/</span>
              <span className="text-xl font-bold text-red-600">{summary.unprofitable_customers}</span>
              <XCircle className="h-4 w-4 text-red-600" />
            </div>
            <p className="text-xs text-muted-foreground">
              Profitable / Unprofitable
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Cost Breakdown Card */}
      <Card>
        <CardHeader>
          <CardTitle>Service Cost Breakdown</CardTitle>
          <CardDescription>What's driving your service costs</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-muted-foreground mb-1">Labor Costs</p>
              <p className="text-2xl font-bold text-blue-600">{formatCurrency(summary.total_labor_cost)}</p>
              <p className="text-xs text-muted-foreground">
                {((summary.total_labor_cost / summary.total_service_cost) * 100).toFixed(1)}% of total
              </p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <p className="text-sm text-muted-foreground mb-1">Parts Costs</p>
              <p className="text-2xl font-bold text-orange-600">{formatCurrency(summary.total_parts_cost)}</p>
              <p className="text-xs text-muted-foreground">
                {((summary.total_parts_cost / summary.total_service_cost) * 100).toFixed(1)}% of total
              </p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-sm text-muted-foreground mb-1">Misc Costs</p>
              <p className="text-2xl font-bold text-purple-600">{formatCurrency(summary.total_misc_cost)}</p>
              <p className="text-xs text-muted-foreground">
                {((summary.total_misc_cost / summary.total_service_cost) * 100).toFixed(1)}% of total
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Customer Profitability Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Customer Profitability
            {summary.unprofitable_customers > 0 && (
              <Badge variant="destructive" className="gap-1">
                <AlertTriangle className="h-3 w-3" />
                {summary.unprofitable_customers} unprofitable
              </Badge>
            )}
          </CardTitle>
          <CardDescription>Click column headers to sort</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <SortHeader field="customer_name">Customer</SortHeader>
                  <SortHeader field="contract_revenue">
                    <span className="text-right w-full">Revenue</span>
                  </SortHeader>
                  <SortHeader field="service_total_cost">
                    <span className="text-right w-full">Service Cost</span>
                  </SortHeader>
                  <SortHeader field="service_wo_count">
                    <span className="text-right w-full">WOs</span>
                  </SortHeader>
                  <SortHeader field="true_profit">
                    <span className="text-right w-full">Profit</span>
                  </SortHeader>
                  <SortHeader field="margin_percent">
                    <span className="text-right w-full">Margin</span>
                  </SortHeader>
                  <TableHead className="text-center">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {getSortedCustomers().map((customer) => (
                  <TableRow
                    key={customer.customer_number}
                    className={!customer.profitable ? 'bg-red-50' : ''}
                  >
                    <TableCell>
                      <div>
                        <p className="font-medium">{customer.customer_name}</p>
                        <p className="text-xs text-muted-foreground">#{customer.customer_number}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatCurrency(customer.contract_revenue)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatCurrency(customer.service_total_cost)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {customer.service_wo_count}
                    </TableCell>
                    <TableCell className={`text-right font-mono font-bold ${customer.profitable ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(customer.true_profit)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge
                        variant={customer.margin_percent >= 50 ? "success" : customer.margin_percent >= 0 ? "warning" : "destructive"}
                      >
                        {customer.margin_percent > 0 ? customer.margin_percent.toFixed(1) : customer.margin_percent.toFixed(0)}%
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      {customer.profitable ? (
                        <CheckCircle className="h-5 w-5 text-green-600 mx-auto" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-600 mx-auto" />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Monthly Trend Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Profitability Trend</CardTitle>
          <CardDescription>Contract revenue vs service costs over time</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
              <RechartsTooltip
                formatter={(value, name) => [formatCurrency(value), name]}
                labelFormatter={(label) => `Month: ${label}`}
              />
              <Legend />
              <Bar dataKey="contract_revenue" name="Contract Revenue" fill="#3b82f6" />
              <Bar dataKey="service_total_cost" name="Service Cost" fill="#ef4444" />
              <Line
                type="monotone"
                dataKey="true_profit"
                name="Profit"
                stroke="#22c55e"
                strokeWidth={3}
                dot={{ fill: '#22c55e', strokeWidth: 2 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Equipment Breakdown Card */}
      {by_equipment && by_equipment.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Truck className="h-5 w-5" />
              Equipment / Serial Number Breakdown
            </CardTitle>
            <CardDescription>
              Service costs by individual equipment unit - click column headers to sort
            </CardDescription>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-sm text-muted-foreground">Filter by customer:</span>
              <select
                value={selectedCustomerFilter}
                onChange={(e) => setSelectedCustomerFilter(e.target.value)}
                className="border rounded px-2 py-1 text-sm"
              >
                <option value="all">All Customers</option>
                {by_customer.map(c => (
                  <option key={c.customer_number} value={c.customer_number}>
                    {c.customer_name}
                  </option>
                ))}
              </select>
              <span className="text-sm text-muted-foreground ml-4">
                Showing {getSortedEquipment().length} units
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-auto max-h-[500px]">
              <Table>
                <TableHeader className="sticky top-0 bg-white">
                  <TableRow>
                    <EquipmentSortHeader field="customer_name">Customer</EquipmentSortHeader>
                    <EquipmentSortHeader field="serial_no">Serial #</EquipmentSortHeader>
                    <EquipmentSortHeader field="unit_no">Unit #</EquipmentSortHeader>
                    <EquipmentSortHeader field="make">Make/Model</EquipmentSortHeader>
                    <EquipmentSortHeader field="wo_count">
                      <span className="text-right w-full">Total WOs</span>
                    </EquipmentSortHeader>
                    <EquipmentSortHeader field="pm_count">
                      <span className="text-right w-full">PMs</span>
                    </EquipmentSortHeader>
                    <EquipmentSortHeader field="service_count">
                      <span className="text-right w-full">Service</span>
                    </EquipmentSortHeader>
                    <EquipmentSortHeader field="labor_cost">
                      <span className="text-right w-full">Labor</span>
                    </EquipmentSortHeader>
                    <EquipmentSortHeader field="parts_cost">
                      <span className="text-right w-full">Parts</span>
                    </EquipmentSortHeader>
                    <EquipmentSortHeader field="total_cost">
                      <span className="text-right w-full">Total Cost</span>
                    </EquipmentSortHeader>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {getSortedEquipment().map((eq, idx) => (
                    <TableRow
                      key={`${eq.customer_number}-${eq.serial_no}-${idx}`}
                      className={eq.total_cost > 5000 ? 'bg-red-50' : eq.total_cost > 2000 ? 'bg-yellow-50' : ''}
                    >
                      <TableCell className="text-xs">
                        <div>
                          <p className="font-medium truncate max-w-[150px]" title={eq.customer_name}>
                            {eq.customer_name}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-xs">{eq.serial_no}</TableCell>
                      <TableCell className="font-mono text-xs">{eq.unit_no || '-'}</TableCell>
                      <TableCell className="text-xs">
                        {eq.make && eq.model ? `${eq.make} ${eq.model}` : eq.make || eq.model || '-'}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs">{eq.wo_count}</TableCell>
                      <TableCell className="text-right font-mono text-xs">{eq.pm_count}</TableCell>
                      <TableCell className="text-right font-mono text-xs">{eq.service_count}</TableCell>
                      <TableCell className="text-right font-mono text-xs">{formatCurrency(eq.labor_cost)}</TableCell>
                      <TableCell className="text-right font-mono text-xs">{formatCurrency(eq.parts_cost)}</TableCell>
                      <TableCell className={`text-right font-mono text-xs font-bold ${eq.total_cost > 5000 ? 'text-red-600' : ''}`}>
                        {formatCurrency(eq.total_cost)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {by_equipment.length > 10 && (
              <p className="text-xs text-muted-foreground mt-2 text-center">
                Showing all {getSortedEquipment().length} equipment records. Scroll to see more.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Notes Card */}
      <Card>
        <CardHeader>
          <CardTitle>About This Report</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p><strong>Contract Revenue:</strong> Monthly billing from FMBILL (Full Maintenance Billing) invoices in the Guaranteed Maintenance department.</p>
          <p><strong>Service Costs:</strong> Actual costs from Work Orders (Labor + Parts + Misc) for customers with maintenance contracts. Includes Service (S), Shop (SH), and PM work order types.</p>
          <p><strong>True Profit:</strong> Contract Revenue minus Actual Service Costs. This shows whether the flat monthly fee covers the actual service delivered.</p>
          <p><strong>Note:</strong> Some customers (like leasing companies) may show 100% margin because work orders are billed to the equipment user, not the leasing company.</p>
        </CardContent>
      </Card>
    </div>
  )
}

export default MaintenanceContractProfitability
