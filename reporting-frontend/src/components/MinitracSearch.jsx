import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Loader2, Search, Download, FileText, DollarSign, Calendar, Gauge, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { apiUrl } from '@/lib/api';

const MinitracSearch = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    category: '',
    status: '',
    make: ''
  });
  const [filterOptions, setFilterOptions] = useState({
    categories: [],
    statuses: [],
    makes: [],
    groups: []
  });
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [unitDetails, setUnitDetails] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 50,
    total: 0,
    total_pages: 0
  });
  const [sortConfig, setSortConfig] = useState({
    key: null,
    direction: 'asc'
  });

  // Load filter options on mount
  useEffect(() => {
    loadFilterOptions();
  }, []);

  const loadFilterOptions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl('/api/minitrac/filters'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setFilterOptions(data.filters);
      }
    } catch (error) {
      console.error('Error loading filter options:', error);
    }
  };

  const handleSearch = async (page = 1) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        search: searchTerm,
        category: filters.category,
        status: filters.status,
        make: filters.make,
        page: page,
        per_page: 50
      });

      const response = await fetch(apiUrl(`/api/minitrac/search?${params}`), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      
      if (data.success) {
        setResults(data.data);
        setPagination(data.pagination);
      }
    } catch (error) {
      console.error('Error searching:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUnitDetails = async (unitNum) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl(`/api/minitrac/equipment/${unitNum}`), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setUnitDetails(data.data);
        setSelectedUnit(unitNum);
      }
    } catch (error) {
      console.error('Error loading unit details:', error);
    }
  };

  const handleExport = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        search: searchTerm,
        category: filters.category,
        status: filters.status,
        make: filters.make
      });

      const response = await fetch(apiUrl(`/api/minitrac/export?${params}`), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `minitrac_export_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting:', error);
    }
  };

  const formatCurrency = (value) => {
    if (!value) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatDate = (date) => {
    if (!date) return '-';
    return new Date(date).toLocaleDateString();
  };

  // Sorting function
  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Sort results based on current sort configuration
  const sortedResults = React.useMemo(() => {
    let sortableResults = [...results];
    if (sortConfig.key) {
      sortableResults.sort((a, b) => {
        // Handle null/undefined values
        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];
        
        if (aValue === null || aValue === undefined) return 1;
        if (bValue === null || bValue === undefined) return -1;
        
        // Handle numeric fields
        if (sortConfig.key === 'net_book_val' || sortConfig.key === 'ytd_income' || sortConfig.key === 'year') {
          const aNum = parseFloat(aValue) || 0;
          const bNum = parseFloat(bValue) || 0;
          return sortConfig.direction === 'asc' ? aNum - bNum : bNum - aNum;
        }
        
        // Handle string fields
        if (aValue < bValue) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableResults;
  }, [results, sortConfig]);

  // Helper function to get sort icon
  const getSortIcon = (columnKey) => {
    if (sortConfig.key !== columnKey) {
      return <ArrowUpDown className="h-4 w-4 ml-1 opacity-50" />;
    }
    return sortConfig.direction === 'asc' 
      ? <ArrowUp className="h-4 w-4 ml-1" />
      : <ArrowDown className="h-4 w-4 ml-1" />;
  };

  return (
    <div className="space-y-6">
      {/* Search Interface */}
      <Card>
        <CardHeader>
          <CardTitle>Search Minitrac Historical Data</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Search Bar */}
            <div className="flex gap-2">
              <Input
                placeholder="Search by unit #, serial, make, model, or customer..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1"
              />
              <Button onClick={() => handleSearch()} disabled={loading}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                Search
              </Button>
              {results.length > 0 && (
                <Button variant="outline" onClick={handleExport}>
                  <Download className="h-4 w-4 mr-2" />
                  Export CSV
                </Button>
              )}
            </div>

            {/* Filters */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Select value={filters.category || "all"} onValueChange={(value) => setFilters({...filters, category: value === "all" ? "" : value})}>
                <SelectTrigger>
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {filterOptions.categories.map(cat => (
                    <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={filters.status || "all"} onValueChange={(value) => setFilters({...filters, status: value === "all" ? "" : value})}>
                <SelectTrigger>
                  <SelectValue placeholder="All Statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  {filterOptions.statuses.map(status => (
                    <SelectItem key={status} value={status}>{status}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={filters.make || "all"} onValueChange={(value) => setFilters({...filters, make: value === "all" ? "" : value})}>
                <SelectTrigger>
                  <SelectValue placeholder="All Makes" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Makes</SelectItem>
                  {filterOptions.makes.map(make => (
                    <SelectItem key={make} value={make}>{make}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results Table */}
      {results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>
              Search Results ({pagination.total} total)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50" 
                      onClick={() => handleSort('unit_num')}
                    >
                      <div className="flex items-center">
                        Unit #
                        {getSortIcon('unit_num')}
                      </div>
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50" 
                      onClick={() => handleSort('category')}
                    >
                      <div className="flex items-center">
                        Category
                        {getSortIcon('category')}
                      </div>
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50" 
                      onClick={() => handleSort('serial')}
                    >
                      <div className="flex items-center">
                        Serial
                        {getSortIcon('serial')}
                      </div>
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50" 
                      onClick={() => handleSort('make')}
                    >
                      <div className="flex items-center">
                        Make
                        {getSortIcon('make')}
                      </div>
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50" 
                      onClick={() => handleSort('model')}
                    >
                      <div className="flex items-center">
                        Model
                        {getSortIcon('model')}
                      </div>
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50" 
                      onClick={() => handleSort('year')}
                    >
                      <div className="flex items-center">
                        Year
                        {getSortIcon('year')}
                      </div>
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50" 
                      onClick={() => handleSort('status')}
                    >
                      <div className="flex items-center">
                        Status
                        {getSortIcon('status')}
                      </div>
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50" 
                      onClick={() => handleSort('ship_name')}
                    >
                      <div className="flex items-center">
                        Customer
                        {getSortIcon('ship_name')}
                      </div>
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50" 
                      onClick={() => handleSort('net_book_val')}
                    >
                      <div className="flex items-center">
                        Book Value
                        {getSortIcon('net_book_val')}
                      </div>
                    </TableHead>
                    <TableHead 
                      className="cursor-pointer hover:bg-gray-50" 
                      onClick={() => handleSort('ytd_income')}
                    >
                      <div className="flex items-center">
                        YTD Income
                        {getSortIcon('ytd_income')}
                      </div>
                    </TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedResults.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="font-mono">{item.unit_num}</TableCell>
                      <TableCell>{item.category}</TableCell>
                      <TableCell>{item.serial || '-'}</TableCell>
                      <TableCell>{item.make || '-'}</TableCell>
                      <TableCell>{item.model || '-'}</TableCell>
                      <TableCell>{item.year || '-'}</TableCell>
                      <TableCell>
                        <Badge variant={item.status === 'A' ? 'success' : 'secondary'}>
                          {item.status || '-'}
                        </Badge>
                      </TableCell>
                      <TableCell>{item.ship_name || '-'}</TableCell>
                      <TableCell className="text-right">{formatCurrency(item.net_book_val)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(item.ytd_income)}</TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => loadUnitDetails(item.unit_num)}
                        >
                          <FileText className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            {pagination.total_pages > 1 && (
              <div className="flex justify-between items-center mt-4">
                <div className="text-sm text-gray-600">
                  Page {pagination.page} of {pagination.total_pages}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleSearch(pagination.page - 1)}
                    disabled={pagination.page === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleSearch(pagination.page + 1)}
                    disabled={pagination.page === pagination.total_pages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Unit Details Dialog */}
      <Dialog open={!!selectedUnit} onOpenChange={() => setSelectedUnit(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Equipment Details - Unit {selectedUnit}</DialogTitle>
          </DialogHeader>
          {unitDetails && (
            <div className="space-y-6">
              {/* Basic Info */}
              <div>
                <h3 className="font-semibold mb-2">Basic Information</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="font-medium">Unit:</span> {unitDetails.unit_num}</div>
                  <div><span className="font-medium">Serial:</span> {unitDetails.serial || '-'}</div>
                  <div><span className="font-medium">Make:</span> {unitDetails.make || '-'}</div>
                  <div><span className="font-medium">Model:</span> {unitDetails.model || '-'}</div>
                  <div><span className="font-medium">Year:</span> {unitDetails.year || '-'}</div>
                  <div><span className="font-medium">Category:</span> {unitDetails.category || '-'}</div>
                  <div><span className="font-medium">Status:</span> {unitDetails.status || '-'}</div>
                  <div><span className="font-medium">Description:</span> {unitDetails.unit_desc || '-'}</div>
                </div>
              </div>

              {/* Customer Info */}
              <div>
                <h3 className="font-semibold mb-2">Customer Information</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="font-medium">Ship To:</span> {unitDetails.ship_name || '-'}</div>
                  <div><span className="font-medium">Bill To:</span> {unitDetails.bill_cust || '-'}</div>
                  <div><span className="font-medium">Address 1:</span> {unitDetails.ship_addr1 || '-'}</div>
                  <div><span className="font-medium">Address 2:</span> {unitDetails.ship_addr2 || '-'}</div>
                  <div><span className="font-medium">City/State/Zip:</span> {unitDetails.ship_addr3 || '-'} {unitDetails.ship_zip || ''}</div>
                </div>
              </div>

              {/* Financial Info */}
              <div>
                <h3 className="font-semibold mb-2">Financial Information</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="font-medium">Acquisition Cost:</span> {formatCurrency(unitDetails.acq_cost)}</div>
                  <div><span className="font-medium">Book Value:</span> {formatCurrency(unitDetails.net_book_val)}</div>
                  <div><span className="font-medium">YTD Income:</span> {formatCurrency(unitDetails.ytd_income)}</div>
                  <div><span className="font-medium">YTD Expense:</span> {formatCurrency(unitDetails.ytd_expense)}</div>
                  <div><span className="font-medium">ATD Income:</span> {formatCurrency(unitDetails.atd_income)}</div>
                  <div><span className="font-medium">ATD Expense:</span> {formatCurrency(unitDetails.atd_expense)}</div>
                </div>
              </div>

              {/* Contract Info */}
              {unitDetails.cont_no && (
                <div>
                  <h3 className="font-semibold mb-2">Contract Information</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div><span className="font-medium">Contract #:</span> {unitDetails.cont_no}</div>
                    <div><span className="font-medium">Status:</span> {unitDetails.contr_stat || '-'}</div>
                    <div><span className="font-medium">Rate:</span> {formatCurrency(unitDetails.contr_rate)}</div>
                    <div><span className="font-medium">Cycle:</span> {unitDetails.contr_cyc || '-'}</div>
                    <div><span className="font-medium">From:</span> {formatDate(unitDetails.contr_from_date)}</div>
                    <div><span className="font-medium">Through:</span> {formatDate(unitDetails.contr_thru_date)}</div>
                  </div>
                </div>
              )}

              {/* Meter Info */}
              {unitDetails.curr_meter_read && (
                <div>
                  <h3 className="font-semibold mb-2">Meter Information</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div><span className="font-medium">Current Reading:</span> {unitDetails.curr_meter_read?.toLocaleString() || '-'}</div>
                    <div><span className="font-medium">Date:</span> {formatDate(unitDetails.curr_meter_dt)}</div>
                    <div><span className="font-medium">Last Reading:</span> {unitDetails.last_meter_read?.toLocaleString() || '-'}</div>
                    <div><span className="font-medium">Date:</span> {formatDate(unitDetails.last_meter_dt)}</div>
                  </div>
                </div>
              )}

              {/* Engine Info */}
              {unitDetails.eng_make && (
                <div>
                  <h3 className="font-semibold mb-2">Engine Information</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div><span className="font-medium">Make:</span> {unitDetails.eng_make}</div>
                    <div><span className="font-medium">Model:</span> {unitDetails.eng_model || '-'}</div>
                    <div><span className="font-medium">Serial:</span> {unitDetails.eng_serial || '-'}</div>
                    <div><span className="font-medium">Year:</span> {unitDetails.eng_yr || '-'}</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MinitracSearch;