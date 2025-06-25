import { Component } from 'obsidian';
import KIWissenssystemPlugin from '../../main';
import { 
  GraphNode, 
  GraphEdge, 
  GraphSearchQuery, 
  GraphSearchResult, 
  GraphSearchFilter,
  GraphCategory,
  GraphStats 
} from '../types';

export class GraphSearch extends Component {
  private container: HTMLElement;
  private plugin: KIWissenssystemPlugin;
  private searchInput: HTMLInputElement;
  private filtersContainer: HTMLElement;
  private resultsContainer: HTMLElement;
  private statsContainer: HTMLElement;
  private categoriesContainer: HTMLElement;
  
  private currentQuery: GraphSearchQuery;
  private currentResults: GraphSearchResult[] = [];
  private allNodes: GraphNode[] = [];
  private allEdges: GraphEdge[] = [];
  private categories: GraphCategory[] = [];
  private stats: GraphStats;
  
  private onSearchResult: (results: GraphSearchResult[]) => void;
  private onNodeSelect: (nodeId: string) => void;

  constructor(
    container: HTMLElement,
    plugin: KIWissenssystemPlugin,
    onSearchResult: (results: GraphSearchResult[]) => void,
    onNodeSelect: (nodeId: string) => void
  ) {
    super();
    this.container = container;
    this.plugin = plugin;
    this.onSearchResult = onSearchResult;
    this.onNodeSelect = onNodeSelect;
    
    this.initializeDefaultQuery();
    this.initialize();
  }

  private initializeDefaultQuery() {
    this.currentQuery = {
      text: '',
      filters: {
        nodeTypes: [],
        edgeTypes: [],
        minConnections: 0,
        maxConnections: 1000,
        tags: [],
        confidence: {
          min: 0,
          max: 1
        }
      },
      searchType: 'semantic',
      scope: 'all',
      maxResults: 50,
      sortBy: 'relevance'
    };
  }

  private initialize() {
    this.container.addClass('ki-graph-search');
    
    // Header
    const header = this.container.createDiv('ki-graph-search-header');
    header.createEl('h3', { text: 'Graph-Suche' });
    
    const toggleBtn = header.createEl('button', {
      text: '⚙️ Filter',
      cls: 'ki-graph-search-toggle'
    });
    toggleBtn.addEventListener('click', () => this.toggleFilters());

    // Search input
    const searchSection = this.container.createDiv('ki-graph-search-input-section');
    
    this.searchInput = searchSection.createEl('input', {
      type: 'text',
      placeholder: 'Knoten, Eigenschaften oder Inhalte durchsuchen...',
      cls: 'ki-graph-search-input'
    });
    
    this.searchInput.addEventListener('input', (e) => {
      this.currentQuery.text = (e.target as HTMLInputElement).value;
      this.performSearch();
    });

    // Search type selector
    const searchTypeContainer = searchSection.createDiv('ki-graph-search-type');
    this.createSearchTypeSelector(searchTypeContainer);

    // Filters container (initially hidden)
    this.filtersContainer = this.container.createDiv('ki-graph-search-filters');
    this.filtersContainer.style.display = 'none';
    this.renderFilters();

    // Stats container
    this.statsContainer = this.container.createDiv('ki-graph-search-stats');
    
    // Categories container
    this.categoriesContainer = this.container.createDiv('ki-graph-search-categories');
    
    // Results container
    this.resultsContainer = this.container.createDiv('ki-graph-search-results');

    // Apply styles
    this.applyStyles();
  }

  private createSearchTypeSelector(container: HTMLElement) {
    const label = container.createEl('label', { text: 'Suchtyp:' });
    const select = container.createEl('select', { cls: 'ki-graph-search-type-select' });
    
    const searchTypes = [
      { value: 'semantic', label: '🧠 Semantisch' },
      { value: 'exact', label: '🎯 Exakt' },
      { value: 'fuzzy', label: '🔍 Unscharf' },
      { value: 'graph-walk', label: '🕸️ Graph-Traversierung' }
    ];
    
    searchTypes.forEach(type => {
      const option = select.createEl('option', { 
        value: type.value, 
        text: type.label 
      });
      if (type.value === this.currentQuery.searchType) {
        option.selected = true;
      }
    });
    
    select.addEventListener('change', (e) => {
      this.currentQuery.searchType = (e.target as HTMLSelectElement).value as any;
      this.performSearch();
    });
  }

  private renderFilters() {
    this.filtersContainer.empty();
    
    const filtersGrid = this.filtersContainer.createDiv('ki-graph-filters-grid');
    
    // Node Types Filter
    const nodeTypesSection = filtersGrid.createDiv('ki-graph-filter-section');
    nodeTypesSection.createEl('h4', { text: 'Knotentypen' });
    const nodeTypesContainer = nodeTypesSection.createDiv('ki-graph-filter-checkboxes');
    
    const availableNodeTypes = ['ControlItem', 'Technology', 'KnowledgeChunk', 'Document', 'Process', 'Risk'];
    availableNodeTypes.forEach(type => {
      const checkboxContainer = nodeTypesContainer.createDiv('ki-graph-filter-checkbox');
      const checkbox = checkboxContainer.createEl('input', { type: 'checkbox' });
      checkbox.id = `node-type-${type}`;
      checkbox.checked = this.currentQuery.filters.nodeTypes.includes(type);
      
      const label = checkboxContainer.createEl('label', { text: type });
      label.setAttribute('for', checkbox.id);
      
      checkbox.addEventListener('change', () => {
        if (checkbox.checked) {
          this.currentQuery.filters.nodeTypes.push(type);
        } else {
          const index = this.currentQuery.filters.nodeTypes.indexOf(type);
          if (index > -1) this.currentQuery.filters.nodeTypes.splice(index, 1);
        }
        this.performSearch();
      });
    });

    // Connection Range Filter
    const connectionsSection = filtersGrid.createDiv('ki-graph-filter-section');
    connectionsSection.createEl('h4', { text: 'Verbindungen' });
    
    const minConnectionsContainer = connectionsSection.createDiv('ki-graph-filter-input');
    minConnectionsContainer.createEl('label', { text: 'Minimum:' });
    const minConnectionsInput = minConnectionsContainer.createEl('input', {
      type: 'number',
      value: this.currentQuery.filters.minConnections.toString(),
      cls: 'ki-graph-filter-number'
    });
    
    const maxConnectionsContainer = connectionsSection.createDiv('ki-graph-filter-input');
    maxConnectionsContainer.createEl('label', { text: 'Maximum:' });
    const maxConnectionsInput = maxConnectionsContainer.createEl('input', {
      type: 'number',
      value: this.currentQuery.filters.maxConnections.toString(),
      cls: 'ki-graph-filter-number'
    });
    
    [minConnectionsInput, maxConnectionsInput].forEach(input => {
      input.addEventListener('change', () => {
        this.currentQuery.filters.minConnections = parseInt(minConnectionsInput.value) || 0;
        this.currentQuery.filters.maxConnections = parseInt(maxConnectionsInput.value) || 1000;
        this.performSearch();
      });
    });

    // Scope and Sort
    const optionsSection = filtersGrid.createDiv('ki-graph-filter-section');
    optionsSection.createEl('h4', { text: 'Optionen' });
    
    const scopeContainer = optionsSection.createDiv('ki-graph-filter-input');
    scopeContainer.createEl('label', { text: 'Bereich:' });
    const scopeSelect = scopeContainer.createEl('select');
    
    const scopes = [
      { value: 'all', label: 'Alle Knoten' },
      { value: 'connected', label: 'Nur verbundene' },
      { value: 'neighborhood', label: 'Nachbarschaft' }
    ];
    
    scopes.forEach(scope => {
      const option = scopeSelect.createEl('option', { 
        value: scope.value, 
        text: scope.label 
      });
      if (scope.value === this.currentQuery.scope) {
        option.selected = true;
      }
    });
    
    scopeSelect.addEventListener('change', () => {
      this.currentQuery.scope = scopeSelect.value as any;
      this.performSearch();
    });

    const sortContainer = optionsSection.createDiv('ki-graph-filter-input');
    sortContainer.createEl('label', { text: 'Sortierung:' });
    const sortSelect = sortContainer.createEl('select');
    
    const sortOptions = [
      { value: 'relevance', label: 'Relevanz' },
      { value: 'connections', label: 'Verbindungen' },
      { value: 'date', label: 'Datum' },
      { value: 'type', label: 'Typ' }
    ];
    
    sortOptions.forEach(sort => {
      const option = sortSelect.createEl('option', { 
        value: sort.value, 
        text: sort.label 
      });
      if (sort.value === this.currentQuery.sortBy) {
        option.selected = true;
      }
    });
    
    sortSelect.addEventListener('change', () => {
      this.currentQuery.sortBy = sortSelect.value as any;
      this.performSearch();
    });

    // Reset button
    const resetBtn = this.filtersContainer.createEl('button', {
      text: 'Filter zurücksetzen',
      cls: 'ki-graph-filter-reset'
    });
    resetBtn.addEventListener('click', () => {
      this.resetFilters();
    });
  }

  private toggleFilters() {
    const isVisible = this.filtersContainer.style.display !== 'none';
    this.filtersContainer.style.display = isVisible ? 'none' : 'block';
  }

  private resetFilters() {
    this.initializeDefaultQuery();
    this.renderFilters();
    this.performSearch();
  }

  updateGraphData(nodes: GraphNode[], edges: GraphEdge[]) {
    this.allNodes = nodes;
    this.allEdges = edges;
    
    // Calculate stats and categories
    this.calculateStats();
    this.renderStats();
    this.renderCategories();
    
    // Perform search if there's a query
    if (this.currentQuery.text) {
      this.performSearch();
    }
  }

  private calculateStats() {
    this.stats = {
      totalNodes: this.allNodes.length,
      totalEdges: this.allEdges.length,
      categories: [],
      avgConnections: 0,
      mostConnected: [],
      orphanNodes: 0,
      clusters: 0
    };

    // Calculate connections for each node
    const nodeConnections = new Map<string, number>();
    this.allEdges.forEach(edge => {
      const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
      const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
      
      nodeConnections.set(sourceId, (nodeConnections.get(sourceId) || 0) + 1);
      nodeConnections.set(targetId, (nodeConnections.get(targetId) || 0) + 1);
    });

    // Calculate average connections
    let totalConnections = 0;
    this.allNodes.forEach(node => {
      const connections = nodeConnections.get(node.id) || 0;
      totalConnections += connections;
    });
    this.stats.avgConnections = this.allNodes.length > 0 ? totalConnections / this.allNodes.length : 0;

    // Find most connected nodes
    this.stats.mostConnected = this.allNodes
      .map(node => ({ ...node, connections: nodeConnections.get(node.id) || 0 }))
      .sort((a, b) => (b as any).connections - (a as any).connections)
      .slice(0, 5);

    // Count orphan nodes
    this.stats.orphanNodes = this.allNodes.filter(node => 
      (nodeConnections.get(node.id) || 0) === 0
    ).length;

    // Calculate categories
    const typeCounts = new Map<string, number>();
    this.allNodes.forEach(node => {
      typeCounts.set(node.type, (typeCounts.get(node.type) || 0) + 1);
    });

    const categoryColors = {
      'ControlItem': '#4a9eff',
      'Technology': '#7c3aed',
      'KnowledgeChunk': '#10b981',
      'Document': '#f59e0b',
      'Process': '#ef4444',
      'Risk': '#8b5cf6'
    };

    const categoryIcons = {
      'ControlItem': '🛡️',
      'Technology': '⚙️',
      'KnowledgeChunk': '📄',
      'Document': '📝',
      'Process': '🔄',
      'Risk': '⚠️'
    };

    this.categories = Array.from(typeCounts.entries()).map(([type, count]) => ({
      name: type,
      color: categoryColors[type as keyof typeof categoryColors] || '#6b7280',
      icon: categoryIcons[type as keyof typeof categoryIcons] || '📊',
      nodeTypes: [type],
      description: `${count} Knoten vom Typ ${type}`,
      count
    }));
  }

  private async performSearch() {
    if (!this.currentQuery.text.trim() && this.currentQuery.filters.nodeTypes.length === 0) {
      this.currentResults = [];
      this.renderResults();
      return;
    }

    try {
      // Show loading state
      this.resultsContainer.empty();
      this.resultsContainer.createDiv('ki-graph-search-loading').setText('Suche läuft...');

      let results: GraphSearchResult[];

      switch (this.currentQuery.searchType) {
        case 'semantic':
          results = await this.performSemanticSearch();
          break;
        case 'exact':
          results = this.performExactSearch();
          break;
        case 'fuzzy':
          results = this.performFuzzySearch();
          break;
        case 'graph-walk':
          results = this.performGraphWalkSearch();
          break;
        default:
          results = this.performExactSearch();
      }

      // Apply filters
      results = this.applyFilters(results);

      // Sort results
      results = this.sortResults(results);

      // Limit results
      results = results.slice(0, this.currentQuery.maxResults);

      this.currentResults = results;
      this.renderResults();
      this.onSearchResult(results);

    } catch (error) {
      console.error('Search error:', error);
      this.resultsContainer.empty();
      this.resultsContainer.createDiv('ki-graph-search-error').setText('Fehler bei der Suche');
    }
  }

  private async performSemanticSearch(): Promise<GraphSearchResult[]> {
    // Use API for semantic search if available
    try {
      const searchResults = await this.plugin.apiClient.searchGraph(
        this.currentQuery.text,
        undefined,
        this.currentQuery.maxResults
      );
      
      return searchResults.nodes?.map((node: any) => ({
        node: node,
        relevance: node.score || 0.5,
        matchType: 'content' as const,
        snippet: node.snippet || '',
        connections: {
          incoming: node.connections?.incoming || 0,
          outgoing: node.connections?.outgoing || 0,
          total: (node.connections?.incoming || 0) + (node.connections?.outgoing || 0)
        }
      })) || [];
    } catch (error) {
      // Fallback to local search
      return this.performFuzzySearch();
    }
  }

  private performExactSearch(): GraphSearchResult[] {
    const query = this.currentQuery.text.toLowerCase();
    return this.allNodes
      .filter(node => {
        const nodeText = this.getNodeSearchText(node).toLowerCase();
        return nodeText.includes(query);
      })
      .map(node => ({
        node,
        relevance: this.calculateExactRelevance(node, query),
        matchType: this.getMatchType(node, query),
        snippet: this.generateSnippet(node, query),
        connections: this.getNodeConnections(node)
      }));
  }

  private performFuzzySearch(): GraphSearchResult[] {
    const query = this.currentQuery.text.toLowerCase();
    const queryWords = query.split(/\s+/).filter(word => word.length > 2);
    
    return this.allNodes
      .map(node => {
        const relevance = this.calculateFuzzyRelevance(node, queryWords);
        return {
          node,
          relevance,
          matchType: this.getMatchType(node, query),
          snippet: this.generateSnippet(node, query),
          connections: this.getNodeConnections(node)
        };
      })
      .filter(result => result.relevance > 0.1);
  }

  private performGraphWalkSearch(): GraphSearchResult[] {
    // Start from nodes that match the query
    const seedNodes = this.performExactSearch();
    const visited = new Set<string>();
    const results = new Map<string, GraphSearchResult>();

    // Add seed nodes
    seedNodes.forEach(result => {
      results.set(result.node.id, result);
      visited.add(result.node.id);
    });

    // Walk the graph to find related nodes
    const queue = [...seedNodes.map(r => r.node)];
    let depth = 0;
    const maxDepth = 3;

    while (queue.length > 0 && depth < maxDepth) {
      const currentBatch = queue.splice(0, queue.length);
      depth++;

      currentBatch.forEach(node => {
        const connectedNodes = this.getConnectedNodes(node);
        connectedNodes.forEach(connectedNode => {
          if (!visited.has(connectedNode.id)) {
            visited.add(connectedNode.id);
            queue.push(connectedNode);
            
            const relevance = Math.max(0.1, 1 - (depth * 0.3));
            results.set(connectedNode.id, {
              node: connectedNode,
              relevance,
              matchType: 'connections',
              snippet: this.generateSnippet(connectedNode, this.currentQuery.text),
              connections: this.getNodeConnections(connectedNode),
              path: this.findShortestPath(seedNodes[0]?.node, connectedNode)
            });
          }
        });
      });
    }

    return Array.from(results.values());
  }

  private getNodeSearchText(node: GraphNode): string {
    let text = node.id;
    if (node.data) {
      text += ' ' + JSON.stringify(node.data);
    }
    return text;
  }

  private calculateExactRelevance(node: GraphNode, query: string): number {
    const nodeText = this.getNodeSearchText(node).toLowerCase();
    const nodeId = node.id.toLowerCase();
    
    if (nodeId === query) return 1.0;
    if (nodeText.startsWith(query)) return 0.9;
    if (nodeId.includes(query)) return 0.8;
    if (nodeText.includes(query)) return 0.7;
    return 0.0;
  }

  private calculateFuzzyRelevance(node: GraphNode, queryWords: string[]): number {
    const nodeText = this.getNodeSearchText(node).toLowerCase();
    const nodeWords = nodeText.split(/\s+/);
    
    let matchScore = 0;
    let totalScore = queryWords.length;

    queryWords.forEach(queryWord => {
      let bestMatch = 0;
      nodeWords.forEach(nodeWord => {
        const similarity = this.calculateStringSimilarity(queryWord, nodeWord);
        bestMatch = Math.max(bestMatch, similarity);
      });
      matchScore += bestMatch;
    });

    return totalScore > 0 ? matchScore / totalScore : 0;
  }

  private calculateStringSimilarity(str1: string, str2: string): number {
    if (str1 === str2) return 1.0;
    if (str1.includes(str2) || str2.includes(str1)) return 0.8;
    
    // Simple character-based similarity
    const longer = str1.length > str2.length ? str1 : str2;
    const shorter = str1.length > str2.length ? str2 : str1;
    
    if (longer.length === 0) return 1.0;
    
    const editDistance = this.levenshteinDistance(longer, shorter);
    return (longer.length - editDistance) / longer.length;
  }

  private levenshteinDistance(str1: string, str2: string): number {
    const matrix = Array(str2.length + 1).fill(null).map(() => 
      Array(str1.length + 1).fill(null)
    );

    for (let i = 0; i <= str1.length; i++) matrix[0][i] = i;
    for (let j = 0; j <= str2.length; j++) matrix[j][0] = j;

    for (let j = 1; j <= str2.length; j++) {
      for (let i = 1; i <= str1.length; i++) {
        const indicator = str1[i - 1] === str2[j - 1] ? 0 : 1;
        matrix[j][i] = Math.min(
          matrix[j][i - 1] + 1,
          matrix[j - 1][i] + 1,
          matrix[j - 1][i - 1] + indicator
        );
      }
    }

    return matrix[str2.length][str1.length];
  }

  private getMatchType(node: GraphNode, query: string): 'title' | 'content' | 'properties' | 'connections' {
    const nodeId = node.id.toLowerCase();
    const lowerQuery = query.toLowerCase();
    
    if (nodeId.includes(lowerQuery)) return 'title';
    if (node.data && JSON.stringify(node.data).toLowerCase().includes(lowerQuery)) return 'properties';
    return 'content';
  }

  private generateSnippet(node: GraphNode, query: string): string {
    const nodeText = this.getNodeSearchText(node);
    const lowerText = nodeText.toLowerCase();
    const lowerQuery = query.toLowerCase();
    
    const index = lowerText.indexOf(lowerQuery);
    if (index === -1) return nodeText.slice(0, 100) + '...';
    
    const start = Math.max(0, index - 50);
    const end = Math.min(nodeText.length, index + query.length + 50);
    
    let snippet = nodeText.slice(start, end);
    if (start > 0) snippet = '...' + snippet;
    if (end < nodeText.length) snippet = snippet + '...';
    
    return snippet;
  }

  private getNodeConnections(node: GraphNode) {
    let incoming = 0, outgoing = 0;
    
    this.allEdges.forEach(edge => {
      const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
      const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
      
      if (sourceId === node.id) outgoing++;
      if (targetId === node.id) incoming++;
    });
    
    return { incoming, outgoing, total: incoming + outgoing };
  }

  private getConnectedNodes(node: GraphNode): GraphNode[] {
    const connected = new Set<string>();
    
    this.allEdges.forEach(edge => {
      const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
      const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
      
      if (sourceId === node.id) connected.add(targetId);
      if (targetId === node.id) connected.add(sourceId);
    });
    
    return this.allNodes.filter(n => connected.has(n.id));
  }

  private findShortestPath(start: GraphNode, end: GraphNode): GraphNode[] | undefined {
    if (!start || !end) return undefined;
    
    const queue = [[start]];
    const visited = new Set([start.id]);
    
    while (queue.length > 0) {
      const path = queue.shift()!;
      const node = path[path.length - 1];
      
      if (node.id === end.id) return path;
      
      const connected = this.getConnectedNodes(node);
      for (const connectedNode of connected) {
        if (!visited.has(connectedNode.id)) {
          visited.add(connectedNode.id);
          queue.push([...path, connectedNode]);
        }
      }
    }
    
    return undefined;
  }

  private applyFilters(results: GraphSearchResult[]): GraphSearchResult[] {
    return results.filter(result => {
      const node = result.node;
      const connections = result.connections;
      
      // Node type filter
      if (this.currentQuery.filters.nodeTypes.length > 0) {
        if (!this.currentQuery.filters.nodeTypes.includes(node.type)) {
          return false;
        }
      }
      
      // Connection count filter
      if (connections.total < this.currentQuery.filters.minConnections ||
          connections.total > this.currentQuery.filters.maxConnections) {
        return false;
      }
      
      return true;
    });
  }

  private sortResults(results: GraphSearchResult[]): GraphSearchResult[] {
    return results.sort((a, b) => {
      switch (this.currentQuery.sortBy) {
        case 'relevance':
          return b.relevance - a.relevance;
        case 'connections':
          return b.connections.total - a.connections.total;
        case 'type':
          return a.node.type.localeCompare(b.node.type);
        case 'date':
          // Assume nodes have creation date in data
          const dateA = a.node.data?.created || 0;
          const dateB = b.node.data?.created || 0;
          return dateB - dateA;
        default:
          return b.relevance - a.relevance;
      }
    });
  }

  private renderStats() {
    this.statsContainer.empty();
    
    if (!this.stats) return;
    
    const statsGrid = this.statsContainer.createDiv('ki-graph-stats-grid');
    
    const stats = [
      { label: 'Knoten', value: this.stats.totalNodes, icon: '🔘' },
      { label: 'Verbindungen', value: this.stats.totalEdges, icon: '🔗' },
      { label: 'Ø Verbindungen', value: this.stats.avgConnections.toFixed(1), icon: '📊' },
      { label: 'Isolierte', value: this.stats.orphanNodes, icon: '🔴' }
    ];
    
    stats.forEach(stat => {
      const statEl = statsGrid.createDiv('ki-graph-stat');
      statEl.createEl('span', { text: stat.icon, cls: 'ki-graph-stat-icon' });
      statEl.createEl('span', { text: stat.value.toString(), cls: 'ki-graph-stat-value' });
      statEl.createEl('span', { text: stat.label, cls: 'ki-graph-stat-label' });
    });
  }

  private renderCategories() {
    this.categoriesContainer.empty();
    
    if (this.categories.length === 0) return;
    
    const categoriesHeader = this.categoriesContainer.createEl('h4', { text: 'Kategorien' });
    const categoriesGrid = this.categoriesContainer.createDiv('ki-graph-categories-grid');
    
    this.categories.forEach(category => {
      const categoryEl = categoriesGrid.createDiv('ki-graph-category');
      categoryEl.style.borderLeftColor = category.color;
      
      const categoryHeader = categoryEl.createDiv('ki-graph-category-header');
      categoryHeader.createEl('span', { text: category.icon, cls: 'ki-graph-category-icon' });
      categoryHeader.createEl('span', { text: category.name, cls: 'ki-graph-category-name' });
      categoryHeader.createEl('span', { text: category.count.toString(), cls: 'ki-graph-category-count' });
      
      categoryEl.addEventListener('click', () => {
        // Filter by this category
        this.currentQuery.filters.nodeTypes = [category.name];
        this.renderFilters();
        this.performSearch();
      });
    });
  }

  private renderResults() {
    this.resultsContainer.empty();
    
    if (this.currentResults.length === 0) {
      if (this.currentQuery.text || this.currentQuery.filters.nodeTypes.length > 0) {
        this.resultsContainer.createDiv('ki-graph-search-empty').setText('Keine Ergebnisse gefunden');
      }
      return;
    }
    
    const resultsHeader = this.resultsContainer.createDiv('ki-graph-search-results-header');
    resultsHeader.createEl('h4', { text: `${this.currentResults.length} Ergebnisse` });
    
    const resultsList = this.resultsContainer.createDiv('ki-graph-search-results-list');
    
    this.currentResults.forEach(result => {
      const resultEl = resultsList.createDiv('ki-graph-search-result');
      
      const resultHeader = resultEl.createDiv('ki-graph-search-result-header');
      resultHeader.createEl('span', { 
        text: this.getCategoryIcon(result.node.type), 
        cls: 'ki-graph-search-result-icon' 
      });
      resultHeader.createEl('span', { 
        text: result.node.id, 
        cls: 'ki-graph-search-result-title' 
      });
      
      const relevanceBar = resultHeader.createDiv('ki-graph-search-result-relevance');
      const relevancePercent = Math.round(result.relevance * 100);
      relevanceBar.style.width = `${relevancePercent}%`;
      relevanceBar.setAttribute('title', `${relevancePercent}% Relevanz`);
      
      const resultMeta = resultEl.createDiv('ki-graph-search-result-meta');
      resultMeta.createEl('span', { 
        text: `${result.node.type}`, 
        cls: 'ki-graph-search-result-type' 
      });
      resultMeta.createEl('span', { 
        text: `${result.connections.total} Verbindungen`, 
        cls: 'ki-graph-search-result-connections' 
      });
      resultMeta.createEl('span', { 
        text: result.matchType, 
        cls: 'ki-graph-search-result-match-type' 
      });
      
      if (result.snippet) {
        const snippetEl = resultEl.createDiv('ki-graph-search-result-snippet');
        snippetEl.setText(result.snippet);
      }
      
      if (result.path && result.path.length > 1) {
        const pathEl = resultEl.createDiv('ki-graph-search-result-path');
        pathEl.createEl('span', { text: 'Pfad: ', cls: 'ki-graph-search-result-path-label' });
        const pathText = result.path.map(node => node.id).join(' → ');
        pathEl.createEl('span', { text: pathText, cls: 'ki-graph-search-result-path-text' });
      }
      
      resultEl.addEventListener('click', () => {
        this.onNodeSelect(result.node.id);
      });
    });
  }

  private getCategoryIcon(nodeType: string): string {
    const icons = {
      'ControlItem': '🛡️',
      'Technology': '⚙️',
      'KnowledgeChunk': '📄',
      'Document': '📝',
      'Process': '🔄',
      'Risk': '⚠️'
    };
    return icons[nodeType as keyof typeof icons] || '📊';
  }

  private applyStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .ki-graph-search {
        display: flex;
        flex-direction: column;
        height: 100%;
        background: var(--background-primary);
      }

      .ki-graph-search-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        border-bottom: 1px solid var(--background-modifier-border);
      }

      .ki-graph-search-header h3 {
        margin: 0;
        font-size: 1.1rem;
      }

      .ki-graph-search-toggle {
        padding: 0.5rem 1rem;
        background: var(--interactive-accent);
        color: white;
        border-radius: 6px;
        font-size: 0.9rem;
        cursor: pointer;
      }

      .ki-graph-search-input-section {
        padding: 1rem;
        border-bottom: 1px solid var(--background-modifier-border);
      }

      .ki-graph-search-input {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid var(--background-modifier-border);
        border-radius: 8px;
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
      }

      .ki-graph-search-type {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      .ki-graph-search-type-select {
        padding: 0.5rem;
        border: 1px solid var(--background-modifier-border);
        border-radius: 6px;
        background: var(--background-primary);
      }

      .ki-graph-search-filters {
        padding: 1rem;
        background: var(--background-secondary);
        border-bottom: 1px solid var(--background-modifier-border);
      }

      .ki-graph-filters-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
      }

      .ki-graph-filter-section h4 {
        margin: 0 0 0.5rem 0;
        font-size: 0.9rem;
        color: var(--text-muted);
      }

      .ki-graph-filter-checkboxes {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
      }

      .ki-graph-filter-checkbox {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      .ki-graph-filter-input {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
      }

      .ki-graph-filter-input label {
        font-size: 0.85rem;
        min-width: 60px;
      }

      .ki-graph-filter-number {
        width: 80px;
        padding: 0.25rem;
        border: 1px solid var(--background-modifier-border);
        border-radius: 4px;
      }

      .ki-graph-filter-reset {
        margin-top: 1rem;
        padding: 0.5rem 1rem;
        background: var(--background-modifier-form-field);
        border: 1px solid var(--background-modifier-border);
        border-radius: 6px;
        cursor: pointer;
      }

      .ki-graph-stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 0.5rem;
        padding: 1rem;
        border-bottom: 1px solid var(--background-modifier-border);
      }

      .ki-graph-stat {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 0.5rem;
        background: var(--background-modifier-form-field);
        border-radius: 8px;
        text-align: center;
      }

      .ki-graph-stat-icon {
        font-size: 1.2rem;
        margin-bottom: 0.25rem;
      }

      .ki-graph-stat-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-normal);
      }

      .ki-graph-stat-label {
        font-size: 0.8rem;
        color: var(--text-muted);
      }

      .ki-graph-categories-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 0.5rem;
        padding: 0 1rem 1rem 1rem;
      }

      .ki-graph-category {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.5rem;
        background: var(--background-modifier-form-field);
        border-radius: 6px;
        border-left: 3px solid;
        cursor: pointer;
        transition: background 0.2s;
      }

      .ki-graph-category:hover {
        background: var(--background-modifier-form-field-highlighted);
      }

      .ki-graph-category-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex: 1;
      }

      .ki-graph-category-name {
        font-size: 0.9rem;
        flex: 1;
      }

      .ki-graph-category-count {
        font-size: 0.8rem;
        color: var(--text-muted);
        background: var(--background-modifier-border);
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
      }

      .ki-graph-search-results {
        flex: 1;
        overflow-y: auto;
      }

      .ki-graph-search-results-header {
        padding: 1rem;
        border-bottom: 1px solid var(--background-modifier-border);
      }

      .ki-graph-search-results-header h4 {
        margin: 0;
        font-size: 1rem;
      }

      .ki-graph-search-results-list {
        padding: 0.5rem;
      }

      .ki-graph-search-result {
        padding: 1rem;
        border: 1px solid var(--background-modifier-border);
        border-radius: 8px;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s;
      }

      .ki-graph-search-result:hover {
        background: var(--background-modifier-hover);
        border-color: var(--interactive-accent);
      }

      .ki-graph-search-result-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
      }

      .ki-graph-search-result-title {
        font-weight: 600;
        flex: 1;
      }

      .ki-graph-search-result-relevance {
        height: 4px;
        background: var(--interactive-accent);
        border-radius: 2px;
        min-width: 20px;
      }

      .ki-graph-search-result-meta {
        display: flex;
        gap: 1rem;
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-bottom: 0.5rem;
      }

      .ki-graph-search-result-snippet {
        font-size: 0.9rem;
        line-height: 1.4;
        color: var(--text-muted);
        background: var(--background-modifier-form-field);
        padding: 0.5rem;
        border-radius: 4px;
        margin-bottom: 0.5rem;
      }

      .ki-graph-search-result-path {
        font-size: 0.8rem;
        color: var(--text-muted);
      }

      .ki-graph-search-result-path-text {
        font-family: monospace;
      }

      .ki-graph-search-loading,
      .ki-graph-search-empty,
      .ki-graph-search-error {
        padding: 2rem;
        text-align: center;
        color: var(--text-muted);
      }

      .ki-graph-search-error {
        color: var(--text-error);
      }
    `;
    document.head.append(style);
  }

  destroy() {
    this.currentResults = [];
    this.allNodes = [];
    this.allEdges = [];
  }
} 