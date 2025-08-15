import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Search, Download, Package, DollarSign, MapPin } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const PartsInventoryByLocation = () => {
  const [loading, setLoading] = useState(true)
  const [locations, setLocations] = useState([])
  const [details, setDetails] = useState([])
  const [grandTotal, setGrandTotal] = useState(0)
  const [locationFilter, setLocationFilter] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [showDetails, setShowDetails] = useState(false)

  useEffect(() => {
    fetchInventoryData()
  }, [])

  const fetchInventoryData = async (location = '') => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      const url = location 
        ? apiUrl(`/api/reports/departments/parts/inventory-by-location?location=${encodeURIComponent(location)}`)
        : apiUrl('/api/reports/departments/parts/inventory-by-location')
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        const errorData = await response.json()
        console.error('Backend error:', errorData)
        throw new Error(errorData.error || 'Failed to fetch inventory data')
      }

      const data = await response.json()
      setLocations(data.locations || [])
      setDetails(data.details || [])
      setGrandTotal(data.grandTotal || 0)
      setLocationFilter(data.locationFilter || '')
      setShowDetails(!!location && data.details && data.details.length > 0)
    } catch (error) {
      console.error('Error fetching inventory data:', error)
      alert(`Error: ${error.message}\n\nPlease check the console for more details.`)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    fetchInventoryData(searchInput)
  }

  const handleLocationClick = (location) => {
    setSearchInput(location)
    fetchInventoryData(location)
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value)
  }

  const exportToCSV = () => {
    const headers = showDetails 
      ? ['Part Number', 'Description', 'Location', 'Bin Type', 'On Hand', 'Cost', 'Total Value']
      : ['Location', 'Part Count', 'Total Entries', 'Total Value']
    
    const rows = showDetails
      ? details.map(item => [
          item.partNo,
          item.description,
          item.location,
          item.binType,
          item.onHand,
          item.cost.toFixed(2),
          item.totalValue.toFixed(2)
        ])
      : locations.map(loc => [
          loc.location,
          loc.partCount,
          loc.totalEntries,
          loc.totalValue.toFixed(2)
        ])
    
    // Add totals row
    if (!showDetails) {
      rows.push([])
      rows.push(['GRAND TOTAL', '', '', grandTotal.toFixed(2)])
    }
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => {
        const cellStr = String(cell)
        if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
          return `"${cellStr.replace(/"/g, '""')}"`
        }
        return cellStr
      }).join(','))
    ].join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    const today = new Date().toISOString().split('T')[0]
    const filename = showDetails 
      ? `parts_inventory_${locationFilter}_${today}.csv`
      : `parts_inventory_by_location_${today}.csv`
    
    link.setAttribute('href', url)
    link.setAttribute('download', filename)
    link.style.visibility = 'hidden'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <Package className="h-8 w-8 animate-pulse mx-auto mb-2" />
            <p>Loading inventory data...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Search Bar */}
      <Card>
        <CardHeader>
          <CardTitle>Inventory Value by Location</CardTitle>
          <CardDescription>
            Search for parts inventory value by bin location (e.g., "V50", "SHOP", "WHS1", "NEW", etc.)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Enter location (e.g., V50, SHOP, WHS1)"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1 px-3 py-2 border rounded-md"
            />
            <Button onClick={handleSearch}>
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
            <Button 
              variant="outline" 
              onClick={() => {
                setSearchInput('')
                fetchInventoryData('')
              }}
            >
              Show All
            </Button>
            <Button variant="outline" onClick={exportToCSV}>
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Locations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <MapPin className="h-4 w-4 text-muted-foreground mr-2" />
              <span className="text-2xl font-bold">{locations.length}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Inventory Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <DollarSign className="h-4 w-4 text-muted-foreground mr-2" />
              <span className="text-2xl font-bold">{formatCurrency(grandTotal)}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              {locationFilter ? `Filtered: ${locationFilter}` : 'All Locations'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <Package className="h-4 w-4 text-muted-foreground mr-2" />
              <span className="text-2xl font-bold">
                {showDetails ? `${details.length} parts` : `${locations.reduce((sum, loc) => sum + loc.partCount, 0)} unique parts`}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Results Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {showDetails ? `Parts in Location: ${locationFilter}` : 'Inventory by Location'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            {showDetails ? (
              // Detailed parts view for specific location
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Part Number</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Bin Type</TableHead>
                    <TableHead className="text-right">On Hand</TableHead>
                    <TableHead className="text-right">Cost</TableHead>
                    <TableHead className="text-right">Total Value</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {details.map((item, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-medium">{item.partNo}</TableCell>
                      <TableCell>{item.description}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{item.location}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={item.binType === 'Primary' ? 'default' : 'secondary'}>
                          {item.binType}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">{item.onHand}</TableCell>
                      <TableCell className="text-right">{formatCurrency(item.cost)}</TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(item.totalValue)}
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="font-bold bg-muted/50">
                    <TableCell colSpan={6}>Total</TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(details.reduce((sum, item) => sum + item.totalValue, 0))}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            ) : (
              // Summary view of all locations
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Location</TableHead>
                    <TableHead className="text-right">Unique Parts</TableHead>
                    <TableHead className="text-right">Total Entries</TableHead>
                    <TableHead className="text-right">Total Value</TableHead>
                    <TableHead className="text-right">% of Total</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {locations.map((loc, idx) => (
                    <TableRow 
                      key={idx}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleLocationClick(loc.location)}
                    >
                      <TableCell className="font-medium">
                        <Badge variant="outline" className="cursor-pointer">
                          {loc.location}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">{loc.partCount}</TableCell>
                      <TableCell className="text-right">{loc.totalEntries}</TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(loc.totalValue)}
                      </TableCell>
                      <TableCell className="text-right">
                        {grandTotal > 0 ? `${((loc.totalValue / grandTotal) * 100).toFixed(1)}%` : '0%'}
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="font-bold bg-muted/50">
                    <TableCell>GRAND TOTAL</TableCell>
                    <TableCell className="text-right">
                      {locations.reduce((sum, loc) => sum + loc.partCount, 0)}
                    </TableCell>
                    <TableCell className="text-right">
                      {locations.reduce((sum, loc) => sum + loc.totalEntries, 0)}
                    </TableCell>
                    <TableCell className="text-right">{formatCurrency(grandTotal)}</TableCell>
                    <TableCell className="text-right">100%</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            )}
          </div>
          {!showDetails && locations.length > 0 && (
            <p className="text-sm text-muted-foreground mt-4">
              Click on any location to see detailed parts information
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default PartsInventoryByLocation