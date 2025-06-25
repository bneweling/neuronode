'use client'

import { useState, useEffect } from 'react'
import ChatInterface from '@/components/chat/ChatInterface'
import GraphVisualization from '@/components/graph/GraphVisualization'
import FileUploadZone from '@/components/upload/FileUploadZone'
import { getAPIClient } from '@/lib/api'

type ViewType = 'overview' | 'chat' | 'graph' | 'upload'

interface SystemStatus {
  api: boolean
  vectorStore: boolean
  graphDb: boolean
  lastCheck: string
}

interface NavigationItem {
  id: ViewType
  label: string
  icon: string
  selectedIcon: string
}

export default function HomePage() {
  const [currentView, setCurrentView] = useState<ViewType>('overview')
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    api: false,
    vectorStore: false,
    graphDb: false,
    lastCheck: 'Nie'
  })
  const [isLoading, setIsLoading] = useState(true)
  const [isMobile, setIsMobile] = useState(false)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)

  // System Status Check
  useEffect(() => {
    const checkSystemStatus = async () => {
      setIsLoading(true)
      try {
        const apiClient = getAPIClient()
        const health = await apiClient.healthCheck()
        setSystemStatus({
          api: health.status === 'healthy',
          vectorStore: health.components?.vector_store === 'healthy' || false,
          graphDb: health.components?.graph_db === 'healthy' || false,
          lastCheck: new Date().toLocaleTimeString('de-DE')
        })
      } catch (error) {
        console.error('Systemstatus-Check fehlgeschlagen:', error)
        setSystemStatus(prev => ({
          ...prev,
          api: false,
          lastCheck: new Date().toLocaleTimeString('de-DE')
        }))
      } finally {
        setIsLoading(false)
      }
    }

    checkSystemStatus()
    const interval = setInterval(checkSystemStatus, 30000) // Alle 30 Sekunden
    return () => clearInterval(interval)
  }, [])

  // Mobile Detection & Escape Key Handler
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 840)
    }
    
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsDrawerOpen(false)
      }
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    window.addEventListener('keydown', handleEscape)
    
    return () => {
      window.removeEventListener('resize', checkMobile)
      window.removeEventListener('keydown', handleEscape)
    }
  }, [])

  const navigationItems: NavigationItem[] = [
    { id: 'overview', label: 'Übersicht', icon: 'dashboard', selectedIcon: 'dashboard' },
    { id: 'chat', label: 'KI-Chat', icon: 'chat_bubble_outline', selectedIcon: 'chat_bubble' },
    { id: 'graph', label: 'Wissensgraph', icon: 'account_tree', selectedIcon: 'account_tree' },
    { id: 'upload', label: 'Dokumente', icon: 'upload_file', selectedIcon: 'upload_file' },
  ]

  const handleNavigation = (viewId: ViewType) => {
    setCurrentView(viewId)
    setIsDrawerOpen(false)
  }

  const renderCurrentView = () => {
    switch (currentView) {
      case 'overview':
        return (
          <div className="p-4">
            {/* Header */}
            <div className="surface-card">
              <h1 className="headline-large">KI-Wissenssystem</h1>
              <p className="body-large mt-4">
                Willkommen im intelligenten Wissensmanagementsystem mit Material Design 3
              </p>
            </div>

            {/* System Status */}
            <div className="surface-card">
              <h2 className="title-large">Systemstatus</h2>
              <div className="flex flex-col gap-3 mt-4">
                <div className="flex items-center justify-between">
                  <span className="body-medium">API-Server</span>
                  <div className={`status-indicator ${systemStatus.api ? 'status-online' : 'status-offline'}`}>
                    <span className="material-symbols-outlined">
                      {systemStatus.api ? 'check_circle' : 'error'}
                    </span>
                    <span>{systemStatus.api ? 'Online' : 'Offline'}</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="body-medium">Vektordatenbank</span>
                  <div className={`status-indicator ${systemStatus.vectorStore ? 'status-online' : 'status-offline'}`}>
                    <span className="material-symbols-outlined">
                      {systemStatus.vectorStore ? 'check_circle' : 'error'}
                    </span>
                    <span>{systemStatus.vectorStore ? 'Verbunden' : 'Getrennt'}</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="body-medium">Graph-Datenbank</span>
                  <div className={`status-indicator ${systemStatus.graphDb ? 'status-online' : 'status-offline'}`}>
                    <span className="material-symbols-outlined">
                      {systemStatus.graphDb ? 'check_circle' : 'error'}
                    </span>
                    <span>{systemStatus.graphDb ? 'Verbunden' : 'Getrennt'}</span>
                  </div>
                </div>
                
                <hr className="my-4" style={{ borderColor: 'var(--md-sys-color-outline-variant)' }} />
                <div className="flex items-center justify-between">
                  <span className="body-medium">Letzte Prüfung</span>
                  <span className="body-medium">{systemStatus.lastCheck}</span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="surface-card">
              <h2 className="title-large">Schnellzugriff</h2>
              <div className="flex flex-wrap gap-3 mt-4">
                <button 
                  className="md-filled-button"
                  onClick={() => handleNavigation('chat')}
                >
                  <span className="material-symbols-outlined">chat</span>
                  KI-Chat starten
                </button>
                
                <button 
                  className="md-outlined-button"
                  onClick={() => handleNavigation('upload')}
                >
                  <span className="material-symbols-outlined">upload_file</span>
                  Dokumente hochladen
                </button>
                
                <button 
                  className="md-outlined-button"
                  onClick={() => handleNavigation('graph')}
                >
                  <span className="material-symbols-outlined">account_tree</span>
                  Wissensgraph erkunden
                </button>
              </div>
            </div>
          </div>
        )
      
      case 'chat':
        return <ChatInterface />
      
      case 'graph':
        return <GraphVisualization />
      
      case 'upload':
        return <FileUploadZone />
      
      default:
        return <div>Unbekannte Ansicht</div>
    }
  }

  return (
    <div className="app-container">
      {/* App Bar mit Hamburger Menu */}
      <header className="app-header">
        <div className="flex items-center gap-3">
          <button
            className="hamburger-button"
            onClick={() => setIsDrawerOpen(true)}
            aria-label="Navigation öffnen"
          >
            <span className="material-symbols-outlined">menu</span>
          </button>
          <h1 className="title-large">KI-Wissenssystem</h1>
        </div>
        
        <div className="flex items-center gap-2">
          <span className={`status-indicator ${systemStatus.api ? 'status-online' : 'status-offline'}`}>
            <span className="material-symbols-outlined">
              {systemStatus.api ? 'wifi' : 'wifi_off'}
            </span>
          </span>
        </div>
      </header>

      {/* Navigation Drawer Overlay */}
      {isDrawerOpen && (
        <div 
          className="drawer-overlay"
          onClick={() => setIsDrawerOpen(false)}
        />
      )}

      {/* Navigation Drawer */}
      <nav className={`navigation-drawer ${isDrawerOpen ? 'open' : ''}`}>
        <div className="drawer-header">
          <div className="flex items-center justify-between">
            <h2 className="title-large">Navigation</h2>
            <button
              className="close-button"
              onClick={() => setIsDrawerOpen(false)}
              aria-label="Navigation schließen"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>
        </div>
        
        <div className="drawer-content">
          {navigationItems.map((item) => (
            <button
              key={item.id}
              className={`nav-drawer-item ${currentView === item.id ? 'active' : ''}`}
              onClick={() => handleNavigation(item.id)}
            >
              <span className="material-symbols-outlined">
                {currentView === item.id ? item.selectedIcon : item.icon}
              </span>
              <span className="body-medium">{item.label}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* Main Content */}
      <main className="app-main-content">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="flex flex-col items-center gap-4">
              <div className="loading-spinner"></div>
              <span className="body-medium">System wird geladen...</span>
            </div>
          </div>
        ) : (
          renderCurrentView()
        )}
      </main>

      {/* Mobile Bottom Navigation (nur bei geschlossenem Drawer) */}
      {isMobile && !isDrawerOpen && (
        <nav className="mobile-nav">
          {navigationItems.map((item) => (
            <button
              key={item.id}
              className={`mobile-nav-item ${currentView === item.id ? 'active' : ''}`}
              onClick={() => handleNavigation(item.id)}
            >
              <span className="material-symbols-outlined">
                {currentView === item.id ? item.selectedIcon : item.icon}
              </span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      )}

      {/* Floating Action Button für Chat */}
      {currentView !== 'chat' && !isDrawerOpen && (
        <button
          className="fab"
          onClick={() => handleNavigation('chat')}
          aria-label="Chat öffnen"
        >
          <span className="material-symbols-outlined">chat</span>
        </button>
      )}
    </div>
  )
}
