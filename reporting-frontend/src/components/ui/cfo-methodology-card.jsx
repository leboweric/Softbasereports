/**
 * CfoMethodologyCard — Reusable CFO Validation Guide panel
 *
 * Renders a collapsible blue card explaining how a report is calculated.
 * Used across all Service page tabs for CFO transparency and validation.
 *
 * Usage:
 *   <CfoMethodologyCard title="Cash Burn" items={[
 *     { label: "Open WO Cost", formula: "SUM(WOLabor.Cost + WOParts.Cost)", detail: "..." },
 *     ...
 *   ]} />
 */
import React, { useState } from 'react'
import { Info, ChevronDown } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'

export function CfoMethodologyCard({ title, items }) {
  const [open, setOpen] = useState(false)

  return (
    <Card className="border-blue-200 bg-blue-50 mb-4">
      <CardContent className="pt-4 pb-3">
        <button
          className="flex items-center gap-2 text-sm font-medium text-blue-700 hover:text-blue-900 w-full text-left"
          onClick={() => setOpen(prev => !prev)}
        >
          <Info className="h-4 w-4 shrink-0" />
          How is this calculated? (CFO Validation Guide) — {title}
          <ChevronDown className={`h-4 w-4 ml-auto transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
        </button>

        {open && (
          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-900">
            {items.map((item, i) => (
              <div key={i} className="space-y-1">
                <div className="font-semibold border-b border-blue-200 pb-1">{item.label}</div>
                {item.formula && (
                  <p>
                    <code className="bg-blue-100 px-1 rounded text-xs">{item.formula}</code>
                  </p>
                )}
                {item.detail && (
                  <p className="text-xs text-blue-700">{item.detail}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
