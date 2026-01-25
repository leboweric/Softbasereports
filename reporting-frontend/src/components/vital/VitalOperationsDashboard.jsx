import React, { useState, useEffect, useCallback } from 'react';
import {
  Settings, RefreshCw, Clock, CheckCircle, Users, TrendingUp, Target,
  AlertTriangle, BarChart3, Activity, Gauge, ArrowLeft, Calendar
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const MetricCard = ({ title, value, subtitle, icon: Icon, trend, color = 'emerald', onClick }) => (
  <div 
    className={`bg-white rounded-xl shadow-sm border border-gray-100 p-6 ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`}
    onClick={onClick}
  >
    <div className="flex items-center justify-between mb-2">
      <span className="text-sm font-medium text-gray-600">{title}</span>
      {Icon && <Icon className={`h-5 w-5 text-${color}-500`} />}
    </div>
    <div className="flex items-baseline gap-2">
      <span className="text-2xl font-bold text-gray-900">{value}</span>
      {trend && (
        <span className={`text-sm ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
        </span>
      )}
    </div>
    {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
  </div>
);

const VitalOperationsDashboard = ({ onBack }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [capacityData, setCapacityData] = useState(null);
  const [slaData, setSlaData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [sentimentData, setSentimentData] = useState(null);
  const [timeframe, setTimeframe] = useState(90);

  const fetchData = useCallback(async (refresh = false) => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
      
      const refreshParam = refresh ? '&refresh=true' : '';
      
      const [dashboardRes, capacityRes, slaRes, forecastRes, sentimentRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/vital/operations/dashboard?days=${timeframe}${refreshParam}`, { headers }),
        fetch(`${API_BASE_URL}/api/vital/operations/capacity?days=${timeframe}${refreshParam}`, { headers }),
        fetch(`${API_BASE_URL}/api/vital/operations/sla-compliance?days=${timeframe}${refreshParam}`, { headers }),
        fetch(`${API_BASE_URL}/api/vital/forecasting/demand${refreshParam ? '?refresh=true' : ''}`, { headers }),
        fetch(`${API_BASE_URL}/api/vital/sentiment/dashboard?days=${timeframe}${refreshParam}`, { headers })
      ]);
      
      if (dashboardRes.ok) {
        const data = await dashboardRes.json();
        setDashboardData(data);
      }
      
      if (capacityRes.ok) {
        const data = await capacityRes.json();
        setCapacityData(data);
      }
      
      if (slaRes.ok) {
        const data = await slaRes.json();
        setSlaData(data);
      }
      
      if (forecastRes.ok) {
        const data = await forecastRes.json();
        setForecastData(data);
      }
      
      if (sentimentRes.ok) {
        const data = await sentimentRes.json();
        setSentimentData(data);
      }
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [timeframe]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const overview = dashboardData?.overview || {};
  const forecast = forecastData?.forecast || {};
  const statistics = forecastData?.statistics || {};
  const sentiment = sentimentData?.overview || {};

  // Prepare chart data
  const throughputData = (dashboardData?.daily_throughput || []).slice(-30);
  const tatDistribution = dashboardData?.tat_distribution || [];
  const qualityByType = dashboardData?.quality_by_case_type || [];
  const workloadData = dashboardData?.case_manager_workload || [];
  
  // Combine historical and forecast data
  const forecastChartData = [
    ...(forecastData?.historical?.weekly || []).slice(-12).map(w => ({
      ...w,
      type: 'actual'
    })),
    ...(forecast.weekly || []).map(w => ({
      week_start: w.week_start,
      cases: w.forecasted_cases,
      type: 'forecast',
      lower: w.lower_bound,
      upper: w.upper_bound
    }))
  ];

  // Sentiment distribution for pie chart
  const sentimentDistribution = [
    { name: 'Positive', value: sentiment.positive_count || 0, color: '#10b981' },
    { name: 'Neutral', value: sentiment.neutral_count || 0, color: '#6b7280' },
    { name: 'Negative', value: sentiment.negative_count || 0, color: '#ef4444' }
  ].filter(s => s.value > 0);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          {onBack && (
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600" />
            </button>
          )}
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Settings className="h-7 w-7 text-orange-500" />
              Operational Efficiency
            </h1>
            <p className="text-gray-600">Resource utilization, SLA compliance, and demand forecasting</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500"
          >
            <option value={30}>Last 30 days</option>
            <option value={60}>Last 60 days</option>
            <option value={90}>Last 90 days</option>
            <option value={180}>Last 6 months</option>
          </select>
          <button
            onClick={() => fetchData(true)}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Efficiency Score Banner */}
      <div className="bg-gradient-to-r from-orange-500 to-amber-500 rounded-xl p-6 mb-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-medium opacity-90">Overall Efficiency Score</h2>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-5xl font-bold">{overview.efficiency_score || 0}</span>
              <span className="text-xl opacity-80">/ 100</span>
            </div>
            <p className="mt-2 opacity-80">Based on close rate, satisfaction, NPS, and response time</p>
          </div>
          <Gauge className="h-20 w-20 opacity-30" />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard
          title="Close Rate"
          value={`${overview.close_rate || 0}%`}
          subtitle="Cases resolved"
          icon={CheckCircle}
          color="green"
        />
        <MetricCard
          title="Avg Time to First Session"
          value={`${overview.avg_time_to_first_session || 0} days`}
          subtitle="From contact to session"
          icon={Clock}
          color="blue"
        />
        <MetricCard
          title="Avg Satisfaction"
          value={overview.avg_satisfaction?.toFixed(2) || '0'}
          subtitle="Out of 5.0"
          icon={Target}
          color="purple"
        />
        <MetricCard
          title="Active Case Managers"
          value={capacityData?.case_manager_utilization?.length || 0}
          subtitle={`${capacityData?.avg_cases_per_manager || 0} cases/manager avg`}
          icon={Users}
          color="orange"
        />
      </div>

      {/* SLA Compliance */}
      {slaData && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Target className="h-5 w-5 text-orange-500" />
            SLA Compliance
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">First Session within {slaData.sla_thresholds?.first_session_days} days</span>
                <span className="text-lg font-bold text-gray-900">{slaData.overall?.first_session_compliance}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className={`h-3 rounded-full ${slaData.overall?.first_session_compliance >= 80 ? 'bg-green-500' : slaData.overall?.first_session_compliance >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${Math.min(slaData.overall?.first_session_compliance || 0, 100)}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Case Closed within {slaData.sla_thresholds?.case_close_days} days</span>
                <span className="text-lg font-bold text-gray-900">{slaData.overall?.close_time_compliance}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className={`h-3 rounded-full ${slaData.overall?.close_time_compliance >= 80 ? 'bg-green-500' : slaData.overall?.close_time_compliance >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${Math.min(slaData.overall?.close_time_compliance || 0, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Daily Throughput */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Activity className="h-5 w-5 text-orange-500" />
            Daily Throughput
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={throughputData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="opened" name="Opened" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              <Area type="monotone" dataKey="closed" name="Closed" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* TAT Distribution */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Clock className="h-5 w-5 text-orange-500" />
            Time to First Session Distribution
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={tatDistribution} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="bucket" type="category" width={80} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#f97316" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Demand Forecast */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-orange-500" />
            Demand Forecast
          </h3>
          <div className="flex items-center gap-4 text-sm">
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
              Actual
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 bg-orange-500 rounded-full"></span>
              Forecast
            </span>
            <span className={`px-2 py-1 rounded ${statistics.trend_direction === 'increasing' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              {statistics.trend_direction === 'increasing' ? '↑' : '↓'} {statistics.trend_direction}
            </span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={forecastChartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="week_start" tick={{ fontSize: 10 }} />
            <YAxis />
            <Tooltip />
            <Line 
              type="monotone" 
              dataKey="cases" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={(props) => {
                const { cx, cy, payload } = props;
                if (payload.type === 'forecast') {
                  return <circle cx={cx} cy={cy} r={4} fill="#f97316" stroke="#f97316" />;
                }
                return <circle cx={cx} cy={cy} r={3} fill="#3b82f6" stroke="#3b82f6" />;
              }}
            />
          </LineChart>
        </ResponsiveContainer>
        <div className="mt-4 grid grid-cols-3 gap-4 text-center">
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Avg Weekly Volume</p>
            <p className="text-xl font-bold text-gray-900">{statistics.avg_weekly_volume || 0}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Std Deviation</p>
            <p className="text-xl font-bold text-gray-900">±{statistics.weekly_std_dev || 0}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Trend Strength</p>
            <p className="text-xl font-bold text-gray-900">{statistics.trend_strength || 0}</p>
          </div>
        </div>
      </div>

      {/* Sentiment Analysis */}
      {sentimentData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Sentiment Distribution</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={sentimentDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {sentimentDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Keywords from Feedback</h3>
            <div className="flex flex-wrap gap-2">
              {(sentimentData?.top_keywords || []).slice(0, 20).map((kw, idx) => (
                <span 
                  key={idx}
                  className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm"
                  style={{ fontSize: `${Math.max(12, Math.min(18, 10 + kw.count / 5))}px` }}
                >
                  {kw.word} ({kw.count})
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Case Manager Workload */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Users className="h-5 w-5 text-orange-500" />
          Case Manager Workload
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-medium text-gray-600">Case Manager</th>
                <th className="text-right py-3 px-4 font-medium text-gray-600">Total Cases</th>
                <th className="text-right py-3 px-4 font-medium text-gray-600">Open Cases</th>
                <th className="text-right py-3 px-4 font-medium text-gray-600">Avg Close Time</th>
                <th className="text-right py-3 px-4 font-medium text-gray-600">Avg Satisfaction</th>
              </tr>
            </thead>
            <tbody>
              {workloadData.slice(0, 10).map((cm, idx) => (
                <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 font-medium text-gray-900">{cm.case_manager || 'Unknown'}</td>
                  <td className="py-3 px-4 text-right">{cm.total_cases}</td>
                  <td className="py-3 px-4 text-right">{cm.open_cases}</td>
                  <td className="py-3 px-4 text-right">{cm.avg_close_time} days</td>
                  <td className="py-3 px-4 text-right">
                    <span className={`px-2 py-1 rounded ${cm.avg_satisfaction >= 4 ? 'bg-green-100 text-green-700' : cm.avg_satisfaction >= 3 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
                      {cm.avg_satisfaction?.toFixed(2) || 'N/A'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Quality by Case Type */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-orange-500" />
          Service Quality by Case Type
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={qualityByType.slice(0, 8)} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" domain={[0, 5]} />
            <YAxis dataKey="case_type" type="category" width={150} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="avg_satisfaction" name="Avg Satisfaction" fill="#10b981" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default VitalOperationsDashboard;
