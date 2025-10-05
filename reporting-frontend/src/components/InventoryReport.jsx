import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Download, Package, Truck, Sparkles, Battery, Building } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const InventoryReport = ({ user }) => {
  const [inventoryData, setInventoryData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchInventoryData()
  }, [])

  const fetchInventoryData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/accounting/inventory'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setInventoryData(data)
      } else {
        setError('Failed to load inventory data')
      }
    } catch (error) {
      setError('Error loading inventory data: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const exportToExcel = async () => {
    try {
      // TODO: Implement Excel export functionality
      alert('Excel export functionality will be implemented')
    } catch (error) {
      setError('Export failed: ' + error.message)
    }
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount || 0)
  }

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'rental':
        return <Truck className="h-4 w-4" />
      case 'new':
        return <Sparkles className="h-4 w-4" />
      case 'used':
        return <Package className="h-4 w-4" />
      case 'batteries_chargers':
        return <Battery className="h-4 w-4" />
      case 'allied':
        return <Building className="h-4 w-4" />
      default:
        return <Package className="h-4 w-4" />
    }
  }

  const getCategoryLabel = (category) => {
    switch (category) {
      case 'rental':
        return 'Rental Equipment'
      case 'new':
        return 'New Equipment'
      case 'used':
        return 'Used Equipment'
      case 'batteries_chargers':
        return 'Batteries & Chargers'
      case 'allied':
        return 'Allied Equipment'
      default:
        return category
    }
  }

  const getStatusBadge = (status) => {
    const statusLower = (status || '').toLowerCase()
    if (statusLower.includes('rental') || statusLower.includes('rent')) {
      return <Badge variant="default">On Rental</Badge>
    } else if (statusLower.includes('available')) {
      return <Badge variant="secondary">Available</Badge>
    } else if (statusLower.includes('hold')) {
      return <Badge variant="destructive">Hold</Badge>
    } else {
      return <Badge variant="outline">{status}</Badge>
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-red-600">{error}</p>
          <Button onClick={fetchInventoryData} className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!inventoryData) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p>No inventory data available</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Export */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Year-End Inventory Report</h2>
          <p className="text-muted-foreground">Equipment categorized by type with financial details</p>
        </div>
        <Button onClick={exportToExcel} className="flex items-center gap-2">
          <Download className="h-4 w-4" />
          Export to Excel
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        {Object.entries(inventoryData).filter(([key]) => key !== 'totals' && key !== 'notes').map(([category, data]) => (
          <Card key={category}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                {getCategoryIcon(category)}
                {getCategoryLabel(category)}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data.qty}</div>
              <p className="text-xs text-muted-foreground">
                {formatCurrency(data.total_book_value)}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Totals Card */}
      {inventoryData.totals && (
        <Card className="bg-muted/50">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Package className="h-5 w-5" />
              Total Inventory
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-3xl font-bold">{inventoryData.totals.total_equipment}</div>
                <p className="text-sm text-muted-foreground">Total Units</p>
              </div>
              <div>
                <div className="text-3xl font-bold">{formatCurrency(inventoryData.totals.total_book_value)}</div>
                <p className="text-sm text-muted-foreground">Total Book Value</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Detailed Equipment Lists by Category */}
      {Object.entries(inventoryData).filter(([key]) => key !== 'totals' && key !== 'notes').map(([category, data]) => (
        <Card key={category}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {getCategoryIcon(category)}
              {getCategoryLabel(category)} ({data.qty} units)
            </CardTitle>
            <CardDescription>
              Total Value: {formatCurrency(data.total_book_value)}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {data.items && data.items.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Control #</TableHead>
                    <TableHead>Make/Model</TableHead>
                    <TableHead>Status</TableHead>
                    {category === 'rental' && <TableHead>Location</TableHead>}
                    <TableHead className="text-right">Book Value</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.items.slice(0, 10).map((item, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-mono text-sm">
                        {item.control_number}
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{item.make}</div>
                          <div className="text-sm text-muted-foreground">{item.model}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(item.current_status)}
                      </TableCell>
                      {category === 'rental' && (
                        <TableCell>
                          <div>
                            <div className="text-sm">{item.location_state}</div>
                            <div className="text-xs text-muted-foreground truncate max-w-32">
                              {item.customer_name}
                            </div>
                          </div>
                        </TableCell>
                      )}
                      <TableCell className="text-right font-mono">
                        {formatCurrency(item.book_value)}
                      </TableCell>
                    </TableRow>
                  ))}
                  {data.items.length > 10 && (
                    <TableRow>
                      <TableCell colSpan={category === 'rental' ? 5 : 4} className="text-center text-muted-foreground">
                        ... and {data.items.length - 10} more items
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            ) : (
              <p className="text-muted-foreground">No items in this category</p>
            )}
          </CardContent>
        </Card>
      ))}

      {/* Data Quality Notes */}
      {inventoryData.notes && inventoryData.notes.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="text-sm text-yellow-800">Data Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="text-sm text-yellow-700 space-y-1">
              {inventoryData.notes.map((note, index) => (
                <li key={index}>• {note}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default InventoryReport