import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  ReferenceLine,
  ComposedChart,
  Line,
  Legend
} from 'recharts'
import { apiUrl } from '@/lib/api'

const ServiceReport = ({ user, onNavigate }) => {
  const [serviceData, setServiceData] = useState(null)
  const [loading, setLoading] = useState(true)

  // Helper function to calculate percentage change
  const calculatePercentageChange = (current, previous) => {
    if (!previous || previous === 0) return null
    const change = ((current - previous) / previous) * 100
    return change
  }

  // Helper function to format percentage with color
  const formatPercentage = (percentage) => {
    if (percentage === null) return ''
    const sign = percentage >= 0 ? '+' : ''
    const color = percentage >= 0 ? 'text-green-600' : 'text-red-600'
    return <span className={`ml-2 ${color}`}>({sign}{percentage.toFixed(1)}%)</span>
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  useEffect(() => {
    fetchServiceData()
  }, [])

  const fetchServiceData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/service'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setServiceData(data)
      } else {
        console.error('Failed to fetch service data:', response.status)
        // Set default empty data structure
        setServiceData({
          monthlyLaborRevenue: []
        })
      }
    } catch (error) {
      console.error('Error fetching service data:', error)
      // Set default empty data structure on error
      setServiceData({
        monthlyLaborRevenue: []
      })
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <LoadingSpinner 
        title="Loading Service Department" 
        description="Fetching service data..."
        size="large"
      />
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Service Department</h1>
        <p className="text-muted-foreground">Monitor service operations</p>
      </div>

      {/* Monthly Labor Revenue */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle>Monthly Labor Revenue & Margin</CardTitle>
              <CardDescription>Labor revenue and gross margin % over the last 12 months</CardDescription>
            </div>
            {serviceData?.monthlyLaborRevenue && serviceData.monthlyLaborRevenue.length > 0 && (() => {
              // Only include historical months (before current month)
              const currentDate = new Date()
              const currentMonthIndex = currentDate.getMonth()
              const currentYear = currentDate.getFullYear()
              
              // Month names in order
              const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
              const currentMonthName = monthNames[currentMonthIndex]
              
              // Get index of current month in the data
              const currentMonthDataIndex = serviceData.monthlyLaborRevenue.findIndex(item => item.month === currentMonthName)
              
              // Filter to only include months before current month with positive revenue
              const historicalMonths = currentMonthDataIndex > 0 
                ? serviceData.monthlyLaborRevenue.slice(0, currentMonthDataIndex).filter(item => item.amount > 0)
                : serviceData.monthlyLaborRevenue.filter(item => item.amount > 0 && item.month !== currentMonthName)
              
              const avgRevenue = historicalMonths.length > 0 ? 
                historicalMonths.reduce((sum, item) => sum + item.amount, 0) / historicalMonths.length : 0
              const avgMargin = historicalMonths.length > 0 ? 
                historicalMonths.reduce((sum, item) => sum + (item.margin || 0), 0) / historicalMonths.length : 0
              
              return (
                <div className="text-right">
                  <div className="mb-2">
                    <p className="text-sm text-muted-foreground">Avg Revenue</p>
                    <p className="text-lg font-semibold">{formatCurrency(avgRevenue)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Avg Margin</p>
                    <p className="text-lg font-semibold">{avgMargin.toFixed(1)}%</p>
                  </div>
                </div>
              )
            })()}
          </div>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <ComposedChart data={serviceData?.monthlyLaborRevenue || []} margin={{ top: 20, right: 70, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis 
                yAxisId="revenue"
                orientation="left"
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <YAxis
                yAxisId="margin"
                orientation="right"
                domain={[0, 100]}
                tickFormatter={(value) => `${value}%`}
              />
              <RechartsTooltip 
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length && serviceData?.monthlyLaborRevenue) {
                    const data = serviceData.monthlyLaborRevenue
                    const currentIndex = data.findIndex(item => item.month === label)
                    const currentData = data[currentIndex]
                    const previousData = currentIndex > 0 ? data[currentIndex - 1] : null
                    
                    return (
                      <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                        <p className="font-semibold mb-2">{label}</p>
                        <div className="space-y-1">
                          <p className="text-blue-600">
                            Revenue: {formatCurrency(currentData.amount)}
                            {formatPercentage(calculatePercentageChange(currentData.amount, previousData?.amount))}
                          </p>
                          <p className="text-green-600">
                            Margin: {currentData.margin || 0}%
                            {previousData && currentData.margin && previousData.margin && (
                              <span className={`ml-2 text-sm ${currentData.margin > previousData.margin ? 'text-green-600' : 'text-red-600'}`}>
                                ({currentData.margin > previousData.margin ? '+' : ''}{(currentData.margin - previousData.margin).toFixed(1)}pp)
                              </span>
                            )}
                          </p>
                        </div>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Legend />
              <Bar yAxisId="revenue" dataKey="amount" fill="#3b82f6" name="Revenue" />
              <Line 
                yAxisId="margin" 
                type="monotone" 
                dataKey="margin" 
                stroke="#10b981" 
                strokeWidth={3}
                name="Gross Margin %"
                dot={{ fill: '#10b981', r: 4 }}
              />
              {serviceData?.monthlyLaborRevenue && serviceData.monthlyLaborRevenue.length > 0 && (() => {
                // Only include historical months (before current month)
                const currentDate = new Date()
                const currentMonthIndex = currentDate.getMonth()
                const currentYear = currentDate.getFullYear()
                
                // Month names in order
                const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                const currentMonthName = monthNames[currentMonthIndex]
                
                // Get index of current month in the data
                const currentMonthDataIndex = serviceData.monthlyLaborRevenue.findIndex(item => item.month === currentMonthName)
                
                // Filter to only include months before current month with positive revenue
                const historicalMonths = currentMonthDataIndex > 0 
                  ? serviceData.monthlyLaborRevenue.slice(0, currentMonthDataIndex).filter(item => item.amount > 0)
                  : serviceData.monthlyLaborRevenue.filter(item => item.amount > 0 && item.month !== currentMonthName)
                
                const avgRevenue = historicalMonths.length > 0 ? 
                  historicalMonths.reduce((sum, item) => sum + item.amount, 0) / historicalMonths.length : 0
                const avgMargin = historicalMonths.length > 0 ? 
                  historicalMonths.reduce((sum, item) => sum + (item.margin || 0), 0) / historicalMonths.length : 0
                
                return (
                  <>
                    <ReferenceLine 
                      yAxisId="revenue"
                      y={avgRevenue} 
                      stroke="#666" 
                      strokeDasharray="3 3"
                      label={{ value: "Avg Revenue", position: "insideTopLeft" }}
                    />
                    <ReferenceLine 
                      yAxisId="margin"
                      y={avgMargin} 
                      stroke="#059669" 
                      strokeDasharray="3 3"
                      label={{ value: "Avg Margin", position: "insideTopRight" }}
                    />
                  </>
                )
              })()}
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

export default ServiceReport