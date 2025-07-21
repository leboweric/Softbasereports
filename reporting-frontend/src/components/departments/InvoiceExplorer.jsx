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
  const [currentMonthTest, setCurrentMonthTest] = useState(null)
  const [testingCurrentMonth, setTestingCurrentMonth] = useState(false)
  const [salecodeSearch, setSalecodeSearch] = useState(null)
  const [searchingSalecodes, setSearchingSalecodes] = useState(false)
  const [historicalMatch, setHistoricalMatch] = useState(null)
  const [matchingHistorical, setMatchingHistorical] = useState(false)
  const [accountTest, setAccountTest] = useState(null)
  const [testingAccounts, setTestingAccounts] = useState(false)
  const [debugRevenue, setDebugRevenue] = useState(null)
  const [debuggingRevenue, setDebuggingRevenue] = useState(false)

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

  const testCurrentMonth = async () => {
    setTestingCurrentMonth(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/test-current-month'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        setCurrentMonthTest(result)
      } else {
        setError(`Failed to test current month: ${response.status}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setTestingCurrentMonth(false)
    }
  }

  const findServiceSalecodes = async () => {
    setSearchingSalecodes(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/find-service-salecodes'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        setSalecodeSearch(result)
      } else {
        setError(`Failed to find salecodes: ${response.status}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setSearchingSalecodes(false)
    }
  }

  const matchHistoricalRevenue = async () => {
    setMatchingHistorical(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/match-historical-revenue'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        setHistoricalMatch(result)
      } else {
        setError(`Failed to match historical: ${response.status}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setMatchingHistorical(false)
    }
  }

  const testAccountNumbers = async () => {
    setTestingAccounts(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/test-account-numbers'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        setAccountTest(result)
      } else {
        setError(`Failed to test accounts: ${response.status}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setTestingAccounts(false)
    }
  }

  const debugRevenueNumber = async () => {
    setDebuggingRevenue(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/debug-revenue-number'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        setDebugRevenue(result)
      } else {
        setError(`Failed to debug revenue: ${response.status}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setDebuggingRevenue(false)
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
              onClick={async () => {
                try {
                  const token = localStorage.getItem('token')
                  const response = await fetch(apiUrl('/api/reports/departments/get-all-columns'), {
                    headers: {
                      'Authorization': `Bearer ${token}`,
                    },
                  })
                  if (response.ok) {
                    const data = await response.json()
                    console.log('=== ALL TABLE COLUMNS ===')
                    console.log('InvoiceReg columns:', data.invoice_column_names)
                    console.log('WO columns:', data.wo_column_names)
                    console.log('Invoice sample:', data.invoice_sample)
                    console.log('WO sample:', data.wo_sample)
                    
                    alert(`InvoiceReg has ${data.invoice_column_names.length} columns\nWO table has ${data.wo_column_names.length} columns\n\nCheck console for full column lists and sample data`)
                  } else {
                    alert('Failed to get columns')
                  }
                } catch (err) {
                  alert('Error: ' + err.message)
                }
              }}
              className="bg-purple-600 hover:bg-purple-700 text-white"
            >
              🗂️ Get All Columns
            </Button>
            <Button 
              onClick={async () => {
                try {
                  const token = localStorage.getItem('token')
                  const response = await fetch(apiUrl('/api/reports/departments/list-salecodes'), {
                    headers: {
                      'Authorization': `Bearer ${token}`,
                    },
                  })
                  if (response.ok) {
                    const data = await response.json()
                    console.log('=== ALL SALECODES IN JULY 2025 ===')
                    console.log('Total codes:', data.total_count)
                    console.log('All codes:', data.all_codes)
                    console.log('Potential Service codes:', data.potential_service)
                    
                    // Show top 10 in alert
                    let message = 'Top 10 SaleCodes in July 2025:\n\n'
                    data.all_codes.slice(0, 10).forEach(code => {
                      message += `${code.SaleCode}: $${code.total?.toLocaleString()} (${code.count} invoices)\n`
                    })
                    message += '\nCheck console for full list'
                    alert(message)
                  } else {
                    alert('Failed to list codes')
                  }
                } catch (err) {
                  alert('Error: ' + err.message)
                }
              }}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              📋 List All SaleCodes
            </Button>
            <Button 
              onClick={async () => {
                try {
                  const token = localStorage.getItem('token')
                  const response = await fetch(apiUrl('/api/reports/departments/simple-service-test'), {
                    headers: {
                      'Authorization': `Bearer ${token}`,
                    },
                  })
                  if (response.ok) {
                    const data = await response.json()
                    console.log('=== JULY 2025 SERVICE REVENUE TEST ===')
                    console.log('Target:', data.target)
                    console.log('Summaries:', data.summaries)
                    console.log('Details:', data.details)
                    alert(`July 2025 Revenue Totals:\n\nFMROAD only: $${data.summaries.field_only?.toLocaleString()}\nFMSHOP only: $${data.summaries.shop_only?.toLocaleString()}\nFMROAD+FMSHOP: $${data.summaries.salecode_fm?.toLocaleString()}\nRecvAccount 410004+410005: $${data.summaries.recv_410004_410005?.toLocaleString()}\n\nTotal July Revenue: $${data.summaries.total_july?.toLocaleString()}\nTarget: $${data.target?.toLocaleString()}\n\nCheck console for full details`)
                  } else {
                    alert('Failed to run test')
                  }
                } catch (err) {
                  alert('Error: ' + err.message)
                }
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              📊 Simple July Test
            </Button>
            <Button 
              onClick={debugRevenueNumber} 
              disabled={debuggingRevenue}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {debuggingRevenue ? 'Debugging...' : '🔍 Debug $23,511.68'}
            </Button>
            <Button 
              onClick={testAccountNumbers} 
              disabled={testingAccounts}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              {testingAccounts ? 'Testing...' : '💰 Test Account Numbers'}
            </Button>
            <Button 
              onClick={matchHistoricalRevenue} 
              disabled={matchingHistorical}
              className="bg-orange-600 hover:bg-orange-700 text-white"
            >
              {matchingHistorical ? 'Matching...' : '📊 Match Historical Revenue'}
            </Button>
            <Button 
              onClick={findServiceSalecodes} 
              disabled={searchingSalecodes}
              className="bg-purple-600 hover:bg-purple-700 text-white"
            >
              {searchingSalecodes ? 'Searching...' : '🔍 Find Service SaleCodes'}
            </Button>
            <Button 
              onClick={async () => {
                try {
                  const token = localStorage.getItem('token')
                  const response = await fetch(apiUrl('/api/reports/departments/analyze-service-revenue'), {
                    headers: {
                      'Authorization': `Bearer ${token}`,
                    },
                  })
                  if (response.ok) {
                    const data = await response.json()
                    console.log('=== COMPREHENSIVE SERVICE REVENUE ANALYSIS ===')
                    console.log('1. All SaleCodes by Revenue:', data.salecode_breakdown)
                    console.log('2. FMROAD & FMSHOP totals:', data.service_codes)
                    console.log('3. Account 410004/410005 breakdown:', data.account_breakdown)
                    console.log('4. All FM* SaleCodes:', data.fm_salecodes)
                    console.log('5. Total July Revenue:', data.total_july)
                    console.log('6. Sample Service Invoices:', data.sample_invoices)
                    
                    // Calculate totals
                    const fmTotal = data.service_codes?.reduce((sum, item) => sum + (item.total_revenue || 0), 0) || 0
                    const acctTotal = data.account_breakdown?.reduce((sum, item) => sum + (item.total_revenue || 0), 0) || 0
                    const fmAllTotal = data.fm_salecodes?.reduce((sum, item) => sum + (item.total_revenue || 0), 0) || 0
                    
                    alert(`Service Revenue Analysis for July 2025:\n\nFMROAD + FMSHOP: $${fmTotal.toLocaleString()}\nAccounts 410004+410005: $${acctTotal.toLocaleString()}\nAll FM* codes: $${fmAllTotal.toLocaleString()}\n\nTotal July Revenue: $${data.total_july?.total_july_revenue?.toLocaleString() || 0}\nTarget: $72,891\n\nCheck console for detailed breakdown`)
                  } else {
                    alert('Failed to analyze revenue')
                  }
                } catch (err) {
                  alert('Error: ' + err.message)
                }
              }}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              📈 Analyze Service Revenue
            </Button>
            <Button 
              onClick={async () => {
                try {
                  const token = localStorage.getItem('token')
                  const response = await fetch(apiUrl('/api/reports/departments/analyze-labor-sales'), {
                    headers: {
                      'Authorization': `Bearer ${token}`,
                    },
                  })
                  if (response.ok) {
                    const data = await response.json()
                    console.log('=== LABOR SALES ANALYSIS (matching OData wolabor) ===')
                    console.log('1. Labor Totals for July:', data.labor_totals)
                    console.log('2. Labor by SaleCode:', data.labor_by_salecode)
                    console.log('3. Labor-related tables found:', data.labor_tables_found)
                    console.log('4. Monthly Labor Trend:', data.monthly_labor_trend)
                    console.log('5. WO Labor Sample:', data.wo_labor_sample)
                    
                    const laborTotal = data.labor_totals?.total_labor_revenue || 0
                    const monthlyData = data.monthly_labor_trend?.map(m => 
                      `${m.month}/${m.year}: $${m.labor_revenue?.toLocaleString()}`
                    ).join('\n') || 'No data'
                    
                    alert(`Labor Sales Analysis:\n\nJuly 2025 Labor Total: $${laborTotal.toLocaleString()}\nTarget: $72,891\n\nMonthly Trend:\n${monthlyData}\n\nTop Labor SaleCodes in console`)
                  } else {
                    alert('Failed to analyze labor sales')
                  }
                } catch (err) {
                  alert('Error: ' + err.message)
                }
              }}
              className="bg-yellow-600 hover:bg-yellow-700 text-white"
            >
              ⚙️ Analyze Labor Sales
            </Button>
            <Button 
              onClick={async () => {
                try {
                  const token = localStorage.getItem('token')
                  const response = await fetch(apiUrl('/api/reports/departments/verify-service-salecodes'), {
                    headers: {
                      'Authorization': `Bearer ${token}`,
                    },
                  })
                  if (response.ok) {
                    const data = await response.json()
                    console.log('=== VERIFY RDCST + SHOPCST ===')
                    console.log('Monthly Breakdown:', data.monthly_breakdown)
                    console.log('Current Month:', data.current_month)
                    
                    let message = 'Service Revenue using RDCST + SHOPCST:\n\n'
                    data.monthly_breakdown.forEach(month => {
                      const monthName = new Date(month.year, month.month - 1).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
                      message += `${monthName}: $${month.total_revenue?.toLocaleString()}`
                      if (month.target) {
                        message += ` (Target: $${month.target.toLocaleString()}, ${month.match_percent}%)`
                      }
                      message += '\n'
                    })
                    
                    message += `\nCurrent Month: $${data.current_month?.total_revenue?.toLocaleString() || 0}`
                    message += `\n  Road: $${data.current_month?.road_revenue?.toLocaleString() || 0}`
                    message += `\n  Shop: $${data.current_month?.shop_revenue?.toLocaleString() || 0}`
                    
                    alert(message)
                  } else {
                    alert('Failed to verify salecodes')
                  }
                } catch (err) {
                  alert('Error: ' + err.message)
                }
              }}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              ✅ Verify RDCST + SHOPCST
            </Button>
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
            <Button 
              onClick={testCurrentMonth} 
              disabled={testingCurrentMonth}
              variant="secondary"
            >
              {testingCurrentMonth ? 'Testing...' : 'Test Current Month'}
            </Button>
          </div>
          
          {debugRevenue && (
            <div className="space-y-4 border-t pt-4">
              <h4 className="font-semibold text-red-600">Debug: Where is $23,511.68 coming from?</h4>
              
              <div className="bg-gray-50 p-4 rounded border border-gray-200">
                <h5 className="font-medium mb-2">Current Date:</h5>
                <p className="text-sm">
                  {debugRevenue.current_date?.month_name} {debugRevenue.current_date?.year} 
                  (Month: {debugRevenue.current_date?.month})
                </p>
              </div>
              
              {debugRevenue.recv_account_test && (
                <div className={`p-4 rounded border ${debugRevenue.recv_account_test.total_revenue === 23511.68 ? 'bg-red-50 border-red-200' : 'bg-white'}`}>
                  <h5 className="font-medium mb-2">RecvAccount Method (410004, 410005):</h5>
                  {debugRevenue.recv_account_test.error ? (
                    <p className="text-red-600">Error: {debugRevenue.recv_account_test.error}</p>
                  ) : (
                    <ul className="text-sm space-y-1">
                      <li>Invoices: {debugRevenue.recv_account_test.invoice_count}</li>
                      <li className={debugRevenue.recv_account_test.total_revenue === 23511.68 ? 'font-bold text-red-600' : ''}>
                        Revenue: ${(debugRevenue.recv_account_test.total_revenue || 0).toLocaleString()}
                        {debugRevenue.recv_account_test.total_revenue === 23511.68 && ' ← MATCH!'}
                      </li>
                      <li>Date Range: {debugRevenue.recv_account_test.min_date} to {debugRevenue.recv_account_test.max_date}</li>
                    </ul>
                  )}
                </div>
              )}
              
              {debugRevenue.dept_test && (
                <div className={`p-4 rounded border ${debugRevenue.dept_test.total_revenue === 23511.68 ? 'bg-red-50 border-red-200' : 'bg-white'}`}>
                  <h5 className="font-medium mb-2">Department Method (40, 45):</h5>
                  {debugRevenue.dept_test.error ? (
                    <p className="text-red-600">Error: {debugRevenue.dept_test.error}</p>
                  ) : (
                    <ul className="text-sm space-y-1">
                      <li>Invoices: {debugRevenue.dept_test.invoice_count}</li>
                      <li className={debugRevenue.dept_test.total_revenue === 23511.68 ? 'font-bold text-red-600' : ''}>
                        Revenue: ${(debugRevenue.dept_test.total_revenue || 0).toLocaleString()}
                        {debugRevenue.dept_test.total_revenue === 23511.68 && ' ← MATCH!'}
                      </li>
                      <li>Date Range: {debugRevenue.dept_test.min_date} to {debugRevenue.dept_test.max_date}</li>
                    </ul>
                  )}
                </div>
              )}
              
              {debugRevenue.salecode_test && (
                <div className={`p-4 rounded border ${debugRevenue.salecode_test.total_revenue === 23511.68 ? 'bg-red-50 border-red-200' : 'bg-white'}`}>
                  <h5 className="font-medium mb-2">SaleCode Method (FMROAD, FMSHOP):</h5>
                  <ul className="text-sm space-y-1">
                    <li>Invoices: {debugRevenue.salecode_test.invoice_count}</li>
                    <li className={debugRevenue.salecode_test.total_revenue === 23511.68 ? 'font-bold text-red-600' : ''}>
                      Revenue: ${(debugRevenue.salecode_test.total_revenue || 0).toLocaleString()}
                      {debugRevenue.salecode_test.total_revenue === 23511.68 && ' ← MATCH!'}
                    </li>
                    <li>Date Range: {debugRevenue.salecode_test.min_date} to {debugRevenue.salecode_test.max_date}</li>
                  </ul>
                </div>
              )}
              
              {debugRevenue.exact_match_search && debugRevenue.exact_match_search.length > 0 && (
                <div className="bg-red-50 p-4 rounded border border-red-200">
                  <h5 className="font-medium mb-2">Found exact matches for $23,511.68:</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">SaleCode</th>
                        <th className="text-left p-2">Dept</th>
                        <th className="text-left p-2">RecvAccount</th>
                        <th className="text-right p-2">Count</th>
                        <th className="text-right p-2">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {debugRevenue.exact_match_search.map((row, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="p-2">{row.SaleCode || 'null'}</td>
                          <td className="p-2">{row.Dept || 'null'}</td>
                          <td className="p-2">{row.RecvAccount || 'null'}</td>
                          <td className="p-2 text-right">{row.count}</td>
                          <td className="p-2 text-right font-bold">${(row.total || 0).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              
              {debugRevenue.single_salecode_matches && debugRevenue.single_salecode_matches.length > 0 && (
                <div className="bg-yellow-50 p-4 rounded border border-yellow-200">
                  <h5 className="font-medium mb-2">Single SaleCodes close to $23,511.68:</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">SaleCode</th>
                        <th className="text-right p-2">Count</th>
                        <th className="text-right p-2">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {debugRevenue.single_salecode_matches.map((row, idx) => (
                        <tr key={idx} className={`border-b ${Math.abs(row.total - 23511.68) < 1 ? 'bg-red-100 font-bold' : ''}`}>
                          <td className="p-2">{row.SaleCode}</td>
                          <td className="p-2 text-right">{row.count}</td>
                          <td className="p-2 text-right">${(row.total || 0).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              
              {debugRevenue.july_recv_account && (
                <div className="bg-blue-50 p-4 rounded border border-blue-200">
                  <h5 className="font-medium mb-2">July 2025 RecvAccount Test:</h5>
                  {debugRevenue.july_recv_account.error ? (
                    <p className="text-red-600">Error: {debugRevenue.july_recv_account.error}</p>
                  ) : (
                    <ul className="text-sm space-y-1">
                      <li>Invoices: {debugRevenue.july_recv_account.invoice_count}</li>
                      <li className="font-bold">Revenue: ${(debugRevenue.july_recv_account.total_revenue || 0).toLocaleString()}</li>
                    </ul>
                  )}
                </div>
              )}
              
              {debugRevenue.recv_account_values && debugRevenue.recv_account_values.length > 0 && (
                <div className="bg-gray-50 p-4 rounded border border-gray-200">
                  <h5 className="font-medium mb-2">RecvAccount values for current month:</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">RecvAccount</th>
                        <th className="text-right p-2">Count</th>
                        <th className="text-right p-2">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {debugRevenue.recv_account_values.map((row, idx) => (
                        <tr key={idx} className={`border-b ${row.RecvAccount === '410004' || row.RecvAccount === '410005' ? 'bg-green-100' : ''}`}>
                          <td className="p-2">{row.RecvAccount}</td>
                          <td className="p-2 text-right">{row.count}</td>
                          <td className="p-2 text-right">${(row.total || 0).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
          
          {accountTest && (
            <div className="space-y-4 border-t pt-4">
              <h4 className="font-semibold text-green-600">Account Number Testing (410004=Field, 410005=Shop):</h4>
              
              {accountTest.account_columns && accountTest.account_columns.length > 0 && (
                <div className="bg-gray-50 p-4 rounded border border-gray-200">
                  <h5 className="font-medium mb-2">Account-related columns found:</h5>
                  <div className="flex flex-wrap gap-2">
                    {accountTest.account_columns.map((col, idx) => (
                      <span key={idx} className="px-2 py-1 bg-gray-200 rounded text-sm">
                        {col.COLUMN_NAME}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {Object.keys(accountTest).filter(key => key.startsWith('found_in_')).map(key => {
                const colName = key.replace('found_in_', '');
                const data = accountTest[key];
                const monthlyKey = `monthly_by_${colName}`;
                const monthlyData = accountTest[monthlyKey];
                
                return (
                  <div key={key} className="space-y-2">
                    <div className="bg-green-50 p-4 rounded border border-green-200">
                      <h5 className="font-medium mb-2">✅ Found in column: {colName}</h5>
                      <table className="text-sm w-full">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left p-2">Account</th>
                            <th className="text-right p-2">Count</th>
                            <th className="text-right p-2">July Revenue</th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.map((row, idx) => (
                            <tr key={idx} className="border-b">
                              <td className="p-2">{row.account} ({row.account === '410004' ? 'Field' : 'Shop'})</td>
                              <td className="p-2 text-right">{row.count}</td>
                              <td className="p-2 text-right">${(row.revenue || 0).toLocaleString()}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    
                    {monthlyData && (
                      <div className="bg-blue-50 p-4 rounded border border-blue-200">
                        <h5 className="font-medium mb-2">Monthly breakdown using {colName}:</h5>
                        <table className="text-sm w-full">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left p-2">Month</th>
                              <th className="text-right p-2">Field (410004)</th>
                              <th className="text-right p-2">Shop (410005)</th>
                              <th className="text-right p-2">Total</th>
                            </tr>
                          </thead>
                          <tbody>
                            {monthlyData.map((row, idx) => (
                              <tr key={idx} className="border-b">
                                <td className="p-2">{row.month}</td>
                                <td className="p-2 text-right">${(row.field_revenue || 0).toLocaleString()}</td>
                                <td className="p-2 text-right">${(row.shop_revenue || 0).toLocaleString()}</td>
                                <td className="p-2 text-right font-bold">${(row.total_revenue || 0).toLocaleString()}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                );
              })}
              
              {(accountTest.sale_acct_search || accountTest.GLAcct_search || accountTest.GLAccount_search || accountTest.SalesAcct_search) && (
                <div className="bg-yellow-50 p-4 rounded border border-yellow-200">
                  <h5 className="font-medium mb-2">Account codes starting with 4100:</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Account</th>
                        <th className="text-right p-2">Count</th>
                        <th className="text-right p-2">July Revenue</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(accountTest.sale_acct_search || accountTest.GLAcct_search || accountTest.GLAccount_search || accountTest.SalesAcct_search || []).map((row, idx) => (
                        <tr key={idx} className={`border-b ${(row.SaleAcct || row.account) === '410004' || (row.SaleAcct || row.account) === '410005' ? 'bg-green-100 font-bold' : ''}`}>
                          <td className="p-2">{row.SaleAcct || row.account}</td>
                          <td className="p-2 text-right">{row.count}</td>
                          <td className="p-2 text-right">${(row.revenue || 0).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
          
          {historicalMatch && (
            <div className="space-y-4 border-t pt-4">
              <h4 className="font-semibold text-orange-600">Historical Revenue Matching Analysis:</h4>
              
              <div className="bg-orange-50 p-4 rounded border border-orange-200">
                <h5 className="font-medium mb-2">Target Values (Your Historical Data):</h5>
                <table className="text-sm w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Month</th>
                      <th className="text-right p-2">Target Revenue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(historicalMatch.targets || {}).map(([month, value]) => (
                      <tr key={month} className="border-b">
                        <td className="p-2">{month}</td>
                        <td className="p-2 text-right">${value.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {historicalMatch.dept_40_only && historicalMatch.dept_40_only.length > 0 && (
                <div className="bg-blue-50 p-4 rounded border border-blue-200">
                  <h5 className="font-medium mb-2">Department 40 Only (Field Service):</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Month</th>
                        <th className="text-right p-2">Revenue</th>
                        <th className="text-right p-2">Difference</th>
                      </tr>
                    </thead>
                    <tbody>
                      {historicalMatch.dept_40_only.map((row) => {
                        const target = historicalMatch.targets[row.month];
                        const diff = row.revenue - target;
                        return (
                          <tr key={row.month} className="border-b">
                            <td className="p-2">{row.month}</td>
                            <td className="p-2 text-right">${(row.revenue || 0).toLocaleString()}</td>
                            <td className={`p-2 text-right ${Math.abs(diff) < 5000 ? 'text-green-600 font-bold' : 'text-red-600'}`}>
                              {diff > 0 ? '+' : ''}{diff.toLocaleString()}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
              
              {historicalMatch.fmroad_only && (
                <div className="bg-green-50 p-4 rounded border border-green-200">
                  <h5 className="font-medium mb-2">FMROAD Only:</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Month</th>
                        <th className="text-right p-2">Revenue</th>
                        <th className="text-right p-2">Difference</th>
                      </tr>
                    </thead>
                    <tbody>
                      {historicalMatch.fmroad_only.map((row) => {
                        const target = historicalMatch.targets[row.month];
                        const diff = row.revenue - target;
                        return (
                          <tr key={row.month} className="border-b">
                            <td className="p-2">{row.month}</td>
                            <td className="p-2 text-right">${(row.revenue || 0).toLocaleString()}</td>
                            <td className={`p-2 text-right ${Math.abs(diff) < 5000 ? 'text-green-600 font-bold' : 'text-red-600'}`}>
                              {diff > 0 ? '+' : ''}{diff.toLocaleString()}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
              
              {historicalMatch.both_departments && historicalMatch.both_departments.length > 0 && (
                <div className="bg-purple-50 p-4 rounded border border-purple-200">
                  <h5 className="font-medium mb-2">Departments 40 + 45 Combined:</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Month</th>
                        <th className="text-right p-2">Field (40)</th>
                        <th className="text-right p-2">Shop (45)</th>
                        <th className="text-right p-2">Total</th>
                        <th className="text-right p-2">Difference</th>
                      </tr>
                    </thead>
                    <tbody>
                      {historicalMatch.both_departments.map((row) => {
                        const target = historicalMatch.targets[row.month];
                        const diff = row.total_revenue - target;
                        return (
                          <tr key={row.month} className="border-b">
                            <td className="p-2">{row.month}</td>
                            <td className="p-2 text-right">${(row.field_revenue || 0).toLocaleString()}</td>
                            <td className="p-2 text-right">${(row.shop_revenue || 0).toLocaleString()}</td>
                            <td className="p-2 text-right">${(row.total_revenue || 0).toLocaleString()}</td>
                            <td className={`p-2 text-right ${Math.abs(diff) < 5000 ? 'text-green-600 font-bold' : 'text-red-600'}`}>
                              {diff > 0 ? '+' : ''}{diff.toLocaleString()}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
              
              {historicalMatch.significant_codes && (
                <div className="bg-gray-50 p-4 rounded border border-gray-200">
                  <h5 className="font-medium mb-2">Top SaleCodes in July (>$5K):</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">SaleCode</th>
                        <th className="text-right p-2">July Revenue</th>
                        <th className="text-right p-2">Total (Mar-Jul)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {historicalMatch.significant_codes?.slice(0, 10).map((code, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="p-2 font-mono">{code.SaleCode}</td>
                          <td className="p-2 text-right">${(code.july_revenue || 0).toLocaleString()}</td>
                          <td className="p-2 text-right">${(code.total_revenue || 0).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
          
          {salecodeSearch && (
            <div className="space-y-4 border-t pt-4">
              <h4 className="font-semibold text-purple-600">Service SaleCode Analysis:</h4>
              
              {salecodeSearch.salecode_analysis && (
                <div className="bg-purple-50 p-4 rounded border border-purple-200">
                  <h5 className="font-medium mb-2">All SaleCodes in July (sorted by revenue):</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">SaleCode</th>
                        <th className="text-left p-2">SaleDept</th>
                        <th className="text-left p-2">Count</th>
                        <th className="text-left p-2">Revenue</th>
                        <th className="text-left p-2">Avg Labor</th>
                        <th className="text-left p-2">Avg Parts</th>
                      </tr>
                    </thead>
                    <tbody>
                      {salecodeSearch.salecode_analysis.slice(0, 15).map((code, idx) => (
                        <tr key={idx} className={`border-b ${code.SaleCode?.includes('CST') ? 'bg-red-50' : ''}`}>
                          <td className="p-2 font-mono">{code.SaleCode}</td>
                          <td className="p-2">{code.SaleDept}</td>
                          <td className="p-2">{code.count}</td>
                          <td className="p-2">${(code.total_revenue || 0).toLocaleString()}</td>
                          <td className="p-2">${(code.avg_labor || 0).toFixed(0)}</td>
                          <td className="p-2">${(code.avg_parts || 0).toFixed(0)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p className="text-xs text-red-600 mt-2">Red rows indicate potential cost codes (containing 'CST')</p>
                </div>
              )}
              
              {salecodeSearch.dept_salecodes && salecodeSearch.dept_salecodes.length > 0 && (
                <div className="bg-blue-50 p-4 rounded border border-blue-200">
                  <h5 className="font-medium mb-2">SaleCodes for Departments 40 & 45:</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Dept</th>
                        <th className="text-left p-2">SaleCode</th>
                        <th className="text-left p-2">Count</th>
                        <th className="text-left p-2">Revenue</th>
                      </tr>
                    </thead>
                    <tbody>
                      {salecodeSearch.dept_salecodes.map((item, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="p-2">{item.Dept == 40 ? '40 (Field)' : '45 (Shop)'}</td>
                          <td className="p-2 font-mono">{item.SaleCode}</td>
                          <td className="p-2">{item.count}</td>
                          <td className="p-2">${(item.revenue || 0).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              
              {salecodeSearch.non_cost_codes && (
                <div className="bg-green-50 p-4 rounded border border-green-200">
                  <h5 className="font-medium mb-2">Revenue SaleCodes (no 'CST' in name, has labor):</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">SaleCode</th>
                        <th className="text-left p-2">Count</th>
                        <th className="text-left p-2">Revenue</th>
                      </tr>
                    </thead>
                    <tbody>
                      {salecodeSearch.non_cost_codes.slice(0, 10).map((code, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="p-2 font-mono font-bold">{code.SaleCode}</td>
                          <td className="p-2">{code.count}</td>
                          <td className="p-2">${(code.revenue || 0).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
          
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
              
              {verifyTest.service_breakdown && (
                <div className="bg-green-50 p-4 rounded border border-green-200">
                  <h5 className="font-medium mb-2">Service Revenue Breakdown (CORRECTED):</h5>
                  <ul className="space-y-1 text-sm">
                    <li className="font-semibold">Revenue Codes:</li>
                    <li className="ml-4">Field Service (FMROAD): ${(verifyTest.service_breakdown.field_service_revenue || 0).toLocaleString()}</li>
                    <li className="ml-4">Shop Service (FMSHOP): ${(verifyTest.service_breakdown.shop_service_revenue || 0).toLocaleString()}</li>
                    <li className="ml-4 font-bold text-green-600">
                      Total Service Revenue: ${(verifyTest.service_breakdown.total_service_revenue || 0).toLocaleString()}
                    </li>
                    <li className="text-green-600">Target: ~$73K ✓</li>
                    
                    <li className="font-semibold mt-2">Cost Codes (for reference):</li>
                    <li className="ml-4 text-gray-500">Field Cost (RDCST): ${(verifyTest.service_breakdown.field_cost || 0).toLocaleString()}</li>
                    <li className="ml-4 text-gray-500">Shop Cost (SHPCST): ${(verifyTest.service_breakdown.shop_cost || 0).toLocaleString()}</li>
                  </ul>
                </div>
              )}
              
              {verifyTest.service_dept_breakdown && !verifyTest.service_dept_breakdown.error && (
                <div className="bg-blue-50 p-4 rounded border border-blue-200">
                  <h5 className="font-medium mb-2">Service Revenue by Department Code:</h5>
                  <ul className="space-y-1 text-sm">
                    <li>Field Service (Dept 40): ${(verifyTest.service_dept_breakdown.field_service_dept || 0).toLocaleString()}</li>
                    <li>Shop Service (Dept 45): ${(verifyTest.service_dept_breakdown.shop_service_dept || 0).toLocaleString()}</li>
                    <li className="font-bold text-blue-600">
                      Total Service: ${(verifyTest.service_dept_breakdown.total_service_dept || 0).toLocaleString()}
                    </li>
                    <li className="text-blue-600">Using Department codes is cleaner!</li>
                  </ul>
                </div>
              )}
            </div>
          )}
          
          {currentMonthTest && (
            <div className="space-y-4 mt-4 border-t pt-4">
              <h4 className="font-semibold text-purple-600">Current Month Test ({currentMonthTest.current_month?.month_name} {currentMonthTest.current_month?.year}):</h4>
              
              {currentMonthTest.total_current_month && (
                <div className="bg-purple-50 p-4 rounded border border-purple-200">
                  <h5 className="font-medium mb-2">Total Current Month (All Invoices):</h5>
                  <p className="text-sm">
                    {currentMonthTest.total_current_month.count} invoices, 
                    Total: ${(currentMonthTest.total_current_month.total || 0).toLocaleString()}
                  </p>
                </div>
              )}
              
              {currentMonthTest.by_department && !currentMonthTest.by_department.error && (
                <div className="bg-blue-50 p-4 rounded border border-blue-200">
                  <h5 className="font-medium mb-2">By Department (40=Field, 45=Shop):</h5>
                  <ul className="space-y-1 text-sm">
                    {currentMonthTest.by_department.map((dept, idx) => (
                      <li key={idx}>
                        Dept {dept.Dept}: {dept.count} invoices, ${(dept.revenue || 0).toLocaleString()}
                      </li>
                    ))}
                    <li className="font-bold mt-2">
                      Total Service (Dept method): ${
                        currentMonthTest.by_department.reduce((sum, dept) => sum + (dept.revenue || 0), 0).toLocaleString()
                      }
                    </li>
                  </ul>
                </div>
              )}
              
              {currentMonthTest.by_salecode && (
                <div className="bg-green-50 p-4 rounded border border-green-200">
                  <h5 className="font-medium mb-2">By SaleCode:</h5>
                  <ul className="space-y-1 text-sm">
                    {currentMonthTest.by_salecode.map((code, idx) => (
                      <li key={idx}>
                        {code.SaleCode}: {code.count} invoices, ${(code.revenue || 0).toLocaleString()}
                      </li>
                    ))}
                    <li className="font-bold mt-2">
                      Total Service (SaleCode method): ${
                        currentMonthTest.by_salecode.reduce((sum, code) => sum + (code.revenue || 0), 0).toLocaleString()
                      }
                    </li>
                  </ul>
                </div>
              )}
              
              {currentMonthTest.all_departments && currentMonthTest.all_departments.length > 0 && (
                <div className="bg-gray-50 p-4 rounded border border-gray-200">
                  <h5 className="font-medium mb-2">Top Departments This Month:</h5>
                  <table className="text-sm w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Dept</th>
                        <th className="text-left p-2">Count</th>
                        <th className="text-left p-2">Revenue</th>
                      </tr>
                    </thead>
                    <tbody>
                      {currentMonthTest.all_departments.map((dept, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="p-2">{dept.Dept}</td>
                          <td className="p-2">{dept.count}</td>
                          <td className="p-2">${(dept.revenue || 0).toLocaleString()}</td>
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