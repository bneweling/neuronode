import { ItemView, WorkspaceLeaf } from 'obsidian';
import KIWissenssystemPlugin from '../../main';
import { ChatInterface } from '../components/ChatInterface';
import { GraphVisualization } from '../components/GraphVisualization';
import { GraphSearch } from '../components/GraphSearch';
import { Message, GraphNode, GraphEdge, GraphSearchResult } from '../types';

export const VIEW_TYPE_KNOWLEDGE_CHAT = 'knowledge-chat-view';

export class KnowledgeChatView extends ItemView {
  plugin: KIWissenssystemPlugin;
  chatInterface: ChatInterface;
  graphViz: GraphVisualization;
  graphSearch: GraphSearch;
  
  currentContext: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  } = { nodes: [], edges: [] };
  
  // Workbench state
  private layout: 'chat-focused' | 'graph-focused' | 'balanced' | 'search-focused' = 'balanced';
  private isGraphSearchVisible: boolean = false;

  constructor(leaf: WorkspaceLeaf, plugin: KIWissenssystemPlugin) {
    super(leaf);
    this.plugin = plugin;
  }

  getViewType() {
    return VIEW_TYPE_KNOWLEDGE_CHAT;
  }

  getDisplayText() {
    return 'KI-Wissenssystem Chat';
  }

  getIcon() {
    return 'message-circle';
  }

  async onOpen() {
    const container = this.containerEl.children[1];
    container.empty();
    container.addClass('ki-chat-view');

    // Create workbench layout
    const workbench = container.createDiv('ki-workbench');
    
    // Workbench header with layout controls
    const header = workbench.createDiv('ki-workbench-header');
    this.createWorkbenchHeader(header);
    
    // Main content area
    const mainArea = workbench.createDiv('ki-workbench-main');
    
    // Create flexible panels
    const chatPanel = mainArea.createDiv('ki-workbench-panel ki-chat-panel');
    const graphPanel = mainArea.createDiv('ki-workbench-panel ki-graph-panel');
    const searchPanel = mainArea.createDiv('ki-workbench-panel ki-search-panel');
    
    // Setup chat panel
    this.setupChatPanel(chatPanel);
    
    // Setup graph panel
    this.setupGraphPanel(graphPanel);
    
    // Setup search panel (initially hidden)
    this.setupSearchPanel(searchPanel);
    
    // Initialize components
    this.chatInterface = new ChatInterface(
      chatPanel.querySelector('.ki-chat-content') as HTMLElement,
      this.plugin,
      this.handleChatMessage.bind(this),
      this.handleContextUpdate.bind(this)
    );

    this.graphViz = new GraphVisualization(
      graphPanel.querySelector('.ki-graph-canvas') as HTMLElement,
      this.plugin.settings
    );

    // Apply initial layout
    this.applyLayout(this.layout);

    // Connect to WebSocket
    this.plugin.wsClient.connect();
    this.plugin.wsClient.onMessage(this.handleWebSocketMessage.bind(this));

    // Apply styles
    this.applyStyles();
  }

  async onClose() {
    // Cleanup
    this.chatInterface?.destroy();
    this.graphViz?.destroy();
    this.graphSearch?.destroy();
  }

  private async handleChatMessage(message: string) {
    // Send message through WebSocket
    this.plugin.wsClient.sendMessage({
      type: 'query',
      query: message,
      conversation: this.chatInterface.getConversationHistory()
    });
  }

  private handleWebSocketMessage(data: any) {
    switch (data.type) {
      case 'processing':
        this.chatInterface.showProcessingIndicator();
        break;
        
      case 'response':
        this.handleQueryResponse(data.data);
        break;
        
      case 'error':
        this.chatInterface.showError(data.error);
        break;
        
      case 'suggestions':
        this.chatInterface.updateSuggestions(data.suggestions);
        break;
    }
  }

  private async handleQueryResponse(response: any) {
    // Add response to chat
    this.chatInterface.addMessage({
      role: 'assistant',
      content: response.response,
      sources: response.sources,
      confidence: response.confidence,
      timestamp: new Date()
    });

    // Update context graph
    if (response.analysis?.entities) {
      await this.updateContextGraph(response);
    }

    // Show follow-up questions
    if (response.follow_up_questions) {
      this.chatInterface.showFollowUpQuestions(response.follow_up_questions);
    }
  }

  private async updateContextGraph(response: any) {
    try {
      // Fetch relevant nodes from the response metadata
      const nodeIds = this.extractNodeIds(response);
      
      if (nodeIds.length === 0) return;

      // Fetch graph data from API
      const graphData = await this.plugin.apiClient.getGraphContext(
        nodeIds,
        this.plugin.settings.graphDepth
      );

      // Update current context
      this.currentContext = graphData;

      // Update visualization
      this.graphViz.updateGraph(
        graphData.nodes,
        graphData.edges,
        nodeIds // Highlight primary nodes
      );

    } catch (error) {
      console.error('Error updating context graph:', error);
    }
  }

  private extractNodeIds(response: any): string[] {
    const nodeIds = new Set<string>();

    // Extract from sources
    if (response.sources) {
      response.sources.forEach((source: any) => {
        if (source.control_id) nodeIds.add(source.control_id);
        if (source.node_id) nodeIds.add(source.node_id);
      });
    }

    // Extract from entities
    if (response.analysis?.entities?.controls) {
      response.analysis.entities.controls.forEach((id: string) => nodeIds.add(id));
    }

    return Array.from(nodeIds);
  }

  private handleContextUpdate(nodeId: string) {
    // Handle clicks on context items in chat
    this.graphViz.highlightNode(nodeId);
  }

  // Workbench Methods
  private createWorkbenchHeader(header: HTMLElement) {
    const title = header.createEl('h3', { text: 'KI-Wissenssystem Workbench', cls: 'ki-workbench-title' });
    
    const controls = header.createDiv('ki-workbench-controls');
    
    // Layout buttons
    const layoutGroup = controls.createDiv('ki-workbench-layout-group');
    layoutGroup.createEl('span', { text: 'Layout:', cls: 'ki-workbench-label' });
    
    const layouts = [
      { key: 'balanced', icon: '⚖️', title: 'Ausgewogen' },
      { key: 'chat-focused', icon: '💬', title: 'Chat-Fokus' },
      { key: 'graph-focused', icon: '🕸️', title: 'Graph-Fokus' },
      { key: 'search-focused', icon: '🔍', title: 'Such-Fokus' }
    ];
    
    layouts.forEach(layout => {
      const btn = layoutGroup.createEl('button', {
        text: layout.icon,
        title: layout.title,
        cls: `ki-workbench-layout-btn ${this.layout === layout.key ? 'active' : ''}`
      });
      btn.addEventListener('click', () => this.setLayout(layout.key as any));
    });
    
    // Additional controls
    const toolsGroup = controls.createDiv('ki-workbench-tools-group');
    
    const searchToggleBtn = toolsGroup.createEl('button', {
      text: '🔍 Suche',
      title: 'Graph-Suche ein-/ausblenden',
      cls: 'ki-workbench-tool-btn'
    });
    searchToggleBtn.addEventListener('click', () => this.toggleGraphSearch());
    
    const syncBtn = toolsGroup.createEl('button', {
      text: '🔄 Sync',
      title: 'Chat und Graph synchronisieren',
      cls: 'ki-workbench-tool-btn'
    });
    syncBtn.addEventListener('click', () => this.syncChatWithGraph());
  }

  private setupChatPanel(panel: HTMLElement) {
    const header = panel.createDiv('ki-panel-header');
    header.createEl('h4', { text: '💬 Chat-Assistent' });
    
    const headerActions = header.createDiv('ki-panel-actions');
    const expandBtn = headerActions.createEl('button', {
      text: '⤢',
      title: 'Chat-Panel maximieren',
      cls: 'ki-panel-action-btn'
    });
    expandBtn.addEventListener('click', () => this.setLayout('chat-focused'));
    
    const content = panel.createDiv('ki-chat-content');
  }

  private setupGraphPanel(panel: HTMLElement) {
    const header = panel.createDiv('ki-panel-header');
    header.createEl('h4', { text: '🕸️ Kontext-Graph' });
    
    const headerActions = header.createDiv('ki-panel-actions');
    const expandBtn = headerActions.createEl('button', {
      text: '⤢',
      title: 'Graph-Panel maximieren',
      cls: 'ki-panel-action-btn'
    });
    expandBtn.addEventListener('click', () => this.setLayout('graph-focused'));
    
    const content = panel.createDiv('ki-graph-content');
    const canvas = content.createDiv('ki-graph-canvas');
  }

  private setupSearchPanel(panel: HTMLElement) {
    const header = panel.createDiv('ki-panel-header');
    header.createEl('h4', { text: '🔍 Graph-Suche' });
    
    const headerActions = header.createDiv('ki-panel-actions');
    const expandBtn = headerActions.createEl('button', {
      text: '⤢',
      title: 'Such-Panel maximieren',
      cls: 'ki-panel-action-btn'
    });
    expandBtn.addEventListener('click', () => this.setLayout('search-focused'));
    
    const closeBtn = headerActions.createEl('button', {
      text: '✕',
      title: 'Such-Panel schließen',
      cls: 'ki-panel-action-btn'
    });
    closeBtn.addEventListener('click', () => this.toggleGraphSearch());
    
    const content = panel.createDiv('ki-search-content');
    panel.style.display = 'none'; // Initially hidden
  }

  private setLayout(layout: 'chat-focused' | 'graph-focused' | 'balanced' | 'search-focused') {
    this.layout = layout;
    this.applyLayout(layout);
    
    // Update active button
    this.containerEl.querySelectorAll('.ki-workbench-layout-btn').forEach(btn => {
      btn.removeClass('active');
    });
    this.containerEl.querySelector(`[title*="${this.getLayoutTitle(layout)}"]`)?.addClass('active');
  }

  private getLayoutTitle(layout: string): string {
    const titles = {
      'balanced': 'Ausgewogen',
      'chat-focused': 'Chat-Fokus',
      'graph-focused': 'Graph-Fokus',
      'search-focused': 'Such-Fokus'
    };
    return titles[layout as keyof typeof titles] || 'Unbekannt';
  }

  private applyLayout(layout: 'chat-focused' | 'graph-focused' | 'balanced' | 'search-focused') {
    const mainArea = this.containerEl.querySelector('.ki-workbench-main') as HTMLElement;
    if (!mainArea) return;
    
    const chatPanel = mainArea.querySelector('.ki-chat-panel') as HTMLElement;
    const graphPanel = mainArea.querySelector('.ki-graph-panel') as HTMLElement;
    const searchPanel = mainArea.querySelector('.ki-search-panel') as HTMLElement;
    
    // Reset all panels
    [chatPanel, graphPanel, searchPanel].forEach(panel => {
      if (panel) {
        panel.style.flex = '';
        panel.style.display = '';
        panel.removeClass('ki-panel-maximized');
      }
    });
    
    // Apply layout-specific styles
    switch (layout) {
      case 'chat-focused':
        if (chatPanel) {
          chatPanel.style.flex = '3';
          chatPanel.addClass('ki-panel-maximized');
        }
        if (graphPanel) graphPanel.style.flex = '1';
        if (searchPanel) searchPanel.style.display = 'none';
        break;
        
      case 'graph-focused':
        if (chatPanel) chatPanel.style.flex = '1';
        if (graphPanel) {
          graphPanel.style.flex = '3';
          graphPanel.addClass('ki-panel-maximized');
        }
        if (searchPanel) searchPanel.style.display = 'none';
        break;
        
      case 'search-focused':
        if (chatPanel) chatPanel.style.flex = '1';
        if (graphPanel) graphPanel.style.flex = '1';
        if (searchPanel) {
          searchPanel.style.flex = '2';
          searchPanel.style.display = 'flex';
          searchPanel.addClass('ki-panel-maximized');
        }
        this.initializeGraphSearchIfNeeded();
        break;
        
      case 'balanced':
      default:
        if (chatPanel) chatPanel.style.flex = '1';
        if (graphPanel) graphPanel.style.flex = '1';
        if (searchPanel && this.isGraphSearchVisible) {
          searchPanel.style.flex = '1';
          searchPanel.style.display = 'flex';
        } else if (searchPanel) {
          searchPanel.style.display = 'none';
        }
        break;
    }
    
    // Update main area class
    mainArea.className = `ki-workbench-main ki-layout-${layout}`;
  }

  private toggleGraphSearch() {
    this.isGraphSearchVisible = !this.isGraphSearchVisible;
    
    if (this.isGraphSearchVisible) {
      this.initializeGraphSearchIfNeeded();
      if (this.layout === 'balanced' || this.layout === 'search-focused') {
        this.applyLayout(this.layout);
      } else {
        this.setLayout('search-focused');
      }
    } else {
      const searchPanel = this.containerEl.querySelector('.ki-search-panel') as HTMLElement;
      if (searchPanel) searchPanel.style.display = 'none';
      
      if (this.layout === 'search-focused') {
        this.setLayout('balanced');
      }
    }
  }

  private initializeGraphSearchIfNeeded() {
    if (!this.graphSearch) {
      const searchContent = this.containerEl.querySelector('.ki-search-content') as HTMLElement;
      if (searchContent) {
        this.graphSearch = new GraphSearch(
          searchContent,
          this.plugin,
          this.handleGraphSearchResults.bind(this),
          this.handleGraphNodeSelect.bind(this)
        );
        
        // Update with current context
        if (this.currentContext.nodes.length > 0) {
          this.graphSearch.updateGraphData(this.currentContext.nodes, this.currentContext.edges);
        }
      }
    }
  }

  private handleGraphSearchResults(results: GraphSearchResult[]) {
    // Update graph visualization with search results
    const nodeIds = results.map(r => r.node.id);
    
    // Filter current context to show only relevant nodes
    const filteredNodes = this.currentContext.nodes.filter(node => 
      nodeIds.includes(node.id) || this.isConnectedToSearchResults(node, nodeIds)
    );
    
    const filteredEdges = this.currentContext.edges.filter(edge => {
      const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
      const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
      const nodeIdSet = new Set(filteredNodes.map(n => n.id));
      return nodeIdSet.has(sourceId) && nodeIdSet.has(targetId);
    });
    
    this.graphViz.updateGraph(filteredNodes, filteredEdges, nodeIds);
  }

  private handleGraphNodeSelect(nodeId: string) {
    // Highlight in graph and potentially trigger chat context
    this.graphViz.highlightNode(nodeId);
    
    // Optionally add context message to chat
    const node = this.currentContext.nodes.find(n => n.id === nodeId);
    if (node) {
      // This could trigger a context-aware message in the chat
      this.handleContextUpdate(nodeId);
    }
  }

  private isConnectedToSearchResults(node: GraphNode, searchResultIds: string[]): boolean {
    return this.currentContext.edges.some(edge => {
      const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
      const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
      
      return (node.id === sourceId && searchResultIds.includes(targetId)) ||
             (node.id === targetId && searchResultIds.includes(sourceId));
    });
  }

  private syncChatWithGraph() {
    // Analyze current chat context and sync with graph
    const conversationHistory = this.chatInterface.getConversationHistory();
    
    if (conversationHistory.length > 0) {
      // Extract entities and topics from recent messages
      const recentMessages = conversationHistory.slice(-3);
      const combinedText = recentMessages.map(msg => msg.content).join(' ');
      
      // Use graph search to find relevant nodes
      if (this.graphSearch) {
        // Trigger a search based on chat content
        const searchInput = this.containerEl.querySelector('.ki-graph-search-input') as HTMLInputElement;
        if (searchInput) {
          searchInput.value = this.extractKeyTerms(combinedText);
          searchInput.dispatchEvent(new Event('input'));
        }
      }
    }
  }

  private extractKeyTerms(text: string): string {
    // Simple keyword extraction - could be enhanced with NLP
    const words = text.toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 3)
      .filter(word => !['eine', 'einen', 'einer', 'dass', 'wenn', 'dann', 'haben', 'sind', 'wird', 'kann', 'soll'].includes(word));
    
    // Get most frequent words
    const wordCount = new Map<string, number>();
    words.forEach(word => {
      wordCount.set(word, (wordCount.get(word) || 0) + 1);
    });
    
    return Array.from(wordCount.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([word]) => word)
      .join(' ');
  }

  private applyStyles() {
    // Add custom CSS for Workbench
    const style = document.createElement('style');
    style.textContent = `
      .ki-chat-view {
        height: 100%;
        overflow: hidden;
        background: var(--background-primary);
      }

      /* Workbench Layout */
      .ki-workbench {
        display: flex;
        flex-direction: column;
        height: 100%;
      }

      .ki-workbench-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        border-bottom: 2px solid var(--background-modifier-border);
        background: var(--background-secondary);
        min-height: 60px;
      }

      .ki-workbench-title {
        margin: 0;
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--text-normal);
      }

      .ki-workbench-controls {
        display: flex;
        align-items: center;
        gap: 1.5rem;
      }

      .ki-workbench-layout-group,
      .ki-workbench-tools-group {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      .ki-workbench-label {
        font-size: 0.9rem;
        color: var(--text-muted);
        font-weight: 500;
      }

      .ki-workbench-layout-btn,
      .ki-workbench-tool-btn {
        padding: 0.5rem 0.75rem;
        border: 1px solid var(--background-modifier-border);
        border-radius: 6px;
        background: var(--background-primary);
        color: var(--text-normal);
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 0.9rem;
      }

      .ki-workbench-layout-btn:hover,
      .ki-workbench-tool-btn:hover {
        background: var(--background-modifier-hover);
        transform: translateY(-1px);
      }

      .ki-workbench-layout-btn.active {
        background: var(--interactive-accent);
        color: white;
        border-color: var(--interactive-accent);
      }

      .ki-workbench-main {
        display: flex;
        flex: 1;
        overflow: hidden;
        gap: 1px;
        background: var(--background-modifier-border);
      }

      /* Panel Styles */
      .ki-workbench-panel {
        display: flex;
        flex-direction: column;
        background: var(--background-primary);
        transition: all 0.3s ease;
        min-width: 250px;
      }

      .ki-panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 1rem;
        background: var(--background-secondary);
        border-bottom: 1px solid var(--background-modifier-border);
        min-height: 45px;
      }

      .ki-panel-header h4 {
        margin: 0;
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-normal);
      }

      .ki-panel-actions {
        display: flex;
        gap: 0.25rem;
      }

      .ki-panel-action-btn {
        padding: 0.25rem 0.5rem;
        background: none;
        border: 1px solid var(--background-modifier-border);
        border-radius: 4px;
        color: var(--text-muted);
        cursor: pointer;
        font-size: 0.8rem;
        transition: all 0.2s ease;
      }

      .ki-panel-action-btn:hover {
        background: var(--background-modifier-hover);
        color: var(--text-normal);
      }

      .ki-panel-maximized {
        box-shadow: 0 0 0 2px var(--interactive-accent);
        z-index: 10;
      }

      .ki-panel-maximized .ki-panel-header {
        background: var(--interactive-accent);
        color: white;
      }

      .ki-panel-maximized .ki-panel-header h4 {
        color: white;
      }

      /* Chat Panel */
      .ki-chat-panel {
        flex: 1;
        display: flex;
        flex-direction: column;
      }

      .ki-chat-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }

      /* Graph Panel */
      .ki-graph-panel {
        flex: 1;
        display: flex;
        flex-direction: column;
      }

      .ki-graph-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }

      .ki-graph-canvas {
        flex: 1;
        position: relative;
        overflow: hidden;
      }

      /* Search Panel */
      .ki-search-panel {
        flex: 1;
        display: flex;
        flex-direction: column;
      }

      .ki-search-content {
        flex: 1;
        overflow: hidden;
      }

      /* Layout-specific styles */
      .ki-layout-chat-focused .ki-chat-panel {
        border: 2px solid var(--interactive-accent);
      }

      .ki-layout-graph-focused .ki-graph-panel {
        border: 2px solid var(--interactive-accent);
      }

      .ki-layout-search-focused .ki-search-panel {
        border: 2px solid var(--interactive-accent);
      }

      .ki-layout-balanced .ki-workbench-panel {
        flex: 1;
      }

      /* Responsive Design */
      @media (max-width: 1200px) {
        .ki-workbench-header {
          flex-direction: column;
          gap: 1rem;
          padding: 0.75rem;
        }

        .ki-workbench-controls {
          gap: 1rem;
        }

        .ki-workbench-main {
          flex-direction: column;
        }

        .ki-workbench-panel {
          min-width: unset;
          min-height: 200px;
        }

        .ki-layout-chat-focused .ki-chat-panel,
        .ki-layout-graph-focused .ki-graph-panel,
        .ki-layout-search-focused .ki-search-panel {
          flex: 3;
        }
      }

      @media (max-width: 768px) {
        .ki-workbench-header {
          padding: 0.5rem;
        }

        .ki-workbench-title {
          font-size: 1.1rem;
        }

        .ki-workbench-layout-btn,
        .ki-workbench-tool-btn {
          padding: 0.4rem 0.6rem;
          font-size: 0.8rem;
        }

        .ki-workbench-main {
          flex-direction: column;
        }

        .ki-panel-header {
          padding: 0.5rem 0.75rem;
        }

        .ki-panel-header h4 {
          font-size: 0.9rem;
        }
      }

      /* Animation and transitions */
      .ki-workbench-panel {
        animation: slideIn 0.3s ease-out;
      }

      @keyframes slideIn {
        from {
          opacity: 0;
          transform: translateY(10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      .ki-panel-maximized {
        animation: maximize 0.3s ease-out;
      }

      @keyframes maximize {
        from {
          transform: scale(0.98);
        }
        to {
          transform: scale(1);
        }
      }

      /* Status indicators */
      .ki-workbench-panel.active::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--interactive-accent);
        z-index: 1;
      }

      .ki-workbench-panel {
        position: relative;
      }

      /* Enhanced visual feedback */
      .ki-workbench-layout-btn.active {
        box-shadow: 0 2px 8px rgba(var(--interactive-accent-rgb), 0.3);
      }

      .ki-workbench-tool-btn:active {
        transform: translateY(0);
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
      }
        min-width: 400px;
      }

      .ki-graph-panel {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-width: 400px;
        border-left: 1px solid var(--background-modifier-border);
      }

      .ki-graph-header {
        padding: 1rem;
        border-bottom: 1px solid var(--background-modifier-border);
      }

      .ki-graph-header h3 {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 600;
      }

      .ki-graph-canvas {
        flex: 1;
        position: relative;
        overflow: hidden;
      }

      @media (max-width: 1000px) {
        .ki-chat-container {
          flex-direction: column;
        }
        
        .ki-graph-panel {
          border-left: none;
          border-top: 1px solid var(--background-modifier-border);
          min-height: 300px;
        }
      }
    `;
    document.head.append(style);
  }
}