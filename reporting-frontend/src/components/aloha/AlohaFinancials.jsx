import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { apiUrl } from '@/lib/api'
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  BarChart3,
  RefreshCw,
  Building2,
  ArrowUpRight,
  ArrowDownRight,
  Calendar
} from 'lucide-react'

const AlohaFinancials = ({ user, organization }) => {
  const [loading, setLoading] = useState(true)
  const [financialData, setFinancialData] = useState(null)
  const [year, setYear] = useState(new Date().getFullYear())

  useEffect(() => {
    fetchFinancials()
  }, [year])

  const fetchFinancials = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/aloha/dashboard/financials?year=${year}`), {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setFinancialData(data)
      }
    } catch (err) {
      console.error('Financials fetch error:', err)
    }
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-teal-500" />
        <span className="ml-3 text-gray-600">Loading financials...</span>
      </div>
    )
  }

  const isAwaitingConnection = financialData?.status === 'awaiting_sap_connection'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <DollarSign className="h-7 w-7 text-green-600" />
            Consolidated Financials
          </h1>
          <p className="text-gray-500 mt-1">
            Profit & Loss across all subsidiary companies
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            value={year}
            onChange={(e) => setYear(parseInt(e.target.value))}
          >
            {[2026, 2025, 2024].map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
          <Button variant="outline" size="sm" onClick={fetchFinancials}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {isAwaitingConnection ? (
        <Card className="border-2 border-dashed border-gray-200">
          <CardContent className="py-16 text-center">
            <DollarSign className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-600">Financial Data Unavailable</h3>
            <p className="text-gray-400 mt-2 max-w-md mx-auto">
              Connect your SAP ERP systems to view consolidated financial reports.
              Revenue, expenses, and P&L data will be automatically synced from each subsidiary.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* YTD Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <SummaryCard title="Revenue" value={financialData?.ytd_summary?.revenue} icon={TrendingUp} color="green" />
            <SummaryCard title="COGS" value={financialData?.ytd_summary?.cogs} icon={ArrowDownRight} color="red" />
            <SummaryCard title="Gross Profit" value={financialData?.ytd_summary?.gross_profit} icon={BarChart3} color="blue" />
            <SummaryCard title="OpEx" value={financialData?.ytd_summary?.operating_expenses} icon={ArrowUpRight} color="orange" />
            <SummaryCard title="Net Income" value={financialData?.ytd_summary?.net_income} icon={DollarSign} color="teal" />
          </div>

          {/* Monthly breakdown placeholder */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Monthly P&L — {year}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center h-48 text-gray-400">
                <p>Monthly financial data will populate once SAP ETL is configured</p>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}

const SummaryCard = ({ title, value, icon: Icon, color }) => {
  const colorMap = {
    green: 'text-green-600 bg-green-50',
    red: 'text-red-600 bg-red-50',
    blue: 'text-blue-600 bg-blue-50',
    orange: 'text-orange-600 bg-orange-50',
    teal: 'text-teal-600 bg-teal-50',
  }
  const classes = colorMap[color] || colorMap.blue

  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-center gap-2 mb-1">
          <div className={`p-1.5 rounded ${classes.split(' ')[1]}`}>
            <Icon className={`h-4 w-4 ${classes.split(' ')[0]}`} />
          </div>
          <span className="text-xs text-gray-500">{title}</span>
        </div>
        <p className="text-xl font-bold">
          {value !== null && value !== undefined ? `$${value.toLocaleString()}` : '—'}
        </p>
      </CardContent>
    </Card>
  )
}

export default AlohaFinancials
