/**
 * Parts Missed Upsell Report
 * Shows where Part A was sold without Part B on the same WO,
 * grouped by rep and by month, with estimated revenue missed.
 */
import { useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AlertCircle, RefreshCw, TrendingDown, ChevronDown, ChevronRight, DollarSign, User, Calendar } from 'lucide-react'
import { apiUrl } from '@/lib/api'
import { CfoMethodologyCard } from '@/components/ui/cfo-methodology-card'

const CFO_ITEMS = [
  {
    label: 'What counts as a missed upsell',
    formula: 'WOParts has TriggerPartNo on WONo AND WOParts does NOT have RecommendedPartNo on same WONo',
    detail: 'A missed upsell is recorded when a work order includes the trigger part (Part A) but does not include the recommended part (Part B) anywhere on the same work order. The system checks every active association in the Parts Association Manager.',
  },
  {
    label: 'Estimated revenue missed',
    formula: 'Missed Revenue = Inventory.Sell price of RecommendedPartNo × missed WO count',
    detail: 'The estimated missed revenue uses the current sell price of the recommended part from the Inventory table. This is an estimate — the actual price may have varied at time of sale, and the customer may not have bought the part even if offered.',
  },
  {
    label: 'Rep attribution',
    formula: 'WOParts.SalesmanNo → linked to the parts rep who processed the WO line',
    detail: 'Each missed opportunity is attributed to the parts rep (SalesmanNo) who processed the trigger part line. If no salesman is recorded on the WO line, it appears under "Unassigned."',
  },
  {
    label: 'Date range',
    formula: 'WOParts.DateOfPart BETWEEN :startDate AND :endDate',
    detail: 'The report filters by the date the part was posted to the work order. Use the date picker to adjust the analysis window. Default is the current year-to-date.',
  },
  {
    label: 'Data sources',
    formula: 'WOParts (trigger), WOParts (recommended check), Inventory (sell price), parts_associations (rules)',
    detail: 'The report joins your Softbase WOParts table against the parts_associations configuration table stored in PostgreSQL. Only active associations are checked. The Inventory table provides current sell prices for the estimated revenue calculation.',
  },
]

const fmt = (n) => n == null ? '—' : `$${Number(n).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
const fmtN = (n) => n == null ? '—' : Number(n).toLocaleString()

export default function PartsMissedUpsell() {
  const today = new Date()
  const startOfYear = `${today.getFullYear()}-01-01`
  const todayStr = today.toISOString().split('T')[0]

  const [startDate, setStartDate] = useState(startOfYear)
  const [endDate, setEndDate] = useState(todayStr)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [view, setView] = useState('by_rep') // 'by_rep' | 'by_association' | 'detail'
  const [expandedReps, setExpandedReps] = useState(new Set())
  const [expandedAssocs, setExpandedAssocs] = useState(new Set())

  const token = localStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }

  const runReport = useCallback(async () => {
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const params = new URLSearchParams({ start_date: startDate, end_date: endDate })
      const res = await fetch(apiUrl(`/api/parts-associations/missed-upsells?${params}`), { headers })
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const d = await res.json()
      setData(d)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [startDate, endDate, headers])

  const toggleRep = (rep) => {
    setExpandedReps(prev => {
      const next = new Set(prev)
      next.has(rep) ? next.delete(rep) : next.add(rep)
      return next
    })
  }

  const toggleAssoc = (key) => {
    setExpandedAssocs(prev => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Missed Upsell Opportunities</h2>
          <p className="text-sm text-gray-500 mt-1">
            Work orders where Part A was sold without the recommended Part B.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1">
            <label className="text-xs text-gray-500">Start</label>
            <input type="date" className="border rounded px-2 py-1 text-sm" value={startDate}
              onChange={e => setStartDate(e.target.value)} />
          </div>
          <div className="flex items-center gap-1">
            <label className="text-xs text-gray-500">End</label>
            <input type="date" className="border rounded px-2 py-1 text-sm" value={endDate}
              onChange={e => setEndDate(e.target.value)} />
          </div>
          <Button onClick={runReport} disabled={loading} className="bg-gray-900 hover:bg-gray-800 text-white">
            {loading ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : null}
            Run Report
          </Button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* No associations warning */}
      {data && data.noAssociations && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm">
          <strong>No associations configured.</strong> This report requires at least one active association in the Parts Association Manager. Go to the "Association Manager" tab to add associations or run AI Discovery.
        </div>
      )}

      {/* Summary Cards */}
      {data && !data.noAssociations && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Missed Opportunities</p>
                <p className="text-2xl font-bold text-red-600 mt-1">{fmtN(data.summary?.totalMissed)}</p>
                <p className="text-xs text-gray-400 mt-0.5">WOs with missing upsell</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Est. Revenue Missed</p>
                <p className="text-2xl font-bold text-red-600 mt-1">{fmt(data.summary?.totalRevenueMissed)}</p>
                <p className="text-xs text-gray-400 mt-0.5">At current sell prices</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Reps with Misses</p>
                <p className="text-2xl font-bold text-gray-800 mt-1">{fmtN(data.summary?.repsAffected)}</p>
                <p className="text-xs text-gray-400 mt-0.5">Parts reps with at least 1 miss</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Top Missed Association</p>
                <p className="text-base font-bold text-gray-800 mt-1 truncate">{data.summary?.topAssociation || '—'}</p>
                <p className="text-xs text-gray-400 mt-0.5">{fmtN(data.summary?.topAssociationCount)} misses</p>
              </CardContent>
            </Card>
          </div>

          {/* View Toggle */}
          <div className="flex gap-2 border-b pb-2">
            {[
              { key: 'by_rep', label: 'By Rep', icon: User },
              { key: 'by_association', label: 'By Association', icon: TrendingDown },
              { key: 'detail', label: 'All Detail', icon: Calendar },
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setView(key)}
                className={`flex items-center gap-1.5 px-4 py-2 text-sm rounded-md transition-colors ${view === key ? 'bg-gray-900 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </div>

          {/* By Rep View */}
          {view === 'by_rep' && (
            <Card>
              <CardContent className="pt-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-8"></TableHead>
                      <TableHead>Parts Rep</TableHead>
                      <TableHead className="text-right">Missed Opps</TableHead>
                      <TableHead className="text-right">Est. Revenue Missed</TableHead>
                      <TableHead className="text-right">Avg per Miss</TableHead>
                      <TableHead>Top Missed Association</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(data.byRep || []).map(rep => (
                      <>
                        <TableRow
                          key={rep.salesmanNo}
                          className="cursor-pointer hover:bg-gray-50"
                          onClick={() => toggleRep(rep.salesmanNo)}
                        >
                          <TableCell>
                            {expandedReps.has(rep.salesmanNo)
                              ? <ChevronDown className="h-4 w-4 text-gray-400" />
                              : <ChevronRight className="h-4 w-4 text-gray-400" />}
                          </TableCell>
                          <TableCell className="font-medium">{rep.salesmanName || rep.salesmanNo || 'Unassigned'}</TableCell>
                          <TableCell className="text-right">
                            <span className="font-semibold text-red-600">{fmtN(rep.missedCount)}</span>
                          </TableCell>
                          <TableCell className="text-right font-semibold text-red-600">{fmt(rep.revenueMissed)}</TableCell>
                          <TableCell className="text-right text-gray-600">{fmt(rep.avgPerMiss)}</TableCell>
                          <TableCell className="text-sm text-gray-600 truncate max-w-48">{rep.topAssociation || '—'}</TableCell>
                        </TableRow>
                        {expandedReps.has(rep.salesmanNo) && (rep.detail || []).map((d, i) => (
                          <TableRow key={i} className="bg-gray-50 text-sm">
                            <TableCell></TableCell>
                            <TableCell className="pl-8 text-gray-500">
                              WO #{d.woNo} — {d.woDate}
                            </TableCell>
                            <TableCell className="text-right text-gray-500">
                              <span className="font-mono text-xs">{d.triggerPartNo}</span> → missing <span className="font-mono text-xs text-red-600">{d.recommendedPartNo}</span>
                            </TableCell>
                            <TableCell className="text-right text-gray-500">{fmt(d.estimatedSell)}</TableCell>
                            <TableCell></TableCell>
                            <TableCell className="text-xs text-gray-400">{d.customer}</TableCell>
                          </TableRow>
                        ))}
                      </>
                    ))}
                    {(data.byRep || []).length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                          No missed upsells found for this period. Great job!
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {/* By Association View */}
          {view === 'by_association' && (
            <Card>
              <CardContent className="pt-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-8"></TableHead>
                      <TableHead>Trigger Part → Recommended Part</TableHead>
                      <TableHead className="text-right">Missed WOs</TableHead>
                      <TableHead className="text-right">Est. Revenue Missed</TableHead>
                      <TableHead>Relationship</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(data.byAssociation || []).map(assoc => {
                      const key = `${assoc.triggerPartNo}-${assoc.recommendedPartNo}`
                      return (
                        <>
                          <TableRow
                            key={key}
                            className="cursor-pointer hover:bg-gray-50"
                            onClick={() => toggleAssoc(key)}
                          >
                            <TableCell>
                              {expandedAssocs.has(key)
                                ? <ChevronDown className="h-4 w-4 text-gray-400" />
                                : <ChevronRight className="h-4 w-4 text-gray-400" />}
                            </TableCell>
                            <TableCell>
                              <span className="font-mono text-sm font-semibold text-blue-700">{assoc.triggerPartNo}</span>
                              <span className="text-gray-400 mx-2">→</span>
                              <span className="font-mono text-sm font-semibold text-green-700">{assoc.recommendedPartNo}</span>
                              <div className="text-xs text-gray-500 mt-0.5">{assoc.triggerDescription} → {assoc.recommendedDescription}</div>
                            </TableCell>
                            <TableCell className="text-right font-semibold text-red-600">{fmtN(assoc.missedCount)}</TableCell>
                            <TableCell className="text-right font-semibold text-red-600">{fmt(assoc.revenueMissed)}</TableCell>
                            <TableCell className="text-sm text-gray-600">
                              {assoc.relationshipType?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                            </TableCell>
                          </TableRow>
                          {expandedAssocs.has(key) && (assoc.detail || []).map((d, i) => (
                            <TableRow key={i} className="bg-gray-50 text-sm">
                              <TableCell></TableCell>
                              <TableCell className="pl-8 text-gray-500">WO #{d.woNo} — {d.woDate}</TableCell>
                              <TableCell className="text-right text-gray-500">{d.salesmanName || d.salesmanNo || 'Unassigned'}</TableCell>
                              <TableCell className="text-right text-gray-500">{fmt(d.estimatedSell)}</TableCell>
                              <TableCell className="text-xs text-gray-400">{d.customer}</TableCell>
                            </TableRow>
                          ))}
                        </>
                      )
                    })}
                    {(data.byAssociation || []).length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                          No missed upsells found for this period.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {/* Detail View */}
          {view === 'detail' && (
            <Card>
              <CardContent className="pt-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>WO #</TableHead>
                      <TableHead>Customer</TableHead>
                      <TableHead>Rep</TableHead>
                      <TableHead>Trigger Part</TableHead>
                      <TableHead>Missing Part</TableHead>
                      <TableHead className="text-right">Est. Missed $</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(data.detail || []).map((d, i) => (
                      <TableRow key={i}>
                        <TableCell className="text-sm text-gray-600">{d.woDate}</TableCell>
                        <TableCell className="font-mono text-sm">{d.woNo}</TableCell>
                        <TableCell className="text-sm max-w-36 truncate">{d.customer}</TableCell>
                        <TableCell className="text-sm">{d.salesmanName || d.salesmanNo || 'Unassigned'}</TableCell>
                        <TableCell>
                          <div className="font-mono text-xs font-semibold text-blue-700">{d.triggerPartNo}</div>
                          <div className="text-xs text-gray-400 truncate max-w-28">{d.triggerDescription}</div>
                        </TableCell>
                        <TableCell>
                          <div className="font-mono text-xs font-semibold text-red-600">{d.recommendedPartNo}</div>
                          <div className="text-xs text-gray-400 truncate max-w-28">{d.recommendedDescription}</div>
                        </TableCell>
                        <TableCell className="text-right font-semibold text-red-600">{fmt(d.estimatedSell)}</TableCell>
                      </TableRow>
                    ))}
                    {(data.detail || []).length === 0 && (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                          No missed upsells found for this period.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Empty state */}
      {!data && !loading && (
        <Card className="border-dashed bg-gray-50">
          <CardContent className="py-16 text-center text-gray-400">
            <TrendingDown className="h-14 w-14 mx-auto mb-4 text-gray-200" />
            <p className="text-lg font-medium text-gray-500">Select a date range and click Run Report</p>
            <p className="text-sm mt-1">Requires at least one active association in the Association Manager.</p>
          </CardContent>
        </Card>
      )}

      {/* CFO Guide */}
      <CfoMethodologyCard
        title="Missed Upsell Report — CFO Validation Guide"
        items={CFO_ITEMS}
      />
    </div>
  )
}
