import { Inter } from 'next/font/google'
import { AppRouterCacheProvider } from '@mui/material-nextjs/v14-appRouter'

import { initializeWebVitalsObserver } from '@/lib/performance'
import { AppProviders } from '@/components/providers/AppProviders'
import './globals.css'

initializeWebVitalsObserver()

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Neuronode',
  description: 'AI-powered knowledge management',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AppRouterCacheProvider>
          <AppProviders>{children}</AppProviders>
        </AppRouterCacheProvider>
      </body>
    </html>
  )
}
