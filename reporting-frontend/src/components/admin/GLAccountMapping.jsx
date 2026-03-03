import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Search, RefreshCw, Download, Upload, Settings2, 
  ChevronLeft, ChevronRight, Check, X, Edit2, Save,
  AlertCircle, CheckCircle2, Loader2, Database
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || '';
const getToken = () => localStorage.getItem('token');

const apiRequest = async (path, options = {}) => {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`,
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `Request failed: ${res.status}`);
  }
  return res.json();
};

// Account type badge colors
const TYPE_COLORS = {
  revenue: 'bg-green-100 text-green-800',
  cogs: 'bg-orange-100 text-orange-800',
  expense: 'bg-red-100 text-red-800',
  other_income: 'bg-blue-100 text-blue-800',
  other: 'bg-gray-100 text-gray-800',
};

const TYPE_LABELS = {
  revenue: 'Revenue',
  cogs: 'COGS',
  expense: 'Expense',
  other_income: 'Other Income',
  other: 'Other',
};

const ITEMS_PER_PAGE = 50;

export const GLAccountMapping = ({ user, organization }) => {
  const [accounts, setAccounts] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [expenseCategories, setExpenseCategories] = useState([]);
  const [discoveryLogs, setDiscoveryLogs] = useState([]);
  const [summary, setSummary] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeTab, setActiveTab] = useState('accounts');
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterDept, setFilterDept] = useState('all');
  const [filterCategory, setFilterCategory] = useState('all');
  const [filterActive, setFilterActive] = useState('all');
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  
  // Editing
  const [editingId, setEditingId] = useState(null);
  const [editValues, setEditValues] = useState({});
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [bulkEditOpen, setBulkEditOpen] = useState(false);
  const [bulkValues, setBulkValues] = useState({});

  // Fetch all data
  const fetchData = async () => {
    setIsLoading(true);
    setError('');
    try {
      const [accountsRes, deptsRes, catsRes, logsRes] = await Promise.all([
        apiRequest('/api/gl-mapping/accounts'),
        apiRequest('/api/gl-mapping/departments'),
        apiRequest('/api/gl-mapping/expense-categories'),
        apiRequest('/api/gl-mapping/discovery-log'),
      ]);
      setAccounts(accountsRes.accounts || []);
      setSummary(accountsRes.summary || []);
      setDepartments(deptsRes.departments || []);
      setExpenseCategories(catsRes.categories || []);
      setDiscoveryLogs(logsRes.logs || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filtered and paginated accounts
  const filteredAccounts = useMemo(() => {
    return accounts.filter(a => {
      if (searchTerm && !a.account_no?.includes(searchTerm) && 
          !a.description?.toLowerCase().includes(searchTerm.toLowerCase())) return false;
      if (filterType !== 'all' && a.account_type !== filterType) return false;
      if (filterDept !== 'all' && a.department_code !== filterDept) return false;
      if (filterCategory !== 'all' && a.expense_category !== filterCategory) return false;
      if (filterActive === 'active' && !a.is_active) return false;
      if (filterActive === 'inactive' && a.is_active) return false;
      return true;
    });
  }, [accounts, searchTerm, filterType, filterDept, filterCategory, filterActive]);

  const totalPages = Math.ceil(filteredAccounts.length / ITEMS_PER_PAGE);
  const paginatedAccounts = filteredAccounts.slice(
    (currentPage - 1) * ITEMS_PER_PAGE, 
    currentPage * ITEMS_PER_PAGE
  );

  // Reset page when filters change
  useEffect(() => { setCurrentPage(1); }, [searchTerm, filterType, filterDept, filterCategory, filterActive]);

  // Discovery
  const handleDiscover = async () => {
    setIsDiscovering(true);
    setError('');
    setSuccess('');
    try {
      const result = await apiRequest('/api/gl-mapping/discover', { method: 'POST' });
      setSuccess(`Discovery complete! Found ${result.counts?.total || 0} accounts (${result.counts?.revenue || 0} revenue, ${result.counts?.cogs || 0} COGS, ${result.counts?.expense || 0} expense)`);
      await fetchData();
    } catch (err) {
      setError(`Discovery failed: ${err.message}`);
    } finally {
      setIsDiscovering(false);
    }
  };

  // Migration
  const handleMigrate = async () => {
    setError('');
    setSuccess('');
    try {
      const result = await apiRequest('/api/gl-mapping/migrate', { method: 'POST' });
      setSuccess(result.message);
      await fetchData();
    } catch (err) {
      setError(`Migration failed: ${err.message}`);
    }
  };

  // Inline editing
  const startEdit = (account) => {
    setEditingId(account.id);
    setEditValues({
      account_type: account.account_type,
      department_code: account.department_code || '',
      department_name: account.department_name || '',
      expense_category: account.expense_category || '',
      description: account.description || '',
      is_active: account.is_active,
    });
  };

  const saveEdit = async () => {
    try {
      await apiRequest(`/api/gl-mapping/accounts/${editingId}`, {
        method: 'PUT',
        body: JSON.stringify(editValues),
      });
      setEditingId(null);
      await fetchData();
      setSuccess('Account updated successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(`Update failed: ${err.message}`);
    }
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditValues({});
  };

  // Selection
  const toggleSelect = (id) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id); else next.add(id);
    setSelectedIds(next);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === paginatedAccounts.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(paginatedAccounts.map(a => a.id)));
    }
  };

  // Bulk update
  const handleBulkUpdate = async () => {
    try {
      const updates = {};
      if (bulkValues.account_type) updates.account_type = bulkValues.account_type;
      if (bulkValues.department_code) updates.department_code = bulkValues.department_code;
      if (bulkValues.expense_category) updates.expense_category = bulkValues.expense_category;
      if (bulkValues.is_active !== undefined) updates.is_active = bulkValues.is_active;

      await apiRequest('/api/gl-mapping/accounts/bulk-update', {
        method: 'PUT',
        body: JSON.stringify({
          account_ids: Array.from(selectedIds),
          updates,
        }),
      });
      setBulkEditOpen(false);
      setBulkValues({});
      setSelectedIds(new Set());
      await fetchData();
      setSuccess(`${selectedIds.size} accounts updated`);
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(`Bulk update failed: ${err.message}`);
    }
  };

  // Get unique department codes from accounts for filter dropdown
  const uniqueDepts = useMemo(() => {
    const depts = [...new Set(accounts.map(a => a.department_code).filter(Boolean))];
    return depts.sort();
  }, [accounts]);

  const uniqueCategories = useMemo(() => {
    const cats = [...new Set(accounts.map(a => a.expense_category).filter(Boolean))];
    return cats.sort();
  }, [accounts]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Loading GL accounts...</span>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">GL Account Mapping</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage chart of accounts mapping for {organization?.name || 'your organization'}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleMigrate} size="sm">
            <Database className="h-4 w-4 mr-1" />
            Initialize Tables
          </Button>
          <Button 
            onClick={handleDiscover} 
            disabled={isDiscovering}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isDiscovering ? (
              <><Loader2 className="h-4 w-4 mr-1 animate-spin" />Discovering...</>
            ) : (
              <><RefreshCw className="h-4 w-4 mr-1" />Run Discovery</>
            )}
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
          <Button variant="ghost" size="sm" className="ml-auto" onClick={() => setError('')}>
            <X className="h-4 w-4" />
          </Button>
        </Alert>
      )}
      {success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {['revenue', 'cogs', 'expense', 'other_income', 'other'].map(type => {
          const s = summary.find(s => s.account_type === type);
          return (
            <Card key={type} className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => { setFilterType(type); setActiveTab('accounts'); }}>
              <CardContent className="p-4">
                <div className="text-xs font-medium text-gray-500 uppercase">{TYPE_LABELS[type]}</div>
                <div className="text-2xl font-bold mt-1">{s?.count || 0}</div>
                <div className="text-xs text-gray-400">{s?.active_count || 0} active</div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="accounts">Accounts ({filteredAccounts.length})</TabsTrigger>
          <TabsTrigger value="departments">Departments ({departments.length})</TabsTrigger>
          <TabsTrigger value="categories">Expense Categories ({expenseCategories.length})</TabsTrigger>
          <TabsTrigger value="history">Discovery History</TabsTrigger>
        </TabsList>

        {/* ACCOUNTS TAB */}
        <TabsContent value="accounts" className="space-y-4">
          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-wrap gap-3 items-center">
                <div className="relative flex-1 min-w-[200px]">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search account number or description..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <Select value={filterType} onValueChange={setFilterType}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="Type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    {Object.entries(TYPE_LABELS).map(([k, v]) => (
                      <SelectItem key={k} value={k}>{v}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={filterDept} onValueChange={setFilterDept}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="Department" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Depts</SelectItem>
                    {uniqueDepts.map(d => (
                      <SelectItem key={d} value={d}>{d}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={filterActive} onValueChange={setFilterActive}>
                  <SelectTrigger className="w-[120px]">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>
                {selectedIds.size > 0 && (
                  <Button variant="outline" onClick={() => setBulkEditOpen(true)}>
                    <Edit2 className="h-4 w-4 mr-1" />
                    Edit {selectedIds.size} selected
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Accounts Table */}
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-10">
                        <Checkbox 
                          checked={paginatedAccounts.length > 0 && selectedIds.size === paginatedAccounts.length}
                          onCheckedChange={toggleSelectAll}
                        />
                      </TableHead>
                      <TableHead>Account No</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Department</TableHead>
                      <TableHead>Expense Category</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Source</TableHead>
                      <TableHead className="w-20">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginatedAccounts.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={9} className="text-center py-8 text-gray-500">
                          {accounts.length === 0 
                            ? 'No accounts found. Click "Run Discovery" to auto-discover GL accounts from your database.'
                            : 'No accounts match the current filters.'}
                        </TableCell>
                      </TableRow>
                    ) : paginatedAccounts.map(account => (
                      <TableRow key={account.id} className={!account.is_active ? 'opacity-50' : ''}>
                        <TableCell>
                          <Checkbox 
                            checked={selectedIds.has(account.id)}
                            onCheckedChange={() => toggleSelect(account.id)}
                          />
                        </TableCell>
                        <TableCell className="font-mono text-sm font-medium">
                          {account.account_no}
                        </TableCell>
                        <TableCell>
                          {editingId === account.id ? (
                            <Select value={editValues.account_type} onValueChange={v => setEditValues({...editValues, account_type: v})}>
                              <SelectTrigger className="w-[120px] h-8">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {Object.entries(TYPE_LABELS).map(([k, v]) => (
                                  <SelectItem key={k} value={k}>{v}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          ) : (
                            <Badge className={TYPE_COLORS[account.account_type] || TYPE_COLORS.other}>
                              {TYPE_LABELS[account.account_type] || account.account_type}
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          {editingId === account.id ? (
                            <div className="flex gap-1">
                              <Input className="w-16 h-8" value={editValues.department_code}
                                onChange={e => setEditValues({...editValues, department_code: e.target.value})} 
                                placeholder="Code" />
                              <Input className="w-24 h-8" value={editValues.department_name}
                                onChange={e => setEditValues({...editValues, department_name: e.target.value})} 
                                placeholder="Name" />
                            </div>
                          ) : (
                            <span className="text-sm">
                              {account.department_code && (
                                <span className="font-mono text-xs bg-gray-100 px-1 rounded mr-1">
                                  {account.department_code}
                                </span>
                              )}
                              {account.department_name || '—'}
                            </span>
                          )}
                        </TableCell>
                        <TableCell>
                          {editingId === account.id ? (
                            <Input className="w-32 h-8" value={editValues.expense_category}
                              onChange={e => setEditValues({...editValues, expense_category: e.target.value})} 
                              placeholder="Category" />
                          ) : (
                            <span className="text-sm">{account.expense_category || '—'}</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {editingId === account.id ? (
                            <Input className="w-48 h-8" value={editValues.description}
                              onChange={e => setEditValues({...editValues, description: e.target.value})} />
                          ) : (
                            <span className="text-sm text-gray-600">{account.description || '—'}</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {editingId === account.id ? (
                            <Checkbox 
                              checked={editValues.is_active}
                              onCheckedChange={v => setEditValues({...editValues, is_active: v})}
                            />
                          ) : (
                            <Badge variant={account.is_active ? 'default' : 'secondary'}>
                              {account.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <span className="text-xs text-gray-400">
                            {account.is_auto_discovered ? 'Auto' : 'Manual'}
                          </span>
                        </TableCell>
                        <TableCell>
                          {editingId === account.id ? (
                            <div className="flex gap-1">
                              <Button variant="ghost" size="sm" onClick={saveEdit}>
                                <Check className="h-4 w-4 text-green-600" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={cancelEdit}>
                                <X className="h-4 w-4 text-red-600" />
                              </Button>
                            </div>
                          ) : (
                            <Button variant="ghost" size="sm" onClick={() => startEdit(account)}>
                              <Edit2 className="h-4 w-4" />
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t">
                  <span className="text-sm text-gray-500">
                    Showing {(currentPage - 1) * ITEMS_PER_PAGE + 1}–{Math.min(currentPage * ITEMS_PER_PAGE, filteredAccounts.length)} of {filteredAccounts.length}
                  </span>
                  <div className="flex gap-1">
                    <Button variant="outline" size="sm" disabled={currentPage === 1}
                      onClick={() => setCurrentPage(p => p - 1)}>
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="px-3 py-1 text-sm">{currentPage} / {totalPages}</span>
                    <Button variant="outline" size="sm" disabled={currentPage === totalPages}
                      onClick={() => setCurrentPage(p => p + 1)}>
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* DEPARTMENTS TAB */}
        <TabsContent value="departments">
          <Card>
            <CardHeader>
              <CardTitle>Departments</CardTitle>
              <CardDescription>
                Departments are auto-discovered from GL account number patterns. 
                Edit names and display order to customize your reports.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Code</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Revenue Accounts</TableHead>
                    <TableHead>COGS Accounts</TableHead>
                    <TableHead>Expense Accounts</TableHead>
                    <TableHead>Total Accounts</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {departments.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                        No departments found. Run discovery to auto-detect departments.
                      </TableCell>
                    </TableRow>
                  ) : departments.map(dept => (
                    <TableRow key={dept.id}>
                      <TableCell className="font-mono font-medium">{dept.dept_code}</TableCell>
                      <TableCell>{dept.dept_name}</TableCell>
                      <TableCell>{dept.revenue_accounts || 0}</TableCell>
                      <TableCell>{dept.cogs_accounts || 0}</TableCell>
                      <TableCell>{dept.expense_accounts || 0}</TableCell>
                      <TableCell className="font-medium">{dept.account_count || 0}</TableCell>
                      <TableCell>
                        <Badge variant={dept.is_active ? 'default' : 'secondary'}>
                          {dept.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* EXPENSE CATEGORIES TAB */}
        <TabsContent value="categories">
          <Card>
            <CardHeader>
              <CardTitle>Expense Categories</CardTitle>
              <CardDescription>
                Expense categories group 6xxxxx accounts for P&L reporting.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Key</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Account Count</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {expenseCategories.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center py-8 text-gray-500">
                        No expense categories found. Run discovery to auto-detect categories.
                      </TableCell>
                    </TableRow>
                  ) : expenseCategories.map(cat => (
                    <TableRow key={cat.id}>
                      <TableCell className="font-mono">{cat.category_key}</TableCell>
                      <TableCell>{cat.category_name}</TableCell>
                      <TableCell>{cat.account_count || 0}</TableCell>
                      <TableCell>
                        <Badge variant={cat.is_active ? 'default' : 'secondary'}>
                          {cat.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* DISCOVERY HISTORY TAB */}
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Discovery History</CardTitle>
              <CardDescription>
                Log of all GL account discovery runs for this tenant.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Accounts Found</TableHead>
                    <TableHead>New</TableHead>
                    <TableHead>Updated</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Error</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {discoveryLogs.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                        No discovery runs yet. Click "Run Discovery" to start.
                      </TableCell>
                    </TableRow>
                  ) : discoveryLogs.map(log => (
                    <TableRow key={log.id}>
                      <TableCell className="text-sm">
                        {new Date(log.started_at).toLocaleString()}
                      </TableCell>
                      <TableCell>{log.discovery_type}</TableCell>
                      <TableCell>{log.accounts_found || 0}</TableCell>
                      <TableCell className="text-green-600">{log.accounts_new || 0}</TableCell>
                      <TableCell className="text-blue-600">{log.accounts_updated || 0}</TableCell>
                      <TableCell>
                        <Badge variant={log.status === 'completed' ? 'default' : 'destructive'}>
                          {log.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-red-500 max-w-[200px] truncate">
                        {log.error_message || '—'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Bulk Edit Dialog */}
      <Dialog open={bulkEditOpen} onOpenChange={setBulkEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Bulk Edit {selectedIds.size} Accounts</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium">Account Type</label>
              <Select value={bulkValues.account_type || ''} onValueChange={v => setBulkValues({...bulkValues, account_type: v})}>
                <SelectTrigger>
                  <SelectValue placeholder="Don't change" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(TYPE_LABELS).map(([k, v]) => (
                    <SelectItem key={k} value={k}>{v}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">Department Code</label>
              <Input value={bulkValues.department_code || ''} 
                onChange={e => setBulkValues({...bulkValues, department_code: e.target.value})}
                placeholder="Don't change" />
            </div>
            <div>
              <label className="text-sm font-medium">Expense Category</label>
              <Input value={bulkValues.expense_category || ''} 
                onChange={e => setBulkValues({...bulkValues, expense_category: e.target.value})}
                placeholder="Don't change" />
            </div>
            <div className="flex items-center gap-2">
              <Checkbox 
                checked={bulkValues.is_active === true}
                onCheckedChange={v => setBulkValues({...bulkValues, is_active: v})}
              />
              <label className="text-sm">Set as Active</label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkEditOpen(false)}>Cancel</Button>
            <Button onClick={handleBulkUpdate}>Apply Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default GLAccountMapping;
