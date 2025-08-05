import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { apiUrl } from '@/lib/api'

const PartsWODiagnostic = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/parts/work-order-status'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        setData(result)
      }
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Parts Work Order Status Diagnostic</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {data?.summary && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Total Work Orders</p>
              <p className="text-lg font-semibold">{data.summary.total_count}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Parts Work Orders</p>
              <p className="text-lg font-semibold">{data.summary.parts_count}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Parts Completed</p>
              <p className="text-lg font-semibold">{data.summary.parts_completed}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Parts Closed</p>
              <p className="text-lg font-semibold">{data.summary.parts_closed}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Parts Invoiced</p>
              <p className="text-lg font-semibold">{data.summary.parts_invoiced}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Parts Awaiting Invoice</p>
              <p className="text-lg font-semibold text-orange-600">{data.summary.parts_awaiting_invoice}</p>
            </div>
          </div>
        )}
        
        {data?.sample_work_orders && data.sample_work_orders.length > 0 && (
          <div>
            <h3 className="font-semibold mb-2">Sample Parts Work Orders</h3>
            <div className="text-xs space-y-1">
              {data.sample_work_orders.map((wo) => (
                <div key={wo.WONo} className="border-b pb-1">
                  WO#{wo.WONo} - Status: {wo.Status} - 
                  Opened: {wo.OpenDate ? new Date(wo.OpenDate).toLocaleDateString() : 'N/A'} - 
                  Completed: {wo.CompletedDate ? new Date(wo.CompletedDate).toLocaleDateString() : 'Not yet'} - 
                  Closed: {wo.ClosedDate ? new Date(wo.ClosedDate).toLocaleDateString() : 'Not yet'}
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default PartsWODiagnostic