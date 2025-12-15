import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Download, Search, Calendar, RefreshCw } from 'lucide-react';
import { apiUrl } from '@/lib/api';
import * as XLSX from 'xlsx';

const AGING_BUCKETS = [
  { key: 'Current', label: 'Current', color: 'green' },
  { key: '1-30', label: '1-30 Days', color: 'blue' },
  { key: '31-60', label: '31-60 Days', color: 'yellow' },
  { key: '61-90', label: '61-90 Days', color: 'orange' },
  { key: '91-120', label: '91-120 Days', color: 'red' },
  { key: '120+', label: '120+ Days', color: 'darkred' }
];

export default function ARAgingReport() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [filteredData, setFilteredData] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBuckets, setSelectedBuckets] = useState(new Set(AGING_BUCKETS.map(b => b.key))); // All selected by default
  const [sortField, setSortField] = useState('CustomerName');
  const [sortDirection, setSortDirection] = useState('asc');
  const [asOfDate, setAsOfDate] = useState(''); // Empty means current date

  useEffect(() => {
    fetchData();
  }, [asOfDate]);

  useEffect(() => {
    if (data && data.invoices) {
      filterAndSortData();
    }
  }, [data, searchTerm, selectedBuckets, sortField, sortDirection]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      let url = '/api/reports/departments/accounting/ar-aging';
      if (asOfDate) {
        url += `?as_of_date=${asOfDate}`;
      }

      const response = await fetch(apiUrl(url), {
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

      // Aging bucket filter (multi-select)
      const matchesAging = selectedBuckets.has(inv.AgingBucket);

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

  const toggleBucket = (bucketKey) => {
    setSelectedBuckets(prev => {
      const newSet = new Set(prev);
      if (newSet.has(bucketKey)) {
        newSet.delete(bucketKey);
      } else {
        newSet.add(bucketKey);
      }
      return newSet;
    });
  };

  const selectAllBuckets = () => {
    setSelectedBuckets(new Set(AGING_BUCKETS.map(b => b.key)));
  };

  const clearAllBuckets = () => {
    setSelectedBuckets(new Set());
  };

  const selectOver90 = () => {
    setSelectedBuckets(new Set(['91-120', '120+']));
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

    // Add summary sheet - only include selected buckets in filtered view
    const summaryData = AGING_BUCKETS
      .filter(b => selectedBuckets.has(b.key))
      .map(b => ({
        'Aging Bucket': b.label,
        'Amount': parseFloat(filteredData.filter(i => i.AgingBucket === b.key).reduce((sum, i) => sum + parseFloat(i.NetBalance || 0), 0)),
        'Invoice Count': filteredData.filter(i => i.AgingBucket === b.key).length
      }));

    // Add total row
    summaryData.push({
      'Aging Bucket': 'TOTAL',
      'Amount': parseFloat(filteredData.reduce((sum, i) => sum + parseFloat(i.NetBalance || 0), 0)),
      'Invoice Count': filteredData.length
    });

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

    // Generate filename with date
    const dateStr = asOfDate || new Date().toISOString().split('T')[0];
    const selectedBucketStr = selectedBuckets.size === AGING_BUCKETS.length ? 'All' :
      Array.from(selectedBuckets).join('_').replace(/\+/g, 'plus');
    XLSX.writeFile(workbook, `AR_Aging_${dateStr}_${selectedBucketStr}.xlsx`);
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

  const getCardBorderColor = (bucket, isSelected) => {
    if (!isSelected) return '';
    switch (bucket) {
      case 'Current': return 'ring-2 ring-green-500';
      case '1-30': return 'ring-2 ring-blue-500';
      case '31-60': return 'ring-2 ring-yellow-500';
      case '61-90': return 'ring-2 ring-orange-500';
      case '91-120': return 'ring-2 ring-red-500';
      case '120+': return 'ring-2 ring-red-700';
      default: return '';
    }
  };

  const formatAsOfDate = () => {
    if (!data?.as_of_date) return 'Current';
    const date = new Date(data.as_of_date + 'T00:00:00');
    return date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AR Aging Report</h1>
          <p className="text-muted-foreground">
            Complete accounts receivable aging for bank reporting
            {asOfDate && <span className="ml-2 text-blue-600 font-medium">- As of {formatAsOfDate()}</span>}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <Input
              type="date"
              value={asOfDate}
              onChange={(e) => setAsOfDate(e.target.value)}
              className="w-40"
              max={new Date().toISOString().split('T')[0]}
            />
            {asOfDate && (
              <Button variant="ghost" size="sm" onClick={() => setAsOfDate('')} title="Reset to current date">
                <RefreshCw className="h-4 w-4" />
              </Button>
            )}
          </div>
          <Button onClick={downloadExcel} className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Download Excel
          </Button>
        </div>
      </div>

      {/* Summary Cards with Multi-Select */}
      <div className="space-y-3">
        <div className="flex items-center gap-4 text-sm">
          <span className="text-muted-foreground">Quick Select:</span>
          <Button variant="outline" size="sm" onClick={selectAllBuckets}>All</Button>
          <Button variant="outline" size="sm" onClick={clearAllBuckets}>None</Button>
          <Button variant="outline" size="sm" onClick={selectOver90}>Over 90 Days</Button>
        </div>
        <div className="grid gap-4 md:grid-cols-7">
          {AGING_BUCKETS.map((bucket) => {
            const isSelected = selectedBuckets.has(bucket.key);
            const bucketTotal = data.totals[bucket.key.toLowerCase()] || data.totals[bucket.key] || 0;
            const bucketCount = data.invoices.filter(i => i.AgingBucket === bucket.key).length;

            return (
              <Card
                key={bucket.key}
                className={`cursor-pointer hover:shadow-md transition-all ${getCardBorderColor(bucket.key, isSelected)} ${!isSelected ? 'opacity-50' : ''}`}
                onClick={() => toggleBucket(bucket.key)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <Checkbox checked={isSelected} onChange={() => {}} className="pointer-events-none" />
                    <CardTitle className={`text-sm font-medium`}>{bucket.label}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className={`text-xl font-bold ${bucket.color === 'red' || bucket.color === 'darkred' ? 'text-red-600' : ''}`}>
                    {formatCurrency(bucketTotal)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {bucketCount} invoices
                  </p>
                </CardContent>
              </Card>
            );
          })}

          <Card className="bg-slate-50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Selected Total</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xl font-bold">{formatCurrency(filteredTotals.total)}</div>
              <p className="text-xs text-muted-foreground">
                {filteredData.length} invoices
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Filters and Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <CardTitle>Invoice Details</CardTitle>
            <div className="flex items-center gap-4">
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
          <div className="text-sm text-muted-foreground mt-2">
            Showing {filteredData.length} of {data.invoices.length} invoices
            {selectedBuckets.size < AGING_BUCKETS.length && ` (${Array.from(selectedBuckets).join(', ')})`}
            {' '}totaling {formatCurrency(filteredTotals.total)}
          </div>
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
                No invoices found matching your criteria
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
