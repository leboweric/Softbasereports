import React, { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, Calendar, ChevronDown, ChevronUp, Clock, Download, User, Wrench } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { apiUrl } from '@/lib/api'
import * as XLSX from 'xlsx'

const PMReport = ({ user }) => {
  const [pmData, setPmData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [sortConfig, setSortConfig] = useState({ key: 'next_pm_date', direction: 'asc' })
  const [selectedTechnician, setSelectedTechnician] = useState('all')
  
  // Collapse state for each section
  const [isOverdueOpen, setIsOverdueOpen] = useState(true)
  const [isDueSoonOpen, setIsDueSoonOpen] = useState(true)
  const [isScheduledOpen, setIsScheduledOpen] = useState(false)
  const [isNotScheduledOpen, setIsNotScheduledOpen] = useState(false)

  useEffect(() => {
    fetchPMData()
  }, [])

  const fetchPMData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/service/pms-due'), {
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

  const handleSort = (key, pms) => {
    let direction = 'asc'
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc'
    }
    setSortConfig({ key, direction })
    
    return [...pms].sort((a, b) => {
      let aValue = a[key]
      let bValue = b[key]
      
      if (aValue === null || aValue === undefined) aValue = ''
      if (bValue === null || bValue === undefined) bValue = ''
      
      if (typeof aValue === 'string') aValue = aValue.toLowerCase()
      if (typeof bValue === 'string') bValue = bValue.toLowerCase()
      
      if (aValue < bValue) {
        return direction === 'asc' ? -1 : 1
      }
      if (aValue > bValue) {
        return direction === 'asc' ? 1 : -1
      }
      return 0
    })
  }

  // Get unique technicians for filter dropdown
  const technicians = useMemo(() => {
    if (!pmData?.pms) return []
    const uniqueTechs = [...new Set(pmData.pms.map(pm => pm.technician).filter(Boolean))]
    return uniqueTechs.sort()
  }, [pmData])

  // Filter PMs by selected technician
  const filteredPMs = useMemo(() => {
    if (!pmData?.pms) return []
    if (selectedTechnician === 'all') return pmData.pms
    return pmData.pms.filter(pm => pm.technician === selectedTechnician)
  }, [pmData, selectedTechnician])

  // Group PMs by status (after technician filter) and sort alphabetically by customer name
  const groupedPMs = useMemo(() => {
    if (!filteredPMs || filteredPMs.length === 0) {
      return { overdue: [], dueSoon: [], scheduled: [], notScheduled: [] }
    }
    
    const sortByCustomer = (pms) => {
      return [...pms].sort((a, b) => {
        const nameA = (a.customer_name || '').toLowerCase()
        const nameB = (b.customer_name || '').toLowerCase()
        return nameA.localeCompare(nameB)
      })
    }
    
    return {
      overdue: sortByCustomer(filteredPMs.filter(pm => pm.status === 'Overdue')),
      dueSoon: sortByCustomer(filteredPMs.filter(pm => pm.status === 'Due Soon')),
      scheduled: sortByCustomer(filteredPMs.filter(pm => pm.status === 'Scheduled')),
      notScheduled: sortByCustomer(filteredPMs.filter(pm => pm.status === 'Not Scheduled'))
    }
  }, [filteredPMs])

  const exportToExcel = (pms, filename) => {
    if (!pms || pms.length === 0) {
      alert('No data to export')
      return
    }

    // Sort PMs alphabetically by customer name before exporting
    const sortedPMs = [...pms].sort((a, b) => {
      const nameA = (a.customer_name || '').toLowerCase()
      const nameB = (b.customer_name || '').toLowerCase()
      return nameA.localeCompare(nameB)
    })

    const exportData = sortedPMs.map(pm => {
      const daysPastDue = pm.days_until_due !== null && pm.days_until_due < 0 ? Math.abs(pm.days_until_due) : 0
      const isOverdue = daysPastDue > 0
      
      return {
        'Customer': pm.customer_name || '',
        'Bill To Address': pm.customer_address || '',
        'Contact': pm.customer_contact || '',
        'Phone': pm.customer_phone || '',
        'City': pm.customer_city || '',
        'Due Date': pm.next_pm_date ? new Date(pm.next_pm_date).toLocaleDateString() : '',
        'Days Past Due': isOverdue ? daysPastDue : '',
        'Overdue': isOverdue ? 'Yes' : 'No',
        'Unit Number': pm.unit_no || '',
        'Model': pm.model || '',
        'Serial Number': pm.serial_no || '',
        'Technician': pm.technician || ''
      }
    })

    const wb = XLSX.utils.book_new()
    const ws = XLSX.utils.json_to_sheet(exportData)

    // Make header row bold
    const range = XLSX.utils.decode_range(ws['!ref'])
    for (let col = range.s.c; col <= range.e.c; col++) {
      const cellAddress = XLSX.utils.encode_cell({ r: 0, c: col })
      if (!ws[cellAddress]) continue
      ws[cellAddress].s = {
        font: { bold: true }
      }
    }

    // Auto-size columns based on content
    const maxWidths = {}
    const headers = Object.keys(exportData[0] || {})
    
    // Initialize with header lengths
    headers.forEach(header => {
      maxWidths[header] = header.length
    })
    
    // Find max width for each column
    exportData.forEach(row => {
      headers.forEach(header => {
        const cellValue = String(row[header] || '')
        maxWidths[header] = Math.max(maxWidths[header], cellValue.length)
      })
    })
    
    // Set column widths with some padding and max limits
    ws['!cols'] = headers.map(header => ({
      wch: Math.min(Math.max(maxWidths[header] + 2, 10), 50)
    }))

    XLSX.utils.book_append_sheet(wb, ws, 'PMs')
    XLSX.writeFile(wb, filename)
  }

  const exportAllToExcel = () => {
    if (!filteredPMs || filteredPMs.length === 0) {
      alert('No data to export')
      return
    }
    const techName = selectedTechnician === 'all' ? 'All_Techs' : selectedTechnician.replace(/\s+/g, '_')
    exportToExcel(filteredPMs, `PM_Report_${techName}_${new Date().toISOString().split('T')[0]}.xlsx`)
  }

  const getStatusBadge = (status, count) => {
    const statusConfig = {
      'Overdue': { variant: 'destructive', icon: AlertTriangle },
      'Due Soon': { variant: 'warning', icon: Clock },
      'Scheduled': { variant: 'secondary', icon: Calendar },
      'Not Scheduled': { variant: 'outline', icon: Calendar }
    }
    
    const config = statusConfig[status] || { variant: 'secondary', icon: Calendar }
    const Icon = config.icon
    
    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {status} ({count})
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

  const PMTable = ({ pms }) => {
    if (pms.length === 0) {
      return <p className="text-muted-foreground text-center py-4">No PMs in this category</p>
    }

    return (
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <SortableHeader label="Customer" sortKey="customer_name" />
              <TableHead>Bill To Address</TableHead>
              <TableHead>Contact</TableHead>
              <TableHead>Phone</TableHead>
              <SortableHeader label="City" sortKey="customer_city" />
              <SortableHeader label="Due Date" sortKey="next_pm_date" />
              <TableHead>Days Past Due</TableHead>
              <TableHead>Overdue</TableHead>
              <TableHead>Unit Number</TableHead>
              <TableHead>Model</TableHead>
              <TableHead>Serial Number</TableHead>
              <SortableHeader label="Technician" sortKey="technician" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {pms.map((pm) => {
              const daysPastDue = pm.days_until_due !== null && pm.days_until_due < 0 ? Math.abs(pm.days_until_due) : 0
              const isOverdue = daysPastDue > 0
              
              return (
                <TableRow key={pm.id}>
                  {/* 1. Customer */}
                  <TableCell className="font-medium">{pm.customer_name}</TableCell>
                  
                  {/* 2. Bill To Address */}
                  <TableCell className="text-sm">{pm.customer_address || 'N/A'}</TableCell>
                  
                  {/* 3. Contact */}
                  <TableCell className="text-sm">{pm.customer_contact || 'N/A'}</TableCell>
                  
                  {/* 4. Phone */}
                  <TableCell className="text-sm">{pm.customer_phone || 'N/A'}</TableCell>
                  
                  {/* 5. City */}
                  <TableCell>
                    <div className="flex flex-col">
                      <span>{pm.customer_city || 'N/A'}</span>
                      {pm.customer_state && (
                        <span className="text-xs text-muted-foreground">{pm.customer_state}</span>
                      )}
                    </div>
                  </TableCell>
                  
                  {/* 6. Due Date */}
                  <TableCell>
                    {pm.next_pm_date ? new Date(pm.next_pm_date).toLocaleDateString() : 'Not scheduled'}
                  </TableCell>
                  
                  {/* 7. Days Past Due */}
                  <TableCell className="text-center">
                    {isOverdue ? (
                      <span className="text-destructive font-medium">{daysPastDue}</span>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  
                  {/* 8. Overdue */}
                  <TableCell className="text-center">
                    {isOverdue ? (
                      <Badge variant="destructive" className="text-xs">Yes</Badge>
                    ) : (
                      <span className="text-muted-foreground text-sm">No</span>
                    )}
                  </TableCell>
                  
                  {/* 9. Unit Number */}
                  <TableCell className="text-sm">{pm.unit_no || 'N/A'}</TableCell>
                  
                  {/* 10. Model */}
                  <TableCell className="text-sm">{pm.model || 'N/A'}</TableCell>
                  
                  {/* 11. Serial Number */}
                  <TableCell className="font-mono text-xs">{pm.serial_no}</TableCell>
                  
                  {/* 12. Technician */}
                  <TableCell className="text-sm">{pm.technician || 'Unassigned'}</TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>
    )
  }

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
      {/* Technician Filter and Export */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex-1">
              <CardTitle>PM Report by Technician</CardTitle>
              <CardDescription>
                Filter PMs by technician and download individual tech reports
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Select value={selectedTechnician} onValueChange={setSelectedTechnician}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Select technician" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Technicians</SelectItem>
                  {technicians.map(tech => (
                    <SelectItem key={tech} value={tech}>{tech}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button onClick={exportAllToExcel} variant="outline">
                <Download className="mr-2 h-4 w-4" />
                Export {selectedTechnician === 'all' ? 'All' : selectedTechnician}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total PMs</CardTitle>
            <Wrench className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{filteredPMs.length}</div>
            {selectedTechnician !== 'all' && (
              <p className="text-xs text-muted-foreground mt-1">of {pmData.summary.total} total</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overdue</CardTitle>
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">{groupedPMs.overdue.length}</div>
            {selectedTechnician !== 'all' && (
              <p className="text-xs text-muted-foreground mt-1">of {pmData.summary.overdue} total</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Due Soon</CardTitle>
            <Clock className="h-4 w-4 text-warning" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-warning">{groupedPMs.dueSoon.length}</div>
            {selectedTechnician !== 'all' && (
              <p className="text-xs text-muted-foreground mt-1">of {pmData.summary.due_soon} total</p>
            )}
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

      {/* Export All Button */}
      <div className="flex justify-end">
        <Button onClick={exportAllToExcel} variant="outline" size="sm">
          <Download className="h-4 w-4 mr-2" />
          Export All to Excel
        </Button>
      </div>

      {/* Overdue PMs - Always Expanded */}
      <Collapsible open={isOverdueOpen} onOpenChange={setIsOverdueOpen}>
        <Card className="border-destructive">
          <CardHeader>
            <CollapsibleTrigger className="flex items-center justify-between w-full hover:opacity-80">
              <div className="flex items-center gap-3">
                {getStatusBadge('Overdue', groupedPMs.overdue.length)}
                <CardTitle className="text-destructive">Overdue PMs - Immediate Attention Required</CardTitle>
              </div>
              {isOverdueOpen ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
            </CollapsibleTrigger>
          </CardHeader>
          <CollapsibleContent>
            <CardContent>
              <PMTable pms={groupedPMs.overdue} />
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>

      {/* Due Soon PMs - Expanded by Default */}
      <Collapsible open={isDueSoonOpen} onOpenChange={setIsDueSoonOpen}>
        <Card className="border-warning">
          <CardHeader>
            <CollapsibleTrigger className="flex items-center justify-between w-full hover:opacity-80">
              <div className="flex items-center gap-3">
                {getStatusBadge('Due Soon', groupedPMs.dueSoon.length)}
                <CardTitle className="text-warning">Due Soon - Next 14 Days</CardTitle>
              </div>
              {isDueSoonOpen ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
            </CollapsibleTrigger>
          </CardHeader>
          <CollapsibleContent>
            <CardContent>
              <PMTable pms={groupedPMs.dueSoon} />
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>

      {/* Scheduled PMs - Collapsed by Default */}
      <Collapsible open={isScheduledOpen} onOpenChange={setIsScheduledOpen}>
        <Card>
          <CardHeader>
            <CollapsibleTrigger className="flex items-center justify-between w-full hover:opacity-80">
              <div className="flex items-center gap-3">
                {getStatusBadge('Scheduled', groupedPMs.scheduled.length)}
                <CardTitle>Scheduled - 15-90 Days Out</CardTitle>
              </div>
              {isScheduledOpen ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
            </CollapsibleTrigger>
          </CardHeader>
          <CollapsibleContent>
            <CardContent>
              <PMTable pms={groupedPMs.scheduled} />
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>

      {/* Not Scheduled PMs - Collapsed by Default */}
      <Collapsible open={isNotScheduledOpen} onOpenChange={setIsNotScheduledOpen}>
        <Card>
          <CardHeader>
            <CollapsibleTrigger className="flex items-center justify-between w-full hover:opacity-80">
              <div className="flex items-center gap-3">
                {getStatusBadge('Not Scheduled', groupedPMs.notScheduled.length)}
                <CardTitle>Not Scheduled - Needs Scheduling</CardTitle>
              </div>
              {isNotScheduledOpen ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
            </CollapsibleTrigger>
          </CardHeader>
          <CollapsibleContent>
            <CardContent>
              <PMTable pms={groupedPMs.notScheduled} />
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>
    </div>
  )
}

export default PMReport
