from __future__ import annotations

import importlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, cast
from urllib.request import Request, urlopen

from .llm_provider import LLMProvider, get_default_provider

logger = logging.getLogger("auto-ppt")

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILL_PATH = ROOT_DIR / "SKILL.md"
SCHEMA_PATH = ROOT_DIR / "deck-schema.json"
SUPPORTED_LAYOUTS = [
    "title",
    "agenda",
    "section",
    "bullet",
    "two-column",
    "comparison",
    "timeline",
    "process",
    "table",
    "chart",
    "quote",
    "summary",
    "closing",
]
MAX_REPAIR_ATTEMPTS = 1


def fail(message: str) -> None:
    raise RuntimeError(message)

def resolve_path(file_path: str | Path) -> Path:
    path = Path(file_path)
    return path if path.is_absolute() else (ROOT_DIR / path).resolve()


def read_text_file(file_path: str | Path) -> str:
    path = resolve_path(file_path)
    if not path.exists():
        fail(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


def ensure_parent_dir(file_path: str | Path) -> None:
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)


def load_skill_instructions() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def load_schema() -> Dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def create_validator(schema: Dict[str, Any] | None = None) -> Any:
    Draft202012Validator = importlib.import_module("jsonschema").Draft202012Validator

    actual_schema = schema or load_schema()
    return Draft202012Validator(actual_schema)


def format_validation_errors(errors: List[Any]) -> str:
    if not errors:
        return "Unknown schema validation error."
    formatted = []
    for error in errors:
        location = "/" + "/".join(str(item) for item in error.path) if list(error.path) else "/"
        formatted.append(f"{location} {error.message}".strip())
    return "; ".join(formatted)


def extract_json(text: str) -> str:
    trimmed = text.strip()
    if trimmed.startswith("{") and trimmed.endswith("}"):
        return trimmed
    first = trimmed.find("{")
    last = trimmed.rfind("}")
    if first >= 0 and last > first:
        return trimmed[first : last + 1]
    fail("Model output did not contain a JSON object.")
    raise RuntimeError("Model output did not contain a JSON object.")


def clamp_slide_count(count: Any) -> int:
    try:
        parsed = int(str(count or ""))
    except ValueError:
        return 8
    return max(5, min(12, parsed))


def infer_language(_: str) -> str:
    return "en-US"


def infer_theme(prompt: str) -> str:
    lower = prompt.lower()
    if "tech" in lower:
        return "tech-modern"
    if "investor" in lower or "pitch" in lower:
        return "pitch-bold"
    if "training" in lower:
        return "education-bright"
    if "internal" in lower:
        return "internal-minimal"
    return "business-clean"


def infer_slide_count(prompt: str) -> int:
    match = re.search(r"(\d{1,2})\s*slides?", prompt, re.IGNORECASE)
    return clamp_slide_count(match.group(1) if match else 8)


def infer_audience(prompt: str) -> str:
    lower = prompt.lower()
    if "executive" in lower or "board" in lower:
        return "Executives and decision makers"
    if "investor" in lower:
        return "Investors and key stakeholders"
    if "client" in lower or "customer" in lower:
        return "Customers and partners"
    return "Management and project stakeholders"


def infer_scenario(prompt: str) -> str:
    lower = prompt.lower()
    if "training" in lower:
        return "Training presentation"
    if "investor" in lower or "pitch" in lower:
        return "Investor pitch"
    if "review" in lower or "quarterly" in lower:
        return "Business review"
    return "General presentation"


def infer_tone(prompt: str) -> str:
    lower = prompt.lower()
    if "tech" in lower:
        return "Modern, technical, fast-paced"
    if "professional" in lower:
        return "Professional, concise, decision-oriented"
    return "Professional and concise"


def infer_deck_title(prompt: str) -> str:
    text = re.sub(r"\s+", " ", prompt).strip()
    if not text:
        return "Auto-generated Presentation"
    return text[:33] + "..." if len(text) > 36 else text


def empty_slide(page: int, layout: str, title: str) -> Dict[str, Any]:
    return {
        "page": page,
        "layout": layout,
        "title": title,
        "subtitle": "",
        "objective": "",
        "bullets": [],
        "left": [],
        "right": [],
        "table": {"columns": [], "rows": []},
        "chart": {"type": "", "title": "", "categories": [], "series": []},
        "visuals": [],
        "sources": [],
        "speakerNotes": [],
    }


def create_slide_source_ref(source: Dict[str, Any], index: int, slide: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": source.get("id") or f"src-{index + 1}",
        "label": source.get("label"),
        "type": source.get("type"),
        "location": source.get("location"),
        "trustLevel": source.get("trustLevel") or "user-provided",
        "priority": source.get("priority") or "normal",
        "notes": source.get("notes") or "",
        "citation": source.get("citation") or "",
        "usedFor": ["deck context"] if slide["layout"] == "title" else ["slide narrative"],
    }


def normalize_deck_source_metadata(deck: Dict[str, Any], loaded_sources: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    sources = loaded_sources or []
    deck["schemaVersion"] = "0.3.0"
    deck["sourceDisplayMode"] = deck.get("sourceDisplayMode") or "notes"
    slides = cast(List[Dict[str, Any]], deck.get("slides") if isinstance(deck.get("slides"), list) else [])
    for slide in slides:
        if not isinstance(slide.get("sources"), list):
            slide["sources"] = []
        if not slide["sources"] and sources:
            slide["sources"] = [create_slide_source_ref(source, index, slide) for index, source in enumerate(sources[:3])]
    return deck


def build_mock_deck(prompt: str, research_notes: List[str], context_texts: List[str], loaded_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    language = infer_language(prompt)
    slide_count = infer_slide_count(prompt)
    deck_title = infer_deck_title(prompt)
    title_slide = empty_slide(1, "title", deck_title)
    title_slide["subtitle"] = "Generated by the Python smart layer"
    title_slide["objective"] = "Offline verification of the Python planning flow"
    title_slide["speakerNotes"] = ["This title slide was generated by the Python mock planner."]

    agenda_slide = empty_slide(2, "agenda", "Agenda")
    agenda_slide["objective"] = "Set the presentation storyline"
    agenda_slide["bullets"] = [
        "Background and goals",
        "Current challenges",
        "Approach",
        "Execution plan",
        "Risks and next steps",
    ]

    background_slide = empty_slide(3, "bullet", "Background and goals")
    background_slide["objective"] = "Explain why this presentation matters now"
    background_slide["bullets"] = [
        f"Translate the request \"{prompt.strip()}\" into a slide-ready storyline",
        "Turn fragmented ideas into a concise business narrative",
        "Keep each slide presentation-friendly instead of document-like",
        "Reserve placeholders where live data is still missing",
    ]
    background_slide["visuals"] = ["Add one market context visual", "Add one operating model diagram"]

    two_column = empty_slide(4, "two-column", "Current state and challenges")
    two_column["objective"] = "Separate current state from blockers"
    two_column["left"] = [
        "Inputs may be incomplete or scattered",
        "Users often provide only topic and style",
        "Supporting material is rarely mapped to slide structure",
    ]
    two_column["right"] = [
        "The flow must clarify missing constraints",
        "Each slide needs controlled information density",
        "Natural language must become stable structured JSON",
    ]

    process_slide = empty_slide(5, "process", "Python smart layer workflow")
    process_slide["objective"] = "Show how Python and JS split responsibilities"
    process_slide["bullets"] = [
        "Understand request and sources in Python",
        "Plan or revise validated deck JSON",
        "Persist deck artifacts for inspection",
        "Call the JS renderer for final PPTX output",
    ]

    timeline_slide = empty_slide(6, "timeline", "Execution timeline")
    timeline_slide["objective"] = "Break delivery into trackable phases"
    timeline_slide["bullets"] = [
        "Capture intent",
        "Load trusted materials",
        "Draft slide storyline",
        "Render deck",
    ]

    chart_slide = empty_slide(7, "chart", "Adoption metrics")
    chart_slide["objective"] = "Visualize key adoption data"
    chart_slide["chart"] = {
        "type": "bar",
        "title": "Quarterly adoption",
        "categories": ["Q1", "Q2", "Q3", "Q4"],
        "series": [
            {"name": "Users", "data": [120, 250, 410, 580]},
            {"name": "Decks created", "data": [45, 110, 230, 390]},
        ],
    }
    chart_slide["bullets"] = ["Steady growth across all quarters", "Deck creation closely tracks user adoption"]

    summary_slide = empty_slide(8, "summary", "Key recommendations")
    summary_slide["objective"] = "Recommend the best next moves for this prototype"
    summary_slide["bullets"] = [
        "Keep the JS layer focused on rendering only",
        "Move agent-facing orchestration into Python",
        "Preserve deck JSON as the stable cross-language contract",
    ]
    if context_texts:
        summary_slide["bullets"][1] = f"Use {len(context_texts)} trusted context item(s) to improve the storyline before adding broader search"

    closing_slide = empty_slide(9, "closing", "Next steps")
    closing_slide["subtitle"] = "Use Python for intelligence and JS for output generation"
    closing_slide["bullets"] = [
        "Harden Python model integration",
        "Expand source understanding",
        "Add more branded deck templates",
    ]

    slides = [
        title_slide,
        agenda_slide,
        background_slide,
        two_column,
        process_slide,
        timeline_slide,
        chart_slide,
        summary_slide,
        closing_slide,
    ][:slide_count]

    for index, slide in enumerate(slides, start=1):
        slide["page"] = index
    slides[-1]["layout"] = "closing"

    return {
        "schemaVersion": "0.3.0",
        "deckTitle": deck_title,
        "language": language,
        "audience": infer_audience(prompt),
        "scenario": infer_scenario(prompt),
        "tone": infer_tone(prompt),
        "theme": infer_theme(prompt),
        "sourceDisplayMode": "notes",
        "slideCount": len(slides),
        "needsSpeakerNotes": True,
        "assumptions": [
            "Using the Python mock planner for workflow verification, not final content quality",
            "Without live research, content is limited to the prompt and provided context",
        ]
        + ([f"Planning used {len(context_texts)} context item(s), including uploaded materials or URLs."] if context_texts else [])
        + research_notes,
        "slides": slides,
    }


def build_system_prompt(skill_instructions: str, schema: Dict[str, Any]) -> str:
    return "\n\n".join(
        [
            "You are an autonomous PowerPoint planning agent.",
            "Your job is to convert a user presentation request into strict deck JSON that matches the provided schema exactly.",
            "Do not explain your reasoning. Do not wrap the JSON in markdown. Return JSON only.",
            "The slide count must match slideCount and pages must be consecutive starting at 1.",
            f"Use only supported layouts: {', '.join(SUPPORTED_LAYOUTS)}.",
            "Do not fabricate hard business metrics unless they are clearly marked as placeholders or directly provided.",
            "When the request lacks information, make explicit assumptions in the assumptions array.",
            "Keep the deck presentation-friendly rather than document-like.",
            # Chart-specific instructions
            "CHART DATA RULES:",
            "When using the 'chart' layout, you MUST populate chart.type, chart.title, chart.categories, and chart.series with concrete data.",
            "Supported chart types: bar, line, pie, area.",
            "Each series needs a 'name' (string) and 'data' (array of numbers). The data array length MUST equal categories length.",
            "If the source material contains numerical data (revenue, percentages, counts, metrics), extract it into chart data.",
            "If no numerical data is available, use realistic placeholder values and note this in assumptions.",
            "Do NOT leave chart.categories or chart.series as empty arrays — this renders as a blank placeholder.",
            'Example chart slide fragment: {"layout": "chart", "chart": {"type": "bar", "title": "Q1-Q4 Revenue", "categories": ["Q1", "Q2", "Q3", "Q4"], "series": [{"name": "2025", "data": [120, 145, 160, 180]}, {"name": "2024", "data": [100, 110, 130, 150]}]}}',
            # Visual / image instructions
            "VISUAL RULES:",
            "The 'visuals' array on each slide supports three kinds of items:",
            "1. Plain strings — text descriptions / suggestions for visuals (e.g. \"Add a market context chart\").",
            "2. Image objects — {\"type\": \"image\", \"path\": \"relative/path.png\"} or {\"type\": \"image\", \"url\": \"https://...\", \"alt\": \"description\", \"position\": \"right\"}.",
            "3. Placeholder objects — {\"type\": \"placeholder\", \"prompt\": \"A diagram of the workflow\", \"position\": \"right\"} for images to be generated later.",
            "Supported position values: right, left, center, full. Default is right.",
            "When source materials reference specific images or diagrams, emit image objects with the file path.",
            "When no actual image is available but a visual would help, use a placeholder with a descriptive prompt.",
            "Otherwise, use plain string descriptions.",
            "SKILL INSTRUCTIONS START",
            skill_instructions,
            "SKILL INSTRUCTIONS END",
            "JSON SCHEMA START",
            json.dumps(schema),
            "JSON SCHEMA END",
        ]
    )


def build_create_prompt(user_prompt: str, context_texts: List[str], research_notes: List[str]) -> str:
    blocks = ["User request:", user_prompt.strip()]
    if context_texts:
        blocks.append("Additional context files:")
        for index, text in enumerate(context_texts, start=1):
            blocks.append(f"Context {index}:\n{text}")
    # Inject numerical data hints to encourage chart usage
    num_hints = extract_numerical_hints(context_texts)
    if num_hints:
        blocks.append(num_hints)
    if research_notes:
        blocks.append("Research notes:")
        blocks.append("\n".join(research_notes))
    blocks.append("Return deck JSON only.")
    return "\n\n".join(blocks)


def build_revise_prompt(existing_deck: Dict[str, Any], revision_prompt: str, context_texts: List[str], research_notes: List[str]) -> str:
    blocks = [
        "Existing deck JSON:",
        json.dumps(existing_deck, indent=2),
        "Revision request:",
        revision_prompt.strip(),
        "Modify the deck to satisfy the revision request while keeping unaffected slides and the overall structure coherent.",
        "Preserve strong existing slide titles and narrative flow unless the revision explicitly requires structural changes.",
        "When asked to compress, merge overlapping slides instead of simply deleting content.",
        "When asked to emphasize a topic, strengthen the relevant slide objective, title, bullets, and speaker notes.",
        "If a slide count change is requested, renumber slides consecutively and keep title or closing slides coherent.",
        "Update slideCount if the slide count changes.",
        "Return full corrected deck JSON only.",
    ]
    if context_texts:
        blocks.append("Additional context files:")
        for index, text in enumerate(context_texts, start=1):
            blocks.append(f"Context {index}:\n{text}")
    if research_notes:
        blocks.append("Research notes:")
        blocks.append("\n".join(research_notes))
    return "\n\n".join(blocks)


def build_repair_prompt(original_prompt: str, invalid_json: str, validation_errors: str) -> str:
    return "\n\n".join(
        [
            "The previous JSON did not pass schema validation.",
            "Fix it without changing the overall intent unless required for validity.",
            f"Validation errors: {validation_errors}",
            "Previous JSON:",
            invalid_json,
            "Original prompt:",
            original_prompt,
            "Return corrected JSON only.",
        ]
    )


def renumber_slides(deck: Dict[str, Any]) -> None:
    for index, slide in enumerate(deck.get("slides", []), start=1):
        slide["page"] = index
    deck["slideCount"] = len(deck.get("slides", []))


def normalize_closing_slide(deck: Dict[str, Any]) -> None:
    slides = deck.get("slides", [])
    if not slides:
        return
    closing_index = next((index for index, slide in enumerate(slides) if slide.get("layout") == "closing"), None)
    if closing_index is not None and closing_index != len(slides) - 1:
        closing_slide = slides.pop(closing_index)
        slides.append(closing_slide)
    closing_slide = slides[-1]
    closing_slide["layout"] = "closing"
    closing_slide["title"] = closing_slide.get("title") or "Next steps"


def _is_valid_chart(chart: Dict[str, Any]) -> bool:
    """Check whether a chart object has usable data for rendering."""
    categories = chart.get("categories", [])
    series = chart.get("series", [])
    if not isinstance(categories, list) or len(categories) == 0:
        return False
    if not isinstance(series, list) or len(series) == 0:
        return False
    for entry in series:
        data = entry.get("data", [])
        if not isinstance(data, list) or len(data) == 0:
            return False
        if not all(isinstance(v, (int, float)) for v in data):
            return False
    return True


def validate_chart_slides(deck: Dict[str, Any]) -> List[str]:
    """Validate chart slides and degrade invalid ones to bullet layout.

    Returns a list of assumption strings describing any fallbacks applied.
    """
    fallback_notes: List[str] = []
    for slide in deck.get("slides", []):
        if slide.get("layout") != "chart":
            continue
        chart = slide.get("chart", {})
        if _is_valid_chart(chart):
            continue
        # Degrade to bullet layout
        logger.warning("Chart fallback: slide %d '%s' has invalid chart data, converting to bullet",
                        slide.get("page", 0), slide.get("title", ""))
        original_title = slide.get("title", "Chart")
        chart_title = chart.get("title", "")
        slide["layout"] = "bullet"
        slide["objective"] = f"Converted from chart: {chart_title or original_title}"
        # Preserve any existing bullets; add chart context as bullets if missing
        if not slide.get("bullets") or len(slide["bullets"]) == 0:
            slide["bullets"] = [
                f"Data visualization: {chart_title}" if chart_title else "Data visualization planned",
                "Chart data was insufficient for rendering — presenting key points instead",
            ]
            if isinstance(chart.get("categories"), list) and chart["categories"]:
                slide["bullets"].append(f"Categories: {', '.join(str(c) for c in chart['categories'][:6])}")
        fallback_notes.append(
            f"Slide {slide.get('page', '?')} ('{original_title}'): chart data was invalid, converted to bullet layout"
        )
    return fallback_notes


def extract_numerical_hints(context_texts: List[str]) -> str:
    """Scan source context for numerical data patterns and return chart hints.

    Looks for percentages, currency values, and tabular number patterns that
    could inform chart generation.
    """
    number_pattern = re.compile(
        r'(?:'
        r'\d+(?:\.\d+)?%'               # percentages
        r'|\$\d[\d,]*(?:\.\d+)?'         # dollar amounts
        r'|\d[\d,]*(?:\.\d+)?\s*(?:million|billion|M|B|K|k)'  # scaled numbers
        r')',
    )
    hits: List[str] = []
    for text in context_texts:
        matches = number_pattern.findall(text[:5000])  # scan first 5k chars
        if len(matches) >= 3:  # only signal if there's meaningful numerical density
            hits.append(f"Source contains numerical data ({len(matches)} values found): {', '.join(matches[:8])}")
    if not hits:
        return ""
    return "NUMERICAL DATA DETECTED IN SOURCES — consider using chart layouts to visualize this data:\n" + "\n".join(hits)


def requested_slide_count(prompt: str) -> int | None:
    match = re.search(r"(?:compress to|reduce to|limit to|change to)\s*(\d{1,2})\s*slides?", prompt, re.IGNORECASE)
    return clamp_slide_count(match.group(1)) if match else None


def requested_page_index(prompt: str) -> int | None:
    match = re.search(r"slide\s*(\d{1,2})", prompt, re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1)) - 1


def revise_requested_layout(prompt: str) -> str | None:
    mappings = [
        (r"timeline", "timeline"),
        (r"process", "process"),
        (r"comparison", "comparison"),
        (r"two-column", "two-column"),
        (r"chart", "chart"),
        (r"summary", "summary"),
    ]
    for pattern, layout in mappings:
        if re.search(pattern, prompt, re.IGNORECASE):
            return layout
    return None


def apply_requested_theme(deck: Dict[str, Any], prompt: str) -> None:
    lower = prompt.lower()
    if "tech" in lower:
        deck["theme"] = "tech-modern"
        deck["tone"] = "Modern, technical, fast-paced"
    if "professional" in lower:
        deck["theme"] = "business-clean"
        deck["tone"] = "Professional, concise, decision-oriented"


def apply_page_specific_revision(deck: Dict[str, Any], prompt: str) -> bool:
    page_index = requested_page_index(prompt)
    target_layout = revise_requested_layout(prompt)
    slides = deck.get("slides", [])
    if page_index is None or target_layout is None or page_index < 0 or page_index >= len(slides):
        return False
    slide = slides[page_index]
    slide["layout"] = target_layout
    slide["objective"] = "Restructured according to the requested slide change"
    if target_layout == "timeline":
        slide["bullets"] = ["Phase 1: define goals", "Phase 2: align approach", "Phase 3: execute", "Phase 4: optimize"]
        slide["left"] = []
        slide["right"] = []
    if target_layout == "process":
        slide["bullets"] = ["Capture request", "Structure the deck", "Generate content", "Export output"]
    if target_layout == "comparison":
        slide["left"] = ["Option A: faster delivery", "Lower cost", "Good for rapid validation"]
        slide["right"] = ["Option B: better scalability", "Higher upfront cost", "Better for long-term buildout"]
        slide["bullets"] = []
    if target_layout == "two-column":
        slide["left"] = ["Current issues", "Core blockers", "Impact scope"]
        slide["right"] = ["Response strategy", "Expected impact", "Execution needs"]
        slide["bullets"] = []
    if target_layout == "summary":
        slide["bullets"] = ["Key point 1: focus the goal", "Key point 2: tighten the message", "Key point 3: clarify execution"]
    return True


def compress_deck(deck: Dict[str, Any], target_count: int) -> None:
    slides = deck.get("slides", [])
    if len(slides) <= target_count:
        return
    while len(slides) > target_count:
        removable_index = next(
            (
                index
                for index, slide in enumerate(slides)
                if 1 < index < len(slides) - 1 and slide.get("layout") != "closing"
            ),
            None,
        )
        if removable_index is None:
            break
        removed = slides.pop(removable_index)
        merge_target = slides[max(1, removable_index - 1)]
        extra_bullets = []
        if removed.get("title"):
            extra_bullets.append(f"Added: {removed['title']}")
        if isinstance(removed.get("bullets"), list):
            extra_bullets.extend(removed["bullets"][:2])
        merge_target["bullets"] = (merge_target.get("bullets") or []) + extra_bullets
        merge_target["bullets"] = merge_target["bullets"][:5]
        merge_target["objective"] = "Combined key points after slide compression"


def emphasize_execution_plan(deck: Dict[str, Any]) -> None:
    slides = deck.get("slides", [])
    slide = next((item for item in slides if re.search(r"execution|implementation|plan", item.get("title", ""), re.IGNORECASE)), None)
    if slide is None:
        insert_index = max(1, len(slides) - 1)
        slide = empty_slide(insert_index + 1, "process", "Execution plan")
        slides.insert(insert_index, slide)
    slide["layout"] = "timeline" if slide.get("layout") == "timeline" else "process"
    slide["title"] = "Execution plan"
    slide["objective"] = "Break the work into concrete execution steps"
    slide["bullets"] = [
        "Set priorities and owners",
        "Deliver in clear phases",
        "Track weekly progress and escalate risks",
        "Review outcomes at each milestone",
    ]
    slide["speakerNotes"] = ["Emphasize that this slide is about execution, not abstract vision."]


def make_more_conclusion_driven(deck: Dict[str, Any]) -> None:
    slides = deck.get("slides", [])
    summary_index = next(
        (
            index
            for index, slide in enumerate(slides)
            if slide.get("layout") == "summary"
            or re.search(r"summary|recommendation|conclusion", slide.get("title", ""), re.IGNORECASE)
        ),
        None,
    )
    summary_slide = slides.pop(summary_index) if summary_index is not None else empty_slide(2, "summary", "Key conclusions")
    summary_slide["layout"] = "summary"
    summary_slide["title"] = "Key conclusions"
    summary_slide["objective"] = "Lead with the conclusions before supporting detail"
    if not summary_slide.get("bullets"):
        summary_slide["bullets"] = [
            "Focus on the highest-value priorities",
            "Put execution before supporting detail",
            "Tie resource requests to goals",
        ]
    slides.insert(1, summary_slide)


def apply_heuristic_revision(existing_deck: Dict[str, Any], prompt: str, context_texts: List[str]) -> Dict[str, Any]:
    cloned = json.loads(json.dumps(existing_deck))
    if not isinstance(cloned.get("slides"), list):
        fail("existingDeck is required for mock revision mode.")
    cloned["sourceDisplayMode"] = cloned.get("sourceDisplayMode") or "notes"
    cloned["assumptions"] = cloned.get("assumptions") if isinstance(cloned.get("assumptions"), list) else []
    cloned["assumptions"].append(f"Updated for revision request: {prompt}")
    if context_texts:
        cloned["assumptions"].append(f"Revision used {len(context_texts)} additional context item(s).")

    apply_requested_theme(cloned, prompt)
    handled_specific_page = apply_page_specific_revision(cloned, prompt)
    if not handled_specific_page and cloned["slides"]:
        target_index = min(2, len(cloned["slides"]) - 1)
        target_slide = cloned["slides"][target_index]
        target_slide["objective"] = "Reflect the latest revision request"
        target_slide["speakerNotes"] = [f"Revision request: {prompt}"]
        if context_texts:
            target_slide["bullets"] = (target_slide.get("bullets") or []) + [f"Additional context sources considered: {len(context_texts)}"]
            target_slide["bullets"] = target_slide["bullets"][:5]

    if re.search(r"conclusion", prompt, re.IGNORECASE):
        make_more_conclusion_driven(cloned)
    if re.search(r"execution plan|implementation", prompt, re.IGNORECASE):
        emphasize_execution_plan(cloned)

    target_count = requested_slide_count(prompt)
    if target_count:
        compress_deck(cloned, target_count)

    normalize_closing_slide(cloned)
    renumber_slides(cloned)
    return cloned


def maybe_run_research(user_prompt: str) -> List[str]:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.debug("TAVILY_API_KEY not set, skipping research")
        return []
    logger.info("Running Tavily research for prompt")
    payload = json.dumps(
        {
            "api_key": api_key,
            "query": user_prompt,
            "search_depth": "advanced",
            "max_results": 5,
            "include_answer": True,
        }
    ).encode("utf-8")
    request = Request(
        "https://api.tavily.com/search",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            fail(f"Tavily request failed with status {response.status}")
        data = json.loads(response.read().decode("utf-8"))
    notes: List[str] = []
    if data.get("answer"):
        notes.append(f"Research summary: {data['answer']}")
    for index, result in enumerate(data.get("results", [])[:5], start=1):
        notes.append(f"Source {index}: {result.get('title', 'Untitled')} - {result.get('url', '')}")
        if result.get("content"):
            notes.append(f"Source {index} note: {result['content'][:300]}")
    return notes


def create_openai_client() -> Any:
    OpenAI = importlib.import_module("openai").OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        fail("OPENAI_API_KEY is not set. Use mock mode for offline testing or configure the API key.")
    base_url = os.getenv("OPENAI_BASE_URL")
    return OpenAI(api_key=api_key, base_url=base_url or None)


def request_deck_json(provider: LLMProvider, system_prompt: str, user_prompt: str) -> str:
    return provider.chat(system_prompt, user_prompt)

def execute_planning_flow(
    prompt: str,
    context_texts: List[str] | None = None,
    loaded_sources: List[Dict[str, Any]] | None = None,
    research_enabled: bool = False,
    mock: bool = False,
    mode: str = "create",
    existing_deck: Dict[str, Any] | None = None,
    llm_provider: LLMProvider | None = None,
) -> Dict[str, Any]:
    contexts = context_texts or []
    sources = loaded_sources or []
    schema = load_schema()
    validator = create_validator(schema)
    research_notes = maybe_run_research(prompt) if research_enabled else []

    logger.info("execute_planning_flow: mode=%s, mock=%s, sources=%d, contexts=%d", mode, mock, len(sources), len(contexts))

    if mock:
        if mode == "create":
            deck = normalize_deck_source_metadata(build_mock_deck(prompt, research_notes, contexts, sources), sources)
        else:
            if existing_deck is None:
                fail("existingDeck is required for revise mode.")
            deck = normalize_deck_source_metadata(apply_heuristic_revision(existing_deck, prompt, contexts), sources)
        # Validate chart data and apply fallbacks
        chart_fallbacks = validate_chart_slides(deck)
        if chart_fallbacks:
            deck.setdefault("assumptions", []).extend(chart_fallbacks)
        errors = sorted(validator.iter_errors(deck), key=lambda error: list(error.path))
        if errors:
            fail(f"Generated deck failed schema validation: {format_validation_errors(errors)}")
        return deck

    skill_instructions = load_skill_instructions()
    system_prompt = build_system_prompt(skill_instructions, schema)
    provider = llm_provider or get_default_provider()
    base_prompt = (
        build_create_prompt(prompt, contexts, research_notes)
        if mode == "create"
        else build_revise_prompt(existing_deck or {}, prompt, contexts, research_notes)
    )
    raw_json = request_deck_json(provider, system_prompt, base_prompt)

    for attempt in range(MAX_REPAIR_ATTEMPTS + 1):
        try:
            parsed = json.loads(extract_json(raw_json))
        except json.JSONDecodeError as error:
            if attempt == MAX_REPAIR_ATTEMPTS:
                raise
            raw_json = request_deck_json(provider, system_prompt, build_repair_prompt(prompt, raw_json, f"JSON parse error: {error}"))
            continue

        normalized = normalize_deck_source_metadata(parsed, sources)
        # Validate chart data and apply fallbacks before schema check
        chart_fallbacks = validate_chart_slides(normalized)
        if chart_fallbacks:
            normalized.setdefault("assumptions", []).extend(chart_fallbacks)
        errors = sorted(validator.iter_errors(normalized), key=lambda item: list(item.path))
        if not errors:
            return normalized
        if attempt == MAX_REPAIR_ATTEMPTS:
            fail(f"Schema validation failed: {format_validation_errors(errors)}")
        raw_json = request_deck_json(
            provider,
            system_prompt,
            build_repair_prompt(prompt, json.dumps(normalized), format_validation_errors(errors)),
        )

    fail("Unable to produce a valid deck JSON.")
