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