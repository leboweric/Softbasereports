/**
 * Parts Counter Assistant
 * Real-time upsell recommendation tool for parts reps at the counter.
 * Type a part number → get instant recommendations with inventory status.
 */
import { useState, useCallback, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, Search, Sparkles, Package, TrendingUp, X, Plus, ChevronRight, Info } from 'lucide-react'
import { apiUrl } from '@/lib/api'
import { CfoMethodologyCard } from '@/components/ui/cfo-methodology-card'

const RELATIONSHIP_LABELS = {
  often_needed_together: 'Often Needed Together',
  replacement_kit: 'Replacement Kit',
  wear_item: 'Wear Item',
  upgrade: 'Upgrade / Better Option',
  accessory: 'Accessory',
}

const RELATIONSHIP_COLORS = {
  often_needed_together: 'bg-blue-100 text-blue-800 border-blue-200',
  replacement_kit: 'bg-orange-100 text-orange-800 border-orange-200',
  wear_item: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  upgrade: 'bg-green-100 text-green-800 border-green-200',
  accessory: 'bg-purple-100 text-purple-800 border-purple-200',
}

const CFO_ITEMS = [
  {
    label: 'How recommendations are generated',
    formula: 'SELECT * FROM parts_associations WHERE trigger_part_no = :partNo AND is_active = TRUE ORDER BY confidence DESC',
    detail: 'When a parts rep types a part number, the system looks up all active associations where that part is the trigger. Results are sorted by confidence score — highest confidence (most reliable) first. AI-discovered associations are shown alongside manually configured ones.',
  },
  {
    label: 'Inventory status shown',
    formula: 'SELECT OnHand, OnOrder, Cost, Sell FROM Inventory WHERE PartNo = :partNo',
    detail: 'For each recommended part, the system checks live inventory. Green = in stock, amber = low stock (≤ 2 units), red = out of stock. This tells the rep whether they can fulfill the upsell immediately or need to order.',
  },
  {
    label: 'AI Fallback',
    formula: 'IF no associations found → GPT-4 query with part description context',
    detail: 'If no configured associations exist for the part number, the system can query the AI model with the part description to generate a suggested upsell reason. This is labeled "AI Suggest" and is less reliable than manager-configured associations.',
  },
  {
    label: 'Multi-part lookup',
    formula: 'Cart: [PartA, PartB, PartC] → UNION ALL recommendations for each part, deduplicated',
    detail: 'The rep can add multiple parts to the lookup cart (simulating a customer order). The system returns all recommendations for all parts in the cart, deduplicated, so the rep sees every upsell opportunity for the entire transaction at once.',
  },
]

export default function PartsCounterAssistant() {
  const [searchInput, setSearchInput] = useState('')
  const [cart, setCart] = useState([]) // parts the customer is buying
  const [results, setResults] = useState([]) // recommendations
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [dismissedIds, setDismissedIds] = useState(new Set())
  const inputRef = useRef(null)

  const token = localStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }

  const addToCart = useCallback(async (partNo) => {
    const trimmed = partNo.trim().toUpperCase()
    if (!trimmed) return
    if (cart.find(p => p.partNo === trimmed)) {
      setSearchInput('')
      return
    }

    setLoading(true)
    setError(null)
    const newCart = [...cart, { partNo: trimmed, description: '' }]
    setCart(newCart)
    setSearchInput('')

    try {
      const res = await fetch(apiUrl('/api/parts-associations/lookup'), {
        method: 'POST',
        headers,
        body: JSON.stringify({ partNumbers: newCart.map(p => p.partNo) }),
      })
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const data = await res.json()

      // Update cart with descriptions from inventory lookup
      if (data.partDetails) {
        setCart(data.partDetails.map(p => ({ partNo: p.partNo, description: p.description || '' })))
      }
      setResults(data.recommendations || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }, [cart, headers])

  const removeFromCart = useCallback(async (partNo) => {
    const newCart = cart.filter(p => p.partNo !== partNo)
    setCart(newCart)
    setDismissedIds(new Set())

    if (newCart.length === 0) {
      setResults([])
      return
    }

    setLoading(true)
    try {
      const res = await fetch(apiUrl('/api/parts-associations/lookup'), {
        method: 'POST',
        headers,
        body: JSON.stringify({ partNumbers: newCart.map(p => p.partNo) }),
      })
      const data = await res.json()
      setResults(data.recommendations || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [cart, headers])

  const clearAll = () => {
    setCart([])
    setResults([])
    setDismissedIds(new Set())
    setError(null)
    setSearchInput('')
    inputRef.current?.focus()
  }

  const requestAiFallback = async () => {
    if (cart.length === 0) return
    setAiLoading(true)
    try {
      const res = await fetch(apiUrl('/api/parts-associations/ai-fallback'), {
        method: 'POST',
        headers,
        body: JSON.stringify({ partNumbers: cart.map(p => p.partNo), partDetails: cart }),
      })
      const data = await res.json()
      if (data.recommendations?.length) {
        setResults(prev => {
          const existingKeys = new Set(prev.map(r => r.recommendedPartNo))
          const newOnes = data.recommendations.filter(r => !existingKeys.has(r.recommendedPartNo))
          return [...prev, ...newOnes]
        })
      } else {
        setError('No additional AI suggestions found for these parts.')
      }
    } catch (e) {
      setError('AI fallback failed: ' + e.message)
    } finally {
      setAiLoading(false)
    }
  }

  const visibleResults = results.filter(r => !dismissedIds.has(r.id || r.recommendedPartNo))

  const stockColor = (onHand) => {
    if (onHand === null || onHand === undefined) return 'text-gray-400'
    if (onHand <= 0) return 'text-red-600'
    if (onHand <= 2) return 'text-amber-600'
    return 'text-green-600'
  }

  const stockLabel = (onHand) => {
    if (onHand === null || onHand === undefined) return 'Unknown'
    if (onHand <= 0) return 'Out of Stock'
    if (onHand <= 2) return `Low (${onHand})`
    return `In Stock (${onHand})`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-gray-900">Counter Assistant</h2>
        <p className="text-sm text-gray-500 mt-1">
          Type a part number and press Enter to see upsell recommendations. Add multiple parts to see all opportunities for the transaction.
        </p>
      </div>

      {/* Search Bar */}
      <Card className="border-2 border-blue-200 bg-blue-50">
        <CardContent className="pt-4 pb-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                ref={inputRef}
                className="pl-9 text-base bg-white border-blue-300 focus:border-blue-500 h-11"
                placeholder="Enter part number and press Enter..."
                value={searchInput}
                onChange={e => setSearchInput(e.target.value.toUpperCase())}
                onKeyDown={e => { if (e.key === 'Enter' && searchInput.trim()) addToCart(searchInput) }}
                autoFocus
              />
            </div>
            <Button
              className="h-11 px-6 bg-blue-600 hover:bg-blue-700"
              onClick={() => searchInput.trim() && addToCart(searchInput)}
              disabled={loading || !searchInput.trim()}
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Part
            </Button>
            {cart.length > 0 && (
              <Button variant="outline" className="h-11" onClick={clearAll}>
                <X className="h-4 w-4 mr-1" />
                Clear
              </Button>
            )}
          </div>

          {/* Cart */}
          {cart.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              <span className="text-xs text-gray-500 self-center">Customer is buying:</span>
              {cart.map(p => (
                <div key={p.partNo} className="flex items-center gap-1 bg-white border border-blue-300 rounded-full px-3 py-1">
                  <span className="font-mono text-sm font-semibold text-blue-700">{p.partNo}</span>
                  {p.description && <span className="text-xs text-gray-500">— {p.description}</span>}
                  <button onClick={() => removeFromCart(p.partNo)} className="ml-1 text-gray-400 hover:text-red-500">
                    <X className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto"><X className="h-4 w-4" /></button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="text-center py-6 text-gray-500 text-sm">Looking up recommendations...</div>
      )}

      {/* Results */}
      {!loading && cart.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-800 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              Upsell Recommendations
              {visibleResults.length > 0 && (
                <span className="text-sm font-normal text-gray-500">({visibleResults.length} suggestions)</span>
              )}
            </h3>
            <Button variant="outline" size="sm" onClick={requestAiFallback} disabled={aiLoading}>
              {aiLoading
                ? <><span className="animate-spin mr-1">⟳</span> Asking AI...</>
                : <><Sparkles className="h-3 w-3 mr-1" /> Ask AI for More</>}
            </Button>
          </div>

          {visibleResults.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="py-10 text-center text-gray-500">
                <Package className="h-10 w-10 mx-auto mb-3 text-gray-300" />
                <p className="font-medium">No configured associations found for these parts.</p>
                <p className="text-sm mt-1">Click "Ask AI for More" to get AI-generated suggestions, or add associations in the Association Manager tab.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3">
              {visibleResults.map((rec, idx) => (
                <Card key={rec.id || idx} className="border-l-4 border-l-green-400 hover:shadow-md transition-shadow">
                  <CardContent className="pt-4 pb-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        {/* Part info row */}
                        <div className="flex items-center gap-3 flex-wrap">
                          <div>
                            <span className="text-xs text-gray-400 uppercase tracking-wide">Recommend</span>
                            <div className="font-mono text-base font-bold text-green-700">{rec.recommendedPartNo}</div>
                            {rec.recommendedDescription && (
                              <div className="text-sm text-gray-600">{rec.recommendedDescription}</div>
                            )}
                          </div>
                          <ChevronRight className="h-4 w-4 text-gray-300 flex-shrink-0" />
                          <div>
                            <span className="text-xs text-gray-400 uppercase tracking-wide">Because customer bought</span>
                            <div className="font-mono text-sm font-semibold text-blue-700">{rec.triggerPartNo}</div>
                          </div>
                        </div>

                        {/* Pitch / reason */}
                        {rec.reason && (
                          <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded text-sm text-amber-900">
                            <span className="font-semibold">Say to customer: </span>
                            {rec.reason}
                          </div>
                        )}

                        {/* Metadata row */}
                        <div className="mt-2 flex items-center gap-3 flex-wrap">
                          <Badge className={`text-xs border ${RELATIONSHIP_COLORS[rec.relationshipType] || 'bg-gray-100 text-gray-700'}`}>
                            {RELATIONSHIP_LABELS[rec.relationshipType] || rec.relationshipType}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            Confidence: <span className={`font-semibold ${rec.confidence >= 70 ? 'text-green-600' : rec.confidence >= 50 ? 'text-amber-600' : 'text-gray-500'}`}>{rec.confidence}%</span>
                          </span>
                          {rec.source === 'ai_suggest' && (
                            <Badge className="text-xs bg-purple-100 text-purple-700 border-purple-200">
                              <Sparkles className="h-3 w-3 mr-1" />AI Suggest
                            </Badge>
                          )}
                        </div>
                      </div>

                      {/* Inventory panel */}
                      <div className="flex-shrink-0 text-right min-w-28">
                        <div className={`text-sm font-semibold ${stockColor(rec.inventory?.onHand)}`}>
                          {stockLabel(rec.inventory?.onHand)}
                        </div>
                        {rec.inventory?.sell > 0 && (
                          <div className="text-sm text-gray-700 font-medium mt-0.5">
                            ${rec.inventory.sell.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </div>
                        )}
                        {rec.inventory?.onOrder > 0 && (
                          <div className="text-xs text-blue-600 mt-0.5">{rec.inventory.onOrder} on order</div>
                        )}
                        <button
                          className="mt-2 text-xs text-gray-400 hover:text-gray-600 underline"
                          onClick={() => setDismissedIds(prev => new Set([...prev, rec.id || rec.recommendedPartNo]))}>
                          Dismiss
                        </button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!loading && cart.length === 0 && (
        <Card className="border-dashed bg-gray-50">
          <CardContent className="py-16 text-center text-gray-400">
            <Search className="h-14 w-14 mx-auto mb-4 text-gray-200" />
            <p className="text-lg font-medium text-gray-500">Ready for a customer</p>
            <p className="text-sm mt-1">Type a part number above and press Enter to see upsell recommendations.</p>
            <div className="mt-4 flex justify-center gap-4 text-xs text-gray-400">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500 inline-block"></span> In Stock</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500 inline-block"></span> Low Stock</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500 inline-block"></span> Out of Stock</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* CFO Guide */}
      <CfoMethodologyCard
        title="Counter Assistant — How It Works"
        items={CFO_ITEMS}
      />
    </div>
  )
}
