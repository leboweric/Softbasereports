import React, { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, Calendar, ChevronDown, ChevronUp, Clock, Download, MapPin, User } from 'lucide-react'
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
import { apiUrl } from '@/lib/api'
import * as XLSX from 'xlsx'

const PMRoutePlanner = ({ user }) => {
  const [pmData, setPmData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [expandedCities, setExpandedCities] = useState({})

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

  // Normalize city name to handle variations
  const normalizeCity = (city) => {
    if (!city) return 'Unknown Location'
    
    return city
      .trim() // Remove leading/trailing spaces
      .replace(/\s+/g, ' ') // Replace multiple spaces with single space
      .toUpperCase() // Standardize capitalization for comparison
      .replace(/^ST\.?\s+/i, 'SAINT ') // Convert "St" or "St." to "Saint"
      .replace(/\s+ST\.?\s+/gi, ' SAINT ') // Convert middle "St" or "St." to "Saint"
  }

  // Group PMs by city, focusing on overdue and due soon
  const cityClusters = useMemo(() => {
    if (!pmData?.pms) return []
    
    // Filter to only overdue and due soon PMs
    const urgentPMs = pmData.pms.filter(pm => 
      pm.status === 'Overdue' || pm.status === 'Due Soon'
    )
    
    // Group by city
    const cityMap = new Map()
    
    urgentPMs.forEach(pm => {
      const originalCity = pm.customer_city || 'Unknown Location'
      const normalizedCity = normalizeCity(originalCity)
      const state = pm.customer_state || ''
      const cityKey = `${normalizedCity}, ${state}`.trim().replace(/,\s*$/, '')
      
      if (!cityMap.has(cityKey)) {
        cityMap.set(cityKey, {
          city: normalizedCity,
          state: state,
          cityKey: cityKey,
          pms: [],
          overdue: 0,
          dueSoon: 0,
          zipCodes: new Set()
        })
      }
      
      const cluster = cityMap.get(cityKey)
      cluster.pms.push(pm)
      
      if (pm.status === 'Overdue') cluster.overdue++
      if (pm.status === 'Due Soon') cluster.dueSoon++
      
      if (pm.customer_zip) {
        cluster.zipCodes.add(pm.customer_zip)
      }
    })
    
    // Convert to array and sort alphabetically by city name
    return Array.from(cityMap.values())
      .map(cluster => ({
        ...cluster,
        total: cluster.pms.length,
        zipCodes: Array.from(cluster.zipCodes).sort()
      }))
      .sort((a, b) => a.cityKey.localeCompare(b.cityKey))
  }, [pmData])

  const toggleCity = (cityKey) => {
    setExpandedCities(prev => ({
      ...prev,
      [cityKey]: !prev[cityKey]
    }))
  }

  const expandAll = () => {
    const allExpanded = {}
    cityClusters.forEach(cluster => {
      allExpanded[cluster.cityKey] = true
    })
    setExpandedCities(allExpanded)
  }

  const collapseAll = () => {
    setExpandedCities({})
  }

  const exportCityPMs = (cluster) => {
    const exportData = cluster.pms.map(pm => ({
      'Serial No': pm.serial_no || '',
      'Customer': pm.customer_name || '',
      'Address': pm.customer_address || '',
      'City': pm.customer_city || '',
      'State': pm.customer_state || '',
      'Zip': pm.customer_zip || '',
      'Phone': pm.customer_phone || '',
      'Contact': pm.customer_contact || '',
      'Make': pm.make || '',
      'Model': pm.model || '',
      'Unit No': pm.unit_no || '',
      'Frequency': pm.frequency || '',
      'Last Labor Date': pm.last_labor_date || '',
      'Next PM Date': pm.next_pm_date || '',
      'Days Until Due': pm.days_until_due,
      'Technician': pm.technician || '',
      'Status': pm.status,
      'Comments': pm.comments || ''
    }))

    const wb = XLSX.utils.book_new()
    const ws = XLSX.utils.json_to_sheet(exportData)

    ws['!cols'] = [
      { wch: 12 }, { wch: 25 }, { wch: 30 }, { wch: 15 }, { wch: 8 },
      { wch: 10 }, { wch: 15 }, { wch: 20 }, { wch: 15 }, { wch: 15 },
      { wch: 12 }, { wch: 10 }, { wch: 15 }, { wch: 15 }, { wch: 12 },
      { wch: 15 }, { wch: 12 }, { wch: 40 }
    ]

    XLSX.utils.book_append_sheet(wb, ws, 'PMs')
    
    const filename = `PM_Route_${cluster.city.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.xlsx`
    XLSX.writeFile(wb, filename)
  }

  const getStatusBadge = (status) => {
    if (status === 'Overdue') {
      return <Badge variant="destructive" className="text-xs">Overdue</Badge>
    }
    return <Badge variant="warning" className="text-xs">Due Soon</Badge>
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

  const totalUrgentPMs = cityClusters.reduce((sum, cluster) => sum + cluster.total, 0)
  const totalOverdue = cityClusters.reduce((sum, cluster) => sum + cluster.overdue, 0)
  const totalDueSoon = cityClusters.reduce((sum, cluster) => sum + cluster.dueSoon, 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="h-5 w-5" />
                PM Route Planner - Geographic Clustering
              </CardTitle>
              <CardDescription className="mt-2">
                Plan efficient routes by grouping PMs in the same geographic area. 
                Cities are organized alphabetically for easy lookup.
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button onClick={expandAll} variant="outline" size="sm">
                Expand All
              </Button>
              <Button onClick={collapseAll} variant="outline" size="sm">
                Collapse All
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-primary/10 p-3">
                <MapPin className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Locations</p>
                <p className="text-2xl font-bold">{cityClusters.length}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-destructive/10 p-3">
                <AlertTriangle className="h-5 w-5 text-destructive" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Overdue PMs</p>
                <p className="text-2xl font-bold text-destructive">{totalOverdue}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-warning/10 p-3">
                <Clock className="h-5 w-5 text-warning" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Due Soon PMs</p>
                <p className="text-2xl font-bold text-warning">{totalDueSoon}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* City Clusters */}
      {cityClusters.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">No overdue or due soon PMs found</p>
          </CardContent>
        </Card>
      ) : (
        cityClusters.map((cluster) => (
          <Collapsible
            key={cluster.cityKey}
            open={expandedCities[cluster.cityKey]}
            onOpenChange={() => toggleCity(cluster.cityKey)}
          >
            <Card className={cluster.overdue > 0 ? 'border-destructive' : 'border-warning'}>
              <CardHeader>
                <CollapsibleTrigger className="flex items-center justify-between w-full hover:opacity-80">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <MapPin className="h-5 w-5 text-primary" />
                      <div className="text-left">
                        <CardTitle>{cluster.cityKey || 'Unknown Location'}</CardTitle>
                        <CardDescription className="mt-1">
                          {cluster.zipCodes.length > 0 && (
                            <span>Zip codes: {cluster.zipCodes.join(', ')}</span>
                          )}
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant="outline" className="text-sm">
                        {cluster.total} PM{cluster.total !== 1 ? 's' : ''}
                      </Badge>
                      {cluster.overdue > 0 && (
                        <Badge variant="destructive" className="text-sm">
                          {cluster.overdue} Overdue
                        </Badge>
                      )}
                      {cluster.dueSoon > 0 && (
                        <Badge variant="warning" className="text-sm">
                          {cluster.dueSoon} Due Soon
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      onClick={(e) => {
                        e.stopPropagation()
                        exportCityPMs(cluster)
                      }}
                      variant="outline"
                      size="sm"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Export
                    </Button>
                    {expandedCities[cluster.cityKey] ? (
                      <ChevronUp className="h-5 w-5" />
                    ) : (
                      <ChevronDown className="h-5 w-5" />
                    )}
                  </div>
                </CollapsibleTrigger>
              </CardHeader>
              <CollapsibleContent>
                <CardContent>
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Serial No</TableHead>
                          <TableHead>Customer</TableHead>
                          <TableHead>Address</TableHead>
                          <TableHead>Make/Model</TableHead>
                          <TableHead>Last Labor</TableHead>
                          <TableHead>Next PM Date</TableHead>
                          <TableHead>Technician</TableHead>
                          <TableHead>Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {cluster.pms.map((pm) => (
                          <TableRow key={pm.id}>
                            <TableCell className="font-mono text-xs">{pm.serial_no}</TableCell>
                            <TableCell>
                              <div className="flex flex-col">
                                <span className="font-medium">{pm.customer_name}</span>
                                {pm.customer_phone && (
                                  <span className="text-xs text-muted-foreground">{pm.customer_phone}</span>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="text-sm">
                                {pm.customer_address && <div>{pm.customer_address}</div>}
                                {pm.customer_zip && (
                                  <div className="text-muted-foreground">{pm.customer_zip}</div>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="text-sm">
                                {pm.make && pm.model ? (
                                  <>
                                    <div>{pm.make}</div>
                                    <div className="text-muted-foreground">{pm.model}</div>
                                  </>
                                ) : (
                                  'N/A'
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              {pm.last_labor_date ? new Date(pm.last_labor_date).toLocaleDateString() : 'N/A'}
                            </TableCell>
                            <TableCell>
                              <div className="flex flex-col">
                                <span>{pm.next_pm_date ? new Date(pm.next_pm_date).toLocaleDateString() : 'Not scheduled'}</span>
                                {pm.days_until_due !== null && (
                                  <span className={`text-xs ${pm.days_until_due < 0 ? 'text-destructive font-semibold' : 'text-muted-foreground'}`}>
                                    {pm.days_until_due < 0 ? Math.abs(pm.days_until_due) + ' days ago' : pm.days_until_due + ' days'}
                                  </span>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-1">
                                <User className="h-3 w-3 text-muted-foreground" />
                                {pm.technician || 'Unassigned'}
                              </div>
                            </TableCell>
                            <TableCell>{getStatusBadge(pm.status)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Card>
          </Collapsible>
        ))
      )}
    </div>
  )
}

export default PMRoutePlanner
