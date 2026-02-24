import * as React from "react";
import { Info } from "lucide-react";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";

/**
 * MetricTooltip - Displays GL account details and calculation formulas on hover.
 * 
 * Usage:
 *   <MetricTooltip metricKey="new_equipment_revenue" />
 *   <MetricTooltip metricKey="custom" accounts={["4110501","4110502"]} formula="Sum of all NE revenue accounts" />
 */
export function MetricTooltip({ metricKey, accounts, formula, label, className }) {
  // If custom accounts/formula provided, use those directly
  const displayAccounts = accounts || [];
  const displayFormula = formula || "";
  const displayLabel = label || "";

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          className={`inline-flex items-center justify-center rounded-full p-0.5 hover:bg-muted/50 transition-colors focus:outline-none ${className || ''}`}
          aria-label="View metric details"
        >
          <Info className="h-3.5 w-3.5 text-muted-foreground/60 hover:text-muted-foreground" />
        </button>
      </TooltipTrigger>
      <TooltipContent
        side="bottom"
        className="max-w-sm bg-popover text-popover-foreground border shadow-lg rounded-lg p-3 z-[100]"
      >
        <div className="space-y-2 text-left">
          {displayLabel && (
            <div className="font-semibold text-xs border-b pb-1 mb-1">{displayLabel}</div>
          )}
          {displayFormula && (
            <div>
              <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">Formula</span>
              <p className="text-xs mt-0.5">{displayFormula}</p>
            </div>
          )}
          {displayAccounts.length > 0 && (
            <div>
              <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">GL Accounts</span>
              <div className="mt-0.5 max-h-32 overflow-y-auto">
                <p className="text-[11px] font-mono leading-relaxed break-all">
                  {displayAccounts.join(", ")}
                </p>
              </div>
            </div>
          )}
          {!displayFormula && displayAccounts.length === 0 && (
            <p className="text-xs text-muted-foreground italic">No metric details available</p>
          )}
        </div>
      </TooltipContent>
    </Tooltip>
  );
}

export default MetricTooltip;
