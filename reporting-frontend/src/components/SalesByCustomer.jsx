import React, { useState, useEffect, useMemo } from 'react';
import { format, subMonths, startOfMonth, endOfMonth } from 'date-fns';
import {
  Calendar as CalendarIcon,
  DollarSign,
  Users,
  TrendingUp,
  Download,
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  BarChart3,
  Percent,
  Layers,
} from 'lucide-react';
import { Tooltip as UITooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow, TableFooter } from '@/components/ui/table';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts';
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

const SalesByCustomer = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [startDate, setStartDate] = useState(() => startOfMonth(subMonths(new Date(), 11)));
  const [endDate, setEndDate] = useState(() => endOfMonth(new Date()));
  const [startOpen, setStartOpen] = useState(false);
  const [endOpen, setEndOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('total_revenue');
  const [sortDirection, setSortDirection] = useState('desc');
  const [showTop, setShowTop] = useState(0); // 0 = all

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const startStr = format(startDate, 'yyyy-MM-dd');
      const endStr = format(endDate, 'yyyy-MM-dd');
      const response = await fetch(
        apiUrl(`/api/reports/sales-by-customer?start_date=${startStr}&end_date=${endStr}`),
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || 'Failed to fetch sales by customer');
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
      setSortDirection(field === 'name' ? 'asc' : 'desc');
    }
  };

  const filteredAndSorted = useMemo(() => {
    if (!data?.customers) return [];
    let filtered = data.customers;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(c => c.name.toLowerCase().includes(term));
    }
    if (showTop > 0) {
      // First sort by revenue desc, take top N, then apply user sort
      const topN = [...filtered].sort((a, b) => b.total_revenue - a.total_revenue).slice(0, showTop);
      filtered = topN;
    }
    return [...filtered].sort((a, b) => {
      let aVal, bVal;
      switch (sortField) {
        case 'name':
          aVal = a.name;
          bVal = b.name;
          return sortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        case 'total_revenue':
          return sortDirection === 'asc' ? a.total_revenue - b.total_revenue : b.total_revenue - a.total_revenue;
        case 'gross_profit':
          return sortDirection === 'asc' ? a.gross_profit - b.gross_profit : b.gross_profit - a.gross_profit;
        case 'gross_margin_pct':
          return sortDirection === 'asc' ? a.gross_margin_pct - b.gross_margin_pct : b.gross_margin_pct - a.gross_margin_pct;
        case 'invoice_count':
          return sortDirection === 'asc' ? a.invoice_count - b.invoice_count : b.invoice_count - a.invoice_count;
        case 'pct_of_total_revenue':
          return sortDirection === 'asc' ? a.pct_of_total_revenue - b.pct_of_total_revenue : b.pct_of_total_revenue - a.pct_of_total_revenue;
        default:
          return 0;
      }
    });
  }, [data, searchTerm, sortField, sortDirection, showTop]);

  // Top 10 for bar chart
  const barChartData = useMemo(() => {
    if (!data?.customers) return [];
    return [...data.customers]
      .sort((a, b) => b.total_revenue - a.total_revenue)
      .slice(0, 10)
      .map(c => ({
        name: c.name.length > 20 ? c.name.substring(0, 17) + '...' : c.name,
        fullName: c.name,
        revenue: c.total_revenue,
        grossProfit: c.gross_profit,
        pct: c.pct_of_total_revenue,
      }));
  }, [data]);

  // Concentration data for pie chart
  const pieChartData = useMemo(() => {
    if (!data?.customers || data.customers.length === 0) return [];
    const sorted = [...data.customers].sort((a, b) => b.total_revenue - a.total_revenue);
    const top5 = sorted.slice(0, 5);
    const rest = sorted.slice(5);
    const restRevenue = rest.reduce((s, c) => s + c.total_revenue, 0);
    const items = top5.map((c, i) => ({
      name: c.name.length > 20 ? c.name.substring(0, 17) + '...' : c.name,
      fullName: c.name,
      value: c.total_revenue,
      fill: CHART_COLORS[i],
    }));
    if (restRevenue > 0) {
      items.push({
        name: `Others (${rest.length})`,
        fullName: `Others (${rest.length} customers)`,
        value: restRevenue,
        fill: '#d1d5db',
      });
    }
    return items;
  }, [data]);

  // Concentration metrics
  const concentrationMetrics = useMemo(() => {
    if (!data?.customers || data.customers.length === 0) return null;
    const sorted = [...data.customers].sort((a, b) => b.total_revenue - a.total_revenue);
    const total = data.total_revenue;
    let cumulative = 0;
    let top80Count = 0;
    for (const c of sorted) {
      cumulative += c.total_revenue;
      top80Count++;
      if (cumulative >= total * 0.8) break;
    }
    const top10Rev = sorted.slice(0, 10).reduce((s, c) => s + c.total_revenue, 0);
    const top10Pct = total > 0 ? (top10Rev / total * 100) : 0;
    return {
      top80Count,
      top80Pct: total > 0 ? (cumulative / total * 100) : 0,
      top10Pct,
      totalCustomers: sorted.length,
    };
  }, [data]);

  const exportCSV = () => {
    if (!filteredAndSorted.length) return;
    const headers = ['Rank', 'Customer', 'Revenue', 'Cost', 'Gross Profit', 'Margin %', '% of Total Revenue', 'Invoices'];
    const rows = filteredAndSorted.map((c, i) => [
      i + 1,
      `"${c.name}"`,
      c.total_revenue.toFixed(2),
      c.total_cost.toFixed(2),
      c.gross_profit.toFixed(2),
      c.gross_margin_pct.toFixed(1) + '%',
      c.pct_of_total_revenue.toFixed(2) + '%',
      c.invoice_count,
    ]);
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `sales-by-customer-${format(startDate, 'yyyy-MM-dd')}-to-${format(endDate, 'yyyy-MM-dd')}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) return <ArrowUpDown className="h-3 w-3 ml-1 opacity-40" />;
    return sortDirection === 'asc' ? <ArrowUp className="h-3 w-3 ml-1" /> : <ArrowDown className="h-3 w-3 ml-1" />;
  };

  const CustomBarTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
        <p className="font-semibold text-gray-800">{d.fullName}</p>
        <p className="text-blue-600 font-medium mt-1">Revenue: {formatCurrencyDetailed(d.revenue)}</p>
        <p className="text-green-600">Gross Profit: {formatCurrencyDetailed(d.grossProfit)}</p>
        <p className="text-gray-500">{d.pct.toFixed(1)}% of total</p>
      </div>
    );
  };

  const CustomPieTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    const pct = data?.total_revenue > 0 ? (d.value / data.total_revenue * 100) : 0;
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
        <p className="font-semibold text-gray-800">{d.fullName}</p>
        <p className="text-blue-600 font-medium mt-1">{formatCurrency(d.value)}</p>
        <p className="text-gray-500">{pct.toFixed(1)}% of total</p>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Header with date pickers */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">Sales by Customer</h2>
          <p className="text-sm text-gray-500">Stack-ranked customer revenue from InvoiceReg</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
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
          <Button variant="outline" size="sm" onClick={exportCSV} disabled={!data?.customers?.length}>
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
          <span className="ml-3 text-gray-500">Loading customer sales data...</span>
        </div>
      )}

      {/* Content */}
      {!loading && !error && data && (
        <>
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-5">
            <Card className="border-l-4 border-l-blue-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <DollarSign className="h-4 w-4 text-blue-500" />
                  <span className="text-xs font-medium text-muted-foreground">Total Revenue</span>
                </div>
                <div className="text-2xl font-bold">{formatCurrency(data.total_revenue)}</div>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-green-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="h-4 w-4 text-green-500" />
                  <span className="text-xs font-medium text-muted-foreground">Gross Profit</span>
                </div>
                <div className="text-2xl font-bold">{formatCurrency(data.total_gross_profit)}</div>
                <p className="text-xs text-muted-foreground mt-1">{data.overall_margin_pct}% margin</p>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-purple-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <Users className="h-4 w-4 text-purple-500" />
                  <span className="text-xs font-medium text-muted-foreground">Customers</span>
                </div>
                <div className="text-2xl font-bold">{data.customer_count}</div>
                <p className="text-xs text-muted-foreground mt-1">Active in period</p>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-amber-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <BarChart3 className="h-4 w-4 text-amber-500" />
                  <span className="text-xs font-medium text-muted-foreground">Top 10 Concentration</span>
                </div>
                <div className="text-2xl font-bold">{concentrationMetrics?.top10Pct.toFixed(1)}%</div>
                <p className="text-xs text-muted-foreground mt-1">of total revenue</p>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-cyan-500">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center gap-2 mb-1">
                  <Percent className="h-4 w-4 text-cyan-500" />
                  <span className="text-xs font-medium text-muted-foreground">80% Revenue</span>
                </div>
                <div className="text-2xl font-bold">{concentrationMetrics?.top80Count}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  customers of {concentrationMetrics?.totalCustomers}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Charts Row */}
          <div className="grid gap-4 md:grid-cols-2">
            {/* Top 10 Bar Chart */}
            {barChartData.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Top 10 Customers by Revenue</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart data={barChartData} layout="vertical" margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                      <XAxis type="number" tickFormatter={(v) => formatCurrency(v)} fontSize={11} />
                      <YAxis type="category" dataKey="name" width={140} fontSize={11} tick={{ fill: '#6b7280' }} />
                      <Tooltip content={<CustomBarTooltip />} />
                      <Bar dataKey="revenue" radius={[0, 4, 4, 0]}>
                        {barChartData.map((_, index) => (
                          <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}

            {/* Concentration Pie Chart */}
            {pieChartData.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Revenue Concentration</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={320}>
                    <PieChart>
                      <Pie
                        data={pieChartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={110}
                        paddingAngle={2}
                        dataKey="value"
                        label={({ name, percent }) => `${name} (${(percent * 100).toFixed(1)}%)`}
                        labelLine={true}
                        fontSize={10}
                      >
                        {pieChartData.map((entry, index) => (
                          <Cell key={index} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip content={<CustomPieTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Table */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                <CardTitle className="text-base">All Customers</CardTitle>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1">
                    {[0, 10, 25, 50].map(n => (
                      <Button
                        key={n}
                        variant={showTop === n ? 'default' : 'outline'}
                        size="sm"
                        className="h-7 text-xs"
                        onClick={() => setShowTop(n)}
                      >
                        {n === 0 ? 'All' : `Top ${n}`}
                      </Button>
                    ))}
                  </div>
                  <div className="relative w-56">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="Search customer..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-8 h-9 text-sm"
                    />
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50px]">#</TableHead>
                    <TableHead
                      className="cursor-pointer select-none hover:bg-gray-50"
                      onClick={() => handleSort('name')}
                    >
                      <div className="flex items-center">
                        Customer <SortIcon field="name" />
                      </div>
                    </TableHead>
                    <TableHead
                      className="text-right cursor-pointer select-none hover:bg-gray-50"
                      onClick={() => handleSort('total_revenue')}
                    >
                      <div className="flex items-center justify-end">
                        Revenue <SortIcon field="total_revenue" />
                      </div>
                    </TableHead>
                    <TableHead
                      className="text-right cursor-pointer select-none hover:bg-gray-50"
                      onClick={() => handleSort('gross_profit')}
                    >
                      <div className="flex items-center justify-end">
                        Gross Profit <SortIcon field="gross_profit" />
                      </div>
                    </TableHead>
                    <TableHead
                      className="text-right cursor-pointer select-none hover:bg-gray-50"
                      onClick={() => handleSort('gross_margin_pct')}
                    >
                      <div className="flex items-center justify-end">
                        Margin % <SortIcon field="gross_margin_pct" />
                      </div>
                    </TableHead>
                    <TableHead
                      className="text-right cursor-pointer select-none hover:bg-gray-50"
                      onClick={() => handleSort('pct_of_total_revenue')}
                    >
                      <div className="flex items-center justify-end">
                        % of Total <SortIcon field="pct_of_total_revenue" />
                      </div>
                    </TableHead>
                    <TableHead
                      className="text-right cursor-pointer select-none hover:bg-gray-50"
                      onClick={() => handleSort('invoice_count')}
                    >
                      <div className="flex items-center justify-end">
                        Invoices <SortIcon field="invoice_count" />
                      </div>
                    </TableHead>
                    <TableHead className="w-[100px]">Share</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAndSorted.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center text-gray-500 py-8">
                        {searchTerm ? 'No customers match your search' : 'No data available for this period'}
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredAndSorted.map((customer, idx) => (
                      <TableRow key={customer.name} className={`${idx % 2 === 0 ? '' : 'bg-gray-50/50'} ${customer.is_grouped ? 'bg-blue-50/50' : ''}`}>
                        <TableCell className="text-sm text-gray-500 font-mono">{idx + 1}</TableCell>
                        <TableCell className="text-sm font-medium">
                          <div className="flex items-center gap-1.5">
                            {customer.name}
                            {customer.is_grouped && (
                              <>
                                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-100 text-blue-700">
                                  {customer.grouped_customers?.length} combined
                                </span>
                                <TooltipProvider>
                                  <UITooltip delayDuration={0}>
                                    <TooltipTrigger asChild>
                                      <span className="inline-flex items-center">
                                        <Layers className="h-3.5 w-3.5 text-blue-500 cursor-help" />
                                      </span>
                                    </TooltipTrigger>
                                    <TooltipContent side="right" className="max-w-sm">
                                      <p className="font-semibold text-xs mb-1">Combined Accounts:</p>
                                      {customer.grouped_customers?.map((gc) => (
                                        <div key={gc.name} className="text-xs flex justify-between gap-4">
                                          <span className="truncate max-w-[180px]">{gc.name}</span>
                                          <span className="font-mono whitespace-nowrap">{formatCurrencyDetailed(gc.total_revenue)} ({gc.invoice_count} inv)</span>
                                        </div>
                                      ))}
                                    </TooltipContent>
                                  </UITooltip>
                                </TooltipProvider>
                              </>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-right text-sm font-medium">
                          {formatCurrencyDetailed(customer.total_revenue)}
                        </TableCell>
                        <TableCell className={`text-right text-sm ${customer.gross_profit < 0 ? 'text-red-600' : 'text-green-700'}`}>
                          {formatCurrencyDetailed(customer.gross_profit)}
                        </TableCell>
                        <TableCell className={`text-right text-sm ${customer.gross_margin_pct < 20 ? 'text-red-600' : customer.gross_margin_pct < 30 ? 'text-amber-600' : 'text-green-700'}`}>
                          {customer.gross_margin_pct.toFixed(1)}%
                        </TableCell>
                        <TableCell className="text-right text-sm text-gray-600">
                          {customer.pct_of_total_revenue.toFixed(2)}%
                        </TableCell>
                        <TableCell className="text-right text-sm text-gray-600">
                          {customer.invoice_count}
                        </TableCell>
                        <TableCell>
                          <div className="w-full bg-gray-100 rounded-full h-2">
                            <div
                              className="h-2 rounded-full bg-blue-500"
                              style={{
                                width: `${Math.min(customer.pct_of_total_revenue * 5, 100)}%`,
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
                      <TableCell />
                      <TableCell>
                        Total ({filteredAndSorted.length} customers{searchTerm ? ' matching filter' : ''})
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrencyDetailed(filteredAndSorted.reduce((s, c) => s + c.total_revenue, 0))}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrencyDetailed(filteredAndSorted.reduce((s, c) => s + c.gross_profit, 0))}
                      </TableCell>
                      <TableCell className="text-right">
                        {(() => {
                          const rev = filteredAndSorted.reduce((s, c) => s + c.total_revenue, 0);
                          const gp = filteredAndSorted.reduce((s, c) => s + c.gross_profit, 0);
                          return rev > 0 ? (gp / rev * 100).toFixed(1) + '%' : '—';
                        })()}
                      </TableCell>
                      <TableCell className="text-right">
                        {filteredAndSorted.reduce((s, c) => s + c.pct_of_total_revenue, 0).toFixed(1)}%
                      </TableCell>
                      <TableCell className="text-right">
                        {filteredAndSorted.reduce((s, c) => s + c.invoice_count, 0)}
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

export default SalesByCustomer;
