import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { apiUrl } from '@/lib/api'

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

  console.log('Rendering WorkOrderTypes, types:', types)
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>All Work Order Types in Database</CardTitle>
      </CardHeader>
      <CardContent>
        {types ? (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground mb-4">
              Total unique types: {types.total_types}
            </p>
            <div className="space-y-2">
              <p className="text-blue-600 font-bold border-2 border-blue-500 p-2">
                DEBUG: About to render {types.work_order_types?.length || 0} work order types
              </p>
              {types.work_order_types && types.work_order_types.length > 0 ? (
                types.work_order_types.map((type) => (
                  <div key={type.type} className="flex justify-between items-center p-2 bg-gray-50 rounded border-2 border-green-500">
                    <div>
                      <span className="font-medium">{type.type}</span>
                      <span className="ml-2 text-muted-foreground">- {type.description}</span>
                    </div>
                    <span className="text-sm">{type.count} work orders</span>
                  </div>
                ))
              ) : (
                <p className="text-red-500 border-2 border-red-500 p-2">No work order types found in data</p>
              )}
            </div>
          </div>
        ) : (
          <p className="text-red-500">No data loaded</p>
        )}
      </CardContent>
    </Card>
  )
}

export default WorkOrderTypes