import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { apiUrl } from '@/lib/api'

const Check147 = () => {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const checkWorkOrders = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl('/api/reports/departments/rental/check-147'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch data')
      }

      const result = await response.json()
      setData(result)
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
          <CardTitle>147 Work Order Diagnostic</CardTitle>
        </CardHeader>
        <CardContent>
          <Button onClick={checkWorkOrders} disabled={loading}>
            {loading ? 'Loading...' : 'Check 147 Work Orders'}
          </Button>

          {error && (
            <div className="mt-4 p-4 bg-red-50 text-red-600 rounded">
              Error: {error}
            </div>
          )}

          {data && (
            <div className="mt-6 space-y-6">
              <div>
                <h3 className="font-semibold mb-2">Open 147 Work Orders Count:</h3>
                <p className="text-2xl font-bold">{data.open_count?.OpenCount || 0}</p>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Types Found in 147 Work Orders:</h3>
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-2 py-1 text-left text-xs font-medium text-gray-500">Type</th>
                      <th className="px-2 py-1 text-left text-xs font-medium text-gray-500">Count</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {data.types?.map((type, idx) => (
                      <tr key={idx}>
                        <td className="px-2 py-1 text-sm">{type.Type || 'NULL'}</td>
                        <td className="px-2 py-1 text-sm">{type.Count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Sample 147 Work Orders:</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-2 py-1 text-left text-xs font-medium text-gray-500">WO#</th>
                        <th className="px-2 py-1 text-left text-xs font-medium text-gray-500">Type</th>
                        <th className="px-2 py-1 text-left text-xs font-medium text-gray-500">BillTo</th>
                        <th className="px-2 py-1 text-left text-xs font-medium text-gray-500">SaleDept</th>
                        <th className="px-2 py-1 text-left text-xs font-medium text-gray-500">Status</th>
                        <th className="px-2 py-1 text-left text-xs font-medium text-gray-500">OpenDate</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {data.work_orders_147?.map((wo, idx) => (
                        <tr key={idx} className={wo.Status === 'Open' ? 'bg-yellow-50' : ''}>
                          <td className="px-2 py-1 text-sm">{wo.WONo}</td>
                          <td className="px-2 py-1 text-sm">{wo.Type || 'NULL'}</td>
                          <td className="px-2 py-1 text-sm">{wo.BillTo}</td>
                          <td className="px-2 py-1 text-sm">{wo.SaleDept}</td>
                          <td className="px-2 py-1 text-sm font-medium">{wo.Status}</td>
                          <td className="px-2 py-1 text-sm">{wo.OpenDate?.split('T')[0]}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Current Filters:</h3>
                <pre className="bg-gray-100 p-2 rounded text-sm">
                  {JSON.stringify(data.query_filters, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default Check147