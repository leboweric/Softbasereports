import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
import AROver90Report from '@/components/AROver90Report'
import APReport from '@/components/APReport'
import SalesCommissionReport from '@/components/SalesCommissionReport'
import ControlNumberReport from '@/components/ControlNumberReport'

const AccountingReport = ({ user }) => {
  const [monthlyExpenses, setMonthlyExpenses] = useState([])
  const [arData, setArData] = useState(null)
  const [apTotal, setApTotal] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAccountingData()
    fetchARData()
    fetchAPTotal()
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
        // Debug: log what buckets we're getting
        if (data.debug_buckets) {
          console.log('AR Debug - Buckets:', data.debug_buckets)
          console.log('AR Debug - Over 90 calculation:', data.over_90_amount)
        }
      } else {
        console.error('AR report error:', response.status, response.statusText)
        const errorText = await response.text()
        console.error('Error details:', errorText)
      }
    } catch (error) {
      console.error('Error fetching AR data:', error)
    }
  }

  const fetchAPTotal = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/accounting/ap-total'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setApTotal(data)
      } else {
        console.error('AP total error:', response.status, response.statusText)
      }
    } catch (error) {
      console.error('Error fetching AP total:', error)
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

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="ar">Accounts Receivable</TabsTrigger>
          <TabsTrigger value="ap">Accounts Payable</TabsTrigger>
          <TabsTrigger value="commissions">Sales Commissions</TabsTrigger>
          <TabsTrigger value="control">Control Numbers</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Total Accounts Receivable</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">$1.697M</div>
              </CardContent>
            </Card>
            
            {arData && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">AR Over 90 Days</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${arData.over_90_percentage < 10 ? 'text-green-600' : 'text-red-600'}`}>
                    {arData.over_90_percentage}%
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">${(arData.over_90_amount / 1000).toFixed(0)}k of total AR</p>
                </CardContent>
              </Card>
            )}
            
            {apTotal && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Total Accounts Payable</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{apTotal.formatted}</div>
                </CardContent>
              </Card>
            )}
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

      {/* Key Customers Over 90 Days */}
      {arData && arData.specific_customers && arData.specific_customers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Key Customers Over 90 Days</CardTitle>
            <CardDescription>Polaris, Grede, and Owens accounts</CardDescription>
          </CardHeader>
          <CardContent>
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
                    <span>Oldest: {customer.max_days_overdue} days</span>
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
          </CardContent>
        </Card>
      )}
        </TabsContent>

        <TabsContent value="ar" className="space-y-6">
          <AROver90Report user={user} />
        </TabsContent>

        <TabsContent value="ap" className="space-y-6">
          <APReport user={user} />
        </TabsContent>

        <TabsContent value="commissions" className="space-y-6">
          <SalesCommissionReport user={user} />
        </TabsContent>

        <TabsContent value="control" className="space-y-6">
          <ControlNumberReport />
        </TabsContent>
      </Tabs>

    </div>
  )
}

export default AccountingReport