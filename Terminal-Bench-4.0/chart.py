import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("analysis.csv")
df["label"] = df.model + "\n" + df.agent + " · " + df.effort
GREY, TEAL, ORANGE, BLUE, GOLD = "#8791A3", "#0F766E", "#B45309", "#2563EB", "#7C3AED"

fig, ax = plt.subplots(figsize=(12.5, 7.6), dpi=200)
ax.set_xscale("log"); ax.set_xlim(65, 13500); ax.set_ylim(0, 72)
ax.grid(True, color="#ddd", ls=":", lw=.8); ax.set_axisbelow(True)

# Pareto frontier (step: best result available at a given budget)
pts = df.sort_values(["cost", "resolution_rate"], ascending=[True, False])
front, best = [], -1
for _, r in pts.iterrows():
    if r.resolution_rate > best:
        front.append(r); best = r.resolution_rate
fx = [r.cost for r in front]; fy = [r.resolution_rate for r in front]
ax.step(fx, fy, where="post", color=TEAL, ls="--", lw=2.4, label="Value frontier (step)")

ax.scatter(df.cost, df.resolution_rate, s=60, color=GREY, zorder=3)

def mark(model, color, marker="o", s=150, label=None):
    r = df[df.model == model].iloc[0]
    ax.scatter(r.cost, r.resolution_rate, s=s, color=color, marker=marker, zorder=5, label=label)

mark("Opus 5.5", ORANGE, label="Highest resolution")
mark("GPT-6 Luna", BLUE, label="Lowest cost (tied at ~$100)")
mark("GLM-5.3-Flash", TEAL, "D", 170, "Best cost / point")
mark("GPT-6.1 Sol", GOLD, "s", 130, "Best cost / point among 55%+ resolvers")

def note(model, dx, dy, ha="left"):
    r = df[df.model == model].iloc[0]
    ax.annotate(r.label, (r.cost, r.resolution_rate), xytext=(r.cost * dx, r.resolution_rate + dy),
                fontsize=9.5, ha=ha, va="center", zorder=6,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#ccc"),
                arrowprops=dict(arrowstyle="-", color="#999", lw=.8))
note("Opus 5.5", 0.72, 4.5, "right")
note("Sonnet 5.5", 0.95, -9, "left")
note("GPT-6.1 Sol", 1.15, -6.5)
note("GPT-6 Astra", 1.15, -6.5)
note("GLM-5.3-Flash", 1.35, 4.5)
note("GPT-6 Luna", 1.35, -4.5)

ax.set_xlabel("Reported total run cost (USD, log scale; rounded $k)", fontsize=12)
ax.set_ylabel("Resolution rate (%)", fontsize=12)
ax.set_title("Higher resolution rate does not mean better value.", loc="left", fontsize=17, fontweight="bold", pad=14)
ax.legend(loc="lower right", frameon=False, fontsize=10)
fig.text(0.01, 0.012, "Source: Terminal-Bench 4.0 public leaderboard (Snorkel AI table), retrieved 2026-10-29. Costs are rounded published \\$k run totals\n"
         "(a \\$0.1k entry could be \\$50–\\$150); the entry with no published cost is excluded. See methodology.md.", fontsize=8.5, color="#444", va="bottom")
fig.tight_layout(rect=(0, 0.05, 1, 1))
fig.savefig("chart.png")
