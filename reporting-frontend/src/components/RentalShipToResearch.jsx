import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { apiUrl } from '@/lib/api'

const RentalShipToResearch = () => {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [comprehensiveResults, setComprehensiveResults] = useState(null)
  const [solutionResults, setSolutionResults] = useState(null)

  const runResearch = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl('/api/reports/departments/rental/shipto-simple'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setResults(data)
        console.log('Research Results:', data)
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const runComprehensiveResearch = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl('/api/reports/departments/rental/comprehensive-research'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setComprehensiveResults(data)
        console.log('Comprehensive Research Results:', data)
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const runSolution = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      const response = await fetch(apiUrl('/api/reports/departments/rental/customer-solution'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setSolutionResults(data)
        console.log('Solution Results:', data)
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Rental Ship To Research</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2 mb-4">
          <Button onClick={runResearch} disabled={loading}>
            {loading ? 'Running...' : 'Run Basic Research'}
          </Button>
          <Button onClick={runComprehensiveResearch} disabled={loading} variant="outline">
            {loading ? 'Running...' : 'Run Comprehensive Research'}
          </Button>
          <Button onClick={runSolution} disabled={loading} variant="default" className="bg-green-600 hover:bg-green-700">
            {loading ? 'Running...' : '🎯 Run Solution (WO Linkage)'}
          </Button>
        </div>
        
        {results && (
          <div className="mt-4 space-y-4">
            <div>
              <h3 className="font-semibold">Basic Research Results:</h3>
              <pre className="text-xs overflow-auto bg-gray-50 p-2 rounded">
                {JSON.stringify(results, null, 2)}
              </pre>
            </div>
          </div>
        )}
        
        {comprehensiveResults && (
          <div className="mt-4 space-y-4">
            <div>
              <h3 className="font-semibold">Comprehensive Research Results:</h3>
              <pre className="text-xs overflow-auto bg-gray-50 p-2 rounded max-h-96">
                {JSON.stringify(comprehensiveResults, null, 2)}
              </pre>
            </div>
          </div>
        )}
        
        {solutionResults && (
          <div className="mt-4 space-y-4 border-2 border-green-500 p-4 rounded-lg bg-green-50">
            <div>
              <h3 className="font-semibold text-green-700">✅ SOLUTION - Rental Customers via WO Linkage:</h3>
              <pre className="text-xs overflow-auto bg-white p-2 rounded max-h-96 border">
                {JSON.stringify(solutionResults, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default RentalShipToResearch