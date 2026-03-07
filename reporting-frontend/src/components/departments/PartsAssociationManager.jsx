/**
 * Parts Association Manager
 * Allows Parts Managers to define which parts should be recommended together.
 * Also runs AI market basket analysis to seed associations from historical data.
 */
import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { AlertCircle, Plus, Trash2, RefreshCw, Sparkles, CheckCircle, Edit2, X, Save, Brain } from 'lucide-react'
import { apiUrl } from '@/lib/api'
import { CfoMethodologyCard } from '@/components/ui/cfo-methodology-card'

const RELATIONSHIP_TYPES = [
  { value: 'often_needed_together', label: 'Often Needed Together' },
  { value: 'replacement_kit', label: 'Replacement Kit' },
  { value: 'wear_item', label: 'Wear Item (same interval)' },
  { value: 'upgrade', label: 'Upgrade / Better Option' },
  { value: 'accessory', label: 'Accessory' },
]

const SOURCE_COLORS = {
  manual: 'bg-blue-100 text-blue-800',
  ai_analysis: 'bg-purple-100 text-purple-800',
  ai_suggest: 'bg-green-100 text-green-800',
}

const SOURCE_LABELS = {
  manual: 'Manual',
  ai_analysis: 'AI Discovery',
  ai_suggest: 'AI Suggest',
}

const CFO_ITEMS = [
  {
    label: 'What is a Parts Association?',
    formula: 'IF sold(TriggerPartNo) AND NOT sold(RecommendedPartNo) → missed upsell',
    detail: 'A parts association defines a pair of parts where selling one without the other represents a missed upsell opportunity. When a customer buys Part A, the system flags that they likely also need Part B.',
  },
  {
    label: 'Manual vs. AI Discovery',
    formula: 'Source: manual | ai_analysis | ai_suggest',
    detail: 'Manual associations are entered by the Parts Manager and are never overwritten by AI. AI Discovery associations come from market basket analysis of your WOParts history. AI Suggest uses GPT to generate the upsell pitch text.',
  },
  {
    label: 'Confidence Score',
    formula: 'Confidence = co_occurrence(A,B) / frequency(A) × 100',
    detail: 'For AI-discovered associations, confidence is the percentage of work orders that included Part A and also included Part B. A confidence of 75% means 3 out of 4 times Part A was sold, Part B was also sold on the same WO.',
  },
  {
    label: 'Market Basket Analysis',
    formula: 'SELECT PartNo pairs FROM WOParts WHERE same WONo, lookback 365 days',
    detail: 'The AI Discovery scan analyzes your WOParts table for the past 12 months, finds all pairs of parts that appeared on the same work order, and calculates co-occurrence statistics. Pairs meeting the minimum support and confidence thresholds are returned as suggested associations.',
  },
  {
    label: 'Data Source',
    formula: 'PostgreSQL: parts_associations (org_id, trigger_part_no, recommended_part_no)',
    detail: 'Associations are stored in your secure PostgreSQL database, isolated by organization. They are never shared between IPS and Bennett. Changes take effect immediately in the Counter Assistant and Missed Opportunity Report.',
  },
]

export default function PartsAssociationManager() {
  const [associations, setAssociations] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  // Add form state
  const [showAddForm, setShowAddForm] = useState(false)
  const [newAssoc, setNewAssoc] = useState({
    triggerPartNo: '',
    triggerDescription: '',
    recommendedPartNo: '',
    recommendedDescription: '',
    relationshipType: 'often_needed_together',
    reason: '',
    confidence: 80,
  })
  const [addingAiSuggest, setAddingAiSuggest] = useState(false)

  // Edit state
  const [editingId, setEditingId] = useState(null)
  const [editData, setEditData] = useState({})

  // AI Discovery state
  const [showAiPanel, setShowAiPanel] = useState(false)
  const [aiDiscovering, setAiDiscovering] = useState(false)
  const [aiResults, setAiResults] = useState([])
  const [aiParams, setAiParams] = useState({ minSupport: 3, minConfidence: 40, lookbackDays: 365 })
  const [selectedAiRows, setSelectedAiRows] = useState(new Set())
  const [importingAi, setImportingAi] = useState(false)

  const token = localStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }

  const fetchAssociations = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(apiUrl('/api/parts-associations/'), { headers })
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const data = await res.json()
      setAssociations(data.associations || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchAssociations() }, [fetchAssociations])

  const handleAdd = async () => {
    if (!newAssoc.triggerPartNo.trim() || !newAssoc.recommendedPartNo.trim()) {
      setError('Trigger Part No and Recommended Part No are required.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(apiUrl('/api/parts-associations/'), {
        method: 'POST',
        headers,
        body: JSON.stringify({ ...newAssoc, source: 'manual' }),
      })
      if (!res.ok) {
        const d = await res.json()
        throw new Error(d.error || `Server error ${res.status}`)
      }
      setSuccess('Association saved.')
      setShowAddForm(false)
      setNewAssoc({ triggerPartNo: '', triggerDescription: '', recommendedPartNo: '', recommendedDescription: '', relationshipType: 'often_needed_together', reason: '', confidence: 80 })
      fetchAssociations()
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this association?')) return
    try {
      const res = await fetch(apiUrl(`/api/parts-associations/${id}`), { method: 'DELETE', headers })
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      setSuccess('Association deleted.')
      fetchAssociations()
    } catch (e) {
      setError(e.message)
    }
  }

  const handleEditSave = async (id) => {
    try {
      const res = await fetch(apiUrl(`/api/parts-associations/${id}`), {
        method: 'PUT',
        headers,
        body: JSON.stringify(editData),
      })
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      setSuccess('Association updated.')
      setEditingId(null)
      fetchAssociations()
    } catch (e) {
      setError(e.message)
    }
  }

  const handleAiSuggest = async () => {
    if (!newAssoc.triggerPartNo.trim() || !newAssoc.recommendedPartNo.trim()) {
      setError('Enter both part numbers first before requesting an AI suggestion.')
      return
    }
    setAddingAiSuggest(true)
    try {
      const res = await fetch(apiUrl('/api/parts-associations/ai-suggest'), {
        method: 'POST',
        headers,
        body: JSON.stringify({
          triggerPartNo: newAssoc.triggerPartNo,
          triggerDescription: newAssoc.triggerDescription,
          recommendedPartNo: newAssoc.recommendedPartNo,
          recommendedDescription: newAssoc.recommendedDescription,
        }),
      })
      const data = await res.json()
      if (data.suggestion) {
        setNewAssoc(prev => ({ ...prev, reason: data.suggestion }))
      }
    } catch (e) {
      setError('AI suggestion failed: ' + e.message)
    } finally {
      setAddingAiSuggest(false)
    }
  }

  const runAiDiscovery = async () => {
    setAiDiscovering(true)
    setAiResults([])
    setError(null)
    try {
      const params = new URLSearchParams({
        min_support: aiParams.minSupport,
        min_confidence: aiParams.minConfidence,
        lookback_days: aiParams.lookbackDays,
      })
      const res = await fetch(apiUrl(`/api/parts-associations/market-basket?${params}`), { headers })
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const data = await res.json()
      setAiResults(data.associations || [])
      setSelectedAiRows(new Set((data.associations || []).map((_, i) => i)))
    } catch (e) {
      setError('AI Discovery failed: ' + e.message)
    } finally {
      setAiDiscovering(false)
    }
  }

  const importSelectedAi = async () => {
    const toImport = aiResults.filter((_, i) => selectedAiRows.has(i))
    if (toImport.length === 0) {
      setError('Select at least one association to import.')
      return
    }
    setImportingAi(true)
    try {
      const res = await fetch(apiUrl('/api/parts-associations/bulk-import'), {
        method: 'POST',
        headers,
        body: JSON.stringify({ associations: toImport }),
      })
      const data = await res.json()
      setSuccess(`${data.saved} associations imported successfully.`)
      setShowAiPanel(false)
      setAiResults([])
      fetchAssociations()
    } catch (e) {
      setError('Import failed: ' + e.message)
    } finally {
      setImportingAi(false)
    }
  }

  const toggleAiRow = (i) => {
    setSelectedAiRows(prev => {
      const next = new Set(prev)
      next.has(i) ? next.delete(i) : next.add(i)
      return next
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Parts Association Manager</h2>
          <p className="text-sm text-gray-500 mt-1">
            Define which parts should be recommended together. Used by the Counter Assistant and Missed Opportunity Report.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => { setShowAiPanel(!showAiPanel); setShowAddForm(false) }}>
            <Brain className="h-4 w-4 mr-2" />
            AI Discovery
          </Button>
          <Button size="sm" onClick={() => { setShowAddForm(!showAddForm); setShowAiPanel(false) }}>
            <Plus className="h-4 w-4 mr-2" />
            Add Association
          </Button>
          <Button variant="outline" size="sm" onClick={fetchAssociations}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto"><X className="h-4 w-4" /></button>
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
          <CheckCircle className="h-4 w-4 flex-shrink-0" />
          {success}
          <button onClick={() => setSuccess(null)} className="ml-auto"><X className="h-4 w-4" /></button>
        </div>
      )}

      {/* Add Form */}
      {showAddForm && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Add New Association</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Trigger Part No *</Label>
                <Input placeholder="e.g. HYD-SEAL-KIT-001" value={newAssoc.triggerPartNo}
                  onChange={e => setNewAssoc(p => ({ ...p, triggerPartNo: e.target.value.toUpperCase() }))} />
              </div>
              <div className="space-y-2">
                <Label>Trigger Description</Label>
                <Input placeholder="e.g. Hydraulic Seal Kit" value={newAssoc.triggerDescription}
                  onChange={e => setNewAssoc(p => ({ ...p, triggerDescription: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label>Recommended Part No *</Label>
                <Input placeholder="e.g. HYD-FLUID-GAL" value={newAssoc.recommendedPartNo}
                  onChange={e => setNewAssoc(p => ({ ...p, recommendedPartNo: e.target.value.toUpperCase() }))} />
              </div>
              <div className="space-y-2">
                <Label>Recommended Description</Label>
                <Input placeholder="e.g. Hydraulic Fluid 1 Gallon" value={newAssoc.recommendedDescription}
                  onChange={e => setNewAssoc(p => ({ ...p, recommendedDescription: e.target.value }))} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Relationship Type</Label>
                <select className="w-full border rounded-md px-3 py-2 text-sm bg-white"
                  value={newAssoc.relationshipType}
                  onChange={e => setNewAssoc(p => ({ ...p, relationshipType: e.target.value }))}>
                  {RELATIONSHIP_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              <div className="space-y-2">
                <Label>Confidence % (manual = 80–100)</Label>
                <Input type="number" min="1" max="100" value={newAssoc.confidence}
                  onChange={e => setNewAssoc(p => ({ ...p, confidence: parseInt(e.target.value) || 80 }))} />
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Upsell Reason / Pitch for Parts Rep</Label>
                <Button variant="outline" size="sm" onClick={handleAiSuggest} disabled={addingAiSuggest}>
                  {addingAiSuggest ? <RefreshCw className="h-3 w-3 mr-1 animate-spin" /> : <Sparkles className="h-3 w-3 mr-1" />}
                  AI Suggest
                </Button>
              </div>
              <textarea className="w-full border rounded-md px-3 py-2 text-sm resize-none" rows={3}
                placeholder="e.g. When replacing the hydraulic seal kit, the fluid is typically contaminated and should be replaced at the same time."
                value={newAssoc.reason}
                onChange={e => setNewAssoc(p => ({ ...p, reason: e.target.value }))} />
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" size="sm" onClick={() => setShowAddForm(false)}>Cancel</Button>
              <Button size="sm" onClick={handleAdd} disabled={loading}>
                <Save className="h-4 w-4 mr-2" />
                Save Association
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* AI Discovery Panel */}
      {showAiPanel && (
        <Card className="border-purple-200 bg-purple-50">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Brain className="h-5 w-5 text-purple-600" />
              AI Market Basket Discovery
            </CardTitle>
            <p className="text-sm text-gray-600">
              Analyzes your WOParts history to find parts that are frequently sold together on the same work order.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-1">
                <Label>Min. Co-occurrences</Label>
                <Input type="number" min="1" value={aiParams.minSupport}
                  onChange={e => setAiParams(p => ({ ...p, minSupport: parseInt(e.target.value) || 3 }))} />
                <p className="text-xs text-gray-500">Min. WOs both parts appeared on</p>
              </div>
              <div className="space-y-1">
                <Label>Min. Confidence %</Label>
                <Input type="number" min="1" max="100" value={aiParams.minConfidence}
                  onChange={e => setAiParams(p => ({ ...p, minConfidence: parseInt(e.target.value) || 40 }))} />
                <p className="text-xs text-gray-500">% of trigger WOs that also had recommended part</p>
              </div>
              <div className="space-y-1">
                <Label>Lookback (days)</Label>
                <Input type="number" min="30" value={aiParams.lookbackDays}
                  onChange={e => setAiParams(p => ({ ...p, lookbackDays: parseInt(e.target.value) || 365 }))} />
                <p className="text-xs text-gray-500">Days of history to analyze</p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={runAiDiscovery} disabled={aiDiscovering} className="bg-purple-600 hover:bg-purple-700 text-white">
                {aiDiscovering ? <><RefreshCw className="h-4 w-4 mr-2 animate-spin" />Analyzing...</> : <><Brain className="h-4 w-4 mr-2" />Run Analysis</>}
              </Button>
              {aiResults.length > 0 && (
                <Button onClick={importSelectedAi} disabled={importingAi || selectedAiRows.size === 0}>
                  {importingAi ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                  Import Selected ({selectedAiRows.size})
                </Button>
              )}
              <Button variant="outline" onClick={() => setShowAiPanel(false)}>Cancel</Button>
            </div>

            {aiResults.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-gray-700">{aiResults.length} associations discovered</p>
                  <div className="flex gap-2 text-xs">
                    <button className="text-blue-600 underline" onClick={() => setSelectedAiRows(new Set(aiResults.map((_, i) => i)))}>Select All</button>
                    <button className="text-blue-600 underline" onClick={() => setSelectedAiRows(new Set())}>Deselect All</button>
                  </div>
                </div>
                <div className="max-h-64 overflow-y-auto border rounded-lg bg-white">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-8"></TableHead>
                        <TableHead>Trigger Part</TableHead>
                        <TableHead>Recommended Part</TableHead>
                        <TableHead>Co-occur.</TableHead>
                        <TableHead>Confidence</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {aiResults.map((r, i) => (
                        <TableRow key={i} className={selectedAiRows.has(i) ? 'bg-purple-50' : ''}>
                          <TableCell>
                            <input type="checkbox" checked={selectedAiRows.has(i)} onChange={() => toggleAiRow(i)} />
                          </TableCell>
                          <TableCell>
                            <div className="font-mono text-xs font-semibold">{r.triggerPartNo}</div>
                            <div className="text-xs text-gray-500 truncate max-w-32">{r.triggerDescription}</div>
                          </TableCell>
                          <TableCell>
                            <div className="font-mono text-xs font-semibold">{r.recommendedPartNo}</div>
                            <div className="text-xs text-gray-500 truncate max-w-32">{r.recommendedDescription}</div>
                          </TableCell>
                          <TableCell className="text-sm">{r.coOccurrence}</TableCell>
                          <TableCell>
                            <span className={`text-sm font-semibold ${r.confidence >= 70 ? 'text-green-600' : r.confidence >= 50 ? 'text-amber-600' : 'text-gray-600'}`}>
                              {r.confidence}%
                            </span>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Associations Table */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">
              Configured Associations
              <span className="ml-2 text-sm font-normal text-gray-500">({associations.length} total)</span>
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {loading && !associations.length ? (
            <div className="text-center py-8 text-gray-500">Loading associations...</div>
          ) : associations.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Brain className="h-12 w-12 mx-auto mb-3 text-gray-300" />
              <p className="font-medium">No associations configured yet.</p>
              <p className="text-sm mt-1">Click "Add Association" to create your first one, or use "AI Discovery" to find associations from your history.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Trigger Part</TableHead>
                    <TableHead>→ Recommend</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Reason / Pitch</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Active</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {associations.map(a => (
                    <TableRow key={a.id}>
                      {editingId === a.id ? (
                        <>
                          <TableCell>
                            <div className="font-mono text-xs font-semibold">{a.triggerPartNo}</div>
                            <Input className="mt-1 text-xs h-7" value={editData.triggerDescription || ''}
                              onChange={e => setEditData(p => ({ ...p, triggerDescription: e.target.value }))} />
                          </TableCell>
                          <TableCell>
                            <div className="font-mono text-xs font-semibold">{a.recommendedPartNo}</div>
                            <Input className="mt-1 text-xs h-7" value={editData.recommendedDescription || ''}
                              onChange={e => setEditData(p => ({ ...p, recommendedDescription: e.target.value }))} />
                          </TableCell>
                          <TableCell>
                            <select className="border rounded px-2 py-1 text-xs w-full"
                              value={editData.relationshipType || 'often_needed_together'}
                              onChange={e => setEditData(p => ({ ...p, relationshipType: e.target.value }))}>
                              {RELATIONSHIP_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                            </select>
                          </TableCell>
                          <TableCell>
                            <textarea className="border rounded px-2 py-1 text-xs w-full resize-none" rows={2}
                              value={editData.reason || ''}
                              onChange={e => setEditData(p => ({ ...p, reason: e.target.value }))} />
                          </TableCell>
                          <TableCell>
                            <Input type="number" className="text-xs h-7 w-16" value={editData.confidence || 80}
                              onChange={e => setEditData(p => ({ ...p, confidence: parseInt(e.target.value) || 80 }))} />
                          </TableCell>
                          <TableCell>
                            <Badge className={SOURCE_COLORS[a.source] || 'bg-gray-100 text-gray-700'}>
                              {SOURCE_LABELS[a.source] || a.source}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <input type="checkbox" checked={editData.isActive !== false}
                              onChange={e => setEditData(p => ({ ...p, isActive: e.target.checked }))} />
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              <Button size="sm" variant="outline" className="h-7 px-2" onClick={() => handleEditSave(a.id)}>
                                <Save className="h-3 w-3" />
                              </Button>
                              <Button size="sm" variant="outline" className="h-7 px-2" onClick={() => setEditingId(null)}>
                                <X className="h-3 w-3" />
                              </Button>
                            </div>
                          </TableCell>
                        </>
                      ) : (
                        <>
                          <TableCell>
                            <div className="font-mono text-xs font-semibold text-blue-700">{a.triggerPartNo}</div>
                            <div className="text-xs text-gray-500 max-w-28 truncate">{a.triggerDescription}</div>
                          </TableCell>
                          <TableCell>
                            <div className="font-mono text-xs font-semibold text-green-700">{a.recommendedPartNo}</div>
                            <div className="text-xs text-gray-500 max-w-28 truncate">{a.recommendedDescription}</div>
                          </TableCell>
                          <TableCell>
                            <span className="text-xs text-gray-600">
                              {RELATIONSHIP_TYPES.find(t => t.value === a.relationshipType)?.label || a.relationshipType}
                            </span>
                          </TableCell>
                          <TableCell>
                            <p className="text-xs text-gray-700 max-w-48 line-clamp-2">{a.reason || '—'}</p>
                          </TableCell>
                          <TableCell>
                            <span className={`text-sm font-semibold ${a.confidence >= 70 ? 'text-green-600' : a.confidence >= 50 ? 'text-amber-600' : 'text-gray-500'}`}>
                              {a.confidence}%
                            </span>
                          </TableCell>
                          <TableCell>
                            <Badge className={SOURCE_COLORS[a.source] || 'bg-gray-100 text-gray-700'}>
                              {SOURCE_LABELS[a.source] || a.source}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <span className={`text-xs font-medium ${a.isActive ? 'text-green-600' : 'text-gray-400'}`}>
                              {a.isActive ? 'Active' : 'Inactive'}
                            </span>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              <Button size="sm" variant="outline" className="h-7 px-2"
                                onClick={() => { setEditingId(a.id); setEditData({ triggerDescription: a.triggerDescription, recommendedDescription: a.recommendedDescription, relationshipType: a.relationshipType, reason: a.reason, confidence: a.confidence, isActive: a.isActive }) }}>
                                <Edit2 className="h-3 w-3" />
                              </Button>
                              <Button size="sm" variant="outline" className="h-7 px-2 text-red-600 hover:bg-red-50"
                                onClick={() => handleDelete(a.id)}>
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </div>
                          </TableCell>
                        </>
                      )}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* CFO Validation Guide */}
      <CfoMethodologyCard
        title="Parts Association Manager — CFO Validation Guide"
        items={CFO_ITEMS}
      />
    </div>
  )
}
