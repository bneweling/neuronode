'use client'

import { useState, useEffect, useRef } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
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
  Share as ShareIcon,
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
import { getAPIClient } from '@/lib/api'

interface GraphNode {
  id: string
  label: string
  type: 'document' | 'concept' | 'entity'
  properties: Record<string, any>
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

export default function GraphVisualization() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [zoomLevel, setZoomLevel] = useState(1)
  const graphRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadGraphData()
  }, [])

  const loadGraphData = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const apiClient = getAPIClient()
      const response = await apiClient.getKnowledgeGraph()
      setGraphData(response)
    } catch (error) {
      console.error('Fehler beim Laden des Graphen:', error)
      setError('Fehler beim Laden des Wissensgraphen. Bitte versuchen Sie es erneut.')
      
      // Fallback mock data
      setGraphData({
        nodes: [
          { id: '1', label: 'Künstliche Intelligenz', type: 'concept', properties: { description: 'Hauptkonzept der KI' } },
          { id: '2', label: 'Machine Learning', type: 'concept', properties: { description: 'Teilbereich der KI' } },
          { id: '3', label: 'Deep Learning', type: 'concept', properties: { description: 'Teilbereich des ML' } },
          { id: '4', label: 'Dokument_1.pdf', type: 'document', properties: { path: '/docs/doc1.pdf' } },
          { id: '5', label: 'Dokument_2.pdf', type: 'document', properties: { path: '/docs/doc2.pdf' } },
        ],
        edges: [
          { id: 'e1', source: '1', target: '2', label: 'enthält', weight: 0.8 },
          { id: 'e2', source: '2', target: '3', label: 'enthält', weight: 0.9 },
          { id: 'e3', source: '4', target: '1', label: 'erwähnt', weight: 0.7 },
          { id: 'e4', source: '5', target: '2', label: 'erwähnt', weight: 0.6 },
        ]
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = () => {
    if (!searchQuery.trim()) return
    
    const matchingNodes = graphData.nodes.filter(node =>
      node.label.toLowerCase().includes(searchQuery.toLowerCase())
    )
    
    if (matchingNodes.length > 0) {
      setSelectedNode(matchingNodes[0])
    } else {
      setError('Keine Knoten gefunden, die der Suche entsprechen.')
    }
  }

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node)
  }

  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 0.2, 3))
  }

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 0.2, 0.5))
  }

  const handleCenter = () => {
    setZoomLevel(1)
    setSelectedNode(null)
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

  const getNodeColor = (type: string) => {
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

  const getConnectedNodes = (nodeId: string) => {
    const connectedIds = new Set<string>()
    graphData.edges.forEach(edge => {
      if (edge.source === nodeId) connectedIds.add(edge.target)
      if (edge.target === nodeId) connectedIds.add(edge.source)
    })
    return graphData.nodes.filter(node => connectedIds.has(node.id))
  }

  const getNodeConnections = (nodeId: string) => {
    return graphData.edges.filter(edge => 
      edge.source === nodeId || edge.target === nodeId
    )
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box mb={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          Wissensgraph
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Visualisierung der Beziehungen in Ihrem Wissenssystem
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Graph Controls */}
        <Grid item xs={12}>
          <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
              <TextField
                size="small"
                placeholder="Knoten suchen..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                sx={{ minWidth: 200 }}
              />
              <Button
                variant="contained"
                onClick={handleSearch}
                startIcon={<SearchIcon />}
                disabled={!searchQuery.trim()}
              >
                Suchen
              </Button>
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
              <Divider orientation="vertical" flexItem />
              <Button
                variant="outlined"
                onClick={loadGraphData}
                startIcon={<RefreshIcon />}
                disabled={isLoading}
              >
                Aktualisieren
              </Button>
              <Button
                variant="outlined"
                startIcon={<ShareIcon />}
              >
                Teilen
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Graph Visualization */}
        <Grid item xs={12} md={8}>
          <Paper 
            elevation={1} 
            sx={{ 
              height: 600, 
              position: 'relative',
              overflow: 'hidden',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Box
              ref={graphRef}
              sx={{
                width: '100%',
                height: '100%',
                transform: `scale(${zoomLevel})`,
                transition: 'transform 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                gap: 2
              }}
            >
              {isLoading ? (
                <Typography variant="h6" color="text.secondary">
                  Graph wird geladen...
                </Typography>
              ) : graphData.nodes.length === 0 ? (
                <Box sx={{ textAlign: 'center' }}>
                  <GraphIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    Keine Daten verfügbar
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Laden Sie Dokumente hoch, um den Wissensgraphen zu erstellen
                  </Typography>
                </Box>
              ) : (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, p: 2 }}>
                  {graphData.nodes.map((node) => (
                    <Card
                      key={node.id}
                      sx={{
                        minWidth: 120,
                        cursor: 'pointer',
                        border: selectedNode?.id === node.id ? 2 : 1,
                        borderColor: selectedNode?.id === node.id ? 'primary.main' : 'divider',
                        '&:hover': {
                          elevation: 4,
                          transform: 'translateY(-2px)'
                        },
                        transition: 'all 0.2s ease'
                      }}
                      onClick={() => handleNodeClick(node)}
                    >
                      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          {getNodeIcon(node.type)}
                          <Chip
                            label={node.type}
                            size="small"
                            color={getNodeColor(node.type) as any}
                            variant="outlined"
                          />
                        </Box>
                        <Typography variant="body2" fontWeight="bold" noWrap>
                          {node.label}
                        </Typography>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Node Details Panel */}
        <Grid item xs={12} md={4}>
          <Paper elevation={1} sx={{ height: 600, overflow: 'auto' }}>
            {selectedNode ? (
              <Box sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  {getNodeIcon(selectedNode.type)}
                  <Typography variant="h6" noWrap>
                    {selectedNode.label}
                  </Typography>
                </Box>
                
                <Chip
                  label={selectedNode.type}
                  color={getNodeColor(selectedNode.type) as any}
                  size="small"
                  sx={{ mb: 2 }}
                />

                <Accordion defaultExpanded>
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
                      {getNodeConnections(selectedNode.id).map((edge) => {
                        const connectedNodeId = edge.source === selectedNode.id ? edge.target : edge.source
                        const connectedNode = graphData.nodes.find(n => n.id === connectedNodeId)
                        return (
                          <ListItem key={edge.id}>
                            <ListItemText
                              primary={connectedNode?.label || 'Unbekannt'}
                              secondary={`${edge.label} (${Math.round(edge.weight * 100)}%)`}
                            />
                          </ListItem>
                        )
                      })}
                    </List>
                  </AccordionDetails>
                </Accordion>

                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle2">
                      Verbundene Knoten ({getConnectedNodes(selectedNode.id).length})
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {getConnectedNodes(selectedNode.id).map((node) => (
                        <ListItem 
                          key={node.id}
                          button
                          onClick={() => setSelectedNode(node)}
                        >
                          <ListItemText
                            primary={node.label}
                            secondary={node.type}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              </Box>
            ) : (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <GraphIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  Kein Knoten ausgewählt
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Klicken Sie auf einen Knoten, um Details anzuzeigen
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Graph Statistics */}
        <Grid item xs={12}>
          <Paper elevation={1} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Graph-Statistiken
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary.main">
                    {graphData.nodes.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Knoten
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="secondary.main">
                    {graphData.edges.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Verbindungen
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="success.main">
                    {graphData.nodes.filter(n => n.type === 'document').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Dokumente
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="warning.main">
                    {graphData.nodes.filter(n => n.type === 'concept').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Konzepte
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  )
} 