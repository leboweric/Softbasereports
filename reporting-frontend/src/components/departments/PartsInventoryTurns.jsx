import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AlertCircle, Download, Search, Settings, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { apiUrl } from '@/lib/api'
import * as XLSX from 'xlsx'

const PartsInventoryTurns = ({ user }) => {
  const [partsData, setPartsData] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [turnRangeFilter, setTurnRangeFilter] = useState('all')
  const [actionFilter, setActionFilter] = useState('all')
  const [sortField, setSortField] = useState('last_12mo_usage')
  const [sortDirection, setSortDirection] = useState('desc')
  
  // Settings
  const [settings, setSettings] = useState({
    months: 12,
    leadTimeDays: 14,
    serviceLevel: 0.95,
    targetTurns: 5.0,
    minUsage: 5
  })
  const [showSettings, setShowSettings] = useState(false)

  useEffect(() => {
    fetchInventoryData()
  }, [])

  const fetchInventoryData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const queryParams = new URLSearchParams({
        months: settings.months,
        lead_time_days: settings.leadTimeDays,
        service_level: settings.serviceLevel,
        target_turns: settings.targetTurns,
        min_usage: settings.minUsage
      })
      
      const response = await fetch(
        apiUrl(`/api/parts/inventory-turns?${queryParams}`),
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      )
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.success) {
        setPartsData(data.parts || [])
        setSummary(data.summary || {})
      } else {
        throw new Error(data.error || 'Failed to fetch inventory data')
      }
    } catch (err) {
      console.error('Error fetching inventory data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const getActionBadge = (action) => {
    const badgeConfig = {
      'Order now': { variant: 'destructive', icon: TrendingUp },
      'Reduce stock': { variant: 'secondary', icon: TrendingDown },
      'Consider increasing stock': { variant: 'default', icon: TrendingUp },
      'Review usage pattern': { variant: 'outline', icon: AlertCircle },
      'Optimal': { variant: 'default', icon: Minus }
    }
    
    const config = badgeConfig[action] || { variant: 'outline', icon: Minus }
    const Icon = config.icon
    
    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {action}
      </Badge>
    )
  }

  const getTurnsBadge = (currentTurns, targetTurns) => {
    if (currentTurns === 0) return <Badge variant="outline">No Data</Badge>
    
    const ratio = currentTurns / targetTurns
    if (ratio >= 0.8 && ratio <= 1.2) {
      return <Badge variant="default" className="bg-green-100 text-green-800">{currentTurns}</Badge>
    } else if (ratio >= 0.6 && ratio < 0.8 || ratio > 1.2 && ratio <= 1.4) {
      return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">{currentTurns}</Badge>
    } else {
      return <Badge variant="destructive" className="bg-red-100 text-red-800">{currentTurns}</Badge>
    }
  }

  const filteredAndSortedParts = partsData
    .filter(part => {
      // Search filter
      if (searchTerm && !part.part_number.toLowerCase().includes(searchTerm.toLowerCase()) && 
          !part.description.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false
      }
      
      // Turn range filter
      if (turnRangeFilter !== 'all') {
        const turns = part.current_turns
        switch (turnRangeFilter) {
          case 'low': return turns > 0 && turns < 3
          case 'optimal': return turns >= 3 && turns <= 7
          case 'high': return turns > 7
          case 'zero': return turns === 0
          default: break
        }
      }
      
      // Action filter
      if (actionFilter !== 'all' && part.recommended_action !== actionFilter) {
        return false
      }
      
      return true
    })
    .sort((a, b) => {
      const aVal = a[sortField]
      const bVal = b[sortField]
      
      if (typeof aVal === 'string') {
        return sortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
      }
      
      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal
    })

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const handleSettingsUpdate = () => {
    setShowSettings(false)
    fetchInventoryData()
  }

  const exportToExcel = () => {
    const exportData = filteredAndSortedParts.map(part => ({
      'Part Number': part.part_number,
      'Description': part.description,
      'Current Stock': part.current_stock,
      'Last 12 Month Usage': part.last_12mo_usage,
      'Avg Monthly Usage': part.avg_monthly_usage,
      'Current Turns': part.current_turns,
      'Target Turns': part.target_turns,
      'Reorder Point (Min)': part.reorder_point_min,
      'Max Level': part.max_level,
      'Optimal Order Qty': part.optimal_order_qty,
      'Cost Per Unit': part.cost_per_unit,
      'Annual Value': part.annual_value,
      'Recommended Action': part.recommended_action,
      'Safety Stock': part.safety_stock
    }))

    const ws = XLSX.utils.json_to_sheet(exportData)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Parts Inventory Analysis')
    
    // Auto-size columns
    const colWidths = Object.keys(exportData[0] || {}).map(key => ({ wch: Math.max(key.length, 15) }))
    ws['!cols'] = colWidths
    
    XLSX.writeFile(wb, `parts-inventory-turns-${new Date().toISOString().split('T')[0]}.xlsx`)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error Loading Data</h3>
              <p className="mt-2 text-sm text-red-700">{error}</p>
              <Button 
                onClick={fetchInventoryData} 
                variant="outline" 
                size="sm" 
                className="mt-2"
              >
                Retry
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Parts Inventory Turns Analysis</h1>
          <p className="text-gray-600">5-Turn Matrix for Optimal Inventory Management</p>
        </div>
        <div className="flex space-x-2">
          <Button 
            variant="outline" 
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center gap-2"
          >
            <Settings className="h-4 w-4" />
            Settings
          </Button>
          <Button 
            onClick={exportToExcel}
            className="flex items-center gap-2"
            disabled={filteredAndSortedParts.length === 0}
          >
            <Download className="h-4 w-4" />
            Export Excel
          </Button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <Card>
          <CardHeader>
            <CardTitle>Analysis Settings</CardTitle>
            <CardDescription>Adjust parameters for inventory turn calculations</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div>
              <Label htmlFor="months">Analysis Period (Months)</Label>
              <Input
                id="months"
                type="number"
                value={settings.months}
                onChange={(e) => setSettings(prev => ({ ...prev, months: parseInt(e.target.value) }))}
                min="1"
                max="24"
              />
            </div>
            <div>
              <Label htmlFor="leadTime">Lead Time (Days)</Label>
              <Input
                id="leadTime"
                type="number"
                value={settings.leadTimeDays}
                onChange={(e) => setSettings(prev => ({ ...prev, leadTimeDays: parseInt(e.target.value) }))}
                min="1"
                max="90"
              />
            </div>
            <div>
              <Label htmlFor="serviceLevel">Service Level</Label>
              <Select 
                value={settings.serviceLevel.toString()} 
                onValueChange={(value) => setSettings(prev => ({ ...prev, serviceLevel: parseFloat(value) }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="0.90">90%</SelectItem>
                  <SelectItem value="0.95">95%</SelectItem>
                  <SelectItem value="0.99">99%</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="targetTurns">Target Turns</Label>
              <Input
                id="targetTurns"
                type="number"
                step="0.1"
                value={settings.targetTurns}
                onChange={(e) => setSettings(prev => ({ ...prev, targetTurns: parseFloat(e.target.value) }))}
                min="1"
                max="20"
              />
            </div>
            <div className="flex items-end">
              <Button onClick={handleSettingsUpdate} className="w-full">
                Update Analysis
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div>
                  <p className="text-sm font-medium text-gray-600">Parts Analyzed</p>
                  <p className="text-2xl font-bold">{summary.total_parts_analyzed}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div>
                  <p className="text-sm font-medium text-gray-600">Current Avg Turns</p>
                  <p className="text-2xl font-bold">{summary.avg_turns_current}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div>
                  <p className="text-sm font-medium text-gray-600">Target Turns</p>
                  <p className="text-2xl font-bold">{summary.target_turns}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div>
                  <p className="text-sm font-medium text-gray-600">Potential Savings</p>
                  <p className="text-2xl font-bold text-green-600">
                    ${summary.potential_savings?.toLocaleString() || '0'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search part number or description..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div>
              <Select value={turnRangeFilter} onValueChange={setTurnRangeFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Turn Range" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Turns</SelectItem>
                  <SelectItem value="zero">No Turns (0)</SelectItem>
                  <SelectItem value="low">Low (&lt; 3)</SelectItem>
                  <SelectItem value="optimal">Optimal (3-7)</SelectItem>
                  <SelectItem value="high">High (&gt; 7)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Select value={actionFilter} onValueChange={setActionFilter}>
                <SelectTrigger className="w-[160px]">
                  <SelectValue placeholder="Action" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Actions</SelectItem>
                  <SelectItem value="Order now">Order Now</SelectItem>
                  <SelectItem value="Reduce stock">Reduce Stock</SelectItem>
                  <SelectItem value="Optimal">Optimal</SelectItem>
                  <SelectItem value="Review usage pattern">Review Usage</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data Table */}
      <Card>
        <CardHeader>
          <CardTitle>Parts Inventory Analysis ({filteredAndSortedParts.length} parts)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('part_number')}
                  >
                    Part Number
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('description')}
                  >
                    Description
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-50 text-right"
                    onClick={() => handleSort('current_stock')}
                  >
                    Current Stock
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-50 text-right"
                    onClick={() => handleSort('last_12mo_usage')}
                  >
                    12Mo Usage
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-50 text-right"
                    onClick={() => handleSort('current_turns')}
                  >
                    Current Turns
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-50 text-right"
                    onClick={() => handleSort('reorder_point_min')}
                  >
                    Min Level
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-50 text-right"
                    onClick={() => handleSort('max_level')}
                  >
                    Max Level
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-50 text-right"
                    onClick={() => handleSort('optimal_order_qty')}
                  >
                    Order Qty
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('recommended_action')}
                  >
                    Action
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer hover:bg-gray-50 text-right"
                    onClick={() => handleSort('annual_value')}
                  >
                    Annual Value
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAndSortedParts.map((part, index) => (
                  <TableRow key={index} className="hover:bg-gray-50">
                    <TableCell className="font-medium">{part.part_number}</TableCell>
                    <TableCell className="max-w-[200px] truncate" title={part.description}>
                      {part.description}
                    </TableCell>
                    <TableCell className="text-right">{part.current_stock}</TableCell>
                    <TableCell className="text-right">{part.last_12mo_usage}</TableCell>
                    <TableCell className="text-right">
                      {getTurnsBadge(part.current_turns, part.target_turns)}
                    </TableCell>
                    <TableCell className="text-right">{part.reorder_point_min}</TableCell>
                    <TableCell className="text-right">{part.max_level}</TableCell>
                    <TableCell className="text-right">{part.optimal_order_qty}</TableCell>
                    <TableCell>{getActionBadge(part.recommended_action)}</TableCell>
                    <TableCell className="text-right">
                      ${part.annual_value?.toLocaleString() || '0'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          
          {filteredAndSortedParts.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No parts found matching the current filters.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default PartsInventoryTurns