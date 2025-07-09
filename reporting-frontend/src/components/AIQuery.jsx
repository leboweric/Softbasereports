import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Send, 
  Sparkles, 
  History, 
  Lightbulb, 
  Search,
  Download,
  Eye,
  Clock,
  MessageSquare
} from 'lucide-react'
import { apiUrl } from '@/lib/api'

const AIQuery = () => {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const [history, setHistory] = useState([])
  const [activeTab, setActiveTab] = useState('query')

  useEffect(() => {
    fetchSuggestions()
    fetchHistory()
  }, [])

  const fetchSuggestions = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/ai/suggestions'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setSuggestions(data.suggestions || [])
      }
    } catch (error) {
      console.error('Failed to fetch suggestions:', error)
    }
  }

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/ai/query-history'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setHistory(data.history || [])
      }
    } catch (error) {
      console.error('Failed to fetch history:', error)
    }
  }

  const executeQuery = async () => {
    if (!query.trim()) return

    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/ai/query'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query.trim() }),
      })

      if (response.ok) {
        const data = await response.json()
        setResults(data)
        setActiveTab('results')
        // Refresh history
        fetchHistory()
      } else {
        const error = await response.json()
        setResults({ error: error.error || 'Query failed' })
      }
    } catch (error) {
      setResults({ error: 'Network error occurred' })
    } finally {
      setLoading(false)
    }
  }

  const validateQuery = async () => {
    if (!query.trim()) return

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/ai/validate-query'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query.trim() }),
      })

      if (response.ok) {
        const data = await response.json()
        alert(`Query Type: ${data.query_type}\nFields: ${data.estimated_fields.join(', ')}\nSQL: ${data.sql_query}`)
      }
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const useSuggestion = (suggestionQuery) => {
    setQuery(suggestionQuery)
    setActiveTab('query')
  }

  const useHistoryQuery = (historyQuery) => {
    setQuery(historyQuery)
    setActiveTab('query')
  }

  const exportResults = () => {
    if (!results?.results) return

    const csv = [
      Object.keys(results.results[0]).join(','),
      ...results.results.map(row => 
        Object.values(row).map(val => 
          typeof val === 'string' && val.includes(',') ? `"${val}"` : val
        ).join(',')
      )
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'ai-query-results.csv'
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const renderResults = () => {
    if (!results) return null

    if (results.error) {
      return (
        <Alert className="border-red-200 bg-red-50">
          <AlertDescription className="text-red-800">
            {results.error}
          </AlertDescription>
        </Alert>
      )
    }

    if (!results.results || results.results.length === 0) {
      return (
        <Alert>
          <AlertDescription>
            No results found for your query.
          </AlertDescription>
        </Alert>
      )
    }

    return (
      <div className="space-y-4">
        {/* Query Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Sparkles className="mr-2 h-5 w-5 text-blue-500" />
              AI Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <strong>Your Question:</strong>
                <p className="text-gray-600 italic">"{results.query}"</p>
              </div>
              <div>
                <strong>AI Explanation:</strong>
                <p className="text-gray-700">{results.explanation}</p>
              </div>
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                <span>Found {results.result_count} results</span>
                <span>Query Type: {results.parsed_params?.query_type}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results Table */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Results</CardTitle>
              <Button onClick={exportResults} variant="outline" size="sm">
                <Download className="mr-2 h-4 w-4" />
                Export CSV
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border max-h-96 overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    {Object.keys(results.results[0]).map((header) => (
                      <TableHead key={header} className="font-medium">
                        {header.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.results.map((row, index) => (
                    <TableRow key={index}>
                      {Object.values(row).map((value, cellIndex) => (
                        <TableCell key={cellIndex}>
                          {typeof value === 'number' && value > 1000 
                            ? new Intl.NumberFormat().format(value)
                            : String(value)
                          }
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Technical Details (Collapsible) */}
        <details className="group">
          <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
            View Technical Details
          </summary>
          <Card className="mt-2">
            <CardContent className="pt-4">
              <div className="space-y-2 text-sm">
                <div>
                  <strong>Generated SQL:</strong>
                  <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
                    {results.sql_query}
                  </pre>
                </div>
                <div>
                  <strong>Parsed Parameters:</strong>
                  <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
                    {JSON.stringify(results.parsed_params, null, 2)}
                  </pre>
                </div>
              </div>
            </CardContent>
          </Card>
        </details>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center">
            <Sparkles className="mr-3 h-8 w-8 text-blue-500" />
            AI Query Assistant
          </h1>
          <p className="text-muted-foreground">
            Ask questions about your business data in plain English
          </p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="query" className="flex items-center">
            <MessageSquare className="mr-2 h-4 w-4" />
            Ask Question
          </TabsTrigger>
          <TabsTrigger value="suggestions" className="flex items-center">
            <Lightbulb className="mr-2 h-4 w-4" />
            Examples
          </TabsTrigger>
          <TabsTrigger value="history" className="flex items-center">
            <History className="mr-2 h-4 w-4" />
            History
          </TabsTrigger>
          <TabsTrigger value="results" className="flex items-center">
            <Search className="mr-2 h-4 w-4" />
            Results
          </TabsTrigger>
        </TabsList>

        <TabsContent value="query" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Ask Your Question</CardTitle>
              <CardDescription>
                Type your question in natural language. For example: "Which Linde parts were we not able to fill last week?"
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Textarea
                  placeholder="Type your question here... (e.g., 'Show me all Toyota forklift sales from last month')"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="min-h-[100px]"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                      executeQuery()
                    }
                  }}
                />
                <div className="flex items-center space-x-2">
                  <Button 
                    onClick={executeQuery} 
                    disabled={loading || !query.trim()}
                    className="flex items-center"
                  >
                    {loading ? (
                      <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    ) : (
                      <Send className="mr-2 h-4 w-4" />
                    )}
                    {loading ? 'Processing...' : 'Ask AI'}
                  </Button>
                  <Button 
                    onClick={validateQuery} 
                    variant="outline"
                    disabled={!query.trim()}
                    className="flex items-center"
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    Preview
                  </Button>
                </div>
                <p className="text-xs text-gray-500">
                  Tip: Press Ctrl+Enter to submit your question quickly
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="suggestions" className="space-y-4">
          {suggestions.map((category, index) => (
            <Card key={index}>
              <CardHeader>
                <CardTitle className="text-lg">{category.category}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2">
                  {category.queries.map((suggestion, qIndex) => (
                    <Button
                      key={qIndex}
                      variant="ghost"
                      className="justify-start h-auto p-3 text-left"
                      onClick={() => useSuggestion(suggestion)}
                    >
                      <div>
                        <div className="font-medium">{suggestion}</div>
                      </div>
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Queries</CardTitle>
              <CardDescription>
                Your recent AI queries and results
              </CardDescription>
            </CardHeader>
            <CardContent>
              {history.length > 0 ? (
                <div className="space-y-3">
                  {history.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
                      onClick={() => useHistoryQuery(item.query)}
                    >
                      <div className="flex-1">
                        <div className="font-medium">{item.query}</div>
                        <div className="text-sm text-gray-500 flex items-center mt-1">
                          <Clock className="mr-1 h-3 w-3" />
                          {new Date(item.timestamp).toLocaleDateString()}
                          <span className="ml-4">
                            {item.result_count} results
                          </span>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm">
                        Use Query
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No query history yet. Start by asking a question!
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          {results ? (
            renderResults()
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center py-12">
                <div className="text-center text-gray-500">
                  <Search className="mx-auto h-12 w-12 mb-4 opacity-50" />
                  <p>No results yet. Ask a question to see results here.</p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default AIQuery

