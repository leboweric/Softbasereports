import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AlertCircle, CheckCircle, XCircle, RefreshCw } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const RentalAvailabilityDebug = () => {
  const [debugData, setDebugData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchDebugData = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl('/api/reports/departments/rental/availability-debug'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to fetch debug data')
      }

      const data = await response.json()
      setDebugData(data)
    } catch (err) {
      setError(err.message)
      console.error('Debug fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDebugData()
  }, [])

  const renderStatus = (value, isError = false) => {
    if (isError || value === 0 || value === null || value === undefined) {
      return <XCircle className="h-4 w-4 text-red-500 inline mr-2" />
    }
    return <CheckCircle className="h-4 w-4 text-green-500 inline mr-2" />
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <RefreshCw className="h-6 w-6 animate-spin mr-2" />
            <span>Running diagnostics...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-red-200">
        <CardHeader>
          <CardTitle className="text-red-600">Debug Error</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-red-500 mr-2 mt-0.5" />
            <div>
              <p className="font-medium">Failed to fetch debug data:</p>
              <p className="text-sm text-gray-600 mt-1">{error}</p>
            </div>
          </div>
          <Button onClick={fetchDebugData} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!debugData) {
    return null
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Rental Availability Debug Report</CardTitle>
          <CardDescription>Diagnostic information for troubleshooting data issues</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Table Access Tests */}
          <div>
            <h3 className="font-semibold mb-3">1. Database Table Access</h3>
            <div className="space-y-2 pl-4">
              <div>
                {renderStatus(debugData.equipment_table_count, debugData.equipment_table_error)}
                <span>Equipment table: </span>
                {debugData.equipment_table_error ? (
                  <span className="text-red-600">{debugData.equipment_table_error}</span>
                ) : (
                  <span className="font-medium">{debugData.equipment_table_count} total records</span>
                )}
              </div>
              
              <div>
                {renderStatus(debugData.equipment_columns, debugData.equipment_columns_error)}
                <span>Table columns: </span>
                {debugData.equipment_columns_error ? (
                  <span className="text-red-600">{debugData.equipment_columns_error}</span>
                ) : (
                  <span className="font-medium">{debugData.equipment_columns?.length || 0} columns found</span>
                )}
              </div>
            </div>
          </div>

          {/* Rental Status Values */}
          <div>
            <h3 className="font-semibold mb-3">2. Rental Status Values in Database</h3>
            <div className="pl-4">
              {debugData.rental_status_error ? (
                <div className="text-red-600">{debugData.rental_status_error}</div>
              ) : debugData.rental_status_values?.length > 0 ? (
                <div className="bg-gray-50 p-3 rounded">
                  <table className="text-sm">
                    <thead>
                      <tr>
                        <th className="text-left pr-8">Status</th>
                        <th className="text-right">Count</th>
                      </tr>
                    </thead>
                    <tbody>
                      {debugData.rental_status_values.map((item, idx) => (
                        <tr key={idx}>
                          <td className="pr-8">{item.RentalStatus || '(null/empty)'}</td>
                          <td className="text-right font-medium">{item.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <span className="text-yellow-600">No rental status values found</span>
              )}
            </div>
          </div>

          {/* Equipment Counts */}
          <div>
            <h3 className="font-semibold mb-3">3. Equipment Filtering Results</h3>
            <div className="space-y-2 pl-4">
              <div>
                {renderStatus(debugData.equipment_with_rates)}
                <span>Equipment with rental rates (Day/Week/Month &gt; 0): </span>
                <span className="font-medium">{debugData.equipment_with_rates || 0}</span>
              </div>
              
              <div>
                {renderStatus(debugData.equipment_with_make)}
                <span>Equipment with Make specified: </span>
                <span className="font-medium">{debugData.equipment_with_make || 0}</span>
              </div>
              
              <div>
                {renderStatus(debugData.simplified_query_results)}
                <span>Simplified query results: </span>
                <span className="font-medium">{debugData.simplified_query_results || 0} records</span>
              </div>
            </div>
          </div>

          {/* Sample Rental Equipment */}
          {debugData.sample_rental_equipment?.length > 0 && (
            <div>
              <h3 className="font-semibold mb-3">4. Sample Rental Equipment (with rates)</h3>
              <div className="pl-4 overflow-x-auto">
                <table className="text-sm border">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="border p-2">Make</th>
                      <th className="border p-2">Model</th>
                      <th className="border p-2">Unit#</th>
                      <th className="border p-2">Status</th>
                      <th className="border p-2">Day Rate</th>
                      <th className="border p-2">Customer#</th>
                    </tr>
                  </thead>
                  <tbody>
                    {debugData.sample_rental_equipment.slice(0, 5).map((item, idx) => (
                      <tr key={idx}>
                        <td className="border p-2">{item.Make}</td>
                        <td className="border p-2">{item.Model}</td>
                        <td className="border p-2">{item.UnitNo}</td>
                        <td className="border p-2">{item.RentalStatus || '-'}</td>
                        <td className="border p-2">${item.DayRent || 0}</td>
                        <td className="border p-2">{item.CustomerNo || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Customer Join Test */}
          {debugData.customer_join_test && (
            <div>
              <h3 className="font-semibold mb-3">5. Customer Join Test</h3>
              <div className="pl-4">
                {debugData.customer_join_error ? (
                  <div className="text-red-600">{debugData.customer_join_error}</div>
                ) : debugData.customer_join_test.length > 0 ? (
                  <div className="bg-gray-50 p-3 rounded text-sm">
                    {debugData.customer_join_test.map((item, idx) => (
                      <div key={idx}>
                        Unit {item.UnitNo}: Customer #{item.CustomerNo} = {item.CustomerName || '(not found)'}
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="text-yellow-600">No equipment with customers found</span>
                )}
              </div>
            </div>
          )}

          {/* Sample Equipment Record */}
          {debugData.sample_equipment && (
            <div>
              <h3 className="font-semibold mb-3">6. Sample Equipment Record (all columns)</h3>
              <div className="pl-4 bg-gray-50 p-3 rounded">
                <pre className="text-xs overflow-x-auto">
                  {JSON.stringify(debugData.sample_equipment, null, 2)}
                </pre>
              </div>
            </div>
          )}

          <div className="pt-4 border-t">
            <Button onClick={fetchDebugData}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Re-run Diagnostics
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default RentalAvailabilityDebug