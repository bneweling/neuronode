import type { Metadata } from 'next'
import './globals.css'
import { AppRouterCacheProvider } from '@mui/material-nextjs/v15-appRouter'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { theme } from '@/lib/theme'

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
          <ThemeProvider theme={theme}>
            <CssBaseline />
            {children}
          </ThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  )
}
