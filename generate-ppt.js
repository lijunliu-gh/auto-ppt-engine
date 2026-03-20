const fs = require('fs');
const path = require('path');
const PptxGenJS = require('pptxgenjs');

// Optional: chartjs-node-canvas for cross-platform chart images (Keynote/Google Slides compat)
let ChartJSNodeCanvas = null;
try {
  ChartJSNodeCanvas = require('chartjs-node-canvas').ChartJSNodeCanvas;
} catch (_) {
  // chartjs-node-canvas not installed — will use native PPT charts
}

// ---------------------------------------------------------------------------
// Theme system
// ---------------------------------------------------------------------------

const DEFAULT_THEME = {
  name: 'business-clean',
  colors: {
    primary:    '0F766E',
    secondary:  '2563EB',
    accent:     'F59E0B',
    background: 'F8FAFC',
    slideBg:    'FFFFFF',
    text:       '1F2937',
    textLight:  'F8FAFC',
    textMuted:  '475569',
    headerBg:   'E2E8F0',
    border:     'CBD5E1',
    closingBg:  '0F172A',
    titleBg:    'F8FAFC',
  },
  fonts: {
    heading: 'Aptos Display, Microsoft YaHei, PingFang SC, Meiryo, Noto Sans CJK SC',
    body:    'Aptos, Microsoft YaHei, PingFang SC, Meiryo, Noto Sans CJK SC',
  },
  chartColors: ['0F766E', '2563EB', 'F59E0B', 'DC2626', '7C3AED', '059669'],
};

/**
 * Resolve the theme for this deck. Priority:
 * 1. deck._theme object (injected by Python backend from template or built-in theme)
 * 2. Built-in theme file matching deck.theme name
 * 3. DEFAULT_THEME
 */
function resolveTheme(deck) {
  if (deck._theme && typeof deck._theme === 'object' && deck._theme.colors) {
    // Merge with defaults to fill any missing fields
    return mergeTheme(deck._theme);
  }

  // Try loading a built-in theme file
  const themeName = deck.theme || 'business-clean';
  const themePath = path.join(__dirname, 'assets', 'themes', `${themeName}.json`);
  if (fs.existsSync(themePath)) {
    try {
      const loaded = JSON.parse(fs.readFileSync(themePath, 'utf8'));
      return mergeTheme(loaded);
    } catch (_) { /* fall through */ }
  }

  return { ...DEFAULT_THEME };
}

function mergeTheme(partial) {
  return {
    name: partial.name || DEFAULT_THEME.name,
    colors: { ...DEFAULT_THEME.colors, ...partial.colors },
    fonts: { ...DEFAULT_THEME.fonts, ...partial.fonts },
    chartColors: Array.isArray(partial.chartColors) && partial.chartColors.length >= 2
      ? partial.chartColors
      : DEFAULT_THEME.chartColors,
  };
}

// Active theme — set at the start of buildDeck(), used by all render helpers
let _t = DEFAULT_THEME;

const allowedLayouts = new Set([
  'title',
  'agenda',
  'section',
  'bullet',
  'two-column',
  'comparison',
  'timeline',
  'process',
  'table',
  'chart',
  'quote',
  'summary',
  'closing'
]);

function fail(message) {
  console.error(`Error: ${message}`);
  process.exit(1);
}

function readDeck(inputPath) {
  if (!fs.existsSync(inputPath)) {
    fail(`Input file not found: ${inputPath}`);
  }

  try {
    return JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  } catch (error) {
    fail(`Invalid JSON in ${inputPath}: ${error.message}`);
  }
}

function validateDeck(deck) {
  if (!deck || typeof deck !== 'object') {
    fail('Deck must be a JSON object.');
  }

  if (!deck.deckTitle || typeof deck.deckTitle !== 'string') {
    fail('deckTitle is required.');
  }

  if (!Array.isArray(deck.slides) || deck.slides.length === 0) {
    fail('slides must be a non-empty array.');
  }

  if (deck.sourceDisplayMode && !['hidden', 'notes', 'footnote', 'appendix'].includes(deck.sourceDisplayMode)) {
    fail(`sourceDisplayMode is not supported: ${deck.sourceDisplayMode}`);
  }

  if (deck.slideCount !== deck.slides.length) {
    fail(`slideCount must equal slides.length (${deck.slides.length}).`);
  }

  deck.slides.forEach((slide, index) => {
    if (slide.page !== index + 1) {
      fail(`slides[${index}].page must be ${index + 1}.`);
    }

    if (!allowedLayouts.has(slide.layout)) {
      fail(`slides[${index}].layout is not supported: ${slide.layout}`);
    }

    if (!slide.title || typeof slide.title !== 'string') {
      fail(`slides[${index}].title is required.`);
    }

    if (!Array.isArray(slide.sources)) {
      fail(`slides[${index}].sources must be an array.`);
    }
  });
}

function ensureOutputDir(outputPath) {
  const outputDir = path.dirname(outputPath);
  fs.mkdirSync(outputDir, { recursive: true });
}

function addTextBox(slide, text, options = {}) {
  if (!text) {
    return;
  }

  slide.addText(text, {
    fontFace: _t.fonts.body,
    color: _t.colors.text,
    margin: 0.08,
    breakLine: true,
    shrinkText: true,
    ...options
  });
}

function addSlideHeader(slide, deck, current) {
  addTextBox(slide, current.title, {
    x: 0.6,
    y: 0.35,
    w: 8.3,
    h: 0.5,
    fontSize: 24,
    bold: true,
    color: _t.colors.closingBg
  });

  if (current.objective) {
    addTextBox(slide, current.objective, {
      x: 0.6,
      y: 0.88,
      w: 8.5,
      h: 0.35,
      fontSize: 10,
      color: _t.colors.textMuted,
      italic: true
    });
  }

  addTextBox(slide, deck.deckTitle, {
    x: 10.3,
    y: 0.36,
    w: 2.3,
    h: 0.25,
    fontSize: 9,
    align: 'right',
    color: _t.colors.textMuted
  });

  slide.addShape('line', {
    x: 0.6,
    y: 1.28,
    w: 12.1,
    h: 0,
    line: { color: _t.colors.border, pt: 1.2 }
  });
}

function addFooter(slide, page) {
  addTextBox(slide, String(page), {
    x: 12.3,
    y: 7.02,
    w: 0.35,
    h: 0.2,
    fontSize: 9,
    align: 'right',
    color: _t.colors.textMuted
  });
}

function formatSourceNotes(sources) {
  if (!Array.isArray(sources) || sources.length === 0) {
    return [];
  }

  return ['Sources:'].concat(
    sources.map((source, index) => {
      const parts = [
        `[${index + 1}] ${source.label || 'Source'}`,
        source.location || '',
        source.citation ? `Citation: ${source.citation}` : '',
        source.notes ? `Note: ${source.notes}` : ''
      ].filter(Boolean);

      return parts.join(' | ');
    })
  );
}

function addBulletList(slide, bullets, area) {
  const items = Array.isArray(bullets) ? bullets.filter(Boolean) : [];
  if (items.length === 0) {
    return;
  }

  slide.addText(
    items.map((item) => ({ text: item, options: { bullet: { indent: 14 }, ...(area.color ? { color: area.color } : {}) } })),
    {
      x: area.x,
      y: area.y,
      w: area.w,
      h: area.h,
      fontFace: _t.fonts.body,
      fontSize: area.fontSize || 18,
      color: area.color || _t.colors.text,
      valign: 'top',
      paraSpaceAfterPt: 10,
      breakLine: true,
      shrinkText: true
    }
  );
}

function addLabel(slide, text, x, y, w) {
  addTextBox(slide, text, {
    x,
    y,
    w,
    h: 0.25,
    fontSize: 11,
    bold: true,
    color: _t.colors.textMuted
  });
}

function renderTitleSlide(slide, deck, current) {
  slide.background = { color: _t.colors.titleBg };
  slide.addShape('rect', {
    x: 0,
    y: 0,
    w: 13.333,
    h: 7.5,
    fill: { color: _t.colors.headerBg, transparency: 70 },
    line: { color: _t.colors.headerBg, transparency: 100 }
  });
  slide.addShape('rect', {
    x: 0.6,
    y: 0.9,
    w: 0.18,
    h: 4.8,
    fill: { color: _t.colors.primary },
    line: { color: _t.colors.primary, transparency: 100 }
  });

  addTextBox(slide, current.title, {
    x: 1.0,
    y: 1.1,
    w: 8.8,
    h: 1.1,
    fontSize: 28,
    bold: true,
    color: _t.colors.closingBg
  });

  addTextBox(slide, current.subtitle || deck.scenario || deck.audience || '', {
    x: 1.02,
    y: 2.35,
    w: 7.4,
    h: 0.5,
    fontSize: 16,
    color: _t.colors.textMuted
  });

  const metaLines = [
    deck.audience ? `Audience: ${deck.audience}` : '',
    deck.scenario ? `Scenario: ${deck.scenario}` : '',
    deck.tone ? `Tone: ${deck.tone}` : ''
  ].filter(Boolean);

  addTextBox(slide, metaLines.join('\n'), {
    x: 1.02,
    y: 4.9,
    w: 4.2,
    h: 1.2,
    fontSize: 12,
    color: _t.colors.textMuted
  });
}

function renderAgendaSlide(slide, deck, current) {
  addSlideHeader(slide, deck, current);
  const agendaItems = (current.bullets || []).map((item, index) => `${index + 1}. ${item}`);
  addBulletList(slide, agendaItems, { x: 0.95, y: 1.7, w: 7.8, h: 4.8, fontSize: 20 });
}

const VISUAL_POSITION_PRESETS = {
  right:  { x: 8.95, y: 1.65, w: 3.35, h: 4.0 },
  left:   { x: 0.6,  y: 1.65, w: 4.5,  h: 4.0 },
  center: { x: 3.5,  y: 1.8,  w: 6.33, h: 4.5 },
  full:   { x: 0.5,  y: 1.4,  w: 12.33, h: 5.8 },
};

const SUPPORTED_IMAGE_EXTS = new Set([
  '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.svg', '.webp'
]);

function classifyVisual(item) {
  if (typeof item === 'string') {
    const lower = item.trim().toLowerCase();
    if (SUPPORTED_IMAGE_EXTS.has(path.extname(lower))) {
      return { kind: 'image', path: item, position: 'right' };
    }
    return { kind: 'description', text: item };
  }
  if (item && typeof item === 'object') {
    if (item.type === 'image') {
      return { kind: 'image', path: item.path || null, url: item.url || null, alt: item.alt || '', position: item.position || 'right' };
    }
    if (item.type === 'placeholder') {
      return { kind: 'placeholder', prompt: item.prompt || '', alt: item.alt || '', position: item.position || 'right' };
    }
  }
  return { kind: 'description', text: String(item) };
}

function getVisualPosition(visual) {
  return VISUAL_POSITION_PRESETS[visual.position] || VISUAL_POSITION_PRESETS.right;
}

function renderVisualsOnSlide(slide, visuals) {
  const descriptions = [];
  const images = [];
  const placeholders = [];

  for (const item of visuals) {
    const classified = classifyVisual(item);
    if (classified.kind === 'description') descriptions.push(classified);
    else if (classified.kind === 'image') images.push(classified);
    else if (classified.kind === 'placeholder') placeholders.push(classified);
  }

  let insertedAny = false;

  // Insert local images (PptxGenJS supports path-based insertion)
  for (const img of images) {
    const imgPath = img.path;
    if (imgPath && fs.existsSync(imgPath)) {
      const pos = getVisualPosition(img);
      slide.addImage({ path: imgPath, x: pos.x, y: pos.y, w: pos.w, h: pos.h });
      insertedAny = true;
    } else {
      descriptions.push({ kind: 'description', text: `[Image: ${img.alt || img.path || img.url || 'Unknown'}]` });
    }
  }

  // Render placeholders as labeled boxes
  for (const ph of placeholders) {
    const pos = getVisualPosition(ph);
    slide.addShape('roundRect', {
      x: pos.x, y: pos.y, w: pos.w, h: pos.h,
      rectRadius: 0.05,
      fill: { color: _t.colors.background },
      line: { color: _t.colors.border, pt: 1 }
    });
    addTextBox(slide, `🖼 ${ph.prompt || 'Image placeholder'}`, {
      x: pos.x + 0.15, y: pos.y + 0.15, w: pos.w - 0.3, h: pos.h - 0.3,
      fontSize: 11, italic: true, color: _t.colors.textMuted
    });
  }

  // Show text descriptions as suggestion box (only if no images were inserted)
  const descTexts = descriptions.map(d => d.text).filter(Boolean);
  if (descTexts.length > 0 && !insertedAny) {
    slide.addShape('roundRect', {
      x: 8.95, y: 1.65, w: 3.35, h: 3.2,
      rectRadius: 0.08,
      fill: { color: _t.colors.background },
      line: { color: _t.colors.border, pt: 1 }
    });
    addLabel(slide, 'Visual Suggestions', 9.2, 1.92, 2.7);
    addBulletList(slide, descTexts, { x: 9.08, y: 2.25, w: 2.9, h: 2.2, fontSize: 12 });
  }
}

function renderBulletSlide(slide, deck, current) {
  addSlideHeader(slide, deck, current);
  addBulletList(slide, current.bullets, { x: 0.9, y: 1.72, w: 7.5, h: 4.9, fontSize: 20 });

  if (Array.isArray(current.visuals) && current.visuals.length > 0) {
    renderVisualsOnSlide(slide, current.visuals);
  }
}

function renderTwoColumnSlide(slide, deck, current) {
  addSlideHeader(slide, deck, current);
  addLabel(slide, 'Left', 0.9, 1.55, 4.8);
  addLabel(slide, 'Right', 6.8, 1.55, 4.8);

  slide.addShape('line', {
    x: 6.45,
    y: 1.75,
    w: 0,
    h: 4.65,
    line: { color: _t.colors.border, pt: 1.1 }
  });

  addBulletList(slide, current.left, { x: 0.9, y: 1.9, w: 5.1, h: 4.8, fontSize: 18 });
  addBulletList(slide, current.right, { x: 6.8, y: 1.9, w: 5.1, h: 4.8, fontSize: 18 });
}

function renderComparisonSlide(slide, deck, current) {
  addSlideHeader(slide, deck, current);

  slide.addShape('roundRect', {
    x: 0.85,
    y: 1.7,
    w: 5.45,
    h: 4.7,
    rectRadius: 0.05,
    fill: { color: _t.colors.background },
    line: { color: _t.colors.border, pt: 1 }
  });
  slide.addShape('roundRect', {
    x: 6.95,
    y: 1.7,
    w: 5.45,
    h: 4.7,
    rectRadius: 0.05,
    fill: { color: _t.colors.background },
    line: { color: _t.colors.border, pt: 1 }
  });

  addLabel(slide, 'Option A', 1.1, 2.0, 4.5);
  addLabel(slide, 'Option B', 7.2, 2.0, 4.5);
  addBulletList(slide, current.left, { x: 1.0, y: 2.35, w: 4.9, h: 3.7, fontSize: 16 });
  addBulletList(slide, current.right, { x: 7.1, y: 2.35, w: 4.9, h: 3.7, fontSize: 16 });
}

function renderTimelineSlide(slide, deck, current) {
  addSlideHeader(slide, deck, current);
  const milestones = (current.bullets || []).slice(0, 5);
  const startX = 1.1;
  const totalWidth = 10.8;
  const gap = milestones.length > 1 ? totalWidth / (milestones.length - 1) : 0;

  slide.addShape('line', {
    x: startX,
    y: 3.65,
    w: totalWidth,
    h: 0,
    line: { color: _t.colors.border, pt: 1.4 }
  });

  milestones.forEach((item, index) => {
    const x = startX + gap * index;
    slide.addShape('ellipse', {
      x: x - 0.16,
      y: 3.48,
      w: 0.32,
      h: 0.32,
      fill: { color: _t.colors.primary },
      line: { color: _t.colors.primary, transparency: 100 }
    });

    addTextBox(slide, `Phase ${index + 1}`, {
      x: x - 0.45,
      y: 2.82,
      w: 0.9,
      h: 0.25,
      fontSize: 10,
      align: 'center',
      bold: true,
      color: _t.colors.closingBg
    });

    addTextBox(slide, item, {
      x: x - 0.85,
      y: 3.95,
      w: 1.7,
      h: 1.0,
      fontSize: 11,
      align: 'center',
      color: _t.colors.textMuted
    });
  });
}

function renderProcessSlide(slide, deck, current) {
  addSlideHeader(slide, deck, current);
  const steps = (current.bullets || []).slice(0, 4);
  const width = 2.7;

  steps.forEach((item, index) => {
    const x = 0.9 + index * 3.0;
    slide.addShape('roundRect', {
      x,
      y: 2.2,
      w: width,
      h: 1.6,
      rectRadius: 0.05,
      fill: { color: index % 2 === 0 ? 'ECFDF5' : 'EFF6FF' },
      line: { color: _t.colors.border, pt: 1 }
    });

    addTextBox(slide, `${index + 1}`, {
      x: x + 0.15,
      y: 2.35,
      w: 0.3,
      h: 0.3,
      fontSize: 12,
      bold: true,
      color: _t.colors.primary
    });

    addTextBox(slide, item, {
      x: x + 0.25,
      y: 2.68,
      w: 2.15,
      h: 0.85,
      fontSize: 15,
      bold: true,
      color: _t.colors.text,
      align: 'center',
      valign: 'mid'
    });

    if (index < steps.length - 1) {
      slide.addShape('chevron', {
        x: x + 2.72,
        y: 2.72,
        w: 0.4,
        h: 0.55,
        fill: { color: _t.colors.border },
        line: { color: _t.colors.border, transparency: 100 }
      });
    }
  });
}

function renderTableSlide(slide, deck, current) {
  addSlideHeader(slide, deck, current);
  const columns = current.table && Array.isArray(current.table.columns) ? current.table.columns : [];
  const rows = current.table && Array.isArray(current.table.rows) ? current.table.rows : [];
  if (columns.length === 0) {
    addTextBox(slide, 'No table data supplied.', {
      x: 0.95,
      y: 2.0,
      w: 4.5,
      h: 0.35,
      fontSize: 18,
      color: 'B91C1C'
    });
    return;
  }

  slide.addTable([columns, ...rows], {
    x: 0.9,
    y: 1.8,
    w: 11.6,
    h: 4.8,
    border: { type: 'solid', color: _t.colors.border, pt: 1 },
    fill: _t.colors.slideBg,
    fontFace: _t.fonts.body,
    fontSize: 13,
    color: _t.colors.text,
    bold: false,
    rowH: 0.42,
    autoFit: true,
    margin: 0.05,
    valign: 'mid',
    align: 'left',
    fillHeader: _t.colors.headerBg,
    boldHeader: true
  });
}

function toChartType(type) {
  switch ((type || '').toLowerCase()) {
    case 'bar':
      return 'bar';
    case 'line':
      return 'line';
    case 'pie':
      return 'pie';
    case 'area':
      return 'area';
    default:
      return 'bar';
  }
}

// Convert chart type to chart.js type name
function toChartJsType(type) {
  const t = (type || '').toLowerCase();
  if (t === 'area') return 'line'; // area = line with fill
  if (['bar', 'line', 'pie'].includes(t)) return t;
  return 'bar';
}

/**
 * Render chart to PNG buffer using chart.js (cross-platform compatible).
 * Returns base64 string or null if chartjs-node-canvas unavailable.
 */
function renderChartImage(chart, categories, series) {
  if (!ChartJSNodeCanvas) return null;

  const chartType = toChartJsType(chart.type);
  const isArea = (chart.type || '').toLowerCase() === 'area';

  const chartCssColors = _t.chartColors.map(c => `#${c}`);

  const canvas = new ChartJSNodeCanvas({ width: 960, height: 540, backgroundColour: '#FFFFFF' });
  const datasets = series.map((entry, i) => ({
    label: entry.name,
    data: entry.data,
    backgroundColor: chartType === 'pie'
      ? chartCssColors.slice(0, categories.length)
      : chartCssColors[i % chartCssColors.length] + '99',
    borderColor: chartCssColors[i % chartCssColors.length],
    borderWidth: chartType === 'pie' ? 1 : 2,
    fill: isArea
  }));

  const config = {
    type: chartType,
    data: { labels: categories, datasets },
    options: {
      responsive: false,
      plugins: {
        title: { display: !!chart.title, text: chart.title || '', font: { size: 16 } },
        legend: { display: series.length > 1 || chartType === 'pie', position: 'bottom' }
      },
      scales: chartType === 'pie' ? {} : {
        x: { ticks: { font: { size: 12 } } },
        y: { ticks: { font: { size: 12 } }, beginAtZero: true }
      }
    }
  };

  const buffer = canvas.renderToBufferSync(config);
  return buffer.toString('base64');
}

function renderChartSlide(slide, deck, current) {
  addSlideHeader(slide, deck, current);
  const chart = current.chart || {};
  const categories = Array.isArray(chart.categories) ? chart.categories : [];
  const series = Array.isArray(chart.series) ? chart.series : [];

  if (categories.length === 0 || series.length === 0) {
    slide.addShape('roundRect', {
      x: 1.0,
      y: 1.9,
      w: 11.2,
      h: 3.8,
      rectRadius: 0.06,
      fill: { color: _t.colors.background },
      line: { color: _t.colors.border, pt: 1 }
    });
    addTextBox(slide, chart.title || 'Chart Placeholder', {
      x: 1.3,
      y: 2.25,
      w: 4.0,
      h: 0.35,
      fontSize: 18,
      bold: true,
      color: _t.colors.text
    });
    addBulletList(slide, current.visuals || ['Provide categories and series data to render a real chart.'], {
      x: 1.3,
      y: 2.8,
      w: 9.4,
      h: 2.2,
      fontSize: 16
    });
    return;
  }

  // Try image-based rendering first (Keynote/Google Slides compatible)
  const useNativeCharts = deck._nativeCharts === true;
  const chartImageBase64 = useNativeCharts ? null : renderChartImage(chart, categories, series);

  if (chartImageBase64) {
    slide.addImage({
      data: `image/png;base64,${chartImageBase64}`,
      x: 0.95,
      y: 1.8,
      w: 8.0,
      h: 4.5
    });
  } else {
    // Fallback: native OOXML chart (best in PowerPoint, may not render in Keynote)
    const chartData = series.map((entry) => ({
      name: entry.name,
      labels: categories,
      values: entry.data
    }));

    slide.addChart(toChartType(chart.type), chartData, {
      x: 0.95,
      y: 1.8,
      w: 8.0,
      h: 4.5,
      catAxisLabelFontSize: 11,
      valAxisLabelFontSize: 11,
      showLegend: true,
      legendFontSize: 10,
      showTitle: true,
      title: chart.title || current.title,
      titleFontFace: _t.fonts.body,
      titleFontSize: 13,
      chartColors: _t.chartColors.slice(0, 4)
    });
  }

  if (Array.isArray(current.bullets) && current.bullets.length > 0) {
    slide.addShape('roundRect', {
      x: 9.35,
      y: 1.85,
      w: 2.9,
      h: 3.6,
      rectRadius: 0.05,
      fill: { color: _t.colors.background },
      line: { color: _t.colors.border, pt: 1 }
    });
    addLabel(slide, 'Takeaways', 9.6, 2.1, 2.2);
    addBulletList(slide, current.bullets, { x: 9.45, y: 2.45, w: 2.45, h: 2.7, fontSize: 12 });
  }
}

function renderQuoteSlide(slide, deck, current) {
  addSlideHeader(slide, deck, current);
  slide.addShape('roundRect', {
    x: 1.0,
    y: 1.95,
    w: 11.0,
    h: 3.2,
    rectRadius: 0.08,
    fill: { color: _t.colors.background },
    line: { color: _t.colors.border, pt: 1 }
  });
  addTextBox(slide, `“${(current.bullets || [current.subtitle || ''])[0] || ''}”`, {
    x: 1.5,
    y: 2.45,
    w: 10.0,
    h: 1.2,
    fontSize: 24,
    italic: true,
    bold: true,
    align: 'center',
    color: _t.colors.text,
    valign: 'mid'
  });
  if (current.subtitle) {
    addTextBox(slide, current.subtitle, {
      x: 8.6,
      y: 4.55,
      w: 2.3,
      h: 0.25,
      fontSize: 11,
      color: _t.colors.textMuted,
      align: 'right'
    });
  }
}

function renderClosingSlide(slide, deck, current) {
  slide.background = { color: _t.colors.closingBg };
  addTextBox(slide, current.title, {
    x: 1.0,
    y: 2.0,
    w: 8.8,
    h: 0.9,
    fontSize: 30,
    bold: true,
    color: _t.colors.textLight
  });
  addTextBox(slide, current.subtitle || 'Questions and discussion', {
    x: 1.02,
    y: 3.1,
    w: 5.4,
    h: 0.45,
    fontSize: 16,
    color: _t.colors.border
  });
  if (Array.isArray(current.bullets) && current.bullets.length > 0) {
    addBulletList(slide, current.bullets, { x: 1.0, y: 4.1, w: 5.8, h: 1.8, fontSize: 15, color: _t.colors.headerBg });
  }
}

function renderSlide(pptx, deck, current) {
  const slide = pptx.addSlide();
  slide.background = { color: _t.colors.slideBg };

  switch (current.layout) {
    case 'title':
      renderTitleSlide(slide, deck, current);
      break;
    case 'agenda':
    case 'section':
    case 'summary':
      renderAgendaSlide(slide, deck, current);
      break;
    case 'bullet':
      renderBulletSlide(slide, deck, current);
      break;
    case 'two-column':
      renderTwoColumnSlide(slide, deck, current);
      break;
    case 'comparison':
      renderComparisonSlide(slide, deck, current);
      break;
    case 'timeline':
      renderTimelineSlide(slide, deck, current);
      break;
    case 'process':
      renderProcessSlide(slide, deck, current);
      break;
    case 'table':
      renderTableSlide(slide, deck, current);
      break;
    case 'chart':
      renderChartSlide(slide, deck, current);
      break;
    case 'quote':
      renderQuoteSlide(slide, deck, current);
      break;
    case 'closing':
      renderClosingSlide(slide, deck, current);
      break;
    default:
      renderBulletSlide(slide, deck, current);
      break;
  }

  const noteLines = [];

  if (deck.needsSpeakerNotes && Array.isArray(current.speakerNotes) && current.speakerNotes.length > 0) {
    noteLines.push(...current.speakerNotes);
  }

  if (deck.sourceDisplayMode === 'notes' && Array.isArray(current.sources) && current.sources.length > 0) {
    if (noteLines.length > 0) {
      noteLines.push('');
    }
    noteLines.push(...formatSourceNotes(current.sources));
  }

  if (noteLines.length > 0) {
    slide.addNotes(noteLines.join('\n'));
  }

  if (current.layout !== 'title' && current.layout !== 'closing') {
    addFooter(slide, current.page);
  }
}

async function buildDeck(deck, outputPath) {
  validateDeck(deck);
  ensureOutputDir(outputPath);

  // Resolve theme for this deck (template → named theme → default)
  _t = resolveTheme(deck);

  const pptx = new PptxGenJS();
  pptx.author = 'GitHub Copilot';
  pptx.company = 'Local Prototype';
  pptx.layout = 'LAYOUT_WIDE';
  pptx.subject = deck.scenario || 'Auto-generated presentation';
  pptx.title = deck.deckTitle;
  pptx.lang = deck.language || 'en-US';
  pptx.theme = {
    headFontFace: _t.fonts.heading,
    bodyFontFace: _t.fonts.body,
    lang: deck.language || 'en-US'
  };

  deck.slides.forEach((slideDef) => renderSlide(pptx, deck, slideDef));

  await pptx.writeFile({ fileName: outputPath });
  console.log(`Generated: ${outputPath}`);
}

async function buildFromFile(inputArg, outputArg, options = {}) {
  const inputPath = path.resolve(inputArg || 'examples/inputs/sample-input.json');
  const outputPath = path.resolve(outputArg || 'output/sample-deck.pptx');
  const deck = readDeck(inputPath);

  if (options.nativeCharts) {
    deck._nativeCharts = true;
  }

  await buildDeck(deck, outputPath);
}

module.exports = {
  allowedLayouts,
  readDeck,
  validateDeck,
  buildDeck,
  buildFromFile
};

if (require.main === module) {
  const args = process.argv.slice(2);
  const nativeCharts = args.includes('--native-charts');
  const positional = args.filter(a => !a.startsWith('--'));
  buildFromFile(positional[0], positional[1], { nativeCharts }).catch((error) => fail(error.message));
}
