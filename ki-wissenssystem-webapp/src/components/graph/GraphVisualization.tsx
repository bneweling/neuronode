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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Step,
  Stepper,
  StepLabel,
  StepContent,
} from '@mui/material'
import type { Core, NodeSingular, EventObject } from 'cytoscape'
import { useState, useEffect, useRef, useCallback } from 'react'

import InlineErrorDisplay from '@/components/error/InlineErrorDisplay'
import { useGraphApi } from '@/hooks/useGraphApi'
import { useDebounce } from '@/hooks/useDebounce'


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

export default function GraphVisualization() {
  const theme = useTheme()
  const { 
    loadGraphData, 
    isLoading, 
    error, 
    clearError, 
    canRetry,
    isRetryableError 
  } = useGraphApi()
  
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] })
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [zoomLevel, setZoomLevel] = useState(1)
  const [isMounted, setIsMounted] = useState(false)
  const [cytoscapeLoaded, setCytoscapeLoaded] = useState(false)
  const [cytoscapeError, setCytoscapeError] = useState<string | null>(null)
  
  // K3.2 Task 2: Advanced Interactivity State
  const [hoveredElement, setHoveredElement] = useState<{
    type: 'node' | 'edge'
    data: any
    position: { x: number; y: number }
  } | null>(null)
  const [highlightedElements, setHighlightedElements] = useState<Set<string>>(new Set())
  
  // K3.2 Task 3: KI-Transparenz & Real-Time State
  const [selectedEdgeForCoT, setSelectedEdgeForCoT] = useState<{
    edge: GraphEdge
    cotData?: {
      reasoning: string
      chain_of_thought: string[]
      confidence: number
      ai_generated: boolean
    }
  } | null>(null)
  const [wsConnected, setWsConnected] = useState(false)
  const [liveUpdates, setLiveUpdates] = useState<{
    type: 'node_added' | 'relationship_created' | 'graph_optimized'
    data: any
    timestamp: number
  }[]>([])
  
  const graphRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    setIsMounted(true)
    const timer = setTimeout(() => {
      // Dynamisches Laden von Cytoscape nur im Browser
      import('cytoscape').then(() => {
        setCytoscapeLoaded(true)
      }).catch((loadError) => {
        console.error('Fehler beim Laden von Cytoscape:', loadError)
        setCytoscapeError('Graph-Bibliothek konnte nicht geladen werden')
      })
    }, 100)
    
    return () => clearTimeout(timer)
  }, [])

  // Load graph data on component mount
  useEffect(() => {
    const fetchGraphData = async () => {
      const data = await loadGraphData()
      if (data) {
        setGraphData(data)
      }
    }
    
    fetchGraphData()
  }, [loadGraphData])

  // K3.2 Task 2: API Call Debouncing für Search und Node-Interaktionen
  const debouncedSearch = useDebounce((query: string) => {
    if (!query.trim() || !cyRef.current) return
    
    const matchingNodes = cyRef.current.nodes().filter((node: NodeSingular) => {
      const label = node.data('label').toLowerCase()
      return label.includes(query.toLowerCase())
    })
    
    if (matchingNodes.length > 0) {
      cyRef.current.fit(matchingNodes, 100)
      const firstNode = matchingNodes[0]
      const nodeData = firstNode.data()
      setSelectedNode({
        id: nodeData.id,
        label: nodeData.label,
        type: nodeData.type,
        properties: nodeData
      })
    } else {
      console.log('Keine Knoten gefunden, die der Suche entsprechen.')
    }
  }, 250) // 250ms delay as specified

  const debouncedNodeClick = useDebounce(async (nodeId: string) => {
    console.log(`Node clicked with debouncing: ${nodeId}`)
    // Future: Load node details or expand node
    // const details = await expandNode(nodeId)
  }, 250)

  // K3.2 Task 3: Real-Time Event Handlers
  const handleLiveNodeAdded = useCallback((nodeData: GraphNode) => {
    if (!cyRef.current) return
    
    try {
      // Add new node to Cytoscape with smooth animation
      const newNode = cyRef.current.add({
        data: {
          id: nodeData.id,
          label: nodeData.label,
          type: nodeData.type,
          ...nodeData.properties
        },
        classes: `node-${nodeData.type}`
      })
      
      // Animate new node appearance
      newNode.style('opacity', 0)
      newNode.animate({
        style: { opacity: 1 },
        duration: 500,
        easing: 'ease-out'
      })
      
      // Update local state
      setGraphData(prev => ({
        ...prev,
        nodes: [...prev.nodes, nodeData]
      }))
      
      console.log(`Live node added: ${nodeData.label}`)
    } catch (error) {
      console.error('Error adding live node:', error)
    }
  }, [])

  const handleLiveRelationshipCreated = useCallback((edgeData: GraphEdge) => {
    if (!cyRef.current) return
    
    try {
      // Add new edge to Cytoscape with smooth animation
      const newEdge = cyRef.current.add({
        data: {
          id: edgeData.id,
          source: edgeData.source,
          target: edgeData.target,
          label: edgeData.label,
          weight: edgeData.weight
        }
      })
      
      // Animate new edge appearance
      newEdge.style('opacity', 0)
      newEdge.animate({
        style: { opacity: 1 },
        duration: 500,
        easing: 'ease-out'
      })
      
      // Update local state
      setGraphData(prev => ({
        ...prev,
        edges: [...prev.edges, edgeData]
      }))
      
      console.log(`Live relationship created: ${edgeData.label}`)
    } catch (error) {
      console.error('Error adding live relationship:', error)
    }
  }, [])

  const handleLiveGraphOptimized = useCallback((optimizationData: { type: string, changes: number }) => {
    if (!cyRef.current) return
    
    try {
      // Re-run layout with optimization
      const layout = cyRef.current.layout({
        name: 'cose',
        idealEdgeLength: () => 100,
        nodeOverlap: 20,
        refresh: 20,
        randomize: false,
        componentSpacing: 100,
        nodeRepulsion: () => 400000,
        edgeElasticity: () => 100,
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

  useEffect(() => {
    const initializeCytoscape = async () => {
        // Umfassende Checks für sichere Initialisierung
        if (!isMounted || !cytoscapeLoaded || !graphRef.current) {
          console.log('Cytoscape-Initialisierung übersprungen: Komponente nicht bereit')
          return
        }
    
        if (graphData.nodes.length === 0) {
          console.log('Cytoscape-Initialisierung übersprungen: Keine Daten')
            if (cyRef.current) {
                cyRef.current.destroy();
                cyRef.current = null;
            }
          return
        }
    
        // Sicherstellen, dass Container korrekte Dimensionen hat
        const containerRect = graphRef.current.getBoundingClientRect()
        if (containerRect.width === 0 || containerRect.height === 0) {
          console.log('Cytoscape-Initialisierung übersprungen: Container hat keine Dimensionen')
          setTimeout(initializeCytoscape, 100) // retry
          return
        }
    
        try {
          const cytoscape = (await import('cytoscape')).default;
    
          // Clean up existing instance
          if (cyRef.current) {
            cyRef.current.destroy()
          }
        
            // ... (rest of the function, exactly as it was in useCallback)
            const elements = [
                // Nodes
                ...graphData.nodes.map(node => ({
                  data: {
                    id: node.id,
                    label: node.label,
                    type: node.type,
                    ...node.properties
                  },
                  classes: `node-${node.type}`
                })),
                // Edges
                ...graphData.edges.map(edge => ({
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
          
              // Dark/Light mode colors with enhanced visibility
              const isDarkMode = theme.palette.mode === 'dark'
              const edgeColor = isDarkMode ? '#b0b0b0' : '#666'
              const edgeLabelColor = isDarkMode ? '#ffffff' : '#333'
              const nodeTextColor = isDarkMode ? '#ffffff' : '#333333'
              const nodeOutlineColor = isDarkMode ? 'rgba(0,0,0,0.9)' : 'rgba(255,255,255,0.9)'
              const nodeOutlineWidth = isDarkMode ? 3 : 2
              const nodeFontWeight = isDarkMode ? 'bold' : 'normal'
              
              // Enhanced color palette for better dark mode contrast
              const nodeColors = {
                document: isDarkMode ? '#4fc3f7' : '#1976d2',    // Lighter blue for dark mode
                concept: isDarkMode ? '#ba68c8' : '#9c27b0',     // Lighter purple for dark mode
                entity: isDarkMode ? '#81c784' : '#388e3c',      // Lighter green for dark mode
                relationship: isDarkMode ? '#ffb74d' : '#f57c00', // Lighter orange for dark mode
                default: isDarkMode ? '#90a4ae' : '#616161'      // Lighter grey for dark mode
              }
          
              // Initialize Cytoscape mit Error Handling
              cyRef.current = cytoscape({
                container: graphRef.current,
                elements,
                style: [
                // Enhanced Node styles with dark mode optimizations
                {
                  selector: 'node',
                  style: {
                    'width': 65,
                    'height': 65,
                    'label': 'data(label)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'color': nodeTextColor,
                    'text-outline-width': nodeOutlineWidth,
                    'text-outline-color': nodeOutlineColor,
                    'font-size': isDarkMode ? 13 : 12,
                    'font-weight': nodeFontWeight,
                    'text-wrap': 'wrap',
                    'text-max-width': 80,
                    'min-zoomed-font-size': 8,
                    'text-opacity': isDarkMode ? 1 : 0.9,
                    'border-width': isDarkMode ? 2 : 1,
                    'border-style': 'solid',
                    'border-opacity': 0.7
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  } as any
                },
                {
                  selector: '.node-document',
                  style: {
                    'background-color': nodeColors.document,
                    'shape': 'rectangle',
                    'border-color': isDarkMode ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.3)'
                  }
                },
                {
                  selector: '.node-concept',
                  style: {
                    'background-color': nodeColors.concept,
                    'shape': 'ellipse',
                    'border-color': isDarkMode ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.3)'
                  }
                },
                {
                  selector: '.node-entity',
                  style: {
                    'background-color': nodeColors.entity,
                    'shape': 'diamond',
                    'border-color': isDarkMode ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.3)'
                  }
                },
                // Enhanced Edge styles with improved dark mode visibility
                {
                  selector: 'edge',
                  style: {
                    'width': isDarkMode ? 3 : 2,
                    'line-color': edgeColor,
                    'target-arrow-color': edgeColor,
                    'target-arrow-shape': 'triangle',
                    'target-arrow-size': isDarkMode ? 12 : 10,
                    'curve-style': 'bezier',
                    'label': 'data(label)',
                    'font-size': isDarkMode ? '11px' : '10px',
                    'font-weight': isDarkMode ? '600' : 'normal',
                    'color': edgeLabelColor,
                    'text-rotation': 'autorotate',
                    'text-margin-y': -12,
                    'text-outline-width': isDarkMode ? 2 : 1,
                    'text-outline-color': isDarkMode ? 'rgba(0,0,0,0.9)' : 'rgba(255,255,255,0.9)',
                    'text-opacity': 1,
                    'line-opacity': isDarkMode ? 0.8 : 0.7,
                    'arrow-opacity': isDarkMode ? 0.8 : 0.7
                  }
                },
                // Enhanced Hover and Selection effects
                {
                  selector: 'node:hover',
                  style: {
                    'border-width': isDarkMode ? 3 : 2,
                    'border-color': isDarkMode ? '#4fc3f7' : '#1976d2',
                    'border-opacity': 1,
                    'font-size': isDarkMode ? '14px' : '13px'
                  }
                },
                {
                  selector: 'node:selected',
                  style: {
                    'border-width': isDarkMode ? 4 : 3,
                    'border-color': isDarkMode ? '#ff6b35' : '#ff5722',
                    'border-opacity': 1,
                    'text-outline-width': isDarkMode ? 4 : 3,
                    'box-shadow': isDarkMode ? '0 0 20px rgba(255, 107, 53, 0.6)' : '0 0 15px rgba(255, 87, 34, 0.4)'
                  }
                },
                {
                  selector: 'edge:hover',
                  style: {
                    'line-color': isDarkMode ? '#4fc3f7' : '#1976d2',
                    'target-arrow-color': isDarkMode ? '#4fc3f7' : '#1976d2',
                    'width': isDarkMode ? 4 : 3,
                    'font-size': isDarkMode ? '12px' : '11px',
                    'text-outline-width': isDarkMode ? 3 : 2
                  }
                },
                {
                  selector: 'edge:selected',
                  style: {
                    'line-color': isDarkMode ? '#ff6b35' : '#ff5722',
                    'target-arrow-color': isDarkMode ? '#ff6b35' : '#ff5722',
                    'width': isDarkMode ? 5 : 4,
                    'color': isDarkMode ? '#ff6b35' : '#ff5722',
                    'font-size': isDarkMode ? '13px' : '12px',
                    'text-outline-width': isDarkMode ? 3 : 2,
                    'font-weight': 'bold'
                  }
                },
                // K3.2 Task 2: Focus & Highlight Styles
                {
                  selector: '.highlighted-node',
                  style: {
                    'border-width': 4,
                    'border-color': theme.palette.primary.main,
                    'border-opacity': 1,
                    'opacity': 1,
                    'text-opacity': 1,
                    'font-weight': 'bold',
                    'z-index': 999
                  }
                },
                {
                  selector: '.highlighted-neighbor',
                  style: {
                    'opacity': 1,
                    'text-opacity': 1,
                    'border-width': 2,
                    'border-opacity': 0.8,
                    'z-index': 998
                  }
                },
                {
                  selector: '.faded',
                  style: {
                    'opacity': 0.2,
                    'text-opacity': 0.2,
                    'line-opacity': 0.2,
                    'arrow-opacity': 0.2,
                    'z-index': 1
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
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
              } as any
            })
        
            // K3.2 Task 2: Enhanced Event Handlers für Advanced Interactivity
            if (cyRef.current) {
              
              // K3.2 Task 2: Intelligent Hover Tooltips (300ms enterDelay anti-flicker)
              let hoverTimeout: NodeJS.Timeout | null = null
              
              cyRef.current.on('mouseover', 'node', (evt: EventObject) => {
                const node = evt.target as NodeSingular
                const nodeData = node.data()
                const renderedPosition = node.renderedPosition()
                
                // Clear existing timeout
                if (hoverTimeout) {
                  clearTimeout(hoverTimeout)
                }
                
                // 300ms delay as specified for anti-flicker
                hoverTimeout = setTimeout(() => {
                  setHoveredElement({
                    type: 'node',
                    data: {
                      id: nodeData.id,
                      label: nodeData.label,
                      type: nodeData.type,
                      typeIcon: nodeData.type, // For icon display
                    },
                    position: { x: renderedPosition.x, y: renderedPosition.y }
                  })
                }, 300)
              })
              
              cyRef.current.on('mouseover', 'edge', (evt: EventObject) => {
                const edge = evt.target
                const edgeData = edge.data()
                const renderedMidpoint = edge.renderedMidpoint()
                
                if (hoverTimeout) {
                  clearTimeout(hoverTimeout)
                }
                
                hoverTimeout = setTimeout(() => {
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
              
              cyRef.current.on('mouseout', 'node,edge', () => {
                if (hoverTimeout) {
                  clearTimeout(hoverTimeout)
                  hoverTimeout = null
                }
                setHoveredElement(null)
              })
              
              // K3.2 Task 2: Focus & Highlight mit Click-Interaktionen
              cyRef.current.on('tap', 'node', (evt: EventObject) => {
                const node = evt.target as NodeSingular
                const nodeData = node.data()
                const nodeId = nodeData.id
                
                // Set selected node for sidebar
                const graphNode: GraphNode = {
                  id: nodeData.id,
                  label: nodeData.label,
                  type: nodeData.type,
                  properties: nodeData
                }
                setSelectedNode(graphNode)
                
                // K3.2 Task 2: Focus & Highlight Logic
                if (cyRef.current) {
                  // Get clicked node and its neighbors
                  const clickedNode = cyRef.current.getElementById(nodeId)
                  const neighbors = clickedNode.neighborhood().nodes()
                  
                  // Create highlighted set
                  const highlightedIds = new Set<string>()
                  highlightedIds.add(nodeId) // clicked node
                  
                  neighbors.forEach((neighbor: NodeSingular) => {
                    highlightedIds.add(neighbor.data('id'))
                  })
                  
                  setHighlightedElements(highlightedIds)
                  
                  // Apply visual styling: highlighted nodes = 100% opacity, others = 20%
                  cyRef.current.elements().forEach((element) => {
                    const elementId = element.data('id')
                    if (highlightedIds.has(elementId) || 
                        (element.isEdge() && 
                         (highlightedIds.has(element.data('source')) || 
                          highlightedIds.has(element.data('target'))))) {
                      // Highlighted elements: full opacity
                      element.removeClass('faded')
                      element.addClass(elementId === nodeId ? 'highlighted-node' : 'highlighted-neighbor')
                    } else {
                      // Faded elements: 20% opacity
                      element.removeClass('highlighted-node highlighted-neighbor')
                      element.addClass('faded')
                    }
                  })
                  
                  // Enhanced border for clicked node with theme primary color
                  clickedNode.addClass('highlighted-node')
                }
                
                // K3.2 Task 2: Debounced API Call für Node-Details
                debouncedNodeClick(nodeId)
              })
              
              // K3.2 Task 3: Edge Click für Chain-of-Thought Transparenz
              cyRef.current.on('tap', 'edge', (evt: EventObject) => {
                const edge = evt.target
                const edgeData = edge.data()
                
                // Find the edge in our graph data
                const graphEdge = graphData.edges.find(e => e.id === edgeData.id)
                if (graphEdge) {
                  setSelectedEdgeForCoT({
                    edge: graphEdge,
                    cotData: {
                      reasoning: 'Diese Beziehung wurde von der KI basierend auf semantischen Ähnlichkeiten zwischen den Konzepten erstellt.',
                      chain_of_thought: [
                        'Schritt 1: Textanalyse der beiden Konzepte durchgeführt',
                        'Schritt 2: Semantische Ähnlichkeit mit NLP-Modell berechnet',
                        'Schritt 3: Kontextuelle Relevanz geprüft',
                        'Schritt 4: Gewichtung basierend auf Häufigkeit der Co-Occurrence'
                      ],
                      confidence: edgeData.weight || 0.8,
                      ai_generated: true
                    }
                  })
                }
              })
              
              // K3.2 Task 2: Background Click Reset (clear highlights)
              cyRef.current.on('tap', (evt: EventObject) => {
                // Only if background was clicked (not a node or edge)
                if (evt.target === cyRef.current) {
                  setHighlightedElements(new Set())
                  setSelectedNode(null)
                  
                  // Remove all highlight classes
                  if (cyRef.current) {
                    cyRef.current.elements().removeClass('highlighted-node highlighted-neighbor faded')
                  }
                }
              })
        
              // Existing zoom handler
              cyRef.current.on('zoom', () => {
                if (cyRef.current) {
                  setZoomLevel(cyRef.current.zoom())
                }
              })
            }
        } catch (error) {
            console.error('Fehler bei der Cytoscape-Initialisierung:', error);
            setCytoscapeError('Graph-Visualisierung konnte nicht initialisiert werden');
        }
    }
    
    initializeCytoscape()

    return () => {
      if (cyRef.current) {
        try {
          cyRef.current.destroy()
        } catch (error) {
          console.error('Fehler beim Cytoscape Cleanup:', error)
        }
        cyRef.current = null
      }
    }
  }, [graphData, cytoscapeLoaded, isMounted, theme.palette.mode]);

  // K3.2 Task 2: Enhanced Search mit Debouncing
  const handleSearch = () => {
    debouncedSearch(searchQuery)
  }
  
  // Trigger debounced search on searchQuery change
  useEffect(() => {
    if (searchQuery.trim()) {
      debouncedSearch(searchQuery)
    }
  }, [searchQuery, debouncedSearch])

  // K3.2 Task 3: WebSocket Integration für Live-Updates
  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout | null = null
    let reconnectAttempts = 0
    const maxReconnectAttempts = 5
    
    const connectWebSocket = () => {
      try {
        // WebSocket connection zu /ws/graph endpoint
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/graph`
        
        wsRef.current = new WebSocket(wsUrl)
        
        wsRef.current.onopen = () => {
          console.log('Graph WebSocket connected')
          setWsConnected(true)
          reconnectAttempts = 0
        }
        
        wsRef.current.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data)
            
            // Handle different types of real-time events
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
            
            // Track live updates for debugging/monitoring
            setLiveUpdates(prev => [
              ...prev.slice(-9), // Keep last 10 updates
              {
                type: message.type,
                data: message.data,
                timestamp: Date.now()
              }
            ])
            
          } catch (error) {
            console.error('Error parsing WebSocket message:', error)
          }
        }
        
        wsRef.current.onclose = () => {
          console.log('Graph WebSocket disconnected')
          setWsConnected(false)
          
          // Robust reconnection with exponential backoff
          if (reconnectAttempts < maxReconnectAttempts) {
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
            console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`)
            
            reconnectTimeout = setTimeout(() => {
              reconnectAttempts++
              connectWebSocket()
            }, delay)
          }
        }
        
        wsRef.current.onerror = (error) => {
          console.error('Graph WebSocket error:', error)
        }
        
      } catch (error) {
        console.error('Error creating WebSocket connection:', error)
      }
    }
    
    // Initialize WebSocket connection
    connectWebSocket()
    
    // Cleanup on unmount
    return () => {
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout)
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, []) // Empty dependency array - only run on mount/unmount

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
    }
  }

  const handleRefresh = () => {
    loadGraphData()
  }

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
    return graphData.edges.filter(edge => 
      edge.source === nodeId || edge.target === nodeId
    )
  }

  const getGraphStats = () => {
    return {
      totalNodes: graphData.nodes.length,
      totalEdges: graphData.edges.length,
      documentNodes: graphData.nodes.filter(n => n.type === 'document').length,
      conceptNodes: graphData.nodes.filter(n => n.type === 'concept').length,
      entityNodes: graphData.nodes.filter(n => n.type === 'entity').length
    }
  }

  const stats = getGraphStats()

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

      {/* K3.2 Error-Foundation Integration: Intelligente Error-Differenzierung */}
      {error && (
        <InlineErrorDisplay 
          source="graph"
          variant="alert"
          showRetryButton={canRetry}
          onRetry={async () => {
            const data = await loadGraphData()
            if (data) {
              setGraphData(data)
            }
          }}
        />
      )}
      
      {/* Cytoscape-specific errors (Non-retryable) */}
      {cytoscapeError && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setCytoscapeError(null)}>
          {cytoscapeError}
          {/* Graceful degradation suggestion */}
          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
            Als Alternative können Sie die Knoten-Liste in der Seitenleiste verwenden.
          </Typography>
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
              <TextField
                size="small"
                label="Graph durchsuchen"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                sx={{ minWidth: 250 }}
                InputProps={{
                  endAdornment: (
                    <IconButton size="small" onClick={handleSearch}>
                      <SearchIcon />
                    </IconButton>
                  )
                }}
              />
              <IconButton onClick={handleRefresh} title="Graph aktualisieren">
                <RefreshIcon />
              </IconButton>
              <Divider orientation="vertical" flexItem />
              <IconButton onClick={handleZoomIn} title="Vergrößern">
                <ZoomInIcon />
              </IconButton>
              <IconButton onClick={handleZoomOut} title="Verkleinern">
                <ZoomOutIcon />
              </IconButton>
              <IconButton onClick={handleCenter} title="Zentrieren">
                <CenterIcon />
              </IconButton>
              <Typography variant="body2" color="text.secondary">
                Zoom: {Math.round(zoomLevel * 100)}%
              </Typography>
              
              {/* K3.2 Task 3: WebSocket Status Indicator */}
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
            </Box>
          </Paper>
        </Grid>

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
                <Typography>Graph wird geladen...</Typography>
              </Box>
            )}
            <div
              ref={graphRef}
              style={{
                width: '100%',
                height: '100%',
                borderRadius: '8px',
                backgroundColor: theme.palette.mode === 'dark' ? '#121212' : '#fafafa'
              }}
            />
            {!cytoscapeLoaded && (
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
                <Typography>Cytoscape wird geladen...</Typography>
              </Box>
            )}
          </Paper>
        </Grid>

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
                      {Object.entries(selectedNode.properties).map(([key, value]) => (
                        <ListItem key={key}>
                          <ListItemText 
                            primary={key}
                            secondary={String(value)}
                          />
                        </ListItem>
                      ))}
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
                      {getNodeConnections(selectedNode.id).map(edge => (
                        <ListItem key={edge.id}>
                          <ListItemText 
                            primary={edge.label}
                            secondary={`${edge.source === selectedNode.id ? 'zu' : 'von'} ${
                              graphData.nodes.find(n => n.id === (edge.source === selectedNode.id ? edge.target : edge.source))?.label
                            }`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              </CardContent>
            </Card>
          )}

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
        </Grid>
      </Grid>
      
      {/* K3.2 Task 3: Chain-of-Thought Transparenz Dialog */}
      <Dialog
        open={!!selectedEdgeForCoT}
        onClose={() => setSelectedEdgeForCoT(null)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            bgcolor: (theme) => 
              theme.palette.mode === 'dark' 
                ? 'rgba(30, 30, 30, 0.95)' 
                : 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(8px)'
          }
        }}
      >
        {selectedEdgeForCoT && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="h6">
                  Warum? KI-Transparenz für Beziehung
                </Typography>
                {selectedEdgeForCoT.cotData?.ai_generated && (
                  <Chip 
                    label="KI-generiert" 
                    color="primary" 
                    size="small" 
                    sx={{ 
                      bgcolor: 'primary.light',
                      color: 'primary.contrastText'
                    }}
                  />
                )}
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {selectedEdgeForCoT.edge.label} • Gewichtung: {Math.round((selectedEdgeForCoT.cotData?.confidence || 0) * 100)}%
              </Typography>
            </DialogTitle>
            
            <DialogContent>
              {/* Reasoning Explanation */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Begründung
                </Typography>
                <Paper 
                  elevation={1} 
                  sx={{ 
                    p: 2, 
                    bgcolor: (theme) => 
                      theme.palette.mode === 'dark' 
                        ? 'rgba(255, 255, 255, 0.05)' 
                        : 'rgba(0, 0, 0, 0.02)'
                  }}
                >
                  <Typography variant="body1">
                    {selectedEdgeForCoT.cotData?.reasoning}
                  </Typography>
                </Paper>
              </Box>
              
              {/* Chain of Thought Steps */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Denkprozess (Chain-of-Thought)
                </Typography>
                <Stepper orientation="vertical">
                  {selectedEdgeForCoT.cotData?.chain_of_thought.map((step, index) => (
                    <Step key={index} active={true} completed={true}>
                      <StepLabel>
                        <Typography variant="body2" fontWeight="medium">
                          {step}
                        </Typography>
                      </StepLabel>
                    </Step>
                  ))}
                </Stepper>
              </Box>
              
              {/* Confidence & Metrics */}
              <Box>
                <Typography variant="h6" gutterBottom>
                  Vertrauenswerte
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ minWidth: 120 }}>
                    Gesamtvertrauen:
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={(selectedEdgeForCoT.cotData?.confidence || 0) * 100} 
                    sx={{ 
                      flexGrow: 1, 
                      height: 8,
                      borderRadius: 4,
                      bgcolor: (theme) => theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'
                    }}
                  />
                  <Typography variant="body2" fontWeight="bold">
                    {Math.round((selectedEdgeForCoT.cotData?.confidence || 0) * 100)}%
                  </Typography>
                </Box>
                
                <Typography variant="caption" color="text.secondary">
                  Basierend auf semantischer Ähnlichkeit, Kontextueller Relevanz und Co-Occurrence-Häufigkeit.
                </Typography>
              </Box>
            </DialogContent>
            
            <DialogActions>
              <Button onClick={() => setSelectedEdgeForCoT(null)}>
                Schließen
              </Button>
              <Button 
                variant="contained" 
                onClick={() => {
                  // Future: Report/Feedback functionality
                  console.log('User feedback on CoT explanation')
                  setSelectedEdgeForCoT(null)
                }}
              >
                Feedback geben
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
      
      {/* K3.2 Task 2: Intelligent Hover Tooltips */}
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
            // Node Tooltip: [Typ-Icon] [Label (fett)] + [Node-ID]
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
            // Edge Tooltip: [Beziehungs-Typ (fett)] + [Confidence als LinearProgress]
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