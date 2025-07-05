'use client'

import { useEffect } from 'react'
import TablerGraphDashboard from '@/components/graph/TablerGraphDashboard'
import { PerformanceMonitor } from '@/lib/performance'

export default function GraphPage() {
  useEffect(() => {
    PerformanceMonitor.trackPageLoad('GraphPage')
  }, [])

  return (
    <>
      <header>
        <h1 style={{ display: 'none' }}>Knowledge Graph Visualization</h1>
      </header>
      <main>
        <TablerGraphDashboard />
      </main>
    </>
  )
} 