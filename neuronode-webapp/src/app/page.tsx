'use client'

import {
  Chat as ChatIcon,
  AccountTree as GraphIcon,
  CloudUpload as UploadIcon,
  Assessment as StatusIcon,
  School as KnowledgeIcon,
  Science as DemoIcon,
  Cloud as ProductionIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material'
import {
  Container,
  Grid,
  Card,
  CardContent,
  Box,
  Paper,
  Fade,
  Grow,
  Typography,
  Chip,
  Alert,
} from '@mui/material'
import { useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'

import QuickChatInterface from '@/components/chat/QuickChatInterface'
import { useAppConfig } from '@/hooks/useAppConfig'
import { PerformanceMonitor } from '@/lib/performance'
import ChatInterface from '@/components/chat/ChatInterface'
import { TablerCard, TablerCardContent, TablerBox, TablerTypography, TablerContainer, TablerIcon, TablerIconSizes } from '@/components/ui'

export default function HomePage() {
  const router = useRouter()
  const { isDemo } = useAppConfig()
  const [isMounted, setIsMounted] = useState(false)

  // Performance Monitoring
  useEffect(() => {
    PerformanceMonitor.trackPageLoad('HomePage')
  }, [])

  // Verhindere Hydration-Fehler durch Warten auf Client-Side Mount
  useEffect(() => {
    setIsMounted(true)
  }, [])

  const handleNavigation = (path: string) => {
    router.push(path)
  }

  const FeatureCard = ({ title, description, icon: Icon, onClick }: {
    title: string
    description: string
    icon: React.ElementType
    onClick: () => void
  }) => (
    <Grow in timeout={1000}>
      <TablerCard variant="feature" onClick={onClick}>
        <TablerCardContent variant="feature">
          <TablerIcon icon={<Icon />} size={TablerIconSizes.HERO} color="primary" />
          <TablerTypography variant="h6" gutterBottom style={{ fontWeight: 600, marginTop: 16 }}>
            {title}
          </TablerTypography>
          <TablerTypography variant="body2" textVariant="muted">
            {description}
          </TablerTypography>
        </TablerCardContent>
      </TablerCard>
    </Grow>
  )

  return (
    <>
      <header>
        <h1 style={{ display: 'none' }}>Dashboard und Schnellzugriff</h1>
      </header>
      <TablerContainer variant="section" data-testid="home-container">
        {/* Mode Indicator - Nur nach Client Mount rendern */}
        {isMounted && (
          <TablerBox variant="flex-center" style={{ marginBottom: 24 }}>
            <Chip
              icon={isDemo ? <DemoIcon /> : <ProductionIcon />}
              label={isDemo ? 'Demo Modus' : 'Produktions Modus'}
              color={isDemo ? 'warning' : 'primary'}
              variant="filled"
              onClick={() => handleNavigation('/settings')}
              style={{ cursor: 'pointer' }}
            />
          </TablerBox>
        )}

        {isMounted && isDemo && (
          <Alert 
            severity="info" 
            style={{ marginBottom: 32, maxWidth: 800, marginLeft: 'auto', marginRight: 'auto' }}
            action={
              <Chip
                icon={<SettingsIcon />}
                label="Einstellungen"
                size="small"
                onClick={() => handleNavigation('/settings')}
                style={{ cursor: 'pointer' }}
              />
            }
          >
            Sie befinden sich im Demo-Modus. Alle Daten sind synthetisch und dienen nur zur Demonstration.
          </Alert>
        )}

        {/* Hero Section */}
        <Fade in timeout={800}>
          <TablerBox variant="hero" style={{ marginBottom: 48 }}>
            <TablerTypography 
              variant="h2" 
              textVariant="hero"
              gutterBottom
            >
              Willkommen im Neuronode
            </TablerTypography>
            <TablerTypography 
              variant="h5" 
              textVariant="description"
            >
              Ihr intelligenter Assistent für Wissensmanagement und Datenanalyse
            </TablerTypography>
          </TablerBox>
        </Fade>

        {/* Quick Chat Interface */}
        <TablerBox variant="section" style={{ marginBottom: 48, maxWidth: 768, marginLeft: 'auto', marginRight: 'auto' }}>
          <QuickChatInterface />
        </TablerBox>

        {/* Feature Cards - Optimiertes Layout */}
        <TablerBox variant="section" style={{ marginBottom: 48 }}>
          <TablerTypography variant="h4" textVariant="section-title">
            Entdecken Sie die Funktionen
          </TablerTypography>
          
          <Grid container spacing={4} justifyContent="center">
            <Grid item xs={12} sm={6} lg={3}>
              <FeatureCard
                title="KI-Chat"
                description="Stellen Sie intelligente Fragen und erhalten Sie präzise Antworten"
                icon={ChatIcon}
                onClick={() => handleNavigation('/chat')}
              />
            </Grid>
            
            <Grid item xs={12} sm={6} lg={3}>
              <FeatureCard
                title="Wissensgraph"
                description="Visualisieren Sie Verbindungen in Ihren Daten"
                icon={GraphIcon}
                onClick={() => handleNavigation('/graph')}
              />
            </Grid>
            
            <Grid item xs={12} sm={6} lg={3}>
              <FeatureCard
                title="Dokumente"
                description="Laden Sie Dateien hoch und verwalten Sie Ihr Wissen"
                icon={UploadIcon}
                onClick={() => handleNavigation('/upload')}
              />
            </Grid>
            
            <Grid item xs={12} sm={6} lg={3}>
              <FeatureCard
                title="System"
                description="Überwachen Sie Performance und Systemgesundheit"
                icon={StatusIcon}
                onClick={() => handleNavigation('/status')}
              />
            </Grid>
          </Grid>
        </TablerBox>

        {/* Info Section */}
        <Fade in timeout={1200}>
          <TablerCard variant="info">
            <TablerCardContent variant="centered">
              <TablerIcon icon={<KnowledgeIcon />} size={TablerIconSizes.HERO} color="inherit" />
              <TablerTypography variant="h5" gutterBottom style={{ fontWeight: 600, marginTop: 16 }}>
                Moderne KI-Technologie
              </TablerTypography>
              <TablerTypography variant="body1" style={{ maxWidth: 600, marginLeft: 'auto', marginRight: 'auto' }}>
                Nutzen Sie die Kraft von Large Language Models, Vektor-Datenbanken und
                Graph-Technologien für intelligentes Wissensmanagement.
              </TablerTypography>
            </TablerCardContent>
          </TablerCard>
        </Fade>
      </TablerContainer>
    </>
  )
}
