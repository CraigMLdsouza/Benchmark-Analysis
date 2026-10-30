
import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd

FILE_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("swebench-verified.jsonl")

A = "qwen3.8-flash-next"
B = "claude-opus-5.5-cc"

with FILE_PATH.open("r", encoding="utf-8") as f:
    df = pd.DataFrame(json.loads(line) for line in f if line.strip())

df["cost_usd"] = pd.to_numeric(df["cost_usd"], errors="coerce")
df["resolved"] = df["resolved"].astype(bool)

assert not df.duplicated(["model", "task_id"]).any(), "Duplicate model/task rows"

counts = df.groupby("model").size()
ref_models = counts[counts == 45].index

if len(ref_models) == 0:
    sys.exit("No model has exactly 45 records.")

ref_tasks = set(df[df.model == ref_models[0]].task_id)

for model in ref_models:
    assert set(df[df.model == model].task_id) == ref_tasks, (
        f"{model} has a different 45-task set"
    )

covering = [
    model for model, group in df.groupby("model")
    if ref_tasks <= set(group.task_id)
]

d = df[df.model.isin(covering) & df.task_id.isin(ref_tasks)].copy()

print(f"Loaded {len(df)} runs | {df.model.nunique()} models")
print(f"Matched tasks: {len(ref_tasks)} | Matched models: {len(covering)}")


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / den
    return centre - half, centre + half


rows = []

for model, group in d.groupby("model"):
    success = group[group.resolved]
    failure = group[~group.resolved]

    solved = len(success)
    n = len(group)
    total = group.cost_usd.sum()
    lo, hi = wilson(solved, n)

    rows.append({
        "model": model,
        "tasks": n,
        "solved": solved,
        "failed": n - solved,
        "resolve_rate_pct": 100 * solved / n,
        "ci95_lo_pct": 100 * lo,
        "ci95_hi_pct": 100 * hi,
        "total_cost_usd": total,
        "cost_per_task_usd": total / n,
        "cost_per_solve_usd": total / solved if solved else np.nan,
        "avg_successful_run_cost_usd": (
            success.cost_usd.mean() if solved else np.nan
        ),
        "avg_failed_run_cost_usd": (
            failure.cost_usd.mean() if len(failure) else np.nan
        ),
        "failed_run_cost_share_pct": (
            100 * failure.cost_usd.sum() / total if total else np.nan
        ),
        "solves_per_dollar": solved / total if total else np.nan,
        "avg_steps": group.steps.mean(),
        "avg_wall_min": group.wall_s.mean() / 60,
    })

summary = pd.DataFrame(rows).sort_values(
    "resolve_rate_pct", ascending=False
)

summary.round(4).to_csv("matched_cost_analysis.csv", index=False)

outcomes = d.groupby(["model", "outcome"]).size().unstack(fill_value=0)
outcomes.to_csv("outcomes.csv")


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


valid = summary.dropna(subset=["cost_per_solve_usd"])
frontier = pareto(valid).sort_values("cost_per_solve_usd")

# Paired bootstrap for Qwen vs Opus
pivot = d.pivot(index="task_id", columns="model", values="resolved")
pa = pivot[A].astype(int).values
pb = pivot[B].astype(int).values

rng = np.random.default_rng(0)
idx = rng.integers(0, len(pa), (10_000, len(pa)))
boot = pa[idx].mean(axis=1) - pb[idx].mean(axis=1)
blo, bhi = np.percentile(boot, [2.5, 97.5])

a_only = int(((pa == 1) & (pb == 0)).sum())
b_only = int(((pa == 0) & (pb == 1)).sum())
both = int(((pa == 1) & (pb == 1)).sum())
neither = int(((pa == 0) & (pb == 0)).sum())

indexed = summary.set_index("model")
ra, rb = indexed.loc[A], indexed.loc[B]

lines = [
    f"SWE-bench Verified | {len(ref_tasks)} common tasks | {len(summary)} matched models",
    "Cost per solve = total spend, including failed runs, / tasks solved",
    "",
    summary[[
        "model", "solved", "resolve_rate_pct", "ci95_lo_pct",
        "ci95_hi_pct", "total_cost_usd", "cost_per_solve_usd",
        "avg_successful_run_cost_usd", "avg_failed_run_cost_usd",
        "failed_run_cost_share_pct"
    ]].round(3).to_string(index=False),
    "",
    "Pareto-efficient configurations:",
    ", ".join(frontier.model),
    "",
    "Outcome counts:",
    outcomes.to_string(),
    "",
    f"Head-to-head: {A} vs {B}",
    f"Resolution: {ra.resolve_rate_pct:.1f}% vs {rb.resolve_rate_pct:.1f}%",
    f"Cost per solve: ${ra.cost_per_solve_usd:.3f} vs ${rb.cost_per_solve_usd:.3f}",
    f"Opus/Qwen cost-per-solve ratio: {rb.cost_per_solve_usd / ra.cost_per_solve_usd:.2f}x",
    f"Qwen solved only: {a_only} | Opus solved only: {b_only}",
    f"Both solved: {both} | Neither solved: {neither}",
    f"Paired bootstrap 95% CI for resolution difference: "
    f"[{100*blo:+.1f}, {100*bhi:+.1f}] percentage points",
]

text = "\n".join(lines)
print("\n" + text)
Path("results_summary.txt").write_text(text, encoding="utf-8")

# Save plotting data for the separate chart script
summary.to_csv("chart_data.csv", index=False)
print("\nSaved matched_cost_analysis.csv, outcomes.csv, chart_data.csv, results_summary.txt")
