import * as d3 from 'd3';
import { GraphNode, GraphEdge } from '../types';

export class GraphVisualization {
  private container: HTMLElement;
  private svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
  private g: d3.Selection<SVGGElement, unknown, null, undefined>;
  private simulation: d3.Simulation<GraphNode, GraphEdge>;
  private settings: any;
  private width: number;
  private height: number;
  private nodes: GraphNode[] = [];
  private edges: GraphEdge[] = [];
  private highlightedNodes: Set<string> = new Set();

  constructor(container: HTMLElement, settings: any) {
    this.container = container;
    this.settings = settings;
    this.initialize();
  }

  private initialize() {
    // Get container dimensions
    const rect = this.container.getBoundingClientRect();
    this.width = rect.width || 800;
    this.height = rect.height || 600;

    // Create SVG
    this.svg = d3.select(this.container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${this.width} ${this.height}`);

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 10])
      .on('zoom', (event) => {
        this.g.attr('transform', event.transform);
      });

    this.svg.call(zoom);

    // Create main group
    this.g = this.svg.append('g');

    // Define arrow markers
    this.svg.append('defs').selectAll('marker')
      .data(['arrow'])
      .enter().append('marker')
      .attr('id', d => d)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', 'var(--text-muted)');

    // Initialize force simulation
    this.simulation = d3.forceSimulation<GraphNode>()
      .force('link', d3.forceLink<GraphNode, GraphEdge>()
        .id(d => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(this.width / 2, this.height / 2))
      .force('collision', d3.forceCollide().radius(30));

    // Add resize observer
    const resizeObserver = new ResizeObserver(() => {
      this.handleResize();
    });
    resizeObserver.observe(this.container);
  }

  updateGraph(nodes: GraphNode[], edges: GraphEdge[], primaryNodeIds: string[] = []) {
    this.nodes = nodes;
    this.edges = edges;
    this.highlightedNodes = new Set(primaryNodeIds);

    // Clear existing elements
    this.g.selectAll('.link').remove();
    this.g.selectAll('.node').remove();

    // Create links
    const link = this.g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(edges)
      .enter().append('line')
      .attr('class', 'link')
      .attr('stroke', d => this.getLinkColor(d))
      .attr('stroke-width', d => this.getLinkWidth(d))
      .attr('marker-end', 'url(#arrow)')
      .style('opacity', d => this.getLinkOpacity(d));

    // Create nodes
    const node = this.g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .enter().append('g')
      .attr('class', 'node')
      .call(this.drag(this.simulation));

    // Add circles
    node.append('circle')
      .attr('r', d => this.getNodeRadius(d))
      .attr('fill', d => this.getNodeColor(d))
      .attr('stroke', d => this.getNodeStrokeColor(d))
      .attr('stroke-width', 2)
      .style('opacity', d => this.getNodeOpacity(d));

    // Add labels
    node.append('text')
      .text(d => this.getNodeLabel(d))
      .attr('x', 0)
      .attr('y', -20)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('fill', 'var(--text-normal)')
      .style('opacity', d => this.getNodeOpacity(d));

    // Add tooltips
    node.append('title')
      .text(d => this.getNodeTooltip(d));

    // Node interactions
    node.on('click', (event, d) => this.handleNodeClick(d))
      .on('mouseenter', (event, d) => this.handleNodeHover(d, true))
      .on('mouseleave', (event, d) => this.handleNodeHover(d, false));

    // Update simulation
    this.simulation.nodes(nodes);
    (this.simulation.force('link') as d3.ForceLink<GraphNode, GraphEdge>).links(edges);

    this.simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as any).x)
        .attr('y1', d => (d.source as any).y)
        .attr('x2', d => (d.target as any).x)
        .attr('y2', d => (d.target as any).y);

      node
        .attr('transform', d => `translate(${d.x},${d.y})`);
    });

    this.simulation.alpha(1).restart();
  }

  highlightNode(nodeId: string) {
    // Update highlighted nodes
    this.highlightedNodes.add(nodeId);
    
    // Update visual representation
    this.g.selectAll('.node')
      .select('circle')
      .transition()
      .duration(300)
      .attr('r', (d: any) => this.getNodeRadius(d))
      .attr('fill', (d: any) => this.getNodeColor(d))
      .style('opacity', (d: any) => this.getNodeOpacity(d));

    // Center on highlighted node
    const node = this.nodes.find(n => n.id === nodeId);
    if (node && node.x && node.y) {
      const transform = d3.zoomIdentity
        .translate(this.width / 2 - node.x, this.height / 2 - node.y);
      
      this.svg.transition()
        .duration(750)
        .call(
          d3.zoom<SVGSVGElement, unknown>().transform,
          transform
        );
    }
  }

  private getNodeRadius(node: GraphNode): number {
    if (this.highlightedNodes.has(node.id)) return 20;
    if (node.type === 'ControlItem') return 15;
    if (node.type === 'Technology') return 12;
    return 10;
  }

  private getNodeColor(node: GraphNode): string {
    if (this.highlightedNodes.has(node.id)) {
      return 'var(--interactive-accent)';
    }
    
    switch (node.type) {
      case 'ControlItem':
        return '#4a9eff';
      case 'Technology':
        return '#7c3aed';
      case 'KnowledgeChunk':
        return '#10b981';
      default:
        return '#6b7280';
    }
  }

  private getNodeStrokeColor(node: GraphNode): string {
    if (this.highlightedNodes.has(node.id)) {
      return 'var(--interactive-accent-hover)';
    }
    return this.getNodeColor(node);
  }

  private getNodeOpacity(node: GraphNode): number {
    if (this.highlightedNodes.size === 0) return 1;
    if (this.highlightedNodes.has(node.id)) return 1;
    
    // Check if node is neighbor of highlighted nodes
    const isNeighbor = this.edges.some(edge => {
      const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source;
      const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target;
      
      return (this.highlightedNodes.has(sourceId) && targetId === node.id) ||
             (this.highlightedNodes.has(targetId) && sourceId === node.id);
    });
    
    return isNeighbor ? 0.6 : 0.3;
  }

  private getNodeLabel(node: GraphNode): string {
    if (node.type === 'ControlItem') {
      return node.data?.id || node.id;
    }
    return node.data?.name || node.data?.title || node.id;
  }

  private getNodeTooltip(node: GraphNode): string {
    const parts = [`Type: ${node.type}`];
    
    if (node.data?.title) parts.push(`Title: ${node.data.title}`);
    if (node.data?.source) parts.push(`Source: ${node.data.source}`);
    if (node.data?.level) parts.push(`Level: ${node.data.level}`);
    
    return parts.join('\n');
  }

  private getLinkColor(edge: GraphEdge): string {
    switch (edge.type) {
      case 'IMPLEMENTS':
        return '#10b981';
      case 'MAPS_TO':
        return '#3b82f6';
      case 'REFERENCES':
        return '#f59e0b';
      default:
        return 'var(--text-muted)';
    }
  }

  private getLinkWidth(edge: GraphEdge): number {
    if (edge.data?.confidence) {
      return 1 + edge.data.confidence * 3;
    }
    return 2;
  }

  private getLinkOpacity(edge: GraphEdge): number {
    if (this.highlightedNodes.size === 0) return 0.6;
    
    const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source;
    const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target;
    
    if (this.highlightedNodes.has(sourceId) || this.highlightedNodes.has(targetId)) {
      return 0.8;
    }
    
    return 0.2;
  }

  private handleNodeClick(node: GraphNode) {
    // Toggle highlight
    if (this.highlightedNodes.has(node.id)) {
      this.highlightedNodes.delete(node.id);
    } else {
      this.highlightedNodes.add(node.id);
    }
    
    // Update visualization
    this.updateGraph(this.nodes, this.edges, Array.from(this.highlightedNodes));
    
    // Emit event
    const event = new CustomEvent('node-clicked', { detail: node });
    this.container.dispatchEvent(event);
  }

  private handleNodeHover(node: GraphNode, isEntering: boolean) {
    if (isEntering) {
      // Show detailed tooltip
      this.showDetailedTooltip(node);
    } else {
      // Hide tooltip
      this.hideTooltip();
    }
  }

  private showDetailedTooltip(node: GraphNode) {
    // Implementation for detailed tooltip
    const tooltip = d3.select(this.container)
      .append('div')
      .attr('class', 'ki-graph-tooltip')
      .style('position', 'absolute')
      .style('opacity', 0);

    const content = this.createTooltipContent(node);
    tooltip.html(content);

    tooltip.transition()
      .duration(200)
      .style('opacity', 0.9);
  }

  private hideTooltip() {
    d3.select(this.container)
      .select('.ki-graph-tooltip')
      .remove();
  }

  private createTooltipContent(node: GraphNode): string {
    let html = `<div class="ki-tooltip-header">${node.type}</div>`;
    
    if (node.data) {
      html += '<div class="ki-tooltip-content">';
      
      if (node.data.id) html += `<div><strong>ID:</strong> ${node.data.id}</div>`;
      if (node.data.title) html += `<div><strong>Title:</strong> ${node.data.title}</div>`;
      if (node.data.source) html += `<div><strong>Source:</strong> ${node.data.source}</div>`;
      if (node.data.level) html += `<div><strong>Level:</strong> ${node.data.level}</div>`;
      
      if (node.data.text) {
        const preview = node.data.text.substring(0, 200) + '...';
        html += `<div class="ki-tooltip-text">${preview}</div>`;
      }
      
      html += '</div>';
    }
    
    return html;
  }

  private drag(simulation: d3.Simulation<GraphNode, GraphEdge>) {
    function dragstarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return d3.drag<SVGGElement, GraphNode>()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended);
  }

  private handleResize() {
    const rect = this.container.getBoundingClientRect();
    this.width = rect.width;
    this.height = rect.height;
    
    this.svg.attr('viewBox', `0 0 ${this.width} ${this.height}`);
    
    if (this.simulation) {
      this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
      this.simulation.alpha(0.3).restart();
    }
  }

  destroy() {
    this.simulation?.stop();
    this.svg?.remove();
  }
}