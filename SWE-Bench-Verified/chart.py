
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ALL_MODELS = "--all-models" in sys.argv

CORE = [
    "claude-opus-5.5-cc",
    "claude-fable-5.1-cc",
    "qwen3.8-flash-next",
    "deepseek-v4-pro",
    "deepseek-v4-flash",
    "kimi-k3",
    "kimi-k2.7",
    "glm-5.3-flash",
    "glm-5.3",
    "qwen3.8-27b",
]

A = "qwen3.8-flash-next"
B = "claude-opus-5.5-cc"

df = pd.read_csv("chart_data.csv")
valid = df.dropna(subset=["cost_per_solve_usd"]).copy()

plot_df = valid if ALL_MODELS else valid[valid.model.isin(CORE)].copy()

if plot_df.empty:
    sys.exit("No models found for the chart. Check chart_data.csv and CORE.")

# Pareto frontier among all matched configurations
def pareto(frame):
    keep = []

    for _, r in frame.iterrows():
        dominated = (
            (frame.cost_per_solve_usd <= r.cost_per_solve_usd)
            & (frame.resolve_rate_pct >= r.resolve_rate_pct)
            & (
                (frame.cost_per_solve_usd < r.cost_per_solve_usd)
                | (frame.resolve_rate_pct > r.resolve_rate_pct)
            )
        ).any()

        keep.append(not dominated)

    return frame[keep]


frontier = pareto(valid)
front_set = set(frontier.model)

# Theme
BG = "#0b0f19"
PANEL = "#111827"
GRID = "#1f2937"
TXT = "#e5e7eb"
MUTED = "#8b95a7"
ACCENT = "#34d399"
WARM = "#fbbf24"
DIM = "#475569"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "text.color": TXT,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "text.parse_math": False,
})


def style_axis(ax):
    ax.set_facecolor(PANEL)

    for spine in ax.spines.values():
        spine.set_color(GRID)


# Shared headline metrics
if A not in valid.model.values or B not in valid.model.values:
    sys.exit(f"Could not find both comparison models ({A}, {B}) in chart_data.csv.")

a = valid.set_index("model").loc[A]
b = valid.set_index("model").loc[B]
ratio = b.cost_per_solve_usd / a.cost_per_solve_usd


# ============================================================
# CHART 1: Cost per solved task vs resolution rate
# ============================================================

fig, ax = plt.subplots(figsize=(12, 8), facecolor=BG)
style_axis(ax)

ax.set_xscale("log")
ax.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)

# Pareto frontier line, preserving original logic
fr = plot_df[plot_df.model.isin(front_set)].sort_values(
    "cost_per_solve_usd"
)

if len(fr) > 1:
    ax.step(
        fr.cost_per_solve_usd,
        fr.resolve_rate_pct,
        where="post",
        color=ACCENT,
        linewidth=1.6,
        linestyle="--",
        alpha=0.55,
    )

placed = []

for _, r in plot_df.sort_values(
    "resolve_rate_pct", ascending=False
).iterrows():

    on_front = r.model in front_set
    colour = ACCENT if on_front else (WARM if r.model == B else DIM)

    # 95% Wilson confidence intervals
    ax.errorbar(
        r.cost_per_solve_usd,
        r.resolve_rate_pct,
        yerr=[[
            r.resolve_rate_pct - r.ci95_lo_pct
        ], [
            r.ci95_hi_pct - r.resolve_rate_pct
        ]],
        fmt="none",
        ecolor=colour,
        elinewidth=1.2,
        alpha=0.45,
        capsize=3,
        zorder=3,
    )

    # Model point
    ax.scatter(
        r.cost_per_solve_usd,
        r.resolve_rate_pct,
        s=230 if (on_front or r.model == B) else 130,
        color=colour,
        edgecolor=BG,
        linewidth=1.5,
        zorder=4,
        alpha=1 if on_front else 0.9,
    )

    # Glow for Pareto-efficient models
    if on_front:
        ax.scatter(
            r.cost_per_solve_usd,
            r.resolve_rate_pct,
            s=700,
            color=ACCENT,
            alpha=0.10,
            zorder=3,
            linewidth=0,
        )

    # Label placement, preserving original overlap adjustment
    dy = 11

    for px, py in placed:
        if (
            abs(np.log10(r.cost_per_solve_usd) - px) < 0.22
            and abs(r.resolve_rate_pct - py) < 4.5
        ):
            dy -= 17

    placed.append((
        np.log10(r.cost_per_solve_usd),
        r.resolve_rate_pct + dy / 4,
    ))

    ax.annotate(
        r.model,
        (r.cost_per_solve_usd, r.resolve_rate_pct),
        textcoords="offset points",
        xytext=(12, dy),
        fontsize=9.5,
        color=TXT if (on_front or r.model == B) else MUTED,
        fontweight="bold" if (on_front or r.model == B) else "normal",
        zorder=5,
    )

ax.xaxis.set_major_formatter(
    FuncFormatter(lambda v, _: f"${v:g}")
)
ax.yaxis.set_major_formatter(
    FuncFormatter(lambda v, _: f"{v:.0f}%")
)

ax.set_xlabel(
    "Cost per solved task (log scale, lower is better)",
    labelpad=10,
)
ax.set_ylabel("Resolution rate", labelpad=10)

ax.set_ylim(
    max(0, plot_df.ci95_lo_pct.min() - 6),
    min(100, plot_df.ci95_hi_pct.max() + 6),
)

ax.text(
    0.985,
    0.025,
    "Green = Pareto-efficient · Amber = Opus · Bars = 95% Wilson CI",
    transform=ax.transAxes,
    color=MUTED,
    fontsize=8,
    ha="right",
)

# Title and subtitle
fig.text(
    0.07,
    0.96,
    "Cost per solved task vs resolution rate",
    fontsize=22,
    fontweight="bold",
    color=TXT,
    ha="left",
)

fig.text(
    0.07,
    0.915,
    f"{A}: {a.resolve_rate_pct:.0f}% at "
    f"${a.cost_per_solve_usd:.2f}/solve · "
    f"{B}: {b.resolve_rate_pct:.0f}% at "
    f"${b.cost_per_solve_usd:.2f}/solve ({ratio:.1f}× the cost)",
    fontsize=11.5,
    color=ACCENT,
    ha="left",
)

fig.text(
    0.07,
    0.88,
    f"SWE-bench Verified · {len(valid)} matched models · "
    "45 common tasks · one run each",
    fontsize=9.5,
    color=MUTED,
    ha="left",
)

fig.text(
    0.975,
    0.015,
    "Source: swebench-verified.jsonl · indicative, small sample",
    fontsize=8.5,
    color=MUTED,
    ha="right",
)

fig.tight_layout(rect=[0.04, 0.045, 0.98, 0.85])
fig.savefig(
    "cost_vs_resolution.png",
    dpi=220,
    facecolor=BG,
    bbox_inches="tight",
)
plt.close(fig)

print("Saved cost_vs_resolution.png")


# ============================================================
# CHART 2: Cost per solve · resolution rate
# ============================================================

bars = plot_df.sort_values("cost_per_solve_usd")
y = np.arange(len(bars))[::-1]

colours = [
    ACCENT if m in front_set else (WARM if m == B else DIM)
    for m in bars.model
]

fig_height = max(7, len(bars) * 0.58)

fig, ax2 = plt.subplots(
    figsize=(12, fig_height),
    facecolor=BG,
)
style_axis(ax2)

ax2.barh(
    y,
    bars.cost_per_solve_usd,
    color=colours,
    height=0.62,
    zorder=3,
)

ax2.set_xscale("log")
ax2.grid(True, axis="x", color=GRID, linewidth=0.8)
ax2.set_axisbelow(True)

ax2.set_yticks(y)
ax2.set_yticklabels(bars.model, fontsize=9.5)

ax2.set_xlim(
    bars.cost_per_solve_usd.min() * 0.55,
    bars.cost_per_solve_usd.max() * 2.4,
)

for yi, (_, r) in zip(y, bars.iterrows()):
    ax2.text(
        r.cost_per_solve_usd * 1.12,
        yi,
        f"${r.cost_per_solve_usd:.2f} · {r.resolve_rate_pct:.0f}%",
        va="center",
        fontsize=9,
        color=TXT,
    )

ax2.xaxis.set_major_formatter(
    FuncFormatter(lambda v, _: f"${v:g}")
)

ax2.set_xlabel(
    "Cost per solved task (log scale)",
    labelpad=10,
)

ax2.tick_params(axis="y", length=0)

ax2.set_title(
    "Cost per solve · resolution rate",
    color=MUTED,
    fontsize=10,
    loc="left",
    pad=12,
)

# Title and subtitle
fig.text(
    0.07,
    0.96,
    "Cost efficiency by model",
    fontsize=22,
    fontweight="bold",
    color=TXT,
    ha="left",
)

fig.text(
    0.07,
    0.915,
    f"{A}: ${a.cost_per_solve_usd:.2f}/solve · "
    f"{B}: ${b.cost_per_solve_usd:.2f}/solve ({ratio:.1f}× the cost)",
    fontsize=11.5,
    color=ACCENT,
    ha="left",
)

fig.text(
    0.07,
    0.88,
    f"SWE-bench Verified · {len(valid)} matched models · "
    "45 common tasks · one run each",
    fontsize=9.5,
    color=MUTED,
    ha="left",
)

fig.text(
    0.975,
    0.015,
    "Source: swebench-verified.jsonl · indicative, small sample",
    fontsize=8.5,
    color=MUTED,
    ha="right",
)

fig.tight_layout(rect=[0.04, 0.045, 0.98, 0.85])
fig.savefig(
    "cost_per_solve.png",
    dpi=220,
    facecolor=BG,
    bbox_inches="tight",
)
plt.close(fig)

print("Saved cost_per_solve.png")
