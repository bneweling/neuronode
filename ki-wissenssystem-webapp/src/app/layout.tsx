import type { Metadata } from 'next'
import './globals.css'
import { AppRouterCacheProvider } from '@mui/material-nextjs/v15-appRouter'
import AppLayout from '@/components/layout/AppLayout'
import { CustomThemeProvider } from '@/contexts/ThemeContext'

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
            <AppLayout>
              {children}
            </AppLayout>
          </CustomThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  )
}
