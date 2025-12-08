import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
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
import { DollarSign, TrendingUp, TrendingDown, Calendar, ArrowRight, Lock, AlertCircle, CheckCircle } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const MyCommissions = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [reportData, setReportData] = useState(null)
  const [transactionHistory, setTransactionHistory] = useState([])
  const [settings, setSettings] = useState(null)
  const [error, setError] = useState(null)
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date()
    const prevMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    return `${prevMonth.getFullYear()}-${String(prevMonth.getMonth() + 1).padStart(2, '0')}`
  })

  // Generate month options (from March 2025)
  const generateMonthOptions = () => {
    const options = []
    const now = new Date()
    const earliestDate = new Date(2025, 2, 1) // March 2025

    for (let i = 0; i < 24; i++) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1)
      if (date < earliestDate) break

      const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      const label = date.toLocaleString('default', { month: 'long', year: 'numeric' })
      options.push({ value, label })
    }
    return options
  }

  useEffect(() => {
    fetchMyCommissionData()
  }, [selectedMonth])

  const fetchMyCommissionData = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = localStorage.getItem('token')

      // Fetch report data for selected month
      const reportResponse = await fetch(apiUrl(`/api/sales-rep-comp/my-report/${selectedMonth}`), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (reportResponse.ok) {
        const data = await reportResponse.json()
        setReportData(data.report)
      } else {
        throw new Error('Failed to fetch commission report')
      }

      // Fetch all settings to get this user's info
      const settingsResponse = await fetch(apiUrl('/api/sales-rep-comp/settings'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (settingsResponse.ok) {
        const settingsData = await settingsResponse.json()
        // For now, take the first active setting - will be filtered by user in backend
        const activeSettings = settingsData.settings?.filter(s => s.is_active) || []
        setSettings(activeSettings[0] || null)

        // Fetch transaction history for first rep
        if (activeSettings[0]) {
          const historyResponse = await fetch(
            apiUrl(`/api/sales-rep-comp/transactions/${encodeURIComponent(activeSettings[0].salesman_name)}`),
            {
              headers: {
                'Authorization': `Bearer ${token}`,
              },
            }
          )

          if (historyResponse.ok) {
            const historyData = await historyResponse.json()
            setTransactionHistory(historyData.transactions || [])
          }
        }
      }
    } catch (err) {
      console.error('Error fetching commission data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value || 0)
  }

  const formatMonth = (yearMonth) => {
    const [year, month] = yearMonth.split('-')
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
    return `${monthNames[parseInt(month, 10) - 1]} ${year}`
  }

  const getBalanceStatus = (balance) => {
    if (balance > 0) {
      return {
        label: 'You Owe',
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        icon: TrendingDown
      }
    } else if (balance < 0) {
      return {
        label: 'To Be Paid',
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        icon: TrendingUp
      }
    }
    return {
      label: 'Even',
      color: 'text-gray-600',
      bgColor: 'bg-gray-50',
      icon: CheckCircle
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="large" />
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="py-8 text-center">
          <AlertCircle className="h-12 w-12 mx-auto mb-4 text-red-600" />
          <h3 className="text-lg font-semibold text-red-600">Error Loading Commission Data</h3>
          <p className="text-red-500 mt-2">{error}</p>
          <Button className="mt-4" onClick={fetchMyCommissionData}>
            Try Again
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!reportData || reportData.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <DollarSign className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-600">No Commission Data Available</h3>
          <p className="text-gray-500 mt-2">
            Contact your administrator to set up your compensation plan.
          </p>
        </CardContent>
      </Card>
    )
  }

  // Get the rep's data for the selected month
  const myData = reportData[0] // For now, just show first rep's data

  const balanceStatus = getBalanceStatus(myData.closing_balance)
  const BalanceIcon = balanceStatus.icon

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">My Commission Report</h1>
          <p className="text-muted-foreground">
            Track your earnings and draw balance
          </p>
        </div>
        <Select value={selectedMonth} onValueChange={setSelectedMonth}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Select month" />
          </SelectTrigger>
          <SelectContent>
            {generateMonthOptions().map(option => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Calendar className="h-4 w-4 text-blue-600" />
              Monthly Draw
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {formatCurrency(myData.monthly_draw)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-green-600" />
              Commissions Earned
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(myData.gross_commissions)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              {myData.gross_commissions >= myData.monthly_draw
                ? <TrendingUp className="h-4 w-4 text-green-600" />
                : <TrendingDown className="h-4 w-4 text-orange-600" />
              }
              Over/(Short)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${myData.gross_commissions >= myData.monthly_draw ? 'text-green-600' : 'text-orange-600'}`}>
              {formatCurrency(myData.gross_commissions - myData.monthly_draw)}
            </div>
          </CardContent>
        </Card>

        <Card className={balanceStatus.bgColor}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <BalanceIcon className={`h-4 w-4 ${balanceStatus.color}`} />
              Current Balance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${balanceStatus.color}`}>
              {formatCurrency(Math.abs(myData.closing_balance))}
            </div>
            <Badge variant="outline" className="mt-1">
              {balanceStatus.label}
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Breakdown - {formatMonth(selectedMonth)}</CardTitle>
          <CardDescription>
            Detailed view of your commission activity this month
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm text-muted-foreground">Opening Balance</p>
                <p className={`text-lg font-semibold ${myData.opening_balance > 0 ? 'text-red-600' : myData.opening_balance < 0 ? 'text-green-600' : ''}`}>
                  {formatCurrency(myData.opening_balance)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Draw Taken</p>
                <p className="text-lg font-semibold text-blue-600">
                  {myData.draw_taken ? formatCurrency(myData.draw_amount) : '$0.00 (Banked)'}
                </p>
              </div>
            </div>

            <div className="flex items-center justify-center gap-4 py-4">
              <div className="text-center">
                <p className="text-sm text-muted-foreground">Opening Balance</p>
                <p className="text-lg font-semibold">{formatCurrency(myData.opening_balance)}</p>
              </div>
              <ArrowRight className="h-5 w-5 text-gray-400" />
              <div className="text-center">
                <p className="text-sm text-muted-foreground">+ Draw</p>
                <p className="text-lg font-semibold text-blue-600">
                  {formatCurrency(myData.draw_taken ? myData.draw_amount : 0)}
                </p>
              </div>
              <ArrowRight className="h-5 w-5 text-gray-400" />
              <div className="text-center">
                <p className="text-sm text-muted-foreground">- Commissions</p>
                <p className="text-lg font-semibold text-green-600">
                  {formatCurrency(myData.gross_commissions)}
                </p>
              </div>
              <ArrowRight className="h-5 w-5 text-gray-400" />
              <div className="text-center">
                <p className="text-sm text-muted-foreground">= Closing Balance</p>
                <p className={`text-lg font-semibold ${myData.closing_balance > 0 ? 'text-red-600' : myData.closing_balance < 0 ? 'text-green-600' : ''}`}>
                  {formatCurrency(myData.closing_balance)}
                </p>
              </div>
            </div>

            {myData.is_locked && (
              <div className="flex items-center gap-2 text-amber-600 bg-amber-50 p-3 rounded-lg">
                <Lock className="h-4 w-4" />
                <span className="text-sm">This month has been finalized and locked</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Transaction History */}
      <Card>
        <CardHeader>
          <CardTitle>Commission History</CardTitle>
          <CardDescription>
            Your monthly commission activity over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          {transactionHistory.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No transaction history available yet.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Month</TableHead>
                  <TableHead className="text-right">Opening Balance</TableHead>
                  <TableHead className="text-right">Draw Taken</TableHead>
                  <TableHead className="text-right">Commissions</TableHead>
                  <TableHead className="text-right">Closing Balance</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {transactionHistory.map((trans) => (
                  <TableRow key={trans.id}>
                    <TableCell className="font-medium">{formatMonth(trans.year_month)}</TableCell>
                    <TableCell className={`text-right ${trans.opening_balance > 0 ? 'text-red-600' : trans.opening_balance < 0 ? 'text-green-600' : ''}`}>
                      {formatCurrency(trans.opening_balance)}
                    </TableCell>
                    <TableCell className="text-right text-blue-600">
                      {trans.draw_taken ? formatCurrency(trans.draw_amount) : '-'}
                    </TableCell>
                    <TableCell className="text-right text-green-600">
                      {formatCurrency(trans.gross_commissions)}
                    </TableCell>
                    <TableCell className={`text-right font-semibold ${trans.closing_balance > 0 ? 'text-red-600' : trans.closing_balance < 0 ? 'text-green-600' : ''}`}>
                      {formatCurrency(trans.closing_balance)}
                    </TableCell>
                    <TableCell>
                      {trans.is_locked ? (
                        <Badge variant="secondary">
                          <Lock className="h-3 w-3 mr-1" />
                          Locked
                        </Badge>
                      ) : (
                        <Badge variant="outline">Open</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default MyCommissions
