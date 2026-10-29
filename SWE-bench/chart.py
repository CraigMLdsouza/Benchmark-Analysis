import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("scaffold_comparison.csv").sort_values("resolved_pct")
INK, MUTED, GREY, ORANGE, TEAL = "#1f2937", "#6b7280", "#c3c9d4", "#B45309", "#0F766E"
fig, ax = plt.subplots(figsize=(12, 6.8), dpi=200)
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
for sp in ("left", "bottom"): ax.spines[sp].set_color("#9ca3af")
ax.grid(axis="x", color="#eceff3", lw=1); ax.set_axisbelow(True)

low, high = df.resolved_pct.min(), df.resolved_pct.max()
colors = [ORANGE if v == low else TEAL if v == high else GREY for v in df.resolved_pct]
bars = ax.barh(df.scaffold, df.resolved_pct, color=colors, height=.62, zorder=3)
for b, (_, r) in zip(bars, df.iterrows()):
    ax.text(r.resolved_pct + .8, b.get_y() + b.get_height()/2, f"{r.resolved_pct:.1f}%  ({r.resolved_tasks}/500)",
            va="center", fontsize=10.5, color=INK, zorder=4)

# bracket over the five-scaffold cluster
cl = df[df.resolved_pct > low].resolved_pct
y = 5.5
ax.plot([cl.min(), cl.min(), cl.max(), cl.max()], [y-.12, y, y, y-.12], color=MUTED, lw=1.4)
ax.text((cl.min()+cl.max())/2, y+.12, f"Five of six scaffolds sit within {cl.max()-cl.min():.1f} points", ha="center", fontsize=10.5, color=MUTED, style="italic")

ax.set_xlim(0, 70); ax.set_ylim(-.6, 6.1)
ax.set_xticks(range(0, 61, 10)); ax.set_xticklabels([f"{v}%" for v in range(0, 61, 10)])
ax.tick_params(colors=MUTED, length=0, labelsize=10.5); ax.tick_params(axis="y", colors=INK)
ax.set_xlabel("SWE-bench Verified tasks resolved (500 tasks)", fontsize=11, color=MUTED, labelpad=10)
fig.text(0.04, 0.945, "Same model family, 20 points apart", fontsize=19, fontweight="bold", color=INK)
fig.text(0.04, 0.903, "Published Claude 3.5 Sonnet results on SWE-bench Verified, by agent scaffold. The gap comes mostly from one setup.",
         fontsize=11, color=MUTED)
fig.text(0.04, 0.015, "Source: published comparison table (preprint); OpenHands row cross-checked with the SWE-bench leaderboard. Not a controlled experiment: model snapshot, prompts,\n"
         "tools, budgets and retries may differ across submissions, and the lowest row may use an older model snapshot. See methodology.md.", fontsize=8.3, color=MUTED, va="bottom")
fig.subplots_adjust(left=0.2, right=0.97, top=0.86, bottom=0.17)
fig.savefig("chart.png")