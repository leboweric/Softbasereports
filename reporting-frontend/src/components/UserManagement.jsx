import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import UserDiagnostic from './UserDiagnostic'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { apiUrl } from '@/lib/api'
import { 
  Users, 
  Shield, 
  Building, 
  UserCheck,
  UserX,
  Plus,
  Trash2,
  Edit,
  Save,
  X
} from 'lucide-react'

const UserManagement = ({ user, organization }) => {
  const [users, setUsers] = useState([])
  const [roles, setRoles] = useState([])
  const [departments, setDepartments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingUser, setEditingUser] = useState(null)
  const [selectedRole, setSelectedRole] = useState({})

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      
      // Fetch users
      const usersRes = await fetch(apiUrl('/api/users'), {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (usersRes.ok) {
        const usersData = await usersRes.json()
        setUsers(usersData.users || [])
      } else {
        console.error('Failed to fetch users:', usersRes.status)
        setUsers([])
      }

      // Fetch roles
      const rolesRes = await fetch(apiUrl('/api/roles'), {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (rolesRes.ok) {
        const rolesData = await rolesRes.json()
        setRoles(rolesData.roles || [])
      } else {
        console.error('Failed to fetch roles:', rolesRes.status)
        setRoles([])
      }

      // Fetch departments
      const deptsRes = await fetch(apiUrl('/api/departments'), {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (deptsRes.ok) {
        const deptsData = await deptsRes.json()
        setDepartments(deptsData.departments || [])
      } else {
        console.error('Failed to fetch departments:', deptsRes.status)
        setDepartments([])
      }
    } catch (err) {
      setError('Failed to load user data')
      console.error(err)
      // Set default empty arrays to prevent crashes
      setUsers([])
      setRoles([])
      setDepartments([])
    } finally {
      setLoading(false)
    }
  }

  const assignRole = async (userId, roleName) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/users/${userId}/roles`), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ role_name: roleName })
      })

      if (response.ok) {
        fetchData() // Refresh data
      } else {
        const data = await response.json()
        setError(data.message)
      }
    } catch (err) {
      setError('Failed to assign role')
    }
  }

  const removeRole = async (userId, roleName) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/users/${userId}/roles/${roleName}`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        fetchData() // Refresh data
      } else {
        const data = await response.json()
        setError(data.message)
      }
    } catch (err) {
      setError('Failed to remove role')
    }
  }

  const toggleUserStatus = async (userId, isActive) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/users/${userId}`), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_active: !isActive })
      })

      if (response.ok) {
        fetchData() // Refresh data
      } else {
        const data = await response.json()
        setError(data.message)
      }
    } catch (err) {
      setError('Failed to update user status')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Temporary Diagnostic */}
      <UserDiagnostic />
      
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
          <p className="text-sm text-gray-500">Manage users, roles, and permissions</p>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{users.length}</div>
            <p className="text-xs text-muted-foreground">
              {users.filter(u => u.is_active).length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Roles</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{roles.length}</div>
            <p className="text-xs text-muted-foreground">Available roles</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Departments</CardTitle>
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{departments.length}</div>
            <p className="text-xs text-muted-foreground">Active departments</p>
          </CardContent>
        </Card>
      </div>

      {/* Users List */}
      <Card>
        <CardHeader>
          <CardTitle>Users</CardTitle>
          <CardDescription>Manage user accounts and role assignments</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {users && users.length > 0 ? users.map((u) => (
              <div key={u.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{u.first_name} {u.last_name}</h3>
                      {!u.is_active && (
                        <Badge variant="destructive" className="text-xs">Inactive</Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-500">{u.email}</p>
                    <p className="text-sm text-gray-500">Username: {u.username}</p>
                    
                    {/* Roles */}
                    <div className="mt-2 flex flex-wrap gap-2">
                      {u.roles && u.roles.length > 0 ? (
                        u.roles.map(role => (
                          <Badge key={role.id} variant="secondary" className="text-xs">
                            {role.name}
                            <button
                              onClick={() => removeRole(u.id, role.name)}
                              className="ml-1 hover:text-red-500"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </Badge>
                        ))
                      ) : (
                        <span className="text-sm text-gray-400">No roles assigned</span>
                      )}
                    </div>

                    {/* Add Role */}
                    {editingUser === u.id && (
                      <div className="mt-3 flex gap-2">
                        <Select
                          value={selectedRole[u.id] || ''}
                          onValueChange={(value) => setSelectedRole({...selectedRole, [u.id]: value})}
                        >
                          <SelectTrigger className="w-48">
                            <SelectValue placeholder="Select a role" />
                          </SelectTrigger>
                          <SelectContent>
                            {roles.filter(r => !u.roles?.some(ur => ur.id === r.id)).map(role => (
                              <SelectItem key={role.id} value={role.name}>
                                {role.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <Button
                          size="sm"
                          onClick={() => {
                            if (selectedRole[u.id]) {
                              assignRole(u.id, selectedRole[u.id])
                              setEditingUser(null)
                              setSelectedRole({...selectedRole, [u.id]: ''})
                            }
                          }}
                          disabled={!selectedRole[u.id]}
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setEditingUser(null)
                            setSelectedRole({...selectedRole, [u.id]: ''})
                          }}
                        >
                          Cancel
                        </Button>
                      </div>
                    )}
                  </div>

                  <div className="flex gap-2">
                    {editingUser !== u.id && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setEditingUser(u.id)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant={u.is_active ? 'destructive' : 'default'}
                      onClick={() => toggleUserStatus(u.id, u.is_active)}
                    >
                      {u.is_active ? <UserX className="h-4 w-4" /> : <UserCheck className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
              </div>
            )) : (
              <p className="text-center text-gray-500 py-4">No users found</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Roles Reference */}
      <Card>
        <CardHeader>
          <CardTitle>Available Roles</CardTitle>
          <CardDescription>Reference of all roles and their permissions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {roles && roles.length > 0 ? roles.map(role => (
              <div key={role.id} className="border rounded-lg p-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold">{role.name}</h4>
                    <p className="text-sm text-gray-500">{role.description}</p>
                    {role.department && (
                      <Badge variant="outline" className="mt-1 text-xs">
                        {role.department} Department
                      </Badge>
                    )}
                  </div>
                  <Badge variant={role.level >= 5 ? 'destructive' : 'secondary'} className="text-xs">
                    Level {role.level}
                  </Badge>
                </div>
              </div>
            )) : (
              <p className="text-center text-gray-500 py-4">No roles configured</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default UserManagement