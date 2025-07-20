import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { apiUrl } from '@/lib/api'
import { AlertCircle } from 'lucide-react'

const InvoiceExplorer = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchInvoiceColumns()
  }, [])

  const fetchInvoiceColumns = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/invoice-columns'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        setData(result)
      } else {
        setError(`Failed to fetch: ${response.status}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center text-red-500">
          <AlertCircle className="h-12 w-12 mx-auto mb-4" />
          <p>Error: {error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">InvoiceReg Table Explorer</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>Column Names</CardTitle>
          <CardDescription>All columns in ben002.InvoiceReg table</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-2">
            {data?.column_names?.map((col, idx) => (
              <div key={idx} className="p-2 bg-gray-100 rounded text-sm">
                {col}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Columns with Data Types</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Column Name</th>
                <th className="text-left p-2">Data Type</th>
              </tr>
            </thead>
            <tbody>
              {data?.columns?.map((col, idx) => (
                <tr key={idx} className="border-b">
                  <td className="p-2">{col.COLUMN_NAME}</td>
                  <td className="p-2 text-gray-600">{col.DATA_TYPE}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Sample Data</CardTitle>
          <CardDescription>First row from InvoiceReg table</CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="overflow-x-auto bg-gray-100 p-4 rounded">
            {JSON.stringify(data?.sample, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  )
}

export default InvoiceExplorer