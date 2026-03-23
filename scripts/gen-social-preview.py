"""Generate GitHub social preview image (1280x640) for auto-ppt-engine."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1280, 640
MARGIN = 60
img = Image.new("RGB", (W, H), "#0f172a")  # dark navy background
draw = ImageDraw.Draw(img)

# --- Subtle corner accents (draw FIRST so text is on top) ---
draw.ellipse([(W - 120, -40), (W + 40, 120)], fill="#1e3a5f", outline=None)
draw.ellipse([(-60, H - 100), (60, H + 20)], fill="#1e3a5f", outline=None)

# --- Gradient accent bar at top ---
for y in range(6):
    draw.line([(0, y), (W, y)], fill="#3b82f6")

# --- Helper: try system fonts, fall back to default ---
def get_font(size, bold=False):
    candidates = [
        # San Francisco — the actual macOS system font
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/SFNSMono.ttf" if bold else "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

font_title = get_font(52, bold=True)
font_subtitle = get_font(22)
font_label = get_font(16, bold=True)
font_feature = get_font(18)
font_url = get_font(16)
font_flow = get_font(20, bold=True)

# --- Title ---
draw.text((MARGIN, 50), "Auto PPT Engine", fill="#ffffff", font=font_title)

# --- Subtitle ---
draw.text((MARGIN, 125), "AI-agent-ready PowerPoint backend for planning,", fill="#94a3b8", font=font_subtitle)
draw.text((MARGIN, 153), "revising, and rendering PPTX decks from natural-language prompts.", fill="#94a3b8", font=font_subtitle)

# --- Flow diagram ---
flow_y = 240

def draw_arrow(draw, x, y, color="#94a3b8"):
    draw.line([(x, y + 10), (x + 20, y + 10)], fill=color, width=2)
    draw.polygon([(x + 20, y + 4), (x + 30, y + 10), (x + 20, y + 16)], fill=color)

flow_labels = [("Prompt", "#f59e0b"), ("Deck JSON", "#94a3b8"), ("PPTX", "#22c55e")]
x = MARGIN
for i, (label, color) in enumerate(flow_labels):
    draw.text((x, flow_y), label, fill=color, font=font_flow)
    bbox = draw.textbbox((x, flow_y), label, font=font_flow)
    x = bbox[2] + 14
    if i < len(flow_labels) - 1:
        draw_arrow(draw, x, flow_y + 2)
        x += 44

# --- Feature columns (evenly spaced) ---
content_w = W - MARGIN * 2  # 1160
col_w = content_w // 3      # ~386 each
col1_x = MARGIN
col2_x = MARGIN + col_w
col3_x = MARGIN + col_w * 2
feat_y_start = 310
row_h = 32
col_label_color = "#3b82f6"
feat_color = "#e2e8f0"
bullet_color = "#f59e0b"

# Column 1: Interfaces
draw.text((col1_x, feat_y_start), "INTERFACES", fill=col_label_color, font=font_label)
features_1 = [
    "MCP Server (stdio + remote HTTP)",
    "CLI (generate, revise, score, QA)",
    "HTTP skill endpoint",
    "JSON agent workflow",
]
for i, feat in enumerate(features_1):
    y = feat_y_start + 30 + i * row_h
    draw.text((col1_x, y), "●", fill=bullet_color, font=font_feature)
    draw.text((col1_x + 20, y), feat, fill=feat_color, font=font_feature)

# Column 2: Capabilities
draw.text((col2_x, feat_y_start), "CAPABILITIES", fill=col_label_color, font=font_label)
features_2 = [
    "12+ source formats (PDF … CSV)",
    "Chart auto-repair & validation",
    "Brand template engine (.pptx)",
    "Image pipeline & placeholders",
]
for i, feat in enumerate(features_2):
    y = feat_y_start + 30 + i * row_h
    draw.text((col2_x, y), "●", fill=bullet_color, font=font_feature)
    draw.text((col2_x + 20, y), feat, fill=feat_color, font=font_feature)

# Column 3: Ecosystem
draw.text((col3_x, feat_y_start), "ECOSYSTEM", fill=col_label_color, font=font_label)
features_3 = [
    "8+ LLM providers supported",
    "Docker one-command deploy",
    "365 tests across CI matrix",
    "EN / JA / ZH-CN docs",
]
for i, feat in enumerate(features_3):
    y = feat_y_start + 30 + i * row_h
    draw.text((col3_x, y), "●", fill=bullet_color, font=font_feature)
    draw.text((col3_x + 20, y), feat, fill=feat_color, font=font_feature)

# --- Divider line ---
draw.line([(MARGIN, 540), (W - MARGIN, 540)], fill="#475569", width=1)

# --- Bottom bar (brighter text for readability) ---
bottom_y = 560
bottom_color = "#94a3b8"  # was #64748b — much more visible now
draw.text((MARGIN, bottom_y), "github.com/lijunliu-gh/auto-ppt-engine", fill=bottom_color, font=font_url)

# Right-align agent compatibility text
right_text = "Works with Claude Desktop · Cursor · Windsurf · any MCP client"
bbox = draw.textbbox((0, 0), right_text, font=font_url)
text_w = bbox[2] - bbox[0]
draw.text((W - MARGIN - text_w, bottom_y), right_text, fill=bottom_color, font=font_url)

out_path = os.path.join(os.path.dirname(__file__), "..", "assets", "social-preview.png")
img.save(out_path, "PNG")
print(f"Saved to {out_path}")
