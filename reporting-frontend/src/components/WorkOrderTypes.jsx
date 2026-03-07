import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { apiUrl } from '@/lib/api'
import { CfoMethodologyCard } from '@/components/ui/cfo-methodology-card'

const WorkOrderTypes = () => {
  const [types, setTypes] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTypes()
  }, [])

  const fetchTypes = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/reports/departments/work-order-types'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        console.log('WorkOrderTypes data:', data)
        setTypes(data)
      }
    } catch (error) {
      console.error('Error fetching work order types:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <div>
      <CfoMethodologyCard
        title="All Work Orders"
        items={[
          {
            label: 'Open Work Orders',
            formula: 'WO.ClosedDate IS NULL',
            detail: 'All work orders where the closed date has not been set in Softbase. Grouped by WO type code.'
          },
          {
            label: 'WO Type Codes',
            formula: 'WO.Type (S=Shop, F=Field, PM, W=Warranty)',
            detail: 'Work order types are defined in Softbase. Each type represents a category of service work performed.'
          },
          {
            label: 'Invoice Delay Analysis',
            formula: 'DATEDIFF(day, WO.CloseDate, InvoiceReg.InvoiceDate)',
            detail: 'Measures the lag between when a WO is closed and when the invoice is posted. Long delays indicate billing bottlenecks that impact cash flow.'
          },
          {
            label: 'Data Source',
            formula: 'WO table joined to InvoiceReg on WONo',
            detail: 'Work order counts from the WO table. Invoice delay analysis joins WO to InvoiceReg. Deleted records (DeletionTime IS NOT NULL) are excluded.'
          },
        ]}
      />
      <Card>
        <CardHeader>
          <CardTitle>Open Work Orders by Type</CardTitle>
        </CardHeader>
        <CardContent>
          {types && (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground mb-4">
                {types.total_open} open work orders ({types.total_all} total in database)
              </p>
              <div className="space-y-2">
                {types.work_order_types.map((type) => (
                  <div key={type.type} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <div>
                      <span className="font-medium">{type.type}</span>
                      <span className="ml-2 text-muted-foreground">- {type.description}</span>
                    </div>
                    <div className="text-sm">
                      <span className="font-semibold">{type.count} open</span>
                      <span className="text-muted-foreground ml-1">({type.total_count} total)</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default WorkOrderTypes
