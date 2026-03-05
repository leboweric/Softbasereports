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
import { UserPlus, Edit, Trash2, CheckCircle, XCircle, KeyRound, Building2, Globe } from 'lucide-react';
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
  const [subsidiaryAccessUser, setSubsidiaryAccessUser] = useState(null);
  const [showSubsidiaryDialog, setShowSubsidiaryDialog] = useState(false);
  const [isAlohaOrg, setIsAlohaOrg] = useState(false);

  // Detect if this is an Aloha Holdings org
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        // Check org name from user context or just check if aloha roles exist
      } catch (e) {}
    }
  }, []);

  useEffect(() => {
    // Detect Aloha org by checking if any loaded roles are Aloha roles
    if (roles.length > 0) {
      const hasAlohaRoles = roles.some(r => r.name && r.name.startsWith('Aloha'));
      setIsAlohaOrg(hasAlohaRoles);
    }
  }, [roles]);
  
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
                {isAlohaOrg && <TableHead>Portfolio Access</TableHead>}
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
                  {isAlohaOrg && (
                    <TableCell>
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex items-center gap-1 text-xs"
                        onClick={() => {
                          setSubsidiaryAccessUser(u);
                          setShowSubsidiaryDialog(true);
                          setError('');
                        }}
                      >
                        <Building2 className="w-3 h-3" />
                        Manage
                      </Button>
                    </TableCell>
                  )}
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

      {showSubsidiaryDialog && subsidiaryAccessUser && isAlohaOrg && (
        <SubsidiaryAccessDialog
          targetUser={subsidiaryAccessUser}
          onClose={() => { setShowSubsidiaryDialog(false); setSubsidiaryAccessUser(null); }}
          onSuccess={(msg) => { setSuccess(msg); setTimeout(() => setSuccess(''), 3000); }}
          onError={(msg) => setError(msg)}
        />
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

function SubsidiaryAccessDialog({ targetUser, onClose, onSuccess, onError }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [allAccess, setAllAccess] = useState(false);
  const [selectedSubs, setSelectedSubs] = useState([]);
  const [allSubsidiaries, setAllSubsidiaries] = useState([]);

  useEffect(() => {
    loadAccess();
  }, [targetUser.id]);

  async function loadAccess() {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl(`/api/aloha/subsidiary-access/${targetUser.id}`), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAllSubsidiaries(data.all_subsidiaries || []);
        setAllAccess(data.has_all_access || false);
        if (data.has_all_access) {
          setSelectedSubs(data.all_subsidiaries.map(s => s.id));
        } else {
          setSelectedSubs(data.assigned_subsidiaries || []);
        }
      } else {
        onError('Failed to load subsidiary access');
      }
    } catch (err) {
      onError('Error loading subsidiary access');
    }
    setLoading(false);
  }

  async function handleSave() {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const body = allAccess
        ? { all_access: true }
        : { subsidiary_ids: selectedSubs };

      const response = await fetch(apiUrl(`/api/aloha/subsidiary-access/${targetUser.id}`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(body)
      });

      if (response.ok) {
        onSuccess(`Portfolio access updated for ${targetUser.first_name} ${targetUser.last_name}`);
        onClose();
      } else {
        const data = await response.json();
        onError(data.error || 'Failed to update subsidiary access');
      }
    } catch (err) {
      onError('Error updating subsidiary access');
    }
    setSaving(false);
  }

  function toggleSubsidiary(subId) {
    setSelectedSubs(prev =>
      prev.includes(subId) ? prev.filter(id => id !== subId) : [...prev, subId]
    );
    // If manually toggling, turn off "all access"
    setAllAccess(false);
  }

  function handleAllAccessToggle(checked) {
    setAllAccess(checked);
    if (checked) {
      setSelectedSubs(allSubsidiaries.map(s => s.id));
    } else {
      setSelectedSubs([]);
    }
  }

  const sapSubs = allSubsidiaries.filter(s => s.erp_type === 'SAP');
  const nsSubs = allSubsidiaries.filter(s => s.erp_type === 'NetSuite');

  function selectGroup(group) {
    const ids = group.map(s => s.id);
    const allSelected = ids.every(id => selectedSubs.includes(id));
    if (allSelected) {
      setSelectedSubs(prev => prev.filter(id => !ids.includes(id)));
    } else {
      setSelectedSubs(prev => [...new Set([...prev, ...ids])]);
    }
    setAllAccess(false);
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Building2 className="w-5 h-5" />
            Portfolio Access
          </DialogTitle>
        </DialogHeader>

        <p className="text-sm text-gray-600">
          Manage which subsidiary companies <strong>{targetUser.first_name} {targetUser.last_name}</strong> ({targetUser.email}) can access.
        </p>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <span className="text-gray-500">Loading...</span>
          </div>
        ) : (
          <div className="space-y-4">
            {/* All Access Toggle */}
            <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg border">
              <Checkbox
                id="all-access"
                checked={allAccess}
                onCheckedChange={handleAllAccessToggle}
              />
              <div className="flex-1">
                <label htmlFor="all-access" className="text-sm font-medium cursor-pointer flex items-center gap-2">
                  <Globe className="w-4 h-4 text-teal-600" />
                  Full Portfolio Access
                </label>
                <p className="text-xs text-gray-500">Access to all current and future subsidiaries</p>
              </div>
            </div>

            {/* SAP Companies */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold text-blue-700">SAP Companies ({sapSubs.length})</h4>
                <Button variant="ghost" size="sm" className="text-xs h-6 px-2" onClick={() => selectGroup(sapSubs)} disabled={allAccess}>
                  {sapSubs.every(s => selectedSubs.includes(s.id)) ? 'Deselect All SAP' : 'Select All SAP'}
                </Button>
              </div>
              <div className="space-y-1 border rounded-lg p-3">
                {sapSubs.map(sub => (
                  <div key={sub.id} className="flex items-center space-x-3">
                    <Checkbox
                      id={`sub-${sub.id}`}
                      checked={selectedSubs.includes(sub.id)}
                      onCheckedChange={() => toggleSubsidiary(sub.id)}
                      disabled={allAccess}
                    />
                    <label htmlFor={`sub-${sub.id}`} className="text-sm cursor-pointer flex-1">
                      {sub.name}
                    </label>
                    <Badge variant="secondary" className="text-xs">SAP</Badge>
                  </div>
                ))}
              </div>
            </div>

            {/* NetSuite Companies */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold text-orange-700">NetSuite Companies ({nsSubs.length})</h4>
                <Button variant="ghost" size="sm" className="text-xs h-6 px-2" onClick={() => selectGroup(nsSubs)} disabled={allAccess}>
                  {nsSubs.every(s => selectedSubs.includes(s.id)) ? 'Deselect All NetSuite' : 'Select All NetSuite'}
                </Button>
              </div>
              <div className="space-y-1 border rounded-lg p-3">
                {nsSubs.map(sub => (
                  <div key={sub.id} className="flex items-center space-x-3">
                    <Checkbox
                      id={`sub-${sub.id}`}
                      checked={selectedSubs.includes(sub.id)}
                      onCheckedChange={() => toggleSubsidiary(sub.id)}
                      disabled={allAccess}
                    />
                    <label htmlFor={`sub-${sub.id}`} className="text-sm cursor-pointer flex-1">
                      {sub.name}
                    </label>
                    <Badge variant="secondary" className="text-xs bg-orange-50 text-orange-700">NetSuite</Badge>
                  </div>
                ))}
              </div>
            </div>

            {/* Summary */}
            <div className="text-xs text-gray-500 pt-1">
              {allAccess
                ? 'Full access to all 8 subsidiaries'
                : `${selectedSubs.length} of ${allSubsidiaries.length} subsidiaries selected`
              }
              {!allAccess && selectedSubs.length === 0 && (
                <span className="text-amber-600 ml-1">— User will not see any subsidiary data</span>
              )}
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <Button type="button" variant="outline" onClick={onClose} disabled={saving}>
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={saving}>
                {saving ? 'Saving...' : 'Save Access'}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
