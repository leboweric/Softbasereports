import { useState, useMemo, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Button } from '@/components/ui/button'
import { Download, FileText, ArrowUpDown, ArrowUp, ArrowDown, TrendingUp, AlertTriangle } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import ExcelJS from 'exceljs'
import { saveAs } from 'file-saver'
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

const UnitsRepairCost = () => {
  const [loading, setLoading] = useState(false)
  const [reportData, setReportData] = useState(null)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [customers, setCustomers] = useState([])
  const [selectedCustomer, setSelectedCustomer] = useState('')
  const [customersLoading, setCustomersLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sortConfig, setSortConfig] = useState({ key: 'total_repair_cost', direction: 'desc' })

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
    if (dateString.includes('-') && dateString.length === 10) {
      const [year, month, day] = dateString.split('-')
      return `${month}/${day}/${year}`
    }
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
      direction: sortConfig.key === key && sortConfig.direction === 'desc' ? 'asc' : 'desc'
    })
  }

  const sortedTopUnits = useMemo(() => {
    if (!reportData?.top_units || !sortConfig.key) return reportData?.top_units || []
    
    return [...reportData.top_units].sort((a, b) => {
      let aValue = a[sortConfig.key]
      let bValue = b[sortConfig.key]
      
      if (aValue == null) aValue = ''
      if (bValue == null) bValue = ''
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortConfig.direction === 'desc' ? bValue - aValue : aValue - bValue
      }
      
      return sortConfig.direction === 'desc' 
        ? String(bValue).localeCompare(String(aValue))
        : String(aValue).localeCompare(String(bValue))
    })
  }, [reportData?.top_units, sortConfig])

  const getSortIcon = (column) => {
    if (sortConfig.key !== column) {
      return <ArrowUpDown className="h-4 w-4 text-gray-400" />
    }
    return sortConfig.direction === 'desc' 
      ? <ArrowDown className="h-4 w-4" />
      : <ArrowUp className="h-4 w-4" />
  }

  // Load customers when date range changes
  useEffect(() => {
    if (startDate && endDate) {
      fetchCustomers()
    }
  }, [startDate, endDate])

  const fetchCustomers = async () => {
    setCustomersLoading(true)
    try {
      const token = localStorage.getItem('token')
      const url = apiUrl(`/api/reports/departments/service/customers?start_date=${startDate}&end_date=${endDate}`)
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        if (Array.isArray(data)) {
          // Filter out "ALL" option - we need a specific customer for this report
          const filteredCustomers = data.filter(c => c.value !== 'ALL')
          setCustomers(filteredCustomers)
        } else {
          setCustomers([])
        }
      } else {
        const errorData = await response.json()
        setError(`Failed to load customers: ${errorData.error || response.statusText}`)
        setCustomers([])
      }
    } catch (error) {
      console.error('Error fetching customers:', error)
      setError(`Error loading customers: ${error.message}`)
      setCustomers([])
    } finally {
      setCustomersLoading(false)
    }
  }

  const getSelectedCustomerName = () => {
    if (!selectedCustomer) return ''
    const customer = customers.find(c => c.value === selectedCustomer)
    return customer ? customer.label : 'Unknown Customer'
  }

  const fetchReport = async () => {
    if (!startDate || !endDate) {
      setError('Please select both start and end dates')
      return
    }
    
    if (!selectedCustomer) {
      setError('Please select a customer')
      return
    }

    setLoading(true)
    setError(null)
    
    try {
      const token = localStorage.getItem('token')
      const url = apiUrl(`/api/reports/departments/service/units-by-repair-cost?start_date=${startDate}&end_date=${endDate}&customer_no=${selectedCustomer}`)
      
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
      console.error('Error fetching units repair cost report:', error)
      setError('Error fetching report')
    } finally {
      setLoading(false)
    }
  }

  const downloadExcel = async () => {
    if (!reportData) return

    const customerName = getSelectedCustomerName()
    const customer = reportData.customer || {}
    
    // Create new workbook
    const workbook = new ExcelJS.Workbook()
    const worksheet = workbook.addWorksheet('Units by Repair Cost')

    // Add title
    const titleRow = worksheet.addRow(['Top Units by Repair Cost'])
    titleRow.font = { size: 16, bold: true }
    titleRow.alignment = { horizontal: 'left' }

    // Add customer name on right side (we'll merge cells later)
    worksheet.getCell('J1').value = customerName
    worksheet.getCell('J1').font = { size: 16, bold: true }
    worksheet.getCell('J1').alignment = { horizontal: 'right' }

    // Add customer address and date range
    const addressParts = [customer.address, customer.city, customer.state, customer.zip].filter(Boolean)
    const addressRow = worksheet.addRow([`${customer.number || selectedCustomer} - ${addressParts.join(', ')}`])
    addressRow.font = { size: 11 }
    
    // Add date range on right
    worksheet.getCell('J2').value = `${formatDate(startDate)} - ${formatDate(endDate)}`
    worksheet.getCell('J2').font = { size: 11 }
    worksheet.getCell('J2').alignment = { horizontal: 'right' }

    // Empty row
    worksheet.addRow([])

    // Top 10 Units section
    const top10HeaderRow = worksheet.addRow(['Top 10 Units'])
    top10HeaderRow.font = { size: 12, bold: true }
    top10HeaderRow.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFE8E8E8' }
    }

    // Column headers
    const headers = ['Mfg', 'Series', 'Model', 'Serial Number', 'Model Year', 'Unit #', 'Total', 'Currency', '% of Total', 'Series Ave']
    const headerRow = worksheet.addRow(headers)
    headerRow.font = { bold: true }
    headerRow.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFF5F5F5' }
    }
    headerRow.alignment = { horizontal: 'center' }

    // Add top units data
    sortedTopUnits.forEach(unit => {
      worksheet.addRow([
        unit.mfg || '',
        unit.series || '',
        unit.model || '',
        unit.serial_no || '',
        unit.model_year || '',
        unit.unit_no || '',
        unit.total_repair_cost,
        'USD',
        `${unit.percent_of_total}%`,
        unit.series_avg_cost
      ])
    })

    // Top 10 totals row
    const top10TotalRow = worksheet.addRow([
      '', '', 'Total Repair Costs for Top 10 Units', '', '', '',
      reportData.summary?.top_10_total || 0,
      '',
      `${reportData.summary?.top_10_percent || 0}%`,
      ''
    ])
    top10TotalRow.font = { bold: true }
    top10TotalRow.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFFFFACD' }
    }

    // Empty row
    worksheet.addRow([])

    // Additional Opportunities section (if any)
    if (reportData.additional_opportunities && reportData.additional_opportunities.length > 0) {
      const addlHeaderRow = worksheet.addRow(['Additional Opportunities'])
      addlHeaderRow.font = { size: 12, bold: true }
      addlHeaderRow.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FFE8E8E8' }
      }

      // Add additional units
      reportData.additional_opportunities.forEach(unit => {
        worksheet.addRow([
          unit.mfg || '',
          unit.series || '',
          unit.model || '',
          unit.serial_no || '',
          unit.model_year || '',
          unit.unit_no || '',
          unit.total_repair_cost,
          'USD',
          `${unit.percent_of_total}%`,
          unit.series_avg_cost
        ])
      })

      // Additional totals row
      const addlTotalRow = worksheet.addRow([
        '', '', 'Total Repair Costs for These Units', '', '', '',
        reportData.summary?.additional_total || 0,
        '',
        `${reportData.summary?.additional_percent || 0}%`,
        ''
      ])
      addlTotalRow.font = { bold: true }
      addlTotalRow.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FFFFFACD' }
      }
    }

    // Format currency columns
    worksheet.getColumn(7).numFmt = '$#,##0.00'
    worksheet.getColumn(10).numFmt = '$#,##0.00'

    // Set column widths
    worksheet.columns = [
      { width: 8 },   // Mfg
      { width: 10 },  // Series
      { width: 15 },  // Model
      { width: 18 },  // Serial Number
      { width: 12 },  // Model Year
      { width: 10 },  // Unit #
      { width: 15 },  // Total
      { width: 10 },  // Currency
      { width: 12 },  // % of Total
      { width: 12 }   // Series Ave
    ]

    // Generate Excel file
    const buffer = await workbook.xlsx.writeBuffer()
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    
    const safeCustomerName = customerName.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 30)
    saveAs(blob, `units_repair_cost_${safeCustomerName}_${startDate}_${endDate}.xlsx`)
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CardTitle>Top Units by Repair Cost</CardTitle>
              <TrendingUp className="h-5 w-5 text-gray-500" />
            </div>
            {reportData && (
              <Button onClick={downloadExcel} size="sm" variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Export Excel
              </Button>
            )}
          </div>
          <CardDescription>
            Identify high-maintenance equipment to justify replacement decisions
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-4 gap-4 items-end">
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
            <div>
              <Label htmlFor="customer-select">Customer</Label>
              <Select 
                value={selectedCustomer} 
                onValueChange={setSelectedCustomer}
                disabled={customersLoading || !startDate || !endDate}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder={
                    !startDate || !endDate ? "Select dates first" :
                    customersLoading ? "Loading customers..." : 
                    customers.length === 0 ? "No customers found" :
                    "Select customer"
                  } />
                </SelectTrigger>
                <SelectContent>
                  {customers.map((customer) => (
                    <SelectItem key={customer.value} value={customer.value}>
                      {customer.label}
                      {customer.invoiceCount && (
                        <span className="text-gray-500 ml-2">({customer.invoiceCount} invoices)</span>
                      )}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Button 
                onClick={fetchReport} 
                disabled={loading || !startDate || !endDate || !selectedCustomer}
                className="w-full"
              >
                {loading ? <LoadingSpinner className="h-4 w-4 mr-2" /> : <FileText className="h-4 w-4 mr-2" />}
                Generate Report
              </Button>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {loading && (
            <div className="flex justify-center py-8">
              <LoadingSpinner className="h-8 w-8" />
            </div>
          )}

          {reportData && !loading && (
            <div className="space-y-6 mt-6">
              {/* Customer Header */}
              <div className="flex justify-between items-start border-b pb-4">
                <div>
                  <h3 className="text-lg font-semibold">{reportData.customer?.name || getSelectedCustomerName()}</h3>
                  <p className="text-sm text-gray-500">
                    {reportData.customer?.number} - {reportData.customer?.address} {reportData.customer?.city}, {reportData.customer?.state} {reportData.customer?.zip}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">{formatDate(startDate)} - {formatDate(endDate)}</p>
                </div>
              </div>

              {/* Top 10 Units Table */}
              {sortedTopUnits.length > 0 ? (
                <div>
                  <h4 className="font-semibold mb-2 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-500" />
                    Top 10 Units
                  </h4>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead 
                          className="cursor-pointer hover:bg-gray-50"
                          onClick={() => handleSort('mfg')}
                        >
                          <div className="flex items-center gap-1">
                            Mfg {getSortIcon('mfg')}
                          </div>
                        </TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-gray-50"
                          onClick={() => handleSort('series')}
                        >
                          <div className="flex items-center gap-1">
                            Series {getSortIcon('series')}
                          </div>
                        </TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-gray-50"
                          onClick={() => handleSort('model')}
                        >
                          <div className="flex items-center gap-1">
                            Model {getSortIcon('model')}
                          </div>
                        </TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-gray-50"
                          onClick={() => handleSort('serial_no')}
                        >
                          <div className="flex items-center gap-1">
                            Serial Number {getSortIcon('serial_no')}
                          </div>
                        </TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-gray-50"
                          onClick={() => handleSort('model_year')}
                        >
                          <div className="flex items-center gap-1">
                            Model Year {getSortIcon('model_year')}
                          </div>
                        </TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-gray-50"
                          onClick={() => handleSort('unit_no')}
                        >
                          <div className="flex items-center gap-1">
                            Unit # {getSortIcon('unit_no')}
                          </div>
                        </TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-gray-50 text-right"
                          onClick={() => handleSort('total_repair_cost')}
                        >
                          <div className="flex items-center justify-end gap-1">
                            Total {getSortIcon('total_repair_cost')}
                          </div>
                        </TableHead>
                        <TableHead className="text-center">Currency</TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-gray-50 text-right"
                          onClick={() => handleSort('percent_of_total')}
                        >
                          <div className="flex items-center justify-end gap-1">
                            % of Total {getSortIcon('percent_of_total')}
                          </div>
                        </TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-gray-50 text-right"
                          onClick={() => handleSort('series_avg_cost')}
                        >
                          <div className="flex items-center justify-end gap-1">
                            Series Ave {getSortIcon('series_avg_cost')}
                          </div>
                        </TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sortedTopUnits.map((unit, index) => (
                        <TableRow key={unit.serial_no || index}>
                          <TableCell>{unit.mfg}</TableCell>
                          <TableCell>{unit.series}</TableCell>
                          <TableCell>{unit.model}</TableCell>
                          <TableCell className="font-mono">{unit.serial_no}</TableCell>
                          <TableCell>{unit.model_year || '-'}</TableCell>
                          <TableCell>{unit.unit_no || '-'}</TableCell>
                          <TableCell className="text-right font-medium">{formatCurrency(unit.total_repair_cost)}</TableCell>
                          <TableCell className="text-center text-gray-500">USD</TableCell>
                          <TableCell className="text-right">{unit.percent_of_total}%</TableCell>
                          <TableCell className="text-right">{formatCurrency(unit.series_avg_cost)}</TableCell>
                        </TableRow>
                      ))}
                      {/* Totals row */}
                      <TableRow className="bg-amber-50 font-semibold">
                        <TableCell colSpan={6}>Total Repair Costs for Top 10 Units</TableCell>
                        <TableCell className="text-right">{formatCurrency(reportData.summary?.top_10_total)}</TableCell>
                        <TableCell></TableCell>
                        <TableCell className="text-right">{reportData.summary?.top_10_percent}%</TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No repair cost data found for this customer in the selected date range.
                </div>
              )}

              {/* Additional Opportunities */}
              {reportData.additional_opportunities && reportData.additional_opportunities.length > 0 && (
                <div className="mt-6">
                  <h4 className="font-semibold mb-2">Additional Opportunities</h4>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Mfg</TableHead>
                        <TableHead>Series</TableHead>
                        <TableHead>Model</TableHead>
                        <TableHead>Serial Number</TableHead>
                        <TableHead>Model Year</TableHead>
                        <TableHead>Unit #</TableHead>
                        <TableHead className="text-right">Total</TableHead>
                        <TableHead className="text-center">Currency</TableHead>
                        <TableHead className="text-right">% of Total</TableHead>
                        <TableHead className="text-right">Series Ave</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {reportData.additional_opportunities.map((unit, index) => (
                        <TableRow key={unit.serial_no || index}>
                          <TableCell>{unit.mfg}</TableCell>
                          <TableCell>{unit.series}</TableCell>
                          <TableCell>{unit.model}</TableCell>
                          <TableCell className="font-mono">{unit.serial_no}</TableCell>
                          <TableCell>{unit.model_year || '-'}</TableCell>
                          <TableCell>{unit.unit_no || '-'}</TableCell>
                          <TableCell className="text-right">{formatCurrency(unit.total_repair_cost)}</TableCell>
                          <TableCell className="text-center text-gray-500">USD</TableCell>
                          <TableCell className="text-right">{unit.percent_of_total}%</TableCell>
                          <TableCell className="text-right">{formatCurrency(unit.series_avg_cost)}</TableCell>
                        </TableRow>
                      ))}
                      {/* Totals row */}
                      <TableRow className="bg-gray-50 font-semibold">
                        <TableCell colSpan={6}>Total Repair Costs for These Units</TableCell>
                        <TableCell className="text-right">{formatCurrency(reportData.summary?.additional_total)}</TableCell>
                        <TableCell></TableCell>
                        <TableCell className="text-right">{reportData.summary?.additional_percent}%</TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              )}

              {/* Summary Card */}
              <Card className="bg-gray-50">
                <CardContent className="pt-4">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-sm text-gray-500">Total Units</p>
                      <p className="text-2xl font-bold">{reportData.summary?.unit_count || 0}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Grand Total Repair Costs</p>
                      <p className="text-2xl font-bold text-red-600">{formatCurrency(reportData.summary?.grand_total)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Top 10 Units Account For</p>
                      <p className="text-2xl font-bold text-amber-600">{reportData.summary?.top_10_percent}%</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default UnitsRepairCost
