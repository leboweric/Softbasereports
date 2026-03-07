import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AlertCircle, Download, Search, ChevronDown, ChevronRight, Info } from 'lucide-react'
import { apiUrl } from '@/lib/api'
import * as XLSX from 'xlsx'

const PartsSoldByCustomer = ({ user }) => {
  const today = new Date()
  const firstOfYear = new Date(today.getFullYear(), 0, 1)
  const fmt = (d) => d.toISOString().split('T')[0]

  const [startDate, setStartDate] = useState(fmt(firstOfYear))
  const [endDate, setEndDate] = useState(fmt(today))
  const [searchTerm, setSearchTerm] = useState('')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [expandedCustomers, setExpandedCustomers] = useState({})
  const [showMethodology, setShowMethodology] = useState(false)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ start_date: startDate, end_date: endDate })
      const response = await fetch(
        apiUrl(`/api/reports/departments/parts/sold-by-customer?${params}`),
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      )
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
      const json = await response.json()
      if (json.error) throw new Error(json.error)
      setData(json)
    } catch (err) {
      console.error('Error fetching parts sold by customer:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const toggleCustomer = (customerNo) => {
    setExpandedCustomers(prev => ({ ...prev, [customerNo]: !prev[customerNo] }))
  }

  const formatCurrency = (val) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(val || 0)

  const CURRIE_PARTS_TARGET = 40 // Currie model GP% target for Parts

  const formatPct = (val) => {
    if (val === null || val === undefined || !isFinite(val)) return '—'
    const color = val >= CURRIE_PARTS_TARGET ? 'text-green-600' : val >= 25 ? 'text-yellow-600' : 'text-red-600'
    return <span className={color}>{val.toFixed(1)}%</span>
  }

  const belowTarget = (val) =>
    val !== null && val !== undefined && isFinite(val) && val < CURRIE_PARTS_TARGET

  const filteredCustomers = (data?.customers || []).filter(c =>
    !searchTerm ||
    c.customerName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.customerNo?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleExport = () => {
    if (!data?.customers) return
    const rows = []
    data.customers.forEach(c => {
      c.lines.forEach(line => {
        rows.push({
          'Customer #': c.customerNo,
          'Customer Name': c.customerName,
          'Invoice Date': line.invoiceDate,
          'Invoice #': line.invoiceNo,
          'WO #': line.woNo,
          'Part #': line.partNo,
          'Description': line.description,
          'QTY': line.qty,
          'Cost Ea': line.costEa,
          'Sell Ea': line.sellEa,
          'Cost Total': line.costTotal,
          'Sell Total': line.sellTotal,
          'GP $': line.gp,
          'GP %': line.gpPct !== null ? line.gpPct / 100 : null,
        })
      })
      rows.push({
        'Customer #': '',
        'Customer Name': `TOTAL — ${c.customerName}`,
        'Invoice Date': '',
        'Invoice #': '',
        'WO #': '',
        'Part #': '',
        'Description': '',
        'QTY': '',
        'Cost Ea': '',
        'Sell Ea': '',
        'Cost Total': c.totalCost,
        'Sell Total': c.totalSell,
        'GP $': c.totalGP,
        'GP %': c.totalGPPct !== null ? c.totalGPPct / 100 : null,
      })
    })
    const ws = XLSX.utils.json_to_sheet(rows)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Parts Sold by Customer')
    XLSX.writeFile(wb, `parts-sold-by-customer-${startDate}-to-${endDate}.xlsx`)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle>Parts Sold by Customer</CardTitle>
          <CardDescription>
            Line-item parts sold grouped by customer, with gross profit analysis. Matches the Softbase "Parts Sold by Customer w/ Cost" report.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 items-end">
            <div className="space-y-1">
              <Label htmlFor="sbc-start">Start Date</Label>
              <Input
                id="sbc-start"
                type="date"
                value={startDate}
                onChange={e => setStartDate(e.target.value)}
                className="w-40"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="sbc-end">End Date</Label>
              <Input
                id="sbc-end"
                type="date"
                value={endDate}
                onChange={e => setEndDate(e.target.value)}
                className="w-40"
              />
            </div>
            <Button onClick={fetchData} disabled={loading}>
              {loading ? 'Loading…' : 'Run Report'}
            </Button>
            {data && (
              <Button variant="outline" onClick={handleExport} className="ml-auto">
                <Download className="h-4 w-4 mr-2" />
                Export to Excel
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Error */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Currie Target Progress Bar */}
      {data && (
        <Card className={data.grandTotalGPPct !== null && data.grandTotalGPPct < CURRIE_PARTS_TARGET ? 'border-red-300' : 'border-green-300'}>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Currie Model Target: {CURRIE_PARTS_TARGET}% Parts GP</span>
              <span className={`text-sm font-bold ${data.grandTotalGPPct !== null && data.grandTotalGPPct < CURRIE_PARTS_TARGET ? 'text-red-600' : 'text-green-600'}`}>
                {data.grandTotalGPPct !== null ? `${data.grandTotalGPPct.toFixed(1)}% actual` : '—'}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 relative">
              <div
                className={`h-3 rounded-full transition-all ${data.grandTotalGPPct !== null && data.grandTotalGPPct >= CURRIE_PARTS_TARGET ? 'bg-green-500' : 'bg-red-500'}`}
                style={{ width: `${Math.min(100, Math.max(0, (data.grandTotalGPPct || 0) / CURRIE_PARTS_TARGET * 100))}%` }}
              />
              <div className="absolute top-0 h-3 w-0.5 bg-gray-600" style={{ left: '100%', transform: 'translateX(-1px)' }} />
            </div>
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>0%</span>
              <span className="font-medium">Target: {CURRIE_PARTS_TARGET}%</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* CFO Methodology Panel */}
      {data && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-4">
            <button
              className="flex items-center gap-2 text-sm font-medium text-blue-700 hover:text-blue-900 w-full text-left"
              onClick={() => setShowMethodology(prev => !prev)}
            >
              <Info className="h-4 w-4" />
              How is this calculated? (CFO Validation Guide)
              <ChevronDown className={`h-4 w-4 ml-auto transition-transform ${showMethodology ? 'rotate-180' : ''}`} />
            </button>
            {showMethodology && (
              <div className="mt-3 space-y-3 text-sm text-blue-900">
                <div>
                  <span className="font-semibold">Parts Sell:</span> Sum of <code className="bg-blue-100 px-1 rounded">InvoiceReg.SellPrice × QTY</code> for all part lines on invoices within the date range, filtered to Parts department sale codes (from the Dept table).
                </div>
                <div>
                  <span className="font-semibold">Parts Cost:</span> Sum of <code className="bg-blue-100 px-1 rounded">WOParts.Cost</code> — the standard cost rate set in Softbase's item master at time of posting. Note: if standard costs are stale or incorrectly configured, cost figures may not reflect actual purchase cost.
                </div>
                <div>
                  <span className="font-semibold">Gross Profit %:</span> <code className="bg-blue-100 px-1 rounded">(Sell − Cost) / Sell × 100</code>. Lines with zero sell are excluded from GP% calculation.
                </div>
                <div>
                  <span className="font-semibold">Currie Model Target (40%):</span> The Currie dealership model benchmarks Parts GP at 40% or above. Rows highlighted in red are below this threshold and warrant review.
                </div>
                <div>
                  <span className="font-semibold">Data Source:</span> Softbase <code className="bg-blue-100 px-1 rounded">InvoiceReg</code> joined to <code className="bg-blue-100 px-1 rounded">WOParts</code>. Matches the Softbase "Parts Sold by Customer w/ Cost" report. Deleted invoices (<code className="bg-blue-100 px-1 rounded">DeletionTime IS NOT NULL</code>) are excluded.
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Summary KPIs */}
      {data && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-muted-foreground">Total Sell</div>
              <div className="text-2xl font-bold">{formatCurrency(data.grandTotalSell)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-muted-foreground">Total Cost</div>
              <div className="text-2xl font-bold">{formatCurrency(data.grandTotalCost)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-muted-foreground">Gross Profit $</div>
              <div className="text-2xl font-bold">{formatCurrency(data.grandTotalGP)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-muted-foreground">Overall GP%</div>
              <div className="text-2xl font-bold">{formatPct(data.grandTotalGPPct)}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Search */}
      {data && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by customer name or number…"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>
      )}

      {/* Customer Table */}
      {data && filteredCustomers.length > 0 && (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-8"></TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead className="text-right">Cost</TableHead>
                  <TableHead className="text-right">Sell</TableHead>
                  <TableHead className="text-right">GP $</TableHead>
                  <TableHead className="text-right">GP %</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCustomers.map(c => (
                  <>
                    {/* Customer summary row — red if GP% below 40% Currie target */}
                    <TableRow
                      key={`cust-${c.customerNo}`}
                      className={`cursor-pointer font-medium ${
                        belowTarget(c.totalGPPct)
                          ? 'bg-red-50 hover:bg-red-100 border-l-4 border-l-red-500'
                          : 'hover:bg-muted/50'
                      }`}
                      onClick={() => toggleCustomer(c.customerNo)}
                    >
                      <TableCell>
                        {expandedCustomers[c.customerNo]
                          ? <ChevronDown className="h-4 w-4" />
                          : <ChevronRight className="h-4 w-4" />}
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{c.customerName}</div>
                        <div className="text-xs text-muted-foreground">#{c.customerNo} · {c.lines?.length || 0} lines</div>
                      </TableCell>
                      <TableCell className="text-right">{formatCurrency(c.totalCost)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(c.totalSell)}</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(c.totalGP)}</TableCell>
                      <TableCell className="text-right font-medium">{formatPct(c.totalGPPct)}</TableCell>
                    </TableRow>

                    {/* Line items (expanded) */}
                    {expandedCustomers[c.customerNo] && (
                      <>
                        {/* Sub-header */}
                        <TableRow className="bg-muted/40 text-xs font-semibold">
                          <TableCell></TableCell>
                          <TableCell>Part # / Description</TableCell>
                          <TableCell className="text-right">Invoice / WO / Date</TableCell>
                          <TableCell className="text-right">Cost (Ea / Total)</TableCell>
                          <TableCell className="text-right">Sell (Ea / Total)</TableCell>
                          <TableCell className="text-right">GP $ / GP%</TableCell>
                        </TableRow>
                        {c.lines.map((line, idx) => (
                          // Line detail row — red if GP% below 40% Currie target
                          <TableRow
                            key={`line-${c.customerNo}-${idx}`}
                            className={`text-sm ${
                              belowTarget(line.gpPct)
                                ? 'bg-red-50 border-l-4 border-l-red-400'
                                : 'bg-muted/10'
                            }`}
                          >
                            <TableCell></TableCell>
                            <TableCell>
                              <div className="font-mono text-xs font-medium">{line.partNo}</div>
                              <div className="text-xs text-muted-foreground">{line.description}</div>
                              <div className="text-xs text-muted-foreground">Qty: {line.qty}</div>
                            </TableCell>
                            <TableCell className="text-right text-xs">
                              <div>{line.invoiceNo}</div>
                              <div className="text-muted-foreground">{line.woNo}</div>
                              <div className="text-muted-foreground">{line.invoiceDate}</div>
                            </TableCell>
                            <TableCell className="text-right text-xs">
                              <div>{formatCurrency(line.costEa)} ea</div>
                              <div className="font-medium">{formatCurrency(line.costTotal)}</div>
                            </TableCell>
                            <TableCell className="text-right text-xs">
                              <div>{formatCurrency(line.sellEa)} ea</div>
                              <div className="font-medium">{formatCurrency(line.sellTotal)}</div>
                            </TableCell>
                            <TableCell className="text-right text-xs font-medium">
                              <div>{formatCurrency(line.gp)}</div>
                              <div>{formatPct(line.gpPct)}</div>
                            </TableCell>
                          </TableRow>
                        ))}
                        {/* Customer subtotal row */}
                        <TableRow className="bg-muted/30 font-semibold text-sm border-t-2">
                          <TableCell></TableCell>
                          <TableCell colSpan={2} className="text-right text-xs uppercase tracking-wide text-muted-foreground">
                            Customer Total
                          </TableCell>
                          <TableCell className="text-right">{formatCurrency(c.totalCost)}</TableCell>
                          <TableCell className="text-right">{formatCurrency(c.totalSell)}</TableCell>
                          <TableCell className="text-right">
                            <div>{formatCurrency(c.totalGP)}</div>
                            <div>{formatPct(c.totalGPPct)}</div>
                          </TableCell>
                        </TableRow>
                      </>
                    )}
                  </>
                ))}

                {/* Grand total row */}
                <TableRow className="bg-slate-100 font-bold border-t-4">
                  <TableCell></TableCell>
                  <TableCell className="text-sm uppercase tracking-wide">
                    Grand Total · {data.customerCount} customers
                  </TableCell>
                  <TableCell className="text-right">{formatCurrency(data.grandTotalCost)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(data.grandTotalSell)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(data.grandTotalGP)}</TableCell>
                  <TableCell className="text-right">{formatPct(data.grandTotalGPPct)}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {data && filteredCustomers.length === 0 && !loading && (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            No parts found for the selected date range{searchTerm ? ' and search term' : ''}.
          </CardContent>
        </Card>
      )}

      {loading && (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            Loading parts data…
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default PartsSoldByCustomer
