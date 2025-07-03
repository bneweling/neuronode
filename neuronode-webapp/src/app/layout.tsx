import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { StrictMode } from 'react'

import AppLayout from '@/components/layout/AppLayout'
import { ApiErrorContextProvider } from '@/contexts/ApiErrorContext'
import { CustomThemeProvider } from '@/contexts/ThemeContext'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Neuronode - KI-Wissenssystem',
  description: 'Intelligente Wissensverarbeitung mit KI',
  manifest: '/manifest.json',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="de">
      <head>
        <style>{`
          @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
          }
          
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
        `}</style>
      </head>
      <body className={inter.className}>
        <StrictMode>
          <CustomThemeProvider>
            <ApiErrorContextProvider>
              <AppLayout>
                {children}
              </AppLayout>
            </ApiErrorContextProvider>
          </CustomThemeProvider>
        </StrictMode>
      </body>
    </html>
  )
}
