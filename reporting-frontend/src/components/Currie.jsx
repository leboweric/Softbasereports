import React, { useState, useEffect } from 'react';
import { FileSpreadsheet, Download, Calendar, RefreshCw } from 'lucide-react';
import axios from 'axios';

const Currie = () => {
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [data, setData] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [expenses, setExpenses] = useState(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('sales'); // 'sales', 'expenses', 'balance'

  // Initialize with current quarter
  useEffect(() => {
    const now = new Date();
    const currentMonth = now.getMonth(); // 0-11
    const currentYear = now.getFullYear();
    
    // Determine calendar year quarter (January start)
    let quarter, calendarYear;
    if (currentMonth >= 0 && currentMonth <= 2) { // Jan-Mar = Q1
      quarter = 1;
      calendarYear = currentYear;
    } else if (currentMonth >= 3 && currentMonth <= 5) { // Apr-Jun = Q2
      quarter = 2;
      calendarYear = currentYear;
    } else if (currentMonth >= 6 && currentMonth <= 8) { // Jul-Sep = Q3
      quarter = 3;
      calendarYear = currentYear;
    } else { // Oct-Dec = Q4
      quarter = 4;
      calendarYear = currentYear;
    }
    
    setQuarter(quarter, calendarYear);
  }, []);

  const setQuarter = (quarter, calendarYear) => {
    let start, end;
    
    switch(quarter) {
      case 1: // Q1: Jan-Mar
        start = `${calendarYear}-01-01`;
        end = `${calendarYear}-03-31`;
        break;
      case 2: // Q2: Apr-Jun
        start = `${calendarYear}-04-01`;
        end = `${calendarYear}-06-30`;
        break;
      case 3: // Q3: Jul-Sep
        start = `${calendarYear}-07-01`;
        end = `${calendarYear}-09-30`;
        break;
      case 4: // Q4: Oct-Dec
        start = `${calendarYear}-10-01`;
        end = `${calendarYear}-12-31`;
        break;
    }
    
    setStartDate(start);
    setEndDate(end);
  };

  const fetchData = async () => {
    if (!startDate || !endDate) {
      setError('Please select a date range');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      
      // Fetch sales/COGS data
      const salesResponse = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/currie/sales-cogs-gp`,
        {
          params: { start_date: startDate, end_date: endDate },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setData(salesResponse.data);
      
      // Fetch metrics data
      const metricsResponse = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/currie/metrics`,
        {
          params: { start_date: startDate, end_date: endDate },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setMetrics(metricsResponse.data.metrics);
      
      // Fetch expenses data
      const expensesResponse = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/currie/expenses`,
        {
          params: { start_date: startDate, end_date: endDate },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setExpenses(expensesResponse.data);
    } catch (err) {
      console.error('Error fetching Currie data:', err);
      setError(err.response?.data?.error || 'Failed to load Currie data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (startDate && endDate) {
      fetchData();
    }
  }, [startDate, endDate]);

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (sales, cogs) => {
    if (!sales || sales === 0) return '0.0%';
    const gp = ((sales - cogs) / sales) * 100;
    return `${gp.toFixed(1)}%`;
  };

  const handleCellEdit = (category, subcategory, field, value) => {
    const numValue = parseFloat(value.replace(/[^0-9.-]/g, '')) || 0;
    setData(prevData => {
      const newData = { ...prevData };
      if (subcategory) {
        newData[category][subcategory][field] = numValue;
        newData[category][subcategory].gross_profit = 
          newData[category][subcategory].sales - newData[category][subcategory].cogs;
      } else {
        newData[category][field] = numValue;
        newData[category].gross_profit = newData[category].sales - newData[category].cogs;
      }
      return newData;
    });
  };

  const exportToExcel = async () => {
    if (!startDate || !endDate) {
      alert('Please select a date range first');
      return;
    }

    setExporting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/currie/export-excel`,
        {
          params: { start_date: startDate, end_date: endDate },
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Currie_Financial_Model_${startDate}_to_${endDate}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error exporting Excel:', err);
      alert('Failed to export Excel file. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-3 text-lg">Loading Currie data...</span>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <FileSpreadsheet className="w-8 h-8 text-blue-600 mr-3" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Currie Financial Model</h1>
              <p className="text-sm text-gray-600">Quarterly Benchmarking Report</p>
            </div>
          </div>
          <button
            onClick={exportToExcel}
            disabled={exporting}
            className={`flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all ${
              exporting ? 'opacity-75 cursor-not-allowed' : ''
            }`}
          >
            <Download className={`w-4 h-4 mr-2 ${exporting ? 'animate-bounce' : ''}`} />
            {exporting ? 'Generating Excel...' : 'Export to Excel'}
          </button>
        </div>
      </div>

      {/* Date Range Selector */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex items-center space-x-4">
          <Calendar className="w-5 h-5 text-gray-500" />
          <div className="flex items-center space-x-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="border border-gray-300 rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="border border-gray-300 rounded px-3 py-2"
              />
            </div>
            <div className="flex space-x-2 pt-6">
              <button
                onClick={() => setQuarter(1, 2025)}
                disabled={loading}
                className={`px-3 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm transition-all ${
                  loading ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                Q1 2025
              </button>
              <button
                onClick={() => setQuarter(2, 2025)}
                disabled={loading}
                className={`px-3 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm transition-all ${
                  loading ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                Q2 2025
              </button>
              <button
                onClick={() => setQuarter(3, 2025)}
                disabled={loading}
                className={`px-3 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm transition-all ${
                  loading ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                Q3 2025
              </button>
              <button
                onClick={() => setQuarter(4, 2025)}
                disabled={loading}
                className={`px-3 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm transition-all ${
                  loading ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                Q4 2025
              </button>
            </div>
            <button
              onClick={fetchData}
              disabled={loading}
              className={`px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center mt-6 transition-all ${
                loading ? 'opacity-75 cursor-not-allowed' : ''
              }`}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {/* Tab Navigation */}
      {data && (
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('sales')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'sales'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Sales, COGS & GP
              </button>
              <button
                onClick={() => setActiveTab('expenses')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'expenses'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Expenses & Metrics
              </button>
              <button
                onClick={() => setActiveTab('balance')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'balance'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Balance Sheet
              </button>
            </nav>
          </div>
        </div>
      )}

      {data && activeTab === 'sales' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {/* Dealership Info */}
          <div className="bg-blue-50 border-b border-blue-200 p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="font-semibold">Dealership:</span> {data.dealership_info.name}
              </div>
              <div>
                <span className="font-semibold">Locations:</span> {data.dealership_info.num_locations}
              </div>
              <div>
                <span className="font-semibold">Months:</span> {data.dealership_info.num_months}
              </div>
              <div>
                <span className="font-semibold">Submitted By:</span> {data.dealership_info.submitted_by}
              </div>
            </div>
          </div>

          {/* Sales, COGS, GP Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-blue-600 text-white">
                  <th className="px-4 py-3 text-left font-semibold">Category</th>
                  <th className="px-4 py-3 text-right font-semibold">Sales</th>
                  <th className="px-4 py-3 text-right font-semibold">COGS</th>
                  <th className="px-4 py-3 text-right font-semibold">Gross Profit</th>
                  <th className="px-4 py-3 text-right font-semibold">GP %</th>
                </tr>
              </thead>
              <tbody>
                {/* NEW EQUIPMENT SECTION */}
                <tr className="bg-gray-100 font-semibold">
                  <td colSpan="5" className="px-4 py-2">NEW EQUIPMENT SALES</td>
                </tr>
                
                <DataRow 
                  label="New Lift Truck Equipment - Primary Brand (Linde)"
                  data={data.new_equipment.new_lift_truck_primary}
                  onEdit={(field, value) => handleCellEdit('new_equipment', 'new_lift_truck_primary', field, value)}
                />
                <DataRow 
                  label="New Lift Truck Equipment - Other Brands"
                  data={data.new_equipment.new_lift_truck_other}
                  onEdit={(field, value) => handleCellEdit('new_equipment', 'new_lift_truck_other', field, value)}
                />
                <DataRow 
                  label="New Allied Equipment"
                  data={data.new_equipment.new_allied}
                  onEdit={(field, value) => handleCellEdit('new_equipment', 'new_allied', field, value)}
                />
                <DataRow 
                  label="Other New Equipment"
                  data={data.new_equipment.other_new_equipment}
                  onEdit={(field, value) => handleCellEdit('new_equipment', 'other_new_equipment', field, value)}
                />
                
                <SubtotalRow label="TOTAL NEW EQUIPMENT" data={data.totals.total_new_equipment} />
                
                <DataRow 
                  label="Operator Training"
                  data={data.new_equipment.operator_training}
                  onEdit={(field, value) => handleCellEdit('new_equipment', 'operator_training', field, value)}
                />
                <DataRow 
                  label="Used Equipment"
                  data={data.new_equipment.used_equipment}
                  onEdit={(field, value) => handleCellEdit('new_equipment', 'used_equipment', field, value)}
                />
                <DataRow 
                  label="E-Commerce"
                  data={data.new_equipment.ecommerce}
                  onEdit={(field, value) => handleCellEdit('new_equipment', 'ecommerce', field, value)}
                />
                <DataRow 
                  label="Systems"
                  data={data.new_equipment.systems}
                  onEdit={(field, value) => handleCellEdit('new_equipment', 'systems', field, value)}
                />
                <DataRow 
                  label="Batteries"
                  data={data.new_equipment.batteries}
                  onEdit={(field, value) => handleCellEdit('new_equipment', 'batteries', field, value)}
                />
                
                <SubtotalRow label="TOTAL SALES DEPT." data={data.totals.total_sales_dept} />

                {/* RENTAL SECTION */}
                <tr className="bg-gray-100 font-semibold">
                  <td colSpan="5" className="px-4 py-2">RENTAL DEPARTMENT</td>
                </tr>
                
                <DataRow 
                  label="Rental Revenue"
                  data={data.rental}
                  onEdit={(field, value) => handleCellEdit('rental', null, field, value)}
                />

                {/* SERVICE SECTION */}
                <tr className="bg-gray-100 font-semibold">
                  <td colSpan="5" className="px-4 py-2">SERVICE DEPARTMENT</td>
                </tr>
                
                <DataRow 
                  label="Customer Labor"
                  data={data.service.customer_labor}
                  onEdit={(field, value) => handleCellEdit('service', 'customer_labor', field, value)}
                />
                <DataRow 
                  label="Internal Labor"
                  data={data.service.internal_labor}
                  onEdit={(field, value) => handleCellEdit('service', 'internal_labor', field, value)}
                />
                <DataRow 
                  label="Warranty Labor"
                  data={data.service.warranty_labor}
                  onEdit={(field, value) => handleCellEdit('service', 'warranty_labor', field, value)}
                />
                <DataRow 
                  label="Sublet Sales"
                  data={data.service.sublet}
                  onEdit={(field, value) => handleCellEdit('service', 'sublet', field, value)}
                />
                <DataRow 
                  label="Other Service Sales"
                  data={data.service.other}
                  onEdit={(field, value) => handleCellEdit('service', 'other', field, value)}
                />
                
                <SubtotalRow label="TOTAL SERVICE" data={data.totals.total_service} />

                {/* PARTS SECTION */}
                <tr className="bg-gray-100 font-semibold">
                  <td colSpan="5" className="px-4 py-2">PARTS DEPARTMENT</td>
                </tr>
                
                <DataRow 
                  label="Primary Brand Counter Parts Sales"
                  data={data.parts.counter_primary}
                  onEdit={(field, value) => handleCellEdit('parts', 'counter_primary', field, value)}
                />
                <DataRow 
                  label="Other Brand Counter Parts"
                  data={data.parts.counter_other}
                  onEdit={(field, value) => handleCellEdit('parts', 'counter_other', field, value)}
                />
                <DataRow 
                  label="Primary Brand Repair Order Parts"
                  data={data.parts.ro_primary}
                  onEdit={(field, value) => handleCellEdit('parts', 'ro_primary', field, value)}
                />
                <DataRow 
                  label="Other Brand Repair Order Parts"
                  data={data.parts.ro_other}
                  onEdit={(field, value) => handleCellEdit('parts', 'ro_other', field, value)}
                />
                <DataRow 
                  label="Internal Parts Sales"
                  data={data.parts.internal}
                  onEdit={(field, value) => handleCellEdit('parts', 'internal', field, value)}
                />
                <DataRow 
                  label="Warranty Parts Sales"
                  data={data.parts.warranty}
                  onEdit={(field, value) => handleCellEdit('parts', 'warranty', field, value)}
                />
                <DataRow 
                  label="E-Commerce Parts Sales"
                  data={data.parts.ecommerce}
                  onEdit={(field, value) => handleCellEdit('parts', 'ecommerce', field, value)}
                />
                
                <SubtotalRow label="TOTAL PARTS" data={data.totals.total_parts} />

                {/* TRUCKING SECTION */}
                <tr className="bg-gray-100 font-semibold">
                  <td colSpan="5" className="px-4 py-2">TRUCKING DEPARTMENT</td>
                </tr>
                
                <DataRow 
                  label="Trucking"
                  data={data.trucking}
                  onEdit={(field, value) => handleCellEdit('trucking', null, field, value)}
                />

                {/* COMPANY TOTALS AND BOTTOM SUMMARY */}
                <SubtotalRow label="TOTAL AFTERMARKET SALES, COGS & GP" data={data.totals.total_aftermarket} />
                <SubtotalRow label="TOTAL NET SALES & GP" data={data.totals.total_net_sales_gp} />
                
                {/* Bottom Summary Section */}
                <tr className="border-t-2 border-gray-400">
                  <td className="px-4 py-2 font-semibold">Total Company Expenses</td>
                  <td className="px-4 py-2 text-right" colSpan="4">{formatCurrency(data.expenses?.grand_total || 0)}</td>
                </tr>
                <tr>
                  <td className="px-4 py-2">Other Income (Expenses)</td>
                  <td className="px-4 py-2 text-right" colSpan="4">{formatCurrency(data.other_income || 0)}</td>
                </tr>
                <tr>
                  <td className="px-4 py-2">Interest (Expense)</td>
                  <td className="px-4 py-2 text-right" colSpan="4">{formatCurrency(data.interest_expense || 0)}</td>
                </tr>
                <tr className="bg-gray-200 font-semibold">
                  <td className="px-4 py-2">Total operating profit</td>
                  <td className="px-4 py-2 text-right" colSpan="4">{formatCurrency(data.total_operating_profit || 0)}</td>
                </tr>
                <tr>
                  <td className="px-4 py-2">F & I Income</td>
                  <td className="px-4 py-2 text-right" colSpan="4">{formatCurrency(data.fi_income || 0)}</td>
                </tr>
                <tr className="bg-blue-600 text-white font-bold border-t-4 border-blue-900">
                  <td className="px-4 py-3">Pre-Tax Income</td>
                  <td className="px-4 py-3 text-right" colSpan="4">{formatCurrency(data.pre_tax_income || 0)}</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Summary */}
          <div className="bg-gray-50 border-t border-gray-200 p-4">
            <div className="text-sm text-gray-700">
              <span className="font-semibold">Average Monthly Sales & GP:</span> {formatCurrency(data.totals.avg_monthly_sales_gp)}
            </div>
          </div>
        </div>
      )}

      {/* Expenses & Metrics Tab */}
      {data && activeTab === 'expenses' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {/* Dealership Info */}
          <div className="bg-blue-50 border-b border-blue-200 p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="font-semibold">Dealership:</span> {data.dealership_info.name}
              </div>
              <div>
                <span className="font-semibold">Locations:</span> {data.dealership_info.num_locations}
              </div>
              <div>
                <span className="font-semibold">Months:</span> {data.dealership_info.num_months}
              </div>
              <div>
                <span className="font-semibold">Submitted By:</span> {data.dealership_info.submitted_by}
              </div>
            </div>
          </div>

          {/* Department Expense Breakdown */}
          <div className="p-6">
            <h2 className="text-xl font-bold mb-4">Expense Detail by Department</h2>
            
            {data.department_expenses && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="bg-blue-600 text-white">
                      <th className="px-4 py-3 text-left font-semibold">Expense Category</th>
                      <th className="px-4 py-3 text-right font-semibold">New</th>
                      <th className="px-4 py-3 text-right font-semibold">Used</th>
                      <th className="px-4 py-3 text-right font-semibold">Total Sales Dept</th>
                      <th className="px-4 py-3 text-right font-semibold">Parts Dept</th>
                      <th className="px-4 py-3 text-right font-semibold">Service Dept</th>
                      <th className="px-4 py-3 text-right font-semibold">Short Term Rental</th>
                      <th className="px-4 py-3 text-right font-semibold">Long Term Rental</th>
                      <th className="px-4 py-3 text-right font-semibold">Trucking</th>
                      <th className="px-4 py-3 text-right font-semibold">G&A Dept</th>
                      <th className="px-4 py-3 text-right font-semibold">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {/* Personnel */}
                    <tr className="border-b border-gray-200">
                      <td className="px-4 py-2 font-medium">Personnel</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.personnel.new)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.personnel.used)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.personnel.total_sales_dept)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.personnel.parts)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.personnel.service)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.personnel.rental)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(0)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.personnel.trucking)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.personnel.ga)}</td>
                      <td className="px-4 py-2 text-right font-bold">{formatCurrency(data.department_expenses.personnel.total)}</td>
                    </tr>
                    {/* Operating */}
                    <tr className="border-b border-gray-200">
                      <td className="px-4 py-2 font-medium">Operating</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.operating.new)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.operating.used)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.operating.total_sales_dept)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.operating.parts)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.operating.service)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.operating.rental)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(0)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.operating.trucking)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.operating.ga)}</td>
                      <td className="px-4 py-2 text-right font-bold">{formatCurrency(data.department_expenses.operating.total)}</td>
                    </tr>
                    {/* Occupancy */}
                    <tr className="border-b border-gray-200">
                      <td className="px-4 py-2 font-medium">Occupancy</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.occupancy.new)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.occupancy.used)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.occupancy.total_sales_dept)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.occupancy.parts)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.occupancy.service)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.occupancy.rental)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(0)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.occupancy.trucking)}</td>
                      <td className="px-4 py-2 text-right">{formatCurrency(data.department_expenses.occupancy.ga)}</td>
                      <td className="px-4 py-2 text-right font-bold">{formatCurrency(data.department_expenses.occupancy.total)}</td>
                    </tr>
                    {/* Total */}
                    <tr className="bg-gray-900 text-white font-bold">
                      <td className="px-4 py-3">Total</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(data.department_expenses.total.new)}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(data.department_expenses.total.used)}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(data.department_expenses.total.total_sales_dept)}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(data.department_expenses.total.parts)}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(data.department_expenses.total.service)}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(data.department_expenses.total.rental)}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(0)}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(data.department_expenses.total.trucking)}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(data.department_expenses.total.ga)}</td>
                      <td className="px-4 py-3 text-right">{formatCurrency(data.department_expenses.total.total)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Personnel Count Section */}
          <div className="p-6 border-t border-gray-200">
            <h2 className="text-xl font-bold mb-4">Personnel Count</h2>
            
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-blue-600 text-white">
                    <th className="px-4 py-3 text-left font-semibold">Role</th>
                    <th className="px-4 py-3 text-center font-semibold">New</th>
                    <th className="px-4 py-3 text-center font-semibold">Used</th>
                    <th className="px-4 py-3 text-center font-semibold">Systems</th>
                    <th className="px-4 py-3 text-center font-semibold">Total Sales Dept</th>
                    <th className="px-4 py-3 text-center font-semibold">Parts Dept</th>
                    <th className="px-4 py-3 text-center font-semibold">Service Dept</th>
                    <th className="px-4 py-3 text-center font-semibold">Short Term Rental</th>
                    <th className="px-4 py-3 text-center font-semibold">Long Term Rental</th>
                    <th className="px-4 py-3 text-center font-semibold">Trucking</th>
                    <th className="px-4 py-3 text-center font-semibold">G&A Dept</th>
                    <th className="px-4 py-3 text-center font-semibold">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Managers */}
                  <tr className="border-b border-gray-200">
                    <td className="px-4 py-2 font-medium">Managers</td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="1.0" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="0.5" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="0.5" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="1.5" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="1.0" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="0.0" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="0.0" step="0.5" /></td>
                    <td className="px-2 py-2 text-center font-bold bg-gray-100">4.5</td>
                  </tr>
                  {/* Sales People */}
                  <tr className="border-b border-gray-200">
                    <td className="px-4 py-2 font-medium">Sales People</td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="3.5" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="0.5" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="4.0" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2 text-center font-bold bg-gray-100">4.0</td>
                  </tr>
                  {/* Technicians / Drivers */}
                  <tr className="border-b border-gray-200">
                    <td className="px-4 py-2 font-medium">Technicians / Drivers</td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="2.0" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="20.0" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2 text-center font-bold bg-gray-100">22.0</td>
                  </tr>
                  {/* Project Engineers */}
                  <tr className="border-b border-gray-200">
                    <td className="px-4 py-2 font-medium">Project Engineers</td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="0.0" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2 text-center font-bold bg-gray-100">0.0</td>
                  </tr>
                  {/* Other */}
                  <tr className="border-b border-gray-200">
                    <td className="px-4 py-2 font-medium">Other</td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="0.0" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="0.0" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="3.0" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="2.5" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="1.0" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="0.0" step="0.5" /></td>
                    <td className="px-2 py-2"><input type="number" className="w-full text-center border rounded px-2 py-1" defaultValue="1.5" step="0.5" /></td>
                    <td className="px-2 py-2 text-center font-bold bg-gray-100">8.0</td>
                  </tr>
                  {/* Total */}
                  <tr className="bg-gray-900 text-white font-bold">
                    <td className="px-4 py-3">Total</td>
                    <td className="px-2 py-3 text-center">4.5</td>
                    <td className="px-2 py-3 text-center">0.5</td>
                    <td className="px-2 py-3 text-center">0.0</td>
                    <td className="px-2 py-3 text-center">4.0</td>
                    <td className="px-2 py-3 text-center">5.5</td>
                    <td className="px-2 py-3 text-center">21.5</td>
                    <td className="px-2 py-3 text-center">1.0</td>
                    <td className="px-2 py-3 text-center">0.0</td>
                    <td className="px-2 py-3 text-center">0.0</td>
                    <td className="px-2 py-3 text-center">1.5</td>
                    <td className="px-2 py-3 text-center">38.5</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="text-sm text-gray-600 mt-2 italic">*If you are unable to break out New, Used and Systems Personnel counts, please enter all amounts in the New Column</p>
          </div>

          {/* Additional Information Section */}
          <div className="p-6 border-t border-gray-200">
            <h2 className="text-xl font-bold mb-4">Additional Information (Editable)</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {/* Marketshare Information */}
                  <div className="bg-gray-50 border rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">Marketshare Information</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Sold Units</label>
                        <input type="number" className="w-full border rounded px-3 py-2" placeholder="0" />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Lost Units</label>
                        <input type="number" className="w-full border rounded px-3 py-2" placeholder="0" />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Size of Market</label>
                        <input type="number" className="w-full border rounded px-3 py-2" placeholder="0" />
                      </div>
                    </div>
                  </div>
                  
                  {/* Technician Productivity */}
                  <div className="bg-gray-50 border rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">Technician Productivity</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1"># of Units Under Maintenance Contract</label>
                        <input type="number" className="w-full border rounded px-3 py-2" placeholder="0" />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Customer Labor Rate ($)</label>
                        <input type="number" step="0.01" className="w-full border rounded px-3 py-2" placeholder="0.00" />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Avg. Hourly Tech Pay Rate ($)</label>
                        <input type="number" step="0.01" className="w-full border rounded px-3 py-2" placeholder="0.00" />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Total Hours Billed</label>
                        <input type="number" step="0.1" className="w-full border rounded px-3 py-2" placeholder="0.0" />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Productive Hours</label>
                        <input type="number" step="0.1" className="w-full border rounded px-3 py-2" placeholder="0.0" />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Non-Productive Hours</label>
                        <input type="number" step="0.1" className="w-full border rounded px-3 py-2" placeholder="0.0" />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Total Hours Paid</label>
                        <input type="number" step="0.1" className="w-full border rounded px-3 py-2" placeholder="0.0" />
                      </div>
                    </div>
                  </div>
                  
                  {/* Inventory Aging */}
                  <div className="bg-gray-50 border rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">Inventory Aging (% over 12 months)</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">New Inventory Aging (%)</label>
                        <input type="number" step="0.1" className="w-full border rounded px-3 py-2" placeholder="0.0" />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Used Inventory Aging (%)</label>
                        <input type="number" step="0.1" className="w-full border rounded px-3 py-2" placeholder="0.0" />
                      </div>
                    </div>
                  </div>
                  
                  {/* Additional Technician Productivity */}
                  <div className="bg-gray-50 border rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">Additional Technician Productivity</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">PM Completion Rate (%)</label>
                        <input type="number" step="0.1" className="w-full border rounded px-3 py-2" placeholder="0.0" />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">First Call Completion Rate (%)</label>
                        <input type="number" step="0.1" className="w-full border rounded px-3 py-2" placeholder="0.0" />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Average Response Time (hours)</label>
                        <input type="number" step="0.1" className="w-full border rounded px-3 py-2" placeholder="0.0" />
                      </div>
                    </div>
                  </div>
                  
                  {/* Marketing */}
                  <div className="bg-gray-50 border rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">Marketing</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Marketing Expense ($)</label>
                        <input type="number" step="0.01" className="w-full border rounded px-3 py-2" placeholder="0.00" />
                      </div>
                    </div>
                  </div>
                  
                  {/* Service Department */}
                  <div className="bg-gray-50 border rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">Service Department</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Service Calls per Day</label>
                        <input type="number" step="0.1" className="w-full border rounded px-3 py-2" placeholder="0.0" />
                      </div>
                    </div>
                  </div>
                </div>
            </div>
          </div>

          {/* Miscellaneous Information Section */}
          {metrics && (
            <div className="p-6 border-t border-gray-200">
              <h2 className="text-xl font-bold mb-4">Miscellaneous Information</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Accounts Receivable Aging */}
                <div className="bg-white border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-3">Accounts Receivable Aging</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Current (0-30):</span>
                      <span className="font-medium">{formatCurrency(metrics.ar_aging?.current || 0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">31-60 days:</span>
                      <span className="font-medium">{formatCurrency(metrics.ar_aging?.days_31_60 || 0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">61-90 days:</span>
                      <span className="font-medium">{formatCurrency(metrics.ar_aging?.days_61_90 || 0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">91+ days:</span>
                      <span className="font-medium text-red-600">{formatCurrency(metrics.ar_aging?.days_91_plus || 0)}</span>
                    </div>
                    <div className="flex justify-between pt-2 border-t">
                      <span className="font-semibold">Total AR:</span>
                      <span className="font-semibold">{formatCurrency(metrics.ar_aging?.total || 0)}</span>
                    </div>
                  </div>
                </div>
                
                {/* Service Metrics */}
                <div className="bg-white border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-3">Service Metrics</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Service Calls/Day:</span>
                      <span className="font-medium">{metrics.service_calls_per_day?.calls_per_day?.toFixed(1) || '0.0'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Calls:</span>
                      <span className="font-medium">{metrics.service_calls_per_day?.total_service_calls || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Active Technicians:</span>
                      <span className="font-medium">{metrics.technician_count?.active_technicians || 0}</span>
                    </div>
                  </div>
                </div>
                
                {/* Labor Metrics */}
                <div className="bg-white border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-3">Labor Productivity</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Billed Hours:</span>
                      <span className="font-medium">{metrics.labor_metrics?.total_billed_hours?.toFixed(1) || '0.0'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Avg Labor Rate:</span>
                      <span className="font-medium">{formatCurrency(metrics.labor_metrics?.average_labor_rate || 0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Labor Value:</span>
                      <span className="font-medium">{formatCurrency(metrics.labor_metrics?.total_labor_value || 0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">WOs with Labor:</span>
                      <span className="font-medium">{metrics.labor_metrics?.work_orders_with_labor || 0}</span>
                    </div>
                  </div>
                </div>
                
                {/* Parts Inventory Metrics */}
                <div className="bg-white border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-3">Parts Inventory</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Fill Rate:</span>
                      <span className="font-medium text-green-600">{metrics.parts_inventory?.fill_rate?.toFixed(1) || '0.0'}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Inventory Turnover:</span>
                      <span className="font-medium">{metrics.parts_inventory?.inventory_turnover?.toFixed(2) || '0.00'}x</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Inventory Value:</span>
                      <span className="font-medium">{formatCurrency(metrics.parts_inventory?.inventory_value || 0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Obsolete Parts:</span>
                      <span className="font-medium text-red-600">{metrics.parts_inventory?.aging?.obsolete_count || 0}</span>
                    </div>
                  </div>
                </div>
                
                {/* Absorption Rate */}
                <div className="bg-white border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-3">Absorption Rate</h3>
                  <div className="text-center">
                    <div className="text-4xl font-bold text-green-600">
                      {metrics.absorption_rate?.total_absorption?.toFixed(1) || '0.0'}%
                    </div>
                  </div>
                </div>
              </div>
          )}
        </div>
      )}

      {/* Balance Sheet Tab - Reorganized to match Excel layout */}
      {data && activeTab === 'balance' && data.balance_sheet && (() => {
        // Calculate summarized line items to match Excel structure
        const bs = data.balance_sheet;
        
        // Helper function to sum accounts by description pattern
        const sumByPattern = (accounts, patterns) => {
          return accounts.reduce((sum, acc) => {
            const desc = acc.description.toUpperCase();
            if (patterns.some(pattern => desc.includes(pattern))) {
              return sum + acc.balance;
            }
            return sum;
          }, 0);
        };
        
        // ASSETS calculations
        const cash = bs.assets.current_assets.cash.reduce((sum, acc) => sum + acc.balance, 0);
        // Match backend: All AR goes to Trade AR, All Other AR is 0
        const tradeAR = bs.assets.current_assets.accounts_receivable.reduce((sum, acc) => sum + acc.balance, 0);
        const allOtherAR = 0;
        
        // Inventory breakdown
        const inventory = bs.assets.current_assets.inventory;
        const newEquipPrimary = sumByPattern(inventory, ['NEW TRUCK']);
        const newEquipOther = 0; // Placeholder
        const newAllied = sumByPattern(inventory, ['NEW ALLIED']);
        const otherNewEquip = 0; // Placeholder
        const usedEquip = sumByPattern(inventory, ['USED TRUCK']);
        const partsInv = sumByPattern(inventory, ['PARTS']) - sumByPattern(inventory, ['MISC']);
        const batteryInv = sumByPattern(inventory, ['BATTRY', 'BATTERY', 'CHARGER']);
        // WIP is separate from inventory in the Excel structure
        const wip = sumByPattern(inventory, ['WORK', 'PROCESS']);
        // Other Inventory = everything else EXCEPT WIP (WIP is shown separately)
        const otherInv = inventory.reduce((sum, acc) => sum + acc.balance, 0) - 
          (newEquipPrimary + newEquipOther + newAllied + otherNewEquip + usedEquip + partsInv + batteryInv + wip);
        // Total Inventories does NOT include WIP
        const totalInventories = newEquipPrimary + newEquipOther + newAllied + otherNewEquip + usedEquip + partsInv + batteryInv + otherInv;
        
        const otherCurrentAssets = bs.assets.current_assets.other_current.reduce((sum, acc) => sum + acc.balance, 0);
        const totalCurrentAssets = cash + tradeAR + allOtherAR + totalInventories + wip + otherCurrentAssets;
        
        // Fixed Assets - match backend logic exactly
        let rentalFleetGross = 0;
        let rentalFleetDeprec = 0;
        let otherFixed = 0;
        
        bs.assets.fixed_assets.forEach(acc => {
          const desc = acc.description.toUpperCase();
          // Match backend: Look for accounts with BOTH 'RENTAL' AND 'EQUIP' in description
          if (desc.includes('RENTAL') && desc.includes('EQUIP')) {
            if (desc.includes('DEPREC') || desc.includes('ACCUM')) {
              rentalFleetDeprec += acc.balance;
            } else {
              rentalFleetGross += acc.balance;
            }
          } else {
            otherFixed += acc.balance;
          }
        });
        
        const rentalFleet = rentalFleetGross + rentalFleetDeprec;
        
        // Other Assets
        const otherAssets = bs.assets.other_assets.reduce((sum, acc) => sum + acc.balance, 0);
        
        // LIABILITIES calculations
        const apPrimary = sumByPattern(bs.liabilities.current_liabilities, ['ACCOUNTS PAYABLE', 'TRADE']);
        const apOther = 0; // Placeholder
        const notesPayableCurrent = 0; // Placeholder
        const shortTermRentalFinance = sumByPattern(bs.liabilities.current_liabilities, ['RENTAL FINANCE', 'FLOOR PLAN']);
        const usedEquipFinancing = sumByPattern(bs.liabilities.current_liabilities, ['TRUCKS PURCHASED']);
        const otherCurrentLiab = bs.liabilities.current_liabilities.reduce((sum, acc) => sum + acc.balance, 0) - 
          (apPrimary + apOther + notesPayableCurrent + shortTermRentalFinance + usedEquipFinancing);
        const totalCurrentLiab = apPrimary + apOther + notesPayableCurrent + shortTermRentalFinance + usedEquipFinancing + otherCurrentLiab;
        
        // Long-term Liabilities
        const longTermNotes = sumByPattern(bs.liabilities.long_term_liabilities, ['NOTES PAYABLE', 'SCALE BANK']);
        const loansFromStockholders = sumByPattern(bs.liabilities.long_term_liabilities, ['STOCKHOLDER', 'SHAREHOLDER']);
        const ltRentalFleetFinancing = sumByPattern(bs.liabilities.long_term_liabilities, ['RENTAL', 'FLEET']) - shortTermRentalFinance;
        const otherLongTermDebt = bs.liabilities.long_term_liabilities.reduce((sum, acc) => sum + acc.balance, 0) - 
          (longTermNotes + loansFromStockholders + ltRentalFleetFinancing);
        const totalLTLiab = longTermNotes + loansFromStockholders + ltRentalFleetFinancing + otherLongTermDebt;
        
        const otherLiabilities = bs.liabilities.other_liabilities.reduce((sum, acc) => sum + acc.balance, 0);
        
        // EQUITY calculations
        const capitalStock = bs.equity.capital_stock.reduce((sum, acc) => sum + acc.balance, 0);
        const retainedEarnings = bs.equity.retained_earnings.reduce((sum, acc) => sum + acc.balance, 0) + 
          bs.equity.distributions.reduce((sum, acc) => sum + acc.balance, 0);
        const totalNetWorth = capitalStock + retainedEarnings;
        
        return (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            {/* Header */}
            <div className="bg-blue-50 border-b border-blue-200 p-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="font-semibold">Dealership:</span> {data.dealership_info.name}
                </div>
                <div>
                  <span className="font-semibold">As of Date:</span> {bs.as_of_date}
                </div>
                <div>
                  <span className="font-semibold">Status:</span> 
                  {bs.balanced ? (
                    <span className="text-green-600 font-semibold ml-2">✓ Balanced</span>
                  ) : (
                    <span className="text-red-600 font-semibold ml-2">⚠ Not Balanced</span>
                  )}
                </div>
              </div>
            </div>

            <div className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* ASSETS Column */}
                <div>
                  <h2 className="text-xl font-bold mb-4 text-blue-900">ASSETS</h2>
                  
                  {/* Current Assets */}
                  <div className="mb-6">
                    <h3 className="font-semibold text-gray-900 mb-2 bg-gray-100 px-3 py-2">Current Assets</h3>
                    
                    <div className="ml-4 space-y-1">
                      <div className="flex justify-between text-sm py-1">
                        <span className="text-gray-700">Cash</span>
                        <span className="font-medium">{formatCurrency(cash)}</span>
                      </div>
                      <div className="flex justify-between text-sm py-1">
                        <span className="text-gray-700">Trade Accounts Receivable</span>
                        <span className="font-medium">{formatCurrency(tradeAR)}</span>
                      </div>
                      <div className="flex justify-between text-sm py-1">
                        <span className="text-gray-700">All Other Accounts Receivable</span>
                        <span className="font-medium">{formatCurrency(allOtherAR)}</span>
                      </div>
                    </div>
                    
                    {/* Inventory Section */}
                    <div className="ml-4 mt-3">
                      <div className="text-sm font-medium text-gray-700 italic mb-1">Inventory</div>
                      <div className="ml-4 space-y-1">
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-gray-600">New Equipment, primary brand</span>
                          <span className="font-medium">{formatCurrency(newEquipPrimary)}</span>
                        </div>
                        {newEquipOther !== 0 && (
                          <div className="flex justify-between text-sm py-1">
                            <span className="text-gray-600">New Equipment, other brand</span>
                            <span className="font-medium">{formatCurrency(newEquipOther)}</span>
                          </div>
                        )}
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-gray-600">New Allied Inventory</span>
                          <span className="font-medium">{formatCurrency(newAllied)}</span>
                        </div>
                        {otherNewEquip !== 0 && (
                          <div className="flex justify-between text-sm py-1">
                            <span className="text-gray-600">Other New Equipment</span>
                            <span className="font-medium">{formatCurrency(otherNewEquip)}</span>
                          </div>
                        )}
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-gray-600">Used Equipment Inventory</span>
                          <span className="font-medium">{formatCurrency(usedEquip)}</span>
                        </div>
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-gray-600">Parts Inventory</span>
                          <span className="font-medium">{formatCurrency(partsInv)}</span>
                        </div>
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-gray-600">Battery Inventory</span>
                          <span className="font-medium">{formatCurrency(batteryInv)}</span>
                        </div>
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-gray-600">Other Inventory</span>
                          <span className="font-medium">{formatCurrency(otherInv)}</span>
                        </div>
                        <div className="flex justify-between text-sm py-1 font-semibold border-t border-gray-300 mt-1 pt-1">
                          <span className="text-gray-700 italic">Total Inventories</span>
                          <span>{formatCurrency(totalInventories)}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="ml-4 mt-2 space-y-1">
                      <div className="flex justify-between text-sm py-1">
                        <span className="text-gray-700">WIP</span>
                        <span className="font-medium">{formatCurrency(wip)}</span>
                      </div>
                      <div className="flex justify-between text-sm py-1">
                        <span className="text-gray-700">Other Current Assets</span>
                        <span className="font-medium">{formatCurrency(otherCurrentAssets)}</span>
                      </div>
                      <div className="flex justify-between text-sm py-1 font-semibold border-t border-gray-400 mt-1 pt-1">
                        <span className="text-gray-800 italic">Total Current Assets</span>
                        <span>{formatCurrency(totalCurrentAssets)}</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Fixed Assets */}
                  <div className="mb-6">
                    <h3 className="font-semibold text-gray-900 mb-2 bg-gray-100 px-3 py-2">Fixed Assets</h3>
                    <div className="ml-4 space-y-1">
                      <div className="flex justify-between text-sm py-1">
                        <span className="text-gray-700">Rental Fleet</span>
                        <span className="font-medium">{formatCurrency(rentalFleet)}</span>
                      </div>
                      <div className="flex justify-between text-sm py-1">
                        <span className="text-gray-700">Other Long Term or Fixed Assets</span>
                        <span className="font-medium">{formatCurrency(otherFixed)}</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Other Assets */}
                  {otherAssets !== 0 && (
                    <div className="mb-6">
                      <h3 className="font-semibold text-gray-900 mb-2 bg-gray-100 px-3 py-2">Other Assets</h3>
                      <div className="ml-4">
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-gray-700">Other Assets</span>
                          <span className="font-medium">{formatCurrency(otherAssets)}</span>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Total Assets */}
                  <div className="border-t-2 border-gray-900 pt-2 mt-4">
                    <div className="flex justify-between font-bold text-lg">
                      <span>Total Assets</span>
                      <span>{formatCurrency(bs.assets.total)}</span>
                    </div>
                  </div>
                </div>
                
                {/* LIABILITIES & EQUITY Column */}
                <div>
                  <h2 className="text-xl font-bold mb-4 text-blue-900">LIABILITIES</h2>
                  
                  {/* Current Liabilities */}
                  <div className="mb-6">
                    <h3 className="font-semibold text-gray-900 mb-2 bg-gray-100 px-3 py-2">Current Liabilities</h3>
                    <div className="ml-4 space-y-1">
                      <div className="flex justify-between text-sm py-1">
                        <span className="text-gray-700">A/P Primary Brand</span>
                        <span className="font-medium">{formatCurrency(apPrimary)}</span>
                      </div>
                      {apOther !== 0 && (
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-gray-700">A/P Other</span>
                          <span className="font-medium">{formatCurrency(apOther)}</span>
                        </div>
                      )}
                      {notesPayableCurrent !== 0 && (
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-gray-700">Notes Payable - due within 1 year</span>
                          <span className="font-medium">{formatCurrency(notesPayableCurrent)}</span>
                        </div>
                      )}
                      {shortTermRentalFinance !== 0 && (
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-gray-700">Short Term Rental Finance</span>
                          <span className="font-medium">{formatCurrency(shortTermRentalFinance)}</span>
                        </div>
                      )}
                      {usedEquipFinancing !== 0 && (
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-gray-700">Used Equipment Financing</span>
                          <span className="font-medium">{formatCurrency(usedEquipFinancing)}</span>
                        </div>
                      )}
                      <div className="flex justify-between text-sm py-1">
                        <span className="text-gray-700">Other Current Liabilities</span>
                        <span className="font-medium">{formatCurrency(otherCurrentLiab)}</span>
                      </div>
                      <div className="flex justify-between text-sm py-1 font-semibold border-t border-gray-400 mt-1 pt-1">
                        <span className="text-gray-800 italic">Total Current Liabilities</span>
                        <span>{formatCurrency(totalCurrentLiab)}</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Long-term Liabilities */}
                  <div className="mb-6">
                    <h3 className="font-semibold text-gray-900 mb-2 bg-gray-100 px-3 py-2">Long-term Liabilities</h3>
                    <div className="ml-4 space-y-1">
                      <div className="flex justify-between text-sm py-1">
                        <span className="text-gray-700">Long Term notes Payable</span>
                        <span className="font-medium">{formatCurrency(longTermNotes)}</span>
                      </div>
                      {loansFromStockholders !== 0 && (
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-gray-700">Loans from Stockholders</span>
                          <span className="font-medium">{formatCurrency(loansFromStockholders)}</span>
                        </div>
                      )}
                      {ltRentalFleetFinancing !== 0 && (
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-gray-700">LT Rental Fleet Financing</span>
                          <span className="font-medium">{formatCurrency(ltRentalFleetFinancing)}</span>
                        </div>
                      )}
                      {otherLongTermDebt !== 0 && (
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-gray-700">Other Long Term Debt</span>
                          <span className="font-medium">{formatCurrency(otherLongTermDebt)}</span>
                        </div>
                      )}
                      <div className="flex justify-between text-sm py-1 font-semibold border-t border-gray-400 mt-1 pt-1">
                        <span className="text-gray-800 italic">Total LT Liabilities</span>
                        <span>{formatCurrency(totalLTLiab)}</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Other Liabilities */}
                  {otherLiabilities !== 0 && (
                    <div className="mb-6">
                      <h3 className="font-semibold text-gray-900 mb-2 bg-gray-100 px-3 py-2">Other Liabilities</h3>
                      <div className="ml-4">
                        <div className="flex justify-between text-sm py-1">
                          <span className="text-gray-700">Other Liabilities</span>
                          <span className="font-medium">{formatCurrency(otherLiabilities)}</span>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Total Liabilities */}
                  <div className="border-t border-gray-600 pt-2 mb-6">
                    <div className="flex justify-between font-semibold text-base">
                      <span>Total Liabilities</span>
                      <span>{formatCurrency(bs.liabilities.total)}</span>
                    </div>
                  </div>
                  
                  {/* Net Worth/Owner Equity */}
                  <div className="mb-6">
                    <h3 className="font-semibold text-gray-900 mb-2 bg-gray-100 px-3 py-2">Net Worth/Owner Equity</h3>
                    <div className="ml-4 space-y-1">
                      <div className="flex justify-between text-sm py-1">
                        <span className="text-gray-700">Capital Stock</span>
                        <span className="font-medium">{formatCurrency(capitalStock)}</span>
                      </div>
                      <div className="flex justify-between text-sm py-1">
                        <span className="text-gray-700">Retained Earnings</span>
                        <span className="font-medium">{formatCurrency(retainedEarnings)}</span>
                      </div>
                      <div className="flex justify-between text-sm py-1 font-semibold border-t border-gray-400 mt-1 pt-1">
                        <span className="text-gray-800 italic">Total Net Worth</span>
                        <span>{formatCurrency(totalNetWorth)}</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Total Liabilities & Net Worth */}
                  <div className="border-t-2 border-gray-900 pt-2">
                    <div className="flex justify-between font-bold text-lg">
                      <span>Total Liabilities & Net Worth</span>
                      <span>{formatCurrency(bs.liabilities.total + bs.equity.total)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      })()}


      {/* Metrics Section (OLD - Remove later) */}
      {false && metrics && (
        <div className="mt-8">
          <h2 className="text-xl font-bold mb-4">Key Metrics</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* AR Aging */}
            <div className="bg-white border rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-3">AR Aging</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Current (0-30):</span>
                  <span className="font-medium">{formatCurrency(metrics.ar_aging?.current || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">31-60 days:</span>
                  <span className="font-medium">{formatCurrency(metrics.ar_aging?.days_31_60 || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">61-90 days:</span>
                  <span className="font-medium">{formatCurrency(metrics.ar_aging?.days_61_90 || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">91+ days:</span>
                  <span className="font-medium text-red-600">{formatCurrency(metrics.ar_aging?.days_91_plus || 0)}</span>
                </div>
                <div className="flex justify-between pt-2 border-t">
                  <span className="font-semibold">Total AR:</span>
                  <span className="font-semibold">{formatCurrency(metrics.ar_aging?.total || 0)}</span>
                </div>
              </div>
            </div>
            
            {/* Service Metrics */}
            <div className="bg-white border rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Service Metrics</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Service Calls/Day:</span>
                  <span className="font-medium">{metrics.service_calls_per_day?.calls_per_day?.toFixed(1) || '0.0'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Calls:</span>
                  <span className="font-medium">{metrics.service_calls_per_day?.total_service_calls || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Active Technicians:</span>
                  <span className="font-medium">{metrics.technician_count?.active_technicians || 0}</span>
                </div>
              </div>
            </div>
            
            {/* Labor Metrics */}
            <div className="bg-white border rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Labor Productivity</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Billed Hours:</span>
                  <span className="font-medium">{metrics.labor_metrics?.total_billed_hours?.toFixed(1) || '0.0'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Avg Labor Rate:</span>
                  <span className="font-medium">{formatCurrency(metrics.labor_metrics?.average_labor_rate || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Labor Value:</span>
                  <span className="font-medium">{formatCurrency(metrics.labor_metrics?.total_labor_value || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">WOs with Labor:</span>
                  <span className="font-medium">{metrics.labor_metrics?.work_orders_with_labor || 0}</span>
                </div>
              </div>
            </div>
            
            {/* Parts Inventory Metrics */}
            <div className="bg-white border rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Parts Inventory</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Fill Rate:</span>
                  <span className="font-medium text-green-600">{metrics.parts_inventory?.fill_rate?.toFixed(1) || '0.0'}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Inventory Turnover:</span>
                  <span className="font-medium">{metrics.parts_inventory?.inventory_turnover?.toFixed(2) || '0.00'}x</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Inventory Value:</span>
                  <span className="font-medium">{formatCurrency(metrics.parts_inventory?.inventory_value || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Obsolete Parts:</span>
                  <span className="font-medium text-red-600">{metrics.parts_inventory?.aging?.obsolete_count || 0}</span>
                </div>
              </div>
            </div>
            
            {/* Absorption Rate */}
            <div className="bg-white border rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Absorption Rate</h3>
              <div className="space-y-2 text-sm">
                <div className="text-center py-4">
                  <div className={`text-4xl font-bold ${
                    (metrics.absorption_rate?.rate || 0) >= 100 ? 'text-green-600' : 
                    (metrics.absorption_rate?.rate || 0) >= 80 ? 'text-yellow-600' : 
                    'text-red-600'
                  }`}>
                    {metrics.absorption_rate?.rate?.toFixed(1) || '0.0'}%
                  </div>
                  <div className="text-gray-500 text-xs mt-1">Aftermarket GP / Expenses</div>
                </div>
                <div className="flex justify-between pt-2 border-t">
                  <span className="text-gray-600">Aftermarket GP:</span>
                  <span className="font-medium">{formatCurrency(metrics.absorption_rate?.aftermarket_gp || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Expenses:</span>
                  <span className="font-medium">{formatCurrency(metrics.absorption_rate?.total_expenses || 0)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Expenses Section */}
      {expenses && (
        <div className="mt-8">
          <h2 className="text-xl font-bold mb-4">Operating Expenses</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Personnel Costs */}
            <div className="bg-white border rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Personnel Costs</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Payroll:</span>
                  <span className="font-medium">{formatCurrency(expenses.personnel?.payroll || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Payroll Taxes:</span>
                  <span className="font-medium">{formatCurrency(expenses.personnel?.payroll_taxes || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Benefits:</span>
                  <span className="font-medium">{formatCurrency(expenses.personnel?.benefits || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Commissions:</span>
                  <span className="font-medium">{formatCurrency(expenses.personnel?.commissions || 0)}</span>
                </div>
                <div className="flex justify-between border-t pt-2 mt-2">
                  <span className="font-semibold">Total:</span>
                  <span className="font-bold">{formatCurrency(expenses.personnel?.total || 0)}</span>
                </div>
              </div>
            </div>
            
            {/* Occupancy Costs */}
            <div className="bg-white border rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Occupancy Costs</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Rent:</span>
                  <span className="font-medium">{formatCurrency(expenses.occupancy?.rent || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Utilities:</span>
                  <span className="font-medium">{formatCurrency(expenses.occupancy?.utilities || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Insurance:</span>
                  <span className="font-medium">{formatCurrency(expenses.occupancy?.insurance || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Maintenance:</span>
                  <span className="font-medium">{formatCurrency(expenses.occupancy?.building_maintenance || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Depreciation:</span>
                  <span className="font-medium">{formatCurrency(expenses.occupancy?.depreciation || 0)}</span>
                </div>
                <div className="flex justify-between border-t pt-2 mt-2">
                  <span className="font-semibold">Total:</span>
                  <span className="font-bold">{formatCurrency(expenses.occupancy?.total || 0)}</span>
                </div>
              </div>
            </div>
            
            {/* Operating Expenses */}
            <div className="bg-white border rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Operating Expenses</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Advertising:</span>
                  <span className="font-medium">{formatCurrency(expenses.operating?.advertising || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Computer/IT:</span>
                  <span className="font-medium">{formatCurrency(expenses.operating?.computer_it || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Professional Services:</span>
                  <span className="font-medium">{formatCurrency(expenses.operating?.professional_services || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Vehicle Expense:</span>
                  <span className="font-medium">{formatCurrency(expenses.operating?.vehicle_expense || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Other:</span>
                  <span className="font-medium">{formatCurrency(expenses.operating?.other || 0)}</span>
                </div>
                <div className="flex justify-between border-t pt-2 mt-2">
                  <span className="font-semibold">Total:</span>
                  <span className="font-bold">{formatCurrency(expenses.operating?.total || 0)}</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Grand Total */}
          <div className="mt-4 bg-gray-900 text-white rounded-lg p-4">
            <div className="flex justify-between items-center">
              <span className="text-lg font-bold">TOTAL OPERATING EXPENSES</span>
              <span className="text-2xl font-bold">{formatCurrency(expenses.grand_total || 0)}</span>
            </div>
          </div>
        </div>
      )}


    </div>
  );
};

// Editable data row component
const DataRow = ({ label, data, onEdit }) => {
  const [editingField, setEditingField] = useState(null);
  const [editValue, setEditValue] = useState('');

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (sales, cogs) => {
    if (!sales || sales === 0) return '0.0%';
    const gp = ((sales - cogs) / sales) * 100;
    return `${gp.toFixed(1)}%`;
  };

  const handleEdit = (field, currentValue) => {
    setEditingField(field);
    setEditValue(currentValue.toString());
  };

  const handleSave = (field) => {
    onEdit(field, editValue);
    setEditingField(null);
  };

  const handleKeyDown = (e, field) => {
    if (e.key === 'Enter') {
      handleSave(field);
    } else if (e.key === 'Escape') {
      setEditingField(null);
    }
  };

  return (
    <tr className="border-b border-gray-200 hover:bg-gray-50">
      <td className="px-4 py-2">{label}</td>
      <td className="px-4 py-2 text-right">
        {editingField === 'sales' ? (
          <input
            type="text"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={() => handleSave('sales')}
            onKeyDown={(e) => handleKeyDown(e, 'sales')}
            className="w-full text-right border border-blue-300 rounded px-2 py-1"
            autoFocus
          />
        ) : (
          <span onClick={() => handleEdit('sales', data.sales)} className="cursor-pointer hover:bg-blue-50 px-2 py-1 rounded">
            {formatCurrency(data.sales)}
          </span>
        )}
      </td>
      <td className="px-4 py-2 text-right">
        {editingField === 'cogs' ? (
          <input
            type="text"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={() => handleSave('cogs')}
            onKeyDown={(e) => handleKeyDown(e, 'cogs')}
            className="w-full text-right border border-blue-300 rounded px-2 py-1"
            autoFocus
          />
        ) : (
          <span onClick={() => handleEdit('cogs', data.cogs)} className="cursor-pointer hover:bg-blue-50 px-2 py-1 rounded">
            {formatCurrency(data.cogs)}
          </span>
        )}
      </td>
      <td className="px-4 py-2 text-right font-medium">{formatCurrency(data.gross_profit)}</td>
      <td className="px-4 py-2 text-right font-medium">{formatPercent(data.sales, data.cogs)}</td>
    </tr>
  );
};

// Subtotal row component
const SubtotalRow = ({ label, data }) => {
  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (sales, cogs) => {
    if (!sales || sales === 0) return '0.0%';
    const gp = ((sales - cogs) / sales) * 100;
    return `${gp.toFixed(1)}%`;
  };

  return (
    <tr className="bg-gray-200 font-semibold border-t-2 border-gray-400">
      <td className="px-4 py-2">{label}</td>
      <td className="px-4 py-2 text-right">{formatCurrency(data.sales)}</td>
      <td className="px-4 py-2 text-right">{formatCurrency(data.cogs)}</td>
      <td className="px-4 py-2 text-right">{formatCurrency(data.gross_profit)}</td>
      <td className="px-4 py-2 text-right">{formatPercent(data.sales, data.cogs)}</td>
    </tr>
  );
};

// Total row component
const TotalRow = ({ label, data }) => {
  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (sales, cogs) => {
    if (!sales || sales === 0) return '0.0%';
    const gp = ((sales - cogs) / sales) * 100;
    return `${gp.toFixed(1)}%`;
  };

  return (
    <tr className="bg-gray-800 text-white font-bold border-t-4 border-gray-900">
      <td className="px-4 py-3">{label}</td>
      <td className="px-4 py-3 text-right">{formatCurrency(data.sales)}</td>
      <td className="px-4 py-3 text-right">{formatCurrency(data.cogs)}</td>
      <td className="px-4 py-3 text-right">{formatCurrency(data.gross_profit)}</td>
      <td className="px-4 py-3 text-right">{formatPercent(data.sales, data.cogs)}</td>
    </tr>
  );
};

export default Currie;
