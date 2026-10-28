import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

df = pd.read_csv("analysis.csv")
INK, MUTED, GREY, TEAL, ORANGE, PURPLE = "#1f2937", "#6b7280", "#c3c9d4", "#0F766E", "#B45309", "#7C3AED"
plt.rcParams["font.family"] = "DejaVu Sans"

fig, ax = plt.subplots(figsize=(12, 7), dpi=200)
ax.set_xscale("log"); ax.set_xlim(70, 12000); ax.set_ylim(0, 75)
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
for sp in ("left", "bottom"): ax.spines[sp].set_color("#9ca3af")
ax.grid(axis="y", color="#eceff3", lw=1); ax.set_axisbelow(True)
ax.xaxis.set_major_locator(FixedLocator([100, 300, 1000, 3000, 10000]))
ax.xaxis.set_minor_locator(NullLocator())
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:,.0f}"))
ax.tick_params(colors=MUTED, length=0, labelsize=10.5)
ax.set_yticks(range(0, 71, 10))
ax.set_yticklabels([f"{v}%" for v in range(0, 71, 10)])

# Pareto frontier (step: best result available at each budget)
pts = df.sort_values(["cost", "resolution_rate"], ascending=[True, False])
fx, fy, best = [], [], -1
for _, r in pts.iterrows():
    if r.resolution_rate > best:
        fx.append(r.cost); fy.append(r.resolution_rate); best = r.resolution_rate
ax.step(fx, fy, where="post", color=TEAL, ls="--", lw=1.8, alpha=.8, zorder=2)

ax.scatter(df.cost, df.resolution_rate, s=45, color=GREY, zorder=3)

def hi(model, color, size=130):
    r = df[df.model == model].iloc[0]
    ax.scatter(r.cost, r.resolution_rate, s=size, color=color, zorder=5, edgecolor="white", lw=1.5)
    return r

def label(model, color, text, dx, dy, ha="left"):
    r = hi(model, color)
    ax.annotate(text, (r.cost, r.resolution_rate), xytext=(r.cost * dx, r.resolution_rate + dy),
                fontsize=10.5, color=INK, ha=ha, va="center", linespacing=1.35)

label("Opus 5.5", ORANGE, "Opus 5.5 · Claude Code\n64.8% · ~$4,700 (leader)", 1.0, 7, "center")
label("GPT-6.1 Sol", PURPLE, "GPT-6.1 Sol · Codex\n58.2% · ~$600", 0.88, 5, "right")
label("GPT-6 Astra", GREY, "GPT-6 Astra · Codex\n58.2% · ~$3,300", 0.92, 5.2, "right")
label("GLM-5.3-Flash", TEAL, "GLM-5.3-Flash · Claude Code\n35.8% · ~$100", 1.25, 5)

# headline callout
ax.annotate("", xy=(600, 56), xytext=(4700, 56), arrowprops=dict(arrowstyle="<->", color=MUTED, lw=1))
ax.text(1680, 54.2, "~90% of the score, ~8× cheaper", ha="center", va="top", fontsize=10, color=MUTED, style="italic")

ax.set_xlabel("Reported total run cost (USD, log scale)", fontsize=11, color=MUTED, labelpad=10)
ax.set_ylabel("Resolution rate", fontsize=11, color=MUTED, labelpad=10)
fig.text(0.065, 0.945, "90% of the score at 13% of the cost", fontsize=19, fontweight="bold", color=INK, ha="left")
fig.text(0.065, 0.903, "Terminal-Bench 4.0: resolution rate vs. total evaluation cost. Dashed line = best result at each budget.",
         fontsize=11, color=MUTED, ha="left")
fig.text(0.065, 0.015, "Source: Terminal-Bench 4.0 public leaderboard (Snorkel AI table), retrieved 2026-10-29. Costs are rounded published \\$k run totals "
         "(\\$0.1k could be \\$50–\\$150).\nThe entry with no published cost is excluded. Configurations differ in model, agent and effort. See methodology.md.",
         fontsize=8.3, color=MUTED, va="bottom")
fig.subplots_adjust(left=0.065, right=0.97, top=0.87, bottom=0.17)
fig.savefig("chart.png")