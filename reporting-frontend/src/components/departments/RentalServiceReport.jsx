import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { DollarSign, Wrench, Download, RefreshCw, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { apiUrl } from '@/lib/api'

const RentalServiceReport = () => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [summary, setSummary] = useState(null)
  const [workOrders, setWorkOrders] = useState([])
  const [showDiagnostics, setShowDiagnostics] = useState(false)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl('/api/reports/departments/rental/service-report'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch rental service report')
      }

      const data = await response.json()
      setSummary(data.summary)
      setWorkOrders(data.workOrders)
      setError(null)
    } catch (err) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value)
  }

  const getStatusBadge = (status) => {
    if (status === 'Open') {
      return (
        <Badge 
          variant="secondary" 
          className="bg-yellow-100 text-yellow-800 border-yellow-200"
        >
          {status}
        </Badge>
      )
    } else if (status === 'Completed') {
      return (
        <Badge 
          variant="secondary" 
          className="bg-green-100 text-green-800 border-green-200"
        >
          {status}
        </Badge>
      )
    } else if (status === 'Invoiced') {
      return <Badge variant="default">{status}</Badge>
    } else {
      return <Badge variant="outline">{status}</Badge>
    }
  }

  const exportToCSV = () => {
    // Create CSV headers
    const headers = ['WO#', 'Bill To', 'Ship To Customer', 'Unit Number', 'Make', 'Model', 'Status', 'Date Opened', 'Total Cost']
    
    // Create CSV rows
    const rows = workOrders.map(wo => [
      wo.woNumber,
      wo.billTo || '',
      wo.shipToCustomer || '',
      wo.unitNumber || '',
      wo.make || '',
      wo.model || '',
      wo.status || '',
      wo.openDate || '',
      wo.totalCost || 0
    ])
    
    // Add summary row
    rows.push([])
    rows.push(['', '', '', '', '', '', '', 'Total:', summary?.totalCost || 0])
    
    // Convert to CSV string
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => {
        // Escape quotes and wrap in quotes if contains comma or quotes
        const cellStr = String(cell)
        if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
          return `"${cellStr.replace(/"/g, '""')}"`
        }
        return cellStr
      }).join(','))
    ].join('\n')
    
    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    const today = new Date().toISOString().split('T')[0]
    link.setAttribute('href', url)
    link.setAttribute('download', `rental_service_report_${today}.csv`)
    link.style.visibility = 'hidden'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-red-600 text-center py-4">
        Error loading rental service report: {error}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Work Orders</CardTitle>
            <Wrench className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.totalWorkOrders || 0}</div>
            <p className="text-xs text-muted-foreground">
              Open & Completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${(summary?.totalCost || 0) > 0 ? 'text-red-600' : ''}`}>
              {formatCurrency(summary?.totalCost || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Avg: {formatCurrency(summary?.averageCostPerWO || 0)}/WO
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Work Orders Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Service Work Orders for Rental Department (Open & Completed)</CardTitle>
          <div className="flex gap-2">
            <Button 
              onClick={fetchData} 
              variant="outline" 
              size="sm"
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button 
              onClick={exportToCSV} 
              variant="outline" 
              size="sm"
              disabled={workOrders.length === 0}
            >
              <Download className="h-4 w-4 mr-2" />
              Export to CSV
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>WO#</TableHead>
                  <TableHead>Bill To</TableHead>
                  <TableHead>Ship To Customer</TableHead>
                  <TableHead>Unit Number</TableHead>
                  <TableHead>Make/Model</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date Opened</TableHead>
                  <TableHead className="text-right">Total Cost</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workOrders.map((wo) => (
                  <TableRow 
                    key={wo.woNumber}
                    className={wo.totalCost > 0 ? "bg-blue-50" : ""}
                  >
                    <TableCell className="font-medium">{wo.woNumber}</TableCell>
                    <TableCell>{wo.billTo || 'N/A'}</TableCell>
                    <TableCell>{wo.shipToCustomer || 'N/A'}</TableCell>
                    <TableCell>{wo.unitNumber || 'N/A'}</TableCell>
                    <TableCell>{wo.make && wo.model ? `${wo.make} ${wo.model}` : 'N/A'}</TableCell>
                    <TableCell>{getStatusBadge(wo.status)}</TableCell>
                    <TableCell>{wo.openDate || 'N/A'}</TableCell>
                    <TableCell className={`text-right font-medium ${wo.totalCost > 0 ? 'text-red-600' : ''}`}>
                      {formatCurrency(wo.totalCost)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
              <TableRow className="bg-gray-50 font-bold">
                <TableCell colSpan={7}>Total</TableCell>
                <TableCell className={`text-right ${(summary?.totalCost || 0) > 0 ? 'text-red-600' : ''}`}>
                  {formatCurrency(summary?.totalCost || 0)}
                </TableCell>
              </TableRow>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Diagnostic Report */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CardTitle>Calculation Diagnostics</CardTitle>
              <Badge variant="outline" className="flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                Debug Mode
              </Badge>
            </div>
            <Button
              onClick={() => setShowDiagnostics(!showDiagnostics)}
              variant="outline"
              size="sm"
            >
              {showDiagnostics ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              {showDiagnostics ? 'Hide' : 'Show'} Diagnostics
            </Button>
          </div>
          <CardDescription>
            Detailed breakdown of how totals are calculated
          </CardDescription>
        </CardHeader>
        {showDiagnostics && (
          <CardContent>
            <div className="space-y-6">
              {/* Query Information */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-semibold text-blue-900 mb-2">Query Filters Applied</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• BillTo customers: 900006, 900066 (Rental Department)</li>
                  <li>• Sale Departments: 47 (PM), 45 (Shop Service), 40 (Field Service)</li>
                  <li>• Work Order Types: Open & Completed (NOT Closed or Invoiced)</li>
                  <li>• Date Range: Work orders opened on or after June 1, 2025</li>
                  <li>• WO Number Patterns: 140xxx (RENTR), 145xxx (RENTRS), 147xxx (RENTPM)</li>
                  <li>• Sale Codes: RENTR, RENTRS, RENTPM</li>
                </ul>
              </div>

              {/* Cost Breakdown by Type */}
              <div>
                <h4 className="font-semibold mb-3">Cost Breakdown by Type</h4>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Cost Type</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead className="text-right">% of Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell>Labor Costs</TableCell>
                      <TableCell className="text-right">{formatCurrency(summary?.totalLaborCost || 0)}</TableCell>
                      <TableCell className="text-right">
                        {summary?.totalCost > 0 
                          ? `${((summary.totalLaborCost / summary.totalCost) * 100).toFixed(1)}%`
                          : '0%'}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Parts Costs</TableCell>
                      <TableCell className="text-right">{formatCurrency(summary?.totalPartsCost || 0)}</TableCell>
                      <TableCell className="text-right">
                        {summary?.totalCost > 0 
                          ? `${((summary.totalPartsCost / summary.totalCost) * 100).toFixed(1)}%`
                          : '0%'}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Misc Costs</TableCell>
                      <TableCell className="text-right">{formatCurrency(summary?.totalMiscCost || 0)}</TableCell>
                      <TableCell className="text-right">
                        {summary?.totalCost > 0 
                          ? `${((summary.totalMiscCost / summary.totalCost) * 100).toFixed(1)}%`
                          : '0%'}
                      </TableCell>
                    </TableRow>
                    <TableRow className="font-bold border-t-2">
                      <TableCell>Total</TableCell>
                      <TableCell className="text-right">{formatCurrency(summary?.totalCost || 0)}</TableCell>
                      <TableCell className="text-right">100%</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>

              {/* Top 10 Work Orders by Cost */}
              <div>
                <h4 className="font-semibold mb-3">Top 10 Work Orders by Cost</h4>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>WO#</TableHead>
                      <TableHead>Unit</TableHead>
                      <TableHead className="text-right">Labor</TableHead>
                      <TableHead className="text-right">Parts</TableHead>
                      <TableHead className="text-right">Misc</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {workOrders.slice(0, 10).map((wo) => (
                      <TableRow key={wo.woNumber}>
                        <TableCell className="font-mono">{wo.woNumber}</TableCell>
                        <TableCell>{wo.unitNumber || 'N/A'}</TableCell>
                        <TableCell className="text-right">{formatCurrency(wo.laborCost)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(wo.partsCost)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(wo.miscCost)}</TableCell>
                        <TableCell className="text-right font-semibold">{formatCurrency(wo.totalCost)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* SQL Query Reference */}
              <div className="bg-gray-50 border rounded-lg p-4">
                <h4 className="font-semibold mb-2">Data Sources</h4>
                <div className="text-sm text-gray-700 space-y-2">
                  <p><strong>Work Orders:</strong> ben002.WO table</p>
                  <p><strong>Labor Costs:</strong> ben002.WOLabor table (SUM of Cost field)</p>
                  <p><strong>Parts Costs:</strong> ben002.WOParts table (SUM of Cost field)</p>
                  <p><strong>Misc Costs:</strong> ben002.WOMisc table (SUM of Cost field)</p>
                  <p className="mt-3 text-yellow-700">
                    <strong>Note:</strong> Total Cost = Labor Cost + Parts Cost + Misc Cost for each work order
                  </p>
                  <p className="text-yellow-700">
                    If totals don't match Softbase CRM, please check:
                    <br />• Date filters (we only show WOs opened after June 1, 2025)
                    <br />• Status filters (we exclude Closed and Invoiced WOs)
                    <br />• Bill To filters (only 900006 and 900066)
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

    </div>
  )
}

export default RentalServiceReport