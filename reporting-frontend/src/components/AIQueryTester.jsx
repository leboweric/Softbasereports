import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Play, 
  CheckCircle2, 
  XCircle, 
  AlertCircle,
  Download,
  RefreshCw,
  ChevronRight,
  Clock,
  BarChart3
} from 'lucide-react'
import { apiUrl } from '@/lib/api'

const AIQueryTester = () => {
  const [loading, setLoading] = useState(false)
  const [testResults, setTestResults] = useState(null)
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [expandedQueries, setExpandedQueries] = useState({})

  const runTests = async (category = null) => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/ai-test/test-all'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ category: category === 'all' ? null : category }),
      })

      if (response.ok) {
        const data = await response.json()
        setTestResults(data)
      } else {
        console.error('Failed to run tests')
      }
    } catch (error) {
      console.error('Error running tests:', error)
    } finally {
      setLoading(false)
    }
  }

  const exportResults = () => {
    if (!testResults) return

    const csvData = []
    csvData.push(['Category', 'Query', 'Status', 'Expected Type', 'Actual Type', 'Row Count', 'Execution Time', 'Error'])

    Object.entries(testResults.results).forEach(([category, queries]) => {
      queries.forEach((result) => {
        csvData.push([
          category,
          result.query,
          result.status,
          result.expected_type,
          result.actual_type || 'N/A',
          result.row_count,
          result.execution_time,
          result.error || ''
        ])
      })
    })

    const csv = csvData.map(row => row.map(cell => 
      typeof cell === 'string' && cell.includes(',') ? `"${cell}"` : cell
    ).join(',')).join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ai-query-test-results-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'passed':
        return <Badge className="bg-green-100 text-green-800">Passed</Badge>
      case 'partial':
        return <Badge className="bg-yellow-100 text-yellow-800">Partial</Badge>
      case 'failed':
        return <Badge className="bg-red-100 text-red-800">Failed</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'passed':
        return <CheckCircle2 className="h-5 w-5 text-green-600" />
      case 'partial':
        return <AlertCircle className="h-5 w-5 text-yellow-600" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />
      default:
        return null
    }
  }

  const renderQueryResult = (result, index, category) => {
    const isExpanded = expandedQueries[`${category}-${index}`]
    const toggleExpanded = () => {
      setExpandedQueries(prev => ({
        ...prev,
        [`${category}-${index}`]: !prev[`${category}-${index}`]
      }))
    }

    return (
      <div key={index} className="border rounded-lg p-4 mb-3 hover:bg-gray-50">
        <div 
          className="flex items-start justify-between cursor-pointer"
          onClick={toggleExpanded}
        >
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              {getStatusIcon(result.status)}
              <h4 className="font-medium">{result.query}</h4>
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {result.execution_time}s
              </span>
              <span>Rows: {result.row_count}</span>
              {getStatusBadge(result.status)}
            </div>
            {result.error && (
              <Alert className="mt-2 border-red-200 bg-red-50">
                <AlertDescription className="text-sm text-red-800">
                  {result.error}
                </AlertDescription>
              </Alert>
            )}
          </div>
          <ChevronRight className={`h-5 w-5 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
        </div>

        {isExpanded && (
          <div className="mt-4 space-y-3 border-t pt-3">
            {/* Expected vs Actual */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <strong>Expected:</strong>
                <div className="text-gray-600">
                  Type: {result.expected_type}<br />
                  Fields: {result.expected_fields.join(', ')}
                </div>
              </div>
              <div>
                <strong>Actual:</strong>
                <div className="text-gray-600">
                  Type: {result.actual_type}<br />
                  Fields: {result.actual_fields.join(', ') || 'None'}
                </div>
              </div>
            </div>

            {/* SQL Query */}
            {result.sql_query && (
              <div>
                <strong className="text-sm">Generated SQL:</strong>
                <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto mt-1">
                  {result.sql_query}
                </pre>
              </div>
            )}

            {/* Sample Results */}
            {result.sample_results && result.sample_results.length > 0 && (
              <div>
                <strong className="text-sm">Sample Results:</strong>
                <div className="overflow-x-auto mt-1">
                  <table className="text-xs border-collapse w-full">
                    <thead>
                      <tr className="bg-gray-100">
                        {Object.keys(result.sample_results[0]).map((key) => (
                          <th key={key} className="border p-1 text-left">{key}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.sample_results.map((row, idx) => (
                        <tr key={idx}>
                          {Object.values(row).map((val, i) => (
                            <td key={i} className="border p-1">{String(val)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* AI Analysis */}
            {result.ai_analysis && (
              <div>
                <strong className="text-sm">AI Analysis:</strong>
                <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto mt-1">
                  {JSON.stringify(result.ai_analysis, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  const categories = testResults ? Object.keys(testResults.results) : []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center">
            <BarChart3 className="mr-3 h-8 w-8 text-blue-500" />
            AI Query Test Suite
          </h1>
          <p className="text-muted-foreground">
            Test and validate all AI query capabilities
          </p>
        </div>
        <div className="flex items-center gap-2">
          {testResults && (
            <Button onClick={exportResults} variant="outline" size="sm">
              <Download className="mr-2 h-4 w-4" />
              Export Results
            </Button>
          )}
          <Button 
            onClick={() => runTests(selectedCategory === 'all' ? null : selectedCategory)} 
            disabled={loading}
          >
            {loading ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Running Tests...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Run Tests
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Summary Card */}
      {testResults && (
        <Card>
          <CardHeader>
            <CardTitle>Test Summary</CardTitle>
            <CardDescription>
              Tested on {new Date(testResults.summary.test_timestamp).toLocaleString()}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-5 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold">{testResults.summary.total_queries}</div>
                <div className="text-sm text-gray-600">Total Queries</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{testResults.summary.passed}</div>
                <div className="text-sm text-gray-600">Passed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">{testResults.summary.partial}</div>
                <div className="text-sm text-gray-600">Partial</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{testResults.summary.failed}</div>
                <div className="text-sm text-gray-600">Failed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{testResults.summary.success_rate}%</div>
                <div className="text-sm text-gray-600">Success Rate</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Category Filter */}
      {testResults && (
        <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="all">All Categories</TabsTrigger>
            {categories.map((category) => (
              <TabsTrigger key={category} value={category}>
                {category.replace(' ', '\n')}
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value="all" className="mt-4">
            <Accordion type="single" collapsible className="space-y-4">
              {categories.map((category) => (
                <AccordionItem key={category} value={category}>
                  <AccordionTrigger className="text-lg font-semibold">
                    {category} ({testResults.results[category].length} queries)
                  </AccordionTrigger>
                  <AccordionContent>
                    <ScrollArea className="h-[600px] pr-4">
                      {testResults.results[category].map((result, index) => 
                        renderQueryResult(result, index, category)
                      )}
                    </ScrollArea>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </TabsContent>

          {categories.map((category) => (
            <TabsContent key={category} value={category} className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle>{category}</CardTitle>
                  <CardDescription>
                    {testResults.results[category].length} test queries
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[600px] pr-4">
                    {testResults.results[category].map((result, index) => 
                      renderQueryResult(result, index, category)
                    )}
                  </ScrollArea>
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </Tabs>
      )}

      {/* Initial State */}
      {!testResults && !loading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <BarChart3 className="h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500 mb-4">Click "Run Tests" to start testing all AI queries</p>
            <Button onClick={() => runTests()}>
              <Play className="mr-2 h-4 w-4" />
              Run All Tests
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default AIQueryTester