'use client'

import { useEffect, useRef, useState } from 'react'
import { useAPI, GraphNode, GraphStats } from '@/lib/api'
import { useMaterialTheme } from '@/lib/theme'
import * as d3 from 'd3'

interface GraphData {
  nodes: GraphNode[]
  links: Array<{
    source: string
    target: string
    type: string
  }>
}

export default function GraphVisualization() {
  const api = useAPI()
  const { breakpoint } = useMaterialTheme()
  const svgRef = useRef<SVGSVGElement>(null)
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] })
  const [stats, setStats] = useState<GraphStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)

  // Load graph stats on mount
  useEffect(() => {
    const loadStats = async () => {
      try {
        const graphStats = await api.getGraphStats()
        setStats(graphStats)
      } catch (error) {
        console.error('Fehler beim Laden der Graph-Statistiken:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadStats()
  }, [api])

  // Search functionality
  const handleSearch = async () => {
    if (!searchQuery.trim()) return

    try {
      const searchResult = await api.searchGraph(searchQuery)
      
      // Convert search results to graph format
      const nodes = searchResult.results
      const links: Array<{ source: string; target: string; type: string }> = []
      
      // For demo purposes, create some sample connections
      for (let i = 0; i < nodes.length - 1; i++) {
        if (Math.random() > 0.7) { // 30% chance of connection
          links.push({
            source: nodes[i].id,
            target: nodes[i + 1].id,
            type: 'related'
          })
        }
      }

      setGraphData({ nodes, links })
      renderGraph({ nodes, links })
    } catch (error) {
      console.error('Fehler bei der Graph-Suche:', error)
    }
  }

  // D3.js Graph Rendering
  const renderGraph = (data: GraphData) => {
    if (!svgRef.current || data.nodes.length === 0) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove() // Clear previous render

    const width = svgRef.current.clientWidth
    const height = svgRef.current.clientHeight

    // Create simulation
    const simulation = d3.forceSimulation(data.nodes as any)
      .force('link', d3.forceLink(data.links).id(d => (d as any).id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))

    // Create links
    const link = svg.append('g')
      .selectAll('line')
      .data(data.links)
      .enter()
      .append('line')
      .attr('class', 'graph-edge')
      .attr('stroke-width', 2)

    // Create nodes
    const node = svg.append('g')
      .selectAll('circle')
      .data(data.nodes)
      .enter()
      .append('circle')
      .attr('class', 'graph-node')
      .attr('r', 8)
      .on('click', (event, d) => {
        setSelectedNode(d as GraphNode)
      })
      .call(d3.drag<SVGCircleElement, GraphNode>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart()
          ;(d as any).fx = (d as any).x
          ;(d as any).fy = (d as any).y
        })
        .on('drag', (event, d) => {
          ;(d as any).fx = event.x
          ;(d as any).fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0)
          ;(d as any).fx = null
          ;(d as any).fy = null
        })
      )

    // Add labels
    const label = svg.append('g')
      .selectAll('text')
      .data(data.nodes)
      .enter()
      .append('text')
      .text(d => d.title.length > 20 ? d.title.substring(0, 20) + '...' : d.title)
      .attr('font-size', '12px')
      .attr('fill', 'var(--md-sys-color-on-surface)')
      .attr('text-anchor', 'middle')

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as any).x)
        .attr('y1', d => (d.source as any).y)
        .attr('x2', d => (d.target as any).x)
        .attr('y2', d => (d.target as any).y)

      node
        .attr('cx', d => (d as any).x)
        .attr('cy', d => (d as any).y)

      label
        .attr('x', d => (d as any).x)
        .attr('y', d => (d as any).y + 20)
    })
  }

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (graphData.nodes.length > 0) {
        renderGraph(graphData)
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [graphData])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="md-surface md-elevation-2 p-6 rounded-xl">
          <div className="flex items-center space-x-4">
            <div className="md-circular-progress w-6 h-6 border-4 border-t-transparent border-blue-500 rounded-full animate-spin"></div>
            <span>Knowledge Graph wird geladen...</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Graph Header */}
      <div className="app-header md-elevation-1 p-4 border-b">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <svg className="w-4 h-4 fill-white" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
            </div>
            <div>
              <h2 className="md-headline-large text-lg font-semibold">
                Knowledge Graph
              </h2>
              <div className="text-sm opacity-60">
                Erkunden Sie Ihr Wissen visuell
              </div>
            </div>
          </div>
          
          {stats && (
            <div className="flex space-x-4 text-sm">
              <span className="md-surface-variant md-shape-small px-3 py-1 flex items-center space-x-2">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
                </svg>
                <span>{Object.values(stats.neo4j.nodes).reduce((a, b) => a + b, 0)} Knoten</span>
              </span>
              <span className="md-surface-variant md-shape-small px-3 py-1 flex items-center space-x-2">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z"/>
                </svg>
                <span>{Object.values(stats.neo4j.relationships).reduce((a, b) => a + b, 0)} Verbindungen</span>
              </span>
            </div>
          )}
        </div>

        {/* Search Bar */}
        <div className="flex space-x-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Nach Knoten und Verbindungen suchen..."
              className="w-full px-4 py-2 md-surface md-shape-large border-2 border-transparent focus:border-primary focus:md-elevation-1 md-motion-short"
            />
            <div className="absolute right-3 top-2.5">
              <svg className="w-4 h-4 opacity-50" fill="currentColor" viewBox="0 0 24 24">
                <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
              </svg>
            </div>
          </div>
          
          <button
            onClick={handleSearch}
            disabled={!searchQuery.trim()}
            className="md-primary md-shape-full px-6 py-2 hover:md-elevation-2 md-motion-short disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <svg className="w-4 h-4 fill-white" viewBox="0 0 24 24">
              <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
            </svg>
            <span>Suchen</span>
          </button>
        </div>
      </div>

      {/* Graph Content */}
      <div className="flex-1 flex">
        {/* Main Graph Area */}
        <div className="flex-1 relative">
          {graphData.nodes.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="md-surface md-elevation-2 md-shape-large p-8 text-center max-w-md">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
                  <svg className="w-8 h-8 text-primary" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                </div>
                <h3 className="md-headline-large text-lg font-semibold mb-2">
                  Knowledge Graph Explorer
                </h3>
                <p className="md-body-large text-gray-600 mb-4">
                  Verwenden Sie die Suchfunktion, um Knoten und Verbindungen in Ihrem Wissensgraph zu erkunden.
                </p>
                <div className="text-sm opacity-60 bg-surface-variant rounded-lg p-3">
                  <strong>Suchen Sie nach Begriffen wie:</strong><br />
                  "BSI C5", "Compliance", "Framework"
                </div>
              </div>
            </div>
          ) : (
            <svg
              ref={svgRef}
              className="w-full h-full"
              style={{ background: 'var(--md-sys-color-surface)' }}
            />
          )}
        </div>

        {/* Node Details Sidebar */}
        {selectedNode && (
          <div className="w-80 md-surface-variant border-l p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="md-headline-medium font-semibold">Knotendetails</h3>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-1 hover:bg-gray-200 rounded"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                </svg>
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium opacity-70">Titel</label>
                <div className="md-body-large">{selectedNode.title}</div>
              </div>
              
                             <div>
                 <label className="text-sm font-medium opacity-70">Labels</label>
                 <div className="md-body-medium">
                   {selectedNode.labels && selectedNode.labels.length > 0 
                     ? selectedNode.labels.join(', ') 
                     : 'Keine Labels'
                   }
                 </div>
               </div>
              
              {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                <div>
                  <label className="text-sm font-medium opacity-70">Eigenschaften</label>
                  <div className="mt-2 space-y-2">
                    {Object.entries(selectedNode.properties).map(([key, value]) => (
                      <div key={key} className="md-surface md-shape-small p-2">
                        <div className="text-xs font-medium opacity-70">{key}</div>
                        <div className="text-sm">{String(value)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
} 