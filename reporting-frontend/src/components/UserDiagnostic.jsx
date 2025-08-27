import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { apiUrl } from '@/lib/api'

const UserDiagnostic = () => {
  const [diagnostic, setDiagnostic] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const runDiagnostic = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/diagnostic/users'), {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        setDiagnostic(data)
      } else {
        setError(`Error: ${response.status}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>User Database Diagnostic</CardTitle>
      </CardHeader>
      <CardContent>
        <Button onClick={runDiagnostic} disabled={loading}>
          {loading ? 'Running...' : 'Run Diagnostic'}
        </Button>
        
        {error && (
          <div className="mt-4 text-red-600">Error: {error}</div>
        )}
        
        {diagnostic && (
          <div className="mt-4 space-y-2">
            <div><strong>Total Users:</strong> {diagnostic.total_users}</div>
            <div><strong>Organizations:</strong> {diagnostic.organizations?.length || 0}</div>
            <div><strong>User Roles Count:</strong> {diagnostic.user_roles_count}</div>
            
            <div className="mt-4">
              <strong>Specific Users:</strong>
              <ul className="ml-4 mt-2">
                {Object.entries(diagnostic.specific_users || {}).map(([key, value]) => (
                  <li key={key}>{key}: {value}</li>
                ))}
              </ul>
            </div>
            
            <div className="mt-4">
              <strong>All Users:</strong>
              <pre className="bg-gray-100 p-2 rounded text-xs overflow-auto max-h-96">
                {JSON.stringify(diagnostic.users, null, 2)}
              </pre>
            </div>
            
            <div className="mt-4">
              <strong>Organizations:</strong>
              <pre className="bg-gray-100 p-2 rounded text-xs">
                {JSON.stringify(diagnostic.organizations, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default UserDiagnostic