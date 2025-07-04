'use client'

import { CssBaseline } from '@mui/material'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import React, { createContext, useContext, useState, useEffect } from 'react'

import { lightPalette, darkPalette } from '@/theme/tokens'

type ThemeMode = 'light' | 'dark' | 'system'

interface ThemeContextType {
  mode: ThemeMode
  isDark: boolean
  toggleTheme: () => void
  setThemeMode: (mode: ThemeMode) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

interface CustomThemeProviderProps {
  children: React.ReactNode
}

export function CustomThemeProvider({ children }: CustomThemeProviderProps) {
  const [mode, setMode] = useState<ThemeMode>('system')
  const [systemPrefersDark, setSystemPrefersDark] = useState(false)

  // Detect system preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    setSystemPrefersDark(mediaQuery.matches)

    const handleChange = (e: MediaQueryListEvent) => {
      setSystemPrefersDark(e.matches)
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  // Load saved preference
  useEffect(() => {
    const savedMode = localStorage.getItem('theme-mode') as ThemeMode
    if (savedMode && ['light', 'dark', 'system'].includes(savedMode)) {
      setMode(savedMode)
    }
  }, [])

  // Save preference
  useEffect(() => {
    localStorage.setItem('theme-mode', mode)
  }, [mode])

  const isDark = mode === 'dark' || (mode === 'system' && systemPrefersDark)

  const paletteTokens = isDark ? darkPalette : lightPalette

  const theme = createTheme({
    palette: {
      mode: isDark ? 'dark' : 'light',
      ...paletteTokens,
    },
    shape: {
      borderRadius: 12,
    },
    components: {
      MuiCard: {
        styleOverrides: {
          root: {
            backgroundColor: isDark ? '#1e1e1e' : '#ffffff',
            backgroundImage: 'none',
            border: isDark ? '1px solid rgba(255, 255, 255, 0.12)' : '1px solid rgba(0, 0, 0, 0.12)',
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundColor: isDark ? '#1e1e1e' : '#1976d2',
            backgroundImage: 'none',
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 500,
          },
        },
      },
    },
  })

  const toggleTheme = () => {
    setMode(current => current === 'light' ? 'dark' : 'light')
  }

  const setThemeMode = (newMode: ThemeMode) => {
    setMode(newMode)
  }

  const contextValue: ThemeContextType = {
    mode,
    isDark,
    toggleTheme,
    setThemeMode,
  }

  return (
    <ThemeContext.Provider value={contextValue}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ThemeContext.Provider>
  )
} 