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
          <DialogTitle>Expense Calculation Debug - {month}</DialogTitle>
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
                    <h4 className="font-semibold mb-2">Cost Breakdown:</h4>
                    <div className="space-y-1 text-sm">
                      <div>Invoice Count: {debugData.summary.invoice_count}</div>
                      <div>Parts Cost: {formatCurrency(debugData.summary.parts_cost)}</div>
                      <div>Labor Cost: {formatCurrency(debugData.summary.labor_cost)}</div>
                      <div>Equipment Cost: {formatCurrency(debugData.summary.equipment_cost)}</div>
                      <div>Rental Cost: {formatCurrency(debugData.summary.rental_cost)}</div>
                      <div>Misc Cost: {formatCurrency(debugData.summary.misc_cost)}</div>
                      <div className="font-bold pt-2 border-t">
                        Total Cost: {formatCurrency(debugData.summary.total_cost)}
                      </div>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2">Revenue Comparison:</h4>
                    <div className="space-y-1 text-sm">
                      <div>Total Revenue: {formatCurrency(debugData.summary.total_revenue)}</div>
                      <div>Parts Revenue: {formatCurrency(debugData.summary.parts_revenue)}</div>
                      <div>Labor Revenue: {formatCurrency(debugData.summary.labor_revenue)}</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Sample Invoices */}
            <Card>
              <CardHeader>
                <CardTitle>Top 10 Invoices by Cost</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Invoice #</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>Customer</TableHead>
                        <TableHead>Dept</TableHead>
                        <TableHead>Parts</TableHead>
                        <TableHead>Labor</TableHead>
                        <TableHead>Equipment</TableHead>
                        <TableHead>Rental</TableHead>
                        <TableHead>Misc</TableHead>
                        <TableHead>Total Cost</TableHead>
                        <TableHead>Revenue</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {debugData.sample_invoices.map((inv) => (
                        <TableRow key={inv.invoice_no}>
                          <TableCell>{inv.invoice_no}</TableCell>
                          <TableCell>{inv.date}</TableCell>
                          <TableCell className="max-w-[150px] truncate">{inv.customer}</TableCell>
                          <TableCell>{inv.department}</TableCell>
                          <TableCell>{formatCurrency(inv.parts_cost)}</TableCell>
                          <TableCell>{formatCurrency(inv.labor_cost)}</TableCell>
                          <TableCell>{formatCurrency(inv.equipment_cost)}</TableCell>
                          <TableCell>{formatCurrency(inv.rental_cost)}</TableCell>
                          <TableCell>{formatCurrency(inv.misc_cost)}</TableCell>
                          <TableCell className="font-semibold">{formatCurrency(inv.total_cost)}</TableCell>
                          <TableCell>{formatCurrency(inv.revenue)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>

            {/* Monthly Trend */}
            <Card>
              <CardHeader>
                <CardTitle>Monthly Expense Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Month</TableHead>
                        <TableHead>Invoices</TableHead>
                        <TableHead>Parts</TableHead>
                        <TableHead>Labor</TableHead>
                        <TableHead>Equipment</TableHead>
                        <TableHead>Rental</TableHead>
                        <TableHead>Misc</TableHead>
                        <TableHead>Total</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {debugData.monthly_trend.map((month) => (
                        <TableRow key={month.month}>
                          <TableCell>{month.month}</TableCell>
                          <TableCell>{month.invoices}</TableCell>
                          <TableCell>{formatCurrency(month.parts)}</TableCell>
                          <TableCell>{formatCurrency(month.labor)}</TableCell>
                          <TableCell>{formatCurrency(month.equipment)}</TableCell>
                          <TableCell>{formatCurrency(month.rental)}</TableCell>
                          <TableCell>{formatCurrency(month.misc)}</TableCell>
                          <TableCell className="font-semibold">{formatCurrency(month.total)}</TableCell>
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