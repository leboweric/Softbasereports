import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Plus, Edit2, Trash2, DollarSign, Users, Calendar, Save, X, AlertCircle } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const RepCompAdmin = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [settings, setSettings] = useState([])
  const [error, setError] = useState(null)
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [editingSetting, setEditingSetting] = useState(null)
  const [saving, setSaving] = useState(false)

  // Form state
  const [formData, setFormData] = useState({
    salesman_name: '',
    salesman_code: '',
    monthly_draw: 0,
    start_date: new Date().toISOString().split('T')[0],
    starting_balance: 0,
    is_active: true,
    notes: ''
  })

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl('/api/sales-rep-comp/settings'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setSettings(data.settings || [])
      } else {
        throw new Error('Failed to fetch settings')
      }
    } catch (err) {
      console.error('Error fetching rep comp settings:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAddNew = () => {
    setFormData({
      salesman_name: '',
      salesman_code: '',
      monthly_draw: 0,
      start_date: new Date().toISOString().split('T')[0],
      starting_balance: 0,
      is_active: true,
      notes: ''
    })
    setShowAddDialog(true)
  }

  const handleEdit = (setting) => {
    setEditingSetting(setting)
    setFormData({
      salesman_name: setting.salesman_name,
      salesman_code: setting.salesman_code || '',
      monthly_draw: setting.monthly_draw,
      start_date: setting.start_date,
      starting_balance: setting.starting_balance,
      is_active: setting.is_active,
      notes: setting.notes || ''
    })
    setShowEditDialog(true)
  }

  const handleSave = async (isNew = false) => {
    try {
      setSaving(true)
      const token = localStorage.getItem('token')

      const url = isNew
        ? apiUrl('/api/sales-rep-comp/settings')
        : apiUrl(`/api/sales-rep-comp/settings/${editingSetting.id}`)

      const response = await fetch(url, {
        method: isNew ? 'POST' : 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        await fetchSettings()
        setShowAddDialog(false)
        setShowEditDialog(false)
        setEditingSetting(null)
      } else {
        const data = await response.json()
        throw new Error(data.error || 'Failed to save settings')
      }
    } catch (err) {
      console.error('Error saving settings:', err)
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (settingId) => {
    if (!confirm('Are you sure you want to delete this compensation plan?')) {
      return
    }

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(apiUrl(`/api/sales-rep-comp/settings/${settingId}`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        await fetchSettings()
      } else {
        throw new Error('Failed to delete settings')
      }
    } catch (err) {
      console.error('Error deleting settings:', err)
      setError(err.message)
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value || 0)
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="large" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Sales Rep Compensation Admin</h1>
          <p className="text-muted-foreground">
            Manage sales rep draw plans and commission tracking
          </p>
        </div>
        <Button onClick={handleAddNew}>
          <Plus className="h-4 w-4 mr-2" />
          Add Rep
        </Button>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-4 flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <span className="text-red-600">{error}</span>
            <Button variant="ghost" size="sm" onClick={() => setError(null)}>
              <X className="h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Users className="h-4 w-4 text-blue-600" />
              Active Reps
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {settings.filter(s => s.is_active).length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-green-600" />
              Total Monthly Draw
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(settings.filter(s => s.is_active).reduce((sum, s) => sum + (s.monthly_draw || 0), 0))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Calendar className="h-4 w-4 text-purple-600" />
              Total Starting Balance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(settings.filter(s => s.is_active).reduce((sum, s) => sum + (s.starting_balance || 0), 0))}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Positive = reps owe company
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Settings Table */}
      <Card>
        <CardHeader>
          <CardTitle>Compensation Plans</CardTitle>
          <CardDescription>
            Configure monthly draw and starting balances for each sales rep
          </CardDescription>
        </CardHeader>
        <CardContent>
          {settings.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No compensation plans configured yet.</p>
              <p className="text-sm">Click "Add Rep" to create your first plan.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Salesman Name</TableHead>
                  <TableHead>Code</TableHead>
                  <TableHead className="text-right">Monthly Draw</TableHead>
                  <TableHead>Start Date</TableHead>
                  <TableHead className="text-right">Starting Balance</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Notes</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {settings.map((setting) => (
                  <TableRow key={setting.id}>
                    <TableCell className="font-medium">{setting.salesman_name}</TableCell>
                    <TableCell>{setting.salesman_code || '-'}</TableCell>
                    <TableCell className="text-right">{formatCurrency(setting.monthly_draw)}</TableCell>
                    <TableCell>{formatDate(setting.start_date)}</TableCell>
                    <TableCell className={`text-right ${setting.starting_balance > 0 ? 'text-red-600' : setting.starting_balance < 0 ? 'text-green-600' : ''}`}>
                      {formatCurrency(setting.starting_balance)}
                    </TableCell>
                    <TableCell>
                      <Badge variant={setting.is_active ? 'default' : 'secondary'}>
                        {setting.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate">
                      {setting.notes || '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="ghost" size="sm" onClick={() => handleEdit(setting)}>
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(setting.id)}>
                          <Trash2 className="h-4 w-4 text-red-600" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Sales Rep</DialogTitle>
            <DialogDescription>
              Create a compensation plan for a new sales rep
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="salesman_name">Salesman Name *</Label>
                <Input
                  id="salesman_name"
                  value={formData.salesman_name}
                  onChange={(e) => setFormData({ ...formData, salesman_name: e.target.value })}
                  placeholder="e.g., Kevin Smith"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="salesman_code">Salesman Code</Label>
                <Input
                  id="salesman_code"
                  value={formData.salesman_code}
                  onChange={(e) => setFormData({ ...formData, salesman_code: e.target.value })}
                  placeholder="e.g., KSMITH"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="monthly_draw">Monthly Draw</Label>
                <Input
                  id="monthly_draw"
                  type="number"
                  step="0.01"
                  value={formData.monthly_draw}
                  onChange={(e) => setFormData({ ...formData, monthly_draw: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="start_date">Start Date</Label>
                <Input
                  id="start_date"
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="starting_balance">Starting Balance</Label>
              <Input
                id="starting_balance"
                type="number"
                step="0.01"
                value={formData.starting_balance}
                onChange={(e) => setFormData({ ...formData, starting_balance: parseFloat(e.target.value) || 0 })}
              />
              <p className="text-xs text-muted-foreground">
                Positive = rep owes company (overdraw), Negative = company owes rep
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="notes">Notes</Label>
              <Input
                id="notes"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Optional notes about this plan"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
              />
              <Label htmlFor="is_active">Active</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddDialog(false)}>
              Cancel
            </Button>
            <Button onClick={() => handleSave(true)} disabled={saving || !formData.salesman_name}>
              {saving ? <LoadingSpinner size="small" /> : <Save className="h-4 w-4 mr-2" />}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Compensation Plan</DialogTitle>
            <DialogDescription>
              Update compensation settings for {editingSetting?.salesman_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit_salesman_name">Salesman Name *</Label>
                <Input
                  id="edit_salesman_name"
                  value={formData.salesman_name}
                  onChange={(e) => setFormData({ ...formData, salesman_name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit_salesman_code">Salesman Code</Label>
                <Input
                  id="edit_salesman_code"
                  value={formData.salesman_code}
                  onChange={(e) => setFormData({ ...formData, salesman_code: e.target.value })}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit_monthly_draw">Monthly Draw</Label>
                <Input
                  id="edit_monthly_draw"
                  type="number"
                  step="0.01"
                  value={formData.monthly_draw}
                  onChange={(e) => setFormData({ ...formData, monthly_draw: parseFloat(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit_start_date">Start Date</Label>
                <Input
                  id="edit_start_date"
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit_starting_balance">Starting Balance</Label>
              <Input
                id="edit_starting_balance"
                type="number"
                step="0.01"
                value={formData.starting_balance}
                onChange={(e) => setFormData({ ...formData, starting_balance: parseFloat(e.target.value) || 0 })}
              />
              <p className="text-xs text-muted-foreground">
                Positive = rep owes company (overdraw), Negative = company owes rep
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit_notes">Notes</Label>
              <Input
                id="edit_notes"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              />
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="edit_is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
              />
              <Label htmlFor="edit_is_active">Active</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              Cancel
            </Button>
            <Button onClick={() => handleSave(false)} disabled={saving || !formData.salesman_name}>
              {saving ? <LoadingSpinner size="small" /> : <Save className="h-4 w-4 mr-2" />}
              Update
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default RepCompAdmin
