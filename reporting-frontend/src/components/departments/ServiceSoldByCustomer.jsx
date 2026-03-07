import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AlertCircle, Download, Search, ChevronDown, ChevronRight, Info } from 'lucide-react'
import { apiUrl } from '@/lib/api'
import * as XLSX from 'xlsx'

// ─── Currie Model Target ───────────────────────────────────────────────────────
// Service GP% target per the Currie model benchmark.
// Rows below this threshold are highlighted red.
const CURRIE_SERVICE_TARGET = 65

const ServiceSoldByCustomer = ({ user }) => {
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
        apiUrl(`/api/reports/departments/service/sold-by-customer?${params}`),
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
      console.error('Error fetching service sold by customer:', err)
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

  const formatPct = (val) => {
    if (val === null || val === undefined || !isFinite(val)) return '—'
    const color = val >= CURRIE_SERVICE_TARGET
      ? 'text-green-600'
      : val >= 50
        ? 'text-yellow-600'
        : 'text-red-600'
    return <span className={color}>{val.toFixed(1)}%</span>
  }

  // Returns true if a GP% value is below the Currie target (triggers red row)
  const belowTarget = (val) =>
    val !== null && val !== undefined && isFinite(val) && val < CURRIE_SERVICE_TARGET

  const filteredCustomers = (data?.customers || []).filter(c =>
    !searchTerm ||
    c.customerName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.customerNo?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleExport = () => {
    if (!data?.customers) return
    const rows = []
    data.customers.forEach(c => {
      c.workOrders.forEach(wo => {
        rows.push({
          'Customer #': c.customerNo,
          'Customer Name': c.customerName,
          'Invoice Date': wo.invoiceDate,
          'Invoice / WO #': wo.invoiceNo,
          'Tech #': wo.techNo,
          'Hours': wo.totalHours,
          'Labor Sell': wo.laborSell,
          'Labor Cost': wo.laborCost,
          'GP $': wo.gp,
          'GP %': wo.gpPct !== null ? wo.gpPct / 100 : null,
          'Currie Target': `${CURRIE_SERVICE_TARGET}%`,
          'At/Above Target': wo.gpPct !== null ? wo.gpPct >= CURRIE_SERVICE_TARGET : null,
        })
      })
      rows.push({
        'Customer #': '',
        'Customer Name': `TOTAL — ${c.customerName}`,
        'Invoice Date': '',
        'Invoice / WO #': `${c.workOrders?.length || 0} WOs`,
        'Tech #': '',
        'Hours': c.totalHours,
        'Labor Sell': c.totalLaborSell,
        'Labor Cost': c.totalLaborCost,
        'GP $': c.totalGP,
        'GP %': c.totalGPPct !== null ? c.totalGPPct / 100 : null,
        'Currie Target': `${CURRIE_SERVICE_TARGET}%`,
        'At/Above Target': c.totalGPPct !== null ? c.totalGPPct >= CURRIE_SERVICE_TARGET : null,
      })
    })
    const ws = XLSX.utils.json_to_sheet(rows)
    // Format GP% columns as percentage
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Service Sold by Customer')
    XLSX.writeFile(wb, `service-sold-by-customer-${startDate}-to-${endDate}.xlsx`)
  }

  return (
    <div className="space-y-6">

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Service Sold by Customer</CardTitle>
            <CardDescription>
              Labor revenue vs. labor cost grouped by customer, with WO-level drill-down and GP analysis.
              Red rows are below the <strong>{CURRIE_SERVICE_TARGET}% Currie model target</strong> for Service.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 items-end">
            <div className="space-y-1">
              <Label htmlFor="svc-start">Start Date</Label>
              <Input
                id="svc-start"
                type="date"
                value={startDate}
                onChange={e => setStartDate(e.target.value)}
                className="w-40"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="svc-end">End Date</Label>
              <Input
                id="svc-end"
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

      {/* ── CFO Methodology Panel ──────────────────────────────────────── */}
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
              <div className="mt-3 text-sm text-blue-900 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="font-semibold border-b border-blue-200 pb-1">Revenue (Labor Sell)</div>
                <p>
                  <code className="bg-blue-100 px-1 rounded text-xs">InvoiceReg.LaborTaxable + InvoiceReg.LaborNonTax</code>
                </p>
                <p className="text-xs text-blue-700">
                  The dollar amount billed to the customer for labor on each invoice — exactly as it
                  appears on the Softbase invoice. Taxable and non-taxable labor are summed together.
                </p>
              </div>
              <div className="space-y-2">
                <div className="font-semibold border-b border-blue-200 pb-1">Cost (Labor Cost)</div>
                <p>
                  <code className="bg-blue-100 px-1 rounded text-xs">SUM(WOLabor.Cost) per WO</code>
                </p>
                <p className="text-xs text-blue-700">
                  Actual technician cost recorded in the WOLabor table at time of posting.
                  This is the same source used by the Cash Burn and Cost per Hour reports.
                  It reflects tech hours × effective labor rate.
                </p>
              </div>
              <div className="space-y-2">
                <div className="font-semibold border-b border-blue-200 pb-1">Gross Profit</div>
                <p>
                  <code className="bg-blue-100 px-1 rounded text-xs">GP $ = Labor Sell − Labor Cost</code>
                </p>
                <p>
                  <code className="bg-blue-100 px-1 rounded text-xs">GP % = GP $ ÷ Labor Sell × 100</code>
                </p>
              </div>
              <div className="space-y-2">
                <div className="font-semibold border-b border-blue-200 pb-1">What's Excluded</div>
                <p className="text-xs text-blue-700">
                  <strong>Parts billed on service WOs are intentionally excluded.</strong> Per the Currie
                  model (BIZ-RULE-002), parts revenue and cost belong to the Parts P&L — not Service.
                  This keeps the Service GP% a pure measure of labor efficiency.
                </p>
              </div>
              <div className="space-y-2">
                <div className="font-semibold border-b border-blue-200 pb-1">Invoice Scope</div>
                <p className="text-xs text-blue-700">
                  Only service invoices are included, identified by matching{' '}
                  <code className="bg-blue-100 px-1 rounded text-xs">InvoiceReg.SaleDept</code> against
                  the tenant's <code className="bg-blue-100 px-1 rounded text-xs">Dept</code> table.
                  This is the same dynamic lookup used by the Customer Billing report — no hardcoded
                  department numbers.
                  {data?.serviceDepts?.length > 0 && (
                    <span className="block mt-1 font-medium">
                      Current service depts for this org: {data.serviceDepts.join(', ')}
                    </span>
                  )}
                </p>
              </div>
              <div className="space-y-2">
                <div className="font-semibold border-b border-blue-200 pb-1">Currie Model Target</div>
                <p className="text-xs text-blue-700">
                  The Currie model benchmark for Service is <strong>{CURRIE_SERVICE_TARGET}% GP</strong>.
                  Rows at or above {CURRIE_SERVICE_TARGET}% are shown in green. Rows below are highlighted
                  red — both at the customer summary level and at the individual WO level.
                </p>
              </div>
              </div>
            </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Error ──────────────────────────────────────────────────────── */}
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

      {/* ── Summary KPIs ───────────────────────────────────────────────── */}
      {data && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-muted-foreground">Labor Sell</div>
              <div className="text-2xl font-bold">{formatCurrency(data.grandTotalLaborSell)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-muted-foreground">Labor Cost</div>
              <div className="text-2xl font-bold">{formatCurrency(data.grandTotalLaborCost)}</div>
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
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-muted-foreground">Total Hours</div>
              <div className="text-2xl font-bold">{(data.grandTotalHours || 0).toFixed(1)}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ── Currie Target Progress Bar ─────────────────────────────────── */}
      {data && (
        <Card className={data.grandTotalGPPct !== null && data.grandTotalGPPct < CURRIE_SERVICE_TARGET ? 'border-red-300' : 'border-green-300'}>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Currie Model Target: {CURRIE_SERVICE_TARGET}% Service GP</span>
              <span className={`text-sm font-bold ${data.grandTotalGPPct !== null && data.grandTotalGPPct < CURRIE_SERVICE_TARGET ? 'text-red-600' : 'text-green-600'}`}>
                {data.grandTotalGPPct !== null ? `${data.grandTotalGPPct.toFixed(1)}% actual` : '—'}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 relative">
              <div
                className={`h-3 rounded-full transition-all ${data.grandTotalGPPct !== null && data.grandTotalGPPct >= CURRIE_SERVICE_TARGET ? 'bg-green-500' : 'bg-red-500'}`}
                style={{ width: `${Math.min(100, Math.max(0, (data.grandTotalGPPct || 0) / CURRIE_SERVICE_TARGET * 100))}%` }}
              />
              <div className="absolute top-0 h-3 w-0.5 bg-gray-600" style={{ left: '100%', transform: 'translateX(-1px)' }} />
            </div>
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>0%</span>
              <span className="font-medium">Target: {CURRIE_SERVICE_TARGET}%</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Search ─────────────────────────────────────────────────────── */}
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

      {/* ── Customer Table ─────────────────────────────────────────────── */}
      {data && filteredCustomers.length > 0 && (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-8"></TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead className="text-right">Hours</TableHead>
                  <TableHead className="text-right">Labor Cost</TableHead>
                  <TableHead className="text-right">Labor Sell</TableHead>
                  <TableHead className="text-right">GP $</TableHead>
                  <TableHead className="text-right">GP %</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCustomers.map(c => (
                  <>
                    {/* ── Customer summary row — red if GP% below Currie target ── */}
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
                        <div className="text-xs text-muted-foreground">
                          #{c.customerNo} · {c.workOrders?.length || 0} WOs
                        </div>
                      </TableCell>
                      <TableCell className="text-right">{(c.totalHours || 0).toFixed(1)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(c.totalLaborCost)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(c.totalLaborSell)}</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(c.totalGP)}</TableCell>
                      <TableCell className="text-right font-medium">{formatPct(c.totalGPPct)}</TableCell>
                    </TableRow>

                    {/* ── WO-level drill-down (expanded) ─────────────────── */}
                    {expandedCustomers[c.customerNo] && (
                      <>
                        {/* Sub-header */}
                        <TableRow className="bg-muted/40 text-xs font-semibold">
                          <TableCell></TableCell>
                          <TableCell>Invoice / WO # · Date</TableCell>
                          <TableCell className="text-right">Tech #</TableCell>
                          <TableCell className="text-right">Hours · Cost</TableCell>
                          <TableCell className="text-right">Labor Sell</TableCell>
                          <TableCell className="text-right">GP $</TableCell>
                          <TableCell className="text-right">GP %</TableCell>
                        </TableRow>

                        {c.workOrders.map((wo, idx) => (
                          // WO detail row — red if GP% below Currie target
                          <TableRow
                            key={`wo-${c.customerNo}-${idx}`}
                            className={`text-sm ${
                              belowTarget(wo.gpPct)
                                ? 'bg-red-50 border-l-4 border-l-red-400'
                                : 'bg-muted/10'
                            }`}
                          >
                            <TableCell></TableCell>
                            <TableCell>
                              <div className="font-mono text-xs font-medium">{wo.invoiceNo}</div>
                              <div className="text-xs text-muted-foreground">{wo.invoiceDate}</div>
                            </TableCell>
                            <TableCell className="text-right text-xs">
                              {wo.techNo || '—'}
                            </TableCell>
                            <TableCell className="text-right text-xs">
                              <div>{(wo.totalHours || 0).toFixed(2)} hrs</div>
                              <div className="text-muted-foreground">{formatCurrency(wo.laborCost)}</div>
                            </TableCell>
                            <TableCell className="text-right text-xs font-medium">
                              {formatCurrency(wo.laborSell)}
                            </TableCell>
                            <TableCell className="text-right text-xs font-medium">
                              {formatCurrency(wo.gp)}
                            </TableCell>
                            <TableCell className="text-right text-xs font-medium">
                              {formatPct(wo.gpPct)}
                            </TableCell>
                          </TableRow>
                        ))}

                        {/* Customer subtotal row */}
                        <TableRow className="bg-muted/30 font-semibold text-sm border-t-2">
                          <TableCell></TableCell>
                          <TableCell colSpan={2} className="text-right text-xs uppercase tracking-wide text-muted-foreground">
                            Customer Total
                          </TableCell>
                          <TableCell className="text-right">{(c.totalHours || 0).toFixed(1)} hrs · {formatCurrency(c.totalLaborCost)}</TableCell>
                          <TableCell className="text-right">{formatCurrency(c.totalLaborSell)}</TableCell>
                          <TableCell className="text-right">{formatCurrency(c.totalGP)}</TableCell>
                          <TableCell className="text-right">
                            {formatPct(c.totalGPPct)}
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
                  <TableCell className="text-right">{(data.grandTotalHours || 0).toFixed(1)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(data.grandTotalLaborCost)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(data.grandTotalLaborSell)}</TableCell>
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
            No service invoices found for the selected date range{searchTerm ? ' and search term' : ''}.
          </CardContent>
        </Card>
      )}

      {loading && (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            Loading service data…
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default ServiceSoldByCustomer
