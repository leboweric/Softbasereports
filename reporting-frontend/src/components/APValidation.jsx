import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { apiUrl } from '@/lib/api'
import { AlertCircle, CheckCircle, XCircle } from 'lucide-react'

const APValidation = () => {
  const [validationData, setValidationData] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchValidation = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/accounting/ap-validation'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setValidationData(data)
      }
    } catch (error) {
      console.error('Error fetching AP validation:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner title="Validating AP Data..." />
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>AP Data Validation</CardTitle>
          <CardDescription>
            Click the button below to validate AP data accuracy
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={fetchValidation} disabled={loading}>
            Run Validation Check
          </Button>

          {validationData && (
            <div className="mt-6 space-y-4">
              {/* Summary */}
              <div className="grid gap-4 md:grid-cols-2">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Total AP (Raw Sum)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      ${(validationData.summary.total_ap_raw / 1000).toFixed(0)}k
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Direct sum of Amount field
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Total AP (Absolute)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      ${(validationData.summary.total_ap_absolute / 1000).toFixed(0)}k
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Sum of absolute values
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Invoice Count</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {validationData.summary.invoice_count}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Distinct unpaid invoices
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Vendor Count</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {validationData.summary.vendor_count}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Vendors with balances
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Entry Types */}
              {validationData.validation_results.by_entry_type && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">AP by Entry Type</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {validationData.validation_results.by_entry_type.map((entry, idx) => (
                        <div key={idx} className="flex justify-between text-sm">
                          <span>{entry.EntryType || 'NULL'}</span>
                          <span>
                            {entry.record_count} records = ${(entry.total_amount / 1000).toFixed(0)}k
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Sample Invoices */}
              {validationData.validation_results.sample_invoices && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Sample Large Invoices</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      {validationData.validation_results.sample_invoices.map((inv, idx) => (
                        <div key={idx} className="border-b pb-2">
                          <div className="flex justify-between">
                            <span className="font-medium">{inv.APInvoiceNo}</span>
                            <span className="font-bold">${inv.Amount.toLocaleString()}</span>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {inv.VendorName || inv.VendorNo} • {inv.EntryType}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Validation Status */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Data Quality Checks</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      {validationData.summary.total_ap_raw < 0 ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-yellow-600" />
                      )}
                      <span className="text-sm">
                        AP amounts are {validationData.summary.total_ap_raw < 0 ? 'negative' : 'positive'} 
                        (expected: negative)
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {validationData.summary.invoice_count > 0 ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-600" />
                      )}
                      <span className="text-sm">
                        Found {validationData.summary.invoice_count} unpaid invoices
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default APValidation