import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Input } from '@/components/ui/input'
import { 
  Download,
  Search,
  Truck,
  DollarSign,
  Package,
  AlertCircle,
  CheckCircle,
  PauseCircle
} from 'lucide-react'
import { apiUrl } from '@/lib/api'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const RentalEquipmentReport = () => {
  const [equipment, setEquipment] = useState([])
  const [filteredEquipment, setFilteredEquipment] = useState([])
  const [summary, setSummary] = useState({})
  const [makeBreakdown, setMakeBreakdown] = useState([])
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [makeFilter, setMakeFilter] = useState('all')

  useEffect(() => {
    fetchEquipmentData()
  }, [])

  useEffect(() => {
    filterEquipment()
  }, [equipment, searchTerm, statusFilter, makeFilter])

  const fetchEquipmentData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/rental/equipment-report'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setEquipment(data.equipment || [])
        setSummary(data.summary || {})
        setMakeBreakdown(data.make_breakdown || [])
      }
    } catch (error) {
      console.error('Error fetching equipment data:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterEquipment = () => {
    let filtered = [...equipment]

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(item => 
        item.UnitNo?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.SerialNo?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.Make?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.Model?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.CurrentCustomer?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(item => item.CurrentStatus === statusFilter)
    }

    // Make filter
    if (makeFilter !== 'all') {
      filtered = filtered.filter(item => item.Make === makeFilter)
    }

    setFilteredEquipment(filtered)
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount || 0)
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    return new Date(dateString).toLocaleDateString()
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'On Rent':
        return <Truck className="h-4 w-4 text-green-600" />
      case 'Available':
        return <CheckCircle className="h-4 w-4 text-blue-600" />
      case 'On Hold':
        return <PauseCircle className="h-4 w-4 text-orange-600" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />
    }
  }

  const getStatusBadge = (status) => {
    const variants = {
      'On Rent': 'success',
      'Available': 'secondary',
      'On Hold': 'warning',
      'Unknown': 'default'
    }
    return (
      <Badge variant={variants[status] || 'default'}>
        {status}
      </Badge>
    )
  }

  const handleDownload = async () => {
    setDownloading(true)
    try {
      // Convert to CSV
      const headers = [
        'Unit No', 'Serial No', 'Make', 'Model', 'Model Year', 
        'Current Status', 'Rental Status', 'Location', 'Current Customer',
        'Cost', 'List Price', 'Day Rate', 'Week Rate', 'Month Rate',
        'Last Hour Meter', 'Last Hour Meter Date', 'YTD Revenue', 'ITD Revenue',
        'Current Month Days', 'Current Month Revenue'
      ]
      
      const rows = filteredEquipment.map(item => [
        item.UnitNo || '',
        item.SerialNo || '',
        item.Make || '',
        item.Model || '',
        item.ModelYear || '',
        item.CurrentStatus || '',
        item.RentalStatus || '',
        item.Location || '',
        item.CurrentCustomer || '',
        item.Cost || 0,
        item.ListPrice || 0,
        item.DayRent || 0,
        item.WeekRent || 0,
        item.MonthRent || 0,
        item.LastHourMeter || '',
        formatDate(item.LastHourMeterDate),
        item.RentalYTD || 0,
        item.RentalITD || 0,
        item.CurrentMonthDays || 0,
        item.CurrentMonthRevenue || 0
      ])
      
      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
      ].join('\n')
      
      // Download file
      const blob = new Blob([csvContent], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `rental_equipment_${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error downloading equipment data:', error)
    } finally {
      setDownloading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  const uniqueMakes = [...new Set(equipment.map(e => e.Make).filter(Boolean))].sort()

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Fleet Size</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.total_units || 0}</div>
            <p className="text-xs text-muted-foreground">
              Total rental equipment
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Fleet Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary.total_fleet_value)}</div>
            <p className="text-xs text-muted-foreground">
              Total equipment cost
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">YTD Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary.total_ytd_revenue)}</div>
            <p className="text-xs text-muted-foreground">
              Year to date rental revenue
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Month</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary.current_month_revenue)}</div>
            <p className="text-xs text-muted-foreground">
              Current month revenue
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Status Breakdown */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">On Rent</CardTitle>
            <Truck className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.units_on_rent || 0}</div>
            <p className="text-xs text-muted-foreground">
              Currently rented out
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available</CardTitle>
            <CheckCircle className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.available_units || 0}</div>
            <p className="text-xs text-muted-foreground">
              Ready to rent
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">On Hold</CardTitle>
            <PauseCircle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.on_hold_units || 0}</div>
            <p className="text-xs text-muted-foreground">
              Reserved or maintenance
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Equipment Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Rental Equipment Details</CardTitle>
              <CardDescription>All equipment associated with the rental department</CardDescription>
            </div>
            <Button 
              onClick={handleDownload}
              disabled={downloading}
              size="sm"
            >
              <Download className="mr-2 h-4 w-4" />
              {downloading ? 'Downloading...' : 'Download CSV'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="flex gap-4 mb-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by unit, serial, make, model, or customer..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="On Rent">On Rent</SelectItem>
                <SelectItem value="Available">Available</SelectItem>
                <SelectItem value="On Hold">On Hold</SelectItem>
              </SelectContent>
            </Select>
            <Select value={makeFilter} onValueChange={setMakeFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by make" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Makes</SelectItem>
                {uniqueMakes.map(make => (
                  <SelectItem key={make} value={make}>{make}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <p className="text-sm text-muted-foreground mb-4">
            Showing {filteredEquipment.length} of {equipment.length} equipment
          </p>

          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Unit No</TableHead>
                  <TableHead>Serial No</TableHead>
                  <TableHead>Make</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead className="text-right">Day Rate</TableHead>
                  <TableHead className="text-right">Month Rate</TableHead>
                  <TableHead className="text-right">YTD Revenue</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredEquipment.map((item) => (
                  <TableRow key={item.SerialNo}>
                    <TableCell className="font-medium">{item.UnitNo}</TableCell>
                    <TableCell>{item.SerialNo}</TableCell>
                    <TableCell>{item.Make}</TableCell>
                    <TableCell>{item.Model}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(item.CurrentStatus)}
                        {getStatusBadge(item.CurrentStatus)}
                      </div>
                    </TableCell>
                    <TableCell>{item.Location}</TableCell>
                    <TableCell>{item.CurrentCustomer || '-'}</TableCell>
                    <TableCell className="text-right">{formatCurrency(item.DayRent)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(item.MonthRent)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(item.RentalYTD)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Make Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Equipment by Make</CardTitle>
          <CardDescription>Breakdown of rental fleet by manufacturer</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {makeBreakdown.map((make) => (
              <div key={make.Make} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">{make.Make}</span>
                    <span className="text-sm text-muted-foreground">
                      {make.unit_count} units ({make.on_rent_count} on rent)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-purple-600 h-2 rounded-full"
                      style={{ width: `${(make.on_rent_count / make.unit_count) * 100}%` }}
                    />
                  </div>
                </div>
                <div className="ml-4 text-right">
                  <div className="text-sm font-medium">{formatCurrency(make.ytd_revenue)}</div>
                  <div className="text-xs text-muted-foreground">YTD Revenue</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default RentalEquipmentReport