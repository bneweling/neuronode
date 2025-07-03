'use client'

import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
  ExpandMore as ExpandMoreIcon,
  AccountTree as GraphIcon,
  Article as DocumentIcon,
  Tag as TagIcon,
} from '@mui/icons-material'
import {
  Box,
  Paper,
  Typography,
  TextField,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Chip,
  Container,
  Grid,
  IconButton,
  Divider,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  useTheme,
  Tooltip,
  LinearProgress,
  CircularProgress,
  Button,
} from '@mui/material'
import type { Core, NodeSingular, EventObject } from 'cytoscape'
import { useState, useEffect, useRef, useCallback, useMemo } from 'react'

import InlineErrorDisplay from '@/components/error/InlineErrorDisplay'
import { useDebounce } from '@/hooks/useDebounce'
import { useGraphState, useGraphStats } from '@/hooks/useGraphState'
import { useWebSocketWithReconnect } from '@/hooks/useWebSocketWithReconnect'

// === TYPE DEFINITIONS ===
interface GraphNode {
  id: string
  label: string
  type: 'document' | 'concept' | 'entity'
  properties: Record<string, unknown>
}

interface GraphEdge {
  id: string
  source: string
  target: string
  label: string
  weight: number
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

type NodeColor = 'primary' | 'secondary' | 'success' | 'default'

/**
 * Enterprise Graph Visualization Component
 * 
 * SOLUTION FOR FLICKER PROBLEM:
 * 1. Uses stable useGraphState hook instead of local useState
 * 2. Separates data fetching from component lifecycle
 * 3. useEffect only runs once for Cytoscape initialization
 * 4. Data changes are handled through stable callbacks
 * 5. StrictMode compliant with proper cleanup
 */
export default function GraphVisualization() {
  const theme = useTheme()
  
  // === ENTERPRISE GRAPH STATE ===
  // Single source of truth for graph data - eliminates flicker
  const { graphState, actions, isLoading, hasData, hasError } = useGraphState()
  const stats = useGraphStats()
  
  // === UI STATE (Ephemeral - kept local) ===
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [zoomLevel, setZoomLevel] = useState(1)
  const [isMounted, setIsMounted] = useState(false)
  const [cytoscapeLoaded, setCytoscapeLoaded] = useState(false)
  const [cytoscapeError, setCytoscapeError] = useState<string | null>(null)
  
  // Advanced Interactivity State
  const [hoveredElement, setHoveredElement] = useState<{
    type: 'node' | 'edge'
    data: any
    position: { x: number; y: number }
  } | null>(null)
  const [highlightedElements, setHighlightedElements] = useState<Set<string>>(new Set())
  
  // Live Updates State
  const [liveUpdates, setLiveUpdates] = useState<{
    type: 'node_added' | 'relationship_created' | 'graph_optimized'
    data: any
    timestamp: number
  }[]>([])
  
  // === REFS ===
  const graphRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)
  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  // === ENHANCED WEBSOCKET WITH RECONNECTION ===
  const {
    connectionState: wsConnectionState,
    connectionStats: wsConnectionStats,
    isConnected: wsConnected,
    isConnecting: wsConnecting,
    hasFailed: wsHasFailed,
    reconnect: wsReconnect,
    configure: wsConfigureConnection
  } = useWebSocketWithReconnect('ws://localhost:8001/ws/graph', {
    onMessage: (event) => {
      try {
        const message = JSON.parse(event.data)
        
        setLiveUpdates(prev => [...prev.slice(-9), {
          type: message.type,
          data: message.data,
          timestamp: Date.now()
        }])
        
        // Handle live updates
        switch (message.type) {
          case 'node_added':
            handleLiveNodeAdded(message.data)
            break
          case 'relationship_created':
            handleLiveRelationshipCreated(message.data)
            break
          case 'graph_optimized':
            handleLiveGraphOptimized(message.data)
            break
          default:
            console.log('Unknown WebSocket message type:', message.type)
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    },
    onOpen: () => {
      console.log('Graph WebSocket connected with enhanced reconnection')
    },
    onClose: () => {
      console.log('Graph WebSocket disconnected')
    },
    onError: (error) => {
      console.error('Graph WebSocket error:', error)
    },
    config: {
      initialDelay: 1000,      // 1 second
      maxDelay: 30000,         // 30 seconds  
      maxAttempts: 10,         // 10 attempts
      backoffFactor: 2,        // Exponential backoff
      enableJitter: true,      // Prevent thundering herd
      timeoutDuration: 5000    // 5 second connection timeout
    },
    autoConnect: true
  })
  
  // === STABLE MEMOIZED VALUES ===
  // Prevent unnecessary re-computations that could trigger flicker
  const graphData = useMemo(() => graphState.data, [graphState.data])
  const hasGraphData = useMemo(() => Boolean(graphData && graphData.nodes.length > 0), [graphData])
  
  // === DEBOUNCED HANDLERS ===
  const debouncedSearch = useDebounce((query: string) => {
    if (!cyRef.current || !query.trim()) return
    
    // Filter and highlight nodes based on search
    const searchTerm = query.toLowerCase()
    const matchingNodes = new Set<string>()
    
    cyRef.current.nodes().forEach((node) => {
      const label = node.data('label')?.toLowerCase() || ''
      const type = node.data('type')?.toLowerCase() || ''
      
      if (label.includes(searchTerm) || type.includes(searchTerm)) {
        matchingNodes.add(node.data('id'))
      }
    })
    
    setHighlightedElements(matchingNodes)
    
    // Apply visual highlighting
    cyRef.current.elements().forEach((element) => {
      const elementId = element.data('id')
      if (matchingNodes.has(elementId)) {
        element.removeClass('faded')
        element.addClass('highlighted-node')
      } else {
        element.removeClass('highlighted-node')
        element.addClass('faded')
      }
    })
  }, 300)
  
  const debouncedNodeClick = useDebounce((nodeId: string) => {
    if (!graphData || !graphData.nodes) return
    
    const node = graphData.nodes.find(n => n.id === nodeId)
    if (node) {
      // Stelle sicher, dass properties existiert
      setSelectedNode({
        ...node,
        properties: node.properties || {}
      })
    }
  }, 150)

  // === INITIALIZATION EFFECT (RUNS ONCE) ===
  useEffect(() => {
    setIsMounted(true)
    
    // Load initial graph data
    if (graphState.status === 'idle') {
      console.log('Loading initial graph data...')
      actions.loadGraphData()
    }
    
    return () => {
      setIsMounted(false)
    }
  }, []) // CRITICAL: Empty dependency array - runs only once!

  // === CYTOSCAPE INITIALIZATION (STABLE) ===
  // This effect only runs when we have new data or the component mounts
  useEffect(() => {
    if (!isMounted || !hasGraphData || !graphRef.current) return

    const initializeCytoscape = async () => {
      try {
        const cytoscape = (await import('cytoscape')).default

        // Clean up existing instance
        if (cyRef.current) {
          cyRef.current.destroy()
          cyRef.current = null
        }

        // Create elements from stable data
        const elements = [
          // Nodes
          ...graphData!.nodes.map(node => ({
            data: {
              id: node.id,
              label: node.label,
              type: node.type,
              ...node.properties
            },
            classes: `node-${node.type}`
          })),
          // Edges
          ...graphData!.edges.map(edge => ({
            data: {
              id: edge.id,
              source: edge.source,
              target: edge.target,
              label: edge.label,
              weight: edge.weight
            },
            classes: 'edge'
          }))
        ]

        // Theme-aware styling
        const isDarkMode = theme.palette.mode === 'dark'
        const edgeColor = isDarkMode ? '#b0b0b0' : '#666'
        const edgeLabelColor = isDarkMode ? '#ffffff' : '#333'
        const nodeTextColor = isDarkMode ? '#ffffff' : '#333333'
        const nodeOutlineColor = isDarkMode ? 'rgba(0,0,0,0.9)' : 'rgba(255,255,255,0.9)'

        // Node colors
        const nodeColors = {
          document: isDarkMode ? '#4fc3f7' : '#1976d2',
          concept: isDarkMode ? '#ba68c8' : '#9c27b0',
          entity: isDarkMode ? '#81c784' : '#388e3c',
          default: isDarkMode ? '#90a4ae' : '#616161'
        }

        // Initialize Cytoscape with stable configuration
        cyRef.current = cytoscape({
          container: graphRef.current,
          elements,
          style: [
            // Base node styles
            {
              selector: 'node',
              style: {
                'width': 65,
                'height': 65,
                'label': 'data(label)',
                'text-valign': 'center',
                'text-halign': 'center',
                'color': nodeTextColor,
                'text-outline-width': 2,
                'text-outline-color': nodeOutlineColor,
                'font-size': isDarkMode ? 13 : 12,
                'font-weight': isDarkMode ? 'bold' : 'normal',
                'text-wrap': 'wrap',
                'text-max-width': 80,
                'min-zoomed-font-size': 8,
                'text-opacity': isDarkMode ? 1 : 0.9,
                'border-width': isDarkMode ? 2 : 1,
                'border-style': 'solid',
                'border-opacity': 0.7
              } as any
            },
            // Document nodes
            {
              selector: '.node-document',
              style: {
                'background-color': nodeColors.document,
                'shape': 'rectangle',
                'border-color': isDarkMode ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.3)'
              }
            },
            // Concept nodes
            {
              selector: '.node-concept',
              style: {
                'background-color': nodeColors.concept,
                'shape': 'ellipse',
                'border-color': isDarkMode ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.3)'
              }
            },
            // Entity nodes
            {
              selector: '.node-entity',
              style: {
                'background-color': nodeColors.entity,
                'shape': 'diamond',
                'border-color': isDarkMode ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.3)'
              }
            },
            // Edge styles
            {
              selector: 'edge',
              style: {
                'width': isDarkMode ? 3 : 2,
                'line-color': edgeColor,
                'target-arrow-color': edgeColor,
                'target-arrow-shape': 'triangle',
                'curve-style': 'bezier',
                'label': 'data(label)',
                'font-size': isDarkMode ? '11px' : '10px',
                'color': edgeLabelColor,
                'text-rotation': 'autorotate',
                'text-margin-y': -12,
                'text-outline-width': isDarkMode ? 2 : 1,
                'text-outline-color': isDarkMode ? 'rgba(0,0,0,0.9)' : 'rgba(255,255,255,0.9)'
              }
            },
            // Interaction styles
            {
              selector: 'node:hover',
              style: {
                'border-width': 3,
                'border-color': isDarkMode ? '#4fc3f7' : '#1976d2',
                'border-opacity': 1
              }
            },
            {
              selector: '.highlighted-node',
              style: {
                'border-width': 4,
                'border-color': theme.palette.primary.main,
                'opacity': 1,
                'z-index': 999
              }
            },
            {
              selector: '.highlighted-neighbor',
              style: {
                'border-width': 3,
                'border-color': theme.palette.secondary.main,
                'opacity': 0.8,
                'z-index': 900
              }
            },
            {
              selector: '.faded',
              style: {
                'opacity': 0.2,
                'text-opacity': 0.2
              }
            }
          ],
          layout: {
            name: 'cose',
            idealEdgeLength: () => 100,
            nodeOverlap: 20,
            refresh: 20,
            randomize: false,
            componentSpacing: 100,
            nodeRepulsion: () => 400000,
            edgeElasticity: () => 100,
            nestingFactor: 5,
            gravity: 80,
            numIter: 1000,
            initialTemp: 200,
            coolingFactor: 0.95,
            minTemp: 1.0
          } as any
        })

        // === EVENT HANDLERS (STABLE) ===
        // Node hover
        cyRef.current.on('mouseover', 'node', (evt: EventObject) => {
          const node = evt.target
          const nodeData = node.data()
          const position = node.renderedPosition()
          
          if (hoverTimeoutRef.current) {
            clearTimeout(hoverTimeoutRef.current)
          }
          
          hoverTimeoutRef.current = setTimeout(() => {
            setHoveredElement({
              type: 'node',
              data: {
                id: nodeData.id,
                label: nodeData.label,
                type: nodeData.type,
                typeIcon: nodeData.type
              },
              position: { x: position.x, y: position.y }
            })
          }, 300)
        })

        // Edge hover
        cyRef.current.on('mouseover', 'edge', (evt: EventObject) => {
          const edge = evt.target
          const edgeData = edge.data()
          const renderedMidpoint = edge.renderedMidpoint()
          
          if (hoverTimeoutRef.current) {
            clearTimeout(hoverTimeoutRef.current)
          }
          
          hoverTimeoutRef.current = setTimeout(() => {
            setHoveredElement({
              type: 'edge',
              data: {
                id: edgeData.id,
                label: edgeData.label,
                weight: edgeData.weight,
                source: edgeData.source,
                target: edgeData.target
              },
              position: { x: renderedMidpoint.x, y: renderedMidpoint.y }
            })
          }, 300)
        })

        // Mouse out
        cyRef.current.on('mouseout', 'node,edge', () => {
          if (hoverTimeoutRef.current) {
            clearTimeout(hoverTimeoutRef.current)
            hoverTimeoutRef.current = null
          }
          setHoveredElement(null)
        })

        // Node click
        cyRef.current.on('tap', 'node', (evt: EventObject) => {
          const node = evt.target
          const nodeId = node.data('id')
          
          // Highlight clicked node and neighbors
          const neighbors = node.neighborhood()
          const highlightedIds = new Set([nodeId])
          
          neighbors.forEach((neighbor) => {
            highlightedIds.add(neighbor.data('id'))
          })
          
          setHighlightedElements(highlightedIds)
          
          // Visual styling
          cyRef.current!.elements().forEach((element) => {
            const elementId = element.data('id')
            if (highlightedIds.has(elementId)) {
              element.removeClass('faded')
              element.addClass(elementId === nodeId ? 'highlighted-node' : 'highlighted-neighbor')
            } else {
              element.removeClass('highlighted-node highlighted-neighbor')
              element.addClass('faded')
            }
          })
          
          // Debounced node click handler
          debouncedNodeClick(nodeId)
        })

        // Zoom handler
        cyRef.current.on('zoom', () => {
          if (cyRef.current) {
            setZoomLevel(cyRef.current.zoom())
          }
        })

        setCytoscapeLoaded(true)
        console.log('Cytoscape initialized successfully with', elements.length, 'elements')

      } catch (error) {
        console.error('Fehler bei der Cytoscape-Initialisierung:', error)
        setCytoscapeError('Graph-Visualisierung konnte nicht initialisiert werden')
      }
    }

    initializeCytoscape()

    // Cleanup function for StrictMode compliance
    return () => {
      if (cyRef.current) {
        try {
          cyRef.current.destroy()
        } catch (error) {
          console.error('Fehler beim Cytoscape Cleanup:', error)
        }
        cyRef.current = null
      }
      setCytoscapeLoaded(false)
    }
  }, [hasGraphData, isMounted, theme.palette.mode]) // STABLE DEPENDENCIES

  // === SEARCH EFFECT ===
  useEffect(() => {
    if (searchQuery.trim()) {
      debouncedSearch(searchQuery)
    } else {
      // Clear search highlighting
      setHighlightedElements(new Set())
      if (cyRef.current) {
        cyRef.current.elements().removeClass('faded highlighted-node')
      }
    }
  }, [searchQuery, debouncedSearch])

  // WebSocket connection is now managed by useWebSocketWithReconnect hook above

  // === LIVE UPDATE HANDLERS ===
  const handleLiveNodeAdded = useCallback((nodeData: GraphNode) => {
    if (!cyRef.current || !graphData || !graphData.nodes) return
    
    try {
      const newNode = cyRef.current.add({
        data: {
          id: nodeData.id,
          label: nodeData.label,
          type: nodeData.type,
          ...nodeData.properties
        },
        classes: `node-${nodeData.type}`
      })
      
      newNode.style('opacity', 0)
      newNode.animate({
        style: { opacity: 1 },
        duration: 500,
        easing: 'ease-out'
      })
      
      // Update graph state
      actions.updateGraphData({
        ...graphData,
        nodes: [...graphData.nodes, nodeData]
      })
      
    } catch (error) {
      console.error('Error adding live node:', error)
    }
  }, [graphData, actions])

  const handleLiveRelationshipCreated = useCallback((edgeData: GraphEdge) => {
    if (!cyRef.current || !graphData || !graphData.edges) return
    
    try {
      const newEdge = cyRef.current.add({
        data: {
          id: edgeData.id,
          source: edgeData.source,
          target: edgeData.target,
          label: edgeData.label,
          weight: edgeData.weight
        }
      })
      
      newEdge.style('opacity', 0)
      newEdge.animate({
        style: { opacity: 1 },
        duration: 500,
        easing: 'ease-out'
      })
      
      // Update graph state
      actions.updateGraphData({
        ...graphData,
        edges: [...graphData.edges, edgeData]
      })
      
    } catch (error) {
      console.error('Error adding live relationship:', error)
    }
  }, [graphData, actions])

  const handleLiveGraphOptimized = useCallback((optimizationData: { type: string, changes: number }) => {
    if (!cyRef.current) return
    
    try {
      const layout = cyRef.current.layout({
        name: 'cose',
        idealEdgeLength: () => 100,
        animate: true,
        animationDuration: 1000,
        animationEasing: 'ease-out'
      })
      
      layout.run()
      console.log(`Graph optimized: ${optimizationData.type}, ${optimizationData.changes} changes`)
    } catch (error) {
      console.error('Error optimizing graph:', error)
    }
  }, [])

  // === UI ACTION HANDLERS ===
  const handleSearch = () => {
    debouncedSearch(searchQuery)
  }

  const handleZoomIn = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 1.2)
    }
  }

  const handleZoomOut = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() / 1.2)
    }
  }

  const handleCenter = () => {
    if (cyRef.current) {
      cyRef.current.fit()
      setSelectedNode(null)
      setHighlightedElements(new Set())
      cyRef.current.elements().removeClass('faded highlighted-node highlighted-neighbor')
    }
  }

  const handleRefresh = () => {
    actions.refreshGraph()
  }

  // === UI HELPER FUNCTIONS ===
  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'document':
        return <DocumentIcon />
      case 'concept':
        return <GraphIcon />
      case 'entity':
        return <TagIcon />
      default:
        return <GraphIcon />
    }
  }

  const getNodeColor = (type: string): NodeColor => {
    switch (type) {
      case 'document':
        return 'primary'
      case 'concept':
        return 'secondary'
      case 'entity':
        return 'success'
      default:
        return 'default'
    }
  }

  const getNodeConnections = (nodeId: string) => {
    if (!graphData || !graphData.edges) return []
    return graphData.edges.filter(edge => 
      edge.source === nodeId || edge.target === nodeId
    )
  }

  // === RENDER CONDITIONS ===
  if (!isMounted) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }} data-testid="graph-container-loading">
        <Box mb={4}>
          <Typography variant="h4" component="h1" gutterBottom>
            Wissensgraph
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Graph wird geladen...
          </Typography>
        </Box>
      </Container>
    )
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }} data-testid="graph-container">
      <Box mb={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          Wissensgraph
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Interaktive Visualisierung der Beziehungen in Ihrem Wissenssystem
        </Typography>
      </Box>

      {/* Error Display */}
      {hasError && (
        <InlineErrorDisplay 
          source="graph"
          variant="alert"
          showRetryButton={true}
          onRetry={handleRefresh}
        />
      )}
      
      {/* Cytoscape-specific errors */}
      {cytoscapeError && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setCytoscapeError(null)}>
          {cytoscapeError}
          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
            Als Alternative können Sie die Knoten-Liste in der Seitenleiste verwenden.
          </Typography>
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Sidebar */}
        <Grid item xs={12} lg={4}>
          <Paper elevation={2} sx={{ p: 3, mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <SearchIcon color="primary" />
              <Typography variant="h6">Graph-Steuerung</Typography>
            </Box>
            
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Knoten oder Konzepte suchen..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              sx={{ mb: 2 }}
              size="small"
            />
            
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Tooltip title="Vergrößern">
                <IconButton onClick={handleZoomIn} size="small">
                  <ZoomInIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Verkleinern">
                <IconButton onClick={handleZoomOut} size="small">
                  <ZoomOutIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Zentrieren">
                <IconButton onClick={handleCenter} size="small">
                  <CenterIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Aktualisieren">
                <IconButton onClick={handleRefresh} size="small" disabled={isLoading}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            </Box>
            
            <Typography variant="body2" color="text.secondary">
              Zoom: {Math.round(zoomLevel * 100)}%
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
              <Box 
                sx={{ 
                  width: 8, 
                  height: 8, 
                  borderRadius: '50%',
                  bgcolor: wsConnected ? 'success.main' : 'error.main',
                  animation: wsConnected ? 'none' : 'pulse 2s infinite'
                }}
              />
              <Typography variant="caption" color="text.secondary">
                Live-Updates {wsConnected ? 'aktiv' : 'getrennt'}
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Main Graph Area */}
        <Grid item xs={12} lg={8}>
          <Paper 
            elevation={2} 
            sx={{ 
              height: 600, 
              position: 'relative',
              bgcolor: (theme) => 
                theme.palette.mode === 'dark' 
                  ? 'rgba(18, 18, 18, 0.95)' 
                  : 'rgba(250, 250, 250, 0.95)',
              border: (theme) =>
                theme.palette.mode === 'dark'
                  ? '1px solid rgba(255, 255, 255, 0.1)'
                  : '1px solid rgba(0, 0, 0, 0.1)'
            }}
          >
            {/* Loading Overlay */}
            {isLoading && (
              <Box 
                sx={{ 
                  position: 'absolute', 
                  top: 0, 
                  left: 0, 
                  right: 0, 
                  bottom: 0, 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  bgcolor: (theme) => 
                    theme.palette.mode === 'dark' 
                      ? 'rgba(18, 18, 18, 0.8)' 
                      : 'rgba(255,255,255,0.8)',
                  zIndex: 1
                }}
              >
                <CircularProgress />
                <Typography sx={{ ml: 2 }}>Graph wird geladen...</Typography>
              </Box>
            )}
            
            {/* Graph Container */}
            <div
              ref={graphRef}
              style={{
                width: '100%',
                height: '100%',
                borderRadius: '8px',
                backgroundColor: theme.palette.mode === 'dark' ? '#121212' : '#fafafa'
              }}
            />
            
            {/* Cytoscape Loading */}
            {!cytoscapeLoaded && hasGraphData && (
              <Box 
                sx={{ 
                  position: 'absolute', 
                  top: 0, 
                  left: 0, 
                  right: 0, 
                  bottom: 0, 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  bgcolor: (theme) => 
                    theme.palette.mode === 'dark' 
                      ? 'rgba(18, 18, 18, 0.9)' 
                      : 'rgba(255,255,255,0.9)',
                  zIndex: 1
                }}
              >
                <CircularProgress />
                <Typography sx={{ ml: 2 }}>Cytoscape wird geladen...</Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Selected Node Details */}
        <Grid item xs={12} lg={4}>
          {selectedNode && (
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  {getNodeIcon(selectedNode.type)}
                  <Typography variant="h6" sx={{ ml: 1 }}>
                    {selectedNode.label}
                  </Typography>
                  <Chip 
                    label={selectedNode.type} 
                    color={getNodeColor(selectedNode.type)}
                    size="small" 
                    sx={{ ml: 'auto' }}
                  />
                </Box>
                
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle2">Eigenschaften</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {selectedNode.properties && Object.entries(selectedNode.properties).length > 0 ? (
                        Object.entries(selectedNode.properties).map(([key, value]) => (
                          <ListItem key={key}>
                            <ListItemText 
                              primary={key}
                              secondary={String(value)}
                            />
                          </ListItem>
                        ))
                      ) : (
                        <ListItem>
                          <ListItemText 
                            primary="Keine Eigenschaften verfügbar"
                            secondary="Dieser Knoten hat keine zusätzlichen Eigenschaften"
                          />
                        </ListItem>
                      )}
                    </List>
                  </AccordionDetails>
                </Accordion>
                
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle2">
                      Verbindungen ({getNodeConnections(selectedNode.id).length})
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {getNodeConnections(selectedNode.id).map((edge) => (
                        <ListItem key={edge.id}>
                          <ListItemText 
                            primary={edge.label}
                            secondary={`Gewichtung: ${Math.round(edge.weight * 100)}%`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              </CardContent>
            </Card>
          )}

          {/* Graph Statistics */}
          <Card data-testid="graph-stats">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Graph-Statistiken
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="Gesamte Knoten"
                    secondary={stats.totalNodes}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Gesamte Kanten"
                    secondary={stats.totalEdges}
                  />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText 
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <DocumentIcon sx={{ mr: 1, color: '#1976d2' }} />
                        Dokumente
                      </Box>
                    }
                    secondary={stats.documentNodes}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <GraphIcon sx={{ mr: 1, color: '#9c27b0' }} />
                        Konzepte
                      </Box>
                    }
                    secondary={stats.conceptNodes}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <TagIcon sx={{ mr: 1, color: '#2e7d32' }} />
                        Entitäten
                      </Box>
                    }
                    secondary={stats.entityNodes}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>

          {/* WebSocket Connection Status */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Live-Verbindung
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box 
                          sx={{ 
                            width: 12, 
                            height: 12, 
                            borderRadius: '50%',
                            bgcolor: wsConnected ? '#4caf50' : wsConnecting ? '#ff9800' : '#f44336',
                            mr: 1,
                            animation: wsConnecting ? 'pulse 1.5s infinite' : 'none'
                          }} 
                        />
                        Status
                      </Box>
                    }
                    secondary={
                      wsConnected ? 'Verbunden' : 
                      wsConnecting ? 'Verbindet...' : 
                      wsHasFailed ? 'Verbindung fehlgeschlagen' : 
                      'Getrennt'
                    }
                  />
                </ListItem>
                {wsConnectionStats.totalAttempts > 0 && (
                  <>
                    <ListItem>
                      <ListItemText 
                        primary="Verbindungsqualität"
                        secondary={wsConnectionStats.connectionQuality}
                      />
                      <Box sx={{ ml: 1 }}>
                        <Chip 
                          label={wsConnectionStats.connectionQuality}
                          color={
                            wsConnectionStats.connectionQuality === 'excellent' ? 'success' :
                            wsConnectionStats.connectionQuality === 'good' ? 'primary' :
                            wsConnectionStats.connectionQuality === 'poor' ? 'warning' : 'error'
                          }
                          size="small"
                        />
                      </Box>
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Erfolgsrate"
                        secondary={`${Math.round((wsConnectionStats.successfulConnections / wsConnectionStats.totalAttempts) * 100)}%`}
                      />
                    </ListItem>
                    {wsConnectionStats.averageConnectionTime > 0 && (
                      <ListItem>
                        <ListItemText 
                          primary="Ø Verbindungszeit"
                          secondary={`${Math.round(wsConnectionStats.averageConnectionTime)}ms`}
                        />
                      </ListItem>
                    )}
                  </>
                )}
                {wsHasFailed && (
                  <ListItem>
                    <Button 
                      variant="outlined" 
                      size="small" 
                      onClick={wsReconnect}
                      sx={{ mt: 1 }}
                    >
                      Erneut verbinden
                    </Button>
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Hover Tooltip */}
      {hoveredElement && (
        <Box
          sx={{
            position: 'fixed',
            left: hoveredElement.position.x + 10,
            top: hoveredElement.position.y - 10,
            zIndex: 9999,
            pointerEvents: 'none',
            bgcolor: (theme) => 
              theme.palette.mode === 'dark' 
                ? 'rgba(0, 0, 0, 0.9)' 
                : 'rgba(255, 255, 255, 0.95)',
            color: (theme) => theme.palette.text.primary,
            p: 1.5,
            borderRadius: 1,
            border: (theme) => `1px solid ${theme.palette.divider}`,
            boxShadow: 3,
            maxWidth: 300,
            animation: 'fadeIn 0.2s ease-out'
          }}
        >
          {hoveredElement.type === 'node' ? (
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                {getNodeIcon(hoveredElement.data.typeIcon)}
                <Typography variant="body2" fontWeight="bold" sx={{ ml: 1 }}>
                  {hoveredElement.data.label}
                </Typography>
              </Box>
              <Typography variant="caption" color="text.secondary">
                ID: {hoveredElement.data.id}
              </Typography>
            </Box>
          ) : (
            <Box>
              <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>
                {hoveredElement.data.label}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Gewichtung:
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={hoveredElement.data.weight * 100} 
                  sx={{ 
                    flexGrow: 1, 
                    height: 4,
                    borderRadius: 2,
                    bgcolor: (theme) => theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  {Math.round(hoveredElement.data.weight * 100)}%
                </Typography>
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                {hoveredElement.data.source} → {hoveredElement.data.target}
              </Typography>
            </Box>
          )}
        </Box>
      )}
    </Container>
  )
} 