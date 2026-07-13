import http from 'http';
import { URL } from 'url';

// Mock graph data for ARGUS project
const mockGraphData = {
  metadata: {
    project: 'ARGUS',
    lastIndexed: new Date().toISOString(),
    nodeCount: 42,
    edgeCount: 67,
    modules: ['argus', 'vision', 'graph', 'cli', 'analytics', 'routing', 'simulation', 'dashboard']
  },
  nodes: [
    // Core module
    { id: 'argus-core', label: 'argus.core', type: 'module', module: 'argus', layer: 'core', x: 0, y: 0, size: 20 },
    { id: 'argus-config', label: 'argus.config', type: 'config', module: 'argus', layer: 'core', x: -50, y: 30, size: 12 },
    { id: 'argus-cli', label: 'argus.cli', type: 'cli', module: 'argus', layer: 'api', x: 50, y: -30, size: 15 },
    { id: 'argus-main', label: 'argus.__main__', type: 'script', module: 'argus', layer: 'api', x: 80, y: -50, size: 10 },
    
    // Vision module
    { id: 'vision-core', label: 'vision.core', type: 'module', module: 'vision', layer: 'core', x: 150, y: 100, size: 18 },
    { id: 'vision-segment', label: 'vision.segment', type: 'class', module: 'vision', layer: 'core', x: 120, y: 140, size: 14 },
    { id: 'vision-extract', label: 'vision.extract', type: 'function', module: 'vision', layer: 'core', x: 180, y: 140, size: 10 },
    { id: 'vision-raster', label: 'vision.raster', type: 'protocol', module: 'vision', layer: 'core', x: 150, y: 180, size: 12 },
    
    // Graph module
    { id: 'graph-core', label: 'graph.core', type: 'module', module: 'graph', layer: 'core', x: -150, y: 100, size: 18 },
    { id: 'graph-build', label: 'graph.build', type: 'class', module: 'graph', layer: 'core', x: -180, y: 140, size: 14 },
    { id: 'graph-sknw', label: 'graph.sknw', type: 'protocol', module: 'graph', layer: 'core', x: -120, y: 140, size: 12 },
    { id: 'graph-export', label: 'graph.export', type: 'function', module: 'graph', layer: 'api', x: -150, y: 180, size: 10 },
    
    // Analytics module
    { id: 'analytics-core', label: 'analytics.core', type: 'module', module: 'analytics', layer: 'core', x: 0, y: -120, size: 16 },
    { id: 'analytics-criticality', label: 'analytics.criticality', type: 'class', module: 'analytics', layer: 'core', x: -40, y: -160, size: 12 },
    { id: 'analytics-centrality', label: 'analytics.centrality', type: 'function', module: 'analytics', layer: 'core', x: 40, y: -160, size: 10 },
    
    // Routing module
    { id: 'routing-core', label: 'routing.core', type: 'module', module: 'routing', layer: 'core', x: -100, y: -80, size: 14 },
    { id: 'routing-dijkstra', label: 'routing.dijkstra', type: 'function', module: 'routing', layer: 'core', x: -140, y: -120, size: 10 },
    { id: 'routing-astar', label: 'routing.astar', type: 'function', module: 'routing', layer: 'core', x: -60, y: -120, size: 10 },
    
    // Simulation module
    { id: 'simulation-core', label: 'simulation.core', type: 'module', module: 'simulation', layer: 'data', x: 100, y: -80, size: 14 },
    { id: 'simulation-engine', label: 'simulation.engine', type: 'class', module: 'simulation', layer: 'data', x: 140, y: -120, size: 11 },
    { id: 'simulation-scenario', label: 'simulation.scenario', type: 'protocol', module: 'simulation', layer: 'data', x: 60, y: -120, size: 11 },
    
    // Dashboard module
    { id: 'dashboard-core', label: 'dashboard.core', type: 'module', module: 'dashboard', layer: 'dashboard', x: 200, y: 0, size: 16 },
    { id: 'dashboard-panel', label: 'dashboard.panel', type: 'class', module: 'dashboard', layer: 'dashboard', x: 240, y: 40, size: 12 },
    { id: 'dashboard-store', label: 'dashboard.store', type: 'file', module: 'dashboard', layer: 'dashboard', x: 260, y: 0, size: 10 },
    
    // Test files
    { id: 'test-vision', label: 'test_vision.py', type: 'test', module: 'vision', layer: 'core', x: 180, y: 220, size: 8 },
    { id: 'test-graph', label: 'test_graph.py', type: 'test', module: 'graph', layer: 'core', x: -150, y: 220, size: 8 },
    { id: 'test-analytics', label: 'test_analytics.py', type: 'test', module: 'analytics', layer: 'core', x: 0, y: -200, size: 8 },
  ],
  edges: [
    // Core dependencies
    { source: 'argus-core', target: 'argus-config', type: 'contains' },
    { source: 'argus-core', target: 'argus-cli', type: 'contains' },
    { source: 'argus-core', target: 'argus-main', type: 'contains' },
    { source: 'argus-cli', target: 'argus-main', type: 'calls' },
    
    // Vision module internal
    { source: 'vision-core', target: 'vision-segment', type: 'contains' },
    { source: 'vision-core', target: 'vision-extract', type: 'contains' },
    { source: 'vision-core', target: 'vision-raster', type: 'contains' },
    { source: 'vision-segment', target: 'vision-extract', type: 'calls' },
    
    // Graph module internal
    { source: 'graph-core', target: 'graph-build', type: 'contains' },
    { source: 'graph-core', target: 'graph-sknw', type: 'contains' },
    { source: 'graph-core', target: 'graph-export', type: 'contains' },
    { source: 'graph-build', target: 'graph-sknw', type: 'implements' },
    
    // Analytics internal
    { source: 'analytics-core', target: 'analytics-criticality', type: 'contains' },
    { source: 'analytics-core', target: 'analytics-centrality', type: 'contains' },
    
    // Routing internal
    { source: 'routing-core', target: 'routing-dijkstra', type: 'contains' },
    { source: 'routing-core', target: 'routing-astar', type: 'contains' },
    
    // Simulation internal
    { source: 'simulation-core', target: 'simulation-engine', type: 'contains' },
    { source: 'simulation-core', target: 'simulation-scenario', type: 'contains' },
    
    // Dashboard internal
    { source: 'dashboard-core', target: 'dashboard-panel', type: 'contains' },
    { source: 'dashboard-core', target: 'dashboard-store', type: 'contains' },
    
    // Cross-module dependencies
    { source: 'vision-core', target: 'graph-core', type: 'depends_on' },
    { source: 'analytics-core', target: 'graph-core', type: 'depends_on' },
    { source: 'routing-core', target: 'graph-core', type: 'depends_on' },
    { source: 'simulation-core', target: 'graph-core', type: 'depends_on' },
    { source: 'dashboard-core', target: 'graph-core', type: 'depends_on' },
    { source: 'dashboard-core', target: 'analytics-core', type: 'depends_on' },
    { source: 'dashboard-core', target: 'routing-core', type: 'depends_on' },
    { source: 'simulation-core', target: 'analytics-core', type: 'depends_on' },
    
    // CLI imports
    { source: 'argus-cli', target: 'vision-core', type: 'imports' },
    { source: 'argus-cli', target: 'graph-core', type: 'imports' },
    { source: 'argus-cli', target: 'analytics-core', type: 'imports' },
    { source: 'argus-cli', target: 'routing-core', type: 'imports' },
    { source: 'argus-cli', target: 'simulation-core', type: 'imports' },
    { source: 'argus-cli', target: 'dashboard-core', type: 'imports' },
    
    // Tests
    { source: 'test-vision', target: 'vision-core', type: 'test_of' },
    { source: 'test-graph', target: 'graph-core', type: 'test_of' },
    { source: 'test-analytics', target: 'analytics-core', type: 'test_of' },
  ]
};

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://localhost:9749`);
  
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }
  
  if (url.pathname === '/api/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok',
      project: 'ARGUS',
      lastIndexed: new Date().toISOString(),
      indexedFiles: 42,
      nodes: mockGraphData.nodes.length,
      edges: mockGraphData.edges.length,
      version: '1.0.0'
    }));
  } else if (url.pathname === '/api/graph') {
    const project = url.searchParams.get('project') || 'ARGUS';
    const limit = parseInt(url.searchParams.get('limit') || '5000');
    
    const nodes = mockGraphData.nodes.slice(0, limit);
    const edges = mockGraphData.edges.slice(0, limit);
    
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      metadata: { ...mockGraphData.metadata, project },
      nodes,
      edges
    }));
  } else {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not found' }));
  }
});

server.listen(9749, '0.0.0.0', () => {
  console.log('Mock Codebase Memory API running on http://localhost:9749');
  console.log('Endpoints:');
  console.log('  GET /api/status');
  console.log('  GET /api/graph?project=ARGUS&limit=5000');
});