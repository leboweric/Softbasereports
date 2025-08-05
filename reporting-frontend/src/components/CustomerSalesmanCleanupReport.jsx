import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, Download, RefreshCw, Users, UserX } from 'lucide-react'
import { apiUrl } from '@/lib/api'
import * as XLSX from 'xlsx'

const CustomerSalesmanCleanupReport = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [cleanupData, setCleanupData] = useState(null)
  const [error, setError] = useState(null)

  const fetchCleanupData = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/customer-salesman-cleanup'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setCleanupData(data)
      } else {
        setError('Failed to fetch cleanup data')
      }
    } catch (error) {
      console.error('Error fetching cleanup data:', error)
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCleanupData()
  }, [])

  const downloadExcel = () => {
    if (!cleanupData) return

    // Create workbook
    const wb = XLSX.utils.book_new()

    // Sheet 1: Missing Assignments
    const missingData = cleanupData.missing_assignments.map(customer => ({
      'Customer Number': customer.Number,
      'Customer Name': customer.Name,
      'Zip Code': customer.ZipCode || '',
      'Active': customer.active_status,
      'YTD Sales': customer.ytd_sales || 0,
      'Last Invoice': customer.last_invoice_date || 'Never',
      'Invoice Count': customer.invoice_count || 0
    }))
    
    const missingSheet = XLSX.utils.json_to_sheet(missingData)
    XLSX.utils.book_append_sheet(wb, missingSheet, 'Missing Salesmen')

    // Sheet 2: Potential Duplicates
    const duplicateData = []
    cleanupData.potential_duplicates.forEach(group => {
      duplicateData.push({
        'Group': `=== ${group.base_name} (${group.count} records) ===`,
        'Customer Number': '',
        'Customer Name': '',
        'Salesman1': '',
        'Salesman2': '',
        'Salesman3': '',
        'Active': '',
        'YTD Sales': '',
        'Last Invoice': ''
      })
      
      group.customers.forEach(customer => {
        duplicateData.push({
          'Group': '',
          'Customer Number': customer.Number,
          'Customer Name': customer.Name,
          'Zip Code': customer.ZipCode || '',
          'Salesman1': customer.Salesman1 || '',
          'Salesman2': customer.Salesman2 || '',
          'Salesman3': customer.Salesman3 || '',
          'Active': customer.active_status,
          'YTD Sales': customer.ytd_sales || 0,
          'Last Invoice': customer.last_invoice_date || 'Never'
        })
      })
      
      duplicateData.push({}) // Empty row between groups
    })
    
    const duplicateSheet = XLSX.utils.json_to_sheet(duplicateData)
    XLSX.utils.book_append_sheet(wb, duplicateSheet, 'Potential Duplicates')

    // Sheet 3: Summary
    const summaryData = [
      { 'Metric': 'Total Customers', 'Count': cleanupData.summary.total_customers },
      { 'Metric': 'Customers with Salesmen', 'Count': cleanupData.summary.with_salesman },
      { 'Metric': 'Customers Missing Salesmen', 'Count': cleanupData.summary.missing_salesman },
      { 'Metric': 'Active Customers Missing Salesmen', 'Count': cleanupData.summary.active_missing_salesman },
      { 'Metric': 'Potential Duplicate Groups', 'Count': cleanupData.summary.duplicate_groups },
      { 'Metric': 'Total Duplicate Records', 'Count': cleanupData.summary.total_duplicate_records }
    ]
    
    const summarySheet = XLSX.utils.json_to_sheet(summaryData)
    XLSX.utils.book_append_sheet(wb, summarySheet, 'Summary')

    // Download file
    XLSX.writeFile(wb, `Customer_Salesman_Cleanup_${new Date().toISOString().split('T')[0]}.xlsx`)
  }

  if (loading) {
    return (
      <LoadingSpinner 
        title="Loading Cleanup Data" 
        description="Analyzing customer records..."
        size="large"
      />
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-red-600">
            Error: {error}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Customer Salesman Cleanup Report</h2>
          <p className="text-muted-foreground">Identify missing assignments and potential duplicate customers</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchCleanupData} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={downloadExcel}>
            <Download className="h-4 w-4 mr-2" />
            Export Excel
          </Button>
        </div>
      </div>

      {cleanupData && (
        <>
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Total Customers</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{cleanupData.summary.total_customers.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {cleanupData.summary.with_salesman.toLocaleString()} have salesmen assigned
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Missing Assignments</CardTitle>
                <UserX className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {cleanupData.summary.missing_salesman.toLocaleString()}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {cleanupData.summary.active_missing_salesman.toLocaleString()} are active customers
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Potential Duplicates</CardTitle>
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-yellow-600">
                  {cleanupData.summary.duplicate_groups}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {cleanupData.summary.total_duplicate_records} total duplicate records
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Active Customers Missing Salesmen */}
          <Card>
            <CardHeader>
              <CardTitle>Active Customers Missing Salesmen</CardTitle>
              <CardDescription>
                Customers with recent invoices but no salesman assigned
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Number</th>
                      <th className="text-left p-2">Name</th>
                      <th className="text-left p-2">Zip Code</th>
                      <th className="text-right p-2">YTD Sales</th>
                      <th className="text-center p-2">Invoices</th>
                      <th className="text-left p-2">Last Invoice</th>
                      <th className="text-center p-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cleanupData.missing_assignments
                      .filter(c => c.active_status === 'Active')
                      .slice(0, 20)
                      .map((customer, idx) => (
                        <tr key={idx} className="border-b hover:bg-gray-50">
                          <td className="p-2 font-mono">{customer.Number}</td>
                          <td className="p-2">{customer.Name}</td>
                          <td className="p-2">{customer.ZipCode || '-'}</td>
                          <td className="text-right p-2">
                            ${(customer.ytd_sales || 0).toLocaleString()}
                          </td>
                          <td className="text-center p-2">{customer.invoice_count || 0}</td>
                          <td className="p-2">
                            {customer.last_invoice_date 
                              ? new Date(customer.last_invoice_date).toLocaleDateString()
                              : 'Never'}
                          </td>
                          <td className="text-center p-2">
                            <Badge variant={customer.active_status === 'Active' ? 'default' : 'secondary'}>
                              {customer.active_status}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
                {cleanupData.missing_assignments.filter(c => c.active_status === 'Active').length > 20 && (
                  <p className="text-sm text-muted-foreground mt-2">
                    Showing 20 of {cleanupData.missing_assignments.filter(c => c.active_status === 'Active').length} active customers. 
                    Download Excel for complete list.
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Potential Duplicates */}
          <Card>
            <CardHeader>
              <CardTitle>Potential Duplicate Customers</CardTitle>
              <CardDescription>
                Customer groups with similar names that might be duplicates
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {cleanupData.potential_duplicates.slice(0, 10).map((group, idx) => (
                  <div key={idx} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-semibold">{group.base_name}</h4>
                      <Badge variant="outline">{group.count} records</Badge>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left p-2">Number</th>
                            <th className="text-left p-2">Full Name</th>
                            <th className="text-left p-2">Zip Code</th>
                            <th className="text-left p-2">Salesman</th>
                            <th className="text-right p-2">YTD Sales</th>
                            <th className="text-center p-2">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {group.customers.map((customer, cidx) => (
                            <tr key={cidx} className="border-b">
                              <td className="p-2 font-mono">{customer.Number}</td>
                              <td className="p-2">{customer.Name}</td>
                              <td className="p-2">{customer.ZipCode || '-'}</td>
                              <td className="p-2">
                                {customer.Salesman1 ? (
                                  <Badge variant="default">{customer.Salesman1}</Badge>
                                ) : (
                                  <Badge variant="destructive">None</Badge>
                                )}
                              </td>
                              <td className="text-right p-2">
                                ${(customer.ytd_sales || 0).toLocaleString()}
                              </td>
                              <td className="text-center p-2">
                                <Badge variant={customer.active_status === 'Active' ? 'default' : 'secondary'}>
                                  {customer.active_status}
                                </Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
                {cleanupData.potential_duplicates.length > 10 && (
                  <p className="text-sm text-muted-foreground">
                    Showing 10 of {cleanupData.potential_duplicates.length} potential duplicate groups. 
                    Download Excel for complete list.
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Data Quality Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle>Data Quality Recommendations</CardTitle>
              <CardDescription>Steps to improve customer data quality</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="bg-blue-100 rounded-full p-1 mt-0.5">
                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                  </div>
                  <div>
                    <p className="font-medium">Assign salesmen to active customers</p>
                    <p className="text-sm text-muted-foreground">
                      {cleanupData.summary.active_missing_salesman} active customers need salesman assignments
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="bg-blue-100 rounded-full p-1 mt-0.5">
                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                  </div>
                  <div>
                    <p className="font-medium">Merge duplicate customer records</p>
                    <p className="text-sm text-muted-foreground">
                      Review {cleanupData.summary.duplicate_groups} groups of potential duplicates
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="bg-blue-100 rounded-full p-1 mt-0.5">
                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                  </div>
                  <div>
                    <p className="font-medium">Implement data validation rules</p>
                    <p className="text-sm text-muted-foreground">
                      Require salesman assignment when creating new customers
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="bg-blue-100 rounded-full p-1 mt-0.5">
                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                  </div>
                  <div>
                    <p className="font-medium">Regular data audits</p>
                    <p className="text-sm text-muted-foreground">
                      Schedule monthly reviews of customer data quality
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}

export default CustomerSalesmanCleanupReport