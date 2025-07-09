import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Loader2, Database, Table, RefreshCw } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const DatabaseExplorer = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [schemaData, setSchemaData] = useState(null)
  const [detailedData, setDetailedData] = useState(null)

  const fetchSchemaSummary = async () => {
    setLoading(true)
    setError('')
    
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/database/schema-summary'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      const data = await response.json()
      
      if (response.ok) {
        setSchemaData(data)
      } else {
        setError(data.message || 'Failed to fetch schema')
      }
    } catch (err) {
      setError('Network error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const fetchDetailedExploration = async () => {
    setLoading(true)
    setError('')
    
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/database/explore'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      const data = await response.json()
      
      if (response.ok) {
        setDetailedData(data)
      } else {
        setError(data.message || 'Failed to fetch detailed exploration. Admin access may be required.')
      }
    } catch (err) {
      setError('Network error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSchemaSummary()
  }, [])

  const renderTableList = (tables, title) => {
    if (!tables || tables.length === 0) return null
    
    return (
      <div className="mb-6">
        <h4 className="font-semibold mb-2">{title}</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {tables.map((table, idx) => (
            <Badge key={idx} variant="secondary" className="justify-start">
              <Table className="w-3 h-3 mr-1" />
              {table}
            </Badge>
          ))}
        </div>
      </div>
    )
  }

  const renderKeyTable = (tableInfo) => {
    return (
      <Card key={tableInfo.table} className="mb-4">
        <CardHeader>
          <CardTitle className="text-lg">{tableInfo.table}</CardTitle>
          <CardDescription>{tableInfo.category}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h5 className="font-semibold mb-2">Columns ({tableInfo.columns?.length || 0})</h5>
              <div className="text-sm space-y-1">
                {tableInfo.columns?.slice(0, 10).map((col, idx) => (
                  <div key={idx} className="flex justify-between py-1 border-b">
                    <span className="font-mono">{col.COLUMN_NAME}</span>
                    <span className="text-muted-foreground">
                      {col.DATA_TYPE}
                      {col.CHARACTER_MAXIMUM_LENGTH && ` (${col.CHARACTER_MAXIMUM_LENGTH})`}
                    </span>
                  </div>
                ))}
                {tableInfo.columns?.length > 10 && (
                  <div className="text-muted-foreground text-center py-2">
                    ... and {tableInfo.columns.length - 10} more columns
                  </div>
                )}
              </div>
            </div>
            
            {tableInfo.sample_data && tableInfo.sample_data.length > 0 && (
              <div>
                <h5 className="font-semibold mb-2">Sample Data</h5>
                <div className="text-xs bg-muted p-2 rounded overflow-x-auto">
                  <pre>{JSON.stringify(tableInfo.sample_data[0], null, 2)}</pre>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="p-4">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Database Explorer</h2>
        <p className="text-muted-foreground">
          Explore the Softbase Evolution database structure
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex gap-2 mb-6">
        <Button 
          onClick={fetchSchemaSummary} 
          disabled={loading}
          variant="outline"
        >
          {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
          Refresh Schema
        </Button>
        <Button 
          onClick={fetchDetailedExploration} 
          disabled={loading}
        >
          {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Database className="w-4 h-4 mr-2" />}
          Detailed Exploration (Admin)
        </Button>
      </div>

      {schemaData && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Database Overview</CardTitle>
            <CardDescription>
              Connected to: {schemaData.status === 'connected' ? 'Azure SQL Database' : 'Unknown'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <Badge variant="outline" className="text-lg px-3 py-1">
                <Database className="w-4 h-4 mr-2" />
                {schemaData.total_tables} Total Tables
              </Badge>
            </div>
            
            {renderTableList(schemaData.categories?.customers, 'Customer Tables')}
            {renderTableList(schemaData.categories?.inventory, 'Inventory/Equipment Tables')}
            {renderTableList(schemaData.categories?.sales, 'Sales/Order Tables')}
            {renderTableList(schemaData.categories?.service, 'Service Tables')}
            {renderTableList(schemaData.categories?.parts, 'Parts Tables')}
          </CardContent>
        </Card>
      )}

      {detailedData && (
        <div>
          <h3 className="text-xl font-semibold mb-4">Detailed Table Analysis</h3>
          <Tabs defaultValue={detailedData.key_tables?.[0]?.category || 'overview'}>
            <TabsList className="mb-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              {detailedData.key_tables?.map((table) => (
                <TabsTrigger key={table.category} value={table.category}>
                  {table.category}
                </TabsTrigger>
              ))}
            </TabsList>
            
            <TabsContent value="overview">
              <Card>
                <CardHeader>
                  <CardTitle>Database Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div>
                      <span className="font-semibold">Server:</span> {detailedData.database_info?.server}
                    </div>
                    <div>
                      <span className="font-semibold">Database:</span> {detailedData.database_info?.database}
                    </div>
                    <div>
                      <span className="font-semibold">Total Tables:</span> {detailedData.total_tables}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            
            {detailedData.key_tables?.map((table) => (
              <TabsContent key={table.category} value={table.category}>
                {renderKeyTable(table)}
              </TabsContent>
            ))}
          </Tabs>
        </div>
      )}
    </div>
  )
}

export default DatabaseExplorer