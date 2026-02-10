import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Database, 
  Download,
  RefreshCw,
  FileText,
  Copy,
  CheckCircle2,
  AlertCircle,
  Table
} from 'lucide-react'
import { apiUrl } from '@/lib/api'

const DatabaseSchemaExporter = () => {
  const [loading, setLoading] = useState(false)
  const [schemaData, setSchemaData] = useState(null)
  const [error, setError] = useState(null)
  const [copiedTable, setCopiedTable] = useState(null)

  const fetchSchema = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/database/export-full-schema'), {
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

  const downloadMarkdown = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/database/export-schema-markdown'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `softbase_schema_${new Date().toISOString().split('T')[0]}.md`
        a.click()
        window.URL.revokeObjectURL(url)
      } else {
        setError('Failed to download markdown')
      }
    } catch (err) {
      setError('Download error: ' + err.message)
    }
  }

  const copyTableInfo = (tableName, tableInfo) => {
    const columns = tableInfo.columns.map(col => {
      let line = `- ${col.name} - ${col.type}`
      if (col.max_length) line += `(${col.max_length})`
      if (!col.nullable) line += ' NOT NULL'
      if (col.is_primary_key) line += ' [PK]'
      if (col.foreign_key) line += ` [FK -> ${col.foreign_key.references}]`
      return line
    }).join('\n')

    const text = `### ${tableName}
Type: ${tableInfo.type}
Rows: ${tableInfo.row_count}

Columns:
${columns}

Sample query:
\`\`\`sql
SELECT TOP 10 * FROM ben002.${tableName}
\`\`\``;

    navigator.clipboard.writeText(text)
    setCopiedTable(tableName)
    setTimeout(() => setCopiedTable(null), 2000)
  }

  const renderTableCard = (tableName, tableInfo) => {
    const hasStockNo = tableInfo.columns.some(col => col.name === 'StockNo')
    const isEquipmentTable = tableName === 'Equipment'
    
    return (
      <Card key={tableName} className={isEquipmentTable && !hasStockNo ? 'border-red-200' : ''}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <Table className="h-4 w-4" />
                {tableName}
                {isEquipmentTable && !hasStockNo && (
                  <Badge variant="destructive" className="ml-2">Missing StockNo</Badge>
                )}
              </CardTitle>
              <CardDescription>
                {tableInfo.type} • {tableInfo.row_count?.toLocaleString() || 'N/A'} rows • {tableInfo.columns.length} columns
              </CardDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => copyTableInfo(tableName, tableInfo)}
            >
              {copiedTable === tableName ? (
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-1 text-sm">
            {tableInfo.primary_keys.length > 0 && (
              <div className="flex items-center gap-2 text-blue-600">
                <Badge variant="outline" className="text-xs">PK</Badge>
                {tableInfo.primary_keys.join(', ')}
              </div>
            )}
            <div className="grid grid-cols-2 gap-1 mt-2">
              {tableInfo.columns.slice(0, 10).map((col, idx) => (
                <div key={idx} className="text-gray-600 text-xs">
                  • {col.name} ({col.type}{col.max_length ? `(${col.max_length})` : ''})
                </div>
              ))}
              {tableInfo.columns.length > 10 && (
                <div className="text-gray-400 text-xs col-span-2">
                  ... and {tableInfo.columns.length - 10} more columns
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center">
            <Database className="mr-3 h-8 w-8 text-blue-500" />
            Database Schema Exporter
          </h1>
          <p className="text-muted-foreground">
            Export complete database schema documentation for CLAUDE.md
          </p>
        </div>
        <div className="flex gap-2">
          {schemaData && (
            <Button onClick={downloadMarkdown} variant="outline">
              <FileText className="mr-2 h-4 w-4" />
              Download Markdown
            </Button>
          )}
          <Button onClick={fetchSchema} disabled={loading}>
            {loading ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Loading Schema...
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

      {/* Error Alert */}
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Schema Data */}
      {schemaData && (
        <div className="space-y-6">
          {/* Summary Card */}
          <Card>
            <CardHeader>
              <CardTitle>Schema Summary</CardTitle>
              <CardDescription>
                Schema: {schemaData.schema_name} • Exported: {new Date(schemaData.export_date).toLocaleString()}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold">{schemaData.summary.total_tables}</div>
                  <p className="text-sm text-gray-500">Total Tables</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">{schemaData.summary.total_columns}</div>
                  <p className="text-sm text-gray-500">Total Columns</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">{schemaData.summary.base_tables}</div>
                  <p className="text-sm text-gray-500">Base Tables</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">{schemaData.summary.views}</div>
                  <p className="text-sm text-gray-500">Views</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tables Grid */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">All Tables</h2>
              <p className="text-sm text-gray-500">Click copy button to copy table info for CLAUDE.md</p>
            </div>
            
            <Tabs defaultValue="all" className="w-full">
              <TabsList>
                <TabsTrigger value="all">All Tables</TabsTrigger>
                <TabsTrigger value="common">Common Tables</TabsTrigger>
                <TabsTrigger value="large">Large Tables</TabsTrigger>
              </TabsList>
              
              <TabsContent value="all" className="mt-4">
                <ScrollArea className="h-[600px]">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pr-4">
                    {Object.entries(schemaData.tables)
                      .sort(([a], [b]) => a.localeCompare(b))
                      .map(([tableName, tableInfo]) => renderTableCard(tableName, tableInfo))}
                  </div>
                </ScrollArea>
              </TabsContent>
              
              <TabsContent value="common" className="mt-4">
                <ScrollArea className="h-[600px]">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pr-4">
                    {Object.entries(schemaData.tables)
                      .filter(([name]) => ['Customer', 'Equipment', 'InvoiceReg', 'WO', 'Parts', 'ServiceClaim'].includes(name))
                      .sort(([a], [b]) => a.localeCompare(b))
                      .map(([tableName, tableInfo]) => renderTableCard(tableName, tableInfo))}
                  </div>
                </ScrollArea>
              </TabsContent>
              
              <TabsContent value="large" className="mt-4">
                <ScrollArea className="h-[600px]">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pr-4">
                    {Object.entries(schemaData.tables)
                      .filter(([, info]) => info.row_count > 1000)
                      .sort(([, a], [, b]) => b.row_count - a.row_count)
                      .map(([tableName, tableInfo]) => renderTableCard(tableName, tableInfo))}
                  </div>
                </ScrollArea>
              </TabsContent>
            </Tabs>
          </div>

          {/* Instructions */}
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>To update CLAUDE.md:</strong> Click "Download Markdown" to get the complete schema documentation, 
              then replace the database schema section in CLAUDE.md with the downloaded content. 
              You can also copy individual table information using the copy button on each card.
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Initial State */}
      {!schemaData && !error && !loading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Database className="h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500 mb-4">Click "Load Schema" to fetch complete database documentation</p>
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

export default DatabaseSchemaExporter