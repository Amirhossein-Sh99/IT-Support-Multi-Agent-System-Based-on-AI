"""
One-off script to generate architecture_diagram.png for the README and the
Kaggle Writeup's required cover image. Not part of the runtime application -
run manually if the diagram ever needs regenerating:

    python tools/generate_diagram.py
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

INK = "#101820"
MUTED = "#647080"
ACCENT = "#0F7A73"
ACCENT_SOFT = "#E1F1EE"
AMBER = "#A8630A"
AMBER_SOFT = "#FBEEDC"
SURFACE = "#FFFFFF"
BORDER = "#DCE1E7"
BG = "#EEF1F4"

fig, ax = plt.subplots(figsize=(12, 6.2), dpi=200)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 12)
ax.set_ylim(0, 6.2)
ax.axis("off")


def box(x, y, w, h, label, sublabel=None, face=SURFACE, edge=BORDER, text_color=INK, bold=True, fontsize=11.5):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=1.4, edgecolor=edge, facecolor=face, zorder=2,
    )
    ax.add_patch(patch)
    if sublabel:
        ax.text(x + w / 2, y + h * 0.62, label, ha="center", va="center",
                 fontsize=fontsize, fontweight="bold" if bold else "normal", color=text_color, zorder=3)
        ax.text(x + w / 2, y + h * 0.28, sublabel, ha="center", va="center",
                 fontsize=fontsize * 0.72, color=MUTED, zorder=3)
    else:
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                 fontsize=fontsize, fontweight="bold" if bold else "normal", color=text_color, zorder=3)
    return (x, y, w, h)


def arrow(x1, y1, x2, y2, color=MUTED, style="-|>", lw=1.6, connectionstyle="arc3,rad=0.0"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14,
                         color=color, linewidth=lw, zorder=1, connectionstyle=connectionstyle)
    ax.add_patch(a)


# Title
ax.text(0.15, 5.85, "IT-Support Multi-Agent System", fontsize=17, fontweight="bold", color=INK, ha="left")
ax.text(0.15, 5.5, "Triage \u2192 Diagnostics \u2192 Documentation \u00b7 Google ADK + Gemini + MCP", fontsize=10.5, color=MUTED, ha="left")

# User
user = box(0.3, 4.1, 1.5, 0.8, "User", "raw ticket")

# Triage
triage = box(2.4, 4.1, 2.0, 0.8, "Triage Agent", "category + urgency", face=ACCENT_SOFT, edge=ACCENT)

# Diagnostics
diag = box(5.0, 4.1, 2.4, 0.8, "Diagnostics Agent", "PLAN \u2192 ACT \u2192 EVALUATE", face=ACCENT_SOFT, edge=ACCENT)

# Documentation
doc = box(8.0, 4.1, 2.6, 0.8, "Documentation Agent", "bilingual EN/DE report", face=ACCENT_SOFT, edge=ACCENT)

arrow(1.8, 4.5, 2.4, 4.5)
arrow(4.4, 4.5, 5.0, 4.5)
arrow(7.4, 4.5, 8.0, 4.5)

# MCP server (below diagnostics)
mcp = box(4.5, 2.5, 2.0, 0.9, "MCP Server", "network_check\ntraceroute \u00b7 search_logs\nservice_status", face=SURFACE, edge=INK, fontsize=10)
arrow(5.6, 4.1, 5.6, 3.4, color=INK, connectionstyle="arc3,rad=0.3")
arrow(5.6, 3.4, 6.0, 4.1, color=INK, connectionstyle="arc3,rad=-0.3")

# Security allow-list (below MCP)
sec = box(4.5, 1.1, 2.0, 0.9, "Security", "structural allow-list\n(runs before every call)", face="#FDEDEA", edge="#B23A2E", fontsize=10)
arrow(5.5, 2.5, 5.5, 2.0, color="#B23A2E")

# Agent Skill (right of MCP)
skill = box(6.9, 2.5, 2.1, 0.9, "Agent Skill", "it_diagnostics_skill/\nskill.md \u2014 procedure,\nnot tools", face=SURFACE, edge=INK, fontsize=10)
arrow(6.7, 4.1, 7.4, 3.4, color=INK, connectionstyle="arc3,rad=0.3")

# Memory (below/left of diagnostics)
mem = box(2.0, 2.5, 2.2, 0.9, "Memory", "long-term: past tickets\nshort-term: session state", face=SURFACE, edge=INK, fontsize=10)
arrow(5.0, 4.1, 3.4, 3.4, color=INK, connectionstyle="arc3,rad=-0.3")
arrow(3.4, 3.4, 3.4, 4.1, color=INK, connectionstyle="arc3,rad=0.3", style="-")

# Ops Dashboard (bottom, receiving from memory)
dash = box(1.0, 0.25, 4.0, 0.7, "Ops Dashboard", "ticket queue + charts (Streamlit UI)", face=AMBER_SOFT, edge=AMBER, fontsize=10.5)
arrow(3.0, 2.5, 3.0, 0.95, color=AMBER, connectionstyle="arc3,rad=0.0")

# Final report out
report = box(9.4, 2.5, 2.0, 0.9, "Resolution\nReport", "EN \u00b7 DE \u00b7 Knowledge Base", face=AMBER_SOFT, edge=AMBER, fontsize=10.5)
arrow(9.3, 4.1, 10.3, 3.4, color=AMBER, connectionstyle="arc3,rad=0.2")

plt.tight_layout()
plt.savefig("examples/architecture_diagram.png", facecolor=BG, bbox_inches="tight")
print("Saved to examples/architecture_diagram.png")
