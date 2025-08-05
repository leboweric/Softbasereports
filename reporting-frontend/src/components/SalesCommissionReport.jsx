import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Download, DollarSign, TrendingUp, Package, Truck, ChevronDown, ChevronUp, AlertCircle, Bug, UserX } from 'lucide-react'
import { apiUrl } from '@/lib/api'
import * as XLSX from 'xlsx'
import SalesCommissionInvoiceDebug from './SalesCommissionInvoiceDebug'
import CustomerSalesmanCleanupReport from './CustomerSalesmanCleanupReport'

const SalesCommissionReport = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [commissionData, setCommissionData] = useState(null)
  const [bucketData, setBucketData] = useState(null)
  const [showDiagnostics, setShowDiagnostics] = useState(false)
  const [loadingBuckets, setLoadingBuckets] = useState(false)
  const [detailsData, setDetailsData] = useState(null)
  const [showDetails, setShowDetails] = useState(false)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [showInvoiceDebug, setShowInvoiceDebug] = useState(false)
  const [showCleanupReport, setShowCleanupReport] = useState(false)
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date()
    // Default to previous month since commissions are usually calculated for completed months
    const prevMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    return `${prevMonth.getFullYear()}-${String(prevMonth.getMonth() + 1).padStart(2, '0')}`
  })

  useEffect(() => {
    fetchCommissionData()
    if (showDiagnostics) {
      fetchBucketData()
    }
    if (showDetails) {
      fetchDetailsData()
    }
  }, [selectedMonth])

  const fetchCommissionData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/reports/departments/accounting/sales-commissions?month=${selectedMonth}`), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setCommissionData(data)
      } else {
        console.error('Failed to fetch commission data')
        setCommissionData(null)
      }
    } catch (error) {
      console.error('Error fetching commission data:', error)
      setCommissionData(null)
    } finally {
      setLoading(false)
    }
  }

  const fetchBucketData = async () => {
    try {
      setLoadingBuckets(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/reports/departments/accounting/sales-commission-buckets?month=${selectedMonth}`), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setBucketData(data)
      } else {
        console.error('Failed to fetch bucket data')
        setBucketData(null)
      }
    } catch (error) {
      console.error('Error fetching bucket data:', error)
      setBucketData(null)
    } finally {
      setLoadingBuckets(false)
    }
  }

  const fetchDetailsData = async () => {
    try {
      setLoadingDetails(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/reports/departments/accounting/sales-commission-details?month=${selectedMonth}`), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setDetailsData(data)
      } else {
        console.error('Failed to fetch details data:', response.status, response.statusText)
        const errorText = await response.text()
        console.error('Error response:', errorText)
        setDetailsData(null)
      }
    } catch (error) {
      console.error('Error fetching details data:', error)
      setDetailsData(null)
    } finally {
      setLoadingDetails(false)
    }
  }

  const downloadExcel = () => {
    if (!commissionData) return

    // Create main commission sheet
    const worksheetData = commissionData.salespeople.map(sp => ({
      'Sales Rep': sp.name,
      'Rental': sp.rental || 0,
      'Used Equipment': sp.used_equipment || 0,
      'Allied Equipment': sp.allied_equipment || 0,
      'New Equipment': sp.new_equipment || 0,
      'Total Sales': sp.total_sales || 0,
      'Commission Rate': `${(sp.commission_rate * 100).toFixed(1)}%`,
      'Commission Due': sp.commission_amount || 0
    }))

    const worksheet = XLSX.utils.json_to_sheet(worksheetData)

    // Apply currency formatting
    const range = XLSX.utils.decode_range(worksheet['!ref'])
    for (let row = 1; row <= range.e.r; row++) {
      // Format currency columns (B through F and H)
      for (const col of [1, 2, 3, 4, 5, 7]) { // 0-indexed columns
        const cellAddress = XLSX.utils.encode_cell({ c: col, r: row })
        if (worksheet[cellAddress]) {
          worksheet[cellAddress].z = '$#,##0.00'
        }
      }
    }

    // Set column widths
    worksheet['!cols'] = [
      { wch: 20 }, // Sales Rep
      { wch: 15 }, // Rental
      { wch: 15 }, // Used Equipment
      { wch: 15 }, // Allied Equipment
      { wch: 15 }, // New Equipment
      { wch: 15 }, // Total Sales
      { wch: 15 }, // Commission Rate
      { wch: 15 }  // Commission Due
    ]

    // Add summary sheet
    const summaryData = [
      { 'Category': 'Rental', 'Total Sales': commissionData.totals.rental || 0 },
      { 'Category': 'Used Equipment', 'Total Sales': commissionData.totals.used_equipment || 0 },
      { 'Category': 'Allied Equipment', 'Total Sales': commissionData.totals.allied_equipment || 0 },
      { 'Category': 'New Equipment', 'Total Sales': commissionData.totals.new_equipment || 0 },
      { 'Category': 'Total', 'Total Sales': commissionData.totals.total_sales || 0 },
      { 'Category': 'Total Commissions', 'Total Sales': commissionData.totals.total_commissions || 0 }
    ]

    const summarySheet = XLSX.utils.json_to_sheet(summaryData)
    
    // Format currency in summary
    const summaryRange = XLSX.utils.decode_range(summarySheet['!ref'])
    for (let row = 1; row <= summaryRange.e.r; row++) {
      const cellAddress = XLSX.utils.encode_cell({ c: 1, r: row })
      if (summarySheet[cellAddress]) {
        summarySheet[cellAddress].z = '$#,##0.00'
      }
    }

    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Commissions')
    XLSX.utils.book_append_sheet(workbook, summarySheet, 'Summary')

    // Download file
    const [year, month] = selectedMonth.split('-')
    const monthName = new Date(year, month - 1).toLocaleString('default', { month: 'long' })
    XLSX.writeFile(workbook, `Sales_Commissions_${monthName}_${year}.xlsx`)
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount || 0)
  }

  // Generate month options for the last 12 months
  const generateMonthOptions = () => {
    const options = []
    const now = new Date()
    for (let i = 0; i < 12; i++) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1)
      const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      const label = date.toLocaleString('default', { month: 'long', year: 'numeric' })
      options.push({ value, label })
    }
    return options
  }

  if (loading) {
    return (
      <LoadingSpinner 
        title="Loading Commission Data" 
        description="Calculating sales commissions..."
        size="large"
      />
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Sales Commission Report</h2>
          <p className="text-muted-foreground">Calculate and review monthly sales commissions</p>
        </div>
        <div className="flex items-center gap-4">
          <Select value={selectedMonth} onValueChange={setSelectedMonth}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {generateMonthOptions().map(option => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={downloadExcel} disabled={!commissionData}>
            <Download className="h-4 w-4 mr-2" />
            Export Excel
          </Button>
        </div>
      </div>

      {commissionData ? (
        <>
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-5">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Rental</CardTitle>
                <Truck className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(commissionData.totals.rental)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Used Equipment</CardTitle>
                <Package className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(commissionData.totals.used_equipment)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Allied Equipment</CardTitle>
                <Package className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(commissionData.totals.allied_equipment)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">New Equipment</CardTitle>
                <Package className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(commissionData.totals.new_equipment)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Total Commissions</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {formatCurrency(commissionData.totals.total_commissions)}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {commissionData.salespeople.length} sales reps
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Commission Details Table */}
          <Card>
            <CardHeader>
              <CardTitle>Commission Details by Sales Rep</CardTitle>
              <CardDescription>
                Breakdown of sales and commissions for {new Date(selectedMonth).toLocaleString('default', { month: 'long', year: 'numeric' })}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Sales Rep</TableHead>
                    <TableHead className="text-right">Rental</TableHead>
                    <TableHead className="text-right">Used Equip</TableHead>
                    <TableHead className="text-right">Allied Equip</TableHead>
                    <TableHead className="text-right">New Equip</TableHead>
                    <TableHead className="text-right">Total Sales</TableHead>
                    <TableHead className="text-center">Rate</TableHead>
                    <TableHead className="text-right">Commission</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {commissionData.salespeople.map((rep, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{rep.name}</TableCell>
                      <TableCell className="text-right">{formatCurrency(rep.rental)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(rep.used_equipment)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(rep.allied_equipment)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(rep.new_equipment)}</TableCell>
                      <TableCell className="text-right font-semibold">
                        {formatCurrency(rep.total_sales)}
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="secondary">
                          {(rep.commission_rate * 100).toFixed(1)}%
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-bold text-green-600">
                        {formatCurrency(rep.commission_amount)}
                      </TableCell>
                    </TableRow>
                  ))}
                  {/* Total Row */}
                  <TableRow className="border-t-2 font-bold">
                    <TableCell>TOTAL</TableCell>
                    <TableCell className="text-right">{formatCurrency(commissionData.totals.rental)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(commissionData.totals.used_equipment)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(commissionData.totals.allied_equipment)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(commissionData.totals.new_equipment)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(commissionData.totals.total_sales)}</TableCell>
                    <TableCell></TableCell>
                    <TableCell className="text-right text-green-600">
                      {formatCurrency(commissionData.totals.total_commissions)}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Detailed Invoice Breakdown */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Detailed Invoice Breakdown</CardTitle>
                  <CardDescription>Individual invoices by sales rep with commission calculations</CardDescription>
                </div>
                <Button
                  onClick={() => {
                    setShowDetails(!showDetails)
                    if (!showDetails && !detailsData) {
                      fetchDetailsData()
                    }
                  }}
                  variant="outline"
                  size="sm"
                >
                  {showDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  {showDetails ? 'Hide' : 'Show'} Details
                </Button>
              </div>
            </CardHeader>
            {showDetails && (
              <CardContent>
                {loadingDetails ? (
                  <div className="py-8 text-center">
                    <LoadingSpinner size="small" />
                    <p className="text-sm text-muted-foreground mt-2">Loading invoice details...</p>
                  </div>
                ) : detailsData && detailsData.salesmen ? (
                  <div className="space-y-6">
                    {detailsData.salesmen.map((salesman, idx) => (
                      <div key={idx} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-semibold">{salesman.name}</h4>
                          <div className="text-sm text-muted-foreground">
                            {salesman.invoices.length} invoices • 
                            Total Sales: {formatCurrency(salesman.total_sales)} • 
                            Commission: <span className="font-semibold text-green-600">{formatCurrency(salesman.total_commission)}</span>
                          </div>
                        </div>
                        {salesman.invoices.length > 0 ? (
                          <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                              <thead>
                                <tr className="border-b">
                                  <th className="text-left p-2">Invoice #</th>
                                  <th className="text-left p-2">Date</th>
                                  <th className="text-left p-2">Customer</th>
                                  <th className="text-left p-2">Sale Code</th>
                                  <th className="text-left p-2">Category</th>
                                  <th className="text-right p-2">Amount</th>
                                  <th className="text-right p-2">Commission</th>
                                </tr>
                              </thead>
                              <tbody>
                                {salesman.invoices.map((inv, invIdx) => (
                                  <tr key={invIdx} className="border-b hover:bg-gray-50">
                                    <td className="p-2">{inv.invoice_no}</td>
                                    <td className="p-2">{new Date(inv.invoice_date).toLocaleDateString()}</td>
                                    <td className="p-2">{inv.customer_name}</td>
                                    <td className="p-2">
                                      <Badge variant="outline" className="font-mono text-xs">
                                        {inv.sale_code}
                                      </Badge>
                                    </td>
                                    <td className="p-2">
                                      <Badge variant="secondary" className="text-xs">
                                        {inv.category}
                                      </Badge>
                                    </td>
                                    <td className="text-right p-2">{formatCurrency(inv.category_amount)}</td>
                                    <td className="text-right p-2 font-medium text-green-600">
                                      {formatCurrency(inv.commission)}
                                    </td>
                                  </tr>
                                ))}
                                <tr className="font-semibold bg-gray-50">
                                  <td colSpan="5" className="p-2 text-right">Subtotal:</td>
                                  <td className="text-right p-2">{formatCurrency(salesman.total_sales)}</td>
                                  <td className="text-right p-2 text-green-600">{formatCurrency(salesman.total_commission)}</td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <p className="text-sm text-muted-foreground">No commission-eligible invoices found.</p>
                        )}
                      </div>
                    ))}
                    
                    {/* Grand Total */}
                    {detailsData.salesmen.length > 0 && detailsData.grand_totals && (
                      <div className="border-t-2 pt-4">
                        <div className="flex items-center justify-between font-bold text-lg">
                          <span>Grand Total</span>
                          <div>
                            <span className="mr-8">Sales: {formatCurrency(detailsData.grand_totals.sales || 0)}</span>
                            <span className="text-green-600">Commission: {formatCurrency(detailsData.grand_totals.commission || 0)}</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    Failed to load invoice details
                  </div>
                )}
              </CardContent>
            )}
          </Card>

          {/* Commission Rules */}
          <Card>
            <CardHeader>
              <CardTitle>Commission Structure</CardTitle>
              <CardDescription>Current commission rates and rules</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <p>• <strong>Rental (RENTAL):</strong> 10% of sales revenue</p>
                <p>• <strong>New Equipment (LINDE, LINDEN, NEWEQ, KOM):</strong> 20% of gross profit</p>
                <p>• <strong>Allied Equipment (ALLIED):</strong> 20% of gross profit</p>
                <p>• <strong>Used Equipment (USEDEQ, USED K/L/SL):</strong> 5% of selling price</p>
                <p>• <strong>Rental Sale (RNTSALE):</strong> 5% of gross profit</p>
                <p className="text-muted-foreground mt-4">
                  <strong>Note:</strong> Gross profit calculations use estimated margins until actual cost data is available:
                  New/Allied: 20%, Rental Sale: 25%
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Diagnostic Window */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CardTitle>Commission Bucket Diagnostics</CardTitle>
                  <Badge variant="outline" className="flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    Debug Mode
                  </Badge>
                </div>
                <Button
                  onClick={() => {
                    setShowDiagnostics(!showDiagnostics)
                    if (!showDiagnostics && !bucketData) {
                      fetchBucketData()
                    }
                  }}
                  variant="outline"
                  size="sm"
                >
                  {showDiagnostics ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  {showDiagnostics ? 'Hide' : 'Show'} Diagnostics
                </Button>
              </div>
              <CardDescription>View which Sale Codes map to each commission bucket and sample invoices</CardDescription>
            </CardHeader>
            {showDiagnostics && (
              <CardContent>
                {loadingBuckets ? (
                  <div className="py-8 text-center">
                    <LoadingSpinner size="small" />
                    <p className="text-sm text-muted-foreground mt-2">Loading bucket diagnostics...</p>
                  </div>
                ) : bucketData ? (
                  <div className="space-y-6">
                    {/* Sale Code Mappings */}
                    <div>
                      <h4 className="font-semibold mb-3">Sale Code Mappings</h4>
                      <div className="grid gap-4 md:grid-cols-2">
                        {Object.entries(bucketData.buckets).map(([key, bucket]) => (
                          <div key={key} className="border rounded-lg p-4">
                            <h5 className="font-medium mb-2">{bucket.name}</h5>
                            <div className="space-y-1">
                              <p className="text-sm text-muted-foreground">
                                Sale Codes: <span className="font-mono">
                                  {bucket.sale_codes.length > 0 ? bucket.sale_codes.join(', ') : '(None assigned)'}
                                </span>
                              </p>
                              <p className="text-sm text-muted-foreground">
                                Revenue Field: <span className="font-mono">{bucket.field}Taxable + {bucket.field}NonTax</span>
                              </p>
                              <p className="text-sm">
                                Total: <span className="font-semibold">{formatCurrency(bucketData.summary[key]?.total || 0)}</span>
                                {' '}({bucketData.summary[key]?.count || 0} invoices)
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Commission Category Invoices */}
                    <div>
                      <h4 className="font-semibold mb-3">Commission Category Invoices</h4>
                      <div className="space-y-4">
                        {Object.entries(bucketData.buckets).filter(([key]) => key !== 'all_other').map(([key, bucket]) => (
                          <div key={key} className="border rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <h5 className="font-medium">{bucket.name}</h5>
                              <span className="text-sm text-muted-foreground">
                                {bucket.sample_invoices.length} invoice{bucket.sample_invoices.length !== 1 ? 's' : ''}
                              </span>
                            </div>
                            {bucket.sample_invoices.length > 0 ? (
                              <>
                                <div className="overflow-x-auto">
                                  <table className="w-full text-sm">
                                  <thead>
                                    <tr className="border-b">
                                      <th className="text-left p-2">Invoice #</th>
                                      <th className="text-left p-2">Date</th>
                                      <th className="text-left p-2">Customer</th>
                                      <th className="text-left p-2">Salesman</th>
                                      <th className="text-left p-2">Sale Code</th>
                                      <th className="text-right p-2">Amount</th>
                                      <th className="text-right p-2">Total</th>
                                      <th className="text-center p-2">Commissionable</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {bucket.sample_invoices.map((inv, idx) => (
                                      <tr key={idx} className="border-b">
                                        <td className="p-2">{inv.InvoiceNo}</td>
                                        <td className="p-2">{new Date(inv.InvoiceDate).toLocaleDateString()}</td>
                                        <td className="p-2">{inv.BillToName}</td>
                                        <td className="p-2">
                                          {inv.Salesman1 ? (
                                            inv.Salesman1
                                          ) : (
                                            <span className="text-red-600 font-medium">N/A</span>
                                          )}
                                        </td>
                                        <td className="p-2">
                                          <Badge variant="outline" className="font-mono">
                                            {inv.SaleCode}
                                          </Badge>
                                        </td>
                                        <td className="text-right p-2">{formatCurrency(inv.CategoryAmount)}</td>
                                        <td className="text-right p-2">{formatCurrency(inv.GrandTotal)}</td>
                                        <td className="text-center p-2">
                                          {inv.Salesman1 ? (
                                            <Badge variant="default" className="bg-green-600">Yes</Badge>
                                          ) : (
                                            <Badge variant="destructive">No - Unassigned</Badge>
                                          )}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                              <div className="mt-3 pt-3 border-t">
                                <div className="flex justify-between text-sm">
                                  <span>Commissionable ({bucket.sample_invoices.filter(inv => inv.Salesman1).length} invoices):</span>
                                  <span className="font-semibold text-green-600">
                                    {formatCurrency(bucket.sample_invoices.filter(inv => inv.Salesman1).reduce((sum, inv) => sum + (inv.CategoryAmount || 0), 0))}
                                  </span>
                                </div>
                                <div className="flex justify-between text-sm mt-1">
                                  <span>Non-Commissionable ({bucket.sample_invoices.filter(inv => !inv.Salesman1).length} invoices):</span>
                                  <span className="font-semibold text-red-600">
                                    {formatCurrency(bucket.sample_invoices.filter(inv => !inv.Salesman1).reduce((sum, inv) => sum + (inv.CategoryAmount || 0), 0))}
                                  </span>
                                </div>
                              </div>
                              </>
                            ) : (
                              <p className="text-sm text-muted-foreground">No invoices found for this category in {new Date(selectedMonth).toLocaleString('default', { month: 'long', year: 'numeric' })}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Unmapped Equipment Codes */}
                    {bucketData.unmapped_equipment_codes && bucketData.unmapped_equipment_codes.length > 0 && (
                      <div className="border rounded-lg p-4 bg-yellow-50">
                        <h4 className="font-semibold mb-2 text-yellow-900">Unmapped Equipment Sale Codes</h4>
                        <p className="text-sm text-yellow-800 mb-3">
                          These Sale Codes have equipment revenue but are not currently mapped to any commission bucket:
                        </p>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b">
                                <th className="text-left p-2">Sale Code</th>
                                <th className="text-right p-2">Invoice Count</th>
                                <th className="text-right p-2">Equipment Revenue</th>
                              </tr>
                            </thead>
                            <tbody>
                              {bucketData.unmapped_equipment_codes.map((code, idx) => (
                                <tr key={idx} className="border-b">
                                  <td className="p-2">
                                    <Badge variant="outline" className="font-mono">
                                      {code.SaleCode}
                                    </Badge>
                                  </td>
                                  <td className="text-right p-2">{code.InvoiceCount}</td>
                                  <td className="text-right p-2">{formatCurrency(code.EquipmentRevenue)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    Failed to load diagnostic data
                  </div>
                )}
              </CardContent>
            )}
          </Card>

          {/* Invoice Debug Tool */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CardTitle>Invoice Salesman Debug</CardTitle>
                  <Badge variant="outline" className="flex items-center gap-1">
                    <Bug className="h-3 w-3" />
                    Debug Tool
                  </Badge>
                </div>
                <Button
                  onClick={() => setShowInvoiceDebug(!showInvoiceDebug)}
                  variant="outline"
                  size="sm"
                >
                  {showInvoiceDebug ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  {showInvoiceDebug ? 'Hide' : 'Show'} Debug Tool
                </Button>
              </div>
              <CardDescription>Investigate missing salesman assignments for specific invoices</CardDescription>
            </CardHeader>
            {showInvoiceDebug && (
              <CardContent>
                <SalesCommissionInvoiceDebug user={user} />
              </CardContent>
            )}
          </Card>

          {/* Customer Cleanup Report */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CardTitle>Customer Salesman Cleanup</CardTitle>
                  <Badge variant="outline" className="flex items-center gap-1">
                    <UserX className="h-3 w-3" />
                    Data Quality
                  </Badge>
                </div>
                <Button
                  onClick={() => setShowCleanupReport(!showCleanupReport)}
                  variant="outline"
                  size="sm"
                >
                  {showCleanupReport ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  {showCleanupReport ? 'Hide' : 'Show'} Cleanup Report
                </Button>
              </div>
              <CardDescription>Identify customers with missing salesman assignments and potential duplicates</CardDescription>
            </CardHeader>
            {showCleanupReport && (
              <CardContent>
                <CustomerSalesmanCleanupReport user={user} />
              </CardContent>
            )}
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-muted-foreground">
              No commission data available for the selected month.
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default SalesCommissionReport