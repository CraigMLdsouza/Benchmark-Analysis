import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# name, $/1k correct (table), accuracy %, snippet tokens
rows = [
    ("TinyFish", 0.0, 92.0, 441),
    ("SERP (RapidAPI)", 3.13, 96.0, 497),
    ("Perplexity low", 5.14, 97.3, 476),
    ("Linkup fast", 5.17, 96.7, 3022),
    ("Firecrawl", 5.24, 95.3, 678),
    ("Brave LLM Context", 5.32, 94.0, 2064),
    ("Parallel basic", 5.36, 93.3, 2330),
    ("Brave Search", 5.36, 93.3, 817),
    ("Nimble standard", 5.38, 93.0, 2730),
    ("Linkup standard", 5.43, 92.0, 2983),
    ("You core", 5.43, 92.0, 2862),
    ("You highlights", 5.51, 90.7, 2837),
    ("Exa fast", 7.05, 99.3, 1987),
    ("Exa instant", 7.17, 97.7, 2128),
]

P = 3.0  # $ per million input tokens (assumption, swap in your model's rate)

pts = []
for n, c, a, t in rows:
    raw = c * a / 100                      # table column is already price / accuracy
    allin = (raw + t * P / 1000) / (a / 100)
    pts.append((n, allin, a, t))

# Pareto frontier: no other point is both cheaper and more accurate
front = [
    p for p in pts
    if not any(
        q[1] <= p[1] and q[2] >= p[2] and q != p and (q[1] < p[1] or q[2] > p[2])
        for q in pts
    )
]
front = sorted(front, key=lambda p: p[1])

BG, FG, MUT, ACC, DIM = "#0f1419", "#e8eaed", "#8b949e", "#3fb950", "#58a6ff"

fig, ax = plt.subplots(figsize=(12, 12), dpi=110)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

for n, x, y, t in pts:
    isf = any(f[0] == n for f in front)
    ax.scatter(
        x, y, s=t / 3 + 60,
        color=ACC if isf else DIM,
        alpha=0.85 if isf else 0.55,
        edgecolor=FG if isf else "none",
        linewidth=1.2, zorder=3,
    )

ax.plot([f[1] for f in front], [f[2] for f in front],
        color=ACC, lw=1.5, ls="--", alpha=0.7, zorder=2)

off = {
    "TinyFish": (12, -4), "SERP (RapidAPI)": (14, 6), "Perplexity low": (-14, 12),
    "Linkup fast": (14, 10), "Firecrawl": (-14, -22), "Brave LLM Context": (-16, 8),
    "Parallel basic": (-14, -16), "Brave Search": (-10, -26), "Nimble standard": (16, -2),
    "Linkup standard": (14, 12), "You core": (-12, -26), "You highlights": (14, -10),
    "Exa fast": (-12, 12), "Exa instant": (14, -14),
}
for n, x, y, t in pts:
    dx, dy = off[n]
    ax.annotate(
        f"{n}\n{t:,} tok", (x, y), xytext=(dx, dy), textcoords="offset points",
        color=FG, fontsize=10, ha="left" if dx > 0 else "right", va="center", zorder=4,
    )

ax.set_xlabel("All-in cost per 1,000 correct answers  (list price + snippet tokens at $3/M, ÷ accuracy)",
              color=FG, fontsize=12, labelpad=12)
ax.set_ylabel("Extracted-answer accuracy (%)", color=FG, fontsize=12, labelpad=12)
ax.set_xlim(0, 18.5)
ax.set_ylim(89.5, 100.5)
ax.tick_params(colors=MUT, labelsize=11)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"${v:g}"))
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}%"))
for s in ax.spines.values():
    s.set_color("#30363d")
ax.grid(color="#21262d", lw=1, zorder=0)

fig.text(0.06, 0.955, "Your search API has two bills",
         color=FG, fontsize=26, fontweight="bold", ha="left")
fig.text(0.06, 0.925, "Openbenchmarks Company News: accuracy vs all-in cost per correct answer",
         color=MUT, fontsize=13, ha="left")
fig.text(
    0.06, 0.035,
    "Bubble size = snippet tokens per query. Green = no other endpoint is both cheaper and more accurate.\n"
    "Endpoints below 90% accuracy omitted. $3/M input tokens is an assumption.\n"
    "Vendors were benchmarked at different times (flagged by the source), so treat as provisional.\n"
    "Source: Openbenchmarks Company News Search benchmark, 300 questions, 21 endpoints.  Benchmark Teardown #6",
    color=MUT, fontsize=9.5, ha="left", va="bottom", linespacing=1.6,
)

plt.subplots_adjust(left=0.08, right=0.97, top=0.89, bottom=0.17)
fig.savefig("benchmark_teardown_6_chart.png", facecolor=BG)