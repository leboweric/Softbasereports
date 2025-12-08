import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Plus, Edit2, Trash2, DollarSign, Users, Save, X, AlertCircle } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const RepCompAdmin = ({ user }) => {
  const [loading, setLoading] = useState(true)
  const [settings, setSettings] = useState([])
  const [error, setError] = useState(null)
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [editingSetting, setEditingSetting] = useState(null)
  const [saving, setSaving] = useState(false)

  // Form state - simplified to essential fields only
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    monthly_draw: '',
    start_date: '2025-03-01',
    starting_balance: '0'
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
      first_name: '',
      last_name: '',
      monthly_draw: '',
      start_date: '2025-03-01',
      starting_balance: '0'
    })
    setShowAddDialog(true)
  }

  const handleEdit = (setting) => {
    // Parse existing salesman_name into first/last
    const nameParts = (setting.salesman_name || '').split(' ')
    const firstName = nameParts[0] || ''
    const lastName = nameParts.slice(1).join(' ') || ''

    setEditingSetting(setting)
    setFormData({
      first_name: firstName,
      last_name: lastName,
      monthly_draw: String(setting.monthly_draw || 0),
      start_date: setting.start_date || '2025-03-01',
      starting_balance: String(setting.starting_balance || 0)
    })
    setShowEditDialog(true)
  }

  const handleSave = async (isNew = false) => {
    try {
      setSaving(true)
      const token = localStorage.getItem('token')

      // Combine first and last name
      const salesman_name = `${formData.first_name.trim()} ${formData.last_name.trim()}`.trim()

      const payload = {
        salesman_name,
        monthly_draw: parseFloat(formData.monthly_draw) || 0,
        start_date: formData.start_date,
        starting_balance: parseFloat(formData.starting_balance) || 0,
        is_active: true
      }

      const url = isNew
        ? apiUrl('/api/sales-rep-comp/settings')
        : apiUrl(`/api/sales-rep-comp/settings/${editingSetting.id}`)

      const response = await fetch(url, {
        method: isNew ? 'POST' : 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
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
      minimumFractionDigits: 0,
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

  const isFormValid = formData.first_name.trim() && formData.last_name.trim() && formData.monthly_draw

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
          <h1 className="text-2xl font-bold">Sales Rep Compensation</h1>
          <p className="text-muted-foreground">
            Manage monthly draw plans
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
      <div className="grid gap-4 md:grid-cols-2">
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
      </div>

      {/* Settings Table */}
      <Card>
        <CardHeader>
          <CardTitle>Compensation Plans</CardTitle>
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
                  <TableHead>Name</TableHead>
                  <TableHead className="text-right">Monthly Draw</TableHead>
                  <TableHead>Start Date</TableHead>
                  <TableHead className="text-right">Starting Balance</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {settings.map((setting) => (
                  <TableRow key={setting.id}>
                    <TableCell className="font-medium">{setting.salesman_name}</TableCell>
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
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add Sales Rep</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="first_name">First Name</Label>
                <Input
                  id="first_name"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  placeholder="Kevin"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name">Last Name</Label>
                <Input
                  id="last_name"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  placeholder="Smith"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="monthly_draw">Monthly Draw ($)</Label>
              <Input
                id="monthly_draw"
                type="number"
                value={formData.monthly_draw}
                onChange={(e) => setFormData({ ...formData, monthly_draw: e.target.value })}
                placeholder="5000"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="start_date">Start Date</Label>
                <Input
                  id="start_date"
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="starting_balance">Starting Balance ($)</Label>
                <Input
                  id="starting_balance"
                  type="number"
                  value={formData.starting_balance}
                  onChange={(e) => setFormData({ ...formData, starting_balance: e.target.value })}
                  placeholder="0"
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddDialog(false)}>
              Cancel
            </Button>
            <Button onClick={() => handleSave(true)} disabled={saving || !isFormValid}>
              {saving ? <LoadingSpinner size="small" /> : <Save className="h-4 w-4 mr-2" />}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit {editingSetting?.salesman_name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit_first_name">First Name</Label>
                <Input
                  id="edit_first_name"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit_last_name">Last Name</Label>
                <Input
                  id="edit_last_name"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit_monthly_draw">Monthly Draw ($)</Label>
              <Input
                id="edit_monthly_draw"
                type="number"
                value={formData.monthly_draw}
                onChange={(e) => setFormData({ ...formData, monthly_draw: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit_start_date">Start Date</Label>
                <Input
                  id="edit_start_date"
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit_starting_balance">Starting Balance ($)</Label>
                <Input
                  id="edit_starting_balance"
                  type="number"
                  value={formData.starting_balance}
                  onChange={(e) => setFormData({ ...formData, starting_balance: e.target.value })}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              Cancel
            </Button>
            <Button onClick={() => handleSave(false)} disabled={saving || !isFormValid}>
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
