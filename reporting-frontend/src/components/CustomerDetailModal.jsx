import React, { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { DollarSign, FileText, Calendar, TrendingUp, AlertTriangle } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const CustomerDetailModal = ({ customer, isOpen, onClose }) => {
  const [customerDetails, setCustomerDetails] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (isOpen && customer) {
      fetchCustomerDetails(customer.customer_id)
    }
  }, [isOpen, customer])

  const fetchCustomerDetails = async (customerId) => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/customers/${customerId}/details`), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch customer details')
      }

      const data = await response.json()
      setCustomerDetails(data)
    } catch (error) {
      console.error('Failed to fetch customer details:', error)
      setError(error.message)
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

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  if (!customer) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div>
              <DialogTitle className="text-2xl">{customer.name}</DialogTitle>
              <DialogDescription>
                Customer ID: {customer.customer_id}
                {customerDetails && (
                  <span className="ml-4">
                    Customer since {formatDate(customerDetails.first_purchase_date)}
                  </span>
                )}
              </DialogDescription>
            </div>
            {customer.risk_level && customer.risk_level !== 'none' && (
              <Badge 
                variant={customer.risk_level === 'high' ? 'destructive' : 'warning'}
                className="ml-2"
              >
                <AlertTriangle className="h-3 w-3 mr-1" />
                {customer.risk_level.toUpperCase()} RISK
              </Badge>
            )}
          </div>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertTriangle className="h-12 w-12 text-red-500 mb-3" />
            <p className="text-sm font-medium text-gray-900 mb-1">Failed to load customer details</p>
            <p className="text-xs text-gray-500">{error}</p>
          </div>
        ) : customerDetails ? (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <DollarSign className="h-4 w-4 mr-1 text-green-600" />
                    Total Sales
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {formatCurrency(customerDetails.total_sales)}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Fiscal YTD
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <FileText className="h-4 w-4 mr-1 text-blue-600" />
                    Invoices
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {customerDetails.total_invoices}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatCurrency(customerDetails.avg_invoice_value)} avg
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <Calendar className="h-4 w-4 mr-1 text-purple-600" />
                    Last Purchase
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {customerDetails.days_since_last_invoice}d
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatDate(customerDetails.last_purchase_date)}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <TrendingUp className="h-4 w-4 mr-1 text-orange-600" />
                    Customer Age
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {Math.floor((new Date(customerDetails.last_purchase_date) - new Date(customerDetails.first_purchase_date)) / (1000 * 60 * 60 * 24 * 30))}m
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Months active
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Risk Factors */}
            {customer.risk_factors && customer.risk_factors.length > 0 && (
              <Card className="border-orange-200 bg-orange-50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center text-orange-800">
                    <AlertTriangle className="h-4 w-4 mr-2" />
                    Risk Factors
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {customer.risk_factors.map((factor, index) => (
                      <li key={index} className="text-sm text-orange-900 flex items-start">
                        <span className="mr-2">•</span>
                        <span>{factor}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Purchase History Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Purchase History (Last 12 Months)</CardTitle>
              </CardHeader>
              <CardContent>
                {customerDetails.monthly_purchases && customerDetails.monthly_purchases.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={customerDetails.monthly_purchases}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="month" 
                        tick={{ fontSize: 12 }}
                      />
                      <YAxis 
                        tick={{ fontSize: 12 }}
                        tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                      />
                      <Tooltip 
                        formatter={(value) => formatCurrency(value)}
                        labelStyle={{ color: '#000' }}
                      />
                      <Bar dataKey="sales" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-[300px] text-gray-500">
                    No purchase history available
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Invoices Table */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Invoices</CardTitle>
              </CardHeader>
              <CardContent>
                {customerDetails.recent_invoices && customerDetails.recent_invoices.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Invoice #</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {customerDetails.recent_invoices.map((invoice) => (
                        <TableRow key={invoice.invoice_no}>
                          <TableCell className="font-medium">{invoice.invoice_no}</TableCell>
                          <TableCell>{formatDate(invoice.invoice_date)}</TableCell>
                          <TableCell className="text-right font-medium">
                            {formatCurrency(invoice.grand_total)}
                          </TableCell>
                          <TableCell>
                            <Badge variant={
                              invoice.status === 'Recent' ? 'default' :
                              invoice.status === 'Normal' ? 'secondary' :
                              'outline'
                            }>
                              {invoice.status}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="flex items-center justify-center py-8 text-gray-500">
                    No recent invoices
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}

export default CustomerDetailModal
