import { useState, useEffect, useMemo, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { apiUrl } from '@/lib/api'
import { ChevronDown, ChevronRight, Download, Search } from 'lucide-react'
import { Input } from '@/components/ui/input'

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

export default function PartsCommissionsReport({ user }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedSalesmen, setExpandedSalesmen] = useState(new Set())
  const [searchTerm, setSearchTerm] = useState('')

  // Default to previous month
  const now = new Date()
  const defaultMonth = now.getMonth() === 0 ? 12 : now.getMonth()
  const defaultYear = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear()
  
  const [selectedMonth, setSelectedMonth] = useState(defaultMonth)
  const [selectedYear, setSelectedYear] = useState(defaultYear)

  // Generate year options (current year and 2 years back)
  const yearOptions = useMemo(() => {
    const currentYear = new Date().getFullYear()
    return [currentYear, currentYear - 1, currentYear - 2]
  }, [])

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        apiUrl(`/api/reports/departments/accounting/parts-commissions?month=${selectedMonth}&year=${selectedYear}`),
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const result = await response.json()
      setData(result)
      // Auto-expand all salesmen on load
      if (result.salesmen) {
        setExpandedSalesmen(new Set(result.salesmen.map(s => s.name)))
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [selectedMonth, selectedYear])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const toggleSalesman = (name) => {
    setExpandedSalesmen(prev => {
      const next = new Set(prev)
      if (next.has(name)) {
        next.delete(name)
      } else {
        next.add(name)
      }
      return next
    })
  }

  const expandAll = () => {
    if (data?.salesmen) {
      setExpandedSalesmen(new Set(data.salesmen.map(s => s.name)))
    }
  }

  const collapseAll = () => {
    setExpandedSalesmen(new Set())
  }

  // Filter salesmen by search term
  const filteredSalesmen = useMemo(() => {
    if (!data?.salesmen) return []
    if (!searchTerm.trim()) return data.salesmen
    const term = searchTerm.toLowerCase()
    return data.salesmen.filter(s => 
      s.name.toLowerCase().includes(term) ||
      s.invoices.some(inv => 
        inv.customer.toLowerCase().includes(term) ||
        String(inv.invoice_no).includes(term)
      )
    )
  }, [data, searchTerm])

  // Calculate filtered grand total
  const filteredGrandTotal = useMemo(() => {
    return filteredSalesmen.reduce((acc, s) => ({
      parts_sale: acc.parts_sale + s.total_sale,
      parts_cost: acc.parts_cost + s.total_cost,
      parts_profit: acc.parts_profit + s.total_profit,
      invoice_count: acc.invoice_count + s.invoice_count,
    }), { parts_sale: 0, parts_cost: 0, parts_profit: 0, invoice_count: 0 })
  }, [filteredSalesmen])

  // Export to CSV
  const exportCSV = () => {
    if (!data?.salesmen) return
    const monthLabel = MONTHS.find(m => m.value === selectedMonth)?.label || ''
    const rows = [
      [`Parts Commissions Report - ${monthLabel} ${selectedYear}`],
      [],
      ['Salesman', 'Invoice Date', 'Invoice No', 'Customer', 'Parts Sale', 'Parts Cost', 'Parts Profit'],
    ]

    data.salesmen.forEach(salesman => {
      salesman.invoices.forEach(inv => {
        rows.push([
          salesman.name,
          inv.invoice_date,
          inv.invoice_no,
          inv.customer,
          inv.parts_sale.toFixed(2),
          inv.parts_cost.toFixed(2),
          inv.parts_profit.toFixed(2),
        ])
      })
      rows.push([
        `${salesman.name} Total`,
        '',
        '',
        '',
        salesman.total_sale.toFixed(2),
        salesman.total_cost.toFixed(2),
        salesman.total_profit.toFixed(2),
      ])
      rows.push([])
    })

    rows.push([
      'Grand Total',
      '',
      '',
      '',
      data.grand_total.parts_sale.toFixed(2),
      data.grand_total.parts_cost.toFixed(2),
      data.grand_total.parts_profit.toFixed(2),
    ])

    const csvContent = rows.map(r => r.map(c => `"${c}"`).join(',')).join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `Parts_Commissions_${monthLabel}_${selectedYear}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const monthLabel = MONTHS.find(m => m.value === selectedMonth)?.label || ''

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Parts Commissions</CardTitle>
            <CardDescription>Invoice detail by salesman (parts) — {monthLabel} {selectedYear}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Select value={String(selectedMonth)} onValueChange={(v) => setSelectedMonth(Number(v))}>
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MONTHS.map(m => (
                  <SelectItem key={m.value} value={String(m.value)}>{m.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={String(selectedYear)} onValueChange={(v) => setSelectedYear(Number(v))}>
              <SelectTrigger className="w-[100px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {yearOptions.map(y => (
                  <SelectItem key={y} value={String(y)}>{y}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={exportCSV} disabled={!data?.salesmen?.length}>
              <Download className="h-4 w-4 mr-1" />
              Export
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="large" />
          </div>
        ) : error ? (
          <div className="text-red-500 py-4">Error loading report: {error}</div>
        ) : !data?.salesmen?.length ? (
          <div className="text-muted-foreground text-center py-12">
            No parts commission data found for {monthLabel} {selectedYear}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Summary cards */}
            <div className="grid gap-4 md:grid-cols-4">
              <div className="bg-blue-50 dark:bg-blue-950 rounded-lg p-4">
                <div className="text-sm text-muted-foreground">Total Parts Sale</div>
                <div className="text-xl font-bold text-blue-700 dark:text-blue-300">
                  {formatCurrency(data.grand_total.parts_sale)}
                </div>
              </div>
              <div className="bg-orange-50 dark:bg-orange-950 rounded-lg p-4">
                <div className="text-sm text-muted-foreground">Total Parts Cost</div>
                <div className="text-xl font-bold text-orange-700 dark:text-orange-300">
                  {formatCurrency(data.grand_total.parts_cost)}
                </div>
              </div>
              <div className="bg-green-50 dark:bg-green-950 rounded-lg p-4">
                <div className="text-sm text-muted-foreground">Total Parts Profit</div>
                <div className="text-xl font-bold text-green-700 dark:text-green-300">
                  {formatCurrency(data.grand_total.parts_profit)}
                </div>
              </div>
              <div className="bg-purple-50 dark:bg-purple-950 rounded-lg p-4">
                <div className="text-sm text-muted-foreground">Total Invoices</div>
                <div className="text-xl font-bold text-purple-700 dark:text-purple-300">
                  {data.grand_total.invoice_count.toLocaleString()}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {data.salesmen.length} salespeople
                </div>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search salesman, customer, or invoice..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-8 w-[300px]"
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={expandAll}>Expand All</Button>
                <Button variant="ghost" size="sm" onClick={collapseAll}>Collapse All</Button>
              </div>
            </div>

            {/* Salesmen accordion table */}
            <div className="border rounded-lg overflow-hidden">
              {/* Header */}
              <div className="grid grid-cols-[2fr_1fr_2fr_1fr_1fr_1fr] gap-2 px-4 py-2 bg-muted text-sm font-medium text-muted-foreground border-b">
                <div>Invoice Date</div>
                <div>Invoice No</div>
                <div>Customer</div>
                <div className="text-right">Parts Sale</div>
                <div className="text-right">Parts Cost</div>
                <div className="text-right">Parts Profit</div>
              </div>

              {filteredSalesmen.map((salesman, idx) => {
                const isExpanded = expandedSalesmen.has(salesman.name)
                const gpPercent = salesman.total_sale > 0 
                  ? ((salesman.total_profit / salesman.total_sale) * 100).toFixed(1)
                  : '0.0'

                return (
                  <div key={salesman.name} className={idx > 0 ? 'border-t' : ''}>
                    {/* Salesman header row */}
                    <div
                      className="grid grid-cols-[2fr_1fr_2fr_1fr_1fr_1fr] gap-2 px-4 py-3 bg-slate-50 dark:bg-slate-900 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors items-center"
                      onClick={() => toggleSalesman(salesman.name)}
                    >
                      <div className="col-span-3 flex items-center gap-2">
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                        )}
                        <span className="font-bold text-sm">{salesman.name}</span>
                        <span className="text-xs text-muted-foreground">
                          ({salesman.invoice_count} invoices, {gpPercent}% GP)
                        </span>
                      </div>
                      <div className="text-right font-bold text-sm">{formatCurrency(salesman.total_sale)}</div>
                      <div className="text-right font-bold text-sm">{formatCurrency(salesman.total_cost)}</div>
                      <div className="text-right font-bold text-sm">{formatCurrency(salesman.total_profit)}</div>
                    </div>

                    {/* Invoice rows */}
                    {isExpanded && salesman.invoices.map((inv, invIdx) => (
                      <div
                        key={`${inv.invoice_no}-${invIdx}`}
                        className="grid grid-cols-[2fr_1fr_2fr_1fr_1fr_1fr] gap-2 px-4 py-1.5 text-sm border-t border-dashed hover:bg-muted/50"
                      >
                        <div className="pl-6 text-muted-foreground">{inv.invoice_date}</div>
                        <div className="text-muted-foreground">{inv.invoice_no}</div>
                        <div className="truncate" title={inv.customer}>{inv.customer}</div>
                        <div className={`text-right ${inv.parts_sale < 0 ? 'text-red-600' : ''}`}>
                          {formatCurrency(inv.parts_sale)}
                        </div>
                        <div className={`text-right ${inv.parts_cost < 0 ? 'text-red-600' : ''}`}>
                          {formatCurrency(inv.parts_cost)}
                        </div>
                        <div className={`text-right ${inv.parts_profit < 0 ? 'text-red-600' : ''}`}>
                          {formatCurrency(inv.parts_profit)}
                        </div>
                      </div>
                    ))}
                  </div>
                )
              })}

              {/* Grand Total */}
              <div className="grid grid-cols-[2fr_1fr_2fr_1fr_1fr_1fr] gap-2 px-4 py-3 bg-slate-100 dark:bg-slate-800 border-t-2 border-slate-300 dark:border-slate-600 font-bold text-sm">
                <div className="col-span-3">
                  Grand Total
                  {searchTerm && <span className="text-xs font-normal text-muted-foreground ml-2">(filtered)</span>}
                </div>
                <div className="text-right">{formatCurrency(filteredGrandTotal.parts_sale)}</div>
                <div className="text-right">{formatCurrency(filteredGrandTotal.parts_cost)}</div>
                <div className="text-right">{formatCurrency(filteredGrandTotal.parts_profit)}</div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
