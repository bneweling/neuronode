import { AppRouterCacheProvider } from '@mui/material-nextjs/v15-appRouter'
import type { Metadata } from 'next'

import GlobalErrorToast from '@/components/error/GlobalErrorToast'
import AppLayout from '@/components/layout/AppLayout'
import { ApiErrorContextProvider } from '@/contexts/ApiErrorContext'
import { CustomThemeProvider } from '@/contexts/ThemeContext'
import './globals.css'

export const metadata: Metadata = {
  title: "KI-Wissenssystem",
  description: "Intelligentes Wissensmanagement mit modernster Technologie",
  keywords: ["KI", "Wissenssystem", "Chat", "Graph", "Dokumenten-Upload"],
  authors: [{ name: "KI-Wissenssystem Team" }],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="de">
      <body>
        <AppRouterCacheProvider>
          <CustomThemeProvider>
            <ApiErrorContextProvider>
              <AppLayout>
                {children}
              </AppLayout>
              <GlobalErrorToast />
            </ApiErrorContextProvider>
          </CustomThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  )
}
