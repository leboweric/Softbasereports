import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { apiUrl } from '@/lib/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend, ComposedChart, Line } from 'recharts'
import { Users, TrendingUp, Star, CheckCircle, XCircle, RefreshCw, ArrowLeft, Activity, Heart } from 'lucide-react'

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#84cc16']
const formatNumber = (value) => { if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M'; if (value >= 1000) return (value / 1000).toFixed(0) + 'K'; return value?.toLocaleString() || '0' }

const MetricCard = ({ title, value, subtitle, icon: Icon, color = 'green' }) => {
  const colorClasses = { green: 'bg-green-50 text-green-600', blue: 'bg-blue-50 text-blue-600', purple: 'bg-purple-50 text-purple-600', amber: 'bg-amber-50 text-amber-600', red: 'bg-red-50 text-red-600', teal: 'bg-teal-50 text-teal-600' }
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-sm text-gray-500 font-medium">{title}</p>
            <p className="text-2xl font-bold mt-1">{value}</p>
            {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
          </div>
          {Icon && <div className={`p-2 rounded-lg ${colorClasses[color]}`}><Icon className="h-5 w-5" /></div>}
        </div>
      </CardContent>
    </Card>
  )
}

const VitalProviderNetworkDashboard = ({ user, onBack }) => {
  const [loading, setLoading] = useState(true)
  const [overview, setOverview] = useState(null)
  const [topProviders, setTopProviders] = useState([])
  const [byType, setByType] = useState([])
  const [satisfactionDist, setSatisfactionDist] = useState([])
  const [modality, setModality] = useState(null)
  const [monthlyTrend, setMonthlyTrend] = useState([])
  const [outcomes, setOutcomes] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [error, setError] = useState(null)
  const [timeframe, setTimeframe] = useState(365)

  const fetchData = async (refresh = false) => {
    setLoading(true); setError(null)
    try {
      const token = localStorage.getItem('token')
      const headers = { 'Authorization': 'Bearer ' + token }
      const params = '?days=' + timeframe + (refresh ? '&refresh=true' : '')
      
      const [overviewRes, providersRes, typeRes, satRes, modalityRes, trendRes, outcomesRes] = await Promise.all([
        fetch(apiUrl + '/api/vital/provider-network/overview' + params, { headers }),
        fetch(apiUrl + '/api/vital/provider-network/top-providers' + params, { headers }),
        fetch(apiUrl + '/api/vital/provider-network/by-type' + params, { headers }),
        fetch(apiUrl + '/api/vital/provider-network/satisfaction-distribution' + params, { headers }),
        fetch(apiUrl + '/api/vital/provider-network/modality-breakdown' + params, { headers }),
        fetch(apiUrl + '/api/vital/provider-network/monthly-trend' + params, { headers }),
        fetch(apiUrl + '/api/vital/provider-network/outcomes' + params, { headers })
      ])
      
      if (overviewRes.ok) { const d = await overviewRes.json(); setOverview(d.overview) }
      if (providersRes.ok) { const d = await providersRes.json(); setTopProviders(d.providers || []) }
      if (typeRes.ok) { const d = await typeRes.json(); setByType(d.by_type || []) }
      if (satRes.ok) { const d = await satRes.json(); setSatisfactionDist(d.distribution || []) }
      if (modalityRes.ok) { const d = await modalityRes.json(); setModality(d.modality) }
      if (trendRes.ok) { const d = await trendRes.json(); setMonthlyTrend(d.trend || []) }
      if (outcomesRes.ok) { const d = await outcomesRes.json(); setOutcomes(d.outcomes) }
      
      setLastUpdated(new Date().toLocaleTimeString())
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchData() }, [timeframe])

  if (loading && !overview) return <div className="flex items-center justify-center h-64"><LoadingSpinner /><span className="ml-3 text-gray-600">Loading provider network data...</span></div>

  const typeChartData = byType.map((t, i) => ({ name: t.type, sessions: t.sessions, providers: t.providers, fill: COLORS[i % COLORS.length] }))
  const satChartData = satisfactionDist.map((s, i) => ({ name: s.tier, value: s.count, fill: COLORS[i % COLORS.length] }))
  const modalityChartData = modality ? [{ name: 'Virtual', value: modality.virtual_sessions, fill: '#3b82f6' }, { name: 'In-Person', value: modality.in_person_sessions, fill: '#10b981' }] : []

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-4">
          {onBack && <Button variant="ghost" size="sm" onClick={onBack}><ArrowLeft className="h-4 w-4 mr-2" />Back</Button>}
          <div><h1 className="text-3xl font-bold tracking-tight text-gray-900">Provider Network</h1><p className="text-gray-600">Provider utilization, satisfaction, and clinical outcomes</p></div>
        </div>
        <div className="flex items-center gap-3">
          <select value={timeframe} onChange={(e) => setTimeframe(Number(e.target.value))} className="border rounded-lg px-3 py-2 text-sm">
            <option value={90}>Last 90 days</option>
            <option value={180}>Last 6 months</option>
            <option value={365}>Last 12 months</option>
            <option value={730}>Last 2 years</option>
          </select>
          <span className="text-sm text-gray-500">Updated: {lastUpdated}</span>
          <Button variant="outline" size="sm" onClick={() => fetchData(true)} className="flex items-center gap-2"><RefreshCw className="h-4 w-4" />Refresh</Button>
        </div>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">Error: {error}</div>}

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
        <MetricCard title="Total Providers" value={formatNumber(overview?.total_providers)} subtitle="Active network" icon={Users} color="blue" />
        <MetricCard title="Total Sessions" value={formatNumber(overview?.total_sessions)} subtitle="Period total" icon={Activity} color="green" />
        <MetricCard title="Completed" value={formatNumber(overview?.completed_sessions)} subtitle="Sessions" icon={CheckCircle} color="green" />
        <MetricCard title="Cancelled" value={formatNumber(overview?.cancelled_sessions)} subtitle="Sessions" icon={XCircle} color="red" />
        <MetricCard title="Completion Rate" value={(overview?.completion_rate || 0) + '%'} subtitle="Sessions completed" icon={TrendingUp} color="teal" />
        <MetricCard title="Avg Satisfaction" value={(overview?.avg_satisfaction || 0).toFixed(1)} subtitle="Out of 5.0" icon={Star} color="amber" />
        <MetricCard title="Avg NPS" value={(overview?.avg_nps || 0).toFixed(0)} subtitle="Net Promoter" icon={Heart} color="purple" />
        <MetricCard title="Orgs Served" value={formatNumber(overview?.organizations_served)} subtitle="Clients" icon={Users} color="blue" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><Activity className="h-5 w-5 text-blue-600" />Sessions by Provider Type</CardTitle></CardHeader>
          <CardContent>{typeChartData.length > 0 ? <ResponsiveContainer width="100%" height={250}><BarChart data={typeChartData} layout="vertical"><CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" /><XAxis type="number" tick={{ fontSize: 12 }} /><YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} /><Tooltip /><Bar dataKey="sessions" name="Sessions" fill="#3b82f6" radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer> : <div className="h-64 flex items-center justify-center text-gray-500">No data</div>}</CardContent>
        </Card>
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><Star className="h-5 w-5 text-amber-600" />Provider Satisfaction Distribution</CardTitle></CardHeader>
          <CardContent>{satChartData.length > 0 ? <ResponsiveContainer width="100%" height={250}><PieChart><Pie data={satChartData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2} dataKey="value" label={({ name, percent }) => name.split(' ')[0] + ' ' + (percent * 100).toFixed(0) + '%'}>{satChartData.map((entry, index) => <Cell key={'cell-' + index} fill={entry.fill} />)}</Pie><Tooltip /><Legend /></PieChart></ResponsiveContainer> : <div className="h-64 flex items-center justify-center text-gray-500">No data</div>}</CardContent>
        </Card>
      </div>

      <Card><CardHeader><CardTitle className="flex items-center gap-2"><TrendingUp className="h-5 w-5 text-green-600" />Monthly Provider Activity</CardTitle></CardHeader>
        <CardContent>{monthlyTrend.length > 0 ? <ResponsiveContainer width="100%" height={300}><ComposedChart data={monthlyTrend}><CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" /><XAxis dataKey="month" tick={{ fontSize: 12 }} /><YAxis yAxisId="left" tick={{ fontSize: 12 }} /><YAxis yAxisId="right" orientation="right" domain={[0, 5]} tick={{ fontSize: 12 }} /><Tooltip /><Legend /><Bar yAxisId="left" dataKey="sessions" name="Sessions" fill="#10b981" radius={[4, 4, 0, 0]} /><Line yAxisId="right" type="monotone" dataKey="satisfaction" name="Satisfaction" stroke="#f59e0b" strokeWidth={2} dot={false} /></ComposedChart></ResponsiveContainer> : <div className="h-64 flex items-center justify-center text-gray-500">No data</div>}</CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><Activity className="h-5 w-5 text-purple-600" />Session Modality</CardTitle></CardHeader>
          <CardContent>{modalityChartData.length > 0 ? <div><ResponsiveContainer width="100%" height={200}><PieChart><Pie data={modalityChartData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2} dataKey="value" label={({ name, percent }) => name + ' ' + (percent * 100).toFixed(0) + '%'}>{modalityChartData.map((entry, index) => <Cell key={'cell-' + index} fill={entry.fill} />)}</Pie><Tooltip /><Legend /></PieChart></ResponsiveContainer><div className="grid grid-cols-2 gap-4 mt-4"><div className="bg-blue-50 rounded-lg p-3 text-center"><p className="text-sm text-blue-600 font-medium">Virtual</p><p className="text-xl font-bold text-blue-900">{formatNumber(modality?.virtual_sessions)}</p><p className="text-xs text-blue-500">{modality?.virtual_pct}%</p></div><div className="bg-green-50 rounded-lg p-3 text-center"><p className="text-sm text-green-600 font-medium">In-Person</p><p className="text-xl font-bold text-green-900">{formatNumber(modality?.in_person_sessions)}</p><p className="text-xs text-green-500">{modality?.in_person_pct}%</p></div></div></div> : <div className="h-64 flex items-center justify-center text-gray-500">No data</div>}</CardContent>
        </Card>
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><Heart className="h-5 w-5 text-red-600" />Clinical Outcomes</CardTitle></CardHeader>
          <CardContent>{outcomes ? <div className="space-y-4"><div className="grid grid-cols-2 gap-4"><div className="bg-green-50 rounded-lg p-4"><p className="text-sm text-green-600 font-medium">Goals Met</p><p className="text-2xl font-bold text-green-900">{outcomes.goals_met_pct}%</p><p className="text-xs text-green-500">{formatNumber(outcomes.goals_met)} cases</p></div><div className="bg-blue-50 rounded-lg p-4"><p className="text-sm text-blue-600 font-medium">Well-Being Improvement</p><p className="text-2xl font-bold text-blue-900">+{outcomes.wellbeing_improvement?.toFixed(1)}</p><p className="text-xs text-blue-500">Pre: {outcomes.pre_wellbeing?.toFixed(1)} to Post: {outcomes.post_wellbeing?.toFixed(1)}</p></div></div><div className="bg-purple-50 rounded-lg p-4"><p className="text-sm text-purple-600 font-medium">Avg Impact on Well-Being</p><p className="text-xl font-bold text-purple-900">{outcomes.avg_wellbeing_impact?.toFixed(2)}</p></div></div> : <div className="h-48 flex items-center justify-center text-gray-500">No data</div>}</CardContent>
        </Card>
      </div>

      <Card><CardHeader><CardTitle className="flex items-center gap-2"><Users className="h-5 w-5 text-teal-600" />Top Providers by Session Volume</CardTitle></CardHeader>
        <CardContent>{topProviders.length > 0 ? <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="text-left p-2 font-medium text-gray-600">Provider</th><th className="text-left p-2 font-medium text-gray-600">Type</th><th className="text-right p-2 font-medium text-gray-600">Sessions</th><th className="text-right p-2 font-medium text-gray-600">Satisfaction</th><th className="text-right p-2 font-medium text-gray-600">NPS</th><th className="text-right p-2 font-medium text-gray-600">Clients</th></tr></thead><tbody>{topProviders.slice(0, 15).map((p, idx) => <tr key={idx} className="border-b hover:bg-gray-50"><td className="p-2 font-medium">{p.name}</td><td className="p-2 text-gray-600">{p.type}</td><td className="p-2 text-right">{formatNumber(p.sessions)}</td><td className="p-2 text-right"><span className={p.satisfaction >= 4.5 ? 'text-green-600 font-medium' : p.satisfaction >= 4 ? 'text-blue-600' : 'text-amber-600'}>{p.satisfaction?.toFixed(1)}</span></td><td className="p-2 text-right">{p.nps?.toFixed(0)}</td><td className="p-2 text-right">{p.clients}</td></tr>)}</tbody></table></div> : <div className="h-48 flex items-center justify-center text-gray-500">No data</div>}</CardContent>
      </Card>
    </div>
  )
}

export default VitalProviderNetworkDashboard
