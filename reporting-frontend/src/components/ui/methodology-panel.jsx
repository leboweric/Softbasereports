import * as React from "react";
import { BookOpen, ChevronDown, ChevronRight } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";

/**
 * MethodologyPanel - A slide-out drawer showing all GL accounts and formulas
 * for every metric on the current page.
 *
 * Usage:
 *   <MethodologyPanel
 *     title="Ed's Dashboard Methodology"
 *     sections={[
 *       {
 *         heading: "Summary Cards",
 *         metrics: [
 *           { label: "Total Revenue", formula: "Sum of...", accounts: ["4110501", ...] },
 *           ...
 *         ]
 *       }
 *     ]}
 *   />
 */

function MetricRow({ metric, defaultOpen = false }) {
  const [open, setOpen] = React.useState(defaultOpen);

  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        type="button"
        className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-muted/50 transition-colors"
        onClick={() => setOpen(!open)}
      >
        <span className="text-sm font-medium">{metric.label}</span>
        {open ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
        )}
      </button>
      {open && (
        <div className="px-3 pb-3 space-y-2 border-t bg-muted/20">
          {metric.formula && (
            <div className="pt-2">
              <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                Calculation
              </span>
              <p className="text-xs mt-0.5 text-foreground">{metric.formula}</p>
            </div>
          )}
          {metric.accounts && metric.accounts.length > 0 && (
            <div>
              <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                GL Accounts ({metric.accounts.length})
              </span>
              <div className="mt-1 max-h-40 overflow-y-auto bg-background rounded p-2 border">
                <p className="text-[11px] font-mono leading-relaxed break-all text-foreground/80">
                  {metric.accounts.join(", ")}
                </p>
              </div>
            </div>
          )}
          {metric.source && (
            <div>
              <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                Data Source
              </span>
              <p className="text-xs mt-0.5 text-foreground/80">{metric.source}</p>
            </div>
          )}
          {(!metric.accounts || metric.accounts.length === 0) && !metric.formula && (
            <p className="text-xs text-muted-foreground italic pt-2">
              This metric is derived from operational data, not directly from GL accounts.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export function MethodologyPanel({ title, description, sections }) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm" className="gap-1.5">
          <BookOpen className="h-4 w-4" />
          <span className="hidden sm:inline">Methodology</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader className="pb-4">
          <SheetTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            {title || "Report Methodology"}
          </SheetTitle>
          <SheetDescription>
            {description ||
              "GL accounts, formulas, and data sources for every metric on this page. Use this to validate the numbers against your general ledger."}
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-6 pb-8">
          {sections?.map((section, sIdx) => (
            <div key={sIdx}>
              <h3 className="text-sm font-semibold text-foreground mb-2 px-1 border-b pb-1">
                {section.heading}
              </h3>
              <div className="space-y-1.5">
                {section.metrics?.map((metric, mIdx) => (
                  <MetricRow key={mIdx} metric={metric} />
                ))}
              </div>
            </div>
          ))}
        </div>
      </SheetContent>
    </Sheet>
  );
}

export default MethodologyPanel;
