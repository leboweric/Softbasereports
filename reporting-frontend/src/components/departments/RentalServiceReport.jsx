import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { DollarSign, Wrench, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { apiUrl } from '@/lib/api'

const RentalServiceReport = () => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [summary, setSummary] = useState(null)
  const [workOrders, setWorkOrders] = useState([])

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
    const variants = {
      'Open': 'destructive',
      'Completed': 'secondary',
      'Invoiced': 'default',
      'Closed': 'outline'
    }
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>
  }

  const exportToCSV = () => {
    // Create CSV headers
    const headers = ['WO#', 'Bill To', 'Ship To Customer', 'Serial Number', 'Make', 'Model', 'Status', 'Date Opened', 'Total Cost']
    
    // Create CSV rows
    const rows = workOrders.map(wo => [
      wo.woNumber,
      wo.billTo || '',
      wo.shipToCustomer || '',
      wo.serialNumber || '',
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
            <CardTitle className="text-sm font-medium">Open Work Orders</CardTitle>
            <Wrench className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.totalWorkOrders || 0}</div>
            <p className="text-xs text-muted-foreground">
              Currently open
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary?.totalCost || 0)}</div>
            <p className="text-xs text-muted-foreground">
              Avg: {formatCurrency(summary?.averageCostPerWO || 0)}/WO
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Work Orders Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Open Service Work Orders for Rental Department</CardTitle>
          <Button 
            onClick={exportToCSV} 
            variant="outline" 
            size="sm"
            disabled={workOrders.length === 0}
          >
            <Download className="h-4 w-4 mr-2" />
            Export to CSV
          </Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>WO#</TableHead>
                  <TableHead>Bill To</TableHead>
                  <TableHead>Ship To Customer</TableHead>
                  <TableHead>Serial Number</TableHead>
                  <TableHead>Make/Model</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date Opened</TableHead>
                  <TableHead className="text-right">Total Cost</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workOrders.map((wo) => (
                  <TableRow key={wo.woNumber}>
                    <TableCell className="font-medium">{wo.woNumber}</TableCell>
                    <TableCell>{wo.billTo || 'N/A'}</TableCell>
                    <TableCell>{wo.shipToCustomer || 'N/A'}</TableCell>
                    <TableCell>{wo.serialNumber || 'N/A'}</TableCell>
                    <TableCell>{wo.make && wo.model ? `${wo.make} ${wo.model}` : 'N/A'}</TableCell>
                    <TableCell>{getStatusBadge(wo.status)}</TableCell>
                    <TableCell>{wo.openDate || 'N/A'}</TableCell>
                    <TableCell className="text-right font-medium">{formatCurrency(wo.totalCost)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
              <TableRow className="bg-gray-50 font-bold">
                <TableCell colSpan={7}>Total</TableCell>
                <TableCell className="text-right">
                  {formatCurrency(summary?.totalCost || 0)}
                </TableCell>
              </TableRow>
            </Table>
          </div>
        </CardContent>
      </Card>

    </div>
  )
}

export default RentalServiceReport