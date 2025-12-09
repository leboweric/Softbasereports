import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { apiUrl } from '@/lib/api'
import { Database, Play, Copy, Download } from 'lucide-react'

const SchemaExplorer = () => {
  const [tableName, setTableName] = useState('')
  const [recordId, setRecordId] = useState('')
  const [idColumn, setIdColumn] = useState('Number')
  const [customQuery, setCustomQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [queryHistory, setQueryHistory] = useState([])

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

  const executeCustomQuery = async () => {
    if (!customQuery.trim()) {
      setError('Please enter a SQL query')
      return
    }

    setLoading(true)
    setError(null)
    const startTime = Date.now()
    
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/schema/query'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: customQuery })
      })
      const data = await response.json()
      const executionTime = Date.now() - startTime

      if (data.success) {
        setResult({ ...data, executionTime })
        setQueryHistory(prev => [{
          query: customQuery,
          timestamp: new Date().toLocaleString(),
          rowCount: data.count,
          executionTime
        }, ...prev.slice(0, 9)]) // Keep last 10 queries
      } else {
        setError(data.error || 'Query failed')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
  }

  const downloadCSV = () => {
    if (!result?.results || result.results.length === 0) return

    const headers = Object.keys(result.results[0])
    const csv = [
      headers.join(','),
      ...result.results.map(row => 
        headers.map(h => {
          const val = row[h]
          return typeof val === 'string' && val.includes(',') ? `"${val}"` : val
        }).join(',')
      )
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `query_results_${Date.now()}.csv`
    a.click()
  }

  const loadSampleQuery = (query) => {
    setCustomQuery(query)
  }

  const sampleQueries = [
    {
      name: 'Check FMBILL Customers (Jake\'s List)',
      query: `SELECT 
  i.BillTo,
  i.ShipTo,
  c.Name as BillToName,
  sc.Name as ShipToName,
  COUNT(*) as invoice_count,
  SUM(COALESCE(i.LaborTaxable, 0) + COALESCE(i.LaborNonTax, 0) + 
      COALESCE(i.PartsTaxable, 0) + COALESCE(i.PartsNonTax, 0) + 
      COALESCE(i.MiscTaxable, 0) + COALESCE(i.MiscNonTax, 0)) as total_revenue
FROM [ben002].InvoiceReg i
LEFT JOIN [ben002].Customer c ON i.BillTo = c.Number
LEFT JOIN [ben002].Customer sc ON i.ShipTo = sc.Number
WHERE i.SaleCode = 'FMBILL'
  AND i.InvoiceDate >= DATEADD(month, -13, GETDATE())
  AND (i.BillTo IN ('48560', '30300', '63700', '34731', '90621', '58095', '58090', '92750', '20250', '16931')
       OR i.ShipTo IN ('48560', '30300', '63700', '34731', '90621', '58095', '58090', '92750', '20250', '16931'))
GROUP BY i.BillTo, i.ShipTo, c.Name, sc.Name
ORDER BY total_revenue DESC`
    },
    {
      name: 'All FMBILL Customers (Current Report)',
      query: `SELECT 
  i.BillTo as customer_number,
  c.Name as customer_name,
  COUNT(*) as invoice_count,
  SUM(COALESCE(i.LaborTaxable, 0) + COALESCE(i.LaborNonTax, 0) +
      COALESCE(i.PartsTaxable, 0) + COALESCE(i.PartsNonTax, 0) +
      COALESCE(i.MiscTaxable, 0) + COALESCE(i.MiscNonTax, 0)) as total_revenue,
  MIN(i.InvoiceDate) as first_invoice,
  MAX(i.InvoiceDate) as last_invoice
FROM [ben002].InvoiceReg i
LEFT JOIN [ben002].Customer c ON i.BillTo = c.Number
WHERE i.SaleCode = 'FMBILL'
  AND i.BillTo NOT IN ('78960', '89410')
  AND i.InvoiceDate >= DATEADD(month, -13, GETDATE())
GROUP BY i.BillTo, c.Name
ORDER BY total_revenue DESC`
    },
    {
      name: 'FMBILL by ShipTo Location',
      query: `SELECT 
  i.ShipTo as customer_number,
  c.Name as customer_name,
  i.BillTo as billed_to,
  bc.Name as billto_name,
  COUNT(*) as invoice_count,
  SUM(COALESCE(i.LaborTaxable, 0) + COALESCE(i.LaborNonTax, 0) +
      COALESCE(i.PartsTaxable, 0) + COALESCE(i.PartsNonTax, 0) +
      COALESCE(i.MiscTaxable, 0) + COALESCE(i.MiscNonTax, 0)) as total_revenue
FROM [ben002].InvoiceReg i
LEFT JOIN [ben002].Customer c ON i.ShipTo = c.Number
LEFT JOIN [ben002].Customer bc ON i.BillTo = bc.Number
WHERE i.SaleCode = 'FMBILL'
  AND i.InvoiceDate >= DATEADD(month, -13, GETDATE())
GROUP BY i.ShipTo, c.Name, i.BillTo, bc.Name
ORDER BY total_revenue DESC`
    }
  ]

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-2 mb-6">
        <Database className="h-6 w-6" />
        <h1 className="text-2xl font-bold">Database Schema Explorer</h1>
      </div>

      <Tabs defaultValue="sql" className="space-y-4">
        <TabsList>
          <TabsTrigger value="sql">SQL Query</TabsTrigger>
          <TabsTrigger value="table">Table Explorer</TabsTrigger>
          <TabsTrigger value="history">Query History</TabsTrigger>
        </TabsList>

        <TabsContent value="sql" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Custom SQL Query</span>
                <span className="text-sm font-normal text-gray-500">
                  Read-only SELECT queries only
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">SQL Query</label>
                <Textarea
                  value={customQuery}
                  onChange={(e) => setCustomQuery(e.target.value)}
                  placeholder="SELECT * FROM [ben002].InvoiceReg WHERE SaleCode = 'FMBILL' LIMIT 10"
                  className="font-mono text-sm min-h-[200px]"
                  spellCheck={false}
                />
              </div>

              <div className="flex gap-2">
                <Button 
                  onClick={executeCustomQuery} 
                  disabled={loading || !customQuery.trim()}
                  className="flex items-center gap-2"
                >
                  <Play className="h-4 w-4" />
                  {loading ? 'Executing...' : 'Execute Query'}
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => setCustomQuery('')}
                  disabled={!customQuery}
                >
                  Clear
                </Button>
                {result?.results && (
                  <Button 
                    variant="outline" 
                    onClick={downloadCSV}
                    className="flex items-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    Download CSV
                  </Button>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Sample Queries</label>
                <div className="grid grid-cols-1 gap-2">
                  {sampleQueries.map((sq, idx) => (
                    <Button
                      key={idx}
                      variant="outline"
                      size="sm"
                      onClick={() => loadSampleQuery(sq.query)}
                      className="justify-start text-left h-auto py-2"
                    >
                      {sq.name}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {error && (
            <Card className="border-red-500">
              <CardContent className="p-4">
                <p className="text-red-600 font-mono text-sm">{error}</p>
              </CardContent>
            </Card>
          )}

          {result?.results && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Query Results</span>
                  <div className="text-sm font-normal text-gray-500 flex gap-4">
                    <span>{result.count} rows</span>
                    {result.executionTime && <span>{result.executionTime}ms</span>}
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        {Object.keys(result.results[0] || {}).map((header) => (
                          <th key={header} className="text-left p-2 font-medium">
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.results.map((row, idx) => (
                        <tr key={idx} className="border-b hover:bg-gray-50">
                          {Object.values(row).map((val, vidx) => (
                            <td key={vidx} className="p-2 font-mono text-xs">
                              {val === null ? <span className="text-gray-400">NULL</span> : String(val)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="table" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Query Specific Table</CardTitle>
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
                      placeholder="Number"
                    />
                  </div>
                </div>
                <Button onClick={exploreTable} disabled={loading || !tableName}>
                  {loading ? 'Loading...' : 'Explore Table'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {result && !result.results && (
            <Card>
              <CardHeader>
                <CardTitle>{result.table} {recordId ? `- Record ${recordId}` : '- Structure'}</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="bg-gray-50 p-4 rounded overflow-auto max-h-[600px] text-sm font-mono">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Query History</CardTitle>
            </CardHeader>
            <CardContent>
              {queryHistory.length === 0 ? (
                <p className="text-gray-500">No queries executed yet</p>
              ) : (
                <div className="space-y-4">
                  {queryHistory.map((item, idx) => (
                    <div key={idx} className="border rounded p-3 space-y-2">
                      <div className="flex justify-between text-sm text-gray-500">
                        <span>{item.timestamp}</span>
                        <span>{item.rowCount} rows • {item.executionTime}ms</span>
                      </div>
                      <pre className="bg-gray-50 p-2 rounded text-xs font-mono overflow-x-auto">
                        {item.query}
                      </pre>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => loadSampleQuery(item.query)}
                        className="flex items-center gap-2"
                      >
                        <Copy className="h-3 w-3" />
                        Load Query
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default SchemaExplorer
