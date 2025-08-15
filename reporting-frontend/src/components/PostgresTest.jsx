import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { apiUrl } from '@/lib/api'

const PostgresTest = () => {
  const [diagnosticResult, setDiagnosticResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const runDiagnostic = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/postgres/diagnostic'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      const data = await response.json()
      setDiagnosticResult(data)
    } catch (error) {
      setDiagnosticResult({ error: error.message })
    } finally {
      setLoading(false)
    }
  }

  const forceCreateTables = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/postgres/force-create-tables'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      const data = await response.json()
      alert(data.message || data.error || 'Operation completed')
      runDiagnostic() // Re-run diagnostic after creating tables
    } catch (error) {
      alert(`Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>PostgreSQL Connection Test</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex gap-2">
            <Button onClick={runDiagnostic} disabled={loading}>
              {loading ? 'Testing...' : 'Test Connection'}
            </Button>
            <Button onClick={forceCreateTables} disabled={loading} variant="destructive">
              Force Create Tables
            </Button>
          </div>
          
          {diagnosticResult && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <pre className="text-xs overflow-auto">
                {JSON.stringify(diagnosticResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default PostgresTest