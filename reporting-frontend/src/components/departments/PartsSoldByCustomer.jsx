import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AlertCircle, Download, Search, ChevronDown, ChevronRight } from 'lucide-react'
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

  const formatPct = (val) => {
    if (val === null || val === undefined || !isFinite(val)) return '—'
    const color = val >= 30 ? 'text-green-600' : val >= 15 ? 'text-yellow-600' : 'text-red-600'
    return <span className={color}>{val.toFixed(1)}%</span>
  }

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
                    {/* Customer summary row */}
                    <TableRow
                      key={`cust-${c.customerNo}`}
                      className="cursor-pointer hover:bg-muted/50 font-medium"
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
                          <TableRow key={`line-${c.customerNo}-${idx}`} className="bg-muted/10 text-sm">
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
