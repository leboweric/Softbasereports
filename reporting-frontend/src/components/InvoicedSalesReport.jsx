import { useState, useEffect, useCallback, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow, TableFooter } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Calendar } from '@/components/ui/calendar'
import { apiUrl } from '@/lib/api'
import { ChevronDown, ChevronRight, Download, Building2, DollarSign, Hash, TrendingUp, Package, Calendar as CalendarIcon } from 'lucide-react'
import { format, startOfMonth, endOfMonth, subMonths } from 'date-fns'

const MONTHS = [
  { value: 1, label: 'January' },
  { value: 2, label: 'February' },
  { value: 3, label: 'March' },
  { value: 4, label: 'April' },
  { value: 5, label: 'May' },
  { value: 6, label: 'June' },
  { value: 7, label: 'July' },
  { value: 8, label: 'August' },
  { value: 9, label: 'September' },
  { value: 10, label: 'October' },
  { value: 11, label: 'November' },
  { value: 12, label: 'December' },
]

function formatCurrency(value) {
  if (value == null) return '$0.00'
  const num = Number(value)
  if (num < 0) {
    return `($${Math.abs(num).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })})`
  }
  return `$${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatPct(value) {
  if (value == null || value === 0) return '0.00%'
  return `${Number(value).toFixed(2)}%`
}

const InvoicedSalesReport = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedBranches, setExpandedBranches] = useState(new Set())
  const [branchDetails, setBranchDetails] = useState({})

  // Date range state - default to previous month
  const now = new Date()
  const prevMonth = subMonths(now, 1)
  const [startDate, setStartDate] = useState(startOfMonth(prevMonth))
  const [endDate, setEndDate] = useState(endOfMonth(prevMonth))
  const [startPickerOpen, setStartPickerOpen] = useState(false)
  const [endPickerOpen, setEndPickerOpen] = useState(false)

  // Quick select mode: 'month' or 'custom'
  const [dateMode, setDateMode] = useState('month')
  const [month, setMonth] = useState(prevMonth.getMonth() + 1)
  const [year, setYear] = useState(prevMonth.getFullYear())

  const years = useMemo(() => {
    const y = new Date().getFullYear()
    return [y, y - 1, y - 2]
  }, [])

  // When month/year changes in month mode, update date range
  useEffect(() => {
    if (dateMode === 'month') {
      const d = new Date(year, month - 1, 1)
      setStartDate(startOfMonth(d))
      setEndDate(endOfMonth(d))
    }
  }, [month, year, dateMode])

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const startStr = format(startDate, 'yyyy-MM-dd')
      const endStr = format(endDate, 'yyyy-MM-dd')
      const res = await fetch(
        apiUrl(`/api/reports/departments/sales/invoiced-summary?start_date=${startStr}&end_date=${endStr}`),
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const result = await res.json()
      setData(result)
      setExpandedBranches(new Set())
      setBranchDetails({})
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [startDate, endDate])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const fetchBranchDetails = useCallback(async (branchNo) => {
    setBranchDetails(prev => ({
      ...prev,
      [branchNo]: { invoices: [], loading: true }
    }))
    try {
      const token = localStorage.getItem('token')
      const branchParam = branchNo === 'all' ? '' : `&branch=${branchNo}`
      const startStr = format(startDate, 'yyyy-MM-dd')
      const endStr = format(endDate, 'yyyy-MM-dd')
      const res = await fetch(
        apiUrl(`/api/reports/departments/sales/invoiced-details?start_date=${startStr}&end_date=${endStr}${branchParam}&category=all`),
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const result = await res.json()
      setBranchDetails(prev => ({
        ...prev,
        [branchNo]: { invoices: result.invoices || [], loading: false }
      }))
    } catch (err) {
      setBranchDetails(prev => ({
        ...prev,
        [branchNo]: { invoices: [], loading: false, error: err.message }
      }))
    }
  }, [startDate, endDate])

  const toggleBranch = (branchNo) => {
    setExpandedBranches(prev => {
      const next = new Set(prev)
      if (next.has(branchNo)) {
        next.delete(branchNo)
      } else {
        next.add(branchNo)
        if (!branchDetails[branchNo]) {
          fetchBranchDetails(branchNo)
        }
      }
      return next
    })
  }

  const exportCSV = () => {
    if (!data?.branches) return
    const dateLabel = `${format(startDate, 'MMM d, yyyy')} - ${format(endDate, 'MMM d, yyyy')}`
    const rows = [
      ['Invoiced Sales Summary', dateLabel],
      [],
      ['Branch', 'Branch Name', 'New Sales', 'New GP', 'New #', 'Used Sales', 'Used GP', 'Used #', 'Allied Sales', 'Allied GP', 'Allied #', 'Total Sales', 'Total GP', 'GP%', 'Total #']
    ]

    data.branches.forEach(b => {
      rows.push([
        b.branch,
        b.branch_name,
        b.new_sales.toFixed(2),
        b.new_gp.toFixed(2),
        b.new_count,
        b.used_sales.toFixed(2),
        b.used_gp.toFixed(2),
        b.used_count,
        b.allied_sales.toFixed(2),
        b.allied_gp.toFixed(2),
        b.allied_count,
        b.total_sales.toFixed(2),
        b.total_gp.toFixed(2),
        b.gp_pct.toFixed(2) + '%',
        b.total_count
      ])
    })

    const gt = data.grand_total
    rows.push([])
    rows.push([
      '', 'Grand Total',
      gt.new_sales.toFixed(2), gt.new_gp.toFixed(2), gt.new_count,
      gt.used_sales.toFixed(2), gt.used_gp.toFixed(2), gt.used_count,
      gt.allied_sales.toFixed(2), gt.allied_gp.toFixed(2), gt.allied_count,
      gt.total_sales.toFixed(2), gt.total_gp.toFixed(2), gt.gp_pct.toFixed(2) + '%', gt.total_count
    ])

    Object.entries(branchDetails).forEach(([branchNo, detail]) => {
      if (detail.invoices?.length > 0) {
        const branchName = data.branches.find(b => b.branch === branchNo)?.branch_name || branchNo
        rows.push([])
        rows.push([`Detail: ${branchName}`])
        rows.push(['Invoice #', 'Date', 'Customer', 'Category', 'Salesman', 'Sale Amount', 'Cost', 'GP', 'GP%'])
        detail.invoices.forEach(inv => {
          rows.push([
            inv.invoice_no,
            inv.invoice_date,
            inv.customer,
            inv.category,
            inv.salesman,
            inv.sale_amount.toFixed(2),
            inv.cost.toFixed(2),
            inv.gp.toFixed(2),
            inv.gp_pct.toFixed(2) + '%'
          ])
        })
      }
    })

    const csv = rows.map(r => r.map(c => `"${c}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `invoiced_sales_${format(startDate, 'yyyy-MM-dd')}_to_${format(endDate, 'yyyy-MM-dd')}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
        <span className="ml-3 text-gray-600">Loading invoiced sales data...</span>
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="pt-6">
          <p className="text-red-600">Error loading report: {error}</p>
          <Button variant="outline" onClick={fetchData} className="mt-2">Retry</Button>
        </CardContent>
      </Card>
    )
  }

  if (!data) return null

  const gt = data.grand_total
  const dateLabel = dateMode === 'month'
    ? `${MONTHS.find(m => m.value === month)?.label || month} ${year}`
    : `${format(startDate, 'MMM d, yyyy')} – ${format(endDate, 'MMM d, yyyy')}`

  return (
    <div className="space-y-4">
      {/* Header with controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">Invoiced Sales — New, Used & Allied</h3>
          <p className="text-sm text-muted-foreground">
            Equipment sales invoiced for {dateLabel}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {/* Mode toggle */}
          <div className="flex rounded-md border overflow-hidden">
            <button
              className={`px-3 py-1.5 text-xs font-medium transition-colors ${dateMode === 'month' ? 'bg-primary text-primary-foreground' : 'bg-background hover:bg-muted'}`}
              onClick={() => setDateMode('month')}
            >
              Month
            </button>
            <button
              className={`px-3 py-1.5 text-xs font-medium transition-colors ${dateMode === 'custom' ? 'bg-primary text-primary-foreground' : 'bg-background hover:bg-muted'}`}
              onClick={() => setDateMode('custom')}
            >
              Custom Range
            </button>
          </div>

          {dateMode === 'month' ? (
            <>
              <Select value={String(month)} onValueChange={v => setMonth(Number(v))}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MONTHS.map(m => (
                    <SelectItem key={m.value} value={String(m.value)}>{m.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={String(year)} onValueChange={v => setYear(Number(v))}>
                <SelectTrigger className="w-[100px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {years.map(y => (
                    <SelectItem key={y} value={String(y)}>{y}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </>
          ) : (
            <>
              <Popover open={startPickerOpen} onOpenChange={setStartPickerOpen}>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-[160px] justify-start text-left font-normal">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {format(startDate, 'MMM d, yyyy')}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={startDate}
                    onSelect={(date) => {
                      if (date) {
                        setStartDate(date)
                        if (date > endDate) setEndDate(date)
                        setStartPickerOpen(false)
                      }
                    }}
                    disabled={(date) => date > new Date()}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
              <span className="text-sm text-muted-foreground">to</span>
              <Popover open={endPickerOpen} onOpenChange={setEndPickerOpen}>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-[160px] justify-start text-left font-normal">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {format(endDate, 'MMM d, yyyy')}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={endDate}
                    onSelect={(date) => {
                      if (date) {
                        setEndDate(date)
                        if (date < startDate) setStartDate(date)
                        setEndPickerOpen(false)
                      }
                    }}
                    disabled={(date) => date > new Date()}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </>
          )}

          <Button variant="outline" size="sm" onClick={exportCSV}>
            <Download className="h-4 w-4 mr-1" />
            Export
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Invoiced</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(gt.total_sales)}</div>
            <p className="text-xs text-muted-foreground">
              {gt.total_count} invoices · GP: {formatPct(gt.gp_pct)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">New Equipment</CardTitle>
            <Package className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{formatCurrency(gt.new_sales)}</div>
            <p className="text-xs text-muted-foreground">
              {gt.new_count} invoices · GP: {formatCurrency(gt.new_gp)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Used Equipment</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{formatCurrency(gt.used_sales)}</div>
            <p className="text-xs text-muted-foreground">
              {gt.used_count} invoices · GP: {formatCurrency(gt.used_gp)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Allied Equipment</CardTitle>
            <Building2 className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">{formatCurrency(gt.allied_sales)}</div>
            <p className="text-xs text-muted-foreground">
              {gt.allied_count} invoices · GP: {formatCurrency(gt.allied_gp)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Table - By Location */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Invoiced by Location</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-gray-50">
                  <TableHead className="w-8"></TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead className="text-right text-blue-600">New Sales</TableHead>
                  <TableHead className="text-right text-blue-600">New GP</TableHead>
                  <TableHead className="text-right text-blue-600">#</TableHead>
                  <TableHead className="text-right text-green-600">Used Sales</TableHead>
                  <TableHead className="text-right text-green-600">Used GP</TableHead>
                  <TableHead className="text-right text-green-600">#</TableHead>
                  <TableHead className="text-right text-amber-600">Allied Sales</TableHead>
                  <TableHead className="text-right text-amber-600">Allied GP</TableHead>
                  <TableHead className="text-right text-amber-600">#</TableHead>
                  <TableHead className="text-right font-bold">Total Sales</TableHead>
                  <TableHead className="text-right font-bold">Total GP</TableHead>
                  <TableHead className="text-right font-bold">GP%</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.branches.map(branch => (
                  <>
                    <TableRow
                      key={branch.branch}
                      className="cursor-pointer hover:bg-gray-50 transition-colors"
                      onClick={() => toggleBranch(branch.branch)}
                    >
                      <TableCell className="w-8 px-2">
                        {expandedBranches.has(branch.branch) ? (
                          <ChevronDown className="h-4 w-4 text-gray-500" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-gray-500" />
                        )}
                      </TableCell>
                      <TableCell className="font-medium">
                        {branch.branch_name}
                        <span className="text-xs text-gray-400 ml-1">({branch.branch})</span>
                      </TableCell>
                      <TableCell className="text-right">{formatCurrency(branch.new_sales)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(branch.new_gp)}</TableCell>
                      <TableCell className="text-right text-gray-500">{branch.new_count}</TableCell>
                      <TableCell className="text-right">{formatCurrency(branch.used_sales)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(branch.used_gp)}</TableCell>
                      <TableCell className="text-right text-gray-500">{branch.used_count}</TableCell>
                      <TableCell className="text-right">{formatCurrency(branch.allied_sales)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(branch.allied_gp)}</TableCell>
                      <TableCell className="text-right text-gray-500">{branch.allied_count}</TableCell>
                      <TableCell className="text-right font-semibold">{formatCurrency(branch.total_sales)}</TableCell>
                      <TableCell className="text-right font-semibold">{formatCurrency(branch.total_gp)}</TableCell>
                      <TableCell className="text-right font-semibold">{formatPct(branch.gp_pct)}</TableCell>
                    </TableRow>
                    {/* Expanded detail rows */}
                    {expandedBranches.has(branch.branch) && (
                      <TableRow key={`${branch.branch}-detail`}>
                        <TableCell colSpan={14} className="p-0 bg-gray-50/50">
                          <div className="px-6 py-3">
                            {branchDetails[branch.branch]?.loading ? (
                              <div className="flex items-center gap-2 py-4 text-sm text-gray-500">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600" />
                                Loading invoice details...
                              </div>
                            ) : branchDetails[branch.branch]?.error ? (
                              <p className="text-red-500 text-sm py-2">Error: {branchDetails[branch.branch].error}</p>
                            ) : branchDetails[branch.branch]?.invoices?.length === 0 ? (
                              <p className="text-gray-500 text-sm py-2">No invoices found</p>
                            ) : (
                              <Table>
                                <TableHeader>
                                  <TableRow className="text-xs">
                                    <TableHead>Invoice #</TableHead>
                                    <TableHead>Date</TableHead>
                                    <TableHead>Customer</TableHead>
                                    <TableHead>Category</TableHead>
                                    <TableHead>Salesman</TableHead>
                                    <TableHead className="text-right">Sale Amount</TableHead>
                                    <TableHead className="text-right">Cost</TableHead>
                                    <TableHead className="text-right">GP</TableHead>
                                    <TableHead className="text-right">GP%</TableHead>
                                  </TableRow>
                                </TableHeader>
                                <TableBody>
                                  {branchDetails[branch.branch].invoices.map(inv => (
                                    <TableRow key={inv.invoice_no} className="text-sm">
                                      <TableCell className="font-mono text-xs">{inv.invoice_no}</TableCell>
                                      <TableCell>{inv.invoice_date}</TableCell>
                                      <TableCell className="max-w-[200px] truncate">{inv.customer}</TableCell>
                                      <TableCell>
                                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                                          inv.category === 'New' ? 'bg-blue-100 text-blue-700' :
                                          inv.category === 'Used' ? 'bg-green-100 text-green-700' :
                                          'bg-amber-100 text-amber-700'
                                        }`}>
                                          {inv.category}
                                        </span>
                                      </TableCell>
                                      <TableCell>{inv.salesman}</TableCell>
                                      <TableCell className="text-right">{formatCurrency(inv.sale_amount)}</TableCell>
                                      <TableCell className="text-right">{formatCurrency(inv.cost)}</TableCell>
                                      <TableCell className={`text-right ${inv.gp < 0 ? 'text-red-600' : ''}`}>
                                        {formatCurrency(inv.gp)}
                                      </TableCell>
                                      <TableCell className={`text-right ${inv.gp_pct < 0 ? 'text-red-600' : ''}`}>
                                        {formatPct(inv.gp_pct)}
                                      </TableCell>
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </>
                ))}
              </TableBody>
              <TableFooter>
                <TableRow className="bg-gray-100 font-bold">
                  <TableCell></TableCell>
                  <TableCell>Grand Total</TableCell>
                  <TableCell className="text-right">{formatCurrency(gt.new_sales)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(gt.new_gp)}</TableCell>
                  <TableCell className="text-right text-gray-500">{gt.new_count}</TableCell>
                  <TableCell className="text-right">{formatCurrency(gt.used_sales)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(gt.used_gp)}</TableCell>
                  <TableCell className="text-right text-gray-500">{gt.used_count}</TableCell>
                  <TableCell className="text-right">{formatCurrency(gt.allied_sales)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(gt.allied_gp)}</TableCell>
                  <TableCell className="text-right text-gray-500">{gt.allied_count}</TableCell>
                  <TableCell className="text-right">{formatCurrency(gt.total_sales)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(gt.total_gp)}</TableCell>
                  <TableCell className="text-right">{formatPct(gt.gp_pct)}</TableCell>
                </TableRow>
              </TableFooter>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default InvoicedSalesReport
