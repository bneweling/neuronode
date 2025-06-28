export class ApiClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  updateSettings(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` }),
      ...options.headers
    };

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  async query(query: string, context?: any) {
    return this.request('/query', {
      method: 'POST',
      body: JSON.stringify({ query, context })
    });
  }

  // === Dokumentenverarbeitung ===
  
  async analyzeDocumentPreview(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('preview_length', '2000');

    const response = await fetch(`${this.baseUrl}/documents/analyze-preview`, {
      method: 'POST',
      headers: {
        ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Preview Analysis Error: ${response.statusText}`);
    }

    return response.json();
  }

  async uploadDocument(file: File, options: {
    forceType?: string;
    validate?: boolean;
  } = {}) {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options.forceType) {
      formData.append('force_type', options.forceType);
    }
    
    if (options.validate !== undefined) {
      formData.append('validate', options.validate.toString());
    }

    const response = await fetch(`${this.baseUrl}/documents/upload`, {
      method: 'POST',
      headers: {
        ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Upload Error: ${response.statusText}`);
    }

    return response.json();
  }

  async getProcessingStatus(taskId: string) {
    return this.request(`/documents/processing-status/${encodeURIComponent(taskId)}`);
  }

  // === Knowledge Graph ===

  async getNodeContext(nodeId: string, depth: number = 2) {
    return this.request(`/knowledge-graph/node/${encodeURIComponent(nodeId)}?depth=${depth}`);
  }

  async getGraphContext(nodeIds: string[], depth: number = 2) {
    const nodes: any[] = [];
    const edges: any[] = [];
    const processedNodes = new Set<string>();

    // Fetch data for each node
    for (const nodeId of nodeIds) {
      try {
        const result = await this.getNodeContext(nodeId, depth);
        
        // Add nodes
        result.nodes.forEach((node: any) => {
          if (!processedNodes.has(node.id)) {
            processedNodes.add(node.id);
            nodes.push({
              id: node.id,
              type: node._labels?.[0] || 'Unknown',
              data: node,
              distance: node._distance || 0
            });
          }
        });

        // Add edges
        result.edges.forEach((edge: any) => {
          edges.push({
            source: edge.source,
            target: edge.target,
            type: edge.type,
            data: edge.properties
          });
        });
      } catch (error) {
        console.warn(`Failed to fetch context for node ${nodeId}:`, error);
      }
    }

    return { nodes, edges };
  }

  async searchGraph(query: string, nodeType?: string, limit: number = 20) {
    const params = new URLSearchParams({
      query,
      ...(nodeType && { node_type: nodeType }),
      limit: limit.toString()
    });

    return this.request(`/knowledge-graph/search?${params}`);
  }

  async getStats() {
    return this.request('/knowledge-graph/stats');
  }

  async getRelationshipTypes() {
    return this.request('/knowledge-graph/relationships/types');
  }

  async getOrphanNodes(minConnections: number = 1) {
    return this.request(`/knowledge-graph/orphans?min_connections=${minConnections}`);
  }

  async validateRelationship(sourceId: string, targetId: string, relationshipType?: string) {
    const params = new URLSearchParams({
      source_id: sourceId,
      target_id: targetId,
      ...(relationshipType && { relationship_type: relationshipType })
    });

    return this.request('/knowledge-graph/validate-relationship', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: params
    });
  }

  // === Hilfsmethoden ===

  extractNodeIds(response: any): string[] {
    const nodeIds: string[] = [];
    
    // Extrahiere IDs aus verschiedenen Response-Formaten
    if (response.context?.nodes) {
      response.context.nodes.forEach((node: any) => {
        if (node.id) nodeIds.push(node.id);
      });
    }
    
    if (response.sources) {
      response.sources.forEach((source: any) => {
        if (source.metadata?.id) nodeIds.push(source.metadata.id);
        if (source.metadata?.control_id) nodeIds.push(source.metadata.control_id);
      });
    }

    // Extrahiere Control-IDs aus Text (z.B. "OPS.1.1.2")
    const controlIdPattern = /\b[A-Z]{2,4}\.\d+\.\d+\.\d+\b/g;
    const textContent = JSON.stringify(response).toLowerCase();
    const matches = textContent.match(controlIdPattern);
    if (matches) {
      nodeIds.push(...matches);
    }

    return [...new Set(nodeIds)]; // Entferne Duplikate
  }

  // === Entwickler-Tools ===

  async getSystemHealth() {
    try {
      const [stats, orphans, relationships] = await Promise.all([
        this.getStats(),
        this.getOrphanNodes(0),
        this.getRelationshipTypes()
      ]);

      return {
        status: 'healthy',
        stats,
        issues: {
          orphan_count: orphans.count,
          missing_relationships: orphans.suggestions_available
        },
        relationship_diversity: relationships.total_types,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return {
        status: 'error',
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }
}