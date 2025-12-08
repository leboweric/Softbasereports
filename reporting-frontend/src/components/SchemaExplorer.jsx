import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { apiUrl } from '@/lib/api'

const SchemaExplorer = () => {
  const [invoiceNo, setInvoiceNo] = useState('110000014')
  const [htmlContent, setHtmlContent] = useState('')
  const [loading, setLoading] = useState(false)

  const loadInvoice = async () => {
    setLoading(true)
    try {
      const response = await fetch(apiUrl(`/api/investigate-invoice?invoice_no=${invoiceNo}`))
      const html = await response.text()
      setHtmlContent(html)
    } catch (error) {
      console.error('Failed to load invoice:', error)
      setHtmlContent('<h1>Error loading invoice</h1>')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6">
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Schema Explorer - Invoice Investigation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-2">Invoice Number</label>
              <Input
                type="text"
                value={invoiceNo}
                onChange={(e) => setInvoiceNo(e.target.value)}
                placeholder="Enter invoice number"
              />
            </div>
            <Button onClick={loadInvoice} disabled={loading}>
              {loading ? 'Loading...' : 'Investigate Invoice'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {htmlContent && (
        <div
          className="border rounded-lg p-4 bg-white"
          dangerouslySetInnerHTML={{ __html: htmlContent }}
        />
      )}
    </div>
  )
}

export default SchemaExplorer
