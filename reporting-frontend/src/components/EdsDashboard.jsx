import SalesGPReport from '@/components/SalesGPReport'
import { Crown } from 'lucide-react'
import { MethodologyPanel } from '@/components/ui/methodology-panel'
import { EDS_DASHBOARD_METHODOLOGY } from '@/config/ipsPageMethodology'

export default function EdsDashboard({ user, organization }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Crown className="h-8 w-8 text-amber-500" />
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Ed's Dashboard</h1>
            <p className="text-muted-foreground">
              Owner overview &mdash; Sales, Cost of Sales, and Gross Profit by Branch and Department
            </p>
          </div>
        </div>
        <MethodologyPanel {...EDS_DASHBOARD_METHODOLOGY} />
      </div>
      <SalesGPReport user={user} />
    </div>
  )
}
