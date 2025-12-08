import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { apiUrl } from '@/lib/api'

const SchemaExplorer = () => {
  const [tableName, setTableName] = useState('')
  const [recordId, setRecordId] = useState('')
  const [idColumn, setIdColumn] = useState('Number')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const exploreTable = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const url = recordId
        ? apiUrl(`/api/schema/record/${tableName}/${recordId}?id_column=${idColumn}`)
        : apiUrl(`/api/schema/table/${tableName}`)

      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await response.json()

      if (data.success) {
        setResult(data)
      } else {
        setError(data.error || 'Query failed')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6">
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Schema Explorer - Query Any Table</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Table Name</label>
              <Input
                value={tableName}
                onChange={(e) => setTableName(e.target.value)}
                placeholder="e.g., InvoiceReg, Salesman, Customer"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Record ID (optional)</label>
                <Input
                  value={recordId}
                  onChange={(e) => setRecordId(e.target.value)}
                  placeholder="e.g., 110000014"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">ID Column</label>
                <Input
                  value={idColumn}
                  onChange={(e) => setIdColumn(e.target.value)}
                  placeholder="e.g., Number, InvoiceNo"
                />
              </div>
            </div>
            <Button onClick={exploreTable} disabled={loading || !tableName}>
              {loading ? 'Loading...' : 'Explore Table'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Card className="mb-6 border-red-500">
          <CardContent className="p-4">
            <p className="text-red-600">Error: {error}</p>
          </CardContent>
        </Card>
      )}

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>{result.table} {recordId ? `- Record ${recordId}` : '- Structure'}</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-gray-50 p-4 rounded overflow-auto max-h-[600px] text-sm">
              {JSON.stringify(result, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default SchemaExplorer
