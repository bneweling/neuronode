import { ItemView, WorkspaceLeaf } from 'obsidian';
import KIWissenssystemPlugin from '../../main';
import { ChatInterface } from '../components/ChatInterface';
import { GraphVisualization } from '../components/GraphVisualization';
import { Message, GraphNode, GraphEdge } from '../types';

export const VIEW_TYPE_KNOWLEDGE_CHAT = 'knowledge-chat-view';

export class KnowledgeChatView extends ItemView {
  plugin: KIWissenssystemPlugin;
  chatInterface: ChatInterface;
  graphViz: GraphVisualization;
  currentContext: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  } = { nodes: [], edges: [] };

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

    // Create main layout
    const mainContainer = container.createDiv('ki-chat-container');
    
    // Left side: Chat interface
    const chatContainer = mainContainer.createDiv('ki-chat-panel');
    
    // Right side: Graph visualization
    const graphContainer = mainContainer.createDiv('ki-graph-panel');
    const graphHeader = graphContainer.createDiv('ki-graph-header');
    graphHeader.createEl('h3', { text: 'Kontext-Graph' });
    
    const graphCanvas = graphContainer.createDiv('ki-graph-canvas');
    
    // Initialize components
    this.chatInterface = new ChatInterface(
      chatContainer,
      this.plugin,
      this.handleChatMessage.bind(this),
      this.handleContextUpdate.bind(this)
    );

    this.graphViz = new GraphVisualization(
      graphCanvas,
      this.plugin.settings
    );

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

  private applyStyles() {
    // Add custom CSS
    const style = document.createElement('style');
    style.textContent = `
      .ki-chat-view {
        height: 100%;
        overflow: hidden;
      }

      .ki-chat-container {
        display: flex;
        height: 100%;
        gap: 1rem;
      }

      .ki-chat-panel {
        flex: 1;
        display: flex;
        flex-direction: column;
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