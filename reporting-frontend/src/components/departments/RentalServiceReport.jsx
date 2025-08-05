import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { DollarSign, Wrench, Download, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { apiUrl } from '@/lib/api'

const RentalServiceReport = () => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [summary, setSummary] = useState(null)
  const [workOrders, setWorkOrders] = useState([])
  const [woLookup, setWoLookup] = useState('140001897')
  const [woDetail, setWoDetail] = useState(null)
  const [loadingWoDetail, setLoadingWoDetail] = useState(false)

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

  const lookupWorkOrder = async () => {
    if (!woLookup.trim()) return
    
    try {
      setLoadingWoDetail(true)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl(`/api/reports/departments/rental/wo-detail/${woLookup.trim()}`), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        if (response.status === 404) {
          setWoDetail({ error: 'Work order not found' })
        } else {
          throw new Error('Failed to fetch work order details')
        }
      } else {
        const data = await response.json()
        setWoDetail(data)
      }
    } catch (err) {
      setWoDetail({ error: err.message || 'An error occurred' })
    } finally {
      setLoadingWoDetail(false)
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
            <CardTitle className="text-sm font-medium">Total Invoice Amount</CardTitle>
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
                  <TableHead className="text-right">Invoice Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workOrders.map((wo) => (
                  <TableRow 
                    key={wo.woNumber}
                    className={wo.totalCost > 0 ? "bg-red-50" : ""}
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


      {/* Work Order Lookup */}
      <Card>
        <CardHeader>
          <CardTitle>Work Order Detail Lookup</CardTitle>
          <CardDescription>
            Look up specific work order details to compare with invoices
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              placeholder="Enter Work Order Number (e.g. 140001897)"
              value={woLookup}
              onChange={(e) => setWoLookup(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && lookupWorkOrder()}
              className="flex-1 px-3 py-2 border rounded-md"
            />
            <Button 
              onClick={lookupWorkOrder}
              disabled={loadingWoDetail || !woLookup.trim()}
            >
              {loadingWoDetail ? 'Loading...' : 'Look Up'}
            </Button>
          </div>

          {woDetail && (
            <div className="space-y-4">
              {woDetail.error ? (
                <div className="text-red-600">{woDetail.error}</div>
              ) : (
                <>
                  {/* Work Order Header */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">Work Order: {woDetail.workOrder.number}</h4>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>Bill To: {woDetail.workOrder.billTo} - {woDetail.workOrder.customerName}</div>
                      <div>Unit: {woDetail.workOrder.unitNo || 'N/A'}</div>
                      <div>Make/Model: {woDetail.workOrder.make} {woDetail.workOrder.model}</div>
                      <div>Sale Code: {woDetail.workOrder.saleCode}</div>
                    </div>
                  </div>

                  {/* Cost Breakdown */}
                  <div className="space-y-4">
                    {/* Labor */}
                    <div>
                      <h5 className="font-semibold mb-2">Labor Details</h5>
                      {(woDetail.labor.details.length > 0 || woDetail.labor.quoteItems?.length > 0) ? (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Mechanic</TableHead>
                              <TableHead>Date</TableHead>
                              <TableHead className="text-right">Hours</TableHead>
                              <TableHead className="text-right">Cost</TableHead>
                              <TableHead className="text-right">Sell</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {woDetail.labor.details.map((item, idx) => (
                              <TableRow key={idx}>
                                <TableCell>{item.MechanicName}</TableCell>
                                <TableCell>{item.DateOfLabor ? new Date(item.DateOfLabor).toLocaleDateString() : 'N/A'}</TableCell>
                                <TableCell className="text-right">{item.Hours || 0}</TableCell>
                                <TableCell className="text-right">{formatCurrency(item.Cost || 0)}</TableCell>
                                <TableCell className="text-right">{formatCurrency(item.Sell || 0)}</TableCell>
                              </TableRow>
                            ))}
                            {/* Show flat rate labor from quotes */}
                            {woDetail.labor.quoteItems?.map((item, idx) => (
                              <TableRow key={`quote-${idx}`} className="bg-yellow-50">
                                <TableCell>Flat Rate Labor</TableCell>
                                <TableCell>Quote</TableCell>
                                <TableCell className="text-right">-</TableCell>
                                <TableCell className="text-right">-</TableCell>
                                <TableCell className="text-right">{formatCurrency(item.Amount || 0)}</TableCell>
                              </TableRow>
                            ))}
                            <TableRow className="font-semibold">
                              <TableCell colSpan={3}>Total Labor</TableCell>
                              <TableCell className="text-right">{formatCurrency(woDetail.labor.costTotal)}</TableCell>
                              <TableCell className="text-right">{formatCurrency(woDetail.labor.sellTotal)}</TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      ) : (
                        <p className="text-gray-500">No labor charges</p>
                      )}
                    </div>

                    {/* Parts */}
                    <div>
                      <h5 className="font-semibold mb-2">Parts Details</h5>
                      {woDetail.parts.details.length > 0 ? (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Part #</TableHead>
                              <TableHead>Description</TableHead>
                              <TableHead className="text-right">Qty</TableHead>
                              <TableHead className="text-right">Cost Each</TableHead>
                              <TableHead className="text-right">Sell Each</TableHead>
                              <TableHead className="text-right">Extended Sell</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {woDetail.parts.details.map((item, idx) => (
                              <TableRow key={idx}>
                                <TableCell>{item.PartNo}</TableCell>
                                <TableCell>{item.Description}</TableCell>
                                <TableCell className="text-right">{item.Qty || 0}</TableCell>
                                <TableCell className="text-right">{formatCurrency(item.Cost || 0)}</TableCell>
                                <TableCell className="text-right">{formatCurrency(item.Sell || 0)}</TableCell>
                                <TableCell className="text-right">{formatCurrency(item.ExtendedSell || 0)}</TableCell>
                              </TableRow>
                            ))}
                            <TableRow className="font-semibold">
                              <TableCell colSpan={5}>Total Parts</TableCell>
                              <TableCell className="text-right">{formatCurrency(woDetail.parts.sellTotal)}</TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      ) : (
                        <p className="text-gray-500">No parts charges</p>
                      )}
                    </div>

                    {/* Misc */}
                    <div>
                      <h5 className="font-semibold mb-2">Misc/Freight Details</h5>
                      {woDetail.misc.details.length > 0 ? (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Description</TableHead>
                              <TableHead className="text-right">Cost</TableHead>
                              <TableHead className="text-right">Sell</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {woDetail.misc.details.map((item, idx) => (
                              <TableRow key={idx}>
                                <TableCell>{item.Description}</TableCell>
                                <TableCell className="text-right">{formatCurrency(item.Cost || 0)}</TableCell>
                                <TableCell className="text-right">{formatCurrency(item.Sell || 0)}</TableCell>
                              </TableRow>
                            ))}
                            <TableRow className="font-semibold">
                              <TableCell>Total Misc</TableCell>
                              <TableCell className="text-right">{formatCurrency(woDetail.misc.costTotal)}</TableCell>
                              <TableCell className="text-right">{formatCurrency(woDetail.misc.sellTotal)}</TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      ) : (
                        <p className="text-gray-500">No misc charges</p>
                      )}
                    </div>

                    {/* Summary */}
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <h5 className="font-semibold mb-2">Cost vs Sell Comparison</h5>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span>Total Cost (what we show in report):</span>
                          <span className="font-semibold">{formatCurrency(woDetail.totals.totalCost)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Total Sell Price (what customer is charged):</span>
                          <span className="font-semibold">{formatCurrency(woDetail.totals.totalSell)}</span>
                        </div>
                        <div className="flex justify-between text-red-600">
                          <span>Difference:</span>
                          <span className="font-semibold">
                            {formatCurrency(woDetail.totals.totalSell - woDetail.totals.totalCost)}
                          </span>
                        </div>
                      </div>
                      <p className="text-sm mt-3 text-yellow-800">
                        <strong>Note:</strong> Our report shows internal COST, not the SELL price charged to customers. 
                        This explains why the invoice total ({formatCurrency(woDetail.totals.totalSell)}) 
                        differs from our report total ({formatCurrency(woDetail.totals.totalCost)}).
                      </p>
                    </div>

                    {/* Invoice Data if Available */}
                    {woDetail.invoice && woDetail.invoice.length > 0 && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <h5 className="font-semibold mb-2">Associated Invoice</h5>
                        {woDetail.invoice.map((inv, idx) => (
                          <div key={idx} className="text-sm space-y-1">
                            <p>Invoice #: {inv.InvoiceNo}</p>
                            <p>Date: {new Date(inv.InvoiceDate).toLocaleDateString()}</p>
                            <p>Grand Total: {formatCurrency(inv.GrandTotal)}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}
        </CardContent>
      </Card>

    </div>
  )
}

export default RentalServiceReport