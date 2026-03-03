import { useState, useCallback, useEffect } from 'react'

/**
 * Custom hook that wraps useState for active tab tracking.
 * Automatically dispatches a 'activeTabChange' window event whenever the tab changes,
 * so the HelpWidget can capture which tab the user is viewing when submitting a ticket.
 */
export function useActiveTab(initialTab) {
  const [activeTab, setActiveTabInternal] = useState(initialTab)

  // Dispatch event whenever activeTab changes
  useEffect(() => {
    if (activeTab) {
      window.dispatchEvent(new CustomEvent('activeTabChange', { detail: activeTab }))
    }
  }, [activeTab])

  // Wrap setActiveTab to also dispatch immediately for programmatic changes
  const setActiveTab = useCallback((newTab) => {
    setActiveTabInternal(newTab)
  }, [])

  return [activeTab, setActiveTab]
}
