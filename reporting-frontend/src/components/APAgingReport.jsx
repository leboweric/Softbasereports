import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { Download, Search, Calendar as CalendarIcon, RefreshCw } from 'lucide-react';
import { apiUrl } from '@/lib/api';
import { format } from 'date-fns';
import * as XLSX from 'xlsx';

const AGING_BUCKETS = [
  { key: 'Not Due', label: 'Not Due', color: 'green', totalsKey: 'not_due' },
  { key: '0-30', label: '0-30 Days', color: 'blue', totalsKey: '0-30' },
  { key: '31-60', label: '31-60 Days', color: 'yellow', totalsKey: '31-60' },
  { key: '61-90', label: '61-90 Days', color: 'orange', totalsKey: '61-90' },
  { key: 'Over 90', label: 'Over 90 Days', color: 'red', totalsKey: 'over_90' },
  { key: 'No Due Date', label: 'No Due Date', color: 'gray', totalsKey: 'no_due_date' }
];

export default function APAgingReport() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [filteredData, setFilteredData] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBuckets, setSelectedBuckets] = useState(new Set(AGING_BUCKETS.map(b => b.key)));
  const [sortField, setSortField] = useState('VendorName');
  const [sortDirection, setSortDirection] = useState('asc');
  const [asOfDate, setAsOfDate] = useState('');

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

      let url = '/api/reports/departments/accounting/ap-aging';
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
      const search = searchTerm.toLowerCase();
      const matchesSearch = (
        inv.APInvoiceNo?.toString().includes(search) ||
        inv.VendorName?.toLowerCase().includes(search) ||
        inv.VendorNo?.toLowerCase().includes(search)
      );

      const matchesAging = selectedBuckets.has(inv.AgingBucket);

      return matchesSearch && matchesAging;
    });

    filtered.sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];

      if (sortField === 'DaysOverdue' || sortField === 'InvoiceAmount') {
        aVal = parseFloat(aVal) || 0;
        bVal = parseFloat(bVal) || 0;
      } else if (sortField === 'APInvoiceDate' || sortField === 'DueDate') {
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
      setSortDirection(field === 'VendorName' ? 'asc' : 'desc');
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

  const selectOverdue = () => {
    setSelectedBuckets(new Set(['0-30', '31-60', '61-90', 'Over 90']));
  };

  const downloadExcel = () => {
    if (!filteredData.length) return;

    const worksheetData = filteredData.map(inv => ({
      'Invoice #': inv.APInvoiceNo,
      'Vendor #': inv.VendorNo,
      'Vendor Name': inv.VendorName || '',
      'Invoice Date': inv.APInvoiceDate ? new Date(inv.APInvoiceDate).toLocaleDateString() : '',
      'Due Date': inv.DueDate ? new Date(inv.DueDate).toLocaleDateString() : '',
      'Days Overdue': inv.DaysOverdue,
      'Amount': parseFloat(inv.InvoiceAmount || 0),
      'Aging Bucket': inv.AgingBucket
    }));

    const worksheet = XLSX.utils.json_to_sheet(worksheetData);

    const range = XLSX.utils.decode_range(worksheet['!ref']);
    for (let row = 1; row <= range.e.r; row++) {
      const cellAddress = XLSX.utils.encode_cell({ c: 6, r: row });
      if (worksheet[cellAddress]) {
        worksheet[cellAddress].z = '$#,##0.00';
      }
    }

    worksheet['!cols'] = [
      { wch: 12 },
      { wch: 12 },
      { wch: 30 },
      { wch: 12 },
      { wch: 12 },
      { wch: 12 },
      { wch: 15 },
      { wch: 12 }
    ];

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'AP Aging');

    const summaryData = AGING_BUCKETS
      .filter(b => selectedBuckets.has(b.key))
      .map(b => ({
        'Aging Bucket': b.label,
        'Amount': parseFloat(filteredData.filter(i => i.AgingBucket === b.key).reduce((sum, i) => sum + parseFloat(i.InvoiceAmount || 0), 0)),
        'Invoice Count': filteredData.filter(i => i.AgingBucket === b.key).length
      }));

    summaryData.push({
      'Aging Bucket': 'TOTAL',
      'Amount': parseFloat(filteredData.reduce((sum, i) => sum + parseFloat(i.InvoiceAmount || 0), 0)),
      'Invoice Count': filteredData.length
    });

    const summarySheet = XLSX.utils.json_to_sheet(summaryData);

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

    const dateStr = asOfDate || new Date().toISOString().split('T')[0];
    const selectedBucketStr = selectedBuckets.size === AGING_BUCKETS.length ? 'All' :
      Array.from(selectedBuckets).join('_').replace(/\s+/g, '');
    XLSX.writeFile(workbook, `AP_Aging_${dateStr}_${selectedBucketStr}.xlsx`);
  };

  if (loading) return <div className="p-6">Loading AP Aging Report...</div>;
  if (!data) return <div className="p-6">No data available</div>;

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const filteredTotals = AGING_BUCKETS.reduce((acc, b) => {
    acc[b.totalsKey] = filteredData.filter(i => i.AgingBucket === b.key).reduce((sum, i) => sum + parseFloat(i.InvoiceAmount || 0), 0);
    return acc;
  }, { total: filteredData.reduce((sum, i) => sum + parseFloat(i.InvoiceAmount || 0), 0) });

  const getBucketColor = (bucket) => {
    switch (bucket) {
      case 'Not Due': return 'bg-green-100 text-green-800';
      case '0-30': return 'bg-blue-100 text-blue-800';
      case '31-60': return 'bg-yellow-100 text-yellow-800';
      case '61-90': return 'bg-orange-100 text-orange-800';
      case 'Over 90': return 'bg-red-100 text-red-800';
      case 'No Due Date': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCardBorderColor = (bucket, isSelected) => {
    if (!isSelected) return '';
    switch (bucket) {
      case 'Not Due': return 'ring-2 ring-green-500';
      case '0-30': return 'ring-2 ring-blue-500';
      case '31-60': return 'ring-2 ring-yellow-500';
      case '61-90': return 'ring-2 ring-orange-500';
      case 'Over 90': return 'ring-2 ring-red-500';
      case 'No Due Date': return 'ring-2 ring-gray-500';
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
          <h1 className="text-3xl font-bold tracking-tight">AP Aging Report</h1>
          <p className="text-muted-foreground">
            Complete accounts payable aging for bank reporting
            {asOfDate && <span className="ml-2 text-blue-600 font-medium">- As of {formatAsOfDate()}</span>}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-52 justify-start text-left font-normal">
                <CalendarIcon className="mr-2 h-4 w-4" />
                {asOfDate ? format(new Date(asOfDate + 'T00:00:00'), 'MMMM d, yyyy') : 'Current (Today)'}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="end">
              <Calendar
                mode="single"
                selected={asOfDate ? new Date(asOfDate + 'T00:00:00') : undefined}
                onSelect={(date) => {
                  if (date) {
                    setAsOfDate(format(date, 'yyyy-MM-dd'));
                  }
                }}
                disabled={(date) => date > new Date()}
                initialFocus
              />
            </PopoverContent>
          </Popover>
          {asOfDate && (
            <Button variant="ghost" size="sm" onClick={() => setAsOfDate('')} title="Reset to current date">
              <RefreshCw className="h-4 w-4" />
            </Button>
          )}
          <Button onClick={downloadExcel} className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Download Excel
          </Button>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-4 text-sm">
          <span className="text-muted-foreground">Quick Select:</span>
          <Button variant="outline" size="sm" onClick={selectAllBuckets}>All</Button>
          <Button variant="outline" size="sm" onClick={clearAllBuckets}>None</Button>
          <Button variant="outline" size="sm" onClick={selectOverdue}>Overdue Only</Button>
        </div>
        <div className="grid gap-4 md:grid-cols-7">
          {AGING_BUCKETS.map((bucket) => {
            const isSelected = selectedBuckets.has(bucket.key);
            const bucketTotal = data.totals[bucket.totalsKey] || 0;
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
                    <CardTitle className="text-sm font-medium">{bucket.label}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className={`text-xl font-bold ${bucket.color === 'red' ? 'text-red-600' : ''}`}>
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
                    onClick={() => handleSort('APInvoiceNo')}
                  >
                    Invoice# {sortField === 'APInvoiceNo' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-left p-2 cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('VendorName')}
                  >
                    Vendor {sortField === 'VendorName' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-left p-2 cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('APInvoiceDate')}
                  >
                    Invoice Date {sortField === 'APInvoiceDate' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-left p-2 cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('DueDate')}
                  >
                    Due Date {sortField === 'DueDate' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-right p-2 cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('DaysOverdue')}
                  >
                    Days Overdue {sortField === 'DaysOverdue' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="text-right p-2 cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort('InvoiceAmount')}
                  >
                    Amount {sortField === 'InvoiceAmount' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="text-center p-2">Aging</th>
                </tr>
              </thead>
              <tbody>
                {filteredData.map((inv, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="p-2">{inv.APInvoiceNo}</td>
                    <td className="p-2">
                      <div>
                        <div className="font-medium">{inv.VendorName || inv.VendorNo}</div>
                        <div className="text-xs text-muted-foreground">{inv.VendorNo}</div>
                      </div>
                    </td>
                    <td className="p-2">{inv.APInvoiceDate ? new Date(inv.APInvoiceDate).toLocaleDateString() : 'N/A'}</td>
                    <td className="p-2">{inv.DueDate ? new Date(inv.DueDate).toLocaleDateString() : 'N/A'}</td>
                    <td className="text-right p-2">
                      <span className={inv.DaysOverdue > 60 ? 'text-red-600 font-semibold' : ''}>
                        {inv.DaysOverdue !== null ? inv.DaysOverdue : '-'}
                      </span>
                    </td>
                    <td className="text-right p-2">{formatCurrency(inv.InvoiceAmount)}</td>
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
