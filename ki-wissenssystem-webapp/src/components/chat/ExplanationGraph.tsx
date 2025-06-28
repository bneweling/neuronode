import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, Typography, Box, Tooltip, IconButton, Collapse } from '@mui/material';
import { ExpandMore, ExpandLess, Info } from '@mui/icons-material';

// Fallback für Cytoscape.js (falls nicht verfügbar)
let cytoscape: any = null;
let cytoscapeAvailable = false;

try {
  cytoscape = require('cytoscape');
  cytoscapeAvailable = true;
} catch (error) {
  console.warn('Cytoscape.js nicht verfügbar - Graph-Visualisierung wird als Netzwerk-Liste angezeigt');
}

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

export const ExplanationGraph: React.FC<ExplanationGraphProps> = ({ 
  graphData, 
  height = 350,
  title = "Erklärung der Antwort" 
}) => {
  const cyRef = useRef<HTMLDivElement>(null);
  const cyInstance = useRef<any>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    if (!cyRef.current || !graphData.nodes.length || !cytoscapeAvailable) return;

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
        nodeRepulsion: 4000,
        idealEdgeLength: 100,
        padding: 20
      }
    });

    // Add interaction handlers
    cyInstance.current.on('tap', 'node', (event: any) => {
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
      
      {graphData.nodes.map((node, index) => (
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
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
            {getNodeTypeIcon(node.type)} {node.label}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Relevanz: {(node.metadata.relevance * 100).toFixed(0)}%
          </Typography>
        </Box>
      ))}
      
      {graphData.edges.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            🔗 Beziehungen ({graphData.edges.length})
          </Typography>
          {graphData.edges.slice(0, 5).map((edge, index) => (
            <Typography key={index} variant="caption" display="block">
              {edge.label}: {edge.source} → {edge.target}
            </Typography>
          ))}
        </Box>
      )}
    </Box>
  );

  return (
    <Card sx={{ mt: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            {title}
          </Typography>
          <Tooltip title="Zeigt die Wissensquellen und deren Beziehungen für diese Antwort">
            <IconButton size="small">
              <Info fontSize="small" />
            </IconButton>
          </Tooltip>
          <IconButton 
            onClick={() => setExpanded(!expanded)}
            size="small"
          >
            {expanded ? <ExpandLess /> : <ExpandMore />}
          </IconButton>
        </Box>
        
        <Collapse in={expanded}>
          {cytoscapeAvailable ? (
            <Box 
              ref={cyRef} 
              sx={{ 
                height: `${height}px`, 
                border: '1px solid #ddd',
                borderRadius: 1,
                position: 'relative'
              }} 
            />
          ) : (
            <SimpleFallbackView />
          )}
          
          {selectedNode && (
            <Box sx={{ mt: 2, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                {getNodeTypeIcon(selectedNode.type)} {selectedNode.metadata.title || selectedNode.label}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Typ: {selectedNode.type} | Relevanz: {(selectedNode.metadata.relevance * 100).toFixed(0)}%
              </Typography>
              {selectedNode.metadata.source && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Quelle: {selectedNode.metadata.source}
                </Typography>
              )}
              <Typography variant="body2">
                {selectedNode.metadata.content_preview}
              </Typography>
            </Box>
          )}
          
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            {cytoscapeAvailable 
              ? "💡 Klicken Sie auf Knoten für Details. Die Größe zeigt die Relevanz an."
              : "💡 Klicken Sie auf Elemente für Details. Cytoscape.js ist nicht verfügbar - vereinfachte Ansicht wird verwendet."
            }
          </Typography>
        </Collapse>
      </CardContent>
    </Card>
  );
}; 