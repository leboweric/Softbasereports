import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { 
  ComposedChart,
  BarChart,
  Bar, 
  Line,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine,
  Legend,
  Cell
} from 'recharts'
import { apiUrl } from '@/lib/api'

const AccountingReport = ({ user }) => {
  const [monthlyExpenses, setMonthlyExpenses] = useState([])
  const [arData, setArData] = useState(null)
  const [arDebugData, setArDebugData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAccountingData()
    fetchARData()
    fetchARDebugData()
  }, [])

  const fetchAccountingData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/accounting'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setMonthlyExpenses(data.monthly_expenses || [])
      }
    } catch (error) {
      console.error('Error fetching accounting data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchARData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/accounting/ar-report'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setArData(data)
      }
    } catch (error) {
      console.error('Error fetching AR data:', error)
    }
  }

  const fetchARDebugData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/accounting/ar-debug'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setArDebugData(data)
        console.log('AR Debug Data:', data)
      }
    } catch (error) {
      console.error('Error fetching AR debug data:', error)
    }
  }

  if (loading) {
    return (
      <LoadingSpinner 
        title="Loading Accounting Data" 
        description="Fetching financial information..."
        size="large"
      />
    )
  }


  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Accounting Department</h1>
        <p className="text-muted-foreground">Financial overview and accounting metrics</p>
      </div>

      {/* G&A Expenses Over Time */}
      <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle>G&A Expenses Over Time</CardTitle>
                <CardDescription>General & Administrative expenses through February {new Date().getFullYear() + 1}</CardDescription>
              </div>
              {monthlyExpenses && monthlyExpenses.length > 0 && (() => {
                // Exclude current month and incomplete months
                const currentDate = new Date()
                const currentMonthIndex = currentDate.getMonth()
                const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                const currentMonthName = monthNames[currentMonthIndex]
                
                // First pass: calculate a rough average to identify incomplete months
                const monthsWithData = monthlyExpenses.filter(item => item.expenses > 0)
                if (monthsWithData.length === 0) return null
                
                const roughAverage = monthsWithData.reduce((sum, item) => sum + item.expenses, 0) / monthsWithData.length
                
                // Second pass: exclude current month and months with less than 50% of rough average (likely incomplete)
                const completeMonths = monthlyExpenses.filter(item => {
                  return item.month !== currentMonthName && 
                         item.expenses > 0 && 
                         item.expenses > (roughAverage * 0.5)
                })
                
                if (completeMonths.length === 0) return null
                
                const avgExpenses = completeMonths.reduce((sum, item) => sum + item.expenses, 0) / completeMonths.length
                
                return (
                  <div className="text-right">
                    <div>
                      <p className="text-sm text-muted-foreground">Avg Expenses</p>
                      <p className="text-lg font-semibold">${(avgExpenses / 1000).toFixed(0)}k</p>
                    </div>
                  </div>
                )
              })()}
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <ComposedChart data={(() => {
                const data = monthlyExpenses || []
                
                // Calculate average for historical months
                if (data.length > 0) {
                  const currentDate = new Date()
                  const currentMonthIndex = currentDate.getMonth()
                  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                  const currentMonthName = monthNames[currentMonthIndex]
                  
                  // Calculate average excluding current month and incomplete months
                  const monthsWithData = data.filter(item => item.expenses > 0)
                  const roughAverage = monthsWithData.length > 0 
                    ? monthsWithData.reduce((sum, item) => sum + item.expenses, 0) / monthsWithData.length 
                    : 0
                  
                  const completeMonths = data.filter(item => {
                    return item.month !== currentMonthName && 
                           item.expenses > 0 && 
                           item.expenses > (roughAverage * 0.5)
                  })
                  
                  const avgExpenses = completeMonths.length > 0 
                    ? completeMonths.reduce((sum, item) => sum + item.expenses, 0) / completeMonths.length 
                    : 0
                  
                  // Add average to each data point for reference line rendering
                  return data.map(item => ({
                    ...item,
                    avgExpenses: avgExpenses
                  }))
                }
                
                return data
              })()} margin={{ top: 20, right: 70, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                <Tooltip content={({ active, payload, label }) => {
                  if (active && payload && payload.length && monthlyExpenses) {
                    const currentIndex = monthlyExpenses.findIndex(item => item.month === label)
                    const currentData = monthlyExpenses[currentIndex]
                    const previousData = currentIndex > 0 ? monthlyExpenses[currentIndex - 1] : null
                    
                    const formatCurrency = (value) => {
                      return new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency: 'USD',
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0,
                      }).format(value)
                    }
                    
                    const calculatePercentageChange = (current, previous) => {
                      if (!previous || previous === 0) return null
                      const change = ((current - previous) / previous) * 100
                      return change
                    }
                    
                    const formatPercentage = (percentage) => {
                      if (percentage === null) return ''
                      const sign = percentage >= 0 ? '+' : ''
                      const color = percentage >= 0 ? 'text-red-600' : 'text-green-600'
                      return <span className={`ml-2 ${color}`}>({sign}{percentage.toFixed(1)}%)</span>
                    }
                    
                    return (
                      <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                        <p className="font-semibold mb-2">{label}</p>
                        <div className="space-y-1">
                          <p className="text-red-600">
                            Expenses: {formatCurrency(currentData.expenses)}
                            {previousData && previousData.expenses > 0 && formatPercentage(calculatePercentageChange(currentData.expenses, previousData.expenses))}
                          </p>
                        </div>
                      </div>
                    )
                  }
                  return null
                }} />
                <Legend />
                <Bar dataKey="expenses" fill="#ef4444" name="G&A Expenses" maxBarSize={60} />
                {/* Average Expenses Line */}
                <Line 
                  type="monotone"
                  dataKey="avgExpenses"
                  stroke="#666"
                  strokeDasharray="5 5"
                  strokeWidth={2}
                  name="Avg Expenses"
                  dot={false}
                  legendType="none"
                />
                {/* Add ReferenceLine for the label */}
                {monthlyExpenses && monthlyExpenses.length > 0 && (() => {
                  const currentDate = new Date()
                  const currentMonthIndex = currentDate.getMonth()
                  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                  const currentMonthName = monthNames[currentMonthIndex]
                  
                  // Calculate average excluding current month and incomplete months
                  const monthsWithData = monthlyExpenses.filter(item => item.expenses > 0)
                  const roughAverage = monthsWithData.length > 0 
                    ? monthsWithData.reduce((sum, item) => sum + item.expenses, 0) / monthsWithData.length 
                    : 0
                  
                  const completeMonths = monthlyExpenses.filter(item => {
                    return item.month !== currentMonthName && 
                           item.expenses > 0 && 
                           item.expenses > (roughAverage * 0.5)
                  })
                  
                  const avgExpenses = completeMonths.length > 0 
                    ? completeMonths.reduce((sum, item) => sum + item.expenses, 0) / completeMonths.length 
                    : 0
                  
                  if (avgExpenses > 0) {
                    return (
                      <ReferenceLine 
                        y={avgExpenses} 
                        stroke="none"
                        label={{ value: "Average", position: "insideTopRight" }}
                      />
                    )
                  }
                  return null
                })()}
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

      {/* AR Report Section */}
      {arData && (
        <div className="space-y-6">
          <h2 className="text-2xl font-semibold">Accounts Receivable Report</h2>
          
          <div className="grid gap-4 md:grid-cols-2">
            {/* AR Over 90 Days Card */}
            <Card>
              <CardHeader>
                <CardTitle>AR Over 90 Days</CardTitle>
                <CardDescription>Percentage of total accounts receivable</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="text-5xl font-bold text-red-600">{arData.over_90_percentage}%</div>
                    <p className="text-sm text-muted-foreground mt-1">of total AR is over 90 days</p>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Total AR:</span>
                      <span className="font-medium">${(arData.total_ar / 1000).toFixed(0)}k</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Over 90 Days:</span>
                      <span className="font-medium text-red-600">${(arData.over_90_amount / 1000).toFixed(0)}k</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Specific Customers Over 90 Days Card */}
            <Card>
              <CardHeader>
                <CardTitle>Key Customers Over 90 Days</CardTitle>
                <CardDescription>Polaris, Grede, and Owens accounts</CardDescription>
              </CardHeader>
              <CardContent>
                {arData.specific_customers && arData.specific_customers.length > 0 ? (
                  <div className="space-y-3">
                    {arData.specific_customers.map((customer, index) => (
                      <div key={index} className="space-y-1">
                        <div className="flex justify-between items-start">
                          <span className="font-medium">{customer.name}</span>
                          <span className="font-bold text-red-600">
                            ${customer.amount.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>{customer.invoice_count} invoices</span>
                          <span>{customer.max_days_overdue} days overdue</span>
                        </div>
                      </div>
                    ))}
                    <div className="pt-3 mt-3 border-t">
                      <div className="flex justify-between font-bold">
                        <span>Total</span>
                        <span className="text-red-600">
                          ${arData.specific_customers.reduce((sum, c) => sum + c.amount, 0).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No overdue accounts for these customers</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* AR Aging Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>AR Aging Breakdown</CardTitle>
              <CardDescription>Distribution of accounts receivable by age</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={arData.aging_summary}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="bucket" />
                  <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                  <Tooltip 
                    formatter={(value) => `$${value.toLocaleString()}`}
                    labelFormatter={(label) => `${label} days`}
                  />
                  <Bar dataKey="amount">
                    {arData.aging_summary.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={
                          entry.bucket === 'Current' ? '#10b981' :
                          entry.bucket === '1-30' ? '#3b82f6' :
                          entry.bucket === '31-60' ? '#f59e0b' :
                          entry.bucket === '61-90' ? '#ef4444' :
                          entry.bucket === 'Over 90' ? '#991b1b' :
                          '#6b7280'
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {/* AR Debug Info - Temporary */}
      {arDebugData && (
        <Card>
          <CardHeader>
            <CardTitle>AR Debug Information</CardTitle>
            <CardDescription>Temporary debug info to diagnose AR calculation</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2">Raw Totals from ARDetail:</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>Total Records: {arDebugData.raw_totals?.total_records}</div>
                  <div>Raw Total: ${(arDebugData.raw_totals?.raw_total / 1000).toFixed(0)}k</div>
                  <div>Invoice Total: ${(arDebugData.raw_totals?.invoice_total / 1000).toFixed(0)}k</div>
                  <div>Payment Total: ${(arDebugData.raw_totals?.payment_total / 1000).toFixed(0)}k</div>
                  <div>Voucher Total: ${(arDebugData.raw_totals?.voucher_total / 1000).toFixed(0)}k</div>
                  <div>Journal Total: ${(arDebugData.raw_totals?.journal_total / 1000).toFixed(0)}k</div>
                  <div>AR Journal Total: ${(arDebugData.raw_totals?.ar_journal_total / 1000).toFixed(0)}k</div>
                </div>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Net AR Calculation:</h4>
                <div className="text-sm space-y-1">
                  <div>Open Invoices: {arDebugData.net_ar?.open_invoices}</div>
                  <div className="font-bold">Total AR (from query): ${(parseFloat(arDebugData.net_ar?.total_ar || 0) / 1000).toFixed(0)}k</div>
                  <div>Calculated Net: ${(arDebugData.calculated_net / 1000).toFixed(0)}k</div>
                </div>
              </div>
              {arDebugData.entry_types && (
                <div>
                  <h4 className="font-semibold mb-2">Entry Types in ARDetail:</h4>
                  <div className="text-sm space-y-1">
                    {arDebugData.entry_types.map((et, i) => (
                      <div key={i}>
                        Type '{et.EntryType || 'NULL'}': {et.count} records, ${(parseFloat(et.total_amount || 0) / 1000).toFixed(0)}k
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div>
                <h4 className="font-semibold mb-2">Largest Open Balances:</h4>
                <div className="text-sm space-y-1">
                  {arDebugData.largest_open_balances?.slice(0, 5).map((inv, i) => (
                    <div key={i}>
                      Invoice {inv.InvoiceNo}: ${parseFloat(inv.NetBalance).toFixed(2)} - {inv.CustomerName || 'Unknown'}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default AccountingReport