import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Database } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const InvoiceSchemaExplorer = () => {
  const [loading, setLoading] = useState(false)
  const [schemaData, setSchemaData] = useState(null)

  const fetchSchema = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        apiUrl('/api/reports/departments/service/invoice-schema'),
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      )
      
      if (response.ok) {
        const data = await response.json()
        setSchemaData(data)
      }
    } catch (error) {
      console.error('Error fetching schema:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle>Invoice Schema Explorer</CardTitle>
            <Database className="h-5 w-5 text-gray-500" />
          </div>
          <Button onClick={fetchSchema} disabled={loading}>
            {loading ? 'Loading...' : 'Explore Schema'}
          </Button>
        </div>
        <CardDescription>
          Diagnostic tool to find all available InvoiceReg fields
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="flex justify-center py-8">
            <LoadingSpinner size={32} />
          </div>
        )}

        {schemaData && !loading && (
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold mb-2">Total Columns: {schemaData.total_columns}</h3>
            </div>

            <div>
              <h3 className="font-semibold mb-2">Freight/PO Related Fields:</h3>
              <div className="bg-gray-50 p-4 rounded-lg overflow-x-auto">
                <pre className="text-xs">
                  {JSON.stringify(schemaData.freight_po_related_fields, null, 2)}
                </pre>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-2">Sample Invoice Data:</h3>
              <div className="bg-gray-50 p-4 rounded-lg overflow-x-auto">
                <pre className="text-xs">
                  {JSON.stringify(schemaData.sample_invoice, null, 2)}
                </pre>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-2">All Columns:</h3>
              <div className="grid grid-cols-3 gap-2 text-sm">
                {schemaData.all_columns.map((col, idx) => (
                  <div key={idx} className="bg-gray-50 p-2 rounded">
                    <span className="font-medium">{col.COLUMN_NAME}</span>
                    <span className="text-gray-500 ml-2 text-xs">({col.DATA_TYPE})</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default InvoiceSchemaExplorer