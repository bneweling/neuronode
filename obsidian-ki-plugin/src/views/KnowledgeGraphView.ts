import { ItemView, WorkspaceLeaf } from 'obsidian';
import KIWissenssystemPlugin from '../../main';
import { GraphVisualization } from '../components/GraphVisualization';
import { GraphSearch } from '../components/GraphSearch';
import { GraphNode, GraphEdge, GraphSearchResult } from '../types';

export const VIEW_TYPE_KNOWLEDGE_GRAPH = 'ki-knowledge-graph';

export class KnowledgeGraphView extends ItemView {
  plugin: KIWissenssystemPlugin;
  graphViz: GraphVisualization;
  graphSearch: GraphSearch;
  
  private allNodes: GraphNode[] = [];
  private allEdges: GraphEdge[] = [];
  private filteredNodes: GraphNode[] = [];
  private filteredEdges: GraphEdge[] = [];

  constructor(leaf: WorkspaceLeaf, plugin: KIWissenssystemPlugin) {
    super(leaf);
    this.plugin = plugin;
  }

  getViewType() {
    return VIEW_TYPE_KNOWLEDGE_GRAPH;
  }

  getDisplayText() {
    return 'Knowledge Graph';
  }

  getIcon() {
    return 'git-branch';
  }

  async onOpen() {
    const container = this.containerEl.children[1];
    container.empty();
    container.addClass('ki-knowledge-graph-view');
    
    // Create main layout
    const mainContainer = container.createDiv('ki-graph-main-container');
    
    // Create sidebar for search
    const sidebar = mainContainer.createDiv('ki-graph-sidebar');
    
    // Create content area for graph
    const contentArea = mainContainer.createDiv('ki-graph-content');
    
    // Header in content area
    const header = contentArea.createEl('div', { cls: 'ki-graph-header' });
    header.createEl('h3', { text: 'Knowledge Graph', cls: 'ki-graph-title' });
    
    // Create controls
    const controls = header.createEl('div', { cls: 'ki-graph-controls' });
    
    const refreshBtn = controls.createEl('button', { 
      text: '🔄 Refresh',
      cls: 'mod-cta'
    });
    refreshBtn.onclick = () => this.refreshGraph();
    
    const toggleSearchBtn = controls.createEl('button', { 
      text: '🔍 Suche',
      cls: 'mod-muted'
    });
    toggleSearchBtn.onclick = () => this.toggleSearch();
    
    const fullGraphBtn = controls.createEl('button', { 
      text: '🌐 Vollansicht',
      cls: 'mod-muted'
    });
    fullGraphBtn.onclick = () => this.showFullGraph();
    
    // Create graph container
    const graphContainer = contentArea.createEl('div', { 
      cls: 'ki-graph-container',
      attr: { style: 'height: calc(100% - 60px); width: 100%;' }
    });
    
    // Initialize components
    this.graphViz = new GraphVisualization(graphContainer, this.plugin.settings);
    
    this.graphSearch = new GraphSearch(
      sidebar,
      this.plugin,
      this.handleSearchResults.bind(this),
      this.handleNodeSelect.bind(this)
    );
    
    // Apply responsive styles
    this.applyStyles();
    
    // Load initial data
    this.loadGraphData();
  }

  async onClose() {
    if (this.graphViz) {
      this.graphViz.destroy();
    }
    if (this.graphSearch) {
      this.graphSearch.destroy();
    }
  }

  async refreshGraph() {
    if (this.graphViz) {
      await this.loadGraphData();
    }
  }

  async loadGraphData() {
    try {
      // Get graph data from API
      const stats = await this.plugin.apiClient.getStats();
      
      // Create a more comprehensive graph based on stats
      const nodes: GraphNode[] = [
        { id: 'controls', type: 'ControlItem', data: { label: `Controls (${stats.nodes?.ControlItem || 0})` } },
        { id: 'chunks', type: 'KnowledgeChunk', data: { label: `Chunks (${stats.nodes?.KnowledgeChunk || 0})` } },
        { id: 'technologies', type: 'Technology', data: { label: `Technologies (${stats.nodes?.Technology || 0})` } }
      ];
      
      const edges: GraphEdge[] = [
        { source: 'controls', target: 'chunks', type: 'RELATES_TO' },
        { source: 'chunks', target: 'technologies', type: 'MENTIONS' }
      ];
      
      // Store full graph data
      this.allNodes = nodes;
      this.allEdges = edges;
      this.filteredNodes = nodes;
      this.filteredEdges = edges;
      
      // Update both components
      this.graphViz.updateGraph(nodes, edges);
      this.graphSearch.updateGraphData(nodes, edges);
      
    } catch (error) {
      console.error('Failed to load graph data:', error);
    }
  }

  private toggleSearch() {
    const sidebar = this.containerEl.querySelector('.ki-graph-sidebar') as HTMLElement;
    if (sidebar) {
      const isVisible = sidebar.style.display !== 'none';
      sidebar.style.display = isVisible ? 'none' : 'block';
      
      // Adjust content area width
      const contentArea = this.containerEl.querySelector('.ki-graph-content') as HTMLElement;
      if (contentArea) {
        contentArea.style.width = isVisible ? '100%' : 'calc(100% - 350px)';
      }
    }
  }

  private showFullGraph() {
    // Reset to show all nodes
    this.filteredNodes = this.allNodes;
    this.filteredEdges = this.allEdges;
    this.graphViz.updateGraph(this.filteredNodes, this.filteredEdges);
  }

  private handleSearchResults(results: GraphSearchResult[]) {
    // Extract nodes and edges from search results
    const nodeIds = new Set(results.map(r => r.node.id));
    
    // Include connected nodes for better context
    const connectedNodeIds = new Set<string>();
    this.allEdges.forEach(edge => {
      const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
      const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
      
      if (nodeIds.has(sourceId)) connectedNodeIds.add(targetId);
      if (nodeIds.has(targetId)) connectedNodeIds.add(sourceId);
    });
    
    // Combine original results with connected nodes
    nodeIds.forEach(id => connectedNodeIds.add(id));
    
    // Filter nodes and edges
    this.filteredNodes = this.allNodes.filter(node => connectedNodeIds.has(node.id));
    this.filteredEdges = this.allEdges.filter(edge => {
      const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
      const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
      return connectedNodeIds.has(sourceId) && connectedNodeIds.has(targetId);
    });
    
    // Update visualization with primary nodes highlighted
    const primaryNodeIds = results.map(r => r.node.id);
    this.graphViz.updateGraph(this.filteredNodes, this.filteredEdges, primaryNodeIds);
  }

  private handleNodeSelect(nodeId: string) {
    // Highlight the selected node
    this.graphViz.highlightNode(nodeId);
  }

  private applyStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .ki-knowledge-graph-view {
        height: 100%;
        display: flex;
        flex-direction: column;
      }

      .ki-graph-main-container {
        display: flex;
        flex: 1;
        overflow: hidden;
      }

      .ki-graph-sidebar {
        width: 350px;
        border-right: 1px solid var(--background-modifier-border);
        background: var(--background-secondary);
        overflow-y: auto;
        display: none;
      }

      .ki-graph-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        width: 100%;
        transition: width 0.3s ease;
      }

      .ki-graph-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        border-bottom: 1px solid var(--background-modifier-border);
        background: var(--background-primary);
      }

      .ki-graph-title {
        margin: 0;
        font-size: 1.2rem;
      }

      .ki-graph-controls {
        display: flex;
        gap: 0.5rem;
      }

      .ki-graph-controls button {
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s;
      }

      .ki-graph-container {
        flex: 1;
        position: relative;
        overflow: hidden;
      }

      @media (max-width: 768px) {
        .ki-graph-sidebar {
          position: absolute;
          top: 0;
          left: 0;
          height: 100%;
          z-index: 1000;
          box-shadow: var(--shadow-l);
        }
        
        .ki-graph-content {
          width: 100% !important;
        }
      }
    `;
    document.head.append(style);
  }
}
