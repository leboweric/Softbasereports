import { useState, useMemo, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Button } from '@/components/ui/button'
import { Calendar, Download, FileText, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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

  const downloadCSV = () => {
    if (!reportData?.invoices) return

    const headers = [
      'Bill To', 'Salesman', 'Invoice No', 'Invoice Date',
      'PO No', 'Parts Taxable', 'Labor Taxable', 'Labor Non Tax',
      'Misc Taxable', 'Freight', 'Total Tax', 'Grand Total', 'Comments'
    ]

    const rows = reportData.invoices.map(inv => [
      inv.BillToName || inv.BillTo || '',
      inv.Salesman || '',
      inv.InvoiceNo || '',
      formatDate(inv.InvoiceDate),
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
      'TOTALS', '', '', '', '',
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

              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>
                        <Button
                          variant="ghost"
                          onClick={() => handleSort('BillTo')}
                          className="h-auto p-0 font-medium hover:bg-transparent"
                        >
                          Bill To
                          {getSortIcon('BillTo')}
                        </Button>
                      </TableHead>
                      <TableHead>
                        <Button
                          variant="ghost"
                          onClick={() => handleSort('Salesman1')}
                          className="h-auto p-0 font-medium hover:bg-transparent"
                        >
                          Salesman
                          {getSortIcon('Salesman1')}
                        </Button>
                      </TableHead>
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
                      <TableHead>PO#</TableHead>
                      <TableHead className="text-right">
                        <Button
                          variant="ghost"
                          onClick={() => handleSort('PartsTaxable')}
                          className="h-auto p-0 font-medium hover:bg-transparent justify-end w-full"
                        >
                          Parts
                          {getSortIcon('PartsTaxable')}
                        </Button>
                      </TableHead>
                      <TableHead className="text-right">
                        <Button
                          variant="ghost"
                          onClick={() => handleSort('LaborTaxable')}
                          className="h-auto p-0 font-medium hover:bg-transparent justify-end w-full"
                        >
                          Labor Tax
                          {getSortIcon('LaborTaxable')}
                        </Button>
                      </TableHead>
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
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sortedInvoices.map((invoice) => (
                      <TableRow key={invoice.InvoiceNo}>
                        <TableCell className="font-medium">
                          {invoice.BillToName || invoice.BillTo}
                        </TableCell>
                        <TableCell>{invoice.Salesman || '-'}</TableCell>
                        <TableCell>{invoice.InvoiceNo}</TableCell>
                        <TableCell>{formatDate(invoice.InvoiceDate)}</TableCell>
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
                      <TableCell colSpan={5} className="text-right">
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

            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default ServiceInvoiceBilling