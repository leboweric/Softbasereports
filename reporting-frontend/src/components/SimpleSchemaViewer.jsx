import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Database, 
  RefreshCw,
  Copy,
  CheckCircle2
} from 'lucide-react'
import { apiUrl } from '@/lib/api'

const SimpleSchemaViewer = () => {
  const [loading, setLoading] = useState(false)
  const [schemaData, setSchemaData] = useState(null)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  const fetchSchema = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/database/simple-schema'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setSchemaData(data.schema)
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

  const copyAllSchema = () => {
    if (!schemaData) return

    let markdown = '# Softbase Database Schema\n\n'
    markdown += 'Schema: ben002\n\n'

    Object.entries(schemaData).forEach(([tableName, tableInfo]) => {
      if (tableInfo.error) {
        markdown += `\n## ${tableName}\nError: ${tableInfo.error}\n`
        return
      }

      markdown += `\n## ${tableName}\n`
      markdown += `Rows: ${tableInfo.row_count}\n\n`
      markdown += 'Columns:\n'
      
      tableInfo.columns.forEach(col => {
        let line = `- ${col.name} - ${col.type}`
        if (col.max_length) line += `(${col.max_length})`
        if (!col.nullable) line += ' NOT NULL'
        markdown += line + '\n'
      })
    })

    navigator.clipboard.writeText(markdown)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center">
            <Database className="mr-3 h-8 w-8 text-blue-500" />
            Simple Schema Viewer
          </h1>
          <p className="text-muted-foreground">
            Essential tables schema for CLAUDE.md
          </p>
        </div>
        <div className="flex gap-2">
          {schemaData && (
            <Button onClick={copyAllSchema} variant="outline">
              {copied ? (
                <>
                  <CheckCircle2 className="mr-2 h-4 w-4 text-green-500" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="mr-2 h-4 w-4" />
                  Copy All
                </>
              )}
            </Button>
          )}
          <Button onClick={fetchSchema} disabled={loading}>
            {loading ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Loading...
              </>
            ) : (
              <>
                <Database className="mr-2 h-4 w-4" />
                Load Schema
              </>
            )}
          </Button>
        </div>
      </div>

      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {schemaData && (
        <div className="space-y-4">
          {Object.entries(schemaData).map(([tableName, tableInfo]) => (
            <Card key={tableName}>
              <CardHeader>
                <CardTitle>{tableName}</CardTitle>
                {!tableInfo.error && (
                  <CardDescription>
                    {tableInfo.row_count} rows • {tableInfo.columns.length} columns
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent>
                {tableInfo.error ? (
                  <Alert>
                    <AlertDescription>{tableInfo.error}</AlertDescription>
                  </Alert>
                ) : (
                  <div className="font-mono text-sm space-y-1">
                    {tableInfo.columns.map((col, idx) => (
                      <div key={idx}>
                        {col.name} - {col.type}
                        {col.max_length && `(${col.max_length})`}
                        {!col.nullable && ' NOT NULL'}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!schemaData && !loading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Database className="h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500 mb-4">Click "Load Schema" to fetch essential tables</p>
            <Button onClick={fetchSchema}>
              <Database className="mr-2 h-4 w-4" />
              Load Schema
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default SimpleSchemaViewer