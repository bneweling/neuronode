export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
  confidence?: number;
}

export interface Source {
  type: string;
  source: string;
  control_id?: string;
  title?: string;
  relevance?: number;
}

export interface GraphNode {
  id: string;
  type: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
  data?: any;
}

export interface GraphEdge {
  source: string | GraphNode;
  target: string | GraphNode;
  type: string;
  data?: any;
}

// Neue Typen für Chat-Speicherung
export interface ChatSession {
  id: string;
  title: string;
  created: Date;
  lastUpdated: Date;
  messages: Message[];
  tags?: string[];
  summary?: string;
}

export interface ChatStorage {
  sessions: ChatSession[];
  currentSessionId: string | null;
  settings: {
    maxSessions: number;
    autoSave: boolean;
    autoTitle: boolean;
  };
}

export interface ChatHistoryEntry {
  sessionId: string;
  title: string;
  preview: string;
  timestamp: Date;
  messageCount: number;
}

// Neue Typen für erweiterte Graph-Suche
export interface GraphSearchFilter {
  nodeTypes: string[];
  edgeTypes: string[];
  minConnections: number;
  maxConnections: number;
  dateRange?: {
    start: Date;
    end: Date;
  };
  tags?: string[];
  confidence?: {
    min: number;
    max: number;
  };
}

export interface GraphSearchQuery {
  text: string;
  filters: GraphSearchFilter;
  searchType: 'semantic' | 'exact' | 'fuzzy' | 'graph-walk';
  scope: 'all' | 'connected' | 'neighborhood';
  maxResults: number;
  sortBy: 'relevance' | 'connections' | 'date' | 'type';
}

export interface GraphSearchResult {
  node: GraphNode;
  relevance: number;
  matchType: 'title' | 'content' | 'properties' | 'connections';
  snippet: string;
  path?: GraphNode[];
  connections: {
    incoming: number;
    outgoing: number;
    total: number;
  };
}

export interface GraphCategory {
  name: string;
  color: string;
  icon: string;
  nodeTypes: string[];
  description: string;
  count: number;
}

export interface GraphStats {
  totalNodes: number;
  totalEdges: number;
  categories: GraphCategory[];
  avgConnections: number;
  mostConnected: GraphNode[];
  orphanNodes: number;
  clusters: number;
}