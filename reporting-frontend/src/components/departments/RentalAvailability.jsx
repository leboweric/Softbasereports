import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Truck, 
  CheckCircle, 
  XCircle, 
  Download,
  Search,
  RefreshCw,
  AlertCircle,
  ChevronUp,
  ChevronDown
} from 'lucide-react'
import { apiUrl } from '@/lib/api'
import RentalAvailabilityDebug from './RentalAvailabilityDebug'

const RentalAvailability = () => {
  const [showDebug, setShowDebug] = useState(false)
  const [loading, setLoading] = useState(true)
  const [equipment, setEquipment] = useState([])
  const [summary, setSummary] = useState({})
  const [filterStatus, setFilterStatus] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [sortColumn, setSortColumn] = useState(null)
  const [sortDirection, setSortDirection] = useState('asc')

  useEffect(() => {
    fetchAvailabilityData()
  }, [])

  const fetchAvailabilityData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl('/api/reports/departments/rental/availability'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch availability data')
      }

      const data = await response.json()
      // Sort equipment: Available first, then On Rent, then others
      const sortedEquipment = (data.equipment || []).sort((a, b) => {
        // Define sort order
        const statusOrder = {
          'Available': 1,
          'On Rent': 2
        }
        const aOrder = statusOrder[a.status] || 99
        const bOrder = statusOrder[b.status] || 99
        
        // Sort by status order first
        if (aOrder !== bOrder) {
          return aOrder - bOrder
        }
        // Then by unit number
        return (a.unitNo || '').localeCompare(b.unitNo || '')
      })
      setEquipment(sortedEquipment)
      setSummary(data.summary || {})
    } catch (error) {
      console.error('Error fetching availability data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column)
      setSortDirection('asc')
    }
  }

  const getStatusBadge = (status) => {
    switch(status) {
      case 'Available':
        return <Badge className="bg-green-100 text-green-800 border-green-200">Available</Badge>
      case 'On Rent':
        return <Badge className="bg-blue-100 text-blue-800 border-blue-200">On Rent</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const filteredAndSortedEquipment = equipment
    .filter(item => {
      const matchesStatus = filterStatus === 'all' || item.status === filterStatus
      const matchesSearch = searchTerm === '' || 
        (item.make && item.make.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (item.model && item.model.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (item.unitNo && item.unitNo.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (item.serialNo && item.serialNo.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (item.billTo && item.billTo.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (item.shipAddress && item.shipAddress.toLowerCase().includes(searchTerm.toLowerCase()))
      
      return matchesStatus && matchesSearch
    })
    .sort((a, b) => {
      if (!sortColumn) return 0
      
      let aValue = ''
      let bValue = ''
      
      switch(sortColumn) {
        case 'make':
          aValue = a.make || ''
          bValue = b.make || ''
          break
        case 'model':
          aValue = a.model || ''
          bValue = b.model || ''
          break
        case 'unitNo':
          aValue = a.unitNo || ''
          bValue = b.unitNo || ''
          break
        case 'serialNo':
          aValue = a.serialNo || ''
          bValue = b.serialNo || ''
          break
        case 'status':
          aValue = a.status || ''
          bValue = b.status || ''
          break
        case 'shipAddress':
          aValue = a.shipAddress || ''
          bValue = b.shipAddress || ''
          break
        default:
          return 0
      }
      
      if (sortDirection === 'asc') {
        return aValue.localeCompare(bValue)
      } else {
        return bValue.localeCompare(aValue)
      }
    })

  const exportToCSV = () => {
    const headers = ['Make', 'Model', 'Unit Number', 'Serial Number', 'Status', 'Ship To / Customer']
    
    const rows = filteredAndSortedEquipment.map(item => [
      item.make || '',
      item.model || '',
      item.unitNo || '',
      item.serialNo || '',
      item.status || '',
      item.shipAddress || ''
    ])
    
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
    link.setAttribute('href', url)
    link.setAttribute('download', `rental_availability_${today}.csv`)
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
            <Truck className="h-8 w-8 animate-pulse mx-auto mb-2" />
            <p>Loading availability data...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Debug Toggle - Temporary */}
      {equipment.length === 0 && !loading && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <AlertCircle className="h-5 w-5 text-yellow-600 mr-2" />
                <span className="text-sm">No equipment data found. Run diagnostics to troubleshoot.</span>
              </div>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setShowDebug(!showDebug)}
              >
                {showDebug ? 'Hide' : 'Show'} Diagnostics
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Debug Component */}
      {showDebug && <RentalAvailabilityDebug />}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Fleet</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.totalUnits || 0}</div>
            <p className="text-xs text-muted-foreground">Units</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Available</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
              <span className="text-2xl font-bold text-green-600">{summary.availableUnits || 0}</span>
            </div>
            <p className="text-xs text-muted-foreground">Ready to rent</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">On Rent</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <Truck className="h-4 w-4 text-blue-600 mr-2" />
              <span className="text-2xl font-bold text-blue-600">{summary.onRentUnits || 0}</span>
            </div>
            <p className="text-xs text-muted-foreground">Currently rented</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Utilization Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.utilizationRate || 0}%</div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
              <div 
                className="bg-blue-600 h-2 rounded-full" 
                style={{ width: `${summary.utilizationRate || 0}%` }}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Actions */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>Rental Equipment Availability</CardTitle>
              <CardDescription>
                Current status of all rental equipment with customer information
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={fetchAvailabilityData}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              <Button variant="outline" onClick={exportToCSV}>
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filter Controls */}
          <div className="flex gap-4 mb-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search by make, model, unit #, serial #, or customer..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
              />
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border rounded-md"
            >
              <option value="all">All Status</option>
              <option value="Available">Available</option>
              <option value="On Rent">On Rent</option>
            </select>
          </div>

          {/* Equipment Table */}
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-100 transition-colors select-none"
                    onClick={() => handleSort('make')}
                  >
                    <div className="flex items-center gap-1 group">
                      <span className="group-hover:text-blue-600">Make</span>
                      {sortColumn === 'make' ? (
                        sortDirection === 'asc' ? 
                        <ChevronUp className="h-4 w-4 text-blue-600" /> : 
                        <ChevronDown className="h-4 w-4 text-blue-600" />
                      ) : (
                        <div className="flex flex-col opacity-40 group-hover:opacity-100">
                          <ChevronUp className="h-3 w-3 -mb-1" />
                          <ChevronDown className="h-3 w-3" />
                        </div>
                      )}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-100 transition-colors select-none"
                    onClick={() => handleSort('model')}
                  >
                    <div className="flex items-center gap-1 group">
                      <span className="group-hover:text-blue-600">Model</span>
                      {sortColumn === 'model' ? (
                        sortDirection === 'asc' ? 
                        <ChevronUp className="h-4 w-4 text-blue-600" /> : 
                        <ChevronDown className="h-4 w-4 text-blue-600" />
                      ) : (
                        <div className="flex flex-col opacity-40 group-hover:opacity-100">
                          <ChevronUp className="h-3 w-3 -mb-1" />
                          <ChevronDown className="h-3 w-3" />
                        </div>
                      )}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-100 transition-colors select-none"
                    onClick={() => handleSort('unitNo')}
                  >
                    <div className="flex items-center gap-1 group">
                      <span className="group-hover:text-blue-600">Unit Number</span>
                      {sortColumn === 'unitNo' ? (
                        sortDirection === 'asc' ? 
                        <ChevronUp className="h-4 w-4 text-blue-600" /> : 
                        <ChevronDown className="h-4 w-4 text-blue-600" />
                      ) : (
                        <div className="flex flex-col opacity-40 group-hover:opacity-100">
                          <ChevronUp className="h-3 w-3 -mb-1" />
                          <ChevronDown className="h-3 w-3" />
                        </div>
                      )}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-100 transition-colors select-none"
                    onClick={() => handleSort('serialNo')}
                  >
                    <div className="flex items-center gap-1 group">
                      <span className="group-hover:text-blue-600">Serial Number</span>
                      {sortColumn === 'serialNo' ? (
                        sortDirection === 'asc' ? 
                        <ChevronUp className="h-4 w-4 text-blue-600" /> : 
                        <ChevronDown className="h-4 w-4 text-blue-600" />
                      ) : (
                        <div className="flex flex-col opacity-40 group-hover:opacity-100">
                          <ChevronUp className="h-3 w-3 -mb-1" />
                          <ChevronDown className="h-3 w-3" />
                        </div>
                      )}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-100 transition-colors select-none"
                    onClick={() => handleSort('status')}
                  >
                    <div className="flex items-center gap-1 group">
                      <span className="group-hover:text-blue-600">Status</span>
                      {sortColumn === 'status' ? (
                        sortDirection === 'asc' ? 
                        <ChevronUp className="h-4 w-4 text-blue-600" /> : 
                        <ChevronDown className="h-4 w-4 text-blue-600" />
                      ) : (
                        <div className="flex flex-col opacity-40 group-hover:opacity-100">
                          <ChevronUp className="h-3 w-3 -mb-1" />
                          <ChevronDown className="h-3 w-3" />
                        </div>
                      )}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-100 transition-colors select-none"
                    onClick={() => handleSort('shipAddress')}
                  >
                    <div className="flex items-center gap-1 group">
                      <span className="group-hover:text-blue-600">Ship To / Customer</span>
                      {sortColumn === 'shipAddress' ? (
                        sortDirection === 'asc' ? 
                        <ChevronUp className="h-4 w-4 text-blue-600" /> : 
                        <ChevronDown className="h-4 w-4 text-blue-600" />
                      ) : (
                        <div className="flex flex-col opacity-40 group-hover:opacity-100">
                          <ChevronUp className="h-3 w-3 -mb-1" />
                          <ChevronDown className="h-3 w-3" />
                        </div>
                      )}
                    </div>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAndSortedEquipment.map((item, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="font-medium">{item.make || ''}</TableCell>
                    <TableCell>{item.model || ''}</TableCell>
                    <TableCell>{item.unitNo || ''}</TableCell>
                    <TableCell>{item.serialNo || ''}</TableCell>
                    <TableCell>{getStatusBadge(item.status)}</TableCell>
                    <TableCell>{item.shipAddress || '-'}</TableCell>
                  </TableRow>
                ))}
                {filteredAndSortedEquipment.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      No equipment found matching your filters
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
          
          {/* Results Summary */}
          <div className="mt-4 text-sm text-muted-foreground">
            Showing {filteredAndSortedEquipment.length} of {equipment.length} units
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default RentalAvailability