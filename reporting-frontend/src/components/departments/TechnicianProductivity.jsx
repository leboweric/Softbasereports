import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AlertCircle, ChevronDown, ChevronRight, RefreshCw, TrendingUp, TrendingDown, Minus, Info, Settings, Save, X, DollarSign } from 'lucide-react'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip'
import { apiUrl } from '@/lib/api'
import { CfoMethodologyCard } from '@/components/ui/cfo-methodology-card'

// ─── Currie Model Targets ──────────────────────────────────────────────────────
const CURRIE_APPLICATION  = 85
const CURRIE_EFFICIENCY   = 100
const CURRIE_PRODUCTIVITY = 85
const AMBER_TOLERANCE     = 5   // percentage points below target before turning amber

// ─── KPI Card Tooltip Definitions ────────────────────────────────────────────
const METRIC_TOOLTIPS = {
  application: {
    title: 'Application Rate',
    formula: 'Applied Hours ÷ Hours Paid',
    description: 'Of every hour you paid a technician, how many were actually spent working on a job? A tech clocked in for 40 hours but only on jobs for 34 of them has 85% Application. Time lost to training, shop meetings, idle time, and admin all reduce this number. Currie target: ≥ 85%.'
  },
  efficiency: {
    title: 'Efficiency Rate',
    formula: 'Billed Hours ÷ Applied Hours',
    description: 'Of the hours a tech spent on jobs, how many were actually billed to a customer? Hours written off for warranty, goodwill, or rework count as Applied but not Billed — dragging Efficiency down. Above 100% is possible with flat-rate billing. Currie target: ≥ 100%.'
  },
  productivity: {
    title: 'Productivity Rate',
    formula: 'Billed Hours ÷ Hours Paid  (= Application × Efficiency)',
    description: 'The single bottom-line number: of every hour you paid for, how many generated billable revenue? This is the metric most directly tied to profitability and is the primary number used in performance reviews. Currie target: ≥ 85%.'
  },
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
const fmt1 = (n) => (n == null ? '—' : n.toFixed(1))
const fmt2 = (n) => (n == null ? '—' : n.toFixed(2))
const fmtPct = (n) => (n == null ? '—' : `${n.toFixed(1)}%`)
const fmtCurrency = (n) => (n == null ? '—' : `$${Number(n).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`)

function getZone(value, target) {
  if (value == null) return 'gray'
  if (value >= target) return 'green'
  if (value >= target - AMBER_TOLERANCE) return 'amber'
  return 'red'
}

// True GP zone: green ≥ 0, amber = small negative (within 10%), red = deeply negative
function getTrueGpZone(gpPct) {
  if (gpPct == null) return 'gray'
  if (gpPct >= 0) return 'green'
  if (gpPct >= -10) return 'amber'
  return 'red'
}

const ZONE_TEXT   = { green: 'text-green-700',  amber: 'text-amber-600',  red: 'text-red-600',  gray: 'text-muted-foreground' }
const ZONE_BG     = { green: 'bg-green-50',      amber: 'bg-amber-50',     red: 'bg-red-50',     gray: '' }
const ZONE_BADGE  = { green: 'bg-green-100 text-green-700', amber: 'bg-amber-100 text-amber-700', red: 'bg-red-100 text-red-600', gray: 'bg-gray-100 text-gray-500' }
const ZONE_BAR    = { green: 'bg-green-500',     amber: 'bg-amber-400',    red: 'bg-red-500',    gray: 'bg-gray-300' }
const ZONE_BORDER = { green: 'border-green-300', amber: 'border-amber-300',red: 'border-red-300', gray: 'border-gray-200' }
const ZONE_CARD   = { green: 'bg-green-50',      amber: 'bg-amber-50',     red: 'bg-red-50',     gray: 'bg-gray-50' }

function MetricBadge({ value, target, label }) {
  if (value == null) return <span className="text-muted-foreground text-sm">—</span>
  const zone = getZone(value, target)
  const diff = value - target
  const Icon = zone === 'green' ? TrendingUp : (zone === 'amber' ? Minus : TrendingDown)
  return (
    <div className={`flex flex-col items-center gap-0.5 ${ZONE_TEXT[zone]}`}>
      <div className="flex items-center gap-1">
        <Icon className="h-4 w-4" />
        <span className="text-2xl font-bold">{fmtPct(value)}</span>
      </div>
      <span className="text-xs font-medium">{label}</span>
      <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${ZONE_BADGE[zone]}`}>
        Target {fmtPct(target)} {diff >= 0 ? `+${diff.toFixed(1)}%` : `${diff.toFixed(1)}%`}
      </span>
    </div>
  )
}

function StatusCell({ value, target, gpMode = false }) {
  if (value == null) return <td className="px-3 py-2 text-center text-muted-foreground text-sm">—</td>
  const zone = gpMode ? getTrueGpZone(value) : getZone(value, target)
  return (
    <td className={`px-3 py-2 text-center font-semibold text-sm ${ZONE_TEXT[zone]} ${ZONE_BG[zone]}`}>
      {fmtPct(value)}
    </td>
  )
}

// ─── Main Component ────────────────────────────────────────────────────────────
const TechnicianProductivity = ({ user }) => {
  const today = new Date()
  const firstOfYear = new Date(today.getFullYear(), 0, 1)
  const fmt = (d) => d.toISOString().split('T')[0]

  // Report data
  const [startDate, setStartDate] = useState(fmt(firstOfYear))
  const [endDate, setEndDate]     = useState(fmt(today))
  const [data, setData]           = useState(null)
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)
  const [expanded, setExpanded]   = useState({})

  // Wage rate config panel
  const [showConfig, setShowConfig]     = useState(false)
  const [wageRates, setWageRates]       = useState([])   // [{techName, fullyLoadedRate, notes, id}]
  const [wageEdits, setWageEdits]       = useState({})   // techName -> rate string being edited
  const [wageNotes, setWageNotes]       = useState({})   // techName -> notes string
  const [savingWages, setSavingWages]   = useState(false)
  const [wageSaveMsg, setWageSaveMsg]   = useState(null)
  const [wageError, setWageError]       = useState(null)

  useEffect(() => { fetchData() }, [])

  const fetchData = async (forceRefresh = false) => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const url = apiUrl(
        `/api/reports/departments/service/technician-productivity?start_date=${startDate}&end_date=${endDate}${forceRefresh ? '&refresh=true' : ''}`
      )
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const json = await res.json()
      setData(json)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // Load existing wage rates when config panel opens
  const loadWageRates = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch(apiUrl('/api/tech-wage-rates/'), {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) throw new Error(`Failed to load rates: ${res.status}`)
      const json = await res.json()
      const rates = json.rates || []
      setWageRates(rates)
      // Pre-populate edit fields from saved rates
      const edits = {}
      const notes = {}
      rates.forEach(r => {
        edits[r.techName] = r.fullyLoadedRate != null ? String(r.fullyLoadedRate) : ''
        notes[r.techName] = r.notes || ''
      })
      setWageEdits(edits)
      setWageNotes(notes)
    } catch (e) {
      setWageError(e.message)
    }
  }, [])

  const openConfig = () => {
    setShowConfig(true)
    setWageSaveMsg(null)
    setWageError(null)
    loadWageRates()
  }

  const saveWageRates = async () => {
    setSavingWages(true)
    setWageSaveMsg(null)
    setWageError(null)
    try {
      const token = localStorage.getItem('token')
      // Build list from all techs in current report + any already saved
      const techNames = new Set([
        ...(data?.technicians || []).map(t => t.techName),
        ...wageRates.map(r => r.techName),
      ])
      const ratesList = []
      techNames.forEach(name => {
        const rateStr = (wageEdits[name] || '').trim()
        const rate = parseFloat(rateStr)
        if (!isNaN(rate) && rate >= 0) {
          ratesList.push({
            techName: name,
            fullyLoadedRate: rate,
            notes: wageNotes[name] || null,
            isActive: true,
          })
        }
      })
      const res = await fetch(apiUrl('/api/tech-wage-rates/bulk'), {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ rates: ratesList }),
      })
      if (!res.ok) throw new Error(`Save failed: ${res.status}`)
      const json = await res.json()
      setWageSaveMsg(`Saved ${ratesList.length} wage rates. Re-run the report to see updated profitability.`)
      // Reload to get fresh data
      await loadWageRates()
    } catch (e) {
      setWageError(e.message)
    } finally {
      setSavingWages(false)
    }
  }

  const toggleExpand = (name) => setExpanded(prev => ({ ...prev, [name]: !prev[name] }))

  const dept  = data?.department    || {}
  const techs = data?.technicians   || []
  const hasWageRates = data?.wageRatesConfigured === true

  // All tech names for the config panel (union of report + saved)
  const configTechNames = showConfig
    ? [...new Set([
        ...(data?.technicians || []).map(t => t.techName),
        ...wageRates.map(r => r.techName),
      ])].sort()
    : []

  return (
    <div className="space-y-6">

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-end gap-4">
        <div>
          <h2 className="text-xl font-bold">Technician Productivity</h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Currie model: Application × Efficiency = Productivity
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-3 md:ml-auto">
          <div>
            <Label className="text-xs">Start Date</Label>
            <Input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} className="h-8 text-sm w-36" />
          </div>
          <div>
            <Label className="text-xs">End Date</Label>
            <Input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} className="h-8 text-sm w-36" />
          </div>
          <Button onClick={() => fetchData()} disabled={loading} className="h-8 text-sm">
            {loading ? 'Loading…' : 'Run'}
          </Button>
          <Button variant="outline" size="sm" className="h-8" onClick={() => fetchData(true)} disabled={loading} title="Force refresh cache">
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-8 gap-1.5"
            onClick={showConfig ? () => setShowConfig(false) : openConfig}
          >
            {showConfig ? <X className="h-3.5 w-3.5" /> : <Settings className="h-3.5 w-3.5" />}
            {showConfig ? 'Close Config' : 'Configure Wage Rates'}
          </Button>
        </div>
      </div>

      {/* ── Error ───────────────────────────────────────────────────────── */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Configure Wage Rates Panel ───────────────────────────────────── */}
      {showConfig && (
        <Card className="border-blue-200 bg-blue-50/40">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-blue-600" />
              Configure Fully-Loaded Hourly Wage Rates
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              Enter the fully-loaded hourly cost per technician (base wage + payroll taxes + benefits + workers comp + retirement).
              These rates are stored securely per organization and used to calculate true profitability.
              Leave blank for techs where you don't want profitability calculated.
            </p>
          </CardHeader>
          <CardContent>
            {wageError && (
              <div className="flex items-center gap-2 text-red-700 text-sm mb-3">
                <AlertCircle className="h-4 w-4" />
                {wageError}
              </div>
            )}
            {wageSaveMsg && (
              <div className="text-green-700 text-sm mb-3 font-medium">{wageSaveMsg}</div>
            )}
            {configTechNames.length === 0 && (
              <p className="text-sm text-muted-foreground">
                Run the report first to populate the technician list, then configure wage rates here.
              </p>
            )}
            {configTechNames.length > 0 && (
              <div className="space-y-2">
                <div className="grid grid-cols-12 gap-2 text-xs font-medium text-muted-foreground px-1 mb-1">
                  <div className="col-span-4">Technician</div>
                  <div className="col-span-3">Fully-Loaded Rate ($/hr)</div>
                  <div className="col-span-5">Notes (optional)</div>
                </div>
                <div className="max-h-72 overflow-y-auto space-y-1.5 pr-1">
                  {configTechNames.map(name => (
                    <div key={name} className="grid grid-cols-12 gap-2 items-center bg-white rounded-md px-2 py-1.5 border border-blue-100">
                      <div className="col-span-4 text-sm font-medium truncate" title={name}>{name}</div>
                      <div className="col-span-3">
                        <div className="relative">
                          <span className="absolute left-2 top-1/2 -translate-y-1/2 text-muted-foreground text-xs">$</span>
                          <Input
                            type="number"
                            min="0"
                            step="0.50"
                            placeholder="e.g. 34.00"
                            value={wageEdits[name] ?? ''}
                            onChange={e => setWageEdits(prev => ({ ...prev, [name]: e.target.value }))}
                            className="h-7 text-sm pl-5"
                          />
                        </div>
                      </div>
                      <div className="col-span-5">
                        <Input
                          type="text"
                          placeholder="e.g. includes $3.50/hr health ins."
                          value={wageNotes[name] ?? ''}
                          onChange={e => setWageNotes(prev => ({ ...prev, [name]: e.target.value }))}
                          className="h-7 text-sm"
                        />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex items-center gap-3 pt-2">
                  <Button onClick={saveWageRates} disabled={savingWages} size="sm" className="gap-1.5">
                    <Save className="h-3.5 w-3.5" />
                    {savingWages ? 'Saving…' : 'Save All Rates'}
                  </Button>
                  <p className="text-xs text-muted-foreground">
                    After saving, click Run to refresh the report with updated profitability data.
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── CFO Validation Guide ─────────────────────────────────────────── */}
      <CfoMethodologyCard
        title="Technician Productivity — CFO Validation Guide"
        items={[
          {
            label: 'Application Rate',
            formula: 'SUM(WOLabor.Hours) / Hours Paid × 100 | Target ≥ 85% (Currie)',
            detail: 'Application measures what percentage of the hours you paid a technician were actually spent working on jobs. Hours Paid is calculated as 40 hours/week × number of weeks in the selected period. Applied Hours come from WOLabor — every labor line posted to a service work order. If Application is below 85%, the tech is spending too much paid time on non-productive activity: training, shop meetings, idle time, or administrative tasks.'
          },
          {
            label: 'Efficiency Rate',
            formula: 'SUM(WOLabor.Hours WHERE Sell > 0) / SUM(WOLabor.Hours) × 100 | Target ≥ 100% (Currie)',
            detail: 'Efficiency measures what percentage of the hours worked on jobs was actually billed to customers. A labor line is counted as "billed" when WOLabor.Sell > 0 — meaning the customer was charged for that time. Lines with Sell = 0 are applied hours that generated no revenue: warranty write-offs, goodwill adjustments, internal work orders, or rework. Efficiency above 100% is possible when flat-rate billing allows techs to bill more hours than they actually spent.'
          },
          {
            label: 'Productivity Rate',
            formula: 'SUM(WOLabor.Hours WHERE Sell > 0) / Hours Paid × 100 | Target ≥ 85% (Currie)',
            detail: 'Productivity is the single bottom-line metric: of every hour you paid for, how many generated billable revenue? It is mathematically equal to Application × Efficiency. A tech can have high Application (always on a job) but low Efficiency (lots of warranty write-offs) and end up with poor Productivity. This is the number that most directly connects to profitability and is the primary metric for performance reviews.'
          },
          {
            label: 'True Profitability (Fully-Loaded)',
            formula: 'True GP $ = Labor Sell − (Wage Rate × Hours Paid) | True GP % = True GP $ / Labor Sell × 100',
            detail: 'True Profitability answers the question: "Did this technician generate enough revenue to cover what we actually paid them?" It uses the fully-loaded hourly rate you configure (base wage + payroll taxes + benefits + workers comp + retirement) multiplied by Hours Paid — not just the hours they billed. A tech with high Labor Sell but low Productivity may still show negative True GP because you paid for many idle hours. This is the most important metric for compensation decisions.'
          },
          {
            label: 'Break-Even Hours',
            formula: 'Break-Even Hrs = Wage Cost / (Labor Sell / Billed Hours) — hours needed to cover fully-loaded wage',
            detail: 'Break-Even Hours tells you how many billed hours a technician needed to generate enough revenue to cover their fully-loaded wage cost. If a tech needs to bill 280 hours to break even but only billed 153, they are operating at a loss for the shop regardless of their Efficiency score. This is a powerful coaching tool: show the tech exactly how many more hours they need to bill each week to be profitable.'
          },
          {
            label: 'Hours Paid (Denominator)',
            formula: '40 hrs/week × (days in period / 7) | Standard assumption — no payroll integration',
            detail: 'Hours Paid is the denominator for Application, Productivity, and True Profitability. Because Softbase does not store payroll hours, we use a standard assumption of 40 hours per week × the number of weeks in the selected period. This assumption is applied equally to all technicians. Part-time techs or those who took significant time off will appear to have lower Application and Productivity than their actual performance warrants.'
          },
          {
            label: 'Applied & Billed Hours Source',
            formula: 'Applied: SUM(WOLabor.Hours) | Billed: SUM(WOLabor.Hours WHERE Sell > 0) | Filter: WO.SaleDept IN (service depts) AND WO.ClosedDate IN period',
            detail: 'Applied Hours are all labor hours posted to service work orders that were closed within the selected date range. Billed Hours are the subset where WOLabor.Sell > 0 — the customer was charged. The date filter uses WO.ClosedDate (invoice date), so hours on open or completed-but-not-invoiced WOs are not counted until the WO is closed. Deleted work orders are excluded.'
          },
          {
            label: 'Color Bands',
            formula: 'Green ≥ target | Amber within 5% below target | Red > 5% below target | True GP: Green ≥ 0%, Amber ≥ −10%, Red < −10%',
            detail: 'Currie metrics use a three-zone traffic light: green (at or above target), amber (within 5 percentage points below target — watch condition), red (more than 5 points below — action required). True GP uses a separate scale: green means profitable, amber means slightly loss-making (within 10% of break-even), red means significantly loss-making.'
          },
          {
            label: 'Performance Review Warning',
            formula: 'These metrics are proxies — verify against actual payroll records before using in reviews',
            detail: 'Because Hours Paid uses a standard 40-hr/week assumption rather than actual payroll data, these metrics should be used as directional indicators, not as the sole basis for compensation decisions. Before using any technician\'s numbers in a performance review, cross-reference with actual payroll records for the period. Significant deviations between the standard assumption and actual hours paid will cause Application and Productivity to appear artificially low or high.'
          },
        ]}
      />

      {/* ── Department Aggregate KPIs ────────────────────────────────────── */}
      {data && (
        <div className="space-y-3">
          <h3 className="text-base font-semibold">Department Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Application */}
            {(() => {
              const zone = getZone(dept.application, CURRIE_APPLICATION)
              const tip = METRIC_TOOLTIPS.application
              return (
                <Card className={`border-2 ${ZONE_BORDER[zone]} ${ZONE_CARD[zone]}`}>
                  <CardContent className="pt-5 pb-4 flex flex-col items-center gap-2">
                    <div className="w-full flex justify-end">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                          </TooltipTrigger>
                          <TooltipContent side="top" className="max-w-xs text-left p-3 space-y-1">
                            <p className="font-semibold text-sm">{tip.title}</p>
                            <p className="text-xs font-mono text-muted-foreground">{tip.formula}</p>
                            <p className="text-xs leading-relaxed">{tip.description}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                    <MetricBadge value={dept.application} target={CURRIE_APPLICATION} label="Application" />
                    <div className="mt-2 text-xs text-center text-muted-foreground space-y-0.5">
                      <div>Applied: <span className="font-medium">{fmt1(dept.appliedHours)} hrs</span></div>
                      <div>Paid: <span className="font-medium">{fmt1(dept.hoursPaid)} hrs</span></div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                      <div className={`h-2 rounded-full ${ZONE_BAR[zone]}`} style={{ width: `${Math.min(dept.application || 0, 100)}%` }} />
                    </div>
                  </CardContent>
                </Card>
              )
            })()}

            {/* Efficiency */}
            {(() => {
              const zone = getZone(dept.efficiency, CURRIE_EFFICIENCY)
              const tip = METRIC_TOOLTIPS.efficiency
              return (
                <Card className={`border-2 ${ZONE_BORDER[zone]} ${ZONE_CARD[zone]}`}>
                  <CardContent className="pt-5 pb-4 flex flex-col items-center gap-2">
                    <div className="w-full flex justify-end">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                          </TooltipTrigger>
                          <TooltipContent side="top" className="max-w-xs text-left p-3 space-y-1">
                            <p className="font-semibold text-sm">{tip.title}</p>
                            <p className="text-xs font-mono text-muted-foreground">{tip.formula}</p>
                            <p className="text-xs leading-relaxed">{tip.description}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                    <MetricBadge value={dept.efficiency} target={CURRIE_EFFICIENCY} label="Efficiency" />
                    <div className="mt-2 text-xs text-center text-muted-foreground space-y-0.5">
                      <div>Billed: <span className="font-medium">{fmt1(dept.billedHours)} hrs</span></div>
                      <div>Unbilled: <span className="font-medium">{fmt2(dept.unbilledHours)} hrs</span></div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                      <div className={`h-2 rounded-full ${ZONE_BAR[zone]}`} style={{ width: `${Math.min(dept.efficiency || 0, 100)}%` }} />
                    </div>
                  </CardContent>
                </Card>
              )
            })()}

            {/* Productivity */}
            {(() => {
              const zone = getZone(dept.productivity, CURRIE_PRODUCTIVITY)
              const tip = METRIC_TOOLTIPS.productivity
              return (
                <Card className={`border-2 ${ZONE_BORDER[zone]} ${ZONE_CARD[zone]}`}>
                  <CardContent className="pt-5 pb-4 flex flex-col items-center gap-2">
                    <div className="w-full flex justify-end">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                          </TooltipTrigger>
                          <TooltipContent side="top" className="max-w-xs text-left p-3 space-y-1">
                            <p className="font-semibold text-sm">{tip.title}</p>
                            <p className="text-xs font-mono text-muted-foreground">{tip.formula}</p>
                            <p className="text-xs leading-relaxed">{tip.description}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                    <MetricBadge value={dept.productivity} target={CURRIE_PRODUCTIVITY} label="Productivity" />
                    <div className="mt-2 text-xs text-center text-muted-foreground space-y-0.5">
                      <div>Billed: <span className="font-medium">{fmt1(dept.billedHours)} hrs</span></div>
                      <div>Paid: <span className="font-medium">{fmt1(dept.hoursPaid)} hrs</span></div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                      <div className={`h-2 rounded-full ${ZONE_BAR[zone]}`} style={{ width: `${Math.min(dept.productivity || 0, 100)}%` }} />
                    </div>
                  </CardContent>
                </Card>
              )
            })()}
          </div>

          {/* Department True Profitability summary (only when wage rates configured) */}
          {hasWageRates && dept.trueGpDollars != null && (
            <Card className={`border-2 ${getTrueGpZone(dept.trueGpPct) === 'green' ? 'border-green-300 bg-green-50' : getTrueGpZone(dept.trueGpPct) === 'amber' ? 'border-amber-300 bg-amber-50' : 'border-red-300 bg-red-50'}`}>
              <CardContent className="pt-4 pb-3">
                <div className="flex flex-wrap items-center gap-6">
                  <div>
                    <div className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-0.5">Department True GP</div>
                    <div className={`text-2xl font-bold ${ZONE_TEXT[getTrueGpZone(dept.trueGpPct)]}`}>
                      {fmtCurrency(dept.trueGpDollars)}
                      <span className="text-base ml-2">({fmtPct(dept.trueGpPct)})</span>
                    </div>
                  </div>
                  <div className="text-sm text-muted-foreground space-y-0.5">
                    <div>Labor Sell: <span className="font-medium">{fmtCurrency(dept.totalSell)}</span></div>
                    <div>Fully-Loaded Wage Cost: <span className="font-medium">{fmtCurrency(dept.wageCost)}</span></div>
                  </div>
                  <div className="text-xs text-muted-foreground ml-auto">
                    Based on {dept.techsWithRates} of {dept.totalTechs} techs with wage rates configured.
                    {dept.techsWithRates < dept.totalTechs && (
                      <span className="text-amber-600 ml-1">Configure remaining techs for complete picture.</span>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Prompt to configure if no wage rates yet */}
          {!hasWageRates && data && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground bg-blue-50 border border-blue-200 rounded-md px-4 py-2.5">
              <DollarSign className="h-4 w-4 text-blue-500 flex-shrink-0" />
              <span>
                <strong>Configure wage rates</strong> to see true profitability per technician (Labor Sell vs. fully-loaded wage cost).
                Click <strong>Configure Wage Rates</strong> above to get started.
              </span>
            </div>
          )}

          {/* Period info */}
          <p className="text-xs text-muted-foreground">
            Period: {data.startDate} → {data.endDate} &nbsp;|&nbsp;
            {data.weeksPeriod} weeks &nbsp;|&nbsp;
            {dept.techCount} technician{dept.techCount !== 1 ? 's' : ''} &nbsp;|&nbsp;
            Hours Paid basis: {data.hoursPaidPerWeek} hrs/week per tech &nbsp;|&nbsp;
            Service depts: {(data.serviceDepts || []).join(', ')}
          </p>
        </div>
      )}

      {/* ── Technician Breakdown Table ───────────────────────────────────── */}
      {data && techs.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-base font-semibold">Technician Breakdown</h3>
          <div className="rounded-md border overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="w-8" />
                  <TableHead>Technician</TableHead>
                  <TableHead className="text-right">Hrs Paid</TableHead>
                  <TableHead className="text-right">Applied Hrs</TableHead>
                  <TableHead className="text-right">Billed Hrs</TableHead>
                  <TableHead className="text-right">Unbilled Hrs</TableHead>
                  <TableHead className="text-center">Application</TableHead>
                  <TableHead className="text-center">Efficiency</TableHead>
                  <TableHead className="text-center">Productivity</TableHead>
                  <TableHead className="text-right">Labor Sell</TableHead>
                  {hasWageRates && <TableHead className="text-right">Wage Cost</TableHead>}
                  {hasWageRates && <TableHead className="text-center">True GP%</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {techs.map((tech) => (
                  <>
                    <TableRow
                      key={tech.techName}
                      className="cursor-pointer hover:bg-muted/30"
                      onClick={() => toggleExpand(tech.techName)}
                    >
                      <TableCell className="w-8 text-center">
                        {expanded[tech.techName]
                          ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
                          : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
                      </TableCell>
                      <TableCell className="font-medium">{tech.techName}</TableCell>
                      <TableCell className="text-right text-sm">{fmt1(tech.hoursPaid)}</TableCell>
                      <TableCell className="text-right text-sm">{fmt1(tech.appliedHours)}</TableCell>
                      <TableCell className="text-right text-sm">{fmt1(tech.billedHours)}</TableCell>
                      <TableCell className={`text-right text-sm ${tech.unbilledHours > 0 ? 'text-amber-600 font-medium' : ''}`}>
                        {fmt2(tech.unbilledHours)}
                      </TableCell>
                      <StatusCell value={tech.application}  target={CURRIE_APPLICATION} />
                      <StatusCell value={tech.efficiency}   target={CURRIE_EFFICIENCY} />
                      <StatusCell value={tech.productivity} target={CURRIE_PRODUCTIVITY} />
                      <TableCell className="text-right text-sm">{fmtCurrency(tech.totalSell)}</TableCell>
                      {hasWageRates && (
                        <TableCell className="text-right text-sm">
                          {tech.hasWageRate ? fmtCurrency(tech.wageCost) : <span className="text-muted-foreground text-xs">not set</span>}
                        </TableCell>
                      )}
                      {hasWageRates && (
                        <StatusCell value={tech.trueGpPct} target={0} gpMode={true} />
                      )}
                    </TableRow>

                    {/* Expanded detail row */}
                    {expanded[tech.techName] && (
                      <TableRow key={`${tech.techName}-detail`} className="bg-blue-50/50">
                        <TableCell colSpan={hasWageRates ? 12 : 10} className="px-6 py-3">
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <div className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">Hours</div>
                              <div className="space-y-0.5">
                                <div>Paid (40 hr/wk × {data.weeksPeriod} wks): <span className="font-semibold">{fmt1(tech.hoursPaid)}</span></div>
                                <div>Applied (on jobs): <span className="font-semibold">{fmt1(tech.appliedHours)}</span></div>
                                <div>Billed (Sell &gt; 0): <span className="font-semibold">{fmt1(tech.billedHours)}</span></div>
                                <div className="text-amber-700">Unbilled (Sell = 0): <span className="font-semibold">{fmt2(tech.unbilledHours)}</span></div>
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">Currie Metrics</div>
                              <div className="space-y-0.5">
                                {[
                                  { label: 'Application',  value: tech.application,  target: CURRIE_APPLICATION },
                                  { label: 'Efficiency',   value: tech.efficiency,   target: CURRIE_EFFICIENCY },
                                  { label: 'Productivity', value: tech.productivity, target: CURRIE_PRODUCTIVITY },
                                ].map(({ label, value, target }) => {
                                  const zone = getZone(value, target)
                                  return (
                                    <div key={label} className={ZONE_TEXT[zone]}>
                                      {label}: <span className="font-semibold">{fmtPct(value)}</span>
                                      <span className="text-xs ml-1">(target {target}%)</span>
                                    </div>
                                  )
                                })}
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">Revenue & Cost</div>
                              <div className="space-y-0.5">
                                <div>Labor Sell: <span className="font-semibold">{fmtCurrency(tech.totalSell)}</span></div>
                                <div>Labor Cost (WOLabor): <span className="font-semibold">{fmtCurrency(tech.totalCost)}</span></div>
                                <div>WO GP $: <span className="font-semibold">{fmtCurrency(tech.totalSell - tech.totalCost)}</span></div>
                                <div>WO GP %: <span className="font-semibold">
                                  {tech.totalSell > 0 ? fmtPct((tech.totalSell - tech.totalCost) / tech.totalSell * 100) : '—'}
                                </span></div>
                              </div>
                            </div>
                            <div>
                              {tech.hasWageRate ? (
                                <>
                                  <div className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">True Profitability</div>
                                  <div className="space-y-0.5">
                                    <div>Wage Rate: <span className="font-semibold">${tech.wageRate?.toFixed(2)}/hr (fully-loaded)</span></div>
                                    <div>Wage Cost: <span className="font-semibold">{fmtCurrency(tech.wageCost)}</span>
                                      <span className="text-xs text-muted-foreground ml-1">({fmt1(tech.hoursPaid)} hrs × ${tech.wageRate?.toFixed(2)})</span>
                                    </div>
                                    <div className={ZONE_TEXT[getTrueGpZone(tech.trueGpPct)]}>
                                      True GP $: <span className="font-semibold">{fmtCurrency(tech.trueGpDollars)}</span>
                                    </div>
                                    <div className={ZONE_TEXT[getTrueGpZone(tech.trueGpPct)]}>
                                      True GP %: <span className="font-semibold">{fmtPct(tech.trueGpPct)}</span>
                                    </div>
                                    {tech.breakEvenHours != null && (
                                      <div className="text-muted-foreground">
                                        Break-even: <span className="font-semibold">{fmt1(tech.breakEvenHours)} billed hrs needed</span>
                                        {tech.billedHours < tech.breakEvenHours && (
                                          <span className="text-red-600 ml-1">({fmt1(tech.breakEvenHours - tech.billedHours)} hrs short)</span>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                </>
                              ) : (
                                <>
                                  <div className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">Activity</div>
                                  <div className="space-y-0.5">
                                    <div>Labor lines posted: <span className="font-semibold">{tech.laborLineCount}</span></div>
                                    <div>Avg billed/hr: <span className="font-semibold">
                                      {tech.billedHours > 0 ? fmtCurrency(tech.totalSell / tech.billedHours) : '—'}/hr
                                    </span></div>
                                    <div>Avg cost/hr: <span className="font-semibold">
                                      {tech.appliedHours > 0 ? fmtCurrency(tech.totalCost / tech.appliedHours) : '—'}/hr
                                    </span></div>
                                    <div className="text-xs text-blue-600 mt-1">Configure wage rate to see true profitability.</div>
                                  </div>
                                </>
                              )}
                            </div>
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </>
                ))}

                {/* Department totals row */}
                <TableRow className="bg-muted font-semibold border-t-2">
                  <TableCell />
                  <TableCell>DEPARTMENT TOTAL</TableCell>
                  <TableCell className="text-right">{fmt1(dept.hoursPaid)}</TableCell>
                  <TableCell className="text-right">{fmt1(dept.appliedHours)}</TableCell>
                  <TableCell className="text-right">{fmt1(dept.billedHours)}</TableCell>
                  <TableCell className="text-right">{fmt2(dept.unbilledHours)}</TableCell>
                  <StatusCell value={dept.application}  target={CURRIE_APPLICATION} />
                  <StatusCell value={dept.efficiency}   target={CURRIE_EFFICIENCY} />
                  <StatusCell value={dept.productivity} target={CURRIE_PRODUCTIVITY} />
                  <TableCell className="text-right">{fmtCurrency(dept.totalSell)}</TableCell>
                  {hasWageRates && <TableCell className="text-right">{fmtCurrency(dept.wageCost)}</TableCell>}
                  {hasWageRates && <StatusCell value={dept.trueGpPct} target={0} gpMode={true} />}
                </TableRow>
              </TableBody>
            </Table>
          </div>

          {/* Legend */}
          <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5"><span className="inline-block w-3 h-3 rounded bg-green-100 border border-green-300" /> At or above Currie target</span>
            <span className="flex items-center gap-1.5"><span className="inline-block w-3 h-3 rounded bg-amber-100 border border-amber-300" /> Within 5% of target (watch)</span>
            <span className="flex items-center gap-1.5"><span className="inline-block w-3 h-3 rounded bg-red-100 border border-red-300" /> More than 5% below target (action required)</span>
            <span className="flex items-center gap-1.5"><span className="inline-block w-3 h-3 rounded bg-amber-50 border border-amber-200" /> Unbilled hours (Sell = 0 — warranty, goodwill, internal)</span>
            {hasWageRates && <span className="flex items-center gap-1.5"><span className="inline-block w-3 h-3 rounded bg-green-100 border border-green-300" /> True GP% green = profitable | amber = within 10% of break-even | red = loss</span>}
            <span>Click any row to expand detail.</span>
          </div>
        </div>
      )}

      {/* ── Empty state ──────────────────────────────────────────────────── */}
      {data && techs.length === 0 && (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            No technician labor data found for the selected period.
            Check that service work orders were closed within the date range.
          </CardContent>
        </Card>
      )}

    </div>
  )
}

export default TechnicianProductivity
