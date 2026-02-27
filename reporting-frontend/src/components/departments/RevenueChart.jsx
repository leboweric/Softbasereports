import React, { useState, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
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
  barColor = "#10b981",
  chartId,
  fiscalYearStartMonth
}) {
  const [includeCurrentMonth, setIncludeCurrentMonth] = useState(false)

  // Sort data by month order
  const monthOrder = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

  // Filter data based on toggle
  const filteredData = useMemo(() => {
    if (!data) return []
    const sorted = [...data].sort((a, b) => {
      // Parse month strings like "Feb '26" or "Jan '25"
      const parseMonth = (m) => {
        const parts = m.match(/^(\w+)\s*'?(\d{2})?$/)
        if (!parts) return monthOrder.indexOf(m)
        const monthIdx = monthOrder.indexOf(parts[1])
        const year = parts[2] ? parseInt(parts[2]) : 0
        return year * 12 + monthIdx
      }
      return parseMonth(a.month) - parseMonth(b.month)
    })
    if (includeCurrentMonth) return sorted
    const now = new Date()
    const currentMonthStr = now.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }).replace(' ', " '")
    return sorted.filter(item => item.month !== currentMonthStr)
  }, [data, includeCurrentMonth])

  // Calculate average revenue and margin from filtered data
  const monthsWithRevenue = filteredData.filter(item => item.amount > 0)
  
  const avgRevenue = monthsWithRevenue.length > 0 ? 
    monthsWithRevenue.reduce((sum, item) => sum + item.amount, 0) / monthsWithRevenue.length : 0
  const avgMargin = monthsWithRevenue.length > 0 ? 
    monthsWithRevenue.reduce((sum, item) => sum + (item.margin || 0), 0) / monthsWithRevenue.length : 0

  // Calculate trendline from filtered data, starting from fiscal year if provided
  const dataWithTrend = useMemo(() => {
    if (monthsWithRevenue.length < 2) return filteredData

    // Determine which months to include in the trend calculation
    let trendMonths = monthsWithRevenue
    
    if (fiscalYearStartMonth) {
      const now = new Date()
      const currentMonth = now.getMonth() + 1
      const fyStartYear = currentMonth >= fiscalYearStartMonth ? now.getFullYear() : now.getFullYear() - 1
      
      // Filter to only months from fiscal year start onwards
      trendMonths = monthsWithRevenue.filter(item => {
        if (item.month_number && item.year) {
          return item.year > fyStartYear || (item.year === fyStartYear && item.month_number >= fiscalYearStartMonth)
        }
        // Fallback: parse month string like "Nov '25"
        const monthStr = item.month
        if (!monthStr) return false
        const monthAbbr = monthStr.split(' ')[0].replace("'", '')
        const parsedMonth = monthOrder.indexOf(monthAbbr) + 1
        const yearMatch = monthStr.match(/'(\d{2})/)
        const parsedYear = yearMatch ? 2000 + parseInt(yearMatch[1]) : null
        if (parsedMonth && parsedYear) {
          return parsedYear > fyStartYear || (parsedYear === fyStartYear && parsedMonth >= fiscalYearStartMonth)
        }
        return true
      })
      
      // Fall back to all months if fiscal year filter yields too few points
      if (trendMonths.length < 2) {
        trendMonths = monthsWithRevenue
      }
    }

    // Calculate linear regression on the trend months
    const n = trendMonths.length
    const sumX = trendMonths.reduce((sum, _, i) => sum + i, 0)
    const sumY = trendMonths.reduce((sum, item) => sum + item.amount, 0)
    const meanX = sumX / n
    const meanY = sumY / n
    
    let numerator = 0
    let denominator = 0
    trendMonths.forEach((item, i) => {
      numerator += (i - meanX) * (item.amount - meanY)
      denominator += (i - meanX) * (i - meanX)
    })
    
    const slope = denominator !== 0 ? numerator / denominator : 0
    const intercept = meanY - slope * meanX

    // Build a set of trend month keys for quick lookup
    const trendMonthSet = new Set(trendMonths.map(m => m.month))

    // Add trendline to data - only for months in the trend period
    return filteredData.map((item) => {
      const isInTrendPeriod = trendMonthSet.has(item.month)
      if (!isInTrendPeriod) {
        return { ...item, trendline: null }
      }
      const trendIndex = trendMonths.findIndex(hm => hm.month === item.month)
      const trendValue = trendIndex >= 0 ? slope * trendIndex + intercept : null
      
      return {
        ...item,
        trendline: trendValue
      }
    })
  }, [filteredData, monthsWithRevenue, fiscalYearStartMonth])

  const switchId = chartId ? `include-current-month-${chartId}` : `include-current-month-${title?.replace(/\s+/g, '-').toLowerCase()}`

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
            <div className="flex items-center gap-2 mt-2">
              <Switch
                id={switchId}
                checked={includeCurrentMonth}
                onCheckedChange={setIncludeCurrentMonth}
              />
              <Label htmlFor={switchId} className="text-sm text-muted-foreground cursor-pointer">
                Include current month
              </Label>
            </div>
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
                if (active && payload && payload.length && filteredData) {
                  const currentIndex = filteredData.findIndex(item => item.month === label)
                  const currentData = filteredData[currentIndex]
                  const previousData = currentIndex > 0 ? filteredData[currentIndex - 1] : null
                  
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
