import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Download, Search } from 'lucide-react';
import { apiUrl } from '@/lib/api';
import * as XLSX from 'xlsx';

export default function ARAgingReport() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [filteredData, setFilteredData] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [agingFilter, setAgingFilter] = useState('all');
  const [sortField, setSortField] = useState('CustomerName');
  const [sortDirection, setSortDirection] = useState('asc');

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (data && data.invoices) {
      filterAndSortData();
    }
  }, [data, searchTerm, agingFilter, sortField, sortDirection]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');

      const response = await fetch(apiUrl('/api/reports/departments/accounting/ar-aging'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch data');

      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortData = () => {
    let filtered = data.invoices.filter(inv => {
      // Search filter
      const search = searchTerm.toLowerCase();
      const matchesSearch = (
        inv.InvoiceNo?.toString().includes(search) ||
        inv.CustomerName?.toLowerCase().includes(search) ||
        inv.CustomerNo?.toLowerCase().includes(search)
      );

      // Aging bucket filter
      const matchesAging = agingFilter === 'all' || inv.AgingBucket === agingFilter;

      return matchesSearch && matchesAging;
    });

    // Sort
    filtered.sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];

      if (sortField === 'DaysOld' || sortField === 'NetBalance') {
        aVal = parseFloat(aVal) || 0;
        bVal = parseFloat(bVal) || 0;
      } else if (sortField === 'InvoiceDate' || sortField === 'Due') {
        aVal = aVal ? new Date(aVal).getTime() : 0;
        bVal = bVal ? new Date(bVal).getTime() : 0;
      } else if (typeof aVal === 'string') {
        aVal = (aVal || '').toLowerCase();
        bVal = (bVal || '').toLowerCase();
      }

      if (sortDirection === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    setFilteredData(filtered);
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection(field === 'CustomerName' ? 'asc' : 'desc');
    }
  };

  const downloadExcel = () => {
    if (!filteredData.length) return;

    // Create worksheet data with proper formatting
    const worksheetData = filteredData.map(inv => ({
      'Invoice #': inv.InvoiceNo,
      'Customer #': inv.CustomerNo,
      'Customer Name': inv.CustomerName || '',
      'Invoice Date': inv.InvoiceDate ? new Date(inv.InvoiceDate).toLocaleDateString() : '',
      'Due Date': inv.Due ? new Date(inv.Due).toLocaleDateString() : '',
      'Days Old': inv.DaysOld,
      'Balance': parseFloat(inv.NetBalance || 0),
      'Aging Bucket': inv.AgingBucket
    }));

    const worksheet = XLSX.utils.json_to_sheet(worksheetData);

    // Apply currency formatting to the Balance column (column G, 0-indexed = 6)
    const range = XLSX.utils.decode_range(worksheet['!ref']);
    for (let row = 1; row <= range.e.r; row++) {
      const cellAddress = XLSX.utils.encode_cell({ c: 6, r: row });
      if (worksheet[cellAddress]) {
        worksheet[cellAddress].z = '$#,##0.00';
      }
    }

    // Set column widths for better readability
    worksheet['!cols'] = [
      { wch: 12 }, // Invoice #
      { wch: 12 }, // Customer #
      { wch: 30 }, // Customer Name
      { wch: 12 }, // Invoice Date
      { wch: 12 }, // Due Date
      { wch: 10 }, // Days Old
      { wch: 15 }, // Balance
      { wch: 12 }  // Aging Bucket
    ];

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'AR Aging');

    // Add summary sheet with proper formatting
    const summaryData = [
      { 'Aging Bucket': 'Current', 'Amount': parseFloat(data.totals.current || 0), 'Invoice Count': data.invoices.filter(i => i.AgingBucket === 'Current').length },
      { 'Aging Bucket': '1-30 Days', 'Amount': parseFloat(data.totals['1-30'] || 0), 'Invoice Count': data.invoices.filter(i => i.AgingBucket === '1-30').length },
      { 'Aging Bucket': '31-60 Days', 'Amount': parseFloat(data.totals['31-60'] || 0), 'Invoice Count': data.invoices.filter(i => i.AgingBucket === '31-60').length },
      { 'Aging Bucket': '61-90 Days', 'Amount': parseFloat(data.totals['61-90'] || 0), 'Invoice Count': data.invoices.filter(i => i.AgingBucket === '61-90').length },
      { 'Aging Bucket': '91-120 Days', 'Amount': parseFloat(data.totals['91-120'] || 0), 'Invoice Count': data.invoices.filter(i => i.AgingBucket === '91-120').length },
      { 'Aging Bucket': '120+ Days', 'Amount': parseFloat(data.totals['120+'] || 0), 'Invoice Count': data.invoices.filter(i => i.AgingBucket === '120+').length },
      { 'Aging Bucket': 'TOTAL', 'Amount': parseFloat(data.totals.total || 0), 'Invoice Count': data.invoices.length }
    ];
    const summarySheet = XLSX.utils.json_to_sheet(summaryData);

    // Apply currency formatting to Amount column in summary
    const summaryRange = XLSX.utils.decode_range(summarySheet['!ref']);
    for (let row = 1; row <= summaryRange.e.r; row++) {
      const cellAddress = XLSX.utils.encode_cell({ c: 1, r: row });
      if (summarySheet[cellAddress]) {
        summarySheet[cellAddress].z = '$#,##0.00';
      }
    }

    summarySheet['!cols'] = [
      { wch: 15 },
      { wch: 15 },
      { wch: 15 }
    ];

    XLSX.utils.book_append_sheet(workbook, summarySheet, 'Summary');

    XLSX.writeFile(workbook, `AR_Aging_Report_${new Date().toISOString().split('T')[0]}.xlsx`);
  };

  if (loading) return <div className="p-6">Loading AR Aging Report...</div>;
  if (!data) return <div className="p-6">No data available</div>;

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  // Calculate filtered totals
  const filteredTotals = {
    current: filteredData.filter(i => i.AgingBucket === 'Current').reduce((sum, i) => sum + parseFloat(i.NetBalance || 0), 0),
    '1-30': filteredData.filter(i => i.AgingBucket === '1-30').reduce((sum, i) => sum + parseFloat(i.NetBalance || 0), 0),
    '31-60': filteredData.filter(i => i.AgingBucket === '31-60').reduce((sum, i) => sum + parseFloat(i.NetBalance || 0), 0),
    '61-90': filteredData.filter(i => i.AgingBucket === '61-90').reduce((sum, i) => sum + parseFloat(i.NetBalance || 0), 0),
    '91-120': filteredData.filter(i => i.AgingBucket === '91-120').reduce((sum, i) => sum + parseFloat(i.NetBalance || 0), 0),
    '120+': filteredData.filter(i => i.AgingBucket === '120+').reduce((sum, i) => sum + parseFloat(i.NetBalance || 0), 0),
    total: filteredData.reduce((sum, i) => sum + parseFloat(i.NetBalance || 0), 0)
  };

  const getBucketColor = (bucket) => {
    switch (bucket) {
      case 'Current': return 'bg-green-100 text-green-800';
      case '1-30': return 'bg-blue-100 text-blue-800';
      case '31-60': return 'bg-yellow-100 text-yellow-800';
      case '61-90': return 'bg-orange-100 text-orange-800';
      case '91-120': return 'bg-red-100 text-red-800';
      case '120+': return 'bg-red-200 text-red-900';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AR Aging Report</h1>
          <p className="text-muted-foreground">Complete accounts receivable aging for bank reporting</p>
        </div>
        <Button onClick={downloadExcel} className="flex items-center gap-2">
          <Download className="h-4 w-4" />
          Download Excel
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-7">
        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setAgingFilter(agingFilter === 'Current' ? 'all' : 'Current')}>
          <CardHeader className="pb-2">
            <CardTitle className={`text-sm font-medium ${agingFilter === 'Current' ? 'text-green-600' : ''}`}>Current</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">{formatCurrency(data.totals.current)}</div>
            <p className="text-xs text-muted-foreground">
              {data.invoices.filter(i => i.AgingBucket === 'Current').length} invoices
            </p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setAgingFilter(agingFilter === '1-30' ? 'all' : '1-30')}>
          <CardHeader className="pb-2">
            <CardTitle className={`text-sm font-medium ${agingFilter === '1-30' ? 'text-blue-600' : ''}`}>1-30 Days</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">{formatCurrency(data.totals['1-30'])}</div>
            <p className="text-xs text-muted-foreground">
              {data.invoices.filter(i => i.AgingBucket === '1-30').length} invoices
            </p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setAgingFilter(agingFilter === '31-60' ? 'all' : '31-60')}>
          <CardHeader className="pb-2">
            <CardTitle className={`text-sm font-medium ${agingFilter === '31-60' ? 'text-yellow-600' : ''}`}>31-60 Days</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">{formatCurrency(data.totals['31-60'])}</div>
            <p className="text-xs text-muted-foreground">
              {data.invoices.filter(i => i.AgingBucket === '31-60').length} invoices
            </p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setAgingFilter(agingFilter === '61-90' ? 'all' : '61-90')}>
          <CardHeader className="pb-2">
            <CardTitle className={`text-sm font-medium ${agingFilter === '61-90' ? 'text-orange-600' : ''}`}>61-90 Days</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">{formatCurrency(data.totals['61-90'])}</div>
            <p className="text-xs text-muted-foreground">
              {data.invoices.filter(i => i.AgingBucket === '61-90').length} invoices
            </p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setAgingFilter(agingFilter === '91-120' ? 'all' : '91-120')}>
          <CardHeader className="pb-2">
            <CardTitle className={`text-sm font-medium ${agingFilter === '91-120' ? 'text-red-600' : ''}`}>91-120 Days</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold text-red-600">{formatCurrency(data.totals['91-120'])}</div>
            <p className="text-xs text-muted-foreground">
              {data.invoices.filter(i => i.AgingBucket === '91-120').length} invoices
            </p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setAgingFilter(agingFilter === '120+' ? 'all' : '120+')}>
          <CardHeader className="pb-2">
            <CardTitle className={`text-sm font-medium ${agingFilter === '120+' ? 'text-red-700' : ''}`}>120+ Days</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold text-red-700">{formatCurrency(data.totals['120+'])}</div>
            <p className="text-xs text-muted-foreground">
              {data.invoices.filter(i => i.AgingBucket === '120+').length} invoices
            </p>
          </CardContent>
        </Card>

        <Card className="bg-slate-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total AR</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">{formatCurrency(data.totals.total)}</div>
            <p className="text-xs text-muted-foreground">
              {data.invoices.length} invoices
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <CardTitle>Invoice Details</CardTitle>
            <div className="flex items-center gap-4">
              <Select value={agingFilter} onValueChange={setAgingFilter}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Filter by aging" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Buckets</SelectItem>
                  <SelectItem value="Current">Current</SelectItem>
                  <SelectItem value="1-30">1-30 Days</SelectItem>
                  <SelectItem value="31-60">31-60 Days</SelectItem>
                  <SelectItem value="61-90">61-90 Days</SelectItem>
                  <SelectItem value="91-120">91-120 Days</SelectItem>
                  <SelectItem value="120+">120+ Days</SelectItem>
                </SelectContent>
              </Select>
              <div className="relative w-64">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search invoices..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
          </div>
          {(searchTerm || agingFilter !== 'all') && (
            <div className="text-sm text-muted-foreground mt-2">
              Showing {filteredData.length} of {data.invoices.length} invoices
              {agingFilter !== 'all' && ` (${agingFilter})`}
              {' '}totaling {formatCurrency(filteredTotals.total)}
            </div>
          )}
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th
                    className="text-left p-2 cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('InvoiceNo')}
                  >
                    Invoice# {sortField === 'InvoiceNo' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-left p-2 cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('CustomerName')}
                  >
                    Customer {sortField === 'CustomerName' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-left p-2 cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('InvoiceDate')}
                  >
                    Invoice Date {sortField === 'InvoiceDate' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-left p-2 cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('Due')}
                  >
                    Due Date {sortField === 'Due' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-right p-2 cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('DaysOld')}
                  >
                    Days Old {sortField === 'DaysOld' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-right p-2 cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('NetBalance')}
                  >
                    Balance {sortField === 'NetBalance' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="text-center p-2">Aging</th>
                </tr>
              </thead>
              <tbody>
                {filteredData.map((inv, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="p-2">{inv.InvoiceNo}</td>
                    <td className="p-2">
                      <div>
                        <div className="font-medium">{inv.CustomerName || inv.CustomerNo}</div>
                        <div className="text-xs text-muted-foreground">{inv.CustomerNo}</div>
                      </div>
                    </td>
                    <td className="p-2">{inv.InvoiceDate ? new Date(inv.InvoiceDate).toLocaleDateString() : 'N/A'}</td>
                    <td className="p-2">{inv.Due ? new Date(inv.Due).toLocaleDateString() : 'N/A'}</td>
                    <td className="text-right p-2">
                      <span className={inv.DaysOld > 90 ? 'text-red-600 font-semibold' : ''}>
                        {inv.DaysOld}
                      </span>
                    </td>
                    <td className="text-right p-2">{formatCurrency(inv.NetBalance)}</td>
                    <td className="text-center p-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getBucketColor(inv.AgingBucket)}`}>
                        {inv.AgingBucket}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredData.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No invoices found matching your search
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
