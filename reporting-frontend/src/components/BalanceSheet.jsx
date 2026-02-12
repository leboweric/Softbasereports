import { useState, useEffect } from 'react';
import { Calendar as CalendarIcon, RefreshCw, Download } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { format } from 'date-fns';
import axios from 'axios';
import * as XLSX from 'xlsx';

const BalanceSheet = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [asOfDate, setAsOfDate] = useState('');
  const [error, setError] = useState(null);

  // Initialize with today's date
  useEffect(() => {
    const today = new Date();
    setAsOfDate(format(today, 'yyyy-MM-dd'));
  }, []);

  useEffect(() => {
    if (asOfDate) {
      fetchData();
    }
  }, [asOfDate]);

  const fetchData = async () => {
    if (!asOfDate) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');

      // Use the currie sales-cogs-gp endpoint which includes balance sheet data
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/currie/sales-cogs-gp`,
        {
          params: { start_date: asOfDate, end_date: asOfDate, refresh: 'true' },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setData(response.data);
    } catch (err) {
      console.error('Error fetching Balance Sheet data:', err);
      setError(err.response?.data?.error || 'Failed to load Balance Sheet data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const exportToExcel = () => {
    if (!data || !data.balance_sheet) return;

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

    // Calculate all the values (same as in render)
    const cash = bs.assets.current_assets.cash.reduce((sum, acc) => sum + acc.balance, 0);
    const tradeAR = bs.assets.current_assets.accounts_receivable.reduce((sum, acc) => sum + acc.balance, 0);
    const allOtherAR = 0;

    const inventory = bs.assets.current_assets.inventory;
    const newEquipPrimary = sumByPattern(inventory, ['NEW TRUCK']);
    const newAllied = sumByPattern(inventory, ['NEW ALLIED']);
    const usedEquip = sumByPattern(inventory, ['USED TRUCK']);
    const partsInv = sumByPattern(inventory, ['PARTS']) - sumByPattern(inventory, ['MISC']);
    const batteryInv = sumByPattern(inventory, ['BATTRY', 'BATTERY', 'CHARGER']);
    const wip = sumByPattern(inventory, ['WORK', 'PROCESS']);
    const otherInv = inventory.reduce((sum, acc) => sum + acc.balance, 0) -
      (newEquipPrimary + newAllied + usedEquip + partsInv + batteryInv + wip);
    const totalInventories = newEquipPrimary + newAllied + usedEquip + partsInv + batteryInv + otherInv;

    const otherCurrentAssets = bs.assets.current_assets.other_current.reduce((sum, acc) => sum + acc.balance, 0);
    const totalCurrentAssets = cash + tradeAR + allOtherAR + totalInventories + wip + otherCurrentAssets;

    let rentalFleetGross = 0;
    let rentalFleetDeprec = 0;
    let otherFixed = 0;
    bs.assets.fixed_assets.forEach(acc => {
      const desc = acc.description.toUpperCase();
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

    const otherAssets = bs.assets.other_assets.reduce((sum, acc) => sum + acc.balance, 0);

    // Negate liabilities and equity for display (GL stores credits as negative)
    const apPrimary = -sumByPattern(bs.liabilities.current_liabilities, ['ACCOUNTS PAYABLE', 'TRADE']);
    const shortTermRentalFinance = -sumByPattern(bs.liabilities.current_liabilities, ['RENTAL FINANCE', 'FLOOR PLAN']);
    const usedEquipFinancing = -sumByPattern(bs.liabilities.current_liabilities, ['TRUCKS PURCHASED']);
    const rawCurrentLiab = -bs.liabilities.current_liabilities.reduce((sum, acc) => sum + acc.balance, 0);
    const otherCurrentLiab = rawCurrentLiab - (apPrimary + shortTermRentalFinance + usedEquipFinancing);
    const totalCurrentLiab = apPrimary + shortTermRentalFinance + usedEquipFinancing + otherCurrentLiab;

    const longTermNotes = -sumByPattern(bs.liabilities.long_term_liabilities, ['NOTES PAYABLE', 'SCALE BANK']);
    const loansFromStockholders = -sumByPattern(bs.liabilities.long_term_liabilities, ['STOCKHOLDER', 'SHAREHOLDER']);
    const ltRentalFleetFinancing = -sumByPattern(bs.liabilities.long_term_liabilities, ['RENTAL', 'FLEET']) - shortTermRentalFinance;
    const rawLTLiab = -bs.liabilities.long_term_liabilities.reduce((sum, acc) => sum + acc.balance, 0);
    const otherLongTermDebt = rawLTLiab - (longTermNotes + loansFromStockholders + ltRentalFleetFinancing);
    const totalLTLiab = longTermNotes + loansFromStockholders + ltRentalFleetFinancing + otherLongTermDebt;

    const otherLiabilities = -bs.liabilities.other_liabilities.reduce((sum, acc) => sum + acc.balance, 0);
    const totalLiabilitiesExport = totalCurrentLiab + totalLTLiab + otherLiabilities;

    const capitalStock = -bs.equity.capital_stock.reduce((sum, acc) => sum + acc.balance, 0);
    const retainedEarnings = -(bs.equity.retained_earnings.reduce((sum, acc) => sum + acc.balance, 0) +
      bs.equity.distributions.reduce((sum, acc) => sum + acc.balance, 0));
    const netIncomeExport = -(bs.equity.net_income || 0);
    const totalNetWorth = capitalStock + retainedEarnings + netIncomeExport;

    // Create worksheet data
    const worksheetData = [
      ['BALANCE SHEET'],
      [`As of: ${bs.as_of_date}`],
      [''],
      ['ASSETS'],
      ['Current Assets'],
      ['  Cash', cash],
      ['  Trade Accounts Receivable', tradeAR],
      ['  All Other Accounts Receivable', allOtherAR],
      ['  Inventory'],
      ['    New Equipment, primary brand', newEquipPrimary],
      ['    New Allied Inventory', newAllied],
      ['    Used Equipment Inventory', usedEquip],
      ['    Parts Inventory', partsInv],
      ['    Battery Inventory', batteryInv],
      ['    Other Inventory', otherInv],
      ['  Total Inventories', totalInventories],
      ['  WIP', wip],
      ['  Other Current Assets', otherCurrentAssets],
      ['Total Current Assets', totalCurrentAssets],
      [''],
      ['Fixed Assets'],
      ['  Rental Fleet', rentalFleet],
      ['  Other Long Term or Fixed Assets', otherFixed],
      [''],
      ['Other Assets', otherAssets],
      [''],
      ['TOTAL ASSETS', bs.assets.total],
      [''],
      ['LIABILITIES'],
      ['Current Liabilities'],
      ['  A/P Primary Brand', apPrimary],
      ['  Short Term Rental Finance', shortTermRentalFinance],
      ['  Used Equipment Financing', usedEquipFinancing],
      ['  Other Current Liabilities', otherCurrentLiab],
      ['Total Current Liabilities', totalCurrentLiab],
      [''],
      ['Long-term Liabilities'],
      ['  Long Term Notes Payable', longTermNotes],
      ['  Loans from Stockholders', loansFromStockholders],
      ['  LT Rental Fleet Financing', ltRentalFleetFinancing],
      ['  Other Long Term Debt', otherLongTermDebt],
      ['Total LT Liabilities', totalLTLiab],
      [''],
      ['Other Liabilities', otherLiabilities],
      [''],
      ['TOTAL LIABILITIES', totalLiabilitiesExport],
      [''],
      ['NET WORTH/OWNER EQUITY'],
      ['  Capital Stock', capitalStock],
      ['  Retained Earnings', retainedEarnings],
      ['  Current Year Net Income', netIncomeExport],
      ['Total Net Worth', totalNetWorth],
      [''],
      ['TOTAL LIABILITIES & NET WORTH', totalLiabilitiesExport + totalNetWorth],
    ];

    const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);

    // Format currency columns
    const range = XLSX.utils.decode_range(worksheet['!ref']);
    for (let row = 0; row <= range.e.r; row++) {
      const cellAddress = XLSX.utils.encode_cell({ c: 1, r: row });
      if (worksheet[cellAddress] && typeof worksheet[cellAddress].v === 'number') {
        worksheet[cellAddress].z = '$#,##0';
      }
    }

    worksheet['!cols'] = [{ wch: 35 }, { wch: 15 }];

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Balance Sheet');

    XLSX.writeFile(workbook, `Balance_Sheet_${asOfDate}.xlsx`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading Balance Sheet...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  if (!data || !data.balance_sheet) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-4 mb-6">
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-52 justify-start text-left font-normal">
                <CalendarIcon className="mr-2 h-4 w-4" />
                {asOfDate ? format(new Date(asOfDate + 'T00:00:00'), 'MMMM d, yyyy') : 'Select date'}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
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
        </div>
        <div className="text-gray-500">Select a date to view the Balance Sheet</div>
      </div>
    );
  }

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
  const tradeAR = bs.assets.current_assets.accounts_receivable.reduce((sum, acc) => sum + acc.balance, 0);
  const allOtherAR = 0;

  const inventory = bs.assets.current_assets.inventory;
  const newEquipPrimary = sumByPattern(inventory, ['NEW TRUCK']);
  const newEquipOther = 0;
  const newAllied = sumByPattern(inventory, ['NEW ALLIED']);
  const otherNewEquip = 0;
  const usedEquip = sumByPattern(inventory, ['USED TRUCK']);
  const partsInv = sumByPattern(inventory, ['PARTS']) - sumByPattern(inventory, ['MISC']);
  const batteryInv = sumByPattern(inventory, ['BATTRY', 'BATTERY', 'CHARGER']);
  const wip = sumByPattern(inventory, ['WORK', 'PROCESS']);
  const otherInv = inventory.reduce((sum, acc) => sum + acc.balance, 0) -
    (newEquipPrimary + newEquipOther + newAllied + otherNewEquip + usedEquip + partsInv + batteryInv + wip);
  const totalInventories = newEquipPrimary + newEquipOther + newAllied + otherNewEquip + usedEquip + partsInv + batteryInv + otherInv;

  const otherCurrentAssets = bs.assets.current_assets.other_current.reduce((sum, acc) => sum + acc.balance, 0);
  const totalCurrentAssets = cash + tradeAR + allOtherAR + totalInventories + wip + otherCurrentAssets;

  // Fixed Assets
  let rentalFleetGross = 0;
  let rentalFleetDeprec = 0;
  let otherFixed = 0;

  bs.assets.fixed_assets.forEach(acc => {
    const desc = acc.description.toUpperCase();
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
  const otherAssets = bs.assets.other_assets.reduce((sum, acc) => sum + acc.balance, 0);

  // LIABILITIES calculations
  // GL stores credits (liabilities, equity) as negative values
  // For balance sheet display, we negate them to show as positive
  const apPrimary = -sumByPattern(bs.liabilities.current_liabilities, ['ACCOUNTS PAYABLE', 'TRADE']);
  const apOther = 0;
  const notesPayableCurrent = 0;
  const shortTermRentalFinance = -sumByPattern(bs.liabilities.current_liabilities, ['RENTAL FINANCE', 'FLOOR PLAN']);
  const usedEquipFinancing = -sumByPattern(bs.liabilities.current_liabilities, ['TRUCKS PURCHASED']);
  const rawCurrentLiab = -bs.liabilities.current_liabilities.reduce((sum, acc) => sum + acc.balance, 0);
  const otherCurrentLiab = rawCurrentLiab - (apPrimary + apOther + notesPayableCurrent + shortTermRentalFinance + usedEquipFinancing);
  const totalCurrentLiab = apPrimary + apOther + notesPayableCurrent + shortTermRentalFinance + usedEquipFinancing + otherCurrentLiab;

  // Long-term Liabilities
  const longTermNotes = -sumByPattern(bs.liabilities.long_term_liabilities, ['NOTES PAYABLE', 'SCALE BANK']);
  const loansFromStockholders = -sumByPattern(bs.liabilities.long_term_liabilities, ['STOCKHOLDER', 'SHAREHOLDER']);
  const ltRentalFleetFinancing = -sumByPattern(bs.liabilities.long_term_liabilities, ['RENTAL', 'FLEET']) - shortTermRentalFinance;
  const rawLTLiab = -bs.liabilities.long_term_liabilities.reduce((sum, acc) => sum + acc.balance, 0);
  const otherLongTermDebt = rawLTLiab - (longTermNotes + loansFromStockholders + ltRentalFleetFinancing);
  const totalLTLiab = longTermNotes + loansFromStockholders + ltRentalFleetFinancing + otherLongTermDebt;

  const otherLiabilities = -bs.liabilities.other_liabilities.reduce((sum, acc) => sum + acc.balance, 0);
  const totalLiabilities = totalCurrentLiab + totalLTLiab + otherLiabilities;

  // EQUITY calculations (also negate for display)
  const capitalStock = -bs.equity.capital_stock.reduce((sum, acc) => sum + acc.balance, 0);
  const retainedEarnings = -(bs.equity.retained_earnings.reduce((sum, acc) => sum + acc.balance, 0) +
    bs.equity.distributions.reduce((sum, acc) => sum + acc.balance, 0));
  const netIncome = -(bs.equity.net_income || 0);
  const totalNetWorth = capitalStock + retainedEarnings + netIncome;

  return (
    <div className="p-6">
      {/* Controls */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-52 justify-start text-left font-normal">
                <CalendarIcon className="mr-2 h-4 w-4" />
                {asOfDate ? format(new Date(asOfDate + 'T00:00:00'), 'MMMM d, yyyy') : 'Select date'}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
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
          <Button variant="ghost" size="sm" onClick={fetchData} title="Refresh">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <Button onClick={exportToExcel} className="flex items-center gap-2">
          <Download className="h-4 w-4" />
          Download Excel
        </Button>
      </div>

      {/* Balance Sheet */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {/* Header */}
        <div className="bg-blue-50 border-b border-blue-200 p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="font-semibold">Dealership:</span> {data.dealership_info?.name || 'N/A'}
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
                  <span>{formatCurrency(totalLiabilities)}</span>
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
                  <div className="flex justify-between text-sm py-1">
                    <span className="text-gray-700">Current Year Net Income</span>
                    <span className="font-medium">{formatCurrency(netIncome)}</span>
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
                  <span>{formatCurrency(totalLiabilities + totalNetWorth)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BalanceSheet;
