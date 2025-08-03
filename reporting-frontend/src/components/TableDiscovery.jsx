import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Database, 
  RefreshCw,
  Search,
  Download,
  CheckCircle2,
  AlertCircle,
  Table,
  Copy,
  ChevronDown,
  ChevronRight
} from 'lucide-react'
import { apiUrl } from '@/lib/api'

const TableDiscovery = () => {
  const [loading, setLoading] = useState(false)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [tables, setTables] = useState(null)
  const [selectedTables, setSelectedTables] = useState(new Set())
  const [tableDetails, setTableDetails] = useState({})
  const [error, setError] = useState(null)
  const [copiedTable, setCopiedTable] = useState(null)
  const [expandedTables, setExpandedTables] = useState(new Set())

  const fetchTables = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/database/list-tables'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setTables(data)
      } else {
        const errorData = await response.json()
        setError(errorData.error || 'Failed to fetch tables')
      }
    } catch (err) {
      setError('Network error: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchTableDetails = async () => {
    if (selectedTables.size === 0) {
      setError('Please select at least one table')
      return
    }

    setLoadingDetails(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/database/table-details'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tables: Array.from(selectedTables)
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setTableDetails(data.tables)
      } else {
        const errorData = await response.json()
        setError(errorData.error || 'Failed to fetch table details')
      }
    } catch (err) {
      setError('Network error: ' + err.message)
    } finally {
      setLoadingDetails(false)
    }
  }

  const exportSelectedSchema = async () => {
    if (selectedTables.size === 0) {
      setError('Please select at least one table')
      return
    }

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/database/export-selected-schema'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tables: Array.from(selectedTables)
        }),
      })

      if (response.ok) {
        const data = await response.json()
        const blob = new Blob([data.markdown], { type: 'text/markdown' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `softbase_schema_${new Date().toISOString().split('T')[0]}.md`
        a.click()
        window.URL.revokeObjectURL(url)
      } else {
        setError('Failed to export schema')
      }
    } catch (err) {
      setError('Export error: ' + err.message)
    }
  }

  const toggleTableSelection = (tableName) => {
    const newSelected = new Set(selectedTables)
    if (newSelected.has(tableName)) {
      newSelected.delete(tableName)
    } else {
      newSelected.add(tableName)
    }
    setSelectedTables(newSelected)
  }

  const selectAll = (tableList) => {
    const newSelected = new Set(selectedTables)
    tableList.forEach(table => newSelected.add(table.name))
    setSelectedTables(newSelected)
  }

  const deselectAll = (tableList) => {
    const newSelected = new Set(selectedTables)
    tableList.forEach(table => newSelected.delete(table.name))
    setSelectedTables(newSelected)
  }

  const copyTableSchema = (tableName, details) => {
    if (!details || details.error) return

    let text = `### ${tableName}\n`
    text += `Rows: ${details.row_count || 'Unknown'}\n\n`
    text += 'Columns:\n'
    
    details.columns.forEach(col => {
      let line = `- ${col.name} - ${col.type}`
      if (col.max_length) line += `(${col.max_length})`
      if (!col.nullable) line += ' NOT NULL'
      if (col.is_primary_key) line += ' [PK]'
      text += line + '\n'
    })

    navigator.clipboard.writeText(text)
    setCopiedTable(tableName)
    setTimeout(() => setCopiedTable(null), 2000)
  }

  const toggleTableExpanded = (tableName) => {
    const newExpanded = new Set(expandedTables)
    if (newExpanded.has(tableName)) {
      newExpanded.delete(tableName)
    } else {
      newExpanded.add(tableName)
    }
    setExpandedTables(newExpanded)
  }

  const renderTableList = (tableList, title) => (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{tableList.length} tables</CardDescription>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => selectAll(tableList)}>
              Select All
            </Button>
            <Button size="sm" variant="outline" onClick={() => deselectAll(tableList)}>
              Deselect All
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px]">
          <div className="space-y-2">
            {tableList.map((table) => (
              <div
                key={table.name}
                className="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded"
              >
                <Checkbox
                  checked={selectedTables.has(table.name)}
                  onCheckedChange={() => toggleTableSelection(table.name)}
                />
                <div className="flex-1">
                  <span className="font-medium">{table.name}</span>
                  <span className="text-sm text-gray-500 ml-2">
                    ({table.column_count} columns)
                  </span>
                </div>
                {tableDetails[table.name] && (
                  <Badge variant="secondary">Loaded</Badge>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )

  const renderTableDetails = () => {
    const detailedTables = Array.from(selectedTables).filter(name => tableDetails[name])
    
    if (detailedTables.length === 0) {
      return (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Select tables and click "Load Selected Tables" to view details
          </AlertDescription>
        </Alert>
      )
    }

    return (
      <div className="space-y-4">
        {detailedTables.map((tableName) => {
          const details = tableDetails[tableName]
          const isExpanded = expandedTables.has(tableName)
          
          if (details.error) {
            return (
              <Card key={tableName} className="border-red-200">
                <CardHeader>
                  <CardTitle className="text-red-600">{tableName}</CardTitle>
                  <CardDescription>Error: {details.error}</CardDescription>
                </CardHeader>
              </Card>
            )
          }

          return (
            <Card key={tableName}>
              <CardHeader 
                className="cursor-pointer"
                onClick={() => toggleTableExpanded(tableName)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      {tableName}
                    </CardTitle>
                    <CardDescription>
                      {details.row_count !== null ? `${details.row_count.toLocaleString()} rows • ` : ''}
                      {details.columns.length} columns
                      {details.primary_keys.length > 0 && ` • PK: ${details.primary_keys.join(', ')}`}
                    </CardDescription>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation()
                      copyTableSchema(tableName, details)
                    }}
                  >
                    {copiedTable === tableName ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </CardHeader>
              {isExpanded && (
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium mb-2">Columns:</h4>
                      <div className="bg-gray-50 rounded p-3 font-mono text-sm space-y-1">
                        {details.columns.map((col, idx) => (
                          <div key={idx}>
                            {col.name} - {col.type}
                            {col.max_length && `(${col.max_length})`}
                            {!col.nullable && ' NOT NULL'}
                            {col.is_primary_key && ' [PK]'}
                          </div>
                        ))}
                      </div>
                    </div>
                    {details.sample_data && details.sample_data.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">Sample Data:</h4>
                        <div className="overflow-x-auto">
                          <pre className="bg-gray-50 rounded p-3 text-xs">
                            {JSON.stringify(details.sample_data, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              )}
            </Card>
          )
        })}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center">
            <Database className="mr-3 h-8 w-8 text-blue-500" />
            Table Discovery
          </h1>
          <p className="text-muted-foreground">
            Discover and document all database tables
          </p>
        </div>
        <div className="flex gap-2">
          {selectedTables.size > 0 && (
            <>
              <Badge variant="secondary" className="text-lg">
                {selectedTables.size} selected
              </Badge>
              <Button 
                onClick={exportSelectedSchema} 
                variant="outline"
                disabled={selectedTables.size === 0}
              >
                <Download className="mr-2 h-4 w-4" />
                Export Selected
              </Button>
            </>
          )}
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

      {/* Step 1: Discover Tables */}
      {!tables && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Database className="h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500 mb-4">Start by discovering all tables in the database</p>
            <Button onClick={fetchTables} disabled={loading}>
              {loading ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Discovering...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Discover Tables
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Select Tables */}
      {tables && (
        <>
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Select Tables to Document</h2>
            <Button 
              onClick={fetchTableDetails} 
              disabled={loadingDetails || selectedTables.size === 0}
            >
              {loadingDetails ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  <Table className="mr-2 h-4 w-4" />
                  Load Selected Tables
                </>
              )}
            </Button>
          </div>

          <Tabs defaultValue="tables" className="w-full">
            <TabsList>
              <TabsTrigger value="tables">Tables ({tables.total_tables})</TabsTrigger>
              <TabsTrigger value="views">Views ({tables.total_views})</TabsTrigger>
              <TabsTrigger value="details">Table Details</TabsTrigger>
            </TabsList>

            <TabsContent value="tables">
              {renderTableList(tables.base_tables, "Base Tables")}
            </TabsContent>

            <TabsContent value="views">
              {renderTableList(tables.views, "Views")}
            </TabsContent>

            <TabsContent value="details">
              {renderTableDetails()}
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  )
}

export default TableDiscovery