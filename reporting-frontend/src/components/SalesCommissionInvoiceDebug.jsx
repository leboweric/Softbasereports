import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const SalesCommissionInvoiceDebug = ({ user }) => {
  const [loading, setLoading] = useState(false)
  const [debugData, setDebugData] = useState(null)
  const [error, setError] = useState(null)

  const fetchDebugData = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/accounting/sales-commission-invoice-debug'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setDebugData(data)
      } else {
        setError('Failed to fetch debug data')
      }
    } catch (error) {
      console.error('Error fetching debug data:', error)
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDebugData()
  }, [])

  if (loading) {
    return (
      <LoadingSpinner 
        title="Loading Debug Data" 
        description="Analyzing invoice salesman assignments..."
        size="large"
      />
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CardTitle>Sales Commission Invoice Debug</CardTitle>
              <Badge variant="outline" className="flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                Diagnostic Tool
              </Badge>
            </div>
            <Button onClick={fetchDebugData} size="sm" variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
          <CardDescription>
            Investigating why salesmen aren't showing for invoices 110000007-110000010
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="text-red-600">Error: {error}</div>
          ) : debugData ? (
            <div className="space-y-6">
              {/* Problem Summary */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h4 className="font-semibold text-yellow-900 mb-2">Issue Summary</h4>
                <p className="text-sm text-yellow-800 mb-2">{debugData.debug_notes.issue}</p>
                <p className="text-sm text-yellow-700">Example: {debugData.debug_notes.example}</p>
              </div>

              {/* Invoice Details */}
              <div>
                <h4 className="font-semibold mb-3">Invoice Query Results</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Invoice #</th>
                        <th className="text-left p-2">Date</th>
                        <th className="text-left p-2">BillTo</th>
                        <th className="text-left p-2">BillToName</th>
                        <th className="text-left p-2">Sale Code</th>
                        <th className="text-right p-2">Amount</th>
                        <th className="text-left p-2">C1 Number</th>
                        <th className="text-left p-2">C1 Salesman</th>
                        <th className="text-left p-2">C2 Number</th>
                        <th className="text-left p-2">C2 Salesman</th>
                      </tr>
                    </thead>
                    <tbody>
                      {debugData.invoices.map((inv, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="p-2">{inv.InvoiceNo}</td>
                          <td className="p-2">{new Date(inv.InvoiceDate).toLocaleDateString()}</td>
                          <td className="p-2 font-mono text-xs">{inv.BillTo || 'NULL'}</td>
                          <td className="p-2">{inv.BillToName}</td>
                          <td className="p-2">
                            <Badge variant="outline">{inv.SaleCode}</Badge>
                          </td>
                          <td className="text-right p-2">${(inv.EquipmentAmount || 0).toLocaleString()}</td>
                          <td className="p-2 font-mono text-xs">{inv.Customer1_Number || 'NULL'}</td>
                          <td className="p-2">
                            {inv.Customer1_Salesman1 ? (
                              <Badge variant="default">{inv.Customer1_Salesman1}</Badge>
                            ) : (
                              <Badge variant="destructive">NULL</Badge>
                            )}
                          </td>
                          <td className="p-2 font-mono text-xs">{inv.Customer2_Number || 'NULL'}</td>
                          <td className="p-2">
                            {inv.Customer2_Salesman1 ? (
                              <Badge variant="default">{inv.Customer2_Salesman1}</Badge>
                            ) : (
                              <Badge variant="destructive">NULL</Badge>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Customer Table Check */}
              <div>
                <h4 className="font-semibold mb-3">Customer Table Records</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Number</th>
                        <th className="text-left p-2">Name</th>
                        <th className="text-left p-2">Salesman1</th>
                        <th className="text-left p-2">Salesman2</th>
                        <th className="text-left p-2">Salesman3</th>
                      </tr>
                    </thead>
                    <tbody>
                      {debugData.customer_details.map((cust, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="p-2 font-mono">{cust.Number}</td>
                          <td className="p-2">{cust.Name}</td>
                          <td className="p-2">
                            {cust.Salesman1 ? (
                              <Badge variant="default">{cust.Salesman1}</Badge>
                            ) : (
                              <span className="text-gray-400">None</span>
                            )}
                          </td>
                          <td className="p-2">{cust.Salesman2 || '-'}</td>
                          <td className="p-2">{cust.Salesman3 || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Salesman Columns in Invoice */}
              <div>
                <h4 className="font-semibold mb-3">Salesman Columns in InvoiceReg Table</h4>
                {debugData.salesman_columns_in_invoice.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {debugData.salesman_columns_in_invoice.map((col, idx) => (
                      <Badge key={idx} variant="secondary">{col}</Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No salesman-related columns found in InvoiceReg table
                  </p>
                )}
              </div>

              {/* Potential Salesman Tables */}
              <div>
                <h4 className="font-semibold mb-3">Potential Salesman/Commission Tables</h4>
                {debugData.potential_salesman_tables.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {debugData.potential_salesman_tables.map((table, idx) => (
                      <Badge key={idx} variant="outline">{table.TABLE_NAME}</Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No additional salesman/commission tables found
                  </p>
                )}
              </div>

              {/* InvoiceSales Data */}
              {debugData.has_invoice_sales_table && (
                <div>
                  <h4 className="font-semibold mb-3">InvoiceSales Table Data</h4>
                  {debugData.invoice_sales_data.length > 0 ? (
                    <p className="text-sm text-green-600">
                      Found {debugData.invoice_sales_data.length} records in InvoiceSales table
                    </p>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No matching records found in InvoiceSales table
                    </p>
                  )}
                </div>
              )}

              {/* Possible Causes */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-semibold text-blue-900 mb-2">Possible Causes</h4>
                <ul className="list-disc list-inside space-y-1">
                  {debugData.debug_notes.possible_causes.map((cause, idx) => (
                    <li key={idx} className="text-sm text-blue-800">{cause}</li>
                  ))}
                </ul>
              </div>

              {/* Analysis */}
              <div className="bg-gray-50 border rounded-lg p-4">
                <h4 className="font-semibold mb-2">Analysis</h4>
                <div className="space-y-2 text-sm">
                  <p>
                    <strong>BillTo Field:</strong> The invoices have BillTo values of{' '}
                    {debugData.invoices.map(inv => inv.BillTo || 'NULL').join(', ')}
                  </p>
                  <p>
                    <strong>Customer Match:</strong> 
                    {debugData.invoices.some(inv => inv.Customer1_Number) 
                      ? ' Found customer records using BillTo = Customer.Number join'
                      : ' No customer records found using BillTo = Customer.Number join'}
                  </p>
                  <p>
                    <strong>Name Match:</strong> 
                    {debugData.invoices.some(inv => inv.Customer2_Number) 
                      ? ' Found customer records using BillToName = Customer.Name join'
                      : ' No customer records found using BillToName = Customer.Name join'}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground">No debug data available</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default SalesCommissionInvoiceDebug