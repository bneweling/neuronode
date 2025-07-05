'use client'

import React from 'react'
import { CssBaseline, ThemeProvider } from '@mui/material'

import { ApiErrorContextProvider } from '@/contexts/ApiErrorContext'
import { ApiClientProvider } from '@/contexts/ApiClientContext'
import { CustomThemeProvider } from '@/contexts/ThemeContext'
import { QueryProvider } from '@/components/providers/QueryProvider'
import { tablerTheme } from '@/theme/tabler-theme'
import TablerAppLayout from '@/components/layout/TablerAppLayout'

export function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <React.StrictMode>
      <ApiClientProvider>
        <CustomThemeProvider>
          <ThemeProvider theme={tablerTheme}>
            <CssBaseline />
            <ApiErrorContextProvider>
              <QueryProvider>
                <TablerAppLayout>{children}</TablerAppLayout>
              </QueryProvider>
            </ApiErrorContextProvider>
          </ThemeProvider>
        </CustomThemeProvider>
      </ApiClientProvider>
    </React.StrictMode>
  )
} 