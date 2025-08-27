import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
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
  X,
  UserPlus,
  Key
} from 'lucide-react'

const UserManagementEnhanced = ({ user, organization }) => {
  const [users, setUsers] = useState([])
  const [roles, setRoles] = useState([])
  const [departments, setDepartments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingUser, setEditingUser] = useState(null)
  const [selectedRole, setSelectedRole] = useState({})
  
  // State for Add User dialog
  const [showAddUser, setShowAddUser] = useState(false)
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: ''
  })
  
  // State for Edit User dialog
  const [showEditUser, setShowEditUser] = useState(false)
  const [editUser, setEditUser] = useState(null)

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
      const usersData = await usersRes.json()
      
      // Handle both array response and object with users property
      if (Array.isArray(usersData)) {
        setUsers(usersData)
      } else {
        setUsers(usersData.users || [])
      }

      // Fetch roles
      const rolesRes = await fetch(apiUrl('/api/roles'), {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (rolesRes.ok) {
        const rolesData = await rolesRes.json()
        setRoles(rolesData.roles || [])
      } else {
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
        setDepartments([])
      }
    } catch (err) {
      setError('Failed to load user data')
      console.error(err)
      setUsers([])
      setRoles([])
      setDepartments([])
    } finally {
      setLoading(false)
    }
  }

  const createUser = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/users/create'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newUser)
      })

      if (response.ok) {
        setShowAddUser(false)
        setNewUser({
          username: '',
          email: '',
          password: '',
          first_name: '',
          last_name: '',
          role: ''
        })
        fetchData() // Refresh data
      } else {
        const data = await response.json()
        setError(data.message || 'Failed to create user')
      }
    } catch (err) {
      setError('Failed to create user')
    }
  }

  const updateUserDetails = async () => {
    try {
      const token = localStorage.getItem('token')
      const updateData = {
        first_name: editUser.first_name,
        last_name: editUser.last_name,
        email: editUser.email,
        username: editUser.username
      }
      // Use POST endpoint to avoid CORS issues with PUT
      const updateUrl = apiUrl(`/api/users/${editUser.id}/update-info`)
      console.log('Updating user:', editUser.id, 'with data:', updateData)
      console.log('POST URL:', updateUrl)
      
      const response = await fetch(updateUrl, {
        method: 'POST',  // Using POST instead of PUT
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      })

      console.log('Update response status:', response.status)
      const data = await response.json()
      console.log('Update response data:', data)

      if (response.ok) {
        // Check if we got the updated user data
        if (data.user && data.user.first_name === editUser.first_name) {
          console.log('Update successful - data matches')
        } else {
          console.warn('Update may have failed - data does not match sent values')
          console.log('Sent:', updateData.first_name, 'Got back:', data.user?.first_name || data.first_name)
        }
        
        setShowEditUser(false)
        setEditUser(null)
        fetchData() // Refresh data - this should get the updated values
      } else {
        console.error('Update failed:', data)
        setError(data.message || 'Failed to update user')
      }
    } catch (err) {
      console.error('Update error:', err)
      setError('Failed to update user: ' + err.message)
    }
  }

  const resetPassword = async (userId) => {
    const newPassword = prompt('Enter new password for user:')
    if (!newPassword) return
    
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/users/${userId}/reset-password`), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ password: newPassword })
      })

      if (response.ok) {
        alert('Password reset successfully')
      } else {
        const data = await response.json()
        setError(data.message || 'Failed to reset password')
      }
    } catch (err) {
      setError('Failed to reset password')
    }
  }

  const deleteUser = async (userId) => {
    if (!confirm('Are you sure you want to delete this user?')) return
    
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/users/${userId}`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        fetchData() // Refresh data
      } else {
        const data = await response.json()
        setError(data.message || 'Failed to delete user')
      }
    } catch (err) {
      setError('Failed to delete user')
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
          <p className="text-sm text-gray-500">Manage users, roles, and permissions</p>
        </div>
        <Button onClick={() => setShowAddUser(true)}>
          <UserPlus className="mr-2 h-4 w-4" />
          Add User
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Add User Dialog */}
      <Dialog open={showAddUser} onOpenChange={setShowAddUser}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New User</DialogTitle>
            <DialogDescription>Create a new user account</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="username" className="text-right">Username</Label>
              <Input
                id="username"
                value={newUser.username}
                onChange={(e) => setNewUser({...newUser, username: e.target.value})}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="email" className="text-right">Email</Label>
              <Input
                id="email"
                type="email"
                value={newUser.email}
                onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="password" className="text-right">Password</Label>
              <Input
                id="password"
                type="password"
                value={newUser.password}
                onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="first_name" className="text-right">First Name</Label>
              <Input
                id="first_name"
                value={newUser.first_name}
                onChange={(e) => setNewUser({...newUser, first_name: e.target.value})}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="last_name" className="text-right">Last Name</Label>
              <Input
                id="last_name"
                value={newUser.last_name}
                onChange={(e) => setNewUser({...newUser, last_name: e.target.value})}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="role" className="text-right">Initial Role</Label>
              <Select
                value={newUser.role}
                onValueChange={(value) => setNewUser({...newUser, role: value})}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Select a role" />
                </SelectTrigger>
                <SelectContent>
                  {roles.map(role => (
                    <SelectItem key={role.id} value={role.name}>
                      {role.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddUser(false)}>Cancel</Button>
            <Button onClick={createUser}>Create User</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit User Dialog */}
      {editUser && (
        <Dialog open={showEditUser} onOpenChange={setShowEditUser}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit User</DialogTitle>
              <DialogDescription>Update user information</DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit_username" className="text-right">Username</Label>
                <Input
                  id="edit_username"
                  value={editUser.username}
                  onChange={(e) => setEditUser({...editUser, username: e.target.value})}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit_email" className="text-right">Email</Label>
                <Input
                  id="edit_email"
                  type="email"
                  value={editUser.email}
                  onChange={(e) => setEditUser({...editUser, email: e.target.value})}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit_first_name" className="text-right">First Name</Label>
                <Input
                  id="edit_first_name"
                  value={editUser.first_name || ''}
                  onChange={(e) => setEditUser({...editUser, first_name: e.target.value})}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit_last_name" className="text-right">Last Name</Label>
                <Input
                  id="edit_last_name"
                  value={editUser.last_name || ''}
                  onChange={(e) => setEditUser({...editUser, last_name: e.target.value})}
                  className="col-span-3"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => {
                setShowEditUser(false)
                setEditUser(null)
              }}>Cancel</Button>
              <Button onClick={updateUserDetails}>Save Changes</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
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
                          <Badge key={role.id || role.name} variant="secondary" className="text-xs">
                            {role.name || role}
                            <button
                              onClick={() => removeRole(u.id, role.name || role)}
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
                            {roles.filter(r => !u.roles?.some(ur => (ur.name || ur) === r.name)).map(role => (
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
                      <>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setEditingUser(u.id)}
                          title="Add Role"
                        >
                          <Shield className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setEditUser(u)
                            setShowEditUser(true)
                          }}
                          title="Edit User"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => resetPassword(u.id)}
                          title="Reset Password"
                        >
                          <Key className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                    <Button
                      size="sm"
                      variant={u.is_active ? 'destructive' : 'default'}
                      onClick={() => toggleUserStatus(u.id, u.is_active)}
                      title={u.is_active ? 'Deactivate' : 'Activate'}
                    >
                      {u.is_active ? <UserX className="h-4 w-4" /> : <UserCheck className="h-4 w-4" />}
                    </Button>
                    {u.username !== user?.username && (
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => deleteUser(u.id)}
                        title="Delete User"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
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

export default UserManagementEnhanced