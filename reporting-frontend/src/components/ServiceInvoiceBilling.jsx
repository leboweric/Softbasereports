import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Button } from '@/components/ui/button'
import { Calendar, Download, FileText } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { apiUrl } from '@/lib/api'

const ServiceInvoiceBilling = () => {
  const [loading, setLoading] = useState(false)
  const [reportData, setReportData] = useState(null)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [error, setError] = useState(null)

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount || 0)
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      month: '2-digit', 
      day: '2-digit', 
      year: 'numeric' 
    })
  }

  const fetchReport = async () => {
    if (!startDate || !endDate) {
      setError('Please select both start and end dates')
      return
    }

    setLoading(true)
    setError(null)
    
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        apiUrl(`/api/reports/departments/service/invoice-billing?start_date=${startDate}&end_date=${endDate}`),
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      )
      
      if (response.ok) {
        const data = await response.json()
        setReportData(data)
      } else {
        const errorData = await response.json()
        setError(errorData.error || 'Failed to fetch report')
      }
    } catch (error) {
      console.error('Error fetching invoice billing report:', error)
      setError('Error fetching report')
    } finally {
      setLoading(false)
    }
  }

  const downloadCSV = () => {
    if (!reportData?.invoices) return

    const headers = [
      'Bill To', 'Salesman', 'Invoice No', 'Invoice Date', 'Unit No',
      'Associated WONo', 'Make', 'Model', 'Serial No', 'Hour Meter',
      'PO No', 'Parts Taxable', 'Labor Taxable', 'Labor Non Tax',
      'Misc Taxable', 'Freight', 'Total Tax', 'Grand Total', 'Comments'
    ]

    const rows = reportData.invoices.map(inv => [
      inv.BillToName || inv.BillTo || '',
      inv.Salesman || '',
      inv.InvoiceNo || '',
      formatDate(inv.InvoiceDate),
      inv.UnitNo || '',
      inv.AssociatedWONo || '',
      inv.Make || '',
      inv.Model || '',
      inv.SerialNo || '',
      inv.HourMeter || '',
      inv.PONo || '',
      inv.PartsTaxable || 0,
      inv.LaborTaxable || 0,
      inv.LaborNonTax || 0,
      inv.MiscTaxable || 0,
      inv.Freight || 0,
      inv.TotalTax || 0,
      inv.GrandTotal || 0,
      (inv.Comments || '').replace(/[\n\r,]/g, ' ')
    ])

    // Add totals row
    rows.push([
      'TOTALS', '', '', '', '', '', '', '', '', '', '',
      reportData.totals.parts_taxable.toFixed(2),
      reportData.totals.labor_taxable.toFixed(2),
      reportData.totals.labor_non_tax.toFixed(2),
      reportData.totals.misc_taxable.toFixed(2),
      reportData.totals.freight.toFixed(2),
      reportData.totals.total_tax.toFixed(2),
      reportData.totals.grand_total.toFixed(2),
      ''
    ])

    const csvContent = [
      `Invoice Billing Report - ${formatDate(startDate)} to ${formatDate(endDate)}`,
      '',
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `invoice_billing_${startDate}_${endDate}.csv`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CardTitle>Invoice Billing Report</CardTitle>
              <FileText className="h-5 w-5 text-gray-500" />
            </div>
            {reportData && (
              <Button onClick={downloadCSV} size="sm" variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
            )}
          </div>
          <CardDescription>
            View all service invoices for a selected date range with complete details
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <Label htmlFor="start-date">Start Date</Label>
              <Input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="mt-1"
              />
            </div>
            <div className="flex-1">
              <Label htmlFor="end-date">End Date</Label>
              <Input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="mt-1"
              />
            </div>
            <Button onClick={fetchReport} disabled={loading}>
              <Calendar className="h-4 w-4 mr-2" />
              Generate Report
            </Button>
          </div>

          {error && (
            <div className="text-red-600 text-sm">{error}</div>
          )}

          {loading && (
            <div className="flex justify-center py-8">
              <LoadingSpinner size={32} />
            </div>
          )}

          {reportData && !loading && (
            <>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Date Range:</span>
                    <span className="ml-2 font-medium">
                      {formatDate(reportData.start_date)} - {formatDate(reportData.end_date)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Total Invoices:</span>
                    <span className="ml-2 font-medium">{reportData.totals.invoice_count}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Grand Total:</span>
                    <span className="ml-2 font-medium text-green-600">
                      {formatCurrency(reportData.totals.grand_total)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Bill To</TableHead>
                      <TableHead>Salesman</TableHead>
                      <TableHead>Invoice No</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Unit</TableHead>
                      <TableHead>WO#</TableHead>
                      <TableHead>Make/Model</TableHead>
                      <TableHead>Serial</TableHead>
                      <TableHead>Hours</TableHead>
                      <TableHead>PO#</TableHead>
                      <TableHead className="text-right">Parts</TableHead>
                      <TableHead className="text-right">Labor Tax</TableHead>
                      <TableHead className="text-right">Labor NT</TableHead>
                      <TableHead className="text-right">Misc</TableHead>
                      <TableHead className="text-right">Freight</TableHead>
                      <TableHead className="text-right">Tax</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reportData.invoices.map((invoice) => (
                      <TableRow key={invoice.InvoiceNo}>
                        <TableCell className="font-medium">
                          {invoice.BillToName || invoice.BillTo}
                        </TableCell>
                        <TableCell>{invoice.Salesman || '-'}</TableCell>
                        <TableCell>{invoice.InvoiceNo}</TableCell>
                        <TableCell>{formatDate(invoice.InvoiceDate)}</TableCell>
                        <TableCell>{invoice.UnitNo || '-'}</TableCell>
                        <TableCell>{invoice.AssociatedWONo || '-'}</TableCell>
                        <TableCell>
                          {invoice.Make && invoice.Model 
                            ? `${invoice.Make} ${invoice.Model}` 
                            : '-'}
                        </TableCell>
                        <TableCell>{invoice.SerialNo || '-'}</TableCell>
                        <TableCell>{invoice.HourMeter || '-'}</TableCell>
                        <TableCell>{invoice.PONo || '-'}</TableCell>
                        <TableCell className="text-right">
                          {invoice.PartsTaxable ? formatCurrency(invoice.PartsTaxable) : '-'}
                        </TableCell>
                        <TableCell className="text-right">
                          {invoice.LaborTaxable ? formatCurrency(invoice.LaborTaxable) : '-'}
                        </TableCell>
                        <TableCell className="text-right">
                          {invoice.LaborNonTax ? formatCurrency(invoice.LaborNonTax) : '-'}
                        </TableCell>
                        <TableCell className="text-right">
                          {invoice.MiscTaxable ? formatCurrency(invoice.MiscTaxable) : '-'}
                        </TableCell>
                        <TableCell className="text-right">
                          {invoice.Freight ? formatCurrency(invoice.Freight) : '-'}
                        </TableCell>
                        <TableCell className="text-right">
                          {invoice.TotalTax ? formatCurrency(invoice.TotalTax) : '-'}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(invoice.GrandTotal)}
                        </TableCell>
                      </TableRow>
                    ))}
                    <TableRow className="font-bold bg-gray-50">
                      <TableCell colSpan={10} className="text-right">
                        TOTALS:
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(reportData.totals.parts_taxable)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(reportData.totals.labor_taxable)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(reportData.totals.labor_non_tax)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(reportData.totals.misc_taxable)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(reportData.totals.freight)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(reportData.totals.total_tax)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(reportData.totals.grand_total)}
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>

              {reportData.invoices.length > 0 && reportData.invoices[0].Comments && (
                <div className="mt-6">
                  <h3 className="text-sm font-medium mb-2">Work Performed Details</h3>
                  <div className="space-y-2">
                    {reportData.invoices.map((invoice) => 
                      invoice.Comments && (
                        <div key={invoice.InvoiceNo} className="text-sm bg-gray-50 p-3 rounded">
                          <span className="font-medium">Invoice #{invoice.InvoiceNo}:</span>
                          <p className="mt-1 text-gray-700 whitespace-pre-wrap">{invoice.Comments}</p>
                        </div>
                      )
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default ServiceInvoiceBilling