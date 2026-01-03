import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Search, Download, TrendingUp, AlertTriangle, DollarSign, Calendar } from 'lucide-react'
import { apiUrl } from '@/lib/api'
import * as XLSX from 'xlsx'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts'

const APReport = ({ user }) => {
  const [apData, setApData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortField, setSortField] = useState('days_overdue')
  const [sortDirection, setSortDirection] = useState('desc')

  useEffect(() => {
    fetchAPData()
  }, [])

  const fetchAPData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/accounting/ap-report'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setApData(data)
      } else {
        console.error('Failed to fetch AP data')
      }
    } catch (error) {
      console.error('Error fetching AP data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSort = (field) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const filteredAndSortedInvoices = apData?.invoices
    ?.filter(invoice => {
      const search = searchTerm.toLowerCase()
      return (
        invoice.vendor_name.toLowerCase().includes(search) ||
        invoice.invoice_no.toLowerCase().includes(search) ||
        invoice.vendor_no.toLowerCase().includes(search)
      )
    })
    ?.sort((a, b) => {
      let aVal = a[sortField]
      let bVal = b[sortField]
      
      if (sortField === 'vendor_name' || sortField === 'invoice_no') {
        aVal = aVal?.toLowerCase() || ''
        bVal = bVal?.toLowerCase() || ''
      }
      
      if (sortDirection === 'asc') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    }) || []

  const downloadExcel = () => {
    if (!apData?.invoices) return

    // Create worksheet data with proper formatting
    const worksheetData = filteredAndSortedInvoices.map(inv => ({
      'Invoice #': inv.invoice_no,
      'Vendor': inv.vendor_name,
      'Invoice Date': inv.invoice_date,
      'Due Date': inv.due_date,
      'Days Overdue': inv.days_overdue > 0 ? inv.days_overdue : 'Not Due',
      'Amount': parseFloat(inv.amount || 0), // Ensure it's a number for Excel formatting
      'Aging Bucket': inv.aging_bucket
    }))

    const worksheet = XLSX.utils.json_to_sheet(worksheetData)

    // Apply currency formatting to the Amount column (column F, 0-indexed = 5)
    const range = XLSX.utils.decode_range(worksheet['!ref'])
    for (let row = 1; row <= range.e.r; row++) { // Start from row 1 (skip header)
      const cellAddress = XLSX.utils.encode_cell({ c: 5, r: row }) // Column F (Amount)
      if (worksheet[cellAddress]) {
        worksheet[cellAddress].z = '$#,##0.00' // Excel currency format
      }
    }

    // Set column widths for better readability
    worksheet['!cols'] = [
      { wch: 15 }, // Invoice #
      { wch: 25 }, // Vendor
      { wch: 12 }, // Invoice Date
      { wch: 12 }, // Due Date
      { wch: 12 }, // Days Overdue
      { wch: 15 }, // Amount
      { wch: 15 }  // Aging Bucket
    ]

    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, 'AP Report')
    XLSX.writeFile(workbook, `AP_Report_${new Date().toISOString().split('T')[0]}.xlsx`)
  }

  const downloadOver90Excel = () => {
    if (!apData?.invoices) return

    // Filter for invoices over 90 days overdue
    const over90Invoices = apData.invoices.filter(inv => inv.days_overdue > 90)

    if (over90Invoices.length === 0) {
      console.log('No invoices over 90 days found')
      return
    }

    // Create worksheet data with proper formatting
    const worksheetData = over90Invoices.map(inv => ({
      'Invoice #': inv.invoice_no,
      'Vendor': inv.vendor_name,
      'Invoice Date': inv.invoice_date,
      'Due Date': inv.due_date,
      'Days Overdue': inv.days_overdue,
      'Amount': parseFloat(inv.amount || 0), // Ensure it's a number for Excel formatting
      'Aging Bucket': inv.aging_bucket
    }))

    const worksheet = XLSX.utils.json_to_sheet(worksheetData)

    // Apply currency formatting to the Amount column (column F, 0-indexed = 5)
    const range = XLSX.utils.decode_range(worksheet['!ref'])
    for (let row = 1; row <= range.e.r; row++) { // Start from row 1 (skip header)
      const cellAddress = XLSX.utils.encode_cell({ c: 5, r: row }) // Column F (Amount)
      if (worksheet[cellAddress]) {
        worksheet[cellAddress].z = '$#,##0.00' // Excel currency format
      }
    }

    // Set column widths for better readability
    worksheet['!cols'] = [
      { wch: 15 }, // Invoice #
      { wch: 25 }, // Vendor
      { wch: 12 }, // Invoice Date
      { wch: 12 }, // Due Date
      { wch: 12 }, // Days Overdue
      { wch: 15 }, // Amount
      { wch: 15 }  // Aging Bucket
    ]

    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Over 90 Days AP')
    XLSX.writeFile(workbook, `AP_Over_90_Days_${new Date().toISOString().split('T')[0]}.xlsx`)
  }

  if (loading) {
    return (
      <LoadingSpinner 
        title="Loading AP Report" 
        description="Fetching accounts payable data..."
        size="large"
      />
    )
  }

  if (!apData) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">Failed to load AP data. Please try again.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Accounts Payable Report</h2>
        <p className="text-muted-foreground">Outstanding payables and vendor analysis</p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total AP Outstanding</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${(apData.total_ap / 1000).toFixed(0)}k</div>
            <p className="text-xs text-muted-foreground mt-1">{apData.invoice_count} invoices</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Not Yet Due</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${((apData.aging_summary.find(b => b.bucket === 'Not Due')?.amount || 0) / 1000).toFixed(0)}k
            </div>
            <p className="text-xs text-muted-foreground mt-1">Not overdue</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">0-90 Days Overdue</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              ${(((apData.aging_summary.find(b => b.bucket === '0-30')?.amount || 0) + 
                  (apData.aging_summary.find(b => b.bucket === '31-60')?.amount || 0) + 
                  (apData.aging_summary.find(b => b.bucket === '61-90')?.amount || 0)) / 1000).toFixed(0)}k
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Standard overdue amounts
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Over 90 Days</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              ${((apData.aging_summary.find(b => b.bucket === 'Over 90')?.amount || 0) / 1000).toFixed(0)}k
            </div>
            <p className="text-xs text-muted-foreground mt-1 mb-3">Requires immediate attention</p>
            <Button 
              onClick={() => downloadOver90Excel()}
              size="sm"
              variant="outline"
              className="w-full"
            >
              <Download className="h-4 w-4 mr-2" />
              Download Over 90
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* AP Aging Chart */}
      <Card>
        <CardHeader>
          <CardTitle>AP Aging Distribution</CardTitle>
          <CardDescription>Outstanding payables by age</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={apData.aging_summary.filter(b => b.amount > 0)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="bucket" />
              <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
              <Tooltip 
                formatter={(value) => `$${value.toLocaleString()}`}
                labelFormatter={(label) => `${label} days`}
              />
              <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                {apData.aging_summary.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={
                      entry.bucket === 'Not Due' ? '#10b981' :
                      entry.bucket === '0-30' ? '#3b82f6' :
                      entry.bucket === '31-60' ? '#f59e0b' :
                      entry.bucket === '61-90' ? '#ef4444' :
                      entry.bucket === 'Over 90' ? '#991b1b' :
                      '#6b7280'
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Top Vendors */}
      <Card>
        <CardHeader>
          <CardTitle>Top Vendors by Amount Owed</CardTitle>
          <CardDescription>Vendors with highest outstanding balances</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {apData.top_vendors.map((vendor, index) => (
              <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                <div className="flex-1">
                  <p className="font-medium">{vendor.vendor_name}</p>
                  <p className="text-sm text-muted-foreground">
                    {vendor.invoice_count} invoices • 
                    {vendor.oldest_days_overdue > 0 ? ` Oldest: ${vendor.oldest_days_overdue} days overdue` : ' All current'}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-lg">${(vendor.total_owed / 1000).toFixed(0)}k</p>
                  <p className="text-xs text-muted-foreground">
                    {((vendor.total_owed / apData.total_ap) * 100).toFixed(1)}% of total
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Invoice Details Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Invoice Details</CardTitle>
              <CardDescription>{apData.invoice_count} outstanding invoices</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search invoices..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8 w-64"
                />
              </div>
              <Button onClick={downloadExcel} size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export Excel
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('invoice_no')}
                  >
                    Invoice # {sortField === 'invoice_no' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('vendor_name')}
                  >
                    Vendor {sortField === 'vendor_name' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </TableHead>
                  <TableHead>Invoice Date</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('days_overdue')}
                  >
                    Days Overdue {sortField === 'days_overdue' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-50 text-right"
                    onClick={() => handleSort('amount')}
                  >
                    Amount {sortField === 'amount' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAndSortedInvoices.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-muted-foreground">
                      No invoices found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredAndSortedInvoices.slice(0, 100).map((invoice, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{invoice.invoice_no}</TableCell>
                      <TableCell>{invoice.vendor_name}</TableCell>
                      <TableCell>{invoice.invoice_date || 'N/A'}</TableCell>
                      <TableCell>{invoice.due_date || 'N/A'}</TableCell>
                      <TableCell>
                        {invoice.days_overdue > 0 ? (
                          <span className={`font-medium ${
                            invoice.days_overdue > 90 ? 'text-red-600' :
                            invoice.days_overdue > 60 ? 'text-orange-600' :
                            invoice.days_overdue > 30 ? 'text-yellow-600' :
                            'text-blue-600'
                          }`}>
                            {invoice.days_overdue} days
                          </span>
                        ) : (
                          <span className="text-green-600">Not Due</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        ${invoice.amount.toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
          {filteredAndSortedInvoices.length > 100 && (
            <p className="text-sm text-muted-foreground mt-2">
              Showing first 100 of {filteredAndSortedInvoices.length} invoices. Export to Excel to see all.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default APReport