import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { 
  Database, 
  RefreshCw, 
  CheckCircle2, 
  XCircle,
  AlertCircle
} from 'lucide-react'
import { apiUrl } from '@/lib/api'

const EquipmentSchemaChecker = () => {
  const [loading, setLoading] = useState(false)
  const [schemaData, setSchemaData] = useState(null)
  const [error, setError] = useState(null)

  const checkSchema = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/diagnostics/equipment-columns'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setSchemaData(data)
      } else {
        const errorData = await response.json()
        setError(errorData.error || 'Failed to fetch schema')
      }
    } catch (err) {
      setError('Network error: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const renderColumnIcon = (columnName) => {
    const problematicColumns = ['StockNo']
    const importantColumns = ['ID', 'SerialNo', 'Make', 'Model']
    
    if (problematicColumns.includes(columnName)) {
      return <XCircle className="h-4 w-4 text-red-500" />
    } else if (importantColumns.includes(columnName)) {
      return <CheckCircle2 className="h-4 w-4 text-green-500" />
    }
    return null
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center">
            <Database className="mr-3 h-8 w-8 text-blue-500" />
            Equipment Schema Checker
          </h1>
          <p className="text-muted-foreground">
            Diagnose Equipment table schema issues
          </p>
        </div>
        <Button onClick={checkSchema} disabled={loading}>
          {loading ? (
            <>
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              Checking...
            </>
          ) : (
            <>
              <Database className="mr-2 h-4 w-4" />
              Check Schema
            </>
          )}
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Results */}
      {schemaData && (
        <div className="space-y-6">
          {/* Summary Card */}
          <Card>
            <CardHeader>
              <CardTitle>Schema Summary</CardTitle>
              <CardDescription>
                Equipment table analysis results
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-2xl font-bold">
                    {schemaData.table_exists ? '✓' : '✗'} Table {schemaData.table_exists ? 'Exists' : 'Not Found'}
                  </div>
                  <p className="text-sm text-gray-500">ben002.Equipment</p>
                </div>
                <div>
                  <div className="text-2xl font-bold">{schemaData.total_columns || 0}</div>
                  <p className="text-sm text-gray-500">Total Columns</p>
                </div>
                <div>
                  <div className="text-2xl font-bold">
                    {schemaData.test_results?.StockNo === 'Column exists' ? '✓' : '✗'} StockNo
                  </div>
                  <p className="text-sm text-gray-500">
                    {schemaData.test_results?.StockNo || 'Not Found'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Column List */}
          <Card>
            <CardHeader>
              <CardTitle>Column Details</CardTitle>
              <CardDescription>
                All columns in the Equipment table
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Column Name</TableHead>
                      <TableHead>Data Type</TableHead>
                      <TableHead>Max Length</TableHead>
                      <TableHead>Nullable</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {schemaData.columns?.map((col, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            {renderColumnIcon(col.COLUMN_NAME)}
                            {col.COLUMN_NAME}
                          </div>
                        </TableCell>
                        <TableCell>{col.DATA_TYPE}</TableCell>
                        <TableCell>{col.CHARACTER_MAXIMUM_LENGTH || '-'}</TableCell>
                        <TableCell>
                          <Badge variant={col.IS_NULLABLE === 'YES' ? 'secondary' : 'default'}>
                            {col.IS_NULLABLE}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {col.COLUMN_NAME === 'StockNo' && (
                            <Badge className="bg-red-100 text-red-800">Issue Found</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* Sample Data */}
          {schemaData.sample_data && schemaData.sample_data.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Sample Data</CardTitle>
                <CardDescription>
                  First few rows from the Equipment table
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <pre className="bg-gray-100 p-4 rounded text-xs">
                    {JSON.stringify(schemaData.sample_data, null, 2)}
                  </pre>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Test Results */}
          <Card>
            <CardHeader>
              <CardTitle>Column Test Results</CardTitle>
              <CardDescription>
                Testing for expected column names
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(schemaData.test_results || {}).map(([col, result]) => (
                  <div key={col} className="flex items-center justify-between p-2 border rounded">
                    <span className="font-medium">{col}</span>
                    <Badge variant={result === 'Column exists' ? 'default' : 'destructive'}>
                      {result}
                    </Badge>
                  </div>
                ))}
              </div>
              {schemaData.test_results?.StockNo !== 'Column exists' && (
                <Alert className="mt-4 border-yellow-200 bg-yellow-50">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="text-yellow-800">
                    <strong>Action Required:</strong> The AI Query system expects a 'StockNo' column but it doesn't exist. 
                    Update the schema configuration to use the correct column name from the list above.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Initial State */}
      {!schemaData && !error && !loading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Database className="h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500 mb-4">Click "Check Schema" to analyze the Equipment table</p>
            <Button onClick={checkSchema}>
              <Database className="mr-2 h-4 w-4" />
              Check Schema
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default EquipmentSchemaChecker