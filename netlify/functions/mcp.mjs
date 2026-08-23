// MCP endpoint (POA W4.3) — the reference dataset as a queryable tool server.
//
// JSON-RPC 2.0 over HTTP POST at /mcp (Streamable HTTP transport, stateless).
// Tools: get_entity, search_entities, list_changes. Data comes from the
// site's own static exports (entities.json, changes.json), fetched once per
// warm instance — the function adds a protocol, never a second source of truth.

const PROTOCOL = '2025-06-18';
const cache = { data: null, changes: null, at: 0 };
const TTL_MS = 5 * 60 * 1000;

async function corpus(origin) {
  const now = Date.now();
  if (!cache.data || now - cache.at > TTL_MS) {
    const [d, c] = await Promise.all([
      fetch(`${origin}/entities.json`).then(r => r.json()),
      fetch(`${origin}/changes.json`).then(r => (r.ok ? r.json() : { events: [] })),
    ]);
    cache.data = d;
    cache.changes = c;
    cache.at = now;
  }
  return cache;
}

const TOOLS = [
  {
    name: 'get_entity',
    description:
      'Fetch one entity from the reference by slug: current status, claim, coordinates, last_verified date and full primary-source list.',
    inputSchema: {
      type: 'object',
      properties: { slug: { type: 'string', description: 'Entity slug, e.g. dxb-vertiport' } },
      required: ['slug'],
    },
  },
  {
    name: 'search_entities',
    description:
      'Search entities by free text (name, claim), optionally filtered by entity_type (aircraft, operator, vertiport, route, regulator, answer) and/or status.',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Free-text match against name and claim; empty matches all' },
        entity_type: { type: 'string' },
        status: { type: 'string' },
      },
    },
  },
  {
    name: 'list_changes',
    description:
      'The fact-change log: every entity addition and status transition in the reference, dated, newest first.',
    inputSchema: { type: 'object', properties: {} },
  },
];

function text(result) {
  return { content: [{ type: 'text', text: JSON.stringify(result, null, 1) }] };
}

async function callTool(name, args, origin) {
  const { data, changes } = await corpus(origin);
  const ents = data.entities;
  if (name === 'get_entity') {
    const e = ents.find(x => x.slug === (args?.slug || ''));
    if (!e) {
      return {
        ...text({ error: `no entity with slug '${args?.slug}'`, known_slugs: ents.map(x => x.slug) }),
        isError: true,
      };
    }
    return text(e);
  }
  if (name === 'search_entities') {
    const q = (args?.query || '').toLowerCase();
    const hits = ents.filter(
      e =>
        (!args?.entity_type || e.entity_type === args.entity_type) &&
        (!args?.status || e.status === args.status) &&
        (!q || `${e.name} ${e.meta_description}`.toLowerCase().includes(q)),
    );
    return text(
      hits.map(e => ({
        slug: e.slug,
        name: e.name,
        entity_type: e.entity_type,
        status: e.status,
        last_verified: e.last_verified,
        claim: e.meta_description,
      })),
    );
  }
  if (name === 'list_changes') return text(changes.events);
  return { ...text({ error: `unknown tool '${name}'` }), isError: true };
}

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Accept, Mcp-Session-Id, MCP-Protocol-Version',
};

export default async function handler(req) {
  const origin = new URL(req.url).origin;
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
  if (req.method === 'GET') {
    return Response.json(
      {
        name: `${new URL(req.url).host} MCP server`,
        transport: 'streamable-http',
        protocolVersion: PROTOCOL,
        usage: 'POST JSON-RPC 2.0 (initialize, tools/list, tools/call)',
        tools: TOOLS.map(t => t.name),
        data: `${origin}/data.html`,
        license: 'CC BY 4.0',
      },
      { headers: CORS },
    );
  }
  if (req.method !== 'POST') return new Response('method not allowed', { status: 405, headers: CORS });

  let rpc;
  try {
    rpc = await req.json();
  } catch {
    return Response.json(
      { jsonrpc: '2.0', id: null, error: { code: -32700, message: 'parse error' } },
      { status: 400, headers: CORS },
    );
  }
  const reply = result =>
    Response.json({ jsonrpc: '2.0', id: rpc.id ?? null, result }, { headers: CORS });

  try {
    switch (rpc.method) {
      case 'initialize':
        return reply({
          protocolVersion: PROTOCOL,
          capabilities: { tools: {} },
          serverInfo: { name: new URL(req.url).host, version: '1.0.0' },
          instructions:
            'Primary-source eVTOL reference. Every record carries last_verified and its sources; attribution (CC BY 4.0) is the only condition of use.',
        });
      case 'notifications/initialized':
      case 'ping':
        return rpc.id === undefined ? new Response(null, { status: 202, headers: CORS }) : reply({});
      case 'tools/list':
        return reply({ tools: TOOLS });
      case 'tools/call':
        return reply(await callTool(rpc.params?.name, rpc.params?.arguments, origin));
      default:
        return Response.json(
          { jsonrpc: '2.0', id: rpc.id ?? null, error: { code: -32601, message: `method not found: ${rpc.method}` } },
          { headers: CORS },
        );
    }
  } catch (err) {
    return Response.json(
      { jsonrpc: '2.0', id: rpc.id ?? null, error: { code: -32603, message: String(err) } },
      { status: 500, headers: CORS },
    );
  }
}

export const config = { path: '/mcp' };
