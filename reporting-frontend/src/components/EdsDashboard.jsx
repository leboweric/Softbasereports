import SalesGPReport from '@/components/SalesGPReport'
import { Crown } from 'lucide-react'

export default function EdsDashboard({ user, organization }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Crown className="h-8 w-8 text-amber-500" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Ed's Dashboard</h1>
          <p className="text-muted-foreground">
            Owner overview &mdash; Sales, Cost of Sales, and Gross Profit by Branch and Department
          </p>
        </div>
      </div>
      <SalesGPReport user={user} />
    </div>
  )
}
