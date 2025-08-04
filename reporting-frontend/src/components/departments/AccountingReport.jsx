import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { 
  ComposedChart,
  Bar, 
  Line,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine,
  Legend
} from 'recharts'
import { apiUrl } from '@/lib/api'

const AccountingReport = ({ user }) => {
  const [monthlyExpenses, setMonthlyExpenses] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAccountingData()
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
                // Only include historical months (before current month)
                const currentDate = new Date()
                const currentMonthIndex = currentDate.getMonth()
                const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                const currentMonthName = monthNames[currentMonthIndex]
                
                // Find current month in data and get historical months
                const currentMonthDataIndex = monthlyExpenses.findIndex(item => item.month === currentMonthName)
                const historicalMonths = currentMonthDataIndex > 0 
                  ? monthlyExpenses.slice(0, currentMonthDataIndex).filter(item => item.expenses > 0)
                  : monthlyExpenses.filter((item, index) => {
                      const monthIndex = monthNames.indexOf(item.month)
                      return monthIndex < currentMonthIndex && item.expenses > 0
                    })
                
                if (historicalMonths.length === 0) return null
                
                const avgExpenses = historicalMonths.reduce((sum, item) => sum + item.expenses, 0) / historicalMonths.length
                
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
                  
                  const currentMonthDataIndex = data.findIndex(item => item.month === currentMonthName)
                  const historicalMonths = currentMonthDataIndex > 0 
                    ? data.slice(0, currentMonthDataIndex).filter(item => item.expenses > 0)
                    : data.filter((item, index) => {
                        const monthIndex = monthNames.indexOf(item.month)
                        return monthIndex < currentMonthIndex && item.expenses > 0
                      })
                  
                  const avgExpenses = historicalMonths.length > 0 
                    ? historicalMonths.reduce((sum, item) => sum + item.expenses, 0) / historicalMonths.length 
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
                  const currentMonthDataIndex = monthlyExpenses.findIndex(item => item.month === currentMonthName)
                  const historicalMonths = currentMonthDataIndex > 0 
                    ? monthlyExpenses.slice(0, currentMonthDataIndex).filter(item => item.expenses > 0)
                    : monthlyExpenses.filter((item, index) => {
                        const monthIndex = monthNames.indexOf(item.month)
                        return monthIndex < currentMonthIndex && item.expenses > 0
                      })
                  const avgExpenses = historicalMonths.length > 0 
                    ? historicalMonths.reduce((sum, item) => sum + item.expenses, 0) / historicalMonths.length 
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
    </div>
  )
}

export default AccountingReport