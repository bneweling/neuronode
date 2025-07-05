import { createTheme } from '@mui/material/styles'

// Tabler-inspired professional design system
export const tablerTheme = createTheme({
  palette: {
    primary: {
      main: '#206bc4',
      light: '#4dabf7',
      dark: '#1862ab',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#6c757d',
      light: '#adb5bd',
      dark: '#495057',
      contrastText: '#ffffff',
    },
    success: {
      main: '#2fb344',
      light: '#51cf66',
      dark: '#2b8a3e',
      contrastText: '#ffffff',
    },
    warning: {
      main: '#f59f00',
      light: '#ffd43b',
      dark: '#f08c00',
      contrastText: '#ffffff',
    },
    error: {
      main: '#d63384',
      light: '#e64980',
      dark: '#c92a2a',
      contrastText: '#ffffff',
    },
    info: {
      main: '#17a2b8',
      light: '#3bc9db',
      dark: '#1098ad',
      contrastText: '#ffffff',
    },
    background: {
      default: '#f8f9fa',
      paper: '#ffffff',
    },
    text: {
      primary: '#2c3e50',
      secondary: '#6c757d',
    },
    divider: '#e9ecef',
  },
  typography: {
    fontFamily: '"Inter", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    h1: {
      fontSize: '2rem',
      fontWeight: 600,
      color: '#2c3e50',
    },
    h2: {
      fontSize: '1.75rem',
      fontWeight: 600,
      color: '#2c3e50',
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
      color: '#2c3e50',
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 600,
      color: '#2c3e50',
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 600,
      color: '#2c3e50',
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      color: '#2c3e50',
    },
    subtitle1: {
      fontSize: '0.875rem',
      fontWeight: 500,
      color: '#6c757d',
    },
    subtitle2: {
      fontSize: '0.75rem',
      fontWeight: 500,
      color: '#6c757d',
    },
    body1: {
      fontSize: '0.875rem',
      color: '#2c3e50',
    },
    body2: {
      fontSize: '0.75rem',
      color: '#6c757d',
    },
    caption: {
      fontSize: '0.6875rem',
      color: '#6c757d',
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          border: '1px solid #e9ecef',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 6,
          fontWeight: 500,
          fontSize: '0.875rem',
        },
        contained: {
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          '&:hover': {
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 6,
            backgroundColor: '#ffffff',
            '& fieldset': {
              borderColor: '#e9ecef',
            },
            '&:hover fieldset': {
              borderColor: '#206bc4',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#206bc4',
            },
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          border: '1px solid #e9ecef',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          fontSize: '0.75rem',
          fontWeight: 500,
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          '&:hover': {
            backgroundColor: 'rgba(32, 107, 196, 0.08)',
          },
        },
      },
    },
  },
})

// Tabler-specific utility styles
export const tablerStyles = {
  // Widget styles for dashboard cards
  widget: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    border: '1px solid #e9ecef',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
    padding: '1.5rem',
    '&:hover': {
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
    },
  },
  
  // Stats number styling
  statNumber: {
    fontSize: '2rem',
    fontWeight: 700,
    color: '#2c3e50',
    lineHeight: 1.2,
  },
  
  // Stats label styling
  statLabel: {
    fontSize: '0.875rem',
    color: '#6c757d',
    fontWeight: 500,
  },
  
  // Percentage indicators
  percentagePositive: {
    color: '#2fb344',
    fontSize: '0.75rem',
    fontWeight: 600,
  },
  
  percentageNegative: {
    color: '#d63384',
    fontSize: '0.75rem',
    fontWeight: 600,
  },
  
  // Icon containers
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '1rem',
  },
  
  // Status indicators
  statusIndicator: {
    width: 8,
    height: 8,
    borderRadius: '50%',
    display: 'inline-block',
    marginRight: '0.5rem',
  },
  
  // Sidebar navigation
  sidebarNav: {
    backgroundColor: '#ffffff',
    borderRight: '1px solid #e9ecef',
    height: '100vh',
    position: 'fixed',
    left: 0,
    top: 0,
    width: 280,
    zIndex: 1000,
  },
  
  // Main content area
  mainContent: {
    marginLeft: 280,
    padding: '2rem',
    backgroundColor: '#f8f9fa',
    minHeight: '100vh',
  },
  
  // Page header
  pageHeader: {
    marginBottom: '2rem',
    '& h1': {
      fontSize: '1.875rem',
      fontWeight: 600,
      color: '#2c3e50',
      marginBottom: '0.5rem',
    },
    '& p': {
      fontSize: '0.875rem',
      color: '#6c757d',
      margin: 0,
    },
  },
}

export default tablerTheme 