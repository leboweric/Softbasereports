import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { apiUrl } from '@/lib/api'
import { Download, AlertCircle, CheckCircle, XCircle, Hash, RefreshCw } from 'lucide-react'
import * as XLSX from 'xlsx'

const ControlNumberReport = () => {
  const [loading, setLoading] = useState(true)
  const [mappingData, setMappingData] = useState(null)
  const [summaryData, setSummaryData] = useState(null)
  const [filter, setFilter] = useState('all') // all, assigned, not_assigned, in_gl

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      // Fetch both reports in parallel
      const [mappingResponse, summaryResponse] = await Promise.all([
        fetch(apiUrl('/api/reports/departments/accounting/control-serial-mapping'), {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(apiUrl('/api/reports/departments/accounting/control-number-summary'), {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ])

      if (mappingResponse.ok) {
        const data = await mappingResponse.json()
        setMappingData(data)
      }

      if (summaryResponse.ok) {
        const data = await summaryResponse.json()
        setSummaryData(data)
      }
    } catch (error) {
      console.error('Error fetching control number data:', error)
    } finally {
      setLoading(false)
    }
  }

  const exportToExcel = () => {
    if (!mappingData?.equipment) return

    // Prepare data for Excel
    const worksheetData = filteredEquipment.map(item => ({
      'Control Number': item.control_number === 'NOT ASSIGNED' ? '' : item.control_number,
      'Serial Number': item.serial_number,
      'Unit Number': item.unit_number,
      'Make': item.make,
      'Model': item.model,
      'Customer Name': item.customer_name || '',
      'Location': item.location || '',
      'Cost': item.cost,
      'Status': item.control_status,
      'In GL': item.in_gl_system,
      'Last WO': item.last_wo_number || '',
      'Last Invoice': item.last_invoice_no || ''
    }))

    // Create workbook and worksheet
    const wb = XLSX.utils.book_new()
    const ws = XLSX.utils.json_to_sheet(worksheetData)

    // Set column widths
    const colWidths = [
      { wch: 15 }, // Control Number
      { wch: 15 }, // Serial Number
      { wch: 12 }, // Unit Number
      { wch: 12 }, // Make
      { wch: 15 }, // Model
      { wch: 25 }, // Customer Name
      { wch: 15 }, // Location
      { wch: 10 }, // Cost
      { wch: 12 }, // Status
      { wch: 8 },  // In GL
      { wch: 12 }, // Last WO
      { wch: 12 }  // Last Invoice
    ]
    ws['!cols'] = colWidths

    // Add worksheet to workbook
    XLSX.utils.book_append_sheet(wb, ws, 'Control Number Mapping')

    // If there's summary data, add a second sheet
    if (mappingData?.summary) {
      const summaryData = [
        ['Summary Statistics'],
        [],
        ['Total Equipment', mappingData.summary.total_equipment],
        ['With Control Numbers', mappingData.summary.with_control_numbers],
        ['Without Control Numbers', mappingData.summary.without_control_numbers],
        ['Percentage Assigned', `${mappingData.summary.percentage_assigned}%`],
        ['With GL Entries', mappingData.summary.with_gl_entries]
      ]
      
      const wsSummary = XLSX.utils.aoa_to_sheet(summaryData)
      wsSummary['!cols'] = [{ wch: 25 }, { wch: 15 }]
      XLSX.utils.book_append_sheet(wb, wsSummary, 'Summary')
    }

    // Generate and download file
    const today = new Date().toISOString().split('T')[0]
    XLSX.writeFile(wb, `control_number_mapping_${today}.xlsx`)
  }

  const filteredEquipment = mappingData?.equipment?.filter(item => {
    if (filter === 'all') return true
    if (filter === 'assigned') return item.control_status === 'Assigned'
    if (filter === 'not_assigned') return item.control_status === 'Not Assigned'
    if (filter === 'in_gl') return item.in_gl_system === 'Yes'
    return true
  }) || []

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <Hash className="h-8 w-8 animate-pulse mx-auto mb-2" />
            <p>Loading control number data...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <Tabs defaultValue="mapping" className="space-y-4">
        <TabsList>
          <TabsTrigger value="mapping">Control Number Mapping</TabsTrigger>
          <TabsTrigger value="summary">Usage Summary</TabsTrigger>
        </TabsList>

        <TabsContent value="mapping" className="space-y-4">
          {/* Summary Cards */}
          {mappingData?.summary && (
            <div className="grid gap-4 md:grid-cols-5">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Total Equipment</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{mappingData.summary.total_equipment}</div>
                  <p className="text-xs text-muted-foreground">With serial numbers</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">With Control #</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span className="text-2xl font-bold text-green-600">
                      {mappingData.summary.with_control_numbers}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {mappingData.summary.percentage_assigned}% assigned
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Without Control #</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center">
                    <XCircle className="h-4 w-4 text-red-600 mr-2" />
                    <span className="text-2xl font-bold text-red-600">
                      {mappingData.summary.without_control_numbers}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">Need assignment</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">In GL System</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{mappingData.summary.with_gl_entries}</div>
                  <p className="text-xs text-muted-foreground">Have GL entries</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Next Control #</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {summaryData?.next_control_number || 'N/A'}
                  </div>
                  <p className="text-xs text-muted-foreground">Auto-increment</p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Equipment List */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Control Number to Serial Number Mapping</CardTitle>
                  <CardDescription>
                    Equipment control numbers linked to serial numbers for accounting reconciliation
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={fetchData}>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh
                  </Button>
                  <Button variant="outline" onClick={exportToExcel}>
                    <Download className="h-4 w-4 mr-2" />
                    Export XLS
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Filter Controls */}
              <div className="flex gap-4 mb-4">
                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  className="px-3 py-2 border rounded-md"
                >
                  <option value="all">All Equipment</option>
                  <option value="assigned">With Control Numbers</option>
                  <option value="not_assigned">Without Control Numbers</option>
                  <option value="in_gl">In GL System</option>
                </select>
                <div className="flex-1 text-right text-sm text-muted-foreground">
                  Showing {filteredEquipment.length} of {mappingData?.equipment?.length || 0} records
                </div>
              </div>

              {/* Equipment Table */}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Control #</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Serial #</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Unit #</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Make</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Model</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Customer</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Location</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Cost</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">GL</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Last WO</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredEquipment.slice(0, 100).map((item, idx) => (
                      <tr key={idx} className={item.control_status === 'Not Assigned' ? 'bg-red-50' : ''}>
                        <td className="px-4 py-2 text-sm">
                          {item.control_number === 'NOT ASSIGNED' ? (
                            <Badge variant="outline" className="bg-red-100">Not Assigned</Badge>
                          ) : (
                            <span className="font-medium">{item.control_number}</span>
                          )}
                        </td>
                        <td className="px-4 py-2 text-sm font-medium">{item.serial_number}</td>
                        <td className="px-4 py-2 text-sm">{item.unit_number}</td>
                        <td className="px-4 py-2 text-sm">{item.make}</td>
                        <td className="px-4 py-2 text-sm">{item.model}</td>
                        <td className="px-4 py-2 text-sm">{item.customer_name || '-'}</td>
                        <td className="px-4 py-2 text-sm">{item.location || '-'}</td>
                        <td className="px-4 py-2 text-sm">
                          ${item.cost ? item.cost.toLocaleString() : '0'}
                        </td>
                        <td className="px-4 py-2 text-sm">
                          {item.in_gl_system === 'Yes' ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <XCircle className="h-4 w-4 text-gray-400" />
                          )}
                        </td>
                        <td className="px-4 py-2 text-sm">{item.last_wo_number || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {filteredEquipment.length > 100 && (
                <div className="mt-4 text-sm text-muted-foreground text-center">
                  Showing first 100 records. Export XLS for complete data.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="summary" className="space-y-4">
          {/* Usage Statistics */}
          {summaryData?.usage_statistics && (
            <Card>
              <CardHeader>
                <CardTitle>Control Number Usage Across System</CardTitle>
                <CardDescription>
                  How control numbers are used in different parts of the system
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Table</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Total Records</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">With Control #</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Unique Control #s</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">% With Control</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {summaryData.usage_statistics.map((stat, idx) => (
                        <tr key={idx}>
                          <td className="px-4 py-2 text-sm font-medium">{stat.table_name}</td>
                          <td className="px-4 py-2 text-sm text-right">
                            {stat.total_records.toLocaleString()}
                          </td>
                          <td className="px-4 py-2 text-sm text-right">
                            {stat.records_with_control_no.toLocaleString()}
                          </td>
                          <td className="px-4 py-2 text-sm text-right">
                            {stat.unique_control_numbers.toLocaleString()}
                          </td>
                          <td className="px-4 py-2 text-sm text-right">
                            <Badge variant={stat.percentage_with_control > 50 ? "default" : "secondary"}>
                              {stat.percentage_with_control}%
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recent Control Number Changes */}
          {summaryData?.recent_changes && summaryData.recent_changes.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recent Control Number Changes</CardTitle>
                <CardDescription>
                  Audit trail of control number modifications
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Date</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Serial #</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Unit #</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Old Control #</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">New Control #</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Changed By</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {summaryData.recent_changes.slice(0, 20).map((change, idx) => (
                        <tr key={idx}>
                          <td className="px-4 py-2 text-sm">{change.change_date || '-'}</td>
                          <td className="px-4 py-2 text-sm font-medium">{change.serial_number}</td>
                          <td className="px-4 py-2 text-sm">{change.unit_number}</td>
                          <td className="px-4 py-2 text-sm">{change.old_control_no || '-'}</td>
                          <td className="px-4 py-2 text-sm font-medium">{change.new_control_no || '-'}</td>
                          <td className="px-4 py-2 text-sm">{change.changed_by || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default ControlNumberReport