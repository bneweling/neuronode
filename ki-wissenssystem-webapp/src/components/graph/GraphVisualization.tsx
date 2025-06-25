'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
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
} from '@mui/material'
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
import { getAPIClient } from '@/lib/serviceFactory'
import type { Core, NodeSingular, EventObject } from 'cytoscape'

// Dynamic import for cytoscape to avoid SSR issues
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let cytoscape: any = null
if (typeof window !== 'undefined') {
  import('cytoscape').then((cy) => {
    cytoscape = cy.default
  })
}

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
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [zoomLevel, setZoomLevel] = useState(1)
  const graphRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)

  const initializeCytoscape = useCallback(() => {
    if (!graphRef.current || !cytoscape || graphData.nodes.length === 0) return

    // Clean up existing instance
    if (cyRef.current) {
      cyRef.current.destroy()
    }

    // Convert data to Cytoscape format
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

    // Initialize Cytoscape
    cyRef.current = cytoscape({
      container: graphRef.current,
      elements,
      style: [
        // Node styles
        {
          selector: 'node',
          style: {
            'width': '60px',
            'height': '60px',
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#fff',
            'text-outline-width': 2,
            'text-outline-color': '#000',
            'font-size': '12px',
            'font-weight': 'bold'
          }
        },
        {
          selector: '.node-document',
          style: {
            'background-color': '#1976d2',
            'shape': 'rectangle'
          }
        },
        {
          selector: '.node-concept',
          style: {
            'background-color': '#9c27b0',
            'shape': 'ellipse'
          }
        },
        {
          selector: '.node-entity',
          style: {
            'background-color': '#2e7d32',
            'shape': 'diamond'
          }
        },
        // Edge styles
        {
          selector: 'edge',
          style: {
            'width': 3,
            'line-color': '#666',
            'target-arrow-color': '#666',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '10px',
            'text-rotation': 'autorotate',
            'text-margin-y': -10
          }
        },
        // Hover effects
        {
          selector: 'node:selected',
          style: {
            'border-width': 3,
            'border-color': '#ff6b35'
          }
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#ff6b35',
            'target-arrow-color': '#ff6b35',
            'width': 5
          }
        }
      ],
      layout: {
        name: 'cose',
        idealEdgeLength: 100,
        nodeOverlap: 20,
        refresh: 20,
        randomize: false,
        componentSpacing: 100,
        nodeRepulsion: 400000,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 80,
        numIter: 1000,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0
      }
    })

    // Event handlers
    if (cyRef.current) {
      cyRef.current.on('tap', 'node', (evt: EventObject) => {
        const node = evt.target as NodeSingular
        const nodeData = node.data()
        const graphNode: GraphNode = {
          id: nodeData.id,
          label: nodeData.label,
          type: nodeData.type,
          properties: nodeData
        }
        setSelectedNode(graphNode)
      })

      cyRef.current.on('zoom', () => {
        if (cyRef.current) {
          setZoomLevel(cyRef.current.zoom())
        }
      })
    }
  }, [graphData])

  useEffect(() => {
    loadGraphData()
  }, [])

  // Initialize Cytoscape when graph data changes
  useEffect(() => {
    if (graphRef.current && graphData.nodes.length > 0 && cytoscape) {
      initializeCytoscape()
    }
    return () => {
      if (cyRef.current) {
        cyRef.current.destroy()
      }
    }
  }, [graphData, initializeCytoscape])

  const loadGraphData = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const apiClient = getAPIClient()
      const response = await apiClient.getKnowledgeGraph()
      // Transform API response to match component types
      const transformedData: GraphData = {
        nodes: response.nodes.map(node => ({
          id: node.id,
          label: node.label,
          type: (node.type as 'document' | 'concept' | 'entity') || 'concept',
          properties: node.properties
        })),
        edges: response.edges
      }
      setGraphData(transformedData)
    } catch (error) {
      console.error('Fehler beim Laden des Graphen:', error)
      setError('Fehler beim Laden des Wissensgraphen. Bitte versuchen Sie es erneut.')
      
      // Enhanced mock data for better testing
      setGraphData({
        nodes: [
          { id: '1', label: 'Künstliche Intelligenz', type: 'concept', properties: { description: 'Hauptkonzept der KI' } },
          { id: '2', label: 'Machine Learning', type: 'concept', properties: { description: 'Teilbereich der KI' } },
          { id: '3', label: 'Deep Learning', type: 'concept', properties: { description: 'Teilbereich des ML' } },
          { id: '4', label: 'Neural Networks', type: 'concept', properties: { description: 'Netzwerkarchitektur' } },
          { id: '5', label: 'Computer Vision', type: 'concept', properties: { description: 'Bilderkennung' } },
          { id: '6', label: 'NLP', type: 'concept', properties: { description: 'Sprachverarbeitung' } },
          { id: '7', label: 'Dokument_1.pdf', type: 'document', properties: { path: '/docs/doc1.pdf' } },
          { id: '8', label: 'Dokument_2.pdf', type: 'document', properties: { path: '/docs/doc2.pdf' } },
          { id: '9', label: 'Python', type: 'entity', properties: { type: 'programming_language' } },
          { id: '10', label: 'TensorFlow', type: 'entity', properties: { type: 'framework' } },
        ],
        edges: [
          { id: 'e1', source: '1', target: '2', label: 'enthält', weight: 0.8 },
          { id: 'e2', source: '2', target: '3', label: 'enthält', weight: 0.9 },
          { id: 'e3', source: '3', target: '4', label: 'verwendet', weight: 0.7 },
          { id: 'e4', source: '2', target: '5', label: 'anwendung', weight: 0.6 },
          { id: 'e5', source: '2', target: '6', label: 'anwendung', weight: 0.6 },
          { id: 'e6', source: '7', target: '1', label: 'erwähnt', weight: 0.7 },
          { id: 'e7', source: '8', target: '2', label: 'erwähnt', weight: 0.6 },
          { id: 'e8', source: '9', target: '3', label: 'implementiert', weight: 0.8 },
          { id: 'e9', source: '10', target: '3', label: 'framework', weight: 0.9 },
        ]
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = () => {
    if (!searchQuery.trim() || !cyRef.current) return
    
    const matchingNodes = cyRef.current.nodes().filter((node: NodeSingular) => {
      const label = node.data('label').toLowerCase()
      return label.includes(searchQuery.toLowerCase())
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
      setError('Keine Knoten gefunden, die der Suche entsprechen.')
    }
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

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box mb={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          Wissensgraph
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Interaktive Visualisierung der Beziehungen in Ihrem Wissenssystem
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Graph Controls */}
        <Grid size={{ xs: 12 }}>
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
            </Box>
          </Paper>
        </Grid>

        {/* Main Graph Visualization */}
        <Grid size={{ xs: 12, lg: 8 }}>
          <Paper elevation={2} sx={{ height: 600, position: 'relative' }}>
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
                  bgcolor: 'rgba(255,255,255,0.8)',
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
                borderRadius: '8px'
              }}
            />
            {!cytoscape && (
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
                  bgcolor: 'rgba(255,255,255,0.9)',
                  zIndex: 1
                }}
              >
                <Typography>Cytoscape wird geladen...</Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Sidebar - Node Details and Statistics */}
        <Grid size={{ xs: 12, lg: 4 }}>
          {/* Selected Node Details */}
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

          {/* Graph Statistics */}
          <Card>
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
    </Container>
  )
} 