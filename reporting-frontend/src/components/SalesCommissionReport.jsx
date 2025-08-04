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
import { Download, DollarSign, TrendingUp, Package, Truck } from 'lucide-react'
import { apiUrl } from '@/lib/api'
import * as XLSX from 'xlsx'

const SalesCommissionReport = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [commissionData, setCommissionData] = useState(null)
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date()
    // Default to previous month since commissions are usually calculated for completed months
    const prevMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    return `${prevMonth.getFullYear()}-${String(prevMonth.getMonth() + 1).padStart(2, '0')}`
  })

  useEffect(() => {
    fetchCommissionData()
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

          {/* Commission Rules */}
          <Card>
            <CardHeader>
              <CardTitle>Commission Structure</CardTitle>
              <CardDescription>Current commission rates and rules</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <p>• <strong>Rental Equipment:</strong> Commissionable at standard rate</p>
                <p>• <strong>Used Equipment:</strong> Commissionable at standard rate</p>
                <p>• <strong>Allied Equipment:</strong> Commissionable at standard rate</p>
                <p>• <strong>New Equipment:</strong> Commissionable at standard rate</p>
                <p className="text-muted-foreground mt-4">
                  Note: Commission rates may vary by sales rep based on their agreement. 
                  Contact management to update commission structures.
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