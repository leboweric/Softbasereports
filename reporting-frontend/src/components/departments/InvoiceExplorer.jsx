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
  const [linkTestV2, setLinkTestV2] = useState(null)
  const [testingLinkV2, setTestingLinkV2] = useState(false)
  const [revenueTest, setRevenueTest] = useState(null)
  const [testingRevenue, setTestingRevenue] = useState(false)
  const [deptTest, setDeptTest] = useState(null)
  const [testingDept, setTestingDept] = useState(false)
  const [verifyTest, setVerifyTest] = useState(null)
  const [testingVerify, setTestingVerify] = useState(false)

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

  const testInvoiceLinkV2 = async () => {
    setTestingLinkV2(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/test-invoice-link-v2'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        setLinkTestV2(result)
      } else {
        setError(`Failed to test link v2: ${response.status}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setTestingLinkV2(false)
    }
  }

  const testServiceRevenue = async () => {
    setTestingRevenue(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/test-service-revenue'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        setRevenueTest(result)
      } else {
        setError(`Failed to test revenue: ${response.status}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setTestingRevenue(false)
    }
  }

  const testSaleDept = async () => {
    setTestingDept(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/test-saledept'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        setDeptTest(result)
      } else {
        setError(`Failed to test departments: ${response.status}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setTestingDept(false)
    }
  }

  const verifyServiceRevenue = async () => {
    setTestingVerify(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/verify-service-revenue'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        setVerifyTest(result)
      } else {
        setError(`Failed to verify revenue: ${response.status}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setTestingVerify(false)
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
          <CardDescription>Test if ControlNo field links to work orders</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 mb-4 flex-wrap">
            <Button 
              onClick={testInvoiceLink} 
              disabled={testingLink}
            >
              {testingLink ? 'Testing...' : 'Test Method 1 (Explore Tables)'}
            </Button>
            <Button 
              onClick={testInvoiceLinkV2} 
              disabled={testingLinkV2}
              variant="secondary"
            >
              {testingLinkV2 ? 'Testing...' : 'Test Method 2 (Try Joins)'}
            </Button>
            <Button 
              onClick={testServiceRevenue} 
              disabled={testingRevenue}
              variant="outline"
            >
              {testingRevenue ? 'Testing...' : 'Test Revenue Query'}
            </Button>
            <Button 
              onClick={testSaleDept} 
              disabled={testingDept}
              variant="secondary"
            >
              {testingDept ? 'Testing...' : 'Test SaleDept Values'}
            </Button>
            <Button 
              onClick={verifyServiceRevenue} 
              disabled={testingVerify}
              variant="destructive"
            >
              {testingVerify ? 'Verifying...' : 'Verify July Revenue'}
            </Button>
          </div>
          
          {linkTest && (
            <div className="space-y-4">
              <div className="bg-white p-4 rounded border">
                <h4 className="font-semibold mb-2">Test Results:</h4>
                {linkTest.statistics ? (
                  <ul className="space-y-1 text-sm">
                    <li>Total Invoices: {linkTest.statistics.total_invoices || 0}</li>
                    <li>Invoices with ControlNo: {linkTest.statistics.invoices_with_control || 0}</li>
                    <li>Successfully Matched to WO: {linkTest.statistics.matched_to_wo || 0}</li>
                    <li>Service Invoices (Type='S'): {linkTest.statistics.service_invoices || 0}</li>
                  </ul>
                ) : (
                  <p className="text-sm text-red-600">{linkTest.error || 'Exploring table structure...'}</p>
                )}
              </div>
              
              {linkTest.wo_columns && (
                <div className="bg-white p-4 rounded border">
                  <h4 className="font-semibold mb-2">WO Table Columns (filtered):</h4>
                  <div className="flex flex-wrap gap-2">
                    {linkTest.wo_columns.map((col, idx) => (
                      <span key={idx} className="px-2 py-1 bg-gray-200 rounded text-sm">
                        {col.COLUMN_NAME}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {linkTest.wo_sample && (
                <div className="bg-white p-4 rounded border">
                  <h4 className="font-semibold mb-2">WO Table Sample (Type='S'):</h4>
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(linkTest.wo_sample, null, 2)}
                  </pre>
                </div>
              )}
              
              {linkTest.invoice_samples && linkTest.invoice_samples.length > 0 && (
                <div className="bg-white p-4 rounded border">
                  <h4 className="font-semibold mb-2">Invoice ControlNo Samples:</h4>
                  <div className="overflow-x-auto">
                    <table className="text-sm w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">Invoice#</th>
                          <th className="text-left p-2">ControlNo</th>
                          <th className="text-left p-2">Date</th>
                          <th className="text-left p-2">Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        {linkTest.invoice_samples.slice(0, 5).map((inv, idx) => (
                          <tr key={idx} className="border-b">
                            <td className="p-2">{inv.InvoiceNo}</td>
                            <td className="p-2">{inv.ControlNo}</td>
                            <td className="p-2">{new Date(inv.InvoiceDate).toLocaleDateString()}</td>
                            <td className="p-2">${inv.GrandTotal}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {linkTestV2 && (
            <div className="space-y-4 mt-4 border-t pt-4">
              <h4 className="font-semibold">Test Method 2 Results:</h4>
              
              {linkTestV2.control_samples && (
                <div className="bg-white p-4 rounded border">
                  <h5 className="font-medium mb-2">Sample ControlNo Values:</h5>
                  <ul className="list-disc list-inside text-sm">
                    {linkTestV2.control_samples.map((sample, idx) => (
                      <li key={idx}>{sample.ControlNo}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {linkTestV2.test_results && (
                <div className="bg-white p-4 rounded border">
                  <h5 className="font-medium mb-2">Join Test Results:</h5>
                  <ul className="space-y-1 text-sm">
                    {Object.entries(linkTestV2.test_results).map(([key, value]) => (
                      <li key={key}>
                        <span className="font-medium">{key}:</span> {value}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {linkTestV2.wo_string_columns && (
                <div className="bg-white p-4 rounded border">
                  <h5 className="font-medium mb-2">WO Table String Columns:</h5>
                  <div className="flex flex-wrap gap-2">
                    {linkTestV2.wo_string_columns.map((col, idx) => (
                      <span key={idx} className="px-2 py-1 bg-gray-200 rounded text-sm">
                        {col.COLUMN_NAME}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          
          {revenueTest && (
            <div className="space-y-4 mt-4 border-t pt-4">
              <h4 className="font-semibold">Revenue Query Test Results:</h4>
              
              <div className="bg-white p-4 rounded border">
                <h5 className="font-medium mb-2">Invoice Statistics (Last 6 Months):</h5>
                <ul className="space-y-1 text-sm">
                  <li><span className="font-medium">Total Invoices:</span> {revenueTest.total_invoices?.total || 0}</li>
                  <li><span className="font-medium">Total Revenue:</span> ${revenueTest.total_invoices?.total_revenue || 0}</li>
                  <li><span className="font-medium">Invoices with ControlNo:</span> {revenueTest.with_controlno?.count || 0}</li>
                  <li><span className="font-medium">Revenue with ControlNo:</span> ${revenueTest.with_controlno?.revenue || 0}</li>
                  <li><span className="font-medium">Joined Matches:</span> {revenueTest.join_matches?.matches || 0}</li>
                  <li><span className="font-medium">Matched Revenue:</span> ${revenueTest.join_matches?.matched_revenue || 0}</li>
                  <li><span className="font-medium">Service Matches:</span> {revenueTest.service_matches?.service_matches || 0}</li>
                  <li><span className="font-medium">Service Revenue:</span> ${revenueTest.service_matches?.service_revenue || 0}</li>
                </ul>
              </div>
              
              {revenueTest.unmatched_samples && revenueTest.unmatched_samples.length > 0 && (
                <div className="bg-white p-4 rounded border">
                  <h5 className="font-medium mb-2">Unmatched ControlNo Samples:</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">ControlNo</th>
                        <th className="text-left p-2">Invoice#</th>
                        <th className="text-left p-2">Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {revenueTest.unmatched_samples.map((item, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="p-2">{item.ControlNo}</td>
                          <td className="p-2">{item.InvoiceNo}</td>
                          <td className="p-2">${item.GrandTotal}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
          
          {deptTest && (
            <div className="space-y-4 mt-4 border-t pt-4">
              <h4 className="font-semibold">SaleDept Analysis:</h4>
              
              {deptTest.department_distribution && (
                <div className="bg-white p-4 rounded border">
                  <h5 className="font-medium mb-2">Department Distribution:</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">SaleDept</th>
                        <th className="text-left p-2">SaleCode</th>
                        <th className="text-left p-2">Count</th>
                        <th className="text-left p-2">Revenue</th>
                      </tr>
                    </thead>
                    <tbody>
                      {deptTest.department_distribution.slice(0, 10).map((dept, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="p-2">{dept.SaleDept}</td>
                          <td className="p-2">{dept.SaleCode}</td>
                          <td className="p-2">{dept.count}</td>
                          <td className="p-2">${(dept.total_revenue || 0).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              
              {deptTest.samples && Object.keys(deptTest.samples).length > 0 && (
                <div className="bg-white p-4 rounded border">
                  <h5 className="font-medium mb-2">Sample Invoices by Department:</h5>
                  {Object.entries(deptTest.samples).map(([key, invoices]) => (
                    <div key={key} className="mb-4">
                      <h6 className="font-medium text-sm mb-1">{key}:</h6>
                      <div className="text-xs space-y-1 ml-4">
                        {invoices.map((inv, idx) => (
                          <div key={idx}>
                            Invoice {inv.InvoiceNo}: ${inv.GrandTotal} 
                            (Labor: ${inv.LaborCost}, Parts: ${inv.PartsCost})
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          
          {verifyTest && (
            <div className="space-y-4 mt-4 border-t pt-4">
              <h4 className="font-semibold text-red-600">July Revenue Verification:</h4>
              
              {verifyTest.july_with_join && (
                <div className="bg-red-50 p-4 rounded border border-red-200">
                  <h5 className="font-medium mb-2">Current Join Results (INCORRECT):</h5>
                  <ul className="space-y-1 text-sm">
                    <li>Invoice Count: {verifyTest.july_with_join.invoice_count}</li>
                    <li>Row Count: {verifyTest.july_with_join.row_count}</li>
                    <li>Total Revenue: ${(verifyTest.july_with_join.total_revenue || 0).toLocaleString()}</li>
                    <li className="text-red-600 font-bold">
                      Should be ~$73K (Field: $54K + Shop: $19K)
                    </li>
                  </ul>
                </div>
              )}
              
              {verifyTest.duplicates && verifyTest.duplicates.length > 0 && (
                <div className="bg-yellow-50 p-4 rounded border border-yellow-200">
                  <h5 className="font-medium mb-2">Duplicate Invoices Found:</h5>
                  <p className="text-sm text-yellow-700">Each invoice is matching multiple work orders!</p>
                </div>
              )}
              
              {verifyTest.july_by_dept && (
                <div className="bg-white p-4 rounded border">
                  <h5 className="font-medium mb-2">July Revenue by Department:</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Dept</th>
                        <th className="text-left p-2">Code</th>
                        <th className="text-left p-2">Count</th>
                        <th className="text-left p-2">Revenue</th>
                      </tr>
                    </thead>
                    <tbody>
                      {verifyTest.july_by_dept.slice(0, 10).map((dept, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="p-2">{dept.SaleDept}</td>
                          <td className="p-2">{dept.SaleCode}</td>
                          <td className="p-2">{dept.invoice_count}</td>
                          <td className="p-2">${(dept.revenue || 0).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              
              {verifyTest.service_likely_codes && (
                <div className="bg-white p-4 rounded border">
                  <h5 className="font-medium mb-2">Codes with High Labor (likely Service):</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">SaleCode</th>
                        <th className="text-left p-2">Count</th>
                        <th className="text-left p-2">Labor Rev</th>
                        <th className="text-left p-2">Total Rev</th>
                      </tr>
                    </thead>
                    <tbody>
                      {verifyTest.service_likely_codes.slice(0, 10).map((code, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="p-2">{code.SaleCode}</td>
                          <td className="p-2">{code.count}</td>
                          <td className="p-2">${(code.labor_revenue || 0).toLocaleString()}</td>
                          <td className="p-2">${(code.total_revenue || 0).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
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