import React, { useState, useEffect, useMemo } from 'react';
import { format, subMonths, startOfMonth, endOfMonth } from 'date-fns';
import { Calendar as CalendarIcon, DollarSign, Hash, TrendingUp, Download, Search, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow, TableFooter } from '@/components/ui/table';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { apiUrl } from '@/lib/api';

const formatCurrency = (value) => {
  if (value === null || value === undefined) return '$0';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const formatCurrencyDetailed = (value) => {
  if (value === null || value === undefined) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

const CHART_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1',
  '#14b8a6', '#eab308', '#dc2626', '#7c3aed', '#0ea5e9',
];

const SalesBreakdown = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [startDate, setStartDate] = useState(() => startOfMonth(subMonths(new Date(), 11)));
  const [endDate, setEndDate] = useState(() => endOfMonth(new Date()));
  const [startOpen, setStartOpen] = useState(false);
  const [endOpen, setEndOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('revenue');
  const [sortDirection, setSortDirection] = useState('desc');

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const startStr = format(startDate, 'yyyy-MM-dd');
      const endStr = format(endDate, 'yyyy-MM-dd');
      const response = await fetch(
        apiUrl(`/api/reports/sales-breakdown?start_date=${startStr}&end_date=${endStr}`),
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || 'Failed to fetch sales breakdown');
      }
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [startDate, endDate]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const filteredAndSorted = useMemo(() => {
    if (!data?.accounts) return [];
    let filtered = data.accounts;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        a => a.account_no.toLowerCase().includes(term) || a.description.toLowerCase().includes(term)
      );
    }
    return [...filtered].sort((a, b) => {
      let aVal, bVal;
      switch (sortField) {
        case 'account_no':
          aVal = a.account_no;
          bVal = b.account_no;
          return sortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        case 'description':
          aVal = a.description;
          bVal = b.description;
          return sortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        case 'revenue':
          aVal = a.revenue;
          bVal = b.revenue;
          return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
        case 'pct_of_total':
          aVal = a.pct_of_total;
          bVal = b.pct_of_total;
          return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
        default:
          return 0;
      }
    });
  }, [data, searchTerm, sortField, sortDirection]);

  // Top 10 for chart
  const chartData = useMemo(() => {
    if (!data?.accounts) return [];
    return [...data.accounts]
      .sort((a, b) => b.revenue - a.revenue)
      .slice(0, 10)
      .map(a => ({
        name: a.description.length > 25 ? a.description.substring(0, 22) + '...' : a.description,
        fullName: a.description,
        accountNo: a.account_no,
        revenue: a.revenue,
        pct: a.pct_of_total,
      }));
  }, [data]);

  const exportCSV = () => {
    if (!filteredAndSorted.length) return;
    const headers = ['Account No', 'Description', 'Revenue', '% of Total'];
    const rows = filteredAndSorted.map(a => [
      a.account_no,
      `"${a.description}"`,
      a.revenue.toFixed(2),
      a.pct_of_total.toFixed(2) + '%',
    ]);
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `sales-breakdown-${format(startDate, 'yyyy-MM-dd')}-to-${format(endDate, 'yyyy-MM-dd')}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) return <ArrowUpDown className="h-3 w-3 ml-1 opacity-40" />;
    return sortDirection === 'asc' ? <ArrowUp className="h-3 w-3 ml-1" /> : <ArrowDown className="h-3 w-3 ml-1" />;
  };

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
        <p className="font-semibold text-gray-800">{d.fullName}</p>
        <p className="text-gray-500 text-xs">Account: {d.accountNo}</p>
        <p className="text-blue-600 font-medium mt-1">{formatCurrencyDetailed(d.revenue)}</p>
        <p className="text-gray-500">{d.pct.toFixed(1)}% of total</p>
      </div>
    );
  };

  // Compute summary stats
  const positiveAccounts = data?.accounts?.filter(a => a.revenue > 0) || [];
  const negativeAccounts = data?.accounts?.filter(a => a.revenue < 0) || [];
  const totalPositive = positiveAccounts.reduce((s, a) => s + a.revenue, 0);
  const totalNegative = negativeAccounts.reduce((s, a) => s + a.revenue, 0);

  return (
    <div className="space-y-4">
      {/* Header with date pickers */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">Sales Breakdown by GL Account</h2>
          <p className="text-sm text-gray-500">Revenue by General Ledger account (4xxx series)</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {/* Start Date Picker */}
          <Popover open={startOpen} onOpenChange={setStartOpen}>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-[160px] justify-start text-left font-normal text-sm">
                <CalendarIcon className="mr-2 h-4 w-4" />
                {format(startDate, 'MMM d, yyyy')}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="end">
              <Calendar
                mode="single"
                selected={startDate}
                onSelect={(date) => {
                  if (date) {
                    setStartDate(date);
                    setStartOpen(false);
                  }
                }}
                initialFocus
              />
            </PopoverContent>
          </Popover>
          <span className="text-gray-400 text-sm">to</span>
          {/* End Date Picker */}
          <Popover open={endOpen} onOpenChange={setEndOpen}>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-[160px] justify-start text-left font-normal text-sm">
                <CalendarIcon className="mr-2 h-4 w-4" />
                {format(endDate, 'MMM d, yyyy')}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="end">
              <Calendar
                mode="single"
                selected={endDate}
                onSelect={(date) => {
                  if (date) {
                    setEndDate(date);
                    setEndOpen(false);
                  }
                }}
                initialFocus
              />
            </PopoverContent>
          </Popover>
          <Button variant="outline" size="sm" onClick={exportCSV} disabled={!data?.accounts?.length}>
            <Download className="h-4 w-4 mr-1" />
            CSV
          </Button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700 text-sm">{error}</p>
          <Button variant="outline" size="sm" className="mt-2" onClick={fetchData}>Retry</Button>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-3 text-gray-500">Loading sales breakdown...</span>
        </div>
      )}

      {/* Content */}
      {!loading && !error && data && (
        <>
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card className="border-l-4 border-l-blue-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <DollarSign className="h-4 w-4 text-blue-500" />
                  <span className="text-xs font-medium text-muted-foreground">Total Revenue</span>
                </div>
                <div className="text-2xl font-bold">{formatCurrency(data.total_revenue)}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {format(startDate, 'MMM yyyy')} – {format(endDate, 'MMM yyyy')}
                </p>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-green-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <Hash className="h-4 w-4 text-green-500" />
                  <span className="text-xs font-medium text-muted-foreground">GL Accounts</span>
                </div>
                <div className="text-2xl font-bold">{data.account_count}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Active revenue accounts
                </p>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-emerald-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="h-4 w-4 text-emerald-500" />
                  <span className="text-xs font-medium text-muted-foreground">Revenue Accounts</span>
                </div>
                <div className="text-2xl font-bold">{positiveAccounts.length}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {formatCurrency(totalPositive)} total
                </p>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-amber-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <DollarSign className="h-4 w-4 text-amber-500" />
                  <span className="text-xs font-medium text-muted-foreground">Contra/Adjustments</span>
                </div>
                <div className="text-2xl font-bold">{negativeAccounts.length}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {formatCurrency(totalNegative)} total
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Top 10 Chart */}
          {chartData.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Top 10 Revenue Accounts</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis
                      type="number"
                      tickFormatter={(v) => formatCurrency(v)}
                      fontSize={11}
                    />
                    <YAxis
                      type="category"
                      dataKey="name"
                      width={180}
                      fontSize={11}
                      tick={{ fill: '#6b7280' }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="revenue" radius={[0, 4, 4, 0]}>
                      {chartData.map((_, index) => (
                        <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Table */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">All GL Accounts</CardTitle>
                <div className="relative w-64">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search account or description..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-8 h-9 text-sm"
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead
                      className="cursor-pointer select-none hover:bg-gray-50"
                      onClick={() => handleSort('account_no')}
                    >
                      <div className="flex items-center">
                        Account No <SortIcon field="account_no" />
                      </div>
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none hover:bg-gray-50"
                      onClick={() => handleSort('description')}
                    >
                      <div className="flex items-center">
                        Description <SortIcon field="description" />
                      </div>
                    </TableHead>
                    <TableHead
                      className="text-right cursor-pointer select-none hover:bg-gray-50"
                      onClick={() => handleSort('revenue')}
                    >
                      <div className="flex items-center justify-end">
                        Revenue <SortIcon field="revenue" />
                      </div>
                    </TableHead>
                    <TableHead
                      className="text-right cursor-pointer select-none hover:bg-gray-50"
                      onClick={() => handleSort('pct_of_total')}
                    >
                      <div className="flex items-center justify-end">
                        % of Total <SortIcon field="pct_of_total" />
                      </div>
                    </TableHead>
                    <TableHead className="w-[120px]">Distribution</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAndSorted.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-gray-500 py-8">
                        {searchTerm ? 'No accounts match your search' : 'No data available for this period'}
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredAndSorted.map((account, idx) => (
                      <TableRow key={account.account_no} className={idx % 2 === 0 ? '' : 'bg-gray-50/50'}>
                        <TableCell className="font-mono text-sm">{account.account_no}</TableCell>
                        <TableCell className="text-sm">{account.description}</TableCell>
                        <TableCell className={`text-right font-medium text-sm ${account.revenue < 0 ? 'text-red-600' : ''}`}>
                          {formatCurrencyDetailed(account.revenue)}
                        </TableCell>
                        <TableCell className="text-right text-sm text-gray-600">
                          {account.pct_of_total.toFixed(1)}%
                        </TableCell>
                        <TableCell>
                          <div className="w-full bg-gray-100 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${account.revenue < 0 ? 'bg-red-400' : 'bg-blue-500'}`}
                              style={{
                                width: `${Math.min(Math.abs(account.pct_of_total), 100)}%`,
                              }}
                            />
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
                {filteredAndSorted.length > 0 && (
                  <TableFooter>
                    <TableRow className="font-semibold">
                      <TableCell colSpan={2}>
                        Total ({filteredAndSorted.length} accounts{searchTerm ? ' matching filter' : ''})
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrencyDetailed(filteredAndSorted.reduce((s, a) => s + a.revenue, 0))}
                      </TableCell>
                      <TableCell className="text-right">
                        {(filteredAndSorted.reduce((s, a) => s + a.pct_of_total, 0)).toFixed(1)}%
                      </TableCell>
                      <TableCell />
                    </TableRow>
                  </TableFooter>
                )}
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};

export default SalesBreakdown;
