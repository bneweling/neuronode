'use client'

import {
  Home as HomeIcon,
  Chat as ChatIcon,
  AccountTree as GraphIcon,
  CloudUpload as UploadIcon,
  Menu as MenuIcon,
  AutoAwesome as AIIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material'
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import { useRouter, usePathname } from 'next/navigation'
import { useState } from 'react'

interface NavigationItem {
  id: string
  label: string
  icon: React.ElementType
  description: string
  path: string
}

interface AppLayoutProps {
  children: React.ReactNode
}

export default function AppLayout({ children }: AppLayoutProps) {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const router = useRouter()
  const pathname = usePathname()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

  const navigationItems: NavigationItem[] = [
    { 
      id: 'overview', 
      label: 'Startseite', 
      icon: HomeIcon,
      description: 'Übersicht und Schnellzugriff',
      path: '/'
    },
    { 
      id: 'chat', 
      label: 'KI-Chat', 
      icon: ChatIcon,
      description: 'Intelligente Unterhaltung',
      path: '/chat'
    },
    { 
      id: 'graph', 
      label: 'Wissensgraph', 
      icon: GraphIcon,
      description: 'Datenvisualisierung',
      path: '/graph'
    },
    { 
      id: 'upload', 
      label: 'Dokumente', 
      icon: UploadIcon,
      description: 'Datei-Management',
      path: '/upload'
    },

    { 
      id: 'settings', 
      label: 'Einstellungen', 
      icon: SettingsIcon,
      description: 'Demo/Produktions-Modus',
      path: '/settings'
    },
  ]

  const handleNavigation = (path: string) => {
    router.push(path)
    setDrawerOpen(false)
  }

  const getCurrentPageTitle = () => {
    const currentItem = navigationItems.find(item => item.path === pathname)
    return currentItem ? currentItem.label : 'Neuronode'
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* AppBar */}
      <AppBar position="static" elevation={0}>
        <Toolbar>
          {isMobile && (
            <IconButton
              edge="start"
              color="inherit"
              aria-label="menu"
              data-testid="mobile-menu-button"
              onClick={() => setDrawerOpen(true)}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          
          <Box display="flex" alignItems="center" gap={2} sx={{ flexGrow: 1 }}>
            <AIIcon sx={{ fontSize: 32 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
              {getCurrentPageTitle()}
            </Typography>
          </Box>

          {!isMobile && (
            <Box display="flex" gap={1}>
              {navigationItems.filter(item => item.id !== 'settings').map((item) => (
                <Button
                  key={item.id}
                  color="inherit"
                  startIcon={<item.icon />}
                  data-testid={`${item.id}-nav`}
                  onClick={() => handleNavigation(item.path)}
                  sx={{
                    textTransform: 'none',
                    backgroundColor: pathname === item.path ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    }
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Box>
          )}

          {/* Settings Icon - Always visible */}
          <IconButton
            color="inherit"
            data-testid="settings-nav"
            onClick={() => handleNavigation('/settings')}
            sx={{
              backgroundColor: pathname === '/settings' ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
              }
            }}
          >
            <SettingsIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Mobile Navigation Drawer */}
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        <Box sx={{ width: 280 }}>
          <Box p={2}>
            <Typography variant="h6" fontWeight="600">
              Navigation
            </Typography>
          </Box>
          <List>
            {navigationItems.map((item) => (
              <ListItem key={item.id} disablePadding>
                <ListItemButton 
                  onClick={() => handleNavigation(item.path)}
                  selected={pathname === item.path}
                  data-testid={`mobile-${item.id}-nav`}
                >
                  <ListItemIcon>
                    <item.icon />
                  </ListItemIcon>
                  <ListItemText 
                    primary={item.label}
                    secondary={item.description}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box component="main">
        {children}
      </Box>
    </Box>
  )
} 