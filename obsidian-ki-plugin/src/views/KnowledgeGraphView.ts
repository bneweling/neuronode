import { ItemView, WorkspaceLeaf } from 'obsidian';
import KIWissenssystemPlugin from '../../main';
import { GraphVisualization } from '../components/GraphVisualization';

export const VIEW_TYPE_KNOWLEDGE_GRAPH = 'ki-knowledge-graph';

export class KnowledgeGraphView extends ItemView {
  plugin: KIWissenssystemPlugin;
  graphViz: GraphVisualization;

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
    
    // Create header
    const header = container.createEl('div', { cls: 'ki-graph-header' });
    header.createEl('h3', { text: 'Knowledge Graph', cls: 'ki-graph-title' });
    
    // Create controls
    const controls = header.createEl('div', { cls: 'ki-graph-controls' });
    
    const refreshBtn = controls.createEl('button', { 
      text: 'Refresh',
      cls: 'mod-cta'
    });
    refreshBtn.onclick = () => this.refreshGraph();
    
    const filterBtn = controls.createEl('button', { 
      text: 'Filter',
      cls: 'mod-muted'
    });
    filterBtn.onclick = () => this.showFilterModal();
    
    // Create graph container
    const graphContainer = container.createEl('div', { 
      cls: 'ki-graph-container',
      attr: { style: 'height: calc(100% - 60px); width: 100%;' }
    });
    
    // Initialize graph visualization
    this.graphViz = new GraphVisualization(graphContainer, this.plugin.settings);
    
    // Load initial data
    this.loadGraphData();
  }

  async onClose() {
    if (this.graphViz) {
      this.graphViz.destroy();
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
      
      // Create a simple overview graph based on stats
      const nodes = [
        { id: 'controls', type: 'ControlItem', label: `Controls (${stats.nodes?.ControlItem || 0})` },
        { id: 'chunks', type: 'KnowledgeChunk', label: `Chunks (${stats.nodes?.KnowledgeChunk || 0})` },
        { id: 'technologies', type: 'Technology', label: `Technologies (${stats.nodes?.Technology || 0})` }
      ];
      
      const edges = [
        { source: 'controls', target: 'chunks', type: 'RELATES_TO' },
        { source: 'chunks', target: 'technologies', type: 'MENTIONS' }
      ];
      
      this.graphViz.updateGraph(nodes, edges);
    } catch (error) {
      console.error('Failed to load graph data:', error);
    }
  }

  showFilterModal() {
    // TODO: Implement filter modal
    console.log('Filter modal not implemented yet');
  }
}
