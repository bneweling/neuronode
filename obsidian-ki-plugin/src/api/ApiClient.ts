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

  async getGraphContext(nodeIds: string[], depth: number = 2) {
    const nodes: any[] = [];
    const edges: any[] = [];
    const processedNodes = new Set<string>();

    // Fetch data for each node
    for (const nodeId of nodeIds) {
      const result = await this.request(`/knowledge-graph/node/${encodeURIComponent(nodeId)}?depth=${depth}`);
      
      // Add nodes
      result.nodes.forEach((node: any) => {
        if (!processedNodes.has(node.id)) {
          processedNodes.add(node.id);
          nodes.push({
            id: node.id,
            type: node.labels?.[0] || 'Unknown',
            data: node
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
}