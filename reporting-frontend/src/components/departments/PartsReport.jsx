import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { 
  BarChart, 
  Bar, 
  LineChart,
  Line,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer
} from 'recharts'
import { TrendingUp, TrendingDown, Package } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const PartsReport = ({ user, onNavigate }) => {
  const [partsData, setPartsData] = useState(null)
  const [fillRateData, setFillRateData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [fillRateLoading, setFillRateLoading] = useState(true)

  useEffect(() => {
    fetchPartsData()
    fetchFillRateData()
  }, [])

  const fetchPartsData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setPartsData(data)
      } else {
        console.error('Failed to fetch parts data:', response.status)
        // Set default empty data structure
        setPartsData({
          monthlyPartsRevenue: []
        })
      }
    } catch (error) {
      console.error('Error fetching parts data:', error)
      // Set default empty data structure on error
      setPartsData({
        monthlyPartsRevenue: []
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchFillRateData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts/fill-rate'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setFillRateData(data)
      } else {
        console.error('Failed to fetch fill rate data:', response.status)
        setFillRateData(null)
      }
    } catch (error) {
      console.error('Error fetching fill rate data:', error)
      setFillRateData(null)
    } finally {
      setFillRateLoading(false)
    }
  }


  if (loading) {
    return (
      <LoadingSpinner 
        title="Loading Parts Department" 
        description="Fetching parts data..."
        size="large"
      />
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Parts Department</h1>
        <p className="text-muted-foreground">Monitor parts sales and inventory performance</p>
      </div>

      {/* Parts Fill Rate Card */}
      {fillRateData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Linde Parts Fill Rate
              </span>
              <Badge variant={fillRateData.summary?.fillRate >= 90 ? "success" : "destructive"}>
                {fillRateData.summary?.fillRate?.toFixed(1)}%
              </Badge>
            </CardTitle>
            <CardDescription>
              {fillRateData.period} - Target: 90% fill rate
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{fillRateData.summary?.totalOrders || 0}</p>
                <p className="text-sm text-muted-foreground">Total Orders</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{fillRateData.summary?.filledOrders || 0}</p>
                <p className="text-sm text-muted-foreground">Filled Orders</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{fillRateData.summary?.unfilledOrders || 0}</p>
                <p className="text-sm text-muted-foreground">Stockouts</p>
              </div>
            </div>

            {/* Fill Rate Trend */}
            {fillRateData.fillRateTrend && fillRateData.fillRateTrend.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Fill Rate Trend</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={fillRateData.fillRateTrend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis domain={[0, 100]} />
                    <RechartsTooltip 
                      formatter={(value, name) => {
                        if (name === 'fillRate') return `${value.toFixed(1)}%`
                        return value
                      }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="fillRate" 
                      stroke="#10b981" 
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Problem Parts Table */}
            {fillRateData.problemParts && fillRateData.problemParts.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Parts Frequently Out of Stock</h4>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Part Number</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Stockouts</TableHead>
                      <TableHead className="text-right">Current Stock</TableHead>
                      <TableHead className="text-right">Stockout Rate</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fillRateData.problemParts.map((part) => (
                      <TableRow key={part.partNo}>
                        <TableCell className="font-medium">{part.partNo}</TableCell>
                        <TableCell>{part.description}</TableCell>
                        <TableCell className="text-right">
                          {part.stockoutCount} / {part.totalOrders}
                        </TableCell>
                        <TableCell className="text-right">{part.currentStock}</TableCell>
                        <TableCell className="text-right">
                          <Badge variant={part.stockoutRate > 20 ? "destructive" : "secondary"}>
                            {part.stockoutRate.toFixed(1)}%
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Monthly Parts Revenue */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Parts Revenue</CardTitle>
          <CardDescription>Parts revenue over the last 12 months</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={partsData?.monthlyPartsRevenue || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis 
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <RechartsTooltip 
                formatter={(value) => `$${value.toLocaleString()}`}
              />
              <Bar dataKey="amount" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

export default PartsReport