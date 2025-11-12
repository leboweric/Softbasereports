import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { apiUrl } from '@/lib/api';
import { Users, TrendingUp, Award, ChevronDown, ChevronUp, Wrench, Clock, FileText } from 'lucide-react';
import * as XLSX from 'xlsx';

const PMTechnicianContest = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState('contest');
  const [customStartDate, setCustomStartDate] = useState('2025-11-01');
  const [customEndDate, setCustomEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [showCustomDates, setShowCustomDates] = useState(false);
  const [selectedTechnician, setSelectedTechnician] = useState(null);
  const [pmDetails, setPmDetails] = useState({});
  const [loadingPMs, setLoadingPMs] = useState({});

  useEffect(() => {
    fetchData();
  }, [dateRange, customStartDate, customEndDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      let url;
      
      if (dateRange === 'contest') {
        // Contest period: November 1, 2025 to today
        url = apiUrl(`/api/reports/service/pm-technician-performance?start_date=2025-11-01&end_date=${new Date().toISOString().split('T')[0]}`);
      } else if (dateRange === 'custom') {
        url = apiUrl(`/api/reports/service/pm-technician-performance?start_date=${customStartDate}&end_date=${customEndDate}`);
      } else {
        url = apiUrl(`/api/reports/service/pm-technician-performance?days=${dateRange}`);
      }
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch PM technician performance data');
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchPMDetails = async (technician) => {
    if (pmDetails[technician]) {
      // Already have the data, just toggle
      return;
    }

    setLoadingPMs(prev => ({ ...prev, [technician]: true }));
    
    try {
      let url;
      if (dateRange === 'contest') {
        url = apiUrl(`/api/reports/service/pm-technician-details?technician=${encodeURIComponent(technician)}&start_date=2025-11-01&end_date=${new Date().toISOString().split('T')[0]}`);
      } else if (dateRange === 'custom') {
        url = apiUrl(`/api/reports/service/pm-technician-details?technician=${encodeURIComponent(technician)}&start_date=${customStartDate}&end_date=${customEndDate}`);
      } else {
        url = apiUrl(`/api/reports/service/pm-technician-details?technician=${encodeURIComponent(technician)}&days=${dateRange}`);
      }
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch PM details');
      }

      const result = await response.json();
      setPmDetails(prev => ({ ...prev, [technician]: result.pms }));
    } catch (err) {
      console.error('Error fetching PM details:', err);
      setPmDetails(prev => ({ ...prev, [technician]: [] }));
    } finally {
      setLoadingPMs(prev => ({ ...prev, [technician]: false }));
    }
  };

  const toggleTechnicianDetails = async (technician) => {
    if (selectedTechnician === technician) {
      setSelectedTechnician(null);
    } else {
      setSelectedTechnician(technician);
      await fetchPMDetails(technician);
    }
  };

  const exportToExcel = () => {
    if (!data || !data.employees) return;

    // Create workbook
    const wb = XLSX.utils.book_new();

    // Summary sheet
    const summaryData = [
      ['PM Technician Performance Contest'],
      ['Period:', data.summary.period],
      [''],
      ['Total Technicians:', data.summary.totalEmployees],
      ['Total PMs Completed:', data.summary.totalPMs],
      ['Top Performer:', data.summary.topPerformer?.employeeName || 'N/A'],
      ['Top Performer PMs:', data.summary.topPerformer?.totalPMs || 0],
      ['Average per Technician:', data.summary.avgPerEmployee],
    ];
    const summaryWs = XLSX.utils.aoa_to_sheet(summaryData);
    XLSX.utils.book_append_sheet(wb, summaryWs, 'Summary');

    // Performance sheet
    const perfHeaders = [
      'Rank',
      'Technician',
      'Total PMs',
      '% of Total',
      'Days Worked',
      'Avg PMs/Day',
      'Total Hours',
      'Avg Time/PM',
      'Last PM Date',
      'Days Inactive'
    ];

    const perfRows = data.employees.map((tech, index) => [
      index + 1,
      tech.employeeName || tech.employeeId,
      tech.totalPMs,
      tech.percentOfTotal + '%',
      tech.daysWorked,
      tech.avgDailyPMs,
      tech.totalHours,
      tech.avgTimePerPM,
      tech.lastPMDate || 'N/A',
      tech.daysInactive
    ]);

    const perfData = [perfHeaders, ...perfRows];
    const perfWs = XLSX.utils.aoa_to_sheet(perfData);

    // Auto-size columns
    const perfColWidths = perfHeaders.map((header, i) => {
      const maxLength = Math.max(
        header.length,
        ...perfRows.map(row => String(row[i] || '').length)
      );
      return { wch: Math.min(maxLength + 2, 30) };
    });
    perfWs['!cols'] = perfColWidths;

    // Bold headers
    const perfRange = XLSX.utils.decode_range(perfWs['!ref']);
    for (let col = perfRange.s.c; col <= perfRange.e.c; col++) {
      const cellAddress = XLSX.utils.encode_cell({ r: 0, c: col });
      if (!perfWs[cellAddress]) continue;
      perfWs[cellAddress].s = {
        font: { bold: true }
      };
    }

    XLSX.utils.book_append_sheet(wb, perfWs, 'Performance');

    // Export
    XLSX.writeFile(wb, `pm-technician-contest-${new Date().toISOString().split('T')[0]}.xlsx`);
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse">Loading PM technician performance data...</div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-red-500">Error: {error}</div>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  const { employees, summary } = data;

  return (
    <div className="space-y-6">
      {/* Contest Leaderboard Banner - Only show for contest period */}
      {dateRange === 'contest' && data && data.employees.length > 0 && (
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-300">
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <span className="text-2xl">🏆</span>
              PM Technician Performance Contest - Q1 FY2026
              <span className="text-sm font-normal text-gray-600 ml-2">
                (Nov 1, 2025 - Jan 31, 2026)
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {data.employees.slice(0, 3).map((tech, index) => (
                <div
                  key={tech.employeeId}
                  className={`p-4 rounded-lg text-center ${
                    index === 0 ? 'bg-yellow-100 border-2 border-yellow-400' :
                    index === 1 ? 'bg-gray-100 border-2 border-gray-400' :
                    'bg-orange-100 border-2 border-orange-400'
                  }`}
                >
                  <div className="text-3xl mb-2">
                    {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                  </div>
                  <div className="font-bold text-lg">
                    {tech.employeeName || tech.employeeId}
                  </div>
                  <div className="text-2xl font-bold mt-2">
                    {tech.totalPMs} PMs
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    {tech.percentOfTotal}% of total • {tech.avgDailyPMs} avg/day
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    {tech.totalHours} hours • {tech.avgTimePerPM} hrs/PM
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Technicians</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.totalEmployees}</div>
            <p className="text-xs text-muted-foreground">Active in period</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total PMs Completed</CardTitle>
            <Wrench className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.totalPMs}</div>
            <p className="text-xs text-muted-foreground">{summary.period}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Top Performer</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">
              {summary.topPerformer?.employeeName || summary.topPerformer?.employeeId || 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {summary.topPerformer?.totalPMs || 0} PMs completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg per Technician</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary.avgPerEmployee}
            </div>
            <p className="text-xs text-muted-foreground">Average PMs</p>
          </CardContent>
        </Card>
      </div>

      {/* Technician Performance Table */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>PM Technician Performance</CardTitle>
              {dateRange === 'contest' && (
                <p className="text-sm text-blue-600 font-semibold mt-1">
                  🏆 Contest Period: November 1, 2025 - January 31, 2026 (Q1 FY2026)
                </p>
              )}
            </div>
            <div className="flex gap-2 items-center">
              <select
                value={dateRange}
                onChange={(e) => {
                  setDateRange(e.target.value);
                  setShowCustomDates(e.target.value === 'custom');
                }}
                className="px-3 py-1 border rounded-md text-sm"
              >
                <option value="contest">🏆 Contest (Nov 1 - Today)</option>
                <option value="7">Last 7 Days</option>
                <option value="30">Last 30 Days</option>
                <option value="60">Last 60 Days</option>
                <option value="90">Last 90 Days</option>
                <option value="365">Last Year</option>
                <option value="custom">Custom Dates</option>
              </select>
              
              {showCustomDates && (
                <>
                  <input
                    type="date"
                    value={customStartDate}
                    onChange={(e) => setCustomStartDate(e.target.value)}
                    className="px-2 py-1 border rounded-md text-sm"
                  />
                  <span className="text-sm">to</span>
                  <input
                    type="date"
                    value={customEndDate}
                    onChange={(e) => setCustomEndDate(e.target.value)}
                    className="px-2 py-1 border rounded-md text-sm"
                  />
                </>
              )}
              
              <button
                onClick={exportToExcel}
                className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 text-sm"
              >
                Export Excel
              </button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Rank</th>
                  <th className="text-left p-2">Technician</th>
                  <th className="text-right p-2">Total PMs</th>
                  <th className="text-right p-2">% of Total</th>
                  <th className="text-right p-2">Days Worked</th>
                  <th className="text-right p-2">Avg PMs/Day</th>
                  <th className="text-right p-2">Total Hours</th>
                  <th className="text-right p-2">Avg Time/PM</th>
                  <th className="text-right p-2">Last PM</th>
                  <th className="text-right p-2">Days Inactive</th>
                  <th className="text-center p-2" width="40">Details</th>
                </tr>
              </thead>
              <tbody>
                {employees.map((tech, index) => (
                  <React.Fragment key={tech.employeeId}>
                  <tr 
                    className={`border-b hover:bg-gray-50 cursor-pointer ${index === 0 ? 'bg-green-50' : ''} ${selectedTechnician === tech.employeeId ? 'bg-blue-50' : ''}`}
                    onClick={() => toggleTechnicianDetails(tech.employeeId)}
                  >
                    <td className="p-2">
                      {index === 0 && <span className="text-xl">🏆</span>}
                      {index === 1 && <span className="text-xl">🥈</span>}
                      {index === 2 && <span className="text-xl">🥉</span>}
                      {index > 2 && <span className="text-gray-500">{index + 1}</span>}
                    </td>
                    <td className="p-2 font-medium">
                      <div className="font-semibold">{tech.employeeName || tech.employeeId}</div>
                    </td>
                    <td className="p-2 text-right font-semibold text-lg">
                      {tech.totalPMs}
                    </td>
                    <td className="p-2 text-right">
                      <span className={`px-2 py-1 rounded text-xs ${
                        tech.percentOfTotal >= 20 ? 'bg-green-100 text-green-800' :
                        tech.percentOfTotal >= 10 ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {tech.percentOfTotal}%
                      </span>
                    </td>
                    <td className="p-2 text-right">{tech.daysWorked}</td>
                    <td className="p-2 text-right">{tech.avgDailyPMs}</td>
                    <td className="p-2 text-right">{tech.totalHours}</td>
                    <td className="p-2 text-right">{tech.avgTimePerPM}</td>
                    <td className="p-2 text-right text-xs">
                      {tech.lastPMDate ? new Date(tech.lastPMDate).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="p-2 text-right">
                      {tech.daysInactive > 0 && (
                        <span className={`px-2 py-1 rounded text-xs ${
                          tech.daysInactive > 7 ? 'bg-red-100 text-red-800' :
                          tech.daysInactive > 3 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {tech.daysInactive}d
                        </span>
                      )}
                    </td>
                    <td className="p-2 text-center">
                      {selectedTechnician === tech.employeeId ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </td>
                  </tr>
                  
                  {/* PM Details Row */}
                  {selectedTechnician === tech.employeeId && (
                    <tr>
                      <td colSpan="11" className="p-0">
                        <div className="bg-gray-50 p-4 border-t border-b">
                          <div className="flex items-center gap-2 mb-3">
                            <Wrench className="h-5 w-5 text-blue-600" />
                            <h4 className="font-semibold text-lg">
                              PM Details for {tech.employeeName || tech.employeeId}
                            </h4>
                            <span className="text-sm text-gray-500">
                              ({pmDetails[tech.employeeId]?.length || 0} PMs)
                            </span>
                          </div>
                          
                          {loadingPMs[tech.employeeId] ? (
                            <div className="text-center py-4">Loading PM details...</div>
                          ) : pmDetails[tech.employeeId] && pmDetails[tech.employeeId].length > 0 ? (
                            <div className="overflow-x-auto">
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="border-b bg-white">
                                    <th className="text-left p-2">WO #</th>
                                    <th className="text-left p-2">Date</th>
                                    <th className="text-right p-2">Hours</th>
                                    <th className="text-left p-2">Customer</th>
                                    <th className="text-left p-2">Unit #</th>
                                    <th className="text-left p-2">Serial #</th>
                                    <th className="text-left p-2">Make</th>
                                    <th className="text-left p-2">Model</th>
                                    <th className="text-left p-2">Phone</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {pmDetails[tech.employeeId].map((pm, idx) => (
                                    <tr key={`${pm.woNo}-${idx}`} className={`border-b ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                                      <td className="p-2 font-mono">{pm.woNo}</td>
                                      <td className="p-2">{pm.laborDate ? new Date(pm.laborDate).toLocaleDateString() : 'N/A'}</td>
                                      <td className="p-2 text-right">{pm.hours}</td>
                                      <td className="p-2">{pm.customer}</td>
                                      <td className="p-2">{pm.unitNo || '-'}</td>
                                      <td className="p-2 font-mono text-xs">{pm.serialNo || '-'}</td>
                                      <td className="p-2">{pm.make || '-'}</td>
                                      <td className="p-2">{pm.model || '-'}</td>
                                      <td className="p-2">{pm.customerPhone || '-'}</td>
                                    </tr>
                                  ))}
                                  <tr className="font-semibold bg-blue-50">
                                    <td colSpan="2" className="p-2 text-right">Total:</td>
                                    <td className="p-2 text-right">
                                      {pmDetails[tech.employeeId].reduce((sum, pm) => sum + (pm.hours || 0), 0).toFixed(1)} hrs
                                    </td>
                                    <td colSpan="6" className="p-2">
                                      {pmDetails[tech.employeeId].length} PMs completed
                                    </td>
                                  </tr>
                                </tbody>
                              </table>
                            </div>
                          ) : (
                            <div className="text-center py-4 text-gray-500">No PM details available</div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>

          {employees.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No PM performance data available for the selected period.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default PMTechnicianContest;
