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
import { Download, DollarSign, TrendingUp, Package, Truck, ChevronDown, ChevronUp } from 'lucide-react'
import { apiUrl } from '@/lib/api'
import * as XLSX from 'xlsx'

const SalesCommissionReport = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [commissionData, setCommissionData] = useState(null)
  const [detailsData, setDetailsData] = useState(null)
  const [showDetails, setShowDetails] = useState(false)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date()
    // Default to previous month since commissions are usually calculated for completed months
    const prevMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    return `${prevMonth.getFullYear()}-${String(prevMonth.getMonth() + 1).padStart(2, '0')}`
  })

  useEffect(() => {
    fetchCommissionData()
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

  const downloadUnassignedInvoices = () => {
    if (!detailsData?.unassigned?.invoices) return

    // Create worksheet data
    const worksheetData = detailsData.unassigned.invoices.map(inv => ({
      'Invoice #': inv.invoice_no,
      'Date': new Date(inv.invoice_date).toLocaleDateString(),
      'Bill To': inv.bill_to || '-',
      'Customer': inv.customer_name,
      'Assigned To': inv.salesman || 'Unassigned',
      'Sale Code': inv.sale_code,
      'Category': inv.category,
      'Amount': inv.category_amount
    }))

    // Add total row
    worksheetData.push({
      'Invoice #': '',
      'Date': '',
      'Bill To': '',
      'Customer': '',
      'Sale Code': '',
      'Category': 'TOTAL',
      'Amount': detailsData.unassigned.total
    })

    // Create worksheet
    const worksheet = XLSX.utils.json_to_sheet(worksheetData)
    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Unassigned Invoices')

    // Generate filename with date
    const monthYear = selectedMonth.replace('-', '_')
    const filename = `unassigned_invoices_${monthYear}.xlsx`

    // Write file
    XLSX.writeFile(workbook, filename)
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
                                  <th className="text-left p-2">Bill To</th>
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
                                    <td className="p-2 font-mono text-xs">{inv.bill_to || '-'}</td>
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
                                  <td colSpan="6" className="p-2 text-right">Subtotal:</td>
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
                    
                    {/* Unassigned Invoices */}
                    {detailsData.unassigned && detailsData.unassigned.count > 0 && (
                      <div className="border rounded-lg p-4 bg-yellow-50 border-yellow-200">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold text-yellow-900">Unassigned & House Invoices</h4>
                            <Badge variant="destructive">{detailsData.unassigned.count} invoices</Badge>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="text-sm text-yellow-800">
                              Total Value: <span className="font-semibold">{formatCurrency(detailsData.unassigned.total)}</span>
                            </div>
                            <Button 
                              onClick={downloadUnassignedInvoices} 
                              size="sm" 
                              variant="outline"
                              className="border-yellow-400 hover:bg-yellow-100"
                            >
                              <Download className="h-4 w-4 mr-1" />
                              Export
                            </Button>
                          </div>
                        </div>
                        <p className="text-sm text-yellow-700 mb-3">
                          These invoices are either unassigned or assigned to "House". Review to ensure proper commission assignment.
                        </p>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-yellow-300">
                                <th className="text-left p-2">Invoice #</th>
                                <th className="text-left p-2">Date</th>
                                <th className="text-left p-2">Bill To</th>
                                <th className="text-left p-2">Customer</th>
                                <th className="text-left p-2">Assigned To</th>
                                <th className="text-left p-2">Sale Code</th>
                                <th className="text-left p-2">Category</th>
                                <th className="text-right p-2">Amount</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detailsData.unassigned.invoices.map((inv, idx) => (
                                <tr key={idx} className="border-b border-yellow-200 hover:bg-yellow-100">
                                  <td className="p-2">{inv.invoice_no}</td>
                                  <td className="p-2">{new Date(inv.invoice_date).toLocaleDateString()}</td>
                                  <td className="p-2 font-mono text-xs">{inv.bill_to || '-'}</td>
                                  <td className="p-2">{inv.customer_name}</td>
                                  <td className="p-2">
                                    <Badge 
                                      variant={inv.salesman === 'House' ? 'warning' : 'destructive'}
                                      className="text-xs"
                                    >
                                      {inv.salesman || 'Unassigned'}
                                    </Badge>
                                  </td>
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
                                  <td className="text-right p-2 font-medium">{formatCurrency(inv.category_amount)}</td>
                                </tr>
                              ))}
                              <tr className="font-semibold bg-yellow-100">
                                <td colSpan="7" className="p-2 text-right">Total Unassigned/House:</td>
                                <td className="text-right p-2">{formatCurrency(detailsData.unassigned.total)}</td>
                              </tr>
                            </tbody>
                          </table>
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
              <div className="space-y-4 text-sm">
                <div>
                  <h4 className="font-semibold text-base mb-2">New Equipment</h4>
                  <ul className="space-y-1 ml-4">
                    <li>• 20% of profit</li>
                    <li>• $100 minimum</li>
                    <li>• $50 minimum on pallet trucks</li>
                    <li>• $200 on National Accounts/Dealer Ship-ins</li>
                    <li>• $100 on Komatsu National Accounts/Dealer Ship-Ins</li>
                    <li>• "Free Loaners" without management approval charged against sale</li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-semibold text-base mb-2">Used Equipment</h4>
                  <ul className="space-y-1 ml-4">
                    <li>• 5% of selling price OR:</li>
                    <li className="ml-4">◦ 20% of profit on "Low Profit" sale</li>
                    <li className="ml-4">◦ $100 on "No Profit" sale</li>
                    <li className="ml-4">◦ Above subject to Salesperson's approval</li>
                    <li>• 20% of profit on any "Pass Through" sale</li>
                    <li>• "In-House" financing: flat $150 after first payment</li>
                    <li>• FMV Returns sold @ 30% over cost: 20% of profit</li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-semibold text-base mb-2">Rental Equipment</h4>
                  <ul className="space-y-1 ml-4">
                    <li>• 10% of rental bill on monthly rentals</li>
                    <li>• 5% of rental bill on monthly rentals &gt;20% off list</li>
                    <li>• 12-Month maximum rental commission</li>
                    <li>• LTR ≥36 months: 5% of rental rate (12-month max)</li>
                    <li className="font-semibold">• No Commission on:</li>
                    <li className="ml-4">◦ Rent to Rent</li>
                    <li className="ml-4">◦ Dealer Rentals</li>
                    <li className="ml-4">◦ House Accounts</li>
                    <li className="ml-4">◦ Service Rentals</li>
                    <li className="ml-4">◦ Construction/Rental Houses (United Rentals, Knutson, etc.)</li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-semibold text-base mb-2">Rental Equipment Sales</h4>
                  <ul className="space-y-1 ml-4">
                    <li>• 5% of selling price or 20% of profit</li>
                    <li>• $100 minimum</li>
                    <li>• $50 minimum on pallet trucks</li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-semibold text-base mb-2">Rental Purchase Option (RPO)</h4>
                  <ul className="space-y-1 ml-4">
                    <li className="font-semibold">• Inadvertent RPO (Not Stated Up Front):</li>
                    <li className="ml-4">◦ Commission paid monthly on rental</li>
                    <li className="ml-4">◦ At sale: greater of rental paid or sale commission</li>
                    <li className="font-semibold">• RPO (Signed Quote):</li>
                    <li className="ml-4">◦ Commission paid upon completion of sale</li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-semibold text-base mb-2">Allied Products</h4>
                  <ul className="space-y-1 ml-4">
                    <li>• 20% of profit</li>
                  </ul>
                </div>
                
                <p className="text-muted-foreground mt-4 text-xs border-t pt-3">
                  <strong>Note:</strong> System calculations use estimated margins where actual cost data is unavailable.
                  Actual commissions may vary based on specific contract terms and management approvals.
                </p>
              </div>
            </CardContent>
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