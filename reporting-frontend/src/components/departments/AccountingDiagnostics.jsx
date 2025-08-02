import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { apiUrl } from '@/lib/api'
import { Database, AlertCircle, CheckCircle, Info } from 'lucide-react'

const AccountingDiagnostics = ({ onClose }) => {
  const [loading, setLoading] = useState(false)
  const [diagnosticsData, setDiagnosticsData] = useState(null)
  const [error, setError] = useState(null)

  const runDiagnostics = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/diagnostics/accounting-tables'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setDiagnosticsData(data)
      } else {
        const errorData = await response.json()
        setError(errorData.error || 'Failed to run diagnostics')
      }
    } catch (error) {
      setError('Failed to connect to server')
    } finally {
      setLoading(false)
    }
  }

  const getCategoryIcon = (category) => {
    const icons = {
      'general_ledger': '📊',
      'accounts_payable': '💳',
      'payroll': '💰',
      'vendor_management': '🏢',
      'expense_tracking': '📝',
      'financial_statements': '📈',
      'other': '📁'
    }
    return icons[category] || '📄'
  }

  const formatColumnInfo = (columns) => {
    if (!columns || columns.length === 0) return 'No columns'
    
    const keyColumns = columns.filter(col => 
      col.name.toLowerCase().includes('amount') ||
      col.name.toLowerCase().includes('date') ||
      col.name.toLowerCase().includes('vendor') ||
      col.name.toLowerCase().includes('account') ||
      col.name.toLowerCase().includes('category')
    ).slice(0, 5)
    
    return keyColumns.map(col => col.name).join(', ')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Accounting Table Diagnostics</h2>
          <p className="text-muted-foreground">Discover and analyze accounting/finance tables in the database</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={runDiagnostics} disabled={loading}>
            {loading ? (
              <>
                <LoadingSpinner className="mr-2 h-4 w-4" />
                Running...
              </>
            ) : (
              <>
                <Database className="mr-2 h-4 w-4" />
                Run Diagnostics
              </>
            )}
          </Button>
          {onClose && (
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          )}
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {diagnosticsData && (
        <div className="space-y-6">
          {/* Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Total Tables Found</p>
                  <p className="text-2xl font-bold">{diagnosticsData.total_tables_found}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">GL Tables</p>
                  <p className="text-2xl font-bold">{diagnosticsData.categories.general_ledger?.length || 0}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">AP Tables</p>
                  <p className="text-2xl font-bold">{diagnosticsData.categories.accounts_payable?.length || 0}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Payroll Tables</p>
                  <p className="text-2xl font-bold">{diagnosticsData.categories.payroll?.length || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recommendations */}
          {diagnosticsData.recommendations && diagnosticsData.recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {diagnosticsData.recommendations.map((rec, idx) => (
                    <Alert key={idx} variant={rec.type === 'warning' ? 'destructive' : 'default'}>
                      <Info className="h-4 w-4" />
                      <AlertDescription>
                        <div className="space-y-2">
                          <p className="font-semibold">{rec.message}</p>
                          {rec.tables && rec.tables.length > 0 && (
                            <div className="flex flex-wrap gap-2">
                              {rec.tables.map(table => (
                                <Badge key={table} variant="secondary">{table}</Badge>
                              ))}
                            </div>
                          )}
                          <p className="text-sm text-muted-foreground">{rec.query_hint}</p>
                        </div>
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Table Details by Category */}
          {Object.entries(diagnosticsData.categories).map(([category, tables]) => {
            if (!tables || tables.length === 0) return null
            
            return (
              <Card key={category}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span>{getCategoryIcon(category)}</span>
                    <span>{category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                    <Badge variant="secondary">{tables.length} tables</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {tables.map(table => (
                      <div key={table.table_name} className="border rounded-lg p-4 space-y-2">
                        <div className="flex items-center justify-between">
                          <h4 className="font-semibold">{table.table_name}</h4>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{table.row_count.toLocaleString()} rows</Badge>
                            {table.has_date_column && (
                              <Badge variant="success">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Has dates
                              </Badge>
                            )}
                          </div>
                        </div>
                        
                        <p className="text-sm text-muted-foreground">
                          Key columns: {formatColumnInfo(table.columns)}
                        </p>
                        
                        {table.sample_data && table.sample_data.length > 0 && (
                          <details className="mt-2">
                            <summary className="cursor-pointer text-sm text-blue-600 hover:text-blue-800">
                              View sample data
                            </summary>
                            <pre className="mt-2 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                              {JSON.stringify(table.sample_data[0], null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )
          })}

          {/* Expense Analysis */}
          {diagnosticsData.expense_analysis && (
            <Card>
              <CardHeader>
                <CardTitle>Expense Pattern Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {diagnosticsData.expense_analysis.gl_account_structure && (
                    <div>
                      <h4 className="font-semibold mb-2">GL Account Structure</h4>
                      <p className="text-sm text-muted-foreground mb-2">
                        Found in table: <Badge variant="secondary">{diagnosticsData.expense_analysis.gl_account_structure.table}</Badge>
                      </p>
                      <pre className="p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                        {JSON.stringify(diagnosticsData.expense_analysis.gl_account_structure.sample_accounts, null, 2)}
                      </pre>
                    </div>
                  )}
                  
                  {diagnosticsData.expense_analysis.vendor_invoice_tables.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-2">Vendor Invoice Tables</h4>
                      <div className="space-y-2">
                        {diagnosticsData.expense_analysis.vendor_invoice_tables.map(table => (
                          <div key={table.table} className="flex items-center gap-2">
                            <Badge variant="secondary">{table.table}</Badge>
                            <span className="text-sm text-muted-foreground">
                              {table.row_count} rows
                              {table.has_amount_column && ' • Has amount'}
                              {table.has_vendor_column && ' • Has vendor'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {!diagnosticsData && !loading && (
        <Card>
          <CardContent className="text-center py-12">
            <Database className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-lg text-muted-foreground">Click "Run Diagnostics" to analyze accounting tables</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default AccountingDiagnostics