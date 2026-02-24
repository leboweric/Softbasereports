import { useState, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Button } from '@/components/ui/button'
import { Download, FileText, ArrowUpDown, ArrowUp, ArrowDown, ChevronDown, ChevronRight, DollarSign, Clock, Wrench, Users } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import ExcelJS from 'exceljs'
import { saveAs } from 'file-saver'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { apiUrl } from '@/lib/api'

const CostPerHour = () => {
  const [loading, setLoading] = useState(false)
  const [reportData, setReportData] = useState(null)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [error, setError] = useState(null)
  const [activeView, setActiveView] = useState('series') // 'series', 'customer', 'units'
  const [expandedSeries, setExpandedSeries] = useState(new Set())
  const [expandedCustomers, setExpandedCustomers] = useState(new Set())
  const [sortConfig, setSortConfig] = useState({ key: 'total_cost', direction: 'desc' })

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return '—'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount)
  }

  const formatNumber = (num, decimals = 0) => {
    if (num === null || num === undefined) return '—'
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(num)
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    if (dateString.includes('-') && dateString.length === 10) {
      const [year, month, day] = dateString.split('-')
      return `${month}/${day}/${year}`
    }
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' })
  }

  const handleSort = (key) => {
    setSortConfig({
      key,
      direction: sortConfig.key === key && sortConfig.direction === 'desc' ? 'asc' : 'desc'
    })
  }

  const getSortIcon = (column) => {
    if (sortConfig.key !== column) {
      return <ArrowUpDown className="h-3 w-3 text-gray-400" />
    }
    return sortConfig.direction === 'desc'
      ? <ArrowDown className="h-3 w-3" />
      : <ArrowUp className="h-3 w-3" />
  }

  const sortData = (data) => {
    if (!data || !sortConfig.key) return data
    return [...data].sort((a, b) => {
      let aVal = a[sortConfig.key]
      let bVal = b[sortConfig.key]
      if (aVal == null) aVal = -Infinity
      if (bVal == null) bVal = -Infinity
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortConfig.direction === 'desc' ? bVal - aVal : aVal - bVal
      }
      return sortConfig.direction === 'desc'
        ? String(bVal).localeCompare(String(aVal))
        : String(aVal).localeCompare(String(bVal))
    })
  }

  const toggleSeries = (key) => {
    setExpandedSeries(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const toggleCustomer = (key) => {
    setExpandedCustomers(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  // Set default dates to trailing 12 months
  useState(() => {
    const now = new Date()
    const end = now.toISOString().split('T')[0]
    const start = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate()).toISOString().split('T')[0]
    setStartDate(start)
    setEndDate(end)
  })

  const fetchReport = async () => {
    if (!startDate || !endDate) {
      setError('Please select both start and end dates')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const token = localStorage.getItem('token')
      const url = apiUrl(`/api/reports/departments/service/cost-per-hour?start_date=${startDate}&end_date=${endDate}`)

      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` },
      })

      if (response.ok) {
        const data = await response.json()
        setReportData(data)
      } else {
        const errorData = await response.json()
        setError(errorData.error || 'Failed to fetch report')
      }
    } catch (error) {
      console.error('Error fetching cost per hour report:', error)
      setError('Error fetching report')
    } finally {
      setLoading(false)
    }
  }

  const downloadExcel = async () => {
    if (!reportData) return

    const workbook = new ExcelJS.Workbook()
    
    // Series Summary sheet
    const seriesSheet = workbook.addWorksheet('Series Summary')
    const titleRow = seriesSheet.addRow(['Cost per Operating Hour by Forklift Series'])
    titleRow.font = { size: 16, bold: true }
    seriesSheet.addRow([`${formatDate(startDate)} - ${formatDate(endDate)}`]).font = { size: 11 }
    seriesSheet.addRow([])

    const seriesHeaders = ['Make', 'Series', 'Units', 'Customers', 'Total Cost', 'Parts', 'Labor', 'Misc', 'Total Hours', 'Cost/Hour', 'Avg Cost/Unit', 'WOs', 'PM Contracts']
    const seriesHeaderRow = seriesSheet.addRow(seriesHeaders)
    seriesHeaderRow.font = { bold: true }
    seriesHeaderRow.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF5F5F5' } }

    reportData.series_summary?.forEach(s => {
      seriesSheet.addRow([
        s.make, s.series, s.unit_count, s.customer_count,
        s.total_cost, s.parts_cost, s.labor_cost, s.misc_cost,
        s.total_hours, s.cost_per_hour || 'N/A',
        s.avg_cost_per_unit, s.invoice_count, s.pm_contract_count
      ])
    })

    // Summary row
    const summary = reportData.summary
    const summaryRow = seriesSheet.addRow([
      '', 'TOTAL', summary?.total_units, summary?.customer_count,
      summary?.total_cost, '', '', '',
      summary?.total_hours, summary?.overall_cost_per_hour || 'N/A',
      '', '', ''
    ])
    summaryRow.font = { bold: true }
    summaryRow.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFFFFACD' } }

    seriesSheet.getColumn(5).numFmt = '$#,##0.00'
    seriesSheet.getColumn(6).numFmt = '$#,##0.00'
    seriesSheet.getColumn(7).numFmt = '$#,##0.00'
    seriesSheet.getColumn(8).numFmt = '$#,##0.00'
    seriesSheet.getColumn(9).numFmt = '#,##0.0'
    seriesSheet.getColumn(10).numFmt = '$#,##0.00'
    seriesSheet.getColumn(11).numFmt = '$#,##0.00'

    seriesSheet.columns.forEach(col => { col.width = 14 })
    seriesSheet.getColumn(1).width = 10
    seriesSheet.getColumn(2).width = 16

    // Customer Breakdown sheet
    const custSheet = workbook.addWorksheet('By Customer')
    const custTitle = custSheet.addRow(['Cost per Operating Hour by Customer'])
    custTitle.font = { size: 16, bold: true }
    custSheet.addRow([`${formatDate(startDate)} - ${formatDate(endDate)}`]).font = { size: 11 }
    custSheet.addRow([])

    reportData.customer_breakdown?.forEach(cust => {
      const custRow = custSheet.addRow([`${cust.customer_name} (${cust.customer_no})`, '', cust.unit_count, '', cust.total_cost, '', '', '', cust.total_hours, cust.cost_per_hour || 'N/A'])
      custRow.font = { bold: true }
      custRow.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFE8E8E8' } }

      cust.series?.forEach(s => {
        custSheet.addRow(['', `${s.make} ${s.series}`, s.unit_count, '', s.total_cost, '', '', '', s.total_hours, s.cost_per_hour || 'N/A'])
      })
      custSheet.addRow([])
    })

    custSheet.getColumn(5).numFmt = '$#,##0.00'
    custSheet.getColumn(9).numFmt = '#,##0.0'
    custSheet.getColumn(10).numFmt = '$#,##0.00'
    custSheet.columns.forEach(col => { col.width = 14 })
    custSheet.getColumn(1).width = 30

    // Unit Details sheet
    const unitSheet = workbook.addWorksheet('Unit Details')
    const unitTitle = unitSheet.addRow(['Unit-Level Cost per Hour Detail'])
    unitTitle.font = { size: 16, bold: true }
    unitSheet.addRow([`${formatDate(startDate)} - ${formatDate(endDate)}`]).font = { size: 11 }
    unitSheet.addRow([])

    const unitHeaders = ['Serial No', 'Unit #', 'Make', 'Series', 'Model', 'Year', 'Customer', 'Total Cost', 'Parts', 'Labor', 'Misc', 'Hours Used', 'Cost/Hour', 'WOs', 'PM Contract']
    const unitHeaderRow = unitSheet.addRow(unitHeaders)
    unitHeaderRow.font = { bold: true }
    unitHeaderRow.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF5F5F5' } }

    reportData.unit_details?.forEach(u => {
      unitSheet.addRow([
        u.serial_no, u.unit_no, u.make, u.series, u.model, u.model_year,
        u.customer_name, u.total_cost, u.parts_cost, u.labor_cost, u.misc_cost,
        u.hours_used || 'N/A', u.cost_per_hour || 'N/A', u.invoice_count,
        u.on_pm_contract ? 'Yes' : 'No'
      ])
    })

    unitSheet.getColumn(8).numFmt = '$#,##0.00'
    unitSheet.getColumn(9).numFmt = '$#,##0.00'
    unitSheet.getColumn(10).numFmt = '$#,##0.00'
    unitSheet.getColumn(11).numFmt = '$#,##0.00'
    unitSheet.getColumn(12).numFmt = '#,##0.0'
    unitSheet.getColumn(13).numFmt = '$#,##0.00'
    unitSheet.columns.forEach(col => { col.width = 14 })

    const buffer = await workbook.xlsx.writeBuffer()
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    saveAs(blob, `Cost_Per_Hour_${startDate}_to_${endDate}.xlsx`)
  }

  const sortedSeriesSummary = useMemo(() => sortData(reportData?.series_summary), [reportData?.series_summary, sortConfig])
  const sortedCustomerBreakdown = useMemo(() => sortData(reportData?.customer_breakdown), [reportData?.customer_breakdown, sortConfig])
  const sortedUnitDetails = useMemo(() => sortData(reportData?.unit_details), [reportData?.unit_details, sortConfig])

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CardTitle>Cost per Operating Hour by Forklift Series</CardTitle>
              <Clock className="h-5 w-5 text-gray-500" />
            </div>
            {reportData && (
              <Button onClick={downloadExcel} size="sm" variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Export Excel
              </Button>
            )}
          </div>
          <CardDescription>
            Actual maintenance cost per operating hour by series — use for quoting PM contracts and identifying high-cost equipment
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Date Range & Generate */}
          <div className="grid grid-cols-3 gap-4 items-end">
            <div>
              <Label htmlFor="cph-start-date">Start Date</Label>
              <Input id="cph-start-date" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="mt-1" />
            </div>
            <div>
              <Label htmlFor="cph-end-date">End Date</Label>
              <Input id="cph-end-date" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="mt-1" />
            </div>
            <div>
              <Button onClick={fetchReport} disabled={loading || !startDate || !endDate} className="w-full">
                {loading ? <LoadingSpinner className="h-4 w-4 mr-2" /> : <FileText className="h-4 w-4 mr-2" />}
                Generate Report
              </Button>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">{error}</div>
          )}

          {loading && (
            <div className="flex justify-center py-8">
              <LoadingSpinner className="h-8 w-8" />
            </div>
          )}

          {reportData && !loading && (
            <div className="space-y-6 mt-4">
              {/* Summary Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-blue-700 text-sm font-medium">
                    <DollarSign className="h-4 w-4" />
                    Overall Cost/Hour
                  </div>
                  <p className="text-2xl font-bold text-blue-900 mt-1">
                    {reportData.summary?.overall_cost_per_hour ? formatCurrency(reportData.summary.overall_cost_per_hour) : 'N/A'}
                  </p>
                  <p className="text-xs text-blue-600 mt-1">
                    {formatNumber(reportData.summary?.total_hours, 0)} total hours tracked
                  </p>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-green-700 text-sm font-medium">
                    <Wrench className="h-4 w-4" />
                    Total Maintenance Cost
                  </div>
                  <p className="text-2xl font-bold text-green-900 mt-1">
                    {formatCurrency(reportData.summary?.total_cost)}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    {formatNumber(reportData.summary?.total_units)} units serviced
                  </p>
                </div>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-purple-700 text-sm font-medium">
                    <Clock className="h-4 w-4" />
                    Meter Coverage
                  </div>
                  <p className="text-2xl font-bold text-purple-900 mt-1">
                    {reportData.summary?.units_with_meter && reportData.summary?.total_units
                      ? Math.round(reportData.summary.units_with_meter / reportData.summary.total_units * 100)
                      : 0}%
                  </p>
                  <p className="text-xs text-purple-600 mt-1">
                    {formatNumber(reportData.summary?.units_with_meter)} of {formatNumber(reportData.summary?.total_units)} units have hour data
                  </p>
                </div>
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-amber-700 text-sm font-medium">
                    <Users className="h-4 w-4" />
                    Series & Customers
                  </div>
                  <p className="text-2xl font-bold text-amber-900 mt-1">
                    {formatNumber(reportData.summary?.series_count)} series
                  </p>
                  <p className="text-xs text-amber-600 mt-1">
                    across {formatNumber(reportData.summary?.customer_count)} customers
                  </p>
                </div>
              </div>

              {/* View Toggle */}
              <div className="flex gap-2 border-b pb-2">
                <Button
                  variant={activeView === 'series' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => { setActiveView('series'); setSortConfig({ key: 'total_cost', direction: 'desc' }) }}
                >
                  By Series
                </Button>
                <Button
                  variant={activeView === 'customer' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => { setActiveView('customer'); setSortConfig({ key: 'total_cost', direction: 'desc' }) }}
                >
                  By Customer
                </Button>
                <Button
                  variant={activeView === 'units' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => { setActiveView('units'); setSortConfig({ key: 'total_cost', direction: 'desc' }) }}
                >
                  Unit Detail
                </Button>
              </div>

              {/* Series Summary View */}
              {activeView === 'series' && (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-8"></TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('make')}>
                          <div className="flex items-center gap-1">Make {getSortIcon('make')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('series')}>
                          <div className="flex items-center gap-1">Series {getSortIcon('series')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50 text-right" onClick={() => handleSort('unit_count')}>
                          <div className="flex items-center gap-1 justify-end">Units {getSortIcon('unit_count')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50 text-right" onClick={() => handleSort('total_cost')}>
                          <div className="flex items-center gap-1 justify-end">Total Cost {getSortIcon('total_cost')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50 text-right" onClick={() => handleSort('total_hours')}>
                          <div className="flex items-center gap-1 justify-end">Total Hours {getSortIcon('total_hours')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50 text-right" onClick={() => handleSort('cost_per_hour')}>
                          <div className="flex items-center gap-1 justify-end font-bold text-blue-700">Cost/Hour {getSortIcon('cost_per_hour')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50 text-right" onClick={() => handleSort('avg_cost_per_unit')}>
                          <div className="flex items-center gap-1 justify-end">Avg/Unit {getSortIcon('avg_cost_per_unit')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50 text-right" onClick={() => handleSort('invoice_count')}>
                          <div className="flex items-center gap-1 justify-end">WOs {getSortIcon('invoice_count')}</div>
                        </TableHead>
                        <TableHead className="text-right">Customers</TableHead>
                        <TableHead className="text-right">PM Contracts</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sortedSeriesSummary?.map((s, idx) => {
                        const key = `${s.make}-${s.series}`
                        const isExpanded = expandedSeries.has(key)
                        const seriesUnits = reportData.unit_details?.filter(u => u.make === s.make && u.series === s.series) || []
                        return (
                          <>
                            <TableRow
                              key={key}
                              className={`cursor-pointer hover:bg-gray-50 ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}
                              onClick={() => toggleSeries(key)}
                            >
                              <TableCell className="w-8">
                                {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                              </TableCell>
                              <TableCell className="font-medium">{s.make}</TableCell>
                              <TableCell className="font-medium">{s.series}</TableCell>
                              <TableCell className="text-right">{s.unit_count}</TableCell>
                              <TableCell className="text-right font-medium">{formatCurrency(s.total_cost)}</TableCell>
                              <TableCell className="text-right">{formatNumber(s.total_hours, 1)}</TableCell>
                              <TableCell className="text-right font-bold text-blue-700">
                                {s.cost_per_hour ? formatCurrency(s.cost_per_hour) : <span className="text-gray-400 font-normal text-xs">No meter data</span>}
                              </TableCell>
                              <TableCell className="text-right">{formatCurrency(s.avg_cost_per_unit)}</TableCell>
                              <TableCell className="text-right">{s.invoice_count}</TableCell>
                              <TableCell className="text-right">{s.customer_count}</TableCell>
                              <TableCell className="text-right">{s.pm_contract_count}</TableCell>
                            </TableRow>
                            {isExpanded && seriesUnits.map((u, uidx) => (
                              <TableRow key={`${key}-${u.serial_no}`} className="bg-blue-50/30">
                                <TableCell></TableCell>
                                <TableCell className="text-xs text-gray-500 pl-6">{u.serial_no}</TableCell>
                                <TableCell className="text-xs">{u.model}</TableCell>
                                <TableCell className="text-xs text-right">{u.model_year}</TableCell>
                                <TableCell className="text-xs text-right">{formatCurrency(u.total_cost)}</TableCell>
                                <TableCell className="text-xs text-right">{u.hours_used ? formatNumber(u.hours_used, 1) : '—'}</TableCell>
                                <TableCell className="text-xs text-right font-semibold text-blue-600">
                                  {u.cost_per_hour ? formatCurrency(u.cost_per_hour) : '—'}
                                </TableCell>
                                <TableCell className="text-xs text-right text-gray-500">{u.customer_name}</TableCell>
                                <TableCell className="text-xs text-right">{u.invoice_count}</TableCell>
                                <TableCell></TableCell>
                                <TableCell className="text-xs text-center">
                                  {u.on_pm_contract ? <span className="text-green-600">Yes</span> : ''}
                                </TableCell>
                              </TableRow>
                            ))}
                          </>
                        )
                      })}
                      {/* Totals Row */}
                      <TableRow className="bg-gray-100 font-bold border-t-2">
                        <TableCell></TableCell>
                        <TableCell colSpan={2}>TOTAL</TableCell>
                        <TableCell className="text-right">{formatNumber(reportData.summary?.total_units)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(reportData.summary?.total_cost)}</TableCell>
                        <TableCell className="text-right">{formatNumber(reportData.summary?.total_hours, 1)}</TableCell>
                        <TableCell className="text-right text-blue-700">
                          {reportData.summary?.overall_cost_per_hour ? formatCurrency(reportData.summary.overall_cost_per_hour) : '—'}
                        </TableCell>
                        <TableCell></TableCell>
                        <TableCell></TableCell>
                        <TableCell className="text-right">{formatNumber(reportData.summary?.customer_count)}</TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              )}

              {/* Customer Breakdown View */}
              {activeView === 'customer' && (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-8"></TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('customer_name')}>
                          <div className="flex items-center gap-1">Customer {getSortIcon('customer_name')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50 text-right" onClick={() => handleSort('unit_count')}>
                          <div className="flex items-center gap-1 justify-end">Units {getSortIcon('unit_count')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50 text-right" onClick={() => handleSort('total_cost')}>
                          <div className="flex items-center gap-1 justify-end">Total Cost {getSortIcon('total_cost')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50 text-right" onClick={() => handleSort('total_hours')}>
                          <div className="flex items-center gap-1 justify-end">Total Hours {getSortIcon('total_hours')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50 text-right" onClick={() => handleSort('cost_per_hour')}>
                          <div className="flex items-center gap-1 justify-end font-bold text-blue-700">Cost/Hour {getSortIcon('cost_per_hour')}</div>
                        </TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sortedCustomerBreakdown?.map((cust, idx) => {
                        const key = cust.customer_no
                        const isExpanded = expandedCustomers.has(key)
                        return (
                          <>
                            <TableRow
                              key={key}
                              className={`cursor-pointer hover:bg-gray-50 ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}
                              onClick={() => toggleCustomer(key)}
                            >
                              <TableCell className="w-8">
                                {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                              </TableCell>
                              <TableCell className="font-medium">{cust.customer_name} <span className="text-gray-400 text-xs">({cust.customer_no})</span></TableCell>
                              <TableCell className="text-right">{cust.unit_count}</TableCell>
                              <TableCell className="text-right font-medium">{formatCurrency(cust.total_cost)}</TableCell>
                              <TableCell className="text-right">{formatNumber(cust.total_hours, 1)}</TableCell>
                              <TableCell className="text-right font-bold text-blue-700">
                                {cust.cost_per_hour ? formatCurrency(cust.cost_per_hour) : <span className="text-gray-400 font-normal text-xs">No meter data</span>}
                              </TableCell>
                            </TableRow>
                            {isExpanded && cust.series?.map((s) => (
                              <TableRow key={`${key}-${s.make}-${s.series}`} className="bg-blue-50/30">
                                <TableCell></TableCell>
                                <TableCell className="text-xs pl-6">{s.make} {s.series}</TableCell>
                                <TableCell className="text-xs text-right">{s.unit_count}</TableCell>
                                <TableCell className="text-xs text-right">{formatCurrency(s.total_cost)}</TableCell>
                                <TableCell className="text-xs text-right">{formatNumber(s.total_hours, 1)}</TableCell>
                                <TableCell className="text-xs text-right font-semibold text-blue-600">
                                  {s.cost_per_hour ? formatCurrency(s.cost_per_hour) : '—'}
                                </TableCell>
                              </TableRow>
                            ))}
                          </>
                        )
                      })}
                      {/* Totals Row */}
                      <TableRow className="bg-gray-100 font-bold border-t-2">
                        <TableCell></TableCell>
                        <TableCell>TOTAL ({formatNumber(reportData.summary?.customer_count)} customers)</TableCell>
                        <TableCell className="text-right">{formatNumber(reportData.summary?.total_units)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(reportData.summary?.total_cost)}</TableCell>
                        <TableCell className="text-right">{formatNumber(reportData.summary?.total_hours, 1)}</TableCell>
                        <TableCell className="text-right text-blue-700">
                          {reportData.summary?.overall_cost_per_hour ? formatCurrency(reportData.summary.overall_cost_per_hour) : '—'}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              )}

              {/* Unit Detail View */}
              {activeView === 'units' && (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('serial_no')}>
                          <div className="flex items-center gap-1">Serial # {getSortIcon('serial_no')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('make')}>
                          <div className="flex items-center gap-1">Make {getSortIcon('make')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('series')}>
                          <div className="flex items-center gap-1">Series {getSortIcon('series')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('model')}>
                          <div className="flex items-center gap-1">Model {getSortIcon('model')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('customer_name')}>
                          <div className="flex items-center gap-1">Customer {getSortIcon('customer_name')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50 text-right" onClick={() => handleSort('total_cost')}>
                          <div className="flex items-center gap-1 justify-end">Total Cost {getSortIcon('total_cost')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50 text-right" onClick={() => handleSort('hours_used')}>
                          <div className="flex items-center gap-1 justify-end">Hours Used {getSortIcon('hours_used')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50 text-right" onClick={() => handleSort('cost_per_hour')}>
                          <div className="flex items-center gap-1 justify-end font-bold text-blue-700">Cost/Hour {getSortIcon('cost_per_hour')}</div>
                        </TableHead>
                        <TableHead className="cursor-pointer hover:bg-gray-50 text-right" onClick={() => handleSort('invoice_count')}>
                          <div className="flex items-center gap-1 justify-end">WOs {getSortIcon('invoice_count')}</div>
                        </TableHead>
                        <TableHead className="text-center">PM</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sortedUnitDetails?.map((u, idx) => (
                        <TableRow key={u.serial_no} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                          <TableCell className="font-mono text-xs">{u.serial_no}</TableCell>
                          <TableCell>{u.make}</TableCell>
                          <TableCell>{u.series}</TableCell>
                          <TableCell className="text-xs">{u.model}</TableCell>
                          <TableCell className="text-xs">{u.customer_name}</TableCell>
                          <TableCell className="text-right font-medium">{formatCurrency(u.total_cost)}</TableCell>
                          <TableCell className="text-right">{u.hours_used ? formatNumber(u.hours_used, 1) : <span className="text-gray-400 text-xs">No data</span>}</TableCell>
                          <TableCell className="text-right font-bold text-blue-700">
                            {u.cost_per_hour ? formatCurrency(u.cost_per_hour) : <span className="text-gray-400 font-normal text-xs">—</span>}
                          </TableCell>
                          <TableCell className="text-right">{u.invoice_count}</TableCell>
                          <TableCell className="text-center">
                            {u.on_pm_contract ? <span className="text-green-600 text-xs font-medium">Yes</span> : ''}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              {/* Methodology note */}
              <div className="bg-gray-50 border rounded-lg p-4 text-sm text-gray-600">
                <p className="font-medium text-gray-700 mb-1">Methodology</p>
                <p>
                  <strong>Cost per Hour</strong> = Total Maintenance Cost (labor + parts + misc from invoices) / Operating Hours Used in Period.
                  Hours are calculated as MAX(HourMeter) - MIN(HourMeter) from invoice readings within the date range.
                  Units require at least 2 meter readings with increasing values to calculate cost/hour.
                  Units without sufficient meter data are included in cost totals but excluded from cost/hour calculations.
                  Non-forklift equipment (batteries, chargers, scissor lifts) is excluded.
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default CostPerHour
