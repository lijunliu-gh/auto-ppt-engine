// ============================================================================
// DEPRECATED — This file is kept for reference only.
// All planning, revision, and orchestration logic has moved to the Python
// smart layer (python_backend/smart_layer.py).  Do NOT add new logic here.
// This file will be removed in a future release.
// ============================================================================

// Legacy Node smart-layer reference.
// Public create, revise, skill, and server entrypoints now route to the Python smart layer.
// Keep this file only as a transition reference while Node remains the PPTX renderer host.

const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');
const OpenAI = require('openai');
const Ajv2020 = require('ajv/dist/2020');

dotenv.config({ override: false });

const rootDir = __dirname;
const skillPath = path.join(rootDir, 'SKILL.md');
const schemaPath = path.join(rootDir, 'deck-schema.json');
const maxRepairAttempts = 1;
const supportedLayouts = [
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
];

function fail(message) {
  throw new Error(message);
}

function resolvePath(filePath) {
  return path.isAbsolute(filePath) ? filePath : path.resolve(rootDir, filePath);
}

function readTextFile(filePath) {
  if (!filePath) {
    fail('Missing file path.');
  }
  if (!fs.existsSync(filePath)) {
    fail(`File not found: ${filePath}`);
  }
  return fs.readFileSync(filePath, 'utf8');
}

function ensureParentDir(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function loadSkillInstructions() {
  return readTextFile(skillPath);
}

function loadSchema() {
  return JSON.parse(readTextFile(schemaPath));
}

function createValidator(schema = loadSchema()) {
  const ajv = new Ajv2020({ allErrors: true, strict: false });
  return ajv.compile(schema);
}

function formatValidationErrors(errors) {
  if (!Array.isArray(errors) || errors.length === 0) {
    return 'Unknown schema validation error.';
  }

  return errors
    .map((error) => `${error.instancePath || '/'} ${error.message}`.trim())
    .join('; ');
}

function extractJson(text) {
  const trimmed = text.trim();
  if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
    return trimmed;
  }

  const firstBrace = trimmed.indexOf('{');
  const lastBrace = trimmed.lastIndexOf('}');
  if (firstBrace >= 0 && lastBrace > firstBrace) {
    return trimmed.slice(firstBrace, lastBrace + 1);
  }

  fail('Model output did not contain a JSON object.');
}

function clampSlideCount(count) {
  const parsed = Number.parseInt(String(count || ''), 10);
  if (Number.isNaN(parsed)) {
    return 8;
  }
  return Math.max(5, Math.min(12, parsed));
}

function inferLanguage() {
  return 'en-US';
}

function inferTheme(prompt) {
  const lower = prompt.toLowerCase();
  if (lower.includes('tech')) {
    return 'tech-modern';
  }
  if (lower.includes('investor') || lower.includes('pitch')) {
    return 'pitch-bold';
  }
  if (lower.includes('training')) {
    return 'education-bright';
  }
  if (lower.includes('internal')) {
    return 'internal-minimal';
  }
  return 'business-clean';
}

function inferSlideCount(prompt) {
  const pageMatch = prompt.match(/(\d{1,2})\s*slides?/i);
  return clampSlideCount(pageMatch ? pageMatch[1] : 8);
}

function inferAudience(prompt) {
  const lower = prompt.toLowerCase();
  if (lower.includes('executive') || lower.includes('board')) {
    return 'Executives and decision makers';
  }
  if (lower.includes('investor')) {
    return 'Investors and key stakeholders';
  }
  if (lower.includes('client') || lower.includes('customer')) {
    return 'Customers and partners';
  }
  return 'Management and project stakeholders';
}

function inferScenario(prompt) {
  const lower = prompt.toLowerCase();
  if (lower.includes('training')) {
    return 'Training presentation';
  }
  if (lower.includes('investor') || lower.includes('pitch')) {
    return 'Investor pitch';
  }
  if (lower.includes('review') || lower.includes('quarterly')) {
    return 'Business review';
  }
  return 'General presentation';
}

function inferTone(prompt) {
  const lower = prompt.toLowerCase();
  if (lower.includes('tech')) {
    return 'Modern, technical, fast-paced';
  }
  if (lower.includes('professional')) {
    return 'Professional, concise, decision-oriented';
  }
  return 'Professional and concise';
}

function inferDeckTitle(prompt) {
  const text = prompt.replace(/\s+/g, ' ').trim();
  if (!text) {
    return 'Auto-generated Presentation';
  }
  return text.length > 36 ? `${text.slice(0, 33)}...` : text;
}

function emptySlide(page, layout, title) {
  return {
    page,
    layout,
    title,
    subtitle: '',
    objective: '',
    bullets: [],
    left: [],
    right: [],
    table: { columns: [], rows: [] },
    chart: { type: '', title: '', categories: [], series: [] },
    visuals: [],
    sources: [],
    speakerNotes: []
  };
}

function createSlideSourceRef(source, index, slide) {
  return {
    id: source.id || `src-${index + 1}`,
    label: source.label,
    type: source.type,
    location: source.location,
    trustLevel: source.trustLevel || 'user-provided',
    priority: source.priority || 'normal',
    notes: source.notes || '',
    citation: source.citation || '',
    usedFor: slide.layout === 'title' ? ['deck context'] : ['slide narrative']
  };
}

function normalizeDeckSourceMetadata(deck, loadedSources = []) {
  deck.sourceDisplayMode = deck.sourceDisplayMode || 'notes';

  if (!Array.isArray(deck.slides)) {
    return deck;
  }

  deck.slides.forEach((slide) => {
    slide.sources = Array.isArray(slide.sources) ? slide.sources : [];

    if (slide.sources.length === 0 && loadedSources.length > 0) {
      slide.sources = loadedSources.slice(0, 3).map((source, index) => createSlideSourceRef(source, index, slide));
    }
  });

  return deck;
}

function buildMockDeck(prompt, researchNotes = [], contextTexts = [], loadedSources = []) {
  const language = inferLanguage(prompt);
  const slideCount = inferSlideCount(prompt);
  const deckTitle = inferDeckTitle(prompt);
  const theme = inferTheme(prompt);
  const scenario = inferScenario(prompt);
  const audience = inferAudience(prompt);
  const tone = inferTone(prompt);
  const titleSlide = emptySlide(1, 'title', deckTitle);
  titleSlide.subtitle = 'Generated by the local mock planner';
  titleSlide.objective = 'Offline verification of the full prompt-to-PPT pipeline';
  titleSlide.speakerNotes = ['This title slide was generated by the mock planner.'];

  const agendaSlide = emptySlide(2, 'agenda', 'Agenda');
  agendaSlide.objective = 'Set the presentation storyline';
  agendaSlide.bullets = ['Background and goals', 'Current challenges', 'Approach', 'Execution plan', 'Risks and next steps'];

  const challengeSlide = emptySlide(3, 'bullet', 'Background and goals');
  challengeSlide.objective = 'Explain why this presentation matters now';
  challengeSlide.bullets = [
    `Organize the request "${prompt.trim()}" into a presentation storyline`,
    'Turn fragmented ideas into a clear business narrative',
    'Keep each slide presentation-friendly instead of document-like',
    'Reserve placeholders for real data and visuals'
  ];
  challengeSlide.visuals = ['Add one background illustration', 'Add one goals framework visual'];

  const twoColumn = emptySlide(4, 'two-column', 'Current state and challenges');
  twoColumn.objective = 'Separate current state from blockers';
  twoColumn.left = ['Input requirements may be incomplete', 'Users often provide only topic and style', 'Content and layout are rarely mapped clearly'];
  twoColumn.right = ['The flow must clarify missing constraints', 'Each slide needs controlled information density', 'Natural language must become stable structured JSON'];

  const processSlide = emptySlide(5, 'process', 'Processing flow');
  processSlide.objective = 'Show the split between the agent and renderer';
  processSlide.bullets = ['Understand request', 'Plan deck', 'Validate JSON', 'Render PPT'];

  const timelineSlide = emptySlide(6, 'timeline', 'Execution timeline');
  timelineSlide.objective = 'Break delivery into trackable phases';
  timelineSlide.bullets = ['Receive prompt', 'Draft outline', 'Create full slides', 'Export final deck'];

  const summarySlide = emptySlide(7, 'summary', 'Key recommendations');
  summarySlide.objective = 'Give practical recommendations for the current version';
  summarySlide.bullets = [
    'Stabilize deck JSON generation before investing in branding and templating',
    'Add research and revision as the next capability layer',
    'Prioritize 3 to 4 reusable templates for real business scenarios'
  ];
  if (contextTexts.length > 0) {
    summarySlide.bullets[1] = `Incorporate ${contextTexts.length} trusted context item(s) into the storyline before expanding web research`;
  }

  const closingSlide = emptySlide(8, 'closing', 'Next steps');
  closingSlide.subtitle = 'Move to model-driven generation once the requirements are confirmed';
  closingSlide.bullets = ['Confirm model integration', 'Add real research capability', 'Add branded templates and image assets'];

  const slides = [titleSlide, agendaSlide, challengeSlide, twoColumn, processSlide, timelineSlide, summarySlide, closingSlide]
    .slice(0, slideCount)
    .map((slide, index) => ({ ...slide, page: index + 1 }));

  slides[slides.length - 1].layout = 'closing';

  return {
    deckTitle,
    language,
    audience,
    scenario,
    tone,
    theme,
    sourceDisplayMode: 'notes',
    slideCount: slides.length,
    needsSpeakerNotes: true,
    assumptions: [
      'Using the local mock planner for workflow verification, not final content quality',
      'Without live research, content is limited to the prompt and provided context'
    ]
      .concat(contextTexts.length > 0 ? [`Planning used ${contextTexts.length} context item(s), including uploaded materials or URLs.`] : [])
      .concat(researchNotes.length > 0 ? researchNotes : []),
    slides
  };
}

async function maybeRunResearch(userPrompt) {
  if (!process.env.TAVILY_API_KEY) {
    return [];
  }

  const response = await fetch('https://api.tavily.com/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      api_key: process.env.TAVILY_API_KEY,
      query: userPrompt,
      search_depth: 'advanced',
      max_results: 5,
      include_answer: true
    })
  });

  if (!response.ok) {
    fail(`Tavily request failed with status ${response.status}`);
  }

  const data = await response.json();
  const notes = [];

  if (data.answer) {
    notes.push(`Research summary: ${data.answer}`);
  }

  if (Array.isArray(data.results)) {
    data.results.slice(0, 5).forEach((result, index) => {
      notes.push(`Source ${index + 1}: ${result.title} - ${result.url}`);
      if (result.content) {
        notes.push(`Source ${index + 1} note: ${result.content.slice(0, 300)}`);
      }
    });
  }

  return notes;
}

function buildSystemPrompt(skillInstructions, schema) {
  return [
    'You are an autonomous PowerPoint planning agent.',
    'Your job is to convert a user presentation request into strict deck JSON that matches the provided schema exactly.',
    'Do not explain your reasoning. Do not wrap the JSON in markdown. Return JSON only.',
    'The slide count must match slideCount and pages must be consecutive starting at 1.',
    `Use only supported layouts: ${supportedLayouts.join(', ')}.`,
    'Do not fabricate hard business metrics unless they are clearly marked as placeholders or directly provided.',
    'When the request lacks information, make explicit assumptions in the assumptions array.',
    'Keep the deck presentation-friendly rather than document-like.',
    'SKILL INSTRUCTIONS START',
    skillInstructions,
    'SKILL INSTRUCTIONS END',
    'JSON SCHEMA START',
    JSON.stringify(schema),
    'JSON SCHEMA END'
  ].join('\n\n');
}

function buildCreatePrompt(userPrompt, contextTexts, researchNotes) {
  const blocks = [
    'User request:',
    userPrompt.trim()
  ];

  if (contextTexts.length > 0) {
    blocks.push('Additional context files:');
    contextTexts.forEach((text, index) => {
      blocks.push(`Context ${index + 1}:\n${text}`);
    });
  }

  if (researchNotes.length > 0) {
    blocks.push('Research notes:');
    blocks.push(researchNotes.join('\n'));
  }

  blocks.push('Return deck JSON only.');
  return blocks.join('\n\n');
}

function buildRevisePrompt(existingDeck, revisionPrompt, contextTexts, researchNotes) {
  const blocks = [
    'Existing deck JSON:',
    JSON.stringify(existingDeck, null, 2),
    'Revision request:',
    revisionPrompt.trim(),
    'Modify the deck to satisfy the revision request while keeping unaffected slides and the overall structure coherent.',
    'Preserve strong existing slide titles and narrative flow unless the revision explicitly requires structural changes.',
    'When asked to compress, merge overlapping slides instead of simply deleting content.',
    'When asked to emphasize a topic, strengthen the relevant slide objective, title, bullets, and speaker notes.',
    'If a slide count change is requested, renumber slides consecutively and keep title/closing slides coherent.',
    'Update slideCount if the slide count changes.',
    'Return full corrected deck JSON only.'
  ];

  if (contextTexts.length > 0) {
    blocks.push('Additional context files:');
    contextTexts.forEach((text, index) => {
      blocks.push(`Context ${index + 1}:\n${text}`);
    });
  }

  if (researchNotes.length > 0) {
    blocks.push('Research notes:');
    blocks.push(researchNotes.join('\n'));
  }

  return blocks.join('\n\n');
}

function buildRepairPrompt(originalPrompt, invalidJson, validationErrors) {
  return [
    'The previous JSON did not pass schema validation.',
    'Fix it without changing the overall intent unless required for validity.',
    `Validation errors: ${validationErrors}`,
    'Previous JSON:',
    invalidJson,
    'Original prompt:',
    originalPrompt,
    'Return corrected JSON only.'
  ].join('\n\n');
}

function renumberSlides(deck) {
  deck.slides.forEach((slide, index) => {
    slide.page = index + 1;
  });
  deck.slideCount = deck.slides.length;
}

function normalizeClosingSlide(deck) {
  if (!Array.isArray(deck.slides) || deck.slides.length === 0) {
    return;
  }

  const lastIndex = deck.slides.length - 1;
  const closingIndex = deck.slides.findIndex((slide) => slide.layout === 'closing');
  if (closingIndex >= 0 && closingIndex !== lastIndex) {
    const [closingSlide] = deck.slides.splice(closingIndex, 1);
    deck.slides.push(closingSlide);
  }

  const closingSlide = deck.slides[deck.slides.length - 1];
  closingSlide.layout = 'closing';
  if (!closingSlide.title) {
    closingSlide.title = 'Next steps';
  }
}

function requestedSlideCount(prompt) {
  const match = prompt.match(/(?:compress to|reduce to|limit to|change to)\s*(\d{1,2})\s*slides?/i);
  return match ? clampSlideCount(match[1]) : null;
}

function requestedPageIndex(prompt) {
  const match = prompt.match(/slide\s*(\d{1,2})/i);
  if (!match) {
    return null;
  }
  const number = Number.parseInt(match[1] || match[2], 10);
  return Number.isNaN(number) ? null : number - 1;
}

function reviseRequestedLayout(prompt) {
  const mappings = [
    { test: /timeline/i, layout: 'timeline' },
    { test: /process/i, layout: 'process' },
    { test: /comparison/i, layout: 'comparison' },
    { test: /two-column/i, layout: 'two-column' },
    { test: /chart/i, layout: 'chart' },
    { test: /summary/i, layout: 'summary' }
  ];

  const match = mappings.find((item) => item.test.test(prompt));
  return match ? match.layout : null;
}

function applyRequestedTheme(deck, prompt) {
  const lower = prompt.toLowerCase();
  if (lower.includes('tech')) {
    deck.theme = 'tech-modern';
    deck.tone = 'Modern, technical, fast-paced';
  }
  if (lower.includes('professional')) {
    deck.theme = 'business-clean';
    deck.tone = 'Professional, concise, decision-oriented';
  }
}

function applyPageSpecificRevision(deck, prompt) {
  const pageIndex = requestedPageIndex(prompt);
  const targetLayout = reviseRequestedLayout(prompt);
  if (pageIndex === null || pageIndex < 0 || pageIndex >= deck.slides.length || !targetLayout) {
    return false;
  }

  const slide = deck.slides[pageIndex];
  slide.layout = targetLayout;
  slide.objective = 'Restructured according to the requested slide change';

  if (targetLayout === 'timeline') {
    slide.bullets = ['Phase 1: define goals', 'Phase 2: converge on approach', 'Phase 3: execute', 'Phase 4: optimize'];
    slide.left = [];
    slide.right = [];
  }

  if (targetLayout === 'process') {
    slide.bullets = ['Capture request', 'Structure the deck', 'Generate content', 'Export output'];
  }

  if (targetLayout === 'comparison') {
    slide.left = ['Option A: faster delivery', 'Lower cost', 'Good for rapid validation'];
    slide.right = ['Option B: better scalability', 'Higher upfront cost', 'Better for long-term buildout'];
    slide.bullets = [];
  }

  if (targetLayout === 'two-column') {
    slide.left = ['Current issues', 'Core blockers', 'Impact scope'];
    slide.right = ['Response strategy', 'Expected impact', 'Execution needs'];
    slide.bullets = [];
  }

  if (targetLayout === 'summary') {
    slide.bullets = ['Key point 1: focus the goal', 'Key point 2: tighten the message', 'Key point 3: clarify execution'];
  }

  return true;
}

function compressDeck(deck, targetCount) {
  if (!Number.isInteger(targetCount) || deck.slides.length <= targetCount) {
    return;
  }

  while (deck.slides.length > targetCount) {
    const removableIndex = deck.slides.findIndex((slide, index) => index > 1 && index < deck.slides.length - 1 && slide.layout !== 'closing');
    if (removableIndex < 0) {
      break;
    }

    const removed = deck.slides.splice(removableIndex, 1)[0];
    const mergeTargetIndex = Math.max(1, removableIndex - 1);
    const mergeTarget = deck.slides[mergeTargetIndex];
    const extraBullets = [];

    if (removed.title) {
      extraBullets.push(`Added: ${removed.title}`);
    }
    if (Array.isArray(removed.bullets)) {
      extraBullets.push(...removed.bullets.slice(0, 2));
    }

    mergeTarget.bullets = Array.isArray(mergeTarget.bullets) ? mergeTarget.bullets.concat(extraBullets).slice(0, 5) : extraBullets.slice(0, 5);
    mergeTarget.objective = 'Combined key points after slide compression';
  }
}

function emphasizeExecutionPlan(deck) {
  let slide = deck.slides.find((item) => /execution|implementation|plan/i.test(item.title || ''));

  if (!slide) {
    const insertIndex = Math.max(1, deck.slides.length - 1);
    slide = emptySlide(insertIndex + 1, 'process', 'Execution plan');
    deck.slides.splice(insertIndex, 0, slide);
  }

  slide.layout = slide.layout === 'timeline' ? 'timeline' : 'process';
  slide.title = 'Execution plan';
  slide.objective = 'Break the work into concrete execution steps';
  slide.bullets = ['Set priorities and owners', 'Deliver in clear phases', 'Track weekly progress and escalate risks', 'Review outcomes at each milestone'];
  slide.speakerNotes = ['Emphasize that this slide is about execution, not abstract vision.'];
}

function makeMoreConclusionDriven(deck) {
  const summaryIndex = deck.slides.findIndex((slide) => slide.layout === 'summary' || /summary|recommendation|conclusion/i.test(slide.title || ''));
  const summarySlide = summaryIndex >= 0 ? deck.slides.splice(summaryIndex, 1)[0] : emptySlide(2, 'summary', 'Key conclusions');

  summarySlide.layout = 'summary';
  summarySlide.title = 'Key conclusions';
  summarySlide.objective = 'Lead with the conclusions before supporting detail';
  if (!Array.isArray(summarySlide.bullets) || summarySlide.bullets.length === 0) {
    summarySlide.bullets = ['Focus on the highest-value priorities', 'Put execution before supporting detail', 'Tie resource requests to goals'];
  }

  deck.slides.splice(1, 0, summarySlide);
}

function applyHeuristicRevision(existingDeck, prompt, contextTexts = []) {
  const cloned = JSON.parse(JSON.stringify(existingDeck));
  if (!cloned || !Array.isArray(cloned.slides)) {
    fail('existingDeck is required for mock revision mode.');
  }

  cloned.sourceDisplayMode = cloned.sourceDisplayMode || 'notes';
  cloned.assumptions = Array.isArray(cloned.assumptions) ? cloned.assumptions : [];
  cloned.assumptions.push(`Updated for revision request: ${prompt}`);
  if (contextTexts.length > 0) {
    cloned.assumptions.push(`Revision used ${contextTexts.length} additional context item(s).`);
  }

  applyRequestedTheme(cloned, prompt);

  const handledSpecificPage = applyPageSpecificRevision(cloned, prompt);
  if (!handledSpecificPage && cloned.slides.length > 0) {
    const targetIndex = Math.min(2, cloned.slides.length - 1);
    cloned.slides[targetIndex].objective = 'Reflect the latest revision request';
    cloned.slides[targetIndex].speakerNotes = [`Revision request: ${prompt}`];
    if (contextTexts.length > 0) {
      cloned.slides[targetIndex].bullets = Array.isArray(cloned.slides[targetIndex].bullets)
        ? cloned.slides[targetIndex].bullets.concat(`Additional context sources considered: ${contextTexts.length}`).slice(0, 5)
        : [`Additional context sources considered: ${contextTexts.length}`];
    }
  }

  if (/conclusion/i.test(prompt)) {
    makeMoreConclusionDriven(cloned);
  }

  if (/execution plan|implementation/i.test(prompt)) {
    emphasizeExecutionPlan(cloned);
  }

  const targetCount = requestedSlideCount(prompt);
  if (targetCount) {
    compressDeck(cloned, targetCount);
  }

  normalizeClosingSlide(cloned);
  renumberSlides(cloned);
  return cloned;
}

function createOpenAIClient() {
  if (!process.env.OPENAI_API_KEY) {
    fail('OPENAI_API_KEY is not set. Use mock mode for offline testing or configure the API key in .env.');
  }

  const config = { apiKey: process.env.OPENAI_API_KEY };
  if (process.env.OPENAI_BASE_URL) {
    config.baseURL = process.env.OPENAI_BASE_URL;
  }
  return new OpenAI(config);
}

async function requestDeckJson(client, systemPrompt, userPrompt) {
  const model = process.env.OPENAI_MODEL || 'gpt-4.1-mini';
  const response = await client.chat.completions.create({
    model,
    temperature: 0.3,
    response_format: { type: 'json_object' },
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt }
    ]
  });

  const content = response.choices?.[0]?.message?.content;
  if (!content) {
    fail('Model returned no content.');
  }
  return content;
}

async function executePlanningFlow({
  prompt,
  contextTexts = [],
  loadedSources = [],
  researchEnabled = false,
  mock = false,
  mode = 'create',
  existingDeck = null
}) {
  const schema = loadSchema();
  const validator = createValidator(schema);
  const researchNotes = researchEnabled ? await maybeRunResearch(prompt) : [];

  if (mock) {
    if (mode === 'create') {
      const deck = normalizeDeckSourceMetadata(buildMockDeck(prompt, researchNotes, contextTexts, loadedSources), loadedSources);
      if (!validator(deck)) {
        fail(`Generated deck failed schema validation: ${formatValidationErrors(validator.errors)}`);
      }
      return deck;
    }

    const revised = normalizeDeckSourceMetadata(applyHeuristicRevision(existingDeck, prompt, contextTexts), loadedSources);
    if (!validator(revised)) {
      fail(`Revised deck failed schema validation: ${formatValidationErrors(validator.errors)}`);
    }
    return revised;
  }

  const skillInstructions = loadSkillInstructions();
  const systemPrompt = buildSystemPrompt(skillInstructions, schema);
  const client = createOpenAIClient();
  const basePrompt = mode === 'create'
    ? buildCreatePrompt(prompt, contextTexts, researchNotes)
    : buildRevisePrompt(existingDeck, prompt, contextTexts, researchNotes);

  let rawJson = await requestDeckJson(client, systemPrompt, basePrompt);

  for (let attempt = 0; attempt <= maxRepairAttempts; attempt += 1) {
    let parsed;
    try {
      parsed = JSON.parse(extractJson(rawJson));
    } catch (error) {
      if (attempt === maxRepairAttempts) {
        throw error;
      }
      rawJson = await requestDeckJson(
        client,
        systemPrompt,
        buildRepairPrompt(prompt, rawJson, `JSON parse error: ${error.message}`)
      );
      continue;
    }

    const normalized = normalizeDeckSourceMetadata(parsed, loadedSources);
    const valid = validator(normalized);
    if (valid) {
      return normalized;
    }

    if (attempt === maxRepairAttempts) {
      fail(`Schema validation failed: ${formatValidationErrors(validator.errors)}`);
    }

    rawJson = await requestDeckJson(
      client,
      systemPrompt,
      buildRepairPrompt(prompt, JSON.stringify(normalized), formatValidationErrors(validator.errors))
    );
  }

  fail('Unable to produce a valid deck JSON.');
}

module.exports = {
  rootDir,
  skillPath,
  schemaPath,
  supportedLayouts,
  resolvePath,
  readTextFile,
  ensureParentDir,
  loadSchema,
  createValidator,
  formatValidationErrors,
  executePlanningFlow,
  buildMockDeck,
  applyHeuristicRevision
};
