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
  ReferenceLine
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
              <CardTitle>Monthly Labor Revenue</CardTitle>
              <CardDescription>Labor revenue over the last 12 months</CardDescription>
            </div>
            {serviceData?.monthlyLaborRevenue && serviceData.monthlyLaborRevenue.length > 0 && (() => {
              const completeMonths = serviceData.monthlyLaborRevenue.slice(0, -1)
              const average = completeMonths.reduce((sum, item) => sum + item.amount, 0) / completeMonths.length
              return (
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Average</p>
                  <p className="text-lg font-semibold">{formatCurrency(average)}</p>
                </div>
              )
            })()}
          </div>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={serviceData?.monthlyLaborRevenue || []} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis 
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <RechartsTooltip 
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length && serviceData?.monthlyLaborRevenue) {
                    const data = serviceData.monthlyLaborRevenue
                    const currentIndex = data.findIndex(item => item.month === label)
                    const currentValue = payload[0].value
                    const previousValue = currentIndex > 0 ? data[currentIndex - 1].amount : null
                    
                    return (
                      <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                        <p className="font-semibold mb-1">{label}</p>
                        <p className="text-blue-600">
                          {formatCurrency(currentValue)}
                          {formatPercentage(calculatePercentageChange(currentValue, previousValue))}
                        </p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Bar dataKey="amount" fill="#3b82f6" />
              {serviceData?.monthlyLaborRevenue && serviceData.monthlyLaborRevenue.length > 0 && (() => {
                // Only calculate average for complete months (exclude current month)
                const completeMonths = serviceData.monthlyLaborRevenue.slice(0, -1)
                const average = completeMonths.reduce((sum, item) => sum + item.amount, 0) / completeMonths.length
                return (
                  <ReferenceLine 
                    y={average} 
                    stroke="#666" 
                    strokeDasharray="3 3"
                    label={{ value: "Average", position: "insideTopRight" }}
                  />
                )
              })()}
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

export default ServiceReport