import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Download, Search } from 'lucide-react';
import { apiUrl } from '@/lib/api';
import * as XLSX from 'xlsx';

export default function AROver90Report() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [filteredData, setFilteredData] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('DaysOld');
  const [sortDirection, setSortDirection] = useState('desc');

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (data && data.invoices) {
      filterAndSortData();
    }
  }, [data, searchTerm, sortField, sortDirection]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Get ALL invoices, not just top 100
      const response = await fetch(apiUrl('/api/reports/departments/accounting/ar-over90-full'), {
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
      return (
        inv.InvoiceNo?.toString().includes(search) ||
        inv.CustomerName?.toLowerCase().includes(search) ||
        inv.CustomerNo?.toLowerCase().includes(search)
      );
    });

    // Sort
    filtered.sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];
      
      if (sortField === 'DaysOld' || sortField === 'NetBalance') {
        aVal = parseFloat(aVal) || 0;
        bVal = parseFloat(bVal) || 0;
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
      setSortDirection('desc');
    }
  };

  const downloadExcel = () => {
    if (!filteredData.length) return;

    // Create worksheet data with proper formatting
    const worksheetData = filteredData.map(inv => ({
      'Invoice #': inv.InvoiceNo,
      'Customer #': inv.CustomerNo,
      'Customer Name': inv.CustomerName || '',
      'Due Date': inv.Due ? new Date(inv.Due).toLocaleDateString() : '',
      'Days Overdue': inv.DaysOld,
      'Balance': parseFloat(inv.NetBalance || 0), // Ensure it's a number for Excel formatting
      'Aging Bucket': inv.DaysOld <= 120 ? '90-120 Days' : '120+ Days'
    }));

    const worksheet = XLSX.utils.json_to_sheet(worksheetData);

    // Apply currency formatting to the Balance column (column F, 0-indexed = 5)
    const range = XLSX.utils.decode_range(worksheet['!ref']);
    for (let row = 1; row <= range.e.r; row++) { // Start from row 1 (skip header)
      const cellAddress = XLSX.utils.encode_cell({ c: 5, r: row }); // Column F (Balance)
      if (worksheet[cellAddress]) {
        worksheet[cellAddress].z = '$#,##0.00'; // Excel currency format
      }
    }

    // Set column widths for better readability
    worksheet['!cols'] = [
      { wch: 12 }, // Invoice #
      { wch: 12 }, // Customer #
      { wch: 25 }, // Customer Name
      { wch: 12 }, // Due Date
      { wch: 12 }, // Days Overdue
      { wch: 15 }, // Balance
      { wch: 15 }  // Aging Bucket
    ];

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'AR Over 90 Days');
    
    // Add summary sheet with proper formatting
    const summaryData = [
      { 'Category': '90-120 Days', 'Amount': parseFloat(data.totals['90-120'] || 0), 'Invoice Count': filteredData.filter(i => i.DaysOld >= 90 && i.DaysOld <= 120).length },
      { 'Category': '120+ Days', 'Amount': parseFloat(data.totals['120+'] || 0), 'Invoice Count': filteredData.filter(i => i.DaysOld > 120).length },
      { 'Category': 'Total Over 90', 'Amount': parseFloat(data.totals.total || 0), 'Invoice Count': filteredData.length }
    ];
    const summarySheet = XLSX.utils.json_to_sheet(summaryData);

    // Apply currency formatting to Amount column in summary (column B, 0-indexed = 1)
    const summaryRange = XLSX.utils.decode_range(summarySheet['!ref']);
    for (let row = 1; row <= summaryRange.e.r; row++) { // Start from row 1 (skip header)
      const cellAddress = XLSX.utils.encode_cell({ c: 1, r: row }); // Column B (Amount)
      if (summarySheet[cellAddress]) {
        summarySheet[cellAddress].z = '$#,##0.00'; // Excel currency format
      }
    }

    // Set column widths for summary sheet
    summarySheet['!cols'] = [
      { wch: 15 }, // Category
      { wch: 15 }, // Amount
      { wch: 15 }  // Invoice Count
    ];

    XLSX.utils.book_append_sheet(workbook, summarySheet, 'Summary');

    XLSX.writeFile(workbook, `AR_Over_90_Days_${new Date().toISOString().split('T')[0]}.xlsx`);
  };

  if (loading) return <div className="p-6">Loading AR Over 90 Days Report...</div>;
  if (!data) return <div className="p-6">No data available</div>;

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AR Over 90 Days Report</h1>
          <p className="text-muted-foreground">Complete list of invoices over 90 days old</p>
        </div>
        <Button onClick={downloadExcel} className="flex items-center gap-2">
          <Download className="h-4 w-4" />
          Download Excel
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">90-120 Days</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(data.totals['90-120'])}</div>
            <p className="text-xs text-muted-foreground">
              {filteredData.filter(i => i.DaysOld >= 90 && i.DaysOld <= 120).length} invoices
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">120+ Days</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(data.totals['120+'])}</div>
            <p className="text-xs text-muted-foreground">
              {filteredData.filter(i => i.DaysOld > 120).length} invoices
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Over 90</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(data.totals.total)}</div>
            <p className="text-xs text-muted-foreground">
              {filteredData.length} invoices
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Oldest Invoice</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {filteredData.length > 0 ? Math.max(...filteredData.map(i => i.DaysOld)) : 0} days
            </div>
            <p className="text-xs text-muted-foreground">
              Most overdue
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filter */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Invoice Details</CardTitle>
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
                  <th className="text-left p-2">Due Date</th>
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
                  <th className="text-center p-2">Aging Bucket</th>
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
                    <td className="p-2">{inv.Due ? new Date(inv.Due).toLocaleDateString() : 'N/A'}</td>
                    <td className="text-right p-2">
                      <span className={inv.DaysOld > 150 ? 'text-red-600 font-semibold' : ''}>
                        {inv.DaysOld}
                      </span>
                    </td>
                    <td className="text-right p-2">{formatCurrency(inv.NetBalance)}</td>
                    <td className="text-center p-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        inv.DaysOld > 120 ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {inv.DaysOld <= 120 ? '90-120' : '120+'}
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