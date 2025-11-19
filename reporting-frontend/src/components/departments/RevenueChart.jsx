import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from 'recharts'
import { Info } from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

const formatCurrency = (value) => {
  if (!value || value === 0) return '$0'
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

const formatPercentage = (value) => {
  if (value === null || value === undefined) return ''
  const sign = value > 0 ? '+' : ''
  return ` (${sign}${value.toFixed(1)}%)`
}

export default function RevenueChart({ 
  data, 
  title, 
  description, 
  tooltipInfo,
  barColor = "#10b981"
}) {
  // Sort data by month order
  const monthOrder = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const sortedData = data ? [...data].sort((a, b) => 
    monthOrder.indexOf(a.month) - monthOrder.indexOf(b.month)
  ) : []

  // Calculate average revenue and margin (excluding current month)
  const currentDate = new Date()
  const currentMonthIndex = currentDate.getMonth()
  const currentMonthName = monthOrder[currentMonthIndex]
  
  const historicalMonths = sortedData.filter(item => 
    item.month !== currentMonthName && item.amount > 0
  )
  
  const avgRevenue = historicalMonths.length > 0 ? 
    historicalMonths.reduce((sum, item) => sum + item.amount, 0) / historicalMonths.length : 0
  const avgMargin = historicalMonths.length > 0 ? 
    historicalMonths.reduce((sum, item) => sum + (item.margin || 0), 0) / historicalMonths.length : 0

  // Calculate trendline
  const dataWithTrend = (() => {
    if (historicalMonths.length < 2) return sortedData

    // Calculate linear regression
    const n = historicalMonths.length
    const sumX = historicalMonths.reduce((sum, _, i) => sum + i, 0)
    const sumY = historicalMonths.reduce((sum, item) => sum + item.amount, 0)
    const meanX = sumX / n
    const meanY = sumY / n
    
    let numerator = 0
    let denominator = 0
    historicalMonths.forEach((item, i) => {
      numerator += (i - meanX) * (item.amount - meanY)
      denominator += (i - meanX) * (i - meanX)
    })
    
    const slope = denominator !== 0 ? numerator / denominator : 0
    const intercept = meanY - slope * meanX

    // Add trendline to data
    return sortedData.map((item) => {
      const isComplete = historicalMonths.some(hm => hm.month === item.month)
      const completeIndex = historicalMonths.findIndex(hm => hm.month === item.month)
      const trendValue = isComplete && completeIndex >= 0 ? slope * completeIndex + intercept : null
      
      return {
        ...item,
        trendline: trendValue
      }
    })
  })()

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle>{title}</CardTitle>
              {tooltipInfo && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-sm">
                      {tooltipInfo}
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </div>
            <CardDescription>{description}</CardDescription>
          </div>
          {avgRevenue > 0 && (
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
          )}
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <ComposedChart data={dataWithTrend} margin={{ top: 40, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
            <RechartsTooltip 
              content={({ active, payload, label }) => {
                if (active && payload && payload.length && sortedData) {
                  const currentIndex = sortedData.findIndex(item => item.month === label)
                  const currentData = sortedData[currentIndex]
                  const previousData = currentIndex > 0 ? sortedData[currentIndex - 1] : null
                  
                  return (
                    <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                      <p className="font-semibold mb-2">{label}</p>
                      <div className="space-y-1">
                        <p style={{ color: barColor }}>
                          Revenue: {formatCurrency(currentData.amount)}
                          {formatPercentage(calculatePercentageChange(currentData.amount, previousData?.amount))}
                        </p>
                        {currentData.margin !== null && currentData.margin !== undefined && (
                          <p className="text-amber-600">
                            Margin: {currentData.margin}%
                            {previousData && previousData.margin !== null && previousData.margin !== undefined && (
                              <span className={`ml-2 text-sm ${currentData.margin > previousData.margin ? 'text-green-600' : 'text-red-600'}`}>
                                ({currentData.margin > previousData.margin ? '+' : ''}{(currentData.margin - previousData.margin).toFixed(1)}pp)
                              </span>
                            )}
                          </p>
                        )}
                      </div>
                    </div>
                  )
                }
                return null
              }}
            />
            <Bar dataKey="amount" fill={barColor} radius={[4, 4, 0, 0]} />
            <Line 
              type="monotone" 
              dataKey="trendline" 
              stroke="#059669" 
              strokeWidth={2} 
              dot={false}
              strokeDasharray="5 5"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
