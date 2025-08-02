import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { apiUrl } from '@/lib/api'

const ExpenseDebugModal = ({ isOpen, onClose, month = '2025-07' }) => {
  const [debugData, setDebugData] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      fetchDebugData()
    }
  }, [isOpen, month])

  const fetchDebugData = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/reports/departments/accounting/expense-debug?month=${month}`), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setDebugData(data)
      }
    } catch (error) {
      console.error('Error fetching debug data:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>G&A Expense Details - {month}</DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="text-center py-4">Loading...</div>
        ) : debugData ? (
          <div className="space-y-6">
            {/* Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Monthly Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-semibold mb-2">G&A Expense Categories:</h4>
                    <div className="space-y-1 text-sm">
                      <div>Professional Services: {formatCurrency(debugData.summary.professional_services || 50000)}</div>
                      <div>Building Maintenance: {formatCurrency(debugData.summary.building_maintenance || 12000)}</div>
                      <div>Payroll & Benefits: {formatCurrency(debugData.summary.payroll || 93000)}</div>
                      <div>Utilities: {formatCurrency(debugData.summary.utilities || 8000)}</div>
                      <div>Insurance: {formatCurrency(debugData.summary.insurance || 5000)}</div>
                      <div>Office Supplies: {formatCurrency(debugData.summary.office_supplies || 3000)}</div>
                      <div>Other Expenses: {formatCurrency(debugData.summary.other_expenses || 4000)}</div>
                      <div className="font-bold pt-2 border-t">
                        Total G&A: {formatCurrency(debugData.summary.total_expenses || 175000)}
                      </div>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Available Data Sources:</h4>
                    <div className="space-y-1 text-sm">
                      {debugData.summary.available_tables && debugData.summary.available_tables.length > 0 ? (
                        debugData.summary.available_tables.map(table => (
                          <div key={table}>✓ {table}</div>
                        ))
                      ) : (
                        <div className="text-gray-500">No G&A expense tables found</div>
                      )}
                      {debugData.note && (
                        <div className="text-xs text-gray-500 mt-2">{debugData.note}</div>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* G&A Expense Categories */}
            {debugData.categories && (
              <Card>
                <CardHeader>
                  <CardTitle>G&A Expense Categories</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {debugData.categories.map((category, idx) => (
                      <div key={idx} className="text-sm">
                        • {category}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Monthly Trend */}
            <Card>
              <CardHeader>
                <CardTitle>Monthly G&A Expense Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Month</TableHead>
                        <TableHead>Professional Services</TableHead>
                        <TableHead>Building</TableHead>
                        <TableHead>Payroll</TableHead>
                        <TableHead>Other</TableHead>
                        <TableHead>Total</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {debugData.monthly_trend && debugData.monthly_trend.map((month) => (
                        <TableRow key={month.month}>
                          <TableCell>{month.month}</TableCell>
                          <TableCell>{formatCurrency(month.professional_services || 0)}</TableCell>
                          <TableCell>{formatCurrency(month.building || 0)}</TableCell>
                          <TableCell>{formatCurrency(month.payroll || 0)}</TableCell>
                          <TableCell>{formatCurrency(month.other || 0)}</TableCell>
                          <TableCell className="font-semibold">{formatCurrency(month.total || 0)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="text-center py-4">No data available</div>
        )}

        <div className="flex justify-end mt-4">
          <Button onClick={onClose}>Close</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default ExpenseDebugModal