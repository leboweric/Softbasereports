import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { apiUrl } from '@/lib/api'
import { Search, Database, AlertCircle } from 'lucide-react'

const ControlNumberFinder = () => {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const findControlFields = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl('/api/reports/departments/accounting/find-control-fields'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch control fields')
      }

      const data = await response.json()
      setResults(data)
    } catch (error) {
      console.error('Error finding control fields:', error)
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Control Number Field Research</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <Button onClick={findControlFields} disabled={loading}>
                <Search className="h-4 w-4 mr-2" />
                {loading ? 'Searching...' : 'Search for Control Fields'}
              </Button>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded p-3">
                <div className="flex items-center">
                  <AlertCircle className="h-4 w-4 text-red-600 mr-2" />
                  <span className="text-sm text-red-800">{error}</span>
                </div>
              </div>
            )}

            {results && (
              <div className="space-y-6">
                {/* Equipment Table Columns */}
                <div>
                  <h3 className="font-semibold mb-2">Equipment Table Columns (First 50)</h3>
                  <div className="bg-gray-50 rounded p-3">
                    <code className="text-xs">
                      {results.equipment_columns?.join(', ') || 'No columns found'}
                    </code>
                  </div>
                </div>

                {/* Control-Related Columns */}
                <div>
                  <h3 className="font-semibold mb-2">Potential Control-Related Columns in Equipment</h3>
                  {results.control_related_columns?.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Column Name</th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Data Type</th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Max Length</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {results.control_related_columns.map((col, idx) => (
                            <tr key={idx}>
                              <td className="px-4 py-2 text-sm font-medium text-gray-900">{col.column}</td>
                              <td className="px-4 py-2 text-sm text-gray-500">{col.type}</td>
                              <td className="px-4 py-2 text-sm text-gray-500">{col.length || 'N/A'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No control-related columns found in Equipment table</p>
                  )}
                </div>

                {/* Sample Equipment Data */}
                <div>
                  <h3 className="font-semibold mb-2">Sample Equipment Records</h3>
                  {results.sample_equipment?.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            {Object.keys(results.sample_equipment[0] || {}).map(key => (
                              <th key={key} className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                                {key}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {results.sample_equipment.map((row, idx) => (
                            <tr key={idx}>
                              {Object.values(row).map((val, vidx) => (
                                <td key={vidx} className="px-4 py-2 text-sm text-gray-900">
                                  {val || '-'}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No sample data available</p>
                  )}
                </div>

                {/* All Control Columns Across Database */}
                <div>
                  <h3 className="font-semibold mb-2">Control Columns in All Tables</h3>
                  {results.all_control_columns?.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Table</th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Column</th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Data Type</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {results.all_control_columns.map((col, idx) => (
                            <tr key={idx}>
                              <td className="px-4 py-2 text-sm font-medium text-gray-900">{col.TABLE_NAME}</td>
                              <td className="px-4 py-2 text-sm text-gray-500">{col.COLUMN_NAME}</td>
                              <td className="px-4 py-2 text-sm text-gray-500">{col.DATA_TYPE}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No control columns found in any table</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default ControlNumberFinder