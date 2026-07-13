import http from 'http';
import { URL } from 'url';
import { readFileSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = join(__filename, '..');

const PORT = 9749;
const DATA_FILE = join(__dirname, 'real_graph_data.json');

let cachedData = null;

function loadData() {
  try {
    const raw = readFileSync(DATA_FILE, 'utf-8');
    cachedData = JSON.parse(raw);
    console.log(`Loaded real graph: ${cachedData.metadata.nodeCount} nodes, ${cachedData.metadata.edgeCount} edges`);
  } catch (e) {
    console.error('Failed to load graph data:', e);
    cachedData = {
      metadata: { project: 'ARGUS', lastIndexed: new Date().toISOString(), nodeCount: 0, edgeCount: 0, modules: [], layers: [] },
      nodes: [],
      edges: []
    };
  }
}

loadData();

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  res.setHeader('Content-Type', 'application/json');

  if (url.pathname === '/api/status') {
    res.writeHead(200);
    res.end(JSON.stringify({
      status: 'ok',
      project: 'ARGUS',
      lastIndexed: cachedData?.metadata?.lastIndexed || new Date().toISOString(),
      indexedFiles: 61,
      nodes: cachedData?.metadata?.nodeCount || 0,
      edges: cachedData?.metadata?.edgeCount || 0,
      version: '1.0.0-real'
    }));
  } else if (url.pathname === '/api/graph') {
    const project = url.searchParams.get('project') || 'ARGUS';
    const limit = parseInt(url.searchParams.get('limit') || '5000');

    const nodes = (cachedData?.nodes || []).slice(0, limit);
    const edges = (cachedData?.edges || []).slice(0, limit);

    res.writeHead(200);
    res.end(JSON.stringify({
      metadata: { ...cachedData?.metadata, project },
      nodes,
      edges
    }));
  } else if (url.pathname === '/api/reload') {
    loadData();
    res.writeHead(200);
    res.end(JSON.stringify({ ok: true, message: 'Graph data reloaded' }));
  } else {
    res.writeHead(404);
    res.end(JSON.stringify({ error: 'Not found' }));
  }
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Real Graph API running on http://localhost:${PORT}`);
  console.log(`Endpoints:`);
  console.log(`  GET /api/status`);
  console.log(`  GET /api/graph?project=ARGUS&limit=5000`);
  console.log(`  POST /api/reload`);
});
