import { useState, useEffect, useCallback, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Calendar } from '@/components/ui/calendar'
import { apiUrl } from '@/lib/api'
import { ChevronDown, ChevronRight, Download, Building2, CalendarIcon } from 'lucide-react'
import { MetricTooltip } from '@/components/ui/metric-tooltip'
import { IPS_METRICS } from '@/config/ipsMetricDefinitions'
import { cn } from '@/lib/utils'

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

// Department name mapping
const DEPT_NAMES = {
  '10': 'New Equipment',
  '20': 'Allied Lines',
  '30': 'Used Equipment',
  '40': 'Road Service',
  '45': 'Shop Service',
  '50': 'Parts',
  '60': 'Rental',
  '70': 'Admin',
  '80': 'Other Income',
}

function formatMonthLabel(month, year) {
  return `${MONTHS.find(m => m.value === month)?.label || ''} ${year}`
}

export default function SalesGPReport({ user }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedBranches, setExpandedBranches] = useState(new Set())
  const [expandedDepts, setExpandedDepts] = useState(new Set())
  const [rangePickerOpen, setRangePickerOpen] = useState(false)

  // Default to previous month (single month mode)
  const now = new Date()
  const defaultMonth = now.getMonth() === 0 ? 12 : now.getMonth()
  const defaultYear = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear()
  
  // Date range state
  const [dateRange, setDateRange] = useState({
    from: new Date(defaultYear, defaultMonth - 1, 1),
    to: new Date(defaultYear, defaultMonth - 1, 28)
  })

  // Derive month/year values from the date range
  const startMonth = dateRange?.from ? dateRange.from.getMonth() + 1 : defaultMonth
  const startYear = dateRange?.from ? dateRange.from.getFullYear() : defaultYear
  const endMonth = dateRange?.to ? dateRange.to.getMonth() + 1 : startMonth
  const endYear = dateRange?.to ? dateRange.to.getFullYear() : startYear

  const isRangeMode = startMonth !== endMonth || startYear !== endYear

  const yearOptions = useMemo(() => {
    const currentYear = new Date().getFullYear()
    return [currentYear, currentYear - 1, currentYear - 2]
  }, [])

  const handleRangeSelect = (range) => {
    if (range?.from && !range?.to) {
      // User clicked the first date, keep popover open
      setDateRange({ from: range.from, to: null })
    } else if (range?.from && range?.to) {
      // Both dates selected
      setDateRange(range)
      setRangePickerOpen(false)
    }
  }

  // Quick single-month selection via dropdowns
  const handleQuickMonthChange = (month) => {
    setDateRange({
      from: new Date(endYear, month - 1, 1),
      to: new Date(endYear, month - 1, 28)
    })
  }

  const handleQuickYearChange = (year) => {
    setDateRange({
      from: new Date(year, startMonth - 1, 1),
      to: new Date(year, endMonth - 1, 28)
    })
  }

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      let url
      if (isRangeMode) {
        url = apiUrl(`/api/reports/departments/accounting/sales-gp-report?start_month=${startMonth}&start_year=${startYear}&end_month=${endMonth}&end_year=${endYear}`)
      } else {
        url = apiUrl(`/api/reports/departments/accounting/sales-gp-report?month=${startMonth}&year=${startYear}`)
      }
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const result = await response.json()
      setData(result)
      // Auto-expand all branches
      if (result.branches) {
        setExpandedBranches(new Set(result.branches.map(b => b.branch)))
        // Auto-expand all departments
        const allDeptKeys = new Set()
        result.branches.forEach(b => {
          b.departments.forEach(d => {
            allDeptKeys.add(`${b.branch}-${d.dept}`)
          })
        })
        setExpandedDepts(allDeptKeys)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [startMonth, startYear, endMonth, endYear, isRangeMode])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const toggleBranch = (branchNo) => {
    setExpandedBranches(prev => {
      const next = new Set(prev)
      if (next.has(branchNo)) {
        next.delete(branchNo)
      } else {
        next.add(branchNo)
      }
      return next
    })
  }

  const toggleDept = (key) => {
    setExpandedDepts(prev => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  const expandAll = () => {
    if (data?.branches) {
      setExpandedBranches(new Set(data.branches.map(b => b.branch)))
      const allDeptKeys = new Set()
      data.branches.forEach(b => {
        b.departments.forEach(d => {
          allDeptKeys.add(`${b.branch}-${d.dept}`)
        })
      })
      setExpandedDepts(allDeptKeys)
    }
  }

  const collapseAll = () => {
    setExpandedBranches(new Set())
    setExpandedDepts(new Set())
  }

  // Build the period label
  const periodLabel = isRangeMode
    ? `${formatMonthLabel(startMonth, startYear)} \u2013 ${formatMonthLabel(endMonth, endYear)}`
    : formatMonthLabel(startMonth, startYear)

  const exportCSV = () => {
    if (!data?.branches) return
    const rows = [
      ['Sales GP Report', periodLabel],
      [],
      ['Branch', 'Dept', 'Account', 'GP Account', 'Description', 'Sales', 'COS', 'GP', 'GP%']
    ]

    data.branches.forEach(branch => {
      rows.push([])
      rows.push([`Branch: ${branch.branch} - ${branch.branch_name}`])
      branch.departments.forEach(dept => {
        dept.line_items.forEach(item => {
          const gpPct = item.sales !== 0 && item.gp !== 0 ? ((item.gp / item.sales) * 100).toFixed(2) + '%' : '0.00%'
          rows.push([
            branch.branch,
            dept.dept,
            item.account,
            item.gp_account,
            item.description,
            item.sales.toFixed(2),
            item.cos.toFixed(2),
            item.gp.toFixed(2),
            gpPct
          ])
        })
        rows.push(['', '', '', '', `Dept ${dept.dept} Total`, dept.total_sales.toFixed(2), dept.total_cos.toFixed(2), dept.total_gp.toFixed(2)])
      })
      rows.push(['', '', '', '', `Branch ${branch.branch} Total`, branch.total_sales.toFixed(2), branch.total_cos.toFixed(2), branch.total_gp.toFixed(2)])
    })
    rows.push([])
    rows.push(['', '', '', '', 'Grand Total', data.grand_total.sales.toFixed(2), data.grand_total.cos.toFixed(2), data.grand_total.gp.toFixed(2), data.grand_total.gp_pct.toFixed(2) + '%'])

    const csv = rows.map(r => r.map(c => `"${c}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `Sales_GP_Report_${periodLabel.replace(/\s/g, '_')}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner />
        <span className="ml-2 text-muted-foreground">Loading Sales GP Report...</span>
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <p className="text-destructive">Error loading report: {error}</p>
          <Button variant="outline" className="mt-2" onClick={fetchData}>Retry</Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Sales GP Report</h3>
          <p className="text-sm text-muted-foreground">
            Revenue, Cost of Sales, and Gross Profit by Branch and Department &mdash; {periodLabel}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Date Range Picker */}
          <Popover open={rangePickerOpen} onOpenChange={setRangePickerOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className={cn(
                  "justify-start text-left font-normal",
                  !dateRange?.from && "text-muted-foreground"
                )}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {dateRange?.from ? (
                  dateRange?.to && (startMonth !== endMonth || startYear !== endYear) ? (
                    <span>
                      {formatMonthLabel(startMonth, startYear)} &ndash; {formatMonthLabel(endMonth, endYear)}
                    </span>
                  ) : (
                    <span>{formatMonthLabel(startMonth, startYear)}</span>
                  )
                ) : (
                  <span>Pick a date range</span>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="end">
              <Calendar
                mode="range"
                selected={dateRange}
                onSelect={handleRangeSelect}
                defaultMonth={dateRange?.from}
                numberOfMonths={2}
                disabled={(date) => date > new Date()}
                initialFocus
              />
              <div className="border-t px-3 py-2 text-xs text-muted-foreground text-center">
                Select start and end dates to define the reporting period
              </div>
            </PopoverContent>
          </Popover>

          {/* Quick Month/Year Selectors */}
          <Select value={String(endMonth)} onValueChange={(v) => handleQuickMonthChange(Number(v))}>
            <SelectTrigger className="w-[130px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MONTHS.map(m => (
                <SelectItem key={m.value} value={String(m.value)}>{m.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={String(endYear)} onValueChange={(v) => handleQuickYearChange(Number(v))}>
            <SelectTrigger className="w-[90px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {yearOptions.map(y => (
                <SelectItem key={y} value={String(y)}>{y}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={exportCSV}>
            <Download className="h-4 w-4 mr-1" /> Export
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground font-medium">Total Sales</p>
              <MetricTooltip {...IPS_METRICS.eds_total_revenue} />
            </div>
            <p className="text-2xl font-bold text-blue-600">{formatCurrency(data?.grand_total?.sales)}</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-red-500">
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground font-medium">Total Cost of Sales</p>
              <MetricTooltip {...IPS_METRICS.eds_total_cogs} />
            </div>
            <p className="text-2xl font-bold text-red-600">{formatCurrency(data?.grand_total?.cos)}</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground font-medium">Total Gross Profit</p>
              <MetricTooltip {...IPS_METRICS.eds_gross_profit} />
            </div>
            <p className="text-2xl font-bold text-green-600">{formatCurrency(data?.grand_total?.gp)}</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="pt-4 pb-3">
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground font-medium">GP Margin</p>
              <MetricTooltip {...IPS_METRICS.eds_gp_pct} />
            </div>
            <p className="text-2xl font-bold text-purple-600">{formatPct(data?.grand_total?.gp_pct)}</p>
            <p className="text-xs text-muted-foreground">{data?.branches?.length || 0} branches</p>
          </CardContent>
        </Card>
      </div>

      {/* Controls */}
      <div className="flex justify-end gap-2">
        <Button variant="ghost" size="sm" onClick={expandAll}>Expand All</Button>
        <Button variant="ghost" size="sm" onClick={collapseAll}>Collapse All</Button>
      </div>

      {/* Report Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead className="w-[60px]">Dept</TableHead>
                <TableHead className="w-[100px]">Account</TableHead>
                <TableHead className="w-[100px]">GP Account</TableHead>
                <TableHead>Description</TableHead>
                <TableHead className="text-right w-[130px]">Sales</TableHead>
                <TableHead className="text-right w-[130px]">COS</TableHead>
                <TableHead className="text-right w-[130px]">GP</TableHead>
                <TableHead className="text-right w-[70px]">GP%</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.branches?.map(branch => (
                <>
                  {/* Branch Header */}
                  <TableRow 
                    key={`branch-${branch.branch}`}
                    className="bg-slate-100 hover:bg-slate-200 cursor-pointer border-t-2 border-slate-300"
                    onClick={() => toggleBranch(branch.branch)}
                  >
                    <TableCell colSpan={8} className="py-2">
                      <div className="flex items-center gap-2 font-bold text-slate-700">
                        {expandedBranches.has(branch.branch) ? 
                          <ChevronDown className="h-4 w-4" /> : 
                          <ChevronRight className="h-4 w-4" />
                        }
                        <Building2 className="h-4 w-4" />
                        <span>Branch {branch.branch}: {branch.branch_name}</span>
                      </div>
                    </TableCell>
                  </TableRow>

                  {expandedBranches.has(branch.branch) && branch.departments.map(dept => {
                    const deptKey = `${branch.branch}-${dept.dept}`
                    const deptName = DEPT_NAMES[dept.dept] || `Dept ${dept.dept}`
                    return (
                      <>
                        {/* Department Header */}
                        <TableRow 
                          key={`dept-${deptKey}`}
                          className="bg-slate-50 hover:bg-slate-100 cursor-pointer"
                          onClick={() => toggleDept(deptKey)}
                        >
                          <TableCell colSpan={4} className="py-1.5 pl-8">
                            <div className="flex items-center gap-2 font-semibold text-sm text-slate-600">
                              {expandedDepts.has(deptKey) ? 
                                <ChevronDown className="h-3.5 w-3.5" /> : 
                                <ChevronRight className="h-3.5 w-3.5" />
                              }
                              <span>{dept.dept} &mdash; {deptName}</span>
                              <span className="text-xs text-muted-foreground font-normal">({dept.line_items.length} accounts)</span>
                            </div>
                          </TableCell>
                          <TableCell className="text-right py-1.5 font-semibold text-sm">{formatCurrency(dept.total_sales)}</TableCell>
                          <TableCell className="text-right py-1.5 font-semibold text-sm">{formatCurrency(dept.total_cos)}</TableCell>
                          <TableCell className="text-right py-1.5 font-semibold text-sm">{formatCurrency(dept.total_gp)}</TableCell>
                          <TableCell className="text-right py-1.5 font-semibold text-sm">
                            {dept.total_sales !== 0 ? formatPct((dept.total_gp / dept.total_sales) * 100) : '0.00%'}
                          </TableCell>
                        </TableRow>

                        {/* Line Items */}
                        {expandedDepts.has(deptKey) && dept.line_items.map((item, idx) => (
                          <TableRow key={`item-${deptKey}-${idx}`} className="hover:bg-blue-50/30">
                            <TableCell className="py-1 pl-14 text-xs text-muted-foreground">{dept.dept}</TableCell>
                            <TableCell className="py-1 text-xs font-mono">{item.account}</TableCell>
                            <TableCell className="py-1 text-xs font-mono text-muted-foreground">{item.gp_account || ''}</TableCell>
                            <TableCell className="py-1 text-sm">{item.description}</TableCell>
                            <TableCell className="py-1 text-right text-sm">{formatCurrency(item.sales)}</TableCell>
                            <TableCell className="py-1 text-right text-sm">{item.cos ? formatCurrency(item.cos) : ''}</TableCell>
                            <TableCell className={`py-1 text-right text-sm ${item.gp < 0 ? 'text-red-600' : item.gp > 0 ? 'text-green-700' : ''}`}>
                              {item.gp ? formatCurrency(item.gp) : ''}
                            </TableCell>
                            <TableCell className="py-1 text-right text-xs text-muted-foreground">
                              {item.gp && item.sales !== 0 ? formatPct((item.gp / item.sales) * 100) : '0.00%'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </>
                    )
                  })}

                  {/* Branch Total */}
                  <TableRow key={`branch-total-${branch.branch}`} className="bg-slate-100 border-b-2 border-slate-300">
                    <TableCell colSpan={4} className="py-2 pl-8 font-bold text-sm text-slate-700 italic">
                      Branch Totals &mdash; {branch.branch_name}
                    </TableCell>
                    <TableCell className="text-right py-2 font-bold text-sm">{formatCurrency(branch.total_sales)}</TableCell>
                    <TableCell className="text-right py-2 font-bold text-sm">{formatCurrency(branch.total_cos)}</TableCell>
                    <TableCell className="text-right py-2 font-bold text-sm">{formatCurrency(branch.total_gp)}</TableCell>
                    <TableCell className="text-right py-2 font-bold text-sm">
                      {branch.total_sales !== 0 ? formatPct((branch.total_gp / branch.total_sales) * 100) : '0.00%'}
                    </TableCell>
                  </TableRow>
                </>
              ))}

              {/* Grand Total */}
              <TableRow className="bg-slate-800 text-white hover:bg-slate-800">
                <TableCell colSpan={4} className="py-3 font-bold text-base">
                  Grand Total
                </TableCell>
                <TableCell className="text-right py-3 font-bold text-base">{formatCurrency(data?.grand_total?.sales)}</TableCell>
                <TableCell className="text-right py-3 font-bold text-base">{formatCurrency(data?.grand_total?.cos)}</TableCell>
                <TableCell className="text-right py-3 font-bold text-base">{formatCurrency(data?.grand_total?.gp)}</TableCell>
                <TableCell className="text-right py-3 font-bold text-base">{formatPct(data?.grand_total?.gp_pct)}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
