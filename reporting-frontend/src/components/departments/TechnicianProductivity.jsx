import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AlertCircle, ChevronDown, ChevronRight, RefreshCw, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { apiUrl } from '@/lib/api'
import { CfoMethodologyCard } from '@/components/ui/cfo-methodology-card'

// ─── Currie Model Targets ──────────────────────────────────────────────────────
const CURRIE_APPLICATION  = 85   // Applied Hours / Hours Paid ≥ 85%
const CURRIE_EFFICIENCY   = 100  // Hours Billed  / Applied Hours ≥ 100%
const CURRIE_PRODUCTIVITY = 85   // Hours Billed  / Hours Paid ≥ 85%

// ─── Three-zone tolerance band (5% below target = amber, >5% below = red) ────
const AMBER_TOLERANCE = 5  // percentage points

// ─── Helpers ──────────────────────────────────────────────────────────────────
const fmt1 = (n) => (n == null ? '—' : n.toFixed(1))
const fmtPct = (n) => (n == null ? '—' : `${n.toFixed(1)}%`)
const fmtCurrency = (n) => (n == null ? '—' : `$${Number(n).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`)

/**
 * Returns 'green' | 'amber' | 'red' based on three-zone logic:
 *   green  = value >= target
 *   amber  = value >= (target - AMBER_TOLERANCE)   [within 5% of target]
 *   red    = value <  (target - AMBER_TOLERANCE)   [more than 5% below target]
 */
function getZone(value, target) {
  if (value == null) return 'gray'
  if (value >= target) return 'green'
  if (value >= target - AMBER_TOLERANCE) return 'amber'
  return 'red'
}

const ZONE_TEXT  = { green: 'text-green-700',  amber: 'text-amber-600',  red: 'text-red-600',  gray: 'text-muted-foreground' }
const ZONE_BG    = { green: 'bg-green-50',      amber: 'bg-amber-50',     red: 'bg-red-50',     gray: '' }
const ZONE_BADGE = { green: 'bg-green-100 text-green-700', amber: 'bg-amber-100 text-amber-700', red: 'bg-red-100 text-red-600', gray: 'bg-gray-100 text-gray-500' }
const ZONE_BAR   = { green: 'bg-green-500',     amber: 'bg-amber-400',    red: 'bg-red-500',    gray: 'bg-gray-300' }
const ZONE_BORDER= { green: 'border-green-300', amber: 'border-amber-300',red: 'border-red-300', gray: 'border-gray-200' }
const ZONE_CARD  = { green: 'bg-green-50',      amber: 'bg-amber-50',     red: 'bg-red-50',     gray: 'bg-gray-50' }

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

function StatusCell({ value, target }) {
  if (value == null) return <td className="px-3 py-2 text-center text-muted-foreground text-sm">—</td>
  const zone = getZone(value, target)
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

  const [startDate, setStartDate] = useState(fmt(firstOfYear))
  const [endDate, setEndDate]     = useState(fmt(today))
  const [data, setData]           = useState(null)
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)
  const [expanded, setExpanded]   = useState({})

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

  const toggleExpand = (name) => setExpanded(prev => ({ ...prev, [name]: !prev[name] }))

  const dept = data?.department || {}
  const techs = data?.technicians || []

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
            label: 'Hours Paid (Denominator)',
            formula: '40 hrs/week × (days in period / 7) | Standard assumption — no payroll integration',
            detail: 'Hours Paid is the denominator for both Application and Productivity. Because Softbase does not store payroll hours, we use a standard assumption of 40 hours per week per technician, prorated for the exact number of days in the selected date range. This means vacation, sick days, and holidays are NOT deducted — the denominator is the same for every tech. If a tech works part-time or was hired mid-period, their metrics will appear artificially low. A future enhancement will allow per-tech hour overrides.'
          },
          {
            label: 'Applied Hours Source',
            formula: 'SUM(WOLabor.Hours) WHERE WO.SaleDept IN (service depts) AND WO.ClosedDate IN period',
            detail: 'Applied Hours are pulled from the WOLabor table, filtered to work orders in service departments (same dynamic Dept table lookup used by all other service reports). The date filter uses WO.ClosedDate — the date the work order was invoiced and closed. Hours on open or completed-but-not-invoiced WOs are NOT counted until the WO is closed.'
          },
          {
            label: 'Billed Hours Source',
            formula: 'SUM(WOLabor.Hours WHERE WOLabor.Sell > 0) — hours with a positive sell amount',
            detail: 'Billed Hours are the subset of Applied Hours where the labor line has a positive Sell value in WOLabor. This is a proxy for "billable hours" — it captures lines where the customer was charged. It does not capture flat-rate billing (WOQuote lines) because those are stored separately. If your shop uses flat-rate billing heavily, Efficiency may appear understated.'
          },
          {
            label: 'Work Order Scope',
            formula: 'WO.SaleDept IN (service dept codes from Dept table) | WO.DeletionTime IS NULL',
            detail: 'Only work orders from service departments are included. Department codes are resolved dynamically from the Dept table — the same lookup used by the Service Sold by Customer and Customer Billing reports. Deleted work orders are excluded. Internal WOs (e.g., shop maintenance) are included in Applied Hours but their labor lines typically have Sell = 0, so they reduce Efficiency — which is the correct behavior.'
          },
          {
            label: 'Color Bands',
            formula: 'Green ≥ target | Amber within 5% below target | Red > 5% below target',
            detail: 'A three-zone traffic light system is used rather than a hard pass/fail. Green means at or above the Currie target. Amber means within 5 percentage points below target — a watch condition that warrants attention but is not an emergency (e.g., 99.8% Efficiency vs. 100% target shows amber, not red). Red means more than 5 percentage points below target and requires action. This prevents minor rounding differences from triggering false alarms.'
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
              return (
                <Card className={`border-2 ${ZONE_BORDER[zone]} ${ZONE_CARD[zone]}`}>
                  <CardContent className="pt-5 pb-4 flex flex-col items-center gap-2">
                    <MetricBadge value={dept.application} target={CURRIE_APPLICATION} label="Application" />
                    <div className="mt-2 text-xs text-center text-muted-foreground space-y-0.5">
                      <div>Applied: <span className="font-medium">{fmt1(dept.appliedHours)} hrs</span></div>
                      <div>Paid: <span className="font-medium">{fmt1(dept.hoursPaid)} hrs</span></div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                      <div
                        className={`h-2 rounded-full ${ZONE_BAR[zone]}`}
                        style={{ width: `${Math.min(dept.application || 0, 100)}%` }}
                      />
                    </div>
                  </CardContent>
                </Card>
              )
            })()}

            {/* Efficiency */}
            {(() => {
              const zone = getZone(dept.efficiency, CURRIE_EFFICIENCY)
              return (
                <Card className={`border-2 ${ZONE_BORDER[zone]} ${ZONE_CARD[zone]}`}>
                  <CardContent className="pt-5 pb-4 flex flex-col items-center gap-2">
                    <MetricBadge value={dept.efficiency} target={CURRIE_EFFICIENCY} label="Efficiency" />
                    <div className="mt-2 text-xs text-center text-muted-foreground space-y-0.5">
                      <div>Billed: <span className="font-medium">{fmt1(dept.billedHours)} hrs</span></div>
                      <div>Unbilled: <span className="font-medium">{fmt1(dept.unbilledHours)} hrs</span></div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                      <div
                        className={`h-2 rounded-full ${ZONE_BAR[zone]}`}
                        style={{ width: `${Math.min(dept.efficiency || 0, 100)}%` }}
                      />
                    </div>
                  </CardContent>
                </Card>
              )
            })()}

            {/* Productivity */}
            {(() => {
              const zone = getZone(dept.productivity, CURRIE_PRODUCTIVITY)
              return (
                <Card className={`border-2 ${ZONE_BORDER[zone]} ${ZONE_CARD[zone]}`}>
                  <CardContent className="pt-5 pb-4 flex flex-col items-center gap-2">
                    <MetricBadge value={dept.productivity} target={CURRIE_PRODUCTIVITY} label="Productivity" />
                    <div className="mt-2 text-xs text-center text-muted-foreground space-y-0.5">
                      <div>Billed: <span className="font-medium">{fmt1(dept.billedHours)} hrs</span></div>
                      <div>Paid: <span className="font-medium">{fmt1(dept.hoursPaid)} hrs</span></div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                      <div
                        className={`h-2 rounded-full ${ZONE_BAR[zone]}`}
                        style={{ width: `${Math.min(dept.productivity || 0, 100)}%` }}
                      />
                    </div>
                  </CardContent>
                </Card>
              )
            })()}
          </div>

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
                        {fmt1(tech.unbilledHours)}
                      </TableCell>
                      <StatusCell value={tech.application}  target={CURRIE_APPLICATION} />
                      <StatusCell value={tech.efficiency}   target={CURRIE_EFFICIENCY} />
                      <StatusCell value={tech.productivity} target={CURRIE_PRODUCTIVITY} />
                      <TableCell className="text-right text-sm">{fmtCurrency(tech.totalSell)}</TableCell>
                    </TableRow>

                    {/* Expanded detail row */}
                    {expanded[tech.techName] && (
                      <TableRow key={`${tech.techName}-detail`} className="bg-blue-50/50">
                        <TableCell colSpan={10} className="px-6 py-3">
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <div className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">Hours</div>
                              <div className="space-y-0.5">
                                <div>Paid (40 hr/wk × {data.weeksPeriod} wks): <span className="font-semibold">{fmt1(tech.hoursPaid)}</span></div>
                                <div>Applied (on jobs): <span className="font-semibold">{fmt1(tech.appliedHours)}</span></div>
                                <div>Billed (Sell &gt; 0): <span className="font-semibold">{fmt1(tech.billedHours)}</span></div>
                                <div className="text-amber-700">Unbilled (Sell = 0): <span className="font-semibold">{fmt1(tech.unbilledHours)}</span></div>
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">Currie Metrics</div>
                              <div className="space-y-0.5">
                                {[
                                  { label: 'Application', value: tech.application, target: CURRIE_APPLICATION },
                                  { label: 'Efficiency',  value: tech.efficiency,  target: CURRIE_EFFICIENCY },
                                  { label: 'Productivity',value: tech.productivity,target: CURRIE_PRODUCTIVITY },
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
                                <div>Labor Cost: <span className="font-semibold">{fmtCurrency(tech.totalCost)}</span></div>
                                <div>GP $: <span className="font-semibold">{fmtCurrency(tech.totalSell - tech.totalCost)}</span></div>
                                <div>GP %: <span className="font-semibold">
                                  {tech.totalSell > 0 ? fmtPct((tech.totalSell - tech.totalCost) / tech.totalSell * 100) : '—'}
                                </span></div>
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">Activity</div>
                              <div className="space-y-0.5">
                                <div>Labor lines posted: <span className="font-semibold">{tech.laborLineCount}</span></div>
                                <div>Avg billed/hr: <span className="font-semibold">
                                  {tech.billedHours > 0 ? fmtCurrency(tech.totalSell / tech.billedHours) : '—'}/hr
                                </span></div>
                                <div>Avg cost/hr: <span className="font-semibold">
                                  {tech.appliedHours > 0 ? fmtCurrency(tech.totalCost / tech.appliedHours) : '—'}/hr
                                </span></div>
                              </div>
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
                  <TableCell className="text-right">{fmt1(dept.unbilledHours)}</TableCell>
                  <StatusCell value={dept.application}  target={CURRIE_APPLICATION} />
                  <StatusCell value={dept.efficiency}   target={CURRIE_EFFICIENCY} />
                  <StatusCell value={dept.productivity} target={CURRIE_PRODUCTIVITY} />
                  <TableCell className="text-right">{fmtCurrency(dept.totalSell)}</TableCell>
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
