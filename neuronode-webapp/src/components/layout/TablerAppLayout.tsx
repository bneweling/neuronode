'use client'

import {
  Home as HomeIcon,
  Chat as ChatIcon,
  AccountTree as GraphIcon,
  CloudUpload as UploadIcon,
  Settings as SettingsIcon,
  AutoAwesome as AIIcon,
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
  Notifications as NotificationsIcon,
  Circle as CircleIcon,
  Close as CloseIcon,
} from '@mui/icons-material'
import {
  Box,
  Drawer,
  SwipeableDrawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  AppBar,
  Toolbar,
  IconButton,
  Badge,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  useMediaQuery,
  useTheme,
  alpha,
  Backdrop,
  Fab,
  Zoom,
  useScrollTrigger,
  Slide,
} from '@mui/material'
import { useRouter, usePathname } from 'next/navigation'
import { useState, useEffect, useCallback, useMemo } from 'react'

interface NavigationItem {
  id: string
  label: string
  icon: React.ElementType
  path: string
  badge?: number
}

interface TablerAppLayoutProps {
  children: React.ReactNode
}

const DRAWER_WIDTH = 280

export default function TablerAppLayout({ children }: TablerAppLayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [userMenuAnchorEl, setUserMenuAnchorEl] = useState<null | HTMLElement>(null)
  const [isOnline, setIsOnline] = useState(true)
  const router = useRouter()
  const pathname = usePathname()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const isTablet = useMediaQuery(theme.breakpoints.between('md', 'lg'))
  const trigger = useScrollTrigger({
    disableHysteresis: true,
    threshold: 0,
  })

  // Network status detection
  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  // Prevent body scroll when drawer is open on mobile
  useEffect(() => {
    if (isMobile && mobileOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isMobile, mobileOpen])

  const navigationItems: NavigationItem[] = [
    { 
      id: 'dashboard', 
      label: 'Dashboard', 
      icon: DashboardIcon,
      path: '/'
    },
    { 
      id: 'chat', 
      label: 'KI-Chat', 
      icon: ChatIcon,
      path: '/chat',
      badge: 3
    },
    { 
      id: 'graph', 
      label: 'Wissensgraph', 
      icon: GraphIcon,
      path: '/graph'
    },
    { 
      id: 'upload', 
      label: 'Dokumente', 
      icon: UploadIcon,
      path: '/upload'
    },
    { 
      id: 'settings', 
      label: 'Einstellungen', 
      icon: SettingsIcon,
      path: '/settings'
    },
  ]

  const handleDrawerToggle = useCallback(() => {
    setMobileOpen(!mobileOpen)
  }, [mobileOpen])

  const handleDrawerClose = useCallback(() => {
    setMobileOpen(false)
  }, [])

  const handleDrawerOpen = useCallback(() => {
    setMobileOpen(true)
  }, [])

  const handleNavigation = useCallback((path: string) => {
    router.push(path)
    if (isMobile) {
      setMobileOpen(false)
    }
  }, [router, isMobile])

  const handleUserMenuOpen = useCallback((event: React.MouseEvent<HTMLElement>) => {
    setUserMenuAnchorEl(event.currentTarget)
  }, [])

  const handleUserMenuClose = useCallback(() => {
    setUserMenuAnchorEl(null)
  }, [])

  const getCurrentPageTitle = useMemo(() => {
    const currentItem = navigationItems.find(item => item.path === pathname)
    return currentItem ? currentItem.label : 'Neuronode'
  }, [pathname, navigationItems])

  // Enhanced touch gesture support
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    const touch = e.touches[0]
    const startX = touch.clientX
    
    const handleTouchMove = (e: TouchEvent) => {
      const touch = e.touches[0]
      const currentX = touch.clientX
      const diffX = currentX - startX
      
      // Swipe right to open drawer (from left edge)
      if (startX < 20 && diffX > 50 && !mobileOpen) {
        setMobileOpen(true)
        document.removeEventListener('touchmove', handleTouchMove)
      }
      
      // Swipe left to close drawer
      if (mobileOpen && diffX < -50) {
        setMobileOpen(false)
        document.removeEventListener('touchmove', handleTouchMove)
      }
    }
    
    document.addEventListener('touchmove', handleTouchMove, { passive: true })
    
    const handleTouchEnd = () => {
      document.removeEventListener('touchmove', handleTouchMove)
      document.removeEventListener('touchend', handleTouchEnd)
    }
    
    document.addEventListener('touchend', handleTouchEnd)
  }, [mobileOpen])

  const drawer = (
    <Box sx={{ 
      height: '100%', 
      backgroundColor: '#ffffff',
      borderRight: '1px solid #e9ecef',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Logo/Brand */}
      <Box sx={{ 
        p: 3, 
        borderBottom: '1px solid #e9ecef',
        display: 'flex',
        alignItems: 'center',
        gap: 2
      }}>
        <Box sx={{
          width: 40,
          height: 40,
          borderRadius: 2,
          backgroundColor: '#206bc4',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <AIIcon sx={{ color: '#ffffff', fontSize: 24 }} />
        </Box>
        <Box>
          <Typography variant="h6" sx={{ 
            fontWeight: 700, 
            color: '#2c3e50',
            fontSize: '1.125rem'
          }}>
            Neuronode
          </Typography>
          <Typography variant="caption" sx={{ 
            color: '#6c757d',
            fontSize: '0.75rem'
          }}>
            AI Knowledge Platform
          </Typography>
        </Box>
      </Box>

      {/* Navigation */}
      <List sx={{ flex: 1, px: 2, py: 1 }} role="menubar">
        {navigationItems.map((item) => (
          <ListItem key={item.id} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton 
              onClick={() => handleNavigation(item.path)}
              selected={pathname === item.path}
              role="menuitem"
              aria-current={pathname === item.path ? 'page' : undefined}
              aria-label={`${item.label}${item.badge ? ` - ${item.badge} neue Nachrichten` : ''}`}
              sx={{
                borderRadius: 2,
                py: 1.5,
                px: 2,
                '&.Mui-selected': {
                  backgroundColor: alpha('#206bc4', 0.1),
                  color: '#206bc4',
                  '&:hover': {
                    backgroundColor: alpha('#206bc4', 0.15),
                  },
                  '& .MuiListItemIcon-root': {
                    color: '#206bc4',
                  },
                },
                '&:hover': {
                  backgroundColor: alpha('#206bc4', 0.05),
                },
              }}
            >
              <ListItemIcon sx={{ 
                minWidth: 40,
                color: pathname === item.path ? '#206bc4' : '#6c757d'
              }}>
                {item.badge ? (
                  <Badge badgeContent={item.badge} color="error">
                    <item.icon />
                  </Badge>
                ) : (
                  <item.icon />
                )}
              </ListItemIcon>
              <ListItemText 
                primary={item.label}
                primaryTypographyProps={{
                  fontSize: '0.875rem',
                  fontWeight: pathname === item.path ? 600 : 500,
                  color: pathname === item.path ? '#206bc4' : '#2c3e50',
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* Status Section */}
      <Box sx={{ p: 2, borderTop: '1px solid #e9ecef' }}>
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 1,
          p: 2,
          borderRadius: 2,
          backgroundColor: alpha(isOnline ? '#2fb344' : '#dc3545', 0.1),
          border: '1px solid #e9ecef'
        }}>
          <CircleIcon sx={{ 
            color: isOnline ? '#2fb344' : '#dc3545',
            fontSize: 8,
            animation: 'pulse 2s infinite'
          }} />
          <Box>
            <Typography variant="caption" sx={{ 
              color: '#2c3e50',
              fontWeight: 600,
              fontSize: '0.75rem'
            }}>
              {isOnline ? 'Online' : 'Offline'}
            </Typography>
            <Typography variant="caption" sx={{ 
              color: '#6c757d',
              display: 'block',
              fontSize: '0.6875rem'
            }}>
              {isOnline ? 'Alle Services verfügbar' : 'Keine Verbindung'}
            </Typography>
          </Box>
        </Box>
      </Box>
    </Box>
  )

  return (
    <Box 
      sx={{ display: 'flex', minHeight: '100vh' }}
      onTouchStart={isMobile ? handleTouchStart : undefined}
    >
      {/* Skip Link for Accessibility */}
      <Box 
        component="a" 
        href="#main-content"
        sx={{
          position: 'absolute',
          top: -40,
          left: 6,
          backgroundColor: '#206bc4',
          color: 'white',
          padding: '8px',
          textDecoration: 'none',
          borderRadius: '4px',
          zIndex: 1000,
          '&:focus': {
            top: 6,
          },
        }}
      >
        Zum Hauptinhalt springen
      </Box>

      {/* Mobile Backdrop */}
      {isMobile && mobileOpen && (
        <Backdrop
          open={mobileOpen}
          onClick={handleDrawerClose}
          sx={{
            zIndex: theme.zIndex.drawer - 1,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
          }}
        />
      )}

      {/* AppBar as Header */}
      <Slide appear={false} direction="down" in={!trigger || !isMobile}>
        <AppBar 
          component="header"
          role="banner"
          position="fixed" 
          elevation={trigger && isMobile ? 4 : 0}
          sx={{ 
            width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
            ml: { md: `${DRAWER_WIDTH}px` },
            backgroundColor: '#ffffff',
            borderBottom: '1px solid #e9ecef',
            boxShadow: trigger && isMobile ? theme.shadows[4] : 'none',
            transition: theme.transitions.create(['box-shadow', 'elevation'], {
              duration: theme.transitions.duration.short,
            }),
          }}
        >
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton
              color="inherit"
              aria-label="Hauptnavigation öffnen"
              aria-expanded={mobileOpen}
              aria-controls="navigation-menu"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ 
                mr: 2, 
                display: { md: 'none' },
                color: '#2c3e50'
              }}
            >
              <MenuIcon />
            </IconButton>
            <Box>
              <Typography variant="h6" sx={{ 
                color: '#2c3e50', 
                fontWeight: 600,
                fontSize: isMobile ? '1rem' : '1.125rem'
              }}>
                {getCurrentPageTitle}
              </Typography>
              {!isMobile && (
                <Typography variant="caption" sx={{ 
                  color: '#6c757d',
                  fontSize: '0.75rem'
                }}>
                  Verwalten Sie Ihr Wissenssystem
                </Typography>
              )}
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton 
              size="large"
              aria-label="Benachrichtigungen - 4 neue Nachrichten"
              sx={{ color: '#6c757d' }}
            >
              <Badge badgeContent={4} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
            
            <IconButton 
              onClick={handleUserMenuOpen}
              size="small"
              aria-label="Benutzermenü öffnen"
              aria-expanded={Boolean(userMenuAnchorEl)}
              aria-controls="user-menu"
              sx={{ ml: 2 }}
            >
              <Avatar 
                sx={{ 
                  width: 32, 
                  height: 32,
                  backgroundColor: '#206bc4',
                  fontSize: '0.875rem'
                }}
              >
                U
              </Avatar>
            </IconButton>
          </Box>
                  </Toolbar>
        </AppBar>
      </Slide>

      {/* Navigation Drawer */}
      <Box
        component="nav"
        role="navigation"
        aria-label="Hauptnavigation"
        sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}
      >
        {isMobile ? (
          <SwipeableDrawer
            variant="temporary"
            open={mobileOpen}
            onClose={handleDrawerClose}
            onOpen={handleDrawerOpen}
            ModalProps={{
              keepMounted: true,
            }}
            PaperProps={{
              id: "navigation-menu",
            }}
            sx={{
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: DRAWER_WIDTH,
                border: 'none',
                boxShadow: theme.shadows[8],
              },
            }}
            disableBackdropTransition
            disableDiscovery
          >
            {drawer}
          </SwipeableDrawer>
        ) : (
          <Drawer
            variant="permanent"
            open={true}
            PaperProps={{
              id: "navigation-menu",
            }}
            sx={{
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: DRAWER_WIDTH,
                border: 'none',
                boxShadow: 'none',
              },
            }}
          >
            {drawer}
          </Drawer>
        )}
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        role="main"
        id="main-content"
        tabIndex={-1}
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          backgroundColor: '#f8f9fa',
          minHeight: '100vh',
          pt: 8,
        }}
      >
        {children}
      </Box>

      {/* Mobile FAB for quick actions */}
      {isMobile && (
        <Zoom in={!mobileOpen}>
          <Fab
            color="primary"
            aria-label="Schnellzugriff Chat"
            onClick={() => handleNavigation('/chat')}
            sx={{
              position: 'fixed',
              bottom: 24,
              right: 24,
              zIndex: theme.zIndex.speedDial,
              backgroundColor: '#206bc4',
              '&:hover': {
                backgroundColor: '#1c5aa3',
              },
            }}
          >
            <ChatIcon />
          </Fab>
        </Zoom>
      )}

      {/* User Menu */}
      <Menu
        id="user-menu"
        anchorEl={userMenuAnchorEl}
        open={Boolean(userMenuAnchorEl)}
        onClose={handleUserMenuClose}
        MenuListProps={{
          'aria-labelledby': 'user-menu-button',
          role: 'menu',
        }}
        PaperProps={{
          elevation: 4,
          sx: {
            mt: 1.5,
            minWidth: 180,
            border: '1px solid #e9ecef',
            '& .MuiMenuItem-root': {
              fontSize: '0.875rem',
              py: 1.5,
            },
          },
        }}
      >
        <MenuItem onClick={handleUserMenuClose} role="menuitem">
          <PersonIcon sx={{ mr: 2, fontSize: 20 }} />
          Profil
        </MenuItem>
        <MenuItem onClick={handleUserMenuClose} role="menuitem">
          <SettingsIcon sx={{ mr: 2, fontSize: 20 }} />
          Einstellungen
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleUserMenuClose} role="menuitem">
          <LogoutIcon sx={{ mr: 2, fontSize: 20 }} />
          Abmelden
        </MenuItem>
      </Menu>
    </Box>
  )
} 