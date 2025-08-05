import { useState, useMemo, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Button } from '@/components/ui/button'
import { Calendar, Download, FileText, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import * as XLSX from 'xlsx'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
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
  const [selectedCustomer, setSelectedCustomer] = useState('ALL')
  const [customers, setCustomers] = useState([])
  const [customersLoading, setCustomersLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' })

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

  const handleSort = (key) => {
    setSortConfig({
      key,
      direction: sortConfig.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc'
    })
  }

  const sortedInvoices = useMemo(() => {
    if (!reportData?.invoices || !sortConfig.key) return reportData?.invoices || []
    
    return [...reportData.invoices].sort((a, b) => {
      let aValue = a[sortConfig.key]
      let bValue = b[sortConfig.key]
      
      // Handle customer name sorting
      if (sortConfig.key === 'BillTo') {
        aValue = a.BillToName || a.BillTo || ''
        bValue = b.BillToName || b.BillTo || ''
      }
      
      // Handle null/undefined values
      if (aValue == null) aValue = ''
      if (bValue == null) bValue = ''
      
      // Handle numeric values
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue
      }
      
      // Handle dates
      if (sortConfig.key === 'InvoiceDate') {
        const dateA = new Date(aValue)
        const dateB = new Date(bValue)
        return sortConfig.direction === 'asc' ? dateA - dateB : dateB - dateA
      }
      
      // Handle strings
      return sortConfig.direction === 'asc' 
        ? String(aValue).localeCompare(String(bValue))
        : String(bValue).localeCompare(String(aValue))
    })
  }, [reportData?.invoices, sortConfig])

  const getSortIcon = (column) => {
    if (sortConfig.key !== column) {
      return <ArrowUpDown className="h-4 w-4 text-gray-400" />
    }
    return sortConfig.direction === 'asc' 
      ? <ArrowUp className="h-4 w-4" />
      : <ArrowDown className="h-4 w-4" />
  }

  useEffect(() => {
    // Fetch customers when both dates are selected
    if (startDate && endDate) {
      fetchCustomers()
    } else {
      // Clear customers if dates are not selected
      setCustomers([{ value: 'ALL', label: 'All Customers' }])
      setSelectedCustomer('ALL')
    }
  }, [startDate, endDate])

  const fetchCustomers = async () => {
    if (!startDate || !endDate) return
    
    setCustomersLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        apiUrl(`/api/reports/departments/service/customers?start_date=${startDate}&end_date=${endDate}`),
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      )
      
      if (response.ok) {
        const data = await response.json()
        setCustomers(data)
        // Reset to 'ALL' if current selection is not in the new list
        if (!data.find(c => c.value === selectedCustomer)) {
          setSelectedCustomer('ALL')
        }
      } else {
        console.error('Failed to fetch customers')
        setCustomers([{ value: 'ALL', label: 'All Customers' }])
      }
    } catch (error) {
      console.error('Error fetching customers:', error)
      setCustomers([{ value: 'ALL', label: 'All Customers' }])
    } finally {
      setCustomersLoading(false)
    }
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
      let url = apiUrl(`/api/reports/departments/service/invoice-billing?start_date=${startDate}&end_date=${endDate}`)
      
      if (selectedCustomer && selectedCustomer !== 'ALL') {
        url += `&customer_no=${encodeURIComponent(selectedCustomer)}`
      }
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
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

  const downloadExcel = () => {
    if (!sortedInvoices || sortedInvoices.length === 0) return

    // Prepare data for Excel
    const data = sortedInvoices.map(inv => ({
      'Bill To': inv.BillToName || inv.BillTo || '',
      'Salesman': inv.Salesman || '',
      'Invoice No': inv.InvoiceNo || '',
      'Invoice Date': formatDate(inv.InvoiceDate),
      'Unit No': inv.UnitNo || '',
      'Associated WONo': inv.AssociatedWONo || '',
      'Make': inv.Make || '',
      'Model': inv.Model || '',
      'Serial No': inv.SerialNo || '',
      'Hour Meter': inv.HourMeter ? Math.round(Number(inv.HourMeter)) : '',
      'PO No': inv.PONo || '',
      'Parts Taxable': Number(inv.PartsTaxable || 0),
      'Labor Taxable': Number(inv.LaborTaxable || 0),
      'Labor Non Tax': Number(inv.LaborNonTax || 0),
      'Misc Taxable': Number(inv.MiscTaxable || 0),
      'Freight': Number(inv.Freight || 0),
      'Total Tax': Number(inv.TotalTax || 0),
      'Grand Total': Number(inv.GrandTotal || 0),
      'Comments': (inv.Comments || '').replace(/[\n\r]/g, ' ')
    }))

    // Add totals row
    if (reportData?.totals) {
      data.push({
        'Bill To': 'TOTALS',
        'Salesman': '',
        'Invoice No': '',
        'Invoice Date': '',
        'Unit No': '',
        'Associated WONo': '',
        'Make': '',
        'Model': '',
        'Serial No': '',
        'Hour Meter': '',
        'PO No': '',
        'Parts Taxable': Number(reportData.totals.parts_taxable || 0),
        'Labor Taxable': Number(reportData.totals.labor_taxable || 0),
        'Labor Non Tax': Number(reportData.totals.labor_non_tax || 0),
        'Misc Taxable': Number(reportData.totals.misc_taxable || 0),
        'Freight': Number(reportData.totals.freight || 0),
        'Total Tax': Number(reportData.totals.total_tax || 0),
        'Grand Total': Number(reportData.totals.grand_total || 0),
        'Comments': ''
      })
    }

    // Create worksheet from data
    const ws = XLSX.utils.json_to_sheet(data)
    const wb = XLSX.utils.book_new()
    
    // Get the range before modifications
    const range = XLSX.utils.decode_range(ws['!ref'])
    
    // Add title rows at the top (this will shift everything down)
    const title = `Invoice Billing Report - ${formatDate(startDate)} to ${formatDate(endDate)}`
    const customerName = customers.find(c => c.value === selectedCustomer)?.label || 'All Customers'
    XLSX.utils.sheet_add_aoa(ws, [
      [title],
      [`Customer: ${customerName}`],
      [] // Empty row for spacing
    ], { origin: 'A1' })
    
    // Bold the header row (now at row 4, index 3)
    for (let C = 0; C <= range.e.c; C++) {
      const header_address = XLSX.utils.encode_cell({ r: 3, c: C })
      if (ws[header_address]) {
        if (!ws[header_address].s) ws[header_address].s = {}
        ws[header_address].s.font = { bold: true }
      }
    }
    
    // Bold the totals row (last row)
    const totalsRow = range.e.r + 3 // Adjusted for the 3 title rows
    for (let C = 0; C <= range.e.c; C++) {
      const totals_address = XLSX.utils.encode_cell({ r: totalsRow, c: C })
      if (ws[totals_address]) {
        if (!ws[totals_address].s) ws[totals_address].s = {}
        ws[totals_address].s.font = { bold: true }
      }
    }
    
    // Format currency columns (columns L through S - indices 11-18)
    const currencyColumns = [11, 12, 13, 14, 15, 16, 17] // Parts through Grand Total
    for (let col of currencyColumns) {
      for (let row = 4; row <= totalsRow; row++) { // Start from row 4 (after headers) to totals row
        const cell_address = XLSX.utils.encode_cell({ r: row, c: col })
        if (ws[cell_address] && typeof ws[cell_address].v === 'number') {
          ws[cell_address].z = '$#,##0.00'
        }
      }
    }
    
    // Set column widths
    const colWidths = [
      { wch: 30 }, // Bill To
      { wch: 15 }, // Salesman
      { wch: 12 }, // Invoice No
      { wch: 12 }, // Invoice Date
      { wch: 10 }, // Unit No
      { wch: 12 }, // Associated WONo
      { wch: 15 }, // Make
      { wch: 15 }, // Model
      { wch: 15 }, // Serial No
      { wch: 10 }, // Hour Meter
      { wch: 15 }, // PO No
      { wch: 12 }, // Parts Taxable
      { wch: 12 }, // Labor Taxable
      { wch: 12 }, // Labor Non Tax
      { wch: 12 }, // Misc Taxable
      { wch: 10 }, // Freight
      { wch: 10 }, // Total Tax
      { wch: 12 }, // Grand Total
      { wch: 40 }  // Comments
    ]
    ws['!cols'] = colWidths
    
    // Add worksheet to workbook
    XLSX.utils.book_append_sheet(wb, ws, 'Invoice Billing')
    
    // Write file
    XLSX.writeFile(wb, `invoice_billing_${startDate}_${endDate}.xlsx`)
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
              <Button onClick={downloadExcel} size="sm" variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Export Excel
              </Button>
            )}
          </div>
          <CardDescription>
            View all service invoices for a selected date range with complete details
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className={`grid ${startDate && endDate ? 'grid-cols-4' : 'grid-cols-3'} gap-4 items-end`}>
            <div>
              <Label htmlFor="start-date">Start Date</Label>
              <Input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="end-date">End Date</Label>
              <Input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="mt-1"
              />
            </div>
            {startDate && endDate && (
              <div>
                <Label htmlFor="customer">Bill To</Label>
                <Select
                  value={selectedCustomer}
                  onValueChange={setSelectedCustomer}
                  disabled={customersLoading}
                >
                  <SelectTrigger id="customer" className="mt-1">
                    <SelectValue placeholder={customersLoading ? "Loading customers..." : "All Customers"} />
                  </SelectTrigger>
                  <SelectContent>
                    {customers.map((customer) => (
                      <SelectItem key={customer.value} value={customer.value}>
                        {customer.label}
                        {customer.value !== 'ALL' && (
                          <span className="text-xs text-gray-500 ml-2">
                            ({customer.invoiceCount} invoices)
                          </span>
                        )}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            <Button onClick={fetchReport} disabled={loading || !startDate || !endDate}>
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
                    <span className="text-gray-600">Customer:</span>
                    <span className="ml-2 font-medium">
                      {customers.find(c => c.value === selectedCustomer)?.label || 'All Customers'}
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

              <div className="overflow-x-auto max-w-full">
                <Table className="min-w-[1800px]">
                  <TableHeader>
                    <TableRow>
                      <TableHead className="sticky left-0 bg-white z-10">
                        <Button
                          variant="ghost"
                          onClick={() => handleSort('BillTo')}
                          className="h-auto p-0 font-medium hover:bg-transparent"
                        >
                          Bill To
                          {getSortIcon('BillTo')}
                        </Button>
                      </TableHead>
                      <TableHead>Salesman</TableHead>
                      <TableHead>
                        <Button
                          variant="ghost"
                          onClick={() => handleSort('InvoiceNo')}
                          className="h-auto p-0 font-medium hover:bg-transparent"
                        >
                          Invoice No
                          {getSortIcon('InvoiceNo')}
                        </Button>
                      </TableHead>
                      <TableHead>
                        <Button
                          variant="ghost"
                          onClick={() => handleSort('InvoiceDate')}
                          className="h-auto p-0 font-medium hover:bg-transparent"
                        >
                          Date
                          {getSortIcon('InvoiceDate')}
                        </Button>
                      </TableHead>
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
                      <TableHead className="text-right">
                        <Button
                          variant="ghost"
                          onClick={() => handleSort('GrandTotal')}
                          className="h-auto p-0 font-medium hover:bg-transparent justify-end w-full"
                        >
                          Total
                          {getSortIcon('GrandTotal')}
                        </Button>
                      </TableHead>
                      <TableHead>Comments</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sortedInvoices.map((invoice) => (
                      <TableRow key={invoice.InvoiceNo}>
                        <TableCell className="font-medium sticky left-0 bg-white">
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
                        <TableCell>
                          {invoice.HourMeter ? Number(invoice.HourMeter).toLocaleString('en-US', { maximumFractionDigits: 0 }) : '-'}
                        </TableCell>
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
                        <TableCell className="max-w-xs truncate" title={invoice.Comments || ''}>
                          {invoice.Comments || '-'}
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
                      <TableCell></TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>

            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default ServiceInvoiceBilling