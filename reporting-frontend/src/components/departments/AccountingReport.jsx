import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine
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
                <CardDescription>General & Administrative expenses (Payroll, Professional Services, etc.)</CardDescription>
              </div>
              {monthlyExpenses && monthlyExpenses.length > 1 && (() => {
                // Calculate average of all months first
                const allMonths = monthlyExpenses.slice(0, -1)
                const totalAverage = allMonths.reduce((sum, item) => sum + item.expenses, 0) / allMonths.length
                
                // Filter out months that are likely incomplete (less than 50% of average)
                const completeMonths = allMonths.filter(month => month.expenses > totalAverage * 0.5)
                
                if (completeMonths.length === 0) return null
                
                const average = completeMonths.reduce((sum, item) => sum + item.expenses, 0) / completeMonths.length
                return (
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Average (Complete Months)</p>
                    <p className="text-lg font-semibold">${(average / 1000).toFixed(0)}k</p>
                  </div>
                )
              })()}
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={monthlyExpenses.slice(0, -1)} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                {(() => {
                  const allMonths = monthlyExpenses.slice(0, -1)
                  const totalAverage = allMonths.reduce((sum, item) => sum + item.expenses, 0) / allMonths.length
                  const completeMonths = allMonths.filter(month => month.expenses > totalAverage * 0.5)
                  if (completeMonths.length === 0) return null
                  const average = completeMonths.reduce((sum, item) => sum + item.expenses, 0) / completeMonths.length
                  return (
                    <ReferenceLine 
                      y={average} 
                      stroke="#6b7280" 
                      strokeDasharray="5 5" 
                      label={{ value: `Avg: $${(average / 1000).toFixed(0)}k`, position: "right" }}
                    />
                  )
                })()}
                <Tooltip content={({ active, payload, label }) => {
                  if (active && payload && payload.length && monthlyExpenses) {
                    const data = monthlyExpenses.slice(0, -1)
                    const currentIndex = data.findIndex(item => item.month === label)
                    const currentValue = payload[0].value
                    const previousValue = currentIndex > 0 ? data[currentIndex - 1].expenses : null
                    
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
                        <p className="font-semibold mb-1">{label}</p>
                        <p className="text-gray-900">
                          {formatCurrency(currentValue)}
                          {previousValue && formatPercentage(calculatePercentageChange(currentValue, previousValue))}
                        </p>
                      </div>
                    )
                  }
                  return null
                }} />
                <Bar 
                  dataKey="expenses" 
                  fill="#ef4444"
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
    </div>
  )
}

export default AccountingReport