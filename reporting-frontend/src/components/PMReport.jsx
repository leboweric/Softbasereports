import React, { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, Calendar, Download, User, Wrench } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { apiUrl } from '@/lib/api'
import * as XLSX from 'xlsx'

const PMReport = ({ user }) => {
  const [pmData, setPmData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [sortConfig, setSortConfig] = useState({ key: 'schedule_date', direction: 'asc' })

  useEffect(() => {
    fetchPMData()
  }, [])

  const fetchPMData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/service/pms-due?status=all&days_ahead=90'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setPmData(data)
      } else {
        console.error('Failed to fetch PM data:', response.status)
      }
    } catch (error) {
      console.error('Error fetching PM data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSort = (key) => {
    let direction = 'asc'
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc'
    }
    setSortConfig({ key, direction })
  }

  const sortedPMs = useMemo(() => {
    if (!pmData?.pms) return []
    
    const sorted = [...pmData.pms].sort((a, b) => {
      let aValue = a[sortConfig.key]
      let bValue = b[sortConfig.key]
      
      // Handle null/undefined values
      if (aValue === null || aValue === undefined) aValue = ''
      if (bValue === null || bValue === undefined) bValue = ''
      
      // Convert to lowercase for string comparison
      if (typeof aValue === 'string') aValue = aValue.toLowerCase()
      if (typeof bValue === 'string') bValue = bValue.toLowerCase()
      
      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1
      }
      return 0
    })
    
    return sorted
  }, [pmData, sortConfig])

  const exportToExcel = () => {
    if (!sortedPMs || sortedPMs.length === 0) {
      alert('No data to export')
      return
    }

    // Prepare data for export
    const exportData = sortedPMs.map(pm => ({
      'WO Number': pm.wo_number,
      'Customer': pm.customer_name,
      'Customer Phone': pm.customer_phone || '',
      'Equipment Unit': pm.equipment_unit || '',
      'Make': pm.equipment_make || '',
      'Model': pm.equipment_model || '',
      'Serial Number': pm.equipment_serial || '',
      'Technician': pm.technician,
      'Service Type': pm.service_type || '',
      'Due Date': pm.schedule_date,
      'Days Until Due': pm.days_until_due,
      'Status': pm.status,
      'Comments': pm.comments || ''
    }))

    // Create workbook and worksheet
    const wb = XLSX.utils.book_new()
    const ws = XLSX.utils.json_to_sheet(exportData)

    // Set column widths
    ws['!cols'] = [
      { wch: 12 },  // WO Number
      { wch: 25 },  // Customer
      { wch: 15 },  // Phone
      { wch: 15 },  // Equipment Unit
      { wch: 12 },  // Make
      { wch: 15 },  // Model
      { wch: 18 },  // Serial
      { wch: 15 },  // Technician
      { wch: 20 },  // Service Type
      { wch: 12 },  // Due Date
      { wch: 12 },  // Days Until Due
      { wch: 12 },  // Status
      { wch: 40 }   // Comments
    ]

    XLSX.utils.book_append_sheet(wb, ws, 'PMs Due')

    // Generate filename with current date
    const filename = `PMs_Due_${new Date().toISOString().split('T')[0]}.xlsx`
    
    // Save file
    XLSX.writeFile(wb, filename)
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      'Overdue': { variant: 'destructive', icon: AlertTriangle },
      'Due Soon': { variant: 'warning', icon: Calendar },
      'Scheduled': { variant: 'secondary', icon: Calendar },
      'Completed': { variant: 'success', icon: Calendar }
    }
    
    const config = statusConfig[status] || { variant: 'secondary', icon: Calendar }
    const Icon = config.icon
    
    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {status}
      </Badge>
    )
  }

  const SortableHeader = ({ label, sortKey }) => (
    <TableHead 
      className="cursor-pointer hover:bg-muted/50 select-none"
      onClick={() => handleSort(sortKey)}
    >
      <div className="flex items-center gap-1">
        {label}
        {sortConfig.key === sortKey && (
          <span className="text-xs">
            {sortConfig.direction === 'asc' ? '↑' : '↓'}
          </span>
        )}
      </div>
    </TableHead>
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  if (!pmData) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground">Failed to load PM data</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total PMs</CardTitle>
            <Wrench className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pmData.summary.total}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overdue</CardTitle>
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">{pmData.summary.overdue}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Due Soon</CardTitle>
            <Calendar className="h-4 w-4 text-warning" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-warning">{pmData.summary.due_soon}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduled</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pmData.summary.scheduled}</div>
          </CardContent>
        </Card>
      </div>

      {/* PM List Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Planned Maintenance Due</CardTitle>
              <CardDescription>
                Click column headers to sort. Showing PMs due within the next 90 days.
              </CardDescription>
            </div>
            <Button onClick={exportToExcel} variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export to Excel
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {sortedPMs.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No PMs due</p>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <SortableHeader label="WO #" sortKey="wo_number" />
                    <SortableHeader label="Customer" sortKey="customer_name" />
                    <SortableHeader label="Equipment" sortKey="equipment_unit" />
                    <TableHead>Make/Model</TableHead>
                    <SortableHeader label="Technician" sortKey="technician" />
                    <SortableHeader label="Due Date" sortKey="schedule_date" />
                    <SortableHeader label="Days" sortKey="days_until_due" />
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedPMs.map((pm) => (
                    <TableRow key={pm.wo_number}>
                      <TableCell className="font-medium">{pm.wo_number}</TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{pm.customer_name}</span>
                          {pm.customer_phone && (
                            <span className="text-xs text-muted-foreground">{pm.customer_phone}</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{pm.equipment_unit || 'N/A'}</span>
                          {pm.equipment_serial && (
                            <span className="text-xs text-muted-foreground">S/N: {pm.equipment_serial}</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {pm.equipment_make && pm.equipment_model ? (
                            <>
                              <div>{pm.equipment_make}</div>
                              <div className="text-muted-foreground">{pm.equipment_model}</div>
                            </>
                          ) : (
                            'N/A'
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <User className="h-3 w-3 text-muted-foreground" />
                          {pm.technician}
                        </div>
                      </TableCell>
                      <TableCell>{pm.schedule_date}</TableCell>
                      <TableCell>
                        <span className={pm.days_until_due < 0 ? 'text-destructive font-semibold' : ''}>
                          {pm.days_until_due < 0 ? Math.abs(pm.days_until_due) + ' days ago' : pm.days_until_due + ' days'}
                        </span>
                      </TableCell>
                      <TableCell>{getStatusBadge(pm.status)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default PMReport
