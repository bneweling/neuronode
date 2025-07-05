'use client'

import {
  Analytics as AnalyticsIcon,
  Article as DocumentIcon,
  CenterFocusStrong as CenterIcon,
  FilterList as FilterIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
  Hub as HubIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Tag as TagIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
} from '@mui/icons-material'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  Grid,
  IconButton,
  Menu,
  MenuItem,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import type { Core } from 'cytoscape'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { useDebounce } from '@/hooks/useDebounce'
import { useGraphState } from '@/hooks/useGraphState'
import { usePerformanceMonitor } from '@/hooks/usePerformanceMonitor'

interface StatCardProps {
  title: string
  value: number | string
  icon: React.ElementType
  color: string
}

const StatCard = ({ title, value, icon: Icon, color }: StatCardProps) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Grid container spacing={2} alignItems="center">
        <Grid item>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 2,
              backgroundColor: `${color}20`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Icon sx={{ color }} />
          </Box>
        </Grid>
        <Grid item xs>
          <Typography variant="h5" fontWeight="bold">
            {value}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {title}
          </Typography>
        </Grid>
      </Grid>
    </CardContent>
  </Card>
)

export default function TablerGraphDashboard() {
  const {
    graphData,
    graphStats,
    isLoading,
    isError,
    error,
    refetchGraphData,
  } = useGraphState()

  const { trackComponentPerformance } = usePerformanceMonitor()

  const [searchQuery, setSearchQuery] = useState('')
  const [zoomLevel, setZoomLevel] = useState(1)
  const [isMounted, setIsMounted] = useState(false)
  const [cytoscapeLoaded, setCytoscapeLoaded] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [filterAnchorEl, setFilterAnchorEl] = useState<null | HTMLElement>(null)
  const [activeFilters, setActiveFilters] = useState<string[]>([])

  const graphRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)

  const hasGraphData = useMemo(
    () => Boolean(graphData && graphData.nodes && graphData.nodes.length > 0),
    [graphData],
  )

  const debouncedSearch = useDebounce((query: string) => {
    if (!cyRef.current) return
    const cy = cyRef.current
    const searchTerm = query.toLowerCase().trim()

    cy.batch(() => {
      if (!searchTerm) {
        cy.elements().removeClass('highlighted faded').style({ opacity: 1 })
        return
      }

      const matchingNodes = cy.nodes().filter(node => {
        const label = node.data('label')?.toLowerCase() || ''
        return label.includes(searchTerm)
      })

      cy.elements().addClass('faded').style({ opacity: 0.2 })
      matchingNodes.removeClass('faded').addClass('highlighted').style({ opacity: 1 })
      matchingNodes.neighborhood().removeClass('faded').style({ opacity: 0.7 })
    })
  }, 300)

  useEffect(() => {
    setIsMounted(true)
    trackComponentPerformance('TablerGraphDashboard', 'render')
  }, [trackComponentPerformance])

  useEffect(() => {
    const initializeCytoscape = async () => {
      if (!graphRef.current || !hasGraphData || cytoscapeLoaded || !isMounted) {
        return
      }

      try {
        const cytoscape = (await import('cytoscape')).default
        const cy = cytoscape({
          container: graphRef.current,
          elements: {
            nodes: graphData.nodes.map(n => ({ data: { ...n } })),
            edges: graphData.edges.map(e => ({ data: { ...e } })),
          },
          style: [
             {
              selector: 'node',
              style: {
                'background-color': '#206bc4',
                'label': 'data(label)',
                'width': 20,
                'height': 20,
              },
            },
            {
              selector: 'edge',
              style: {
                'width': 2,
                'line-color': '#ccc',
                'target-arrow-color': '#ccc',
                'curve-style': 'bezier',
              },
            },
            {
              selector: '.highlighted',
              style: {
                'background-color': '#e67e22',
                'border-color': '#d35400',
                'border-width': 2,
              },
            },
            {
              selector: '.faded',
              style: { 'opacity': 0.25 },
            },
          ],
          layout: {
            name: 'cose',
            idealEdgeLength: 100,
            nodeOverlap: 20,
            refresh: 20,
            fit: true,
            padding: 30,
          },
        })

        cyRef.current = cy
        setCytoscapeLoaded(true)

        cy.on('zoom', () => setZoomLevel(cy.zoom()))
      } catch (e) {
        console.error('Failed to load Cytoscape', e)
      }
    }

    initializeCytoscape()
  }, [hasGraphData, isMounted, cytoscapeLoaded, graphData])

  const handleZoom = useCallback((factor: number) => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * factor)
    }
  }, [])

  const handleCenter = useCallback(() => cyRef.current?.fit(), [])
  const handleRefresh = useCallback(() => refetchGraphData(), [refetchGraphData])

  return (
    <Box
      sx={{ p: 3, height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}
    >
      <Typography variant="h4" gutterBottom>
        Wissensgraph-Dashboard
      </Typography>

      <Grid container spacing={2} mb={2}>
        <Grid item xs={12} md={3}>
          <StatCard title="Knoten" value={graphStats?.node_count || 0} icon={HubIcon} color="#20639B" />
        </Grid>
        <Grid item xs={12} md={3}>
          <StatCard title="Kanten" value={graphStats?.edge_count || 0} icon={AnalyticsIcon} color="#3CAEA3" />
        </Grid>
        <Grid item xs={12} md={3}>
          <StatCard title="Dokumente" value={graphStats?.document_count || 0} icon={DocumentIcon} color="#F6D55C" />
        </Grid>
        <Grid item xs={12} md={3}>
          <StatCard title="Konzepte" value={graphStats?.concept_count || 0} icon={TagIcon} color="#ED553B" />
        </Grid>
      </Grid>

      <Card sx={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
        <CardContent>
          <Stack direction="row" spacing={1} alignItems="center">
            <SearchIcon color="action" />
            <TextField
              variant="outlined"
              size="small"
              placeholder="Graph durchsuchen..."
              value={searchQuery}
              onChange={e => {
                setSearchQuery(e.target.value)
                debouncedSearch(e.target.value)
              }}
              sx={{ flexGrow: 1 }}
            />
            <Tooltip title="Aktualisieren">
              <IconButton onClick={handleRefresh}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Filter">
              <IconButton onClick={e => setFilterAnchorEl(e.currentTarget)}>
                <FilterIcon />
              </IconButton>
            </Tooltip>
            <Divider orientation="vertical" flexItem />
            <Tooltip title="Hineinzoomen">
              <IconButton onClick={() => handleZoom(1.2)}>
                <ZoomInIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Herauszoomen">
              <IconButton onClick={() => handleZoom(0.8)}>
                <ZoomOutIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Zentrieren">
              <IconButton onClick={handleCenter}>
                <CenterIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        </CardContent>

        <Box sx={{ flex: 1, position: 'relative', borderTop: '1px solid #eee' }}>
          {isLoading && (
            <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.7)', zIndex: 10 }}>
              <CircularProgress />
              <Typography ml={2}>Lade Graphdaten...</Typography>
            </Box>
          )}
          {isError && !isLoading && (
            <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10 }}>
              <Alert severity="error" action={<Button onClick={handleRefresh}>Erneut versuchen</Button>}>
                Fehler beim Laden der Graphdaten: {error?.message}
              </Alert>
            </Box>
          )}
          <div
            ref={graphRef}
            style={{ width: '100%', height: '100%', position: 'absolute', background: '#f9f9f9' }}
          />
        </Box>
      </Card>

      <Menu
        anchorEl={filterAnchorEl}
        open={Boolean(filterAnchorEl)}
        onClose={() => setFilterAnchorEl(null)}
      >
        <MenuItem onClick={() => { /* Implement filter logic */ }}>Dokumente</MenuItem>
        <MenuItem onClick={() => { /* Implement filter logic */ }}>Konzepte</MenuItem>
      </Menu>
    </Box>
  )
}