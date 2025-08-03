import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { apiUrl } from '@/lib/api'

const RentalDiagnostic = () => {
  const [loading, setLoading] = useState(false)
  const [schemaData, setSchemaData] = useState(null)
  const [error, setError] = useState(null)

  const fetchSchema = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl('/api/reports/departments/rental/wo-schema'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch schema')
      }

      const data = await response.json()
      setSchemaData(data)
    } catch (err) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6 p-6">
      <Card>
        <CardHeader>
          <CardTitle>WO Table Diagnostic Tool</CardTitle>
        </CardHeader>
        <CardContent>
          <Button onClick={fetchSchema} disabled={loading}>
            {loading ? 'Loading...' : 'Fetch WO Table Schema'}
          </Button>

          {error && (
            <div className="mt-4 p-4 bg-red-50 text-red-600 rounded">
              Error: {error}
            </div>
          )}

          {schemaData && (
            <div className="mt-6 space-y-6">
              <div>
                <h3 className="font-semibold mb-2">Potential Customer Fields:</h3>
                <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto">
                  {JSON.stringify(schemaData.potential_customer_fields, null, 2)}
                </pre>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Sample Work Order:</h3>
                <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto max-h-96">
                  {JSON.stringify(schemaData.sample_work_order, null, 2)}
                </pre>
              </div>

              <div>
                <h3 className="font-semibold mb-2">WO Table Columns:</h3>
                <div className="max-h-64 overflow-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-2 py-1 text-left text-xs font-medium text-gray-500">Column</th>
                        <th className="px-2 py-1 text-left text-xs font-medium text-gray-500">Type</th>
                        <th className="px-2 py-1 text-left text-xs font-medium text-gray-500">Nullable</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {schemaData.wo_columns?.map((col, idx) => (
                        <tr key={idx}>
                          <td className="px-2 py-1 text-sm">{col.COLUMN_NAME}</td>
                          <td className="px-2 py-1 text-sm">{col.DATA_TYPE}</td>
                          <td className="px-2 py-1 text-sm">{col.IS_NULLABLE}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2">WOLabor Columns:</h3>
                <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto max-h-48">
                  {JSON.stringify(schemaData.labor_columns, null, 2)}
                </pre>
              </div>

              <div>
                <h3 className="font-semibold mb-2">WOParts Columns:</h3>
                <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto max-h-48">
                  {JSON.stringify(schemaData.parts_columns, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default RentalDiagnostic