'use client'

import { useState } from 'react'
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Card,
  CardContent,
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
  Paper,
  Fade,
  Grow,
} from '@mui/material'
import {
  Home as HomeIcon,
  Chat as ChatIcon,
  AccountTree as GraphIcon,
  CloudUpload as UploadIcon,
  Menu as MenuIcon,
  Assessment as StatusIcon,
  AutoAwesome as AIIcon,
  School as KnowledgeIcon,

} from '@mui/icons-material'
import { useRouter } from 'next/navigation'
import QuickChatInterface from '@/components/chat/QuickChatInterface'

type ViewType = 'overview' | 'chat' | 'graph' | 'upload' | 'status'

interface NavigationItem {
  id: ViewType
  label: string
  icon: React.ElementType
  description: string
  path: string
}

export default function HomePage() {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const router = useRouter()
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
      id: 'status', 
      label: 'Systemstatus', 
      icon: StatusIcon,
      description: 'System-Überwachung',
      path: '/status'
    },
  ]

  const handleNavigation = (path: string) => {
    router.push(path)
    setDrawerOpen(false)
  }

  const FeatureCard = ({ title, description, icon: Icon, onClick }: {
    title: string
    description: string
    icon: React.ElementType
    onClick: () => void
  }) => (
    <Grow in timeout={1000}>
      <Card 
        elevation={2}
        sx={{ 
          height: '100%',
          cursor: 'pointer',
          transition: 'all 0.3s ease-in-out',
          '&:hover': {
            elevation: 8,
            transform: 'translateY(-4px)',
          }
        }}
        onClick={onClick}
      >
        <CardContent sx={{ textAlign: 'center', p: 3 }}>
          <Icon color="primary" sx={{ fontSize: 48, mb: 2 }} />
          <Typography variant="h6" gutterBottom fontWeight="600">
            {title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {description}
          </Typography>
        </CardContent>
      </Card>
    </Grow>
  )

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
              onClick={() => setDrawerOpen(true)}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          
          <Box display="flex" alignItems="center" gap={2}>
            <AIIcon sx={{ fontSize: 32 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
              KI-Wissenssystem
            </Typography>
          </Box>

          {!isMobile && (
            <Box display="flex" gap={1}>
              {navigationItems.map((item) => (
                <Button
                  key={item.id}
                  color="inherit"
                  startIcon={<item.icon />}
                  onClick={() => handleNavigation(item.path)}
                  sx={{
                    textTransform: 'none',
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
                <ListItemButton onClick={() => handleNavigation(item.path)}>
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
      <Container maxWidth="lg" sx={{ py: 6 }}>
        {/* Hero Section */}
        <Fade in timeout={800}>
          <Box textAlign="center" mb={6}>
            <Typography 
              variant="h2" 
              component="h1" 
              gutterBottom
              sx={{ 
                fontWeight: 300,
                background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 2
              }}
            >
              Willkommen im KI-Wissenssystem
            </Typography>
            <Typography 
              variant="h5" 
              color="text.secondary" 
              sx={{ maxWidth: 600, mx: 'auto', mb: 4, fontWeight: 300 }}
            >
              Ihr intelligenter Assistent für Wissensmanagement und Datenanalyse
            </Typography>
          </Box>
        </Fade>

        {/* Quick Chat Interface */}
        <Box mb={6} maxWidth="md" mx="auto">
          <QuickChatInterface />
        </Box>

        {/* Feature Cards */}
        <Box mb={6}>
          <Typography variant="h4" textAlign="center" gutterBottom sx={{ mb: 4 }}>
            Entdecken Sie die Funktionen
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <FeatureCard
                title="KI-Chat"
                description="Stellen Sie intelligente Fragen und erhalten Sie präzise Antworten"
                icon={ChatIcon}
                onClick={() => handleNavigation('/chat')}
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <FeatureCard
                title="Wissensgraph"
                description="Visualisieren Sie Verbindungen in Ihren Daten"
                icon={GraphIcon}
                onClick={() => handleNavigation('/graph')}
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <FeatureCard
                title="Dokumente"
                description="Laden Sie Dateien hoch und verwalten Sie Ihr Wissen"
                icon={UploadIcon}
                onClick={() => handleNavigation('/upload')}
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <FeatureCard
                title="System"
                description="Überwachen Sie Performance und Systemgesundheit"
                icon={StatusIcon}
                onClick={() => handleNavigation('/status')}
              />
            </Grid>
          </Grid>
        </Box>

        {/* Info Section */}
        <Fade in timeout={1200}>
          <Paper 
            elevation={2} 
            sx={{ 
              p: 4, 
              textAlign: 'center',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white'
            }}
          >
            <KnowledgeIcon sx={{ fontSize: 48, mb: 2 }} />
            <Typography variant="h5" gutterBottom fontWeight="600">
              Moderne KI-Technologie
            </Typography>
            <Typography variant="body1" sx={{ maxWidth: 600, mx: 'auto' }}>
              Nutzen Sie die Kraft von Large Language Models, Vektor-Datenbanken und 
              Graph-Technologien für intelligentes Wissensmanagement.
            </Typography>
          </Paper>
        </Fade>
      </Container>
    </Box>
  )
}
