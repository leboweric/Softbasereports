import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Checkbox } from '../ui/checkbox';
import { Alert, AlertDescription } from '../ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Badge } from '../ui/badge';
import { UserPlus, Edit, Trash2, CheckCircle, XCircle, KeyRound } from 'lucide-react';
import { apiUrl } from '../../lib/api';

export function UserManagement({ user }) {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [resetPasswordUser, setResetPasswordUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [showResetDialog, setShowResetDialog] = useState(false);
  
  useEffect(() => {
    loadUsers();
    loadRoles();
  }, []);
  
  async function loadUsers() {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl('/api/admin/users'), {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      } else {
        setError('Failed to load users');
      }
    } catch (err) {
      setError('Error loading users');
    }
  }
  
  async function loadRoles() {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl('/api/admin/roles'), {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setRoles(data);
      } else {
        setError('Failed to load roles');
      }
    } catch (err) {
      setError('Error loading roles');
    }
  }
  
  async function handleSaveUser(userData) {
    setLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('token');
      const url = editingUser 
        ? apiUrl(`/api/admin/users/${editingUser.id}`)
        : apiUrl('/api/admin/users');
      
      const method = editingUser ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(userData)
      });
      
      if (response.ok) {
        setSuccess(editingUser ? 'User updated successfully' : 'User created successfully');
        setShowDialog(false);
        setEditingUser(null);
        loadUsers();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to save user');
      }
    } catch (err) {
      setError('Error saving user');
    }
    setLoading(false);
  }
  
  async function handleResetPassword() {
    if (!resetPasswordUser || !newPassword) return;
    setLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl(`/api/users/${resetPasswordUser.id}/reset-password`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ password: newPassword })
      });
      
      if (response.ok) {
        setSuccess(`Password reset successfully for ${resetPasswordUser.first_name} ${resetPasswordUser.last_name}`);
        setShowResetDialog(false);
        setResetPasswordUser(null);
        setNewPassword('');
        setTimeout(() => setSuccess(''), 5000);
      } else {
        const data = await response.json();
        setError(data.message || data.error || 'Failed to reset password');
      }
    } catch (err) {
      setError('Error resetting password');
    }
    setLoading(false);
  }

  async function handleDeleteUser(userId) {
    if (!confirm('Are you sure you want to deactivate this user?')) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl(`/api/admin/users/${userId}`), {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        setSuccess('User deactivated successfully');
        loadUsers();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError('Failed to deactivate user');
      }
    } catch (err) {
      setError('Error deactivating user');
    }
  }
  
  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">User Management</h1>
          <p className="text-gray-600 mt-1">Manage user accounts and role assignments</p>
        </div>
        <Button 
          onClick={() => { 
            setEditingUser(null); 
            setShowDialog(true); 
            setError('');
          }}
          className="flex items-center gap-2"
        >
          <UserPlus className="w-4 h-4" />
          Create User
        </Button>
      </div>
      
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      {success && (
        <Alert>
          <CheckCircle className="w-4 h-4" />
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}
      
      <Card>
        <CardHeader>
          <CardTitle>All Users ({users.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Roles</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map(u => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">
                    {u.first_name} {u.last_name}
                  </TableCell>
                  <TableCell>{u.email}</TableCell>
                  <TableCell>
                    <div className="flex gap-1 flex-wrap">
                      {u.roles.length > 0 ? (
                        u.roles.map(role => (
                          <Badge key={role.id} variant="secondary">
                            {role.name}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-gray-400 text-sm">No roles</span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {u.is_active ? (
                      <Badge variant="success" className="flex items-center gap-1 w-fit">
                        <CheckCircle className="w-3 h-3" />
                        Active
                      </Badge>
                    ) : (
                      <Badge variant="destructive" className="flex items-center gap-1 w-fit">
                        <XCircle className="w-3 h-3" />
                        Inactive
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex gap-2 justify-end">
                      <Button 
                        variant="outline" 
                        size="sm"
                        title="Reset Password"
                        onClick={() => { 
                          setResetPasswordUser(u);
                          setNewPassword('');
                          setShowResetDialog(true);
                          setError('');
                        }}
                      >
                        <KeyRound className="w-4 h-4" />
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => { 
                          setEditingUser(u); 
                          setShowDialog(true); 
                          setError('');
                        }}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button 
                        variant="destructive" 
                        size="sm"
                        onClick={() => handleDeleteUser(u.id)}
                        disabled={!u.is_active}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      
      {showResetDialog && resetPasswordUser && (
        <Dialog open onOpenChange={() => { setShowResetDialog(false); setResetPasswordUser(null); setNewPassword(''); }}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Reset Password</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Reset password for <strong>{resetPasswordUser.first_name} {resetPasswordUser.last_name}</strong> ({resetPasswordUser.email})
              </p>
              <div>
                <Label htmlFor="new_password">New Password *</Label>
                <Input
                  id="new_password"
                  type="text"
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  placeholder="Enter new password"
                  autoFocus
                />
              </div>
              <div className="flex justify-end space-x-2 pt-2">
                <Button type="button" variant="outline" onClick={() => { setShowResetDialog(false); setResetPasswordUser(null); setNewPassword(''); }} disabled={loading}>
                  Cancel
                </Button>
                <Button onClick={handleResetPassword} disabled={loading || !newPassword}>
                  {loading ? 'Resetting...' : 'Reset Password'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {showDialog && (
        <UserDialog
          user={editingUser}
          roles={roles}
          onSave={handleSaveUser}
          onClose={() => {
            setShowDialog(false);
            setEditingUser(null);
            setError('');
          }}
          loading={loading}
          error={error}
        />
      )}
    </div>
  );
}

function UserDialog({ user, roles, onSave, onClose, loading, error }) {
  const [formData, setFormData] = useState({
    email: user?.email || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    password: '',
    organization_id: user?.organization_id || 4,
    role_ids: user?.roles?.map(r => r.id) || [],
  });
  
  function handleSubmit(e) {
    e.preventDefault();
    
    // Validation
    if (!formData.email || !formData.first_name || !formData.last_name) {
      return;
    }
    
    if (!user && !formData.password) {
      return;
    }
    
    onSave(formData);
  }
  
  function toggleRole(roleId) {
    setFormData(prev => ({
      ...prev,
      role_ids: prev.role_ids.includes(roleId)
        ? prev.role_ids.filter(id => id !== roleId)
        : [...prev.role_ids, roleId]
    }));
  }
  
  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {user ? 'Edit User' : 'Create New User'}
          </DialogTitle>
        </DialogHeader>
        
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="first_name">First Name *</Label>
              <Input
                id="first_name"
                value={formData.first_name}
                onChange={e => setFormData({...formData, first_name: e.target.value})}
                required
                placeholder="John"
              />
            </div>
            <div>
              <Label htmlFor="last_name">Last Name *</Label>
              <Input
                id="last_name"
                value={formData.last_name}
                onChange={e => setFormData({...formData, last_name: e.target.value})}
                required
                placeholder="Doe"
              />
            </div>
          </div>
          
          <div>
            <Label htmlFor="email">Email *</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={e => setFormData({...formData, email: e.target.value})}
              required
              placeholder="john.doe@company.com"
              disabled={!!user}
            />
            {user && (
              <p className="text-sm text-gray-500 mt-1">Email cannot be changed</p>
            )}
          </div>
          
          {!user && (
            <div>
              <Label htmlFor="password">Password *</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={e => setFormData({...formData, password: e.target.value})}
                required
                placeholder="Minimum 8 characters"
              />
              <p className="text-sm text-gray-500 mt-1">
                User will need to change password on first login
              </p>
            </div>
          )}
          
          <div>
            <Label className="mb-3 block">Assign Roles *</Label>
            <div className="space-y-2 border rounded-lg p-4">
              {roles.map(role => (
                <div key={role.id} className="flex items-start space-x-3">
                  <Checkbox
                    id={`role-${role.id}`}
                    checked={formData.role_ids.includes(role.id)}
                    onCheckedChange={() => toggleRole(role.id)}
                  />
                  <div className="flex-1">
                    <label 
                      htmlFor={`role-${role.id}`}
                      className="text-sm font-medium cursor-pointer"
                    >
                      {role.name}
                    </label>
                    {role.description && (
                      <p className="text-xs text-gray-500">{role.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
            {formData.role_ids.length === 0 && (
              <p className="text-sm text-amber-600 mt-2">
                Warning: User will have no access without a role
              </p>
            )}
          </div>
          
          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Saving...' : (user ? 'Update User' : 'Create User')}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}