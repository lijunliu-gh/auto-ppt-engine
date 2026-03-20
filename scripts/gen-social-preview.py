"""Generate GitHub social preview image (1280x640) for auto-ppt-prototype."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1280, 640
img = Image.new("RGB", (W, H), "#0f172a")  # dark navy background
draw = ImageDraw.Draw(img)

# --- Gradient accent bar at top ---
for y in range(6):
    draw.line([(0, y), (W, y)], fill="#3b82f6")

# --- Helper: try system fonts, fall back to default ---
def get_font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/SFPro-Bold.otf" if bold else "/System/Library/Fonts/SFPro-Regular.otf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
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
font_url = get_font(15)
font_flow = get_font(20, bold=True)
font_version = get_font(14, bold=True)

# --- Title ---
draw.text((60, 50), "Auto PPT Prototype", fill="#ffffff", font=font_title)

# --- Version badge ---
vx = 60
vy = 115
draw.rounded_rectangle([(vx, vy), (vx + 68, vy + 24)], radius=4, fill="#3b82f6")
draw.text((vx + 10, vy + 3), "v0.7.0", fill="#ffffff", font=font_version)

# --- Subtitle ---
draw.text((60, 155), "AI-agent-ready PowerPoint backend for planning,", fill="#94a3b8", font=font_subtitle)
draw.text((60, 183), "revising, and rendering PPTX decks from natural-language prompts.", fill="#94a3b8", font=font_subtitle)

# --- Flow diagram ---
flow_y = 250
colors_flow = ["#f59e0b", "#94a3b8", "#94a3b8", "#94a3b8", "#22c55e"]
labels = ["Prompt", "→", "Deck JSON", "→", "PPTX"]
x = 60
for i, (label, color) in enumerate(zip(labels, colors_flow)):
    draw.text((x, flow_y), label, fill=color, font=font_flow)
    bbox = draw.textbbox((x, flow_y), label, font=font_flow)
    x = bbox[2] + 18

# --- Feature columns ---
col1_x, col2_x = 60, 440
feat_y_start = 320
col_label_color = "#3b82f6"
feat_color = "#e2e8f0"
bullet_color = "#f59e0b"

# Column 1: Interfaces
draw.text((col1_x, feat_y_start), "INTERFACES", fill=col_label_color, font=font_label)
features_1 = [
    "MCP Server (stdio + remote HTTP)",
    "CLI for generate & revise",
    "HTTP skill endpoint",
    "JSON agent workflow",
]
for i, feat in enumerate(features_1):
    y = feat_y_start + 30 + i * 30
    draw.text((col1_x, y), "●", fill=bullet_color, font=font_feature)
    draw.text((col1_x + 20, y), feat, fill=feat_color, font=font_feature)

# Column 2: Capabilities
draw.text((col2_x, feat_y_start), "CAPABILITIES", fill=col_label_color, font=font_label)
features_2 = [
    "Trusted source ingestion (PDF, DOCX, URL)",
    "Chart auto-repair & validation",
    "Brand template engine (.pptx)",
    "Image pipeline & placeholder protocol",
]
for i, feat in enumerate(features_2):
    y = feat_y_start + 30 + i * 30
    draw.text((col2_x, y), "●", fill=bullet_color, font=font_feature)
    draw.text((col2_x + 20, y), feat, fill=feat_color, font=font_feature)

# Column 3: Ecosystem
col3_x = 870
draw.text((col3_x, feat_y_start), "ECOSYSTEM", fill=col_label_color, font=font_label)
features_3 = [
    "5 LLM providers supported",
    "Docker one-command deploy",
    "263 tests, 84% coverage",
    "EN / JA / ZH-CN docs",
]
for i, feat in enumerate(features_3):
    y = feat_y_start + 30 + i * 30
    draw.text((col3_x, y), "●", fill=bullet_color, font=font_feature)
    draw.text((col3_x + 20, y), feat, fill=feat_color, font=font_feature)

# --- Divider line ---
draw.line([(60, 530), (W - 60, 530)], fill="#334155", width=1)

# --- Bottom bar ---
draw.text((60, 555), "github.com/lijunliu-gh/auto-ppt-prototype", fill="#64748b", font=font_url)

# Right side: agent compatibility
draw.text((700, 555), "Works with Claude Desktop · Cursor · Windsurf · any MCP client", fill="#64748b", font=font_url)

# --- Subtle corner accents ---
# Top-right accent circle
draw.ellipse([(W - 120, -40), (W + 40, 120)], fill="#1e3a5f", outline=None)
# Bottom-left accent
draw.ellipse([(-60, H - 100), (60, H + 20)], fill="#1e3a5f", outline=None)

out_path = os.path.join(os.path.dirname(__file__), "..", "assets", "social-preview.png")
img.save(out_path, "PNG")
print(f"Saved to {out_path}")
