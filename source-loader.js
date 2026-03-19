// ============================================================================
// DEPRECATED — This file is kept for reference only.
// All source-loading logic has moved to python_backend/source_loader.py.
// Do NOT add new logic here.  This file will be removed in a future release.
// ============================================================================

// Legacy Node source-ingestion reference.
// The Python smart layer is now the primary source loading implementation for public entrypoints.

const fs = require('fs');
const path = require('path');
const mammoth = require('mammoth');
const pdfParse = require('pdf-parse');

const maxInlineChars = 12000;
const imageExtensions = new Set(['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg']);
const textExtensions = new Set(['.txt', '.md', '.markdown', '.csv', '.json', '.yaml', '.yml', '.xml', '.html', '.htm']);

function fail(message) {
  throw new Error(message);
}

function isUrl(value) {
  return /^https?:\/\//i.test(String(value || ''));
}

function resolveSourcePath(sourcePath, baseDir) {
  if (!sourcePath) {
    fail('Source path is required.');
  }
  return path.isAbsolute(sourcePath) ? sourcePath : path.resolve(baseDir, sourcePath);
}

function inferType(source) {
  if (source.type) {
    return String(source.type).toLowerCase();
  }

  if (source.url || isUrl(source.path)) {
    return 'url';
  }

  const extension = path.extname(source.path || '').toLowerCase();
  if (extension === '.pdf') {
    return 'pdf';
  }
  if (extension === '.docx') {
    return 'docx';
  }
  if (imageExtensions.has(extension)) {
    return 'image';
  }
  if (textExtensions.has(extension)) {
    return extension === '.json' ? 'json' : extension === '.html' || extension === '.htm' ? 'html' : 'text';
  }

  return 'text';
}

function trimText(text, maxChars = maxInlineChars) {
  const normalized = String(text || '').replace(/\r\n/g, '\n').trim();
  if (normalized.length <= maxChars) {
    return normalized;
  }
  return `${normalized.slice(0, maxChars)}\n\n[Truncated for planning]`;
}

function stripHtml(html) {
  return String(html || '')
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, ' ')
    .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/\s+/g, ' ')
    .trim();
}

function normalizeSource(input) {
  if (typeof input === 'string') {
    return isUrl(input) ? { url: input } : { path: input };
  }
  if (!input || typeof input !== 'object') {
    fail('Each source must be a string or an object.');
  }
  return { ...input };
}

async function readUrlSource(source) {
  const response = await fetch(source.url, {
    headers: {
      'User-Agent': 'auto-ppt-prototype/0.3.0'
    }
  });

  if (!response.ok) {
    fail(`Failed to fetch URL source ${source.url}: ${response.status}`);
  }

  const contentType = response.headers.get('content-type') || '';
  const rawBody = await response.text();
  const text = contentType.includes('html') ? stripHtml(rawBody) : rawBody;

  return {
    location: source.url,
    label: source.label || source.url,
    type: 'url',
    text: trimText(text),
    trustLevel: source.trustLevel || 'external',
    priority: source.priority || 'normal',
    notes: source.notes || ''
  };
}

async function readFileSource(source, baseDir) {
  const absolutePath = resolveSourcePath(source.path, baseDir);
  if (!fs.existsSync(absolutePath)) {
    fail(`Source file not found: ${absolutePath}`);
  }

  const type = inferType({ ...source, path: absolutePath });
  const extension = path.extname(absolutePath).toLowerCase();
  const label = source.label || path.basename(absolutePath);
  const trustLevel = source.trustLevel || 'user-provided';
  const priority = source.priority || 'high';
  let text = '';

  if (type === 'pdf') {
    const buffer = fs.readFileSync(absolutePath);
    const parsed = await pdfParse(buffer);
    text = parsed.text || '';
  } else if (type === 'docx') {
    const result = await mammoth.extractRawText({ path: absolutePath });
    text = result.value || '';
  } else if (type === 'html') {
    text = stripHtml(fs.readFileSync(absolutePath, 'utf8'));
  } else if (type === 'image' || imageExtensions.has(extension)) {
    text = `Image asset reference: ${path.basename(absolutePath)}. OCR or visual analysis is not performed by this repository. The upstream agent should analyze the image and provide extracted findings as additional context.`;
  } else {
    text = fs.readFileSync(absolutePath, 'utf8');
  }

  return {
    location: absolutePath,
    label,
    type,
    text: trimText(text),
    trustLevel,
    priority,
    notes: source.notes || ''
  };
}

function buildSourceContext(source) {
  const parts = [
    `Source label: ${source.label}`,
    `Source type: ${source.type}`,
    `Source location: ${source.location}`,
    `Source trust level: ${source.trustLevel}`,
    `Source priority: ${source.priority}`
  ];

  if (source.notes) {
    parts.push(`Source notes: ${source.notes}`);
  }

  parts.push('Source content:');
  parts.push(source.text || '[No extractable text]');
  return parts.join('\n');
}

async function loadSourceContexts(sources = [], options = {}) {
  const baseDir = options.baseDir || process.cwd();
  const normalizedSources = Array.isArray(sources) ? sources.map(normalizeSource) : [];
  const loaded = [];

  for (const source of normalizedSources) {
    const loadedSource = source.url || isUrl(source.path)
      ? await readUrlSource(source.url ? source : { ...source, url: source.path })
      : await readFileSource(source, baseDir);
    loaded.push(loadedSource);
  }

  return {
    loadedSources: loaded,
    contextTexts: loaded.map(buildSourceContext)
  };
}

module.exports = {
  loadSourceContexts,
  inferType,
  buildSourceContext
};
