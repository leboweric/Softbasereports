import React, { useState, useEffect } from 'react'
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
  ComposedChart,
  Legend,
  Area
} from 'recharts'
import {
  TrendingDown,
  Calendar,
  DollarSign,
  Truck,
  Download,
  ChevronDown,
  ChevronUp,
  Info
} from 'lucide-react'
import { apiUrl } from '@/lib/api'

const DepreciationRolloff = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedMonths, setExpandedMonths] = useState({})
  const [sortConfig, setSortConfig] = useState({ key: 'depreciationEndDate', direction: 'asc' })

  useEffect(() => {
    fetchDepreciationData()
  }, [])

  const fetchDepreciationData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/rental/depreciation-rolloff'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const result = await response.json()
        setData(result)
      } else {
        setError('Failed to load depreciation data')
      }
    } catch (err) {
      console.error('Error fetching depreciation data:', err)
      setError('Error loading depreciation data')
    } finally {
      setLoading(false)
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

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
  }

  const toggleMonthExpand = (month) => {
    setExpandedMonths(prev => ({
      ...prev,
      [month]: !prev[month]
    }))
  }

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }))
  }

  const sortedEquipment = React.useMemo(() => {
    if (!data?.equipment) return []
    return [...data.equipment].sort((a, b) => {
      let aVal = a[sortConfig.key]
      let bVal = b[sortConfig.key]

      // Handle null/undefined
      if (aVal == null) return 1
      if (bVal == null) return -1

      // Handle dates
      if (sortConfig.key === 'depreciationEndDate') {
        aVal = new Date(aVal).getTime()
        bVal = new Date(bVal).getTime()
      }

      if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1
      if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1
      return 0
    })
  }, [data?.equipment, sortConfig])

  const handleDownloadCSV = () => {
    if (!data?.equipment) return

    const headers = ['Unit No', 'Serial No', 'Make', 'Model', 'Year', 'Starting Value', 'Net Book Value', 'Monthly Depreciation', 'Remaining Months', 'End Date']
    const rows = data.equipment.map(item => [
      item.unitNo || '',
      item.serialNo || '',
      item.make || '',
      item.model || '',
      item.modelYear || '',
      item.startingValue,
      item.netBookValue,
      item.monthlyDepreciation,
      item.remainingMonths,
      item.depreciationEndDate ? new Date(item.depreciationEndDate).toLocaleDateString() : ''
    ])

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `depreciation_schedule_${new Date().toISOString().split('T')[0]}.csv`
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

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-red-600">
            <p>{error}</p>
            <Button onClick={fetchDepreciationData} className="mt-4">
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!data || data.equipment?.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-gray-500">
            <Truck className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No active depreciation records found</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Prepare chart data - show monthly roll-off with cumulative remaining
  const chartData = data.monthlyRolloff?.map((month, idx) => ({
    ...month,
    remainingMonthly: data.summary.totalMonthlyDepreciation - month.cumulativeRolloff
  })) || []

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Depreciating Units</CardTitle>
            <Truck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.summary.totalActiveItems}</div>
            <p className="text-xs text-muted-foreground">Units with remaining depreciation</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Monthly Depreciation</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(data.summary.totalMonthlyDepreciation)}</div>
            <p className="text-xs text-muted-foreground">Total monthly expense</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Net Book Value</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(data.summary.totalRemainingBookValue)}</div>
            <p className="text-xs text-muted-foreground">Remaining book value</p>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Roll-off Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Monthly Depreciation Roll-off Schedule
          </CardTitle>
          <CardDescription>
            How much depreciation expense ends each month (bars) and cumulative savings (line)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="monthLabel" />
              <YAxis
                yAxisId="left"
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                label={{ value: 'Monthly Roll-off', angle: -90, position: 'insideLeft' }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                label={{ value: 'Cumulative Savings', angle: 90, position: 'insideRight' }}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    const monthData = chartData.find(d => d.monthLabel === label)
                    return (
                      <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                        <p className="font-semibold mb-2">{label}</p>
                        <div className="space-y-1 text-sm">
                          <p className="text-blue-600">
                            Roll-off: {formatCurrency(monthData?.rolloffAmount || 0)}
                          </p>
                          <p className="text-green-600">
                            Cumulative Savings: {formatCurrency(monthData?.cumulativeRolloff || 0)}
                          </p>
                          <p className="text-gray-600">
                            {monthData?.itemCount || 0} unit{monthData?.itemCount !== 1 ? 's' : ''} finishing
                          </p>
                        </div>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Legend />
              <Bar
                yAxisId="left"
                dataKey="rolloffAmount"
                fill="#3b82f6"
                name="Monthly Roll-off"
                radius={[4, 4, 0, 0]}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="cumulativeRolloff"
                stroke="#10b981"
                strokeWidth={3}
                name="Cumulative Savings"
                dot={{ fill: '#10b981', r: 4 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Monthly Roll-off Details */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingDown className="h-5 w-5" />
            Roll-off by Month
          </CardTitle>
          <CardDescription>
            Click a month to see which units finish depreciating
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {data.monthlyRolloff?.map((month) => (
              <div key={month.month} className="border rounded-lg">
                <button
                  onClick={() => toggleMonthExpand(month.month)}
                  className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="text-left">
                      <p className="font-medium">{month.monthLabel}</p>
                      <p className="text-sm text-gray-500">{month.itemCount} unit{month.itemCount !== 1 ? 's' : ''}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-medium text-blue-600">{formatCurrency(month.rolloffAmount)}</p>
                      <p className="text-sm text-green-600">Total: {formatCurrency(month.cumulativeRolloff)}</p>
                    </div>
                    {expandedMonths[month.month] ? (
                      <ChevronUp className="h-5 w-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                </button>
                {expandedMonths[month.month] && (
                  <div className="px-4 pb-4 border-t">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Unit No</TableHead>
                          <TableHead>Serial No</TableHead>
                          <TableHead className="text-right">Monthly Depreciation</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {month.items.map((item, idx) => (
                          <TableRow key={idx}>
                            <TableCell>{item.unitNo || '-'}</TableCell>
                            <TableCell className="font-mono text-sm">{item.serialNo}</TableCell>
                            <TableCell className="text-right">{formatCurrency(item.monthlyDepreciation)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Full Equipment Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Truck className="h-5 w-5" />
                Depreciation Schedule
              </CardTitle>
              <CardDescription>
                All units with active depreciation, sorted by end date
              </CardDescription>
            </div>
            <Button onClick={handleDownloadCSV} variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('unitNo')}
                  >
                    Unit No {sortConfig.key === 'unitNo' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </TableHead>
                  <TableHead>Make/Model</TableHead>
                  <TableHead
                    className="text-right cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('startingValue')}
                  >
                    Starting Value {sortConfig.key === 'startingValue' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </TableHead>
                  <TableHead
                    className="text-right cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('netBookValue')}
                  >
                    Net Book Value {sortConfig.key === 'netBookValue' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </TableHead>
                  <TableHead
                    className="text-right cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('monthlyDepreciation')}
                  >
                    Monthly Dep. {sortConfig.key === 'monthlyDepreciation' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </TableHead>
                  <TableHead
                    className="text-right cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('remainingMonths')}
                  >
                    Remaining {sortConfig.key === 'remainingMonths' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('depreciationEndDate')}
                  >
                    End Date {sortConfig.key === 'depreciationEndDate' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedEquipment.map((item, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="font-medium">{item.unitNo || '-'}</TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{item.make || '-'}</p>
                        <p className="text-sm text-gray-500">{item.model || '-'} {item.modelYear ? `(${item.modelYear})` : ''}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">{formatCurrency(item.startingValue)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(item.netBookValue)}</TableCell>
                    <TableCell className="text-right font-medium text-blue-600">
                      {formatCurrency(item.monthlyDepreciation)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant={item.remainingMonths <= 6 ? 'destructive' : item.remainingMonths <= 12 ? 'warning' : 'secondary'}>
                        {item.remainingMonths} mo
                      </Badge>
                    </TableCell>
                    <TableCell>{formatDate(item.depreciationEndDate)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default DepreciationRolloff
