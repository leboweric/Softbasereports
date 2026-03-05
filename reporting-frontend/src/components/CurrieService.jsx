import React, { useState, useEffect } from 'react';
import { Wrench, DollarSign, Users, Activity, BarChart3, Gauge, HelpCircle, TrendingUp, TrendingDown, RefreshCw, Target, Clock, FileText, Percent, ArrowUpRight, ArrowDownRight, Calendar } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import axios from 'axios';
import { apiUrl } from '@/lib/api';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from 'recharts';

// ─── Currie Service KPI Help Content ───────────────────────────────────────────
const KPI_HELP = {
  service_gp_pct: {
    title: 'Service Gross Profit %',
    what: 'Service Gross Profit Percentage measures how much of your service revenue remains after direct costs (technician wages, parts used on jobs, sublet costs). The Currie benchmark for service departments is 65%. This is the single most important measure of your service department\'s pricing and cost control effectiveness.',
    formula: '(Service Revenue − Service COGS) ÷ Service Revenue × 100',
    actions: [
      'Review and increase labor rates — ensure your effective rate keeps pace with technician pay increases',
      'Reduce warranty and goodwill write-offs by improving first-time fix rates',
      'Minimize unbilled time — track and bill for travel, diagnostics, and setup',
      'Negotiate better sublet pricing or bring high-volume sublet work in-house',
      'Train technicians to upsell PM services and identify additional needed repairs'
    ]
  },
  revenue_per_tech: {
    title: 'Revenue per Technician per Month',
    what: 'Total service department revenue divided by the number of active technicians and the number of months in the period. This measures how much revenue each tech generates. The Currie benchmark is $20,000–$25,000 per tech per month for industrial equipment dealers.',
    formula: 'Total Service Revenue ÷ Number of Months ÷ Active Technicians',
    actions: [
      'Increase billable hours per tech — reduce downtime between jobs',
      'Raise labor rates to match market and technician skill levels',
      'Improve dispatching efficiency to reduce travel and idle time',
      'Cross-train technicians to handle a wider variety of equipment',
      'Ensure all billable work is captured — audit for missed charges'
    ]
  },
  gp_per_tech: {
    title: 'GP per Technician per Month',
    what: 'Gross profit generated per technician per month. This is the most important service productivity metric because it accounts for both revenue generation AND cost control. The Currie benchmark is approximately $15,000 per tech per month.',
    formula: 'Total Service GP ÷ Number of Months ÷ Active Technicians',
    actions: [
      'Focus on high-margin work — PM contracts, customer labor vs. warranty',
      'Reduce parts costs on service jobs through better sourcing',
      'Minimize rework and comebacks that consume labor without revenue',
      'Improve technician efficiency through training and better tools',
      'Balance workload across technicians to maximize overall output'
    ]
  },
  effective_labor_rate: {
    title: 'Effective Labor Rate',
    what: 'The actual revenue earned per billed labor hour. This is calculated from work order labor charges divided by billed hours. Compare this to your posted shop rate to identify discounting, warranty write-downs, or unbilled time. A healthy effective rate should be 85–95% of posted rate.',
    formula: 'Total Labor Revenue ÷ Total Billed Hours',
    actions: [
      'Reduce discounting and goodwill adjustments on labor charges',
      'Review warranty labor rates — negotiate higher reimbursement from OEMs',
      'Ensure all diagnostic and travel time is captured and billed',
      'Increase posted shop rate if market conditions support it',
      'Track effective rate by technician to identify training opportunities'
    ]
  },
  billed_hours_per_tech: {
    title: 'Billed Hours per Technician per Month',
    what: 'The average number of labor hours billed per technician per month. This measures technician utilization — how much of their available time is being converted to billable work. The Currie target is 130+ hours per month (approximately 75% utilization on a 40-hour week).',
    formula: 'Total Billed Hours ÷ Number of Months ÷ Active Technicians',
    actions: [
      'Improve dispatching to reduce travel time and gaps between jobs',
      'Ensure parts are staged and ready before technicians arrive',
      'Reduce administrative burden on technicians (paperwork, approvals)',
      'Cross-train technicians so more types of work can be assigned',
      'Track and address reasons for unbilled time (training, meetings, rework)'
    ]
  },
  service_calls_per_day: {
    title: 'Service Calls per Day',
    what: 'The average number of work orders opened per business day. This measures overall service demand and throughput. Tracking this helps identify seasonal patterns and capacity constraints.',
    formula: 'Total Work Orders Opened ÷ Business Days in Period',
    actions: [
      'Market PM programs to create predictable, recurring demand',
      'Offer emergency/priority service at premium rates to capture urgent work',
      'Expand service territory or add mobile units to reach more customers',
      'Improve scheduling to handle more calls without adding headcount',
      'Track by day-of-week to optimize staffing levels'
    ]
  },
  active_technicians: {
    title: 'Active Technicians',
    what: 'The number of technicians who have logged labor hours on work orders during the selected period. This is the denominator for all per-technician metrics and is critical for accurate benchmarking.',
    formula: 'Count of unique technicians with billed hours in the period',
    actions: [
      'Recruit and retain skilled technicians — the #1 constraint in most dealerships',
      'Invest in apprenticeship programs to build your own talent pipeline',
      'Offer competitive compensation packages including benefits and tool programs',
      'Create career paths (Tech I → II → III → Lead → Manager) to retain talent',
      'Track turnover rate and conduct exit interviews to address retention issues'
    ]
  },
  total_service_revenue: {
    title: 'Total Service Revenue',
    what: 'The total revenue generated by the service department during the selected period. This is a fully-loaded Currie model view that includes: Customer Labor (field, shop, PM), Parts Billed on Service WOs (road parts, shop parts, PM parts), Internal Labor, Warranty Labor, Sublet, Van Maintenance Recovery, and other service revenue. Parts billed on service work orders ARE included in both revenue and COGS — this is consistent with the Currie model, which measures service as a fully-loaded profit center.',
    formula: 'Sum of all service revenue GL accounts for the period (labor + parts + sublet + other)',
    actions: [
      'Grow PM contract base for predictable recurring revenue',
      'Increase labor rates annually to keep pace with cost increases',
      'Expand service offerings (field service, shop, emergency, installations)',
      'Improve customer retention through excellent service quality',
      'Target competitive accounts with superior response time and quality'
    ]
  },
  total_service_gp: {
    title: 'Total Service Gross Profit',
    what: 'The total gross profit (revenue minus direct costs) generated by the service department. Service COGS includes: Technician Labor (road, shop, PM), Parts Cost on Service WOs (road parts, shop parts, PM parts), Van Maintenance, Van Leases (Internal Rental to Service), Nonbillable Time, Warranty Costs, Rework, and Service Materials. Both parts revenue and parts costs are included on each side of the GP calculation — so the GP% correctly reflects the full service profit margin including parts.',
    formula: 'Total Service Revenue − Total Service COGS (labor + parts cost + van costs + warranty + nonbillable)',
    actions: [
      'Focus on both revenue growth AND cost control for maximum GP',
      'Review technician compensation structure to align with productivity',
      'Minimize warranty and goodwill write-offs',
      'Optimize parts markup on service jobs',
      'Reduce sublet costs by investing in capabilities to do work in-house'
    ]
  },
  absorption_rate: {
    title: 'Absorption Rate',
    what: 'Absorption rate measures whether your aftermarket departments (Service, Parts, Rental) generate enough gross profit to cover all of the dealership\'s overhead expenses. At 100%, your aftermarket GP fully "absorbs" your fixed costs — meaning every dollar of equipment sales GP is pure profit. The Currie target is 100%+.',
    formula: '(Service GP + Parts GP + Rental GP) ÷ Total Overhead Expenses × 100',
    actions: [
      'Increase service labor rates and improve technician utilization to boost Service GP',
      'Grow parts counter sales and improve parts margins through better vendor negotiations',
      'Maximize rental fleet utilization and review rental rates against market',
      'Scrutinize overhead expenses — reduce discretionary spending where possible',
      'Target 100%+ absorption so equipment sales become pure profit'
    ]
  },
  wo_throughput: {
    title: 'Work Order Throughput',
    what: 'The total number of work orders completed during the period. This measures the overall volume and capacity of your service department. Combined with revenue per WO, it helps identify whether growth should come from more volume or higher value per job.',
    formula: 'Count of work orders with labor entries in the period',
    actions: [
      'Streamline work order creation and closure processes',
      'Reduce cycle time on common repairs through standardized procedures',
      'Ensure adequate parts availability to prevent WO delays',
      'Optimize scheduling to maximize throughput without sacrificing quality',
      'Track WO aging to identify and resolve bottlenecks'
    ]
  },
  avg_revenue_per_wo: {
    title: 'Average Revenue per Work Order',
    what: 'The average total revenue generated per work order. This helps identify whether your service department is capturing full value on each job. Low averages may indicate missed upsell opportunities or underpricing.',
    formula: 'Total Service Revenue ÷ Total Work Orders',
    actions: [
      'Train technicians to perform thorough inspections and recommend additional work',
      'Implement multi-point inspection checklists on every work order',
      'Review pricing on common jobs to ensure full cost recovery plus margin',
      'Bundle related services (e.g., PM + inspection + fluid analysis)',
      'Track by service type to identify high-value vs. low-value work mix'
    ]
  },
};

// ─── KPI Help Button Component ─────────────────────────────────────────────────
const KpiHelpButton = ({ helpKey }) => {
  const [open, setOpen] = useState(false);
  const help = KPI_HELP[helpKey];
  if (!help) return null;

  return (
    <>
      <button
        onClick={(e) => { e.stopPropagation(); setOpen(true); }}
        className="absolute top-2 right-2 w-5 h-5 rounded-full bg-gray-200 hover:bg-gray-300 flex items-center justify-center text-gray-500 hover:text-gray-700 transition-colors z-10"
        title="Learn more"
      >
        <HelpCircle className="w-3.5 h-3.5" />
      </button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-blue-600" />
              {help.title}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-sm text-gray-700 mb-1">What does this measure?</h4>
              <p className="text-sm text-gray-600">{help.what}</p>
            </div>
            <div>
              <h4 className="font-semibold text-sm text-gray-700 mb-1">Formula</h4>
              <p className="text-sm text-gray-600 font-mono bg-gray-50 px-3 py-2 rounded">{help.formula}</p>
            </div>
            <div>
              <h4 className="font-semibold text-sm text-gray-700 mb-1">How to improve</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                {help.actions.map((action, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <ArrowUpRight className="w-3.5 h-3.5 text-green-500 mt-0.5 flex-shrink-0" />
                    {action}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

// ─── Status Badge ──────────────────────────────────────────────────────────────
const StatusBadge = ({ value, target }) => {
  const pct = target ? (value / target) * 100 : 0;
  if (pct >= 95) return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"><TrendingUp className="w-3 h-3 mr-1" />On Target</span>;
  if (pct >= 80) return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800"><TrendingDown className="w-3 h-3 mr-1" />Near Target</span>;
  return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"><TrendingDown className="w-3 h-3 mr-1" />Below Target</span>;
};

// ─── Formatters ────────────────────────────────────────────────────────────────
const formatCurrency = (value) => {
  if (value === null || value === undefined) return '$0';
  if (Math.abs(value) >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
  if (Math.abs(value) >= 1000) return `$${(value / 1000).toFixed(1)}K`;
  return `$${value.toFixed(0)}`;
};

const formatNumber = (value, decimals = 0) => {
  if (value === null || value === undefined) return '0';
  return value.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
};

const formatDateLabel = (dateStr) => {
  if (!dateStr) return '';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

// ─── Main Component ────────────────────────────────────────────────────────────
const CurrieService = ({ user, organization }) => {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [error, setError] = useState(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [dateLabel, setDateLabel] = useState('Trailing 12 Months');

  // Initialize with trailing 12 months
  useEffect(() => {
    setTrailing12();
  }, []);

  // Debounce date changes
  useEffect(() => {
    if (startDate && endDate) {
      const timer = setTimeout(() => {
        fetchData(startDate, endDate);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [startDate, endDate]);

  const setTrailing12 = () => {
    const now = new Date();
    const end = now.toISOString().split('T')[0];
    const start = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate() + 1).toISOString().split('T')[0];
    setStartDate(start);
    setEndDate(end);
    setDateLabel('Trailing 12 Months');
  };

  const setYTD = () => {
    const now = new Date();
    const end = now.toISOString().split('T')[0];
    const start = `${now.getFullYear()}-01-01`;
    setStartDate(start);
    setEndDate(end);
    setDateLabel(`YTD ${now.getFullYear()}`);
  };

  const setQuarter = (quarter, year) => {
    let start, end;
    switch (quarter) {
      case 1:
        start = `${year}-01-01`; end = `${year}-03-31`; break;
      case 2:
        start = `${year}-04-01`; end = `${year}-06-30`; break;
      case 3:
        start = `${year}-07-01`; end = `${year}-09-30`; break;
      case 4:
        start = `${year}-10-01`; end = `${year}-12-31`; break;
    }
    setStartDate(start);
    setEndDate(end);
    setDateLabel(`Q${quarter} ${year}`);
  };

  const handleDateChange = (field, value) => {
    if (field === 'start') setStartDate(value);
    else setEndDate(value);
    setDateLabel('Custom Range');
  };

  const fetchData = async (start, end) => {
    const sd = start || startDate;
    const ed = end || endDate;
    if (!sd || !ed) return;

    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');

      // Fetch Currie metrics
      const metricsResponse = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/currie/metrics`,
        {
          params: { start_date: sd, end_date: ed, refresh: 'true' },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setMetrics(metricsResponse.data.metrics);

      // Fetch service Currie benchmarks (monthly GP% trend)
      const benchmarkResponse = await axios.get(
        apiUrl('/api/reports/departments/service/currie-benchmarks'),
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setBenchmarkData(benchmarkResponse.data);
    } catch (err) {
      console.error('Error fetching Currie Service data:', err);
      setError(err.response?.data?.error || 'Failed to load Currie Service data');
    } finally {
      setLoading(false);
    }
  };

  // Calculate number of months in the selected range for per-month metrics
  const getMonthsInRange = () => {
    if (!startDate || !endDate) return 12;
    const start = new Date(startDate);
    const end = new Date(endDate);
    const months = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth()) + 1;
    return Math.max(1, months);
  };

  // Derived values
  const serviceGpPct = metrics?.dept_gp_benchmarks?.service?.gp_pct || 0;
  const serviceRevenue = metrics?.service_productivity?.total_service_revenue || 0;
  const serviceGp = metrics?.service_productivity?.total_service_gp || 0;
  const revenuePerTech = metrics?.service_productivity?.revenue_per_tech_monthly || 0;
  const gpPerTech = metrics?.service_productivity?.gp_per_tech_monthly || 0;
  const effectiveLaborRate = metrics?.labor_metrics?.average_labor_rate || 0;
  const billedHoursPerTech = metrics?.service_productivity?.hours_per_tech_monthly || 0;
  const callsPerDay = metrics?.service_calls_per_day?.calls_per_day || 0;
  const totalCalls = metrics?.service_calls_per_day?.total_service_calls || 0;
  const activeTechs = metrics?.technician_count?.active_technicians || 0;
  const technicianList = metrics?.technician_count?.technician_list || [];
  const totalBilledHours = metrics?.labor_metrics?.total_billed_hours || 0;
  const woWithLabor = metrics?.labor_metrics?.work_orders_with_labor || 0;
  const absorptionRate = metrics?.absorption_rate?.rate || 0;
  const monthsInRange = getMonthsInRange();

  // Chart data for GP% trend
  const chartData = benchmarkData?.monthly_data?.map(d => ({
    name: `${d.month} '${String(d.year).slice(-2)}`,
    gp_margin: d.gp_margin,
    revenue: d.revenue,
    currie_target: 65,
  })) || [];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Wrench className="w-6 h-6 text-blue-600" />
            Currie Service Metrics
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Key service department KPIs benchmarked against the Currie Financial Model — {dateLabel}
          </p>
        </div>
        <button
          onClick={() => fetchData()}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Date Range Selector */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => handleDateChange('start', e.target.value)}
              className="border border-gray-300 rounded px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => handleDateChange('end', e.target.value)}
              className="border border-gray-300 rounded px-3 py-2 text-sm"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={setTrailing12}
              disabled={loading}
              className={`px-3 py-2 rounded text-sm transition-all ${dateLabel === 'Trailing 12 Months' ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'} ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              T12
            </button>
            <button
              onClick={setYTD}
              disabled={loading}
              className={`px-3 py-2 rounded text-sm transition-all ${dateLabel.startsWith('YTD') ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'} ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              YTD
            </button>
            <button
              onClick={() => setQuarter(1, 2025)}
              disabled={loading}
              className={`px-3 py-2 rounded text-sm transition-all ${dateLabel === 'Q1 2025' ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'} ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              Q1 '25
            </button>
            <button
              onClick={() => setQuarter(2, 2025)}
              disabled={loading}
              className={`px-3 py-2 rounded text-sm transition-all ${dateLabel === 'Q2 2025' ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'} ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              Q2 '25
            </button>
            <button
              onClick={() => setQuarter(3, 2025)}
              disabled={loading}
              className={`px-3 py-2 rounded text-sm transition-all ${dateLabel === 'Q3 2025' ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'} ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              Q3 '25
            </button>
            <button
              onClick={() => setQuarter(4, 2025)}
              disabled={loading}
              className={`px-3 py-2 rounded text-sm transition-all ${dateLabel === 'Q4 2025' ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'} ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              Q4 '25
            </button>
            <button
              onClick={() => setQuarter(1, 2026)}
              disabled={loading}
              className={`px-3 py-2 rounded text-sm transition-all ${dateLabel === 'Q1 2026' ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'} ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              Q1 '26
            </button>
          </div>
        </div>
        {startDate && endDate && (
          <p className="text-xs text-gray-400 mt-2">
            Showing data from {formatDateLabel(startDate)} to {formatDateLabel(endDate)}
          </p>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {loading && !metrics ? (
        <div className="flex items-center justify-center py-20">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
          <span className="ml-3 text-gray-500">Loading Currie Service metrics...</span>
        </div>
      ) : metrics ? (
        <>
          {/* ─── Primary KPI Cards ─────────────────────────────────────────── */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Service GP% — the headline metric */}
            <Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-white">
              <CardContent className="pt-6 relative">
                <KpiHelpButton helpKey="service_gp_pct" />
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                    <Percent className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Service GP%</p>
                    <p className="text-3xl font-bold text-gray-900">{serviceGpPct.toFixed(1)}%</p>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">Currie Target: 65%</span>
                  <StatusBadge value={serviceGpPct} target={65} />
                </div>
              </CardContent>
            </Card>

            {/* Total Service Revenue */}
            <Card className="border-2 border-green-200 bg-gradient-to-br from-green-50 to-white">
              <CardContent className="pt-6 relative">
                <KpiHelpButton helpKey="total_service_revenue" />
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                    <DollarSign className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Total Service Revenue</p>
                    <p className="text-3xl font-bold text-gray-900">{formatCurrency(serviceRevenue)}</p>
                  </div>
                </div>
                <p className="text-xs text-gray-400">{dateLabel}</p>
              </CardContent>
            </Card>

            {/* Total Service GP */}
            <Card className="border-2 border-purple-200 bg-gradient-to-br from-purple-50 to-white">
              <CardContent className="pt-6 relative">
                <KpiHelpButton helpKey="total_service_gp" />
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Total Service GP</p>
                    <p className="text-3xl font-bold text-gray-900">{formatCurrency(serviceGp)}</p>
                  </div>
                </div>
                <p className="text-xs text-gray-400">{dateLabel}</p>
              </CardContent>
            </Card>
          </div>

          {/* ─── Technician Productivity Cards ─────────────────────────────── */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-600" />
                <CardTitle>Technician Productivity</CardTitle>
              </div>
              <CardDescription>Per-technician metrics benchmarked against Currie standards</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* Revenue per Tech */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center relative">
                  <KpiHelpButton helpKey="revenue_per_tech" />
                  <DollarSign className="w-5 h-5 text-blue-600 mx-auto mb-1" />
                  <p className="text-xs text-gray-500 mb-1">Revenue / Tech / Mo</p>
                  <p className="text-xl font-bold text-gray-900">{formatCurrency(revenuePerTech)}</p>
                  <p className="text-xs text-gray-400 mt-1">Currie: $20-25K</p>
                  <StatusBadge value={revenuePerTech} target={22500} />
                </div>

                {/* GP per Tech */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center relative">
                  <KpiHelpButton helpKey="gp_per_tech" />
                  <TrendingUp className="w-5 h-5 text-green-600 mx-auto mb-1" />
                  <p className="text-xs text-gray-500 mb-1">GP / Tech / Mo</p>
                  <p className="text-xl font-bold text-gray-900">{formatCurrency(gpPerTech)}</p>
                  <p className="text-xs text-gray-400 mt-1">Currie: ~$15K</p>
                  <StatusBadge value={gpPerTech} target={15000} />
                </div>

                {/* Effective Labor Rate */}
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center relative">
                  <KpiHelpButton helpKey="effective_labor_rate" />
                  <Gauge className="w-5 h-5 text-purple-600 mx-auto mb-1" />
                  <p className="text-xs text-gray-500 mb-1">Effective Labor Rate</p>
                  <p className="text-xl font-bold text-gray-900">{formatCurrency(effectiveLaborRate)}/hr</p>
                  <p className="text-xs text-gray-400 mt-1">{formatNumber(totalBilledHours, 0)} total hrs billed</p>
                </div>

                {/* Billed Hours per Tech */}
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 text-center relative">
                  <KpiHelpButton helpKey="billed_hours_per_tech" />
                  <Activity className="w-5 h-5 text-orange-600 mx-auto mb-1" />
                  <p className="text-xs text-gray-500 mb-1">Billed Hrs / Tech / Mo</p>
                  <p className="text-xl font-bold text-gray-900">{billedHoursPerTech?.toFixed(1) || '0.0'}</p>
                  <p className="text-xs text-gray-400 mt-1">Target: 130+ hrs/mo</p>
                  <StatusBadge value={billedHoursPerTech} target={130} />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* ─── Operations Cards ──────────────────────────────────────────── */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Wrench className="w-5 h-5 text-cyan-600" />
                <CardTitle>Service Operations</CardTitle>
              </div>
              <CardDescription>Work order volume, throughput, and absorption</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* Service Calls per Day */}
                <div className="bg-cyan-50 border border-cyan-200 rounded-lg p-4 text-center relative">
                  <KpiHelpButton helpKey="service_calls_per_day" />
                  <Wrench className="w-5 h-5 text-cyan-600 mx-auto mb-1" />
                  <p className="text-xs text-gray-500 mb-1">Service Calls / Day</p>
                  <p className="text-xl font-bold text-gray-900">{callsPerDay?.toFixed(1) || '0.0'}</p>
                  <p className="text-xs text-gray-400 mt-1">{formatNumber(totalCalls)} total calls</p>
                </div>

                {/* Active Technicians */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center relative">
                  <KpiHelpButton helpKey="active_technicians" />
                  <Users className="w-5 h-5 text-gray-600 mx-auto mb-1" />
                  <p className="text-xs text-gray-500 mb-1">Active Technicians</p>
                  <p className="text-xl font-bold text-gray-900">{activeTechs}</p>
                  <p className="text-xs text-gray-400 mt-1">WOs with labor: {formatNumber(woWithLabor)}</p>
                  {technicianList.length > 0 && (
                    <details className="mt-2 text-left">
                      <summary className="text-xs text-blue-600 cursor-pointer hover:underline text-center">View list</summary>
                      <ul className="mt-1 text-xs text-gray-600 space-y-0.5 max-h-40 overflow-y-auto">
                        {technicianList.map((name, i) => (
                          <li key={i} className="truncate">{name}</li>
                        ))}
                      </ul>
                    </details>
                  )}
                </div>

                {/* Work Order Throughput */}
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 text-center relative">
                  <KpiHelpButton helpKey="wo_throughput" />
                  <FileText className="w-5 h-5 text-indigo-600 mx-auto mb-1" />
                  <p className="text-xs text-gray-500 mb-1">Work Orders ({dateLabel === 'Trailing 12 Months' ? 'T12' : dateLabel})</p>
                  <p className="text-xl font-bold text-gray-900">{formatNumber(woWithLabor)}</p>
                  <p className="text-xs text-gray-400 mt-1">{formatNumber(woWithLabor / monthsInRange, 0)} avg/mo</p>
                </div>

                {/* Absorption Rate */}
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-center relative">
                  <KpiHelpButton helpKey="absorption_rate" />
                  <Target className="w-5 h-5 text-amber-600 mx-auto mb-1" />
                  <p className="text-xs text-gray-500 mb-1">Absorption Rate</p>
                  <p className="text-xl font-bold text-gray-900">{absorptionRate.toFixed(1)}%</p>
                  <p className="text-xs text-gray-400 mt-1">Currie Target: 100%</p>
                  <StatusBadge value={absorptionRate} target={100} />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* ─── Service GP% Trend Chart ───────────────────────────────────── */}
          {chartData.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-blue-600" />
                  <CardTitle>Service GP% Trend vs Currie Benchmark</CardTitle>
                </div>
                <CardDescription>Monthly service gross profit margin compared to the 65% Currie target</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                      <YAxis
                        yAxisId="left"
                        tick={{ fontSize: 12 }}
                        domain={[0, 100]}
                        label={{ value: 'GP %', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
                      />
                      <YAxis
                        yAxisId="right"
                        orientation="right"
                        tick={{ fontSize: 12 }}
                        tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`}
                        label={{ value: 'Revenue', angle: 90, position: 'insideRight', style: { fontSize: 12 } }}
                      />
                      <Tooltip
                        formatter={(value, name) => {
                          if (name === 'Revenue') return [`$${(value / 1000).toFixed(1)}K`, name];
                          return [`${value.toFixed(1)}%`, name];
                        }}
                      />
                      <Legend />
                      <ReferenceLine yAxisId="left" y={65} stroke="#ef4444" strokeDasharray="5 5" label={{ value: 'Currie 65%', position: 'right', fill: '#ef4444', fontSize: 11 }} />
                      <Bar yAxisId="right" dataKey="revenue" name="Revenue" fill="#93c5fd" radius={[4, 4, 0, 0]} />
                      <Line yAxisId="left" type="monotone" dataKey="gp_margin" name="GP %" stroke="#2563eb" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ─── Currie Benchmarks Reference Table ─────────────────────────── */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-gray-600" />
                <CardTitle>Currie Service Benchmarks Reference</CardTitle>
              </div>
              <CardDescription>Industry standards from the Currie Financial Model for service departments</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 px-3 font-medium text-gray-600">Metric</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-600">Your Value</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-600">Currie Target</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-600">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2 px-3">Service GP%</td>
                      <td className="py-2 px-3 text-right font-medium">{serviceGpPct.toFixed(1)}%</td>
                      <td className="py-2 px-3 text-right text-gray-500">65.0%</td>
                      <td className="py-2 px-3 text-right"><StatusBadge value={serviceGpPct} target={65} /></td>
                    </tr>
                    <tr className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2 px-3">Revenue / Tech / Month</td>
                      <td className="py-2 px-3 text-right font-medium">{formatCurrency(revenuePerTech)}</td>
                      <td className="py-2 px-3 text-right text-gray-500">$20K–$25K</td>
                      <td className="py-2 px-3 text-right"><StatusBadge value={revenuePerTech} target={22500} /></td>
                    </tr>
                    <tr className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2 px-3">GP / Tech / Month</td>
                      <td className="py-2 px-3 text-right font-medium">{formatCurrency(gpPerTech)}</td>
                      <td className="py-2 px-3 text-right text-gray-500">~$15K</td>
                      <td className="py-2 px-3 text-right"><StatusBadge value={gpPerTech} target={15000} /></td>
                    </tr>
                    <tr className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2 px-3">Billed Hours / Tech / Month</td>
                      <td className="py-2 px-3 text-right font-medium">{billedHoursPerTech?.toFixed(1) || '0.0'}</td>
                      <td className="py-2 px-3 text-right text-gray-500">130+ hrs</td>
                      <td className="py-2 px-3 text-right"><StatusBadge value={billedHoursPerTech} target={130} /></td>
                    </tr>
                    <tr className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2 px-3">Absorption Rate</td>
                      <td className="py-2 px-3 text-right font-medium">{absorptionRate.toFixed(1)}%</td>
                      <td className="py-2 px-3 text-right text-gray-500">100%+</td>
                      <td className="py-2 px-3 text-right"><StatusBadge value={absorptionRate} target={100} /></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
};

export default CurrieService;
