import React, { useState, useEffect } from 'react';
import { FileSpreadsheet, Download, Calendar, RefreshCw } from 'lucide-react';
import axios from 'axios';

const Currie = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [error, setError] = useState(null);

  // Initialize with current quarter
  useEffect(() => {
    const now = new Date();
    const currentMonth = now.getMonth(); // 0-11
    const currentYear = now.getFullYear();
    
    // Determine fiscal year quarter (March start)
    let quarter, fiscalYear;
    if (currentMonth >= 2 && currentMonth <= 4) { // Mar-May = Q1
      quarter = 1;
      fiscalYear = currentYear;
    } else if (currentMonth >= 5 && currentMonth <= 7) { // Jun-Aug = Q2
      quarter = 2;
      fiscalYear = currentYear;
    } else if (currentMonth >= 8 && currentMonth <= 10) { // Sep-Nov = Q3
      quarter = 3;
      fiscalYear = currentYear;
    } else { // Dec-Feb = Q4
      quarter = 4;
      fiscalYear = currentMonth >= 11 ? currentYear : currentYear - 1;
    }
    
    setQuarter(quarter, fiscalYear);
  }, []);

  const setQuarter = (quarter, fiscalYear) => {
    let start, end;
    
    switch(quarter) {
      case 1: // Q1: Mar-May
        start = `${fiscalYear}-03-01`;
        end = `${fiscalYear}-05-31`;
        break;
      case 2: // Q2: Jun-Aug
        start = `${fiscalYear}-06-01`;
        end = `${fiscalYear}-08-31`;
        break;
      case 3: // Q3: Sep-Nov
        start = `${fiscalYear}-09-01`;
        end = `${fiscalYear}-11-30`;
        break;
      case 4: // Q4: Dec-Feb
        start = `${fiscalYear}-12-01`;
        end = `${fiscalYear + 1}-02-28`;
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
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/currie/sales-cogs-gp`,
        {
          params: { start_date: startDate, end_date: endDate },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setData(response.data);
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

  const exportToExcel = () => {
    // TODO: Phase 4 - Generate Excel file matching Currie template
    alert('Excel export coming in Phase 4!');
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
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Download className="w-4 h-4 mr-2" />
            Export to Excel
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
                onClick={() => setQuarter(1, 2026)}
                className="px-3 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm"
              >
                Q1 FY2026
              </button>
              <button
                onClick={() => setQuarter(2, 2026)}
                className="px-3 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm"
              >
                Q2 FY2026
              </button>
              <button
                onClick={() => setQuarter(3, 2026)}
                className="px-3 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm"
              >
                Q3 FY2026
              </button>
              <button
                onClick={() => setQuarter(4, 2026)}
                className="px-3 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm"
              >
                Q4 FY2026
              </button>
            </div>
            <button
              onClick={fetchData}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center mt-6"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {data && (
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
                
                <SubtotalRow label="TOTAL NEW EQUIPMENT" data={data.totals.total_new_equipment} />
                <SubtotalRow label="TOTAL SALES DEPARTMENT" data={data.totals.total_sales_dept} />

                {/* RENTAL SECTION */}
                <tr className="bg-gray-100 font-semibold">
                  <td colSpan="5" className="px-4 py-2">RENTAL DEPARTMENT</td>
                </tr>
                
                <DataRow 
                  label="Short Term Rental Sales"
                  data={data.rental.short_term}
                  onEdit={(field, value) => handleCellEdit('rental', 'short_term', field, value)}
                />
                <DataRow 
                  label="Long Term Rental Sales"
                  data={data.rental.long_term}
                  onEdit={(field, value) => handleCellEdit('rental', 'long_term', field, value)}
                />
                <DataRow 
                  label="Re-rent (Sub-rent)"
                  data={data.rental.rerent}
                  onEdit={(field, value) => handleCellEdit('rental', 'rerent', field, value)}
                />
                
                <SubtotalRow label="TOTAL RENTAL" data={data.totals.total_rental} />

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
                <SubtotalRow label="TOTAL AFTERMARKET" data={data.totals.total_aftermarket} />

                {/* TRUCKING SECTION */}
                <tr className="bg-gray-100 font-semibold">
                  <td colSpan="5" className="px-4 py-2">TRUCKING DEPARTMENT</td>
                </tr>
                
                <DataRow 
                  label="Trucking"
                  data={data.trucking}
                  onEdit={(field, value) => handleCellEdit('trucking', null, field, value)}
                />

                {/* COMPANY TOTAL */}
                <TotalRow label="TOTAL COMPANY" data={data.totals.total_company} />
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

      {/* Notes */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">Implementation Notes</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• <strong>Phase 1:</strong> Sales, COGS, and Gross Profit data (current view)</li>
          <li>• <strong>Rental COGS:</strong> Using simplified approach (direct costs only). Depreciation/interest calculation coming in Phase 2.</li>
          <li>• <strong>Brand Classification:</strong> Linde equipment classified as "Primary Brand", all others as "Other Brands"</li>
          <li>• <strong>Editable Cells:</strong> Click any value to edit manually. Changes are temporary until exported.</li>
          <li>• <strong>Excel Export:</strong> Coming in Phase 4 - will match exact Currie template format</li>
        </ul>
      </div>
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
