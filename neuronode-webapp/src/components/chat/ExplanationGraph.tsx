import { ExpandMore, ExpandLess, Info } from '@mui/icons-material';
import { Card, CardContent, Typography, Box, Tooltip, IconButton, Collapse } from '@mui/material';
import type { Core } from 'cytoscape';
import React, { useEffect, useRef, useState } from 'react';

// Skelett-Komponente für Ladezustand
const GraphSkeleton = () => (
  <Box 
    sx={{ 
      width: '100%', 
      height: '100%', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      background: 'linear-gradient(45deg, #f0f0f0 25%, transparent 25%, transparent 75%, #f0f0f0 75%, #f0f0f0)',
      backgroundSize: '20px 20px',
      animation: 'skeleton 1s infinite linear'
    }}
  >
    <Typography variant="body2" color="text.secondary">
      Graph wird geladen...
    </Typography>
  </Box>
);

interface GraphNode {
  id: string;
  label: string;
  type: string;
  size: number;
  color: string;
  metadata: {
    title: string;
    source: string;
    relevance: number;
    content_preview: string;
  };
}

interface GraphEdge {
  source: string;
  target: string;
  label: string;
  weight: number;
  color: string;
}

interface ExplanationGraphProps {
  graphData: {
    nodes: GraphNode[];
    edges: GraphEdge[];
    layout?: string;
    interactive?: boolean;
  };
  height?: number;
  title?: string;
}

// Haupt-Graph-Komponente
const ExplanationGraphCore: React.FC<ExplanationGraphProps> = ({ 
  graphData, 
  height = 350,
  title = "Erklärung der Antwort" 
}) => {
  const cyRef = useRef<HTMLDivElement>(null);
  const cyInstance = useRef<Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [expanded, setExpanded] = useState(true);
  const [cytoscapeLoaded, setCytoscapeLoaded] = useState(false);

  useEffect(() => {
    if (!cyRef.current || !graphData.nodes.length) return;

    // Dynamisches Laden von Cytoscape
    const loadCytoscape = async () => {
      try {
        const cytoscapeModule = await import('cytoscape');
        const cytoscape = cytoscapeModule.default || cytoscapeModule;
        
        // Prepare data for Cytoscape
        const elements = [
          ...graphData.nodes.map(node => ({
            data: {
              id: node.id,
              label: node.label,
              type: node.type,
              ...node.metadata
            },
            style: {
              'background-color': node.color,
              'width': node.size,
              'height': node.size,
              'label': node.label,
              'font-size': '11px',
              'text-valign': 'center',
              'text-halign': 'center',
              'text-wrap': 'wrap',
              'text-max-width': '80px'
            }
          })),
          ...graphData.edges.map(edge => ({
            data: {
              id: `${edge.source}-${edge.target}`,
              source: edge.source,
              target: edge.target,
              label: edge.label,
              weight: edge.weight
            },
            style: {
              'line-color': edge.color,
              'target-arrow-color': edge.color,
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier',
              'width': Math.max(edge.weight * 4, 2),
              'label': edge.label,
              'font-size': '9px',
              'text-rotation': 'autorotate'
            }
          }))
        ];

        // Initialize Cytoscape
        cyInstance.current = cytoscape({
          container: cyRef.current,
          elements,
          style: [
            {
              selector: 'node',
              style: {
                'text-outline-width': 2,
                'text-outline-color': '#fff',
                'border-width': 2,
                'border-color': '#333'
              }
            },
            {
              selector: 'edge',
              style: {
                'text-outline-width': 1,
                'text-outline-color': '#fff'
              }
            },
            {
              selector: 'node:selected',
              style: {
                'border-width': 4,
                'border-color': '#ff6b6b',
                'background-opacity': 0.8
              }
            }
          ],
          layout: {
            name: graphData.layout === 'force-directed' ? 'cose' : 'grid',
            animate: true,
            animationDuration: 1000,
            nodeRepulsion: () => 4000,
            idealEdgeLength: 100,
            padding: 20
          } as any // Type assertion for compatibility
        });

        // Add interaction handlers
        cyInstance.current.on('tap', 'node', (event) => {
          const node = event.target;
          const nodeData = node.data();
          
          // Find corresponding graph node
          const graphNode = graphData.nodes.find(n => n.id === nodeData.id);
          if (graphNode) {
            setSelectedNode(graphNode);
          }
        });

        // Auto-fit graph
        cyInstance.current.fit();
        setCytoscapeLoaded(true);
        
      } catch (error) {
        console.error('Fehler beim Laden von Cytoscape:', error);
        setCytoscapeLoaded(false);
        // Fallback: Immer SimpleFallbackView anzeigen bei Fehlern
      }
    };

    loadCytoscape();

    return () => {
      if (cyInstance.current) {
        cyInstance.current.destroy();
      }
    };
  }, [graphData]);

  if (!graphData.nodes.length) {
    return null;
  }

  const getNodeTypeIcon = (type: string) => {
    const icons: { [key: string]: string } = {
      'ControlItem': '🎯',
      'Technology': '🔧',
      'KnowledgeChunk': '📝',
      'Document': '📄',
      'Entity': '🏷️'
    };
    return icons[type] || '📋';
  };

  const SimpleFallbackView = () => (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        📊 Verwendete Wissensquellen
      </Typography>
      
      {graphData.nodes.map((node) => (
        <Box 
          key={node.id}
          sx={{ 
            mb: 2, 
            p: 2, 
            border: '1px solid #ddd', 
            borderRadius: 1,
            backgroundColor: node.color + '20',
            cursor: 'pointer',
            '&:hover': {
              backgroundColor: node.color + '40'
            }
          }}
          onClick={() => setSelectedNode(node)}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" sx={{ fontSize: '1.2em' }}>
              {getNodeTypeIcon(node.type)}
            </Typography>
            <Typography variant="subtitle2" fontWeight="bold">
              {node.label}
            </Typography>
          </Box>
          
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {node.metadata.content_preview}
          </Typography>
          
          <Typography variant="caption" color="text.secondary">
            Relevanz: {(node.metadata.relevance * 100).toFixed(0)}% • 
            Quelle: {node.metadata.source}
          </Typography>
        </Box>
      ))}
    </Box>
  );

  return (
    <Card sx={{ mt: 2, mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6">
              {title}
            </Typography>
            <Tooltip title="Diese Visualisierung zeigt die Wissensquellen, die für diese Antwort verwendet wurden">
              <IconButton size="small">
                <Info fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
          <IconButton
            onClick={() => setExpanded(!expanded)}
            sx={{ 
              transform: expanded ? 'rotate(0deg)' : 'rotate(180deg)',
              transition: 'transform 0.2s'
            }}
          >
            {expanded ? <ExpandLess /> : <ExpandMore />}
          </IconButton>
        </Box>

        <Collapse in={expanded}>
          <Box sx={{ position: 'relative' }}>
            {cytoscapeLoaded ? (
              <div
                ref={cyRef}
                style={{
                  width: '100%',
                  height: `${height}px`,
                  border: '1px solid #e0e0e0',
                  borderRadius: '4px',
                  backgroundColor: '#fafafa'
                }}
              />
            ) : (
              <SimpleFallbackView />
            )}
            
            {selectedNode && (
              <Box 
                sx={{ 
                  position: 'absolute', 
                  bottom: 10, 
                  left: 10, 
                  right: 10,
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  p: 2,
                  borderRadius: 1,
                  boxShadow: 2
                }}
              >
                <Typography variant="subtitle2" fontWeight="bold">
                  {selectedNode.label}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedNode.metadata.content_preview}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Relevanz: {(selectedNode.metadata.relevance * 100).toFixed(0)}%
                </Typography>
              </Box>
            )}
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};

// Hauptkomponente mit React Suspense
export const ExplanationGraph: React.FC<ExplanationGraphProps> = (props) => {
  return (
    <React.Suspense fallback={<GraphSkeleton />}>
      <ExplanationGraphCore {...props} />
    </React.Suspense>
  );
};

export default ExplanationGraph; 