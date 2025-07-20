import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { apiUrl } from '@/lib/api'
import { AlertCircle } from 'lucide-react'

const InvoiceExplorer = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [linkTest, setLinkTest] = useState(null)
  const [testingLink, setTestingLink] = useState(false)

  useEffect(() => {
    fetchInvoiceColumns()
  }, [])

  const fetchInvoiceColumns = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/invoice-columns'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        setData(result)
      } else {
        setError(`Failed to fetch: ${response.status}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const testInvoiceLink = async () => {
    setTestingLink(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/test-invoice-link'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        setLinkTest(result)
      } else {
        setError(`Failed to test link: ${response.status}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setTestingLink(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center text-red-500">
          <AlertCircle className="h-12 w-12 mx-auto mb-4" />
          <p>Error: {error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">InvoiceReg Table Explorer</h1>
      
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle>Test Invoice-Work Order Link</CardTitle>
          <CardDescription>Test if ControlNo field links to WONumber</CardDescription>
        </CardHeader>
        <CardContent>
          <Button 
            onClick={testInvoiceLink} 
            disabled={testingLink}
            className="mb-4"
          >
            {testingLink ? 'Testing...' : 'Test ControlNo → WONumber Link'}
          </Button>
          
          {linkTest && (
            <div className="space-y-4">
              <div className="bg-white p-4 rounded border">
                <h4 className="font-semibold mb-2">Statistics (Last Month):</h4>
                <ul className="space-y-1 text-sm">
                  <li>Total Invoices: {linkTest.statistics.total_invoices || 0}</li>
                  <li>Invoices with ControlNo: {linkTest.statistics.invoices_with_control || 0}</li>
                  <li>Successfully Matched to WO: {linkTest.statistics.matched_to_wo || 0}</li>
                  <li>Service Invoices (Type='S'): {linkTest.statistics.service_invoices || 0}</li>
                </ul>
              </div>
              
              {linkTest.sample_matches && linkTest.sample_matches.length > 0 && (
                <div className="bg-white p-4 rounded border">
                  <h4 className="font-semibold mb-2">Sample Matches:</h4>
                  <div className="overflow-x-auto">
                    <table className="text-sm w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">Invoice#</th>
                          <th className="text-left p-2">ControlNo</th>
                          <th className="text-left p-2">WO Type</th>
                          <th className="text-left p-2">Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        {linkTest.sample_matches.slice(0, 5).map((match, idx) => (
                          <tr key={idx} className="border-b">
                            <td className="p-2">{match.InvoiceNo}</td>
                            <td className="p-2">{match.ControlNo}</td>
                            <td className="p-2">{match.Type}</td>
                            <td className="p-2">${match.GrandTotal}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Column Names</CardTitle>
          <CardDescription>All columns in ben002.InvoiceReg table</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-2">
            {data?.column_names?.map((col, idx) => (
              <div key={idx} className="p-2 bg-gray-100 rounded text-sm">
                {col}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Columns with Data Types</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Column Name</th>
                <th className="text-left p-2">Data Type</th>
              </tr>
            </thead>
            <tbody>
              {data?.columns?.map((col, idx) => (
                <tr key={idx} className="border-b">
                  <td className="p-2">{col.COLUMN_NAME}</td>
                  <td className="p-2 text-gray-600">{col.DATA_TYPE}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Sample Data</CardTitle>
          <CardDescription>First row from InvoiceReg table</CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="overflow-x-auto bg-gray-100 p-4 rounded">
            {JSON.stringify(data?.sample, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  )
}

export default InvoiceExplorer