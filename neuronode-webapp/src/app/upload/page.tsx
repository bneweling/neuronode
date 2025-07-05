'use client'

import { useEffect } from 'react'
import FileUploadZone from '@/components/upload/FileUploadZone'
import { PerformanceMonitor } from '@/lib/performance'

export default function UploadPage() {
  useEffect(() => {
    PerformanceMonitor.trackPageLoad('UploadPage')
  }, [])

  return (
    <>
      <header>
        <h1 style={{ display: 'none' }}>Document Upload</h1>
      </header>
      <main>
        <FileUploadZone />
      </main>
    </>
  )
} 