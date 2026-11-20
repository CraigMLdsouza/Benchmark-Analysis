"""
SWE-bench Verified: where did the runs (and the money) go?

Usage:
    python chart-2.py                    # looks for swebench-verified.jsonl
    python chart-2.py path/to/file.jsonl

Outputs (current folder):
    outcome_by_model.csv      run outcomes + spend per model
    spend_by_outcome.csv      overall spend split by outcome
    failure_anatomy.png       dark-mode chart
    failure_summary.txt       plain-text summary

Requires: pandas, numpy, matplotlib
"""
import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd

args = [a for a in sys.argv[1:] if not a.startswith("--")]
FILE_PATH = Path(args[0]) if args else Path("swebench-verified.jsonl")

# --------------------------------------------------------------------------
# Load + match on task IDs (same logic as cost_per_solve_full.py)
# --------------------------------------------------------------------------
with FILE_PATH.open("r", encoding="utf-8") as f:
    df = pd.DataFrame([json.loads(line) for line in f if line.strip()])
df["cost_usd"] = pd.to_numeric(df["cost_usd"], errors="coerce")
df["resolved"] = df["resolved"].astype(bool)
assert not df.duplicated(["model", "task_id"]).any()

counts = df.groupby("model").size()
ref_models = counts[counts == 45].index
ref_tasks = set(df[df.model == ref_models[0]].task_id)
covering = [m for m, g in df.groupby("model") if ref_tasks <= set(g.task_id)]
d = df[df.model.isin(covering) & df.task_id.isin(ref_tasks)].copy()
n_tasks, n_models = len(ref_tasks), len(covering)
print(f"{n_models} models x {n_tasks} tasks = {len(d)} runs")

ORDER = ["resolved", "failed_tests", "failed_step_limit", "failed_empty_patch", "failed_time_limit"]
LABEL = {
    "resolved": "Solved",
    "failed_tests": "Patch submitted, tests failed",
    "failed_step_limit": "Hit the 100-iteration cap",
    "failed_empty_patch": "Ended with no patch",
    "failed_time_limit": "Hit time limit",
}

# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------
runs = d.groupby(["model", "outcome"]).size().unstack(fill_value=0).reindex(columns=ORDER, fill_value=0)
spend = d.groupby(["model", "outcome"]).cost_usd.sum().unstack(fill_value=0).reindex(columns=ORDER, fill_value=0)
by_model = runs.add_prefix("runs_").join(spend.add_prefix("usd_"))
by_model["total_usd"] = spend.sum(axis=1)
by_model["resolve_rate_pct"] = 100 * runs["resolved"] / runs.sum(axis=1)
by_model["cost_per_solve_usd"] = by_model.total_usd / runs["resolved"].replace(0, np.nan)
by_model["wasted_spend_pct"] = 100 * (1 - spend["resolved"] / spend.sum(axis=1))
by_model = by_model.sort_values("resolve_rate_pct", ascending=False)
by_model.round(4).to_csv("outcome_by_model.csv")

overall_runs = d.outcome.value_counts().reindex(ORDER, fill_value=0)
overall_spend = d.groupby("outcome").cost_usd.sum().reindex(ORDER, fill_value=0)
total_spend = overall_spend.sum()
overall = pd.DataFrame({
    "runs": overall_runs,
    "runs_pct": 100 * overall_runs / overall_runs.sum(),
    "spend_usd": overall_spend,
    "spend_pct": 100 * overall_spend / total_spend,
    "avg_cost_per_run_usd": overall_spend / overall_runs.replace(0, np.nan),
})
overall.round(3).to_csv("spend_by_outcome.csv")

failures = d[~d.resolved]
fail_mix = failures.outcome.value_counts(normalize=True).reindex(ORDER[1:], fill_value=0) * 100

# How many step-limit runs still produced an applicable patch?
sl = d[d.outcome == "failed_step_limit"]
sl_patch_pct = 100 * sl.apply_ok.astype(bool).mean() if len(sl) else np.nan

# Models whose failures are mostly "never finished" vs mostly "wrong patch"
f_by_model = failures.groupby(["model", "outcome"]).size().unstack(fill_value=0).reindex(columns=ORDER[1:], fill_value=0)
f_by_model["fail_n"] = f_by_model.sum(axis=1)
f_by_model["never_finished_pct"] = 100 * (f_by_model.failed_step_limit + f_by_model.failed_empty_patch
                                           + f_by_model.failed_time_limit) / f_by_model.fail_n
f_by_model["wrong_patch_pct"] = 100 * f_by_model.failed_tests / f_by_model.fail_n

# --------------------------------------------------------------------------
# Text summary
# --------------------------------------------------------------------------
L = []
L.append(f"SWE-bench Verified | {n_tasks} common tasks | {n_models} models | {len(d)} runs")
L.append(f"Total logged spend: ${total_spend:,.2f}\n")
L.append("OVERALL (runs and spend by outcome)")
L.append(overall.round(2).to_string())
L.append(f"\nShare of spend on runs that did NOT solve the task: {100 - overall.spend_pct['resolved']:.1f}%")
L.append(f"Failures: {len(failures)} runs -> " + ", ".join(f"{LABEL[k]} {v:.1f}%" for k, v in fail_mix.items()))
L.append(f"Step-cap runs whose patch still applied: {sl_patch_pct:.1f}%")
L.append("\nPER MODEL (sorted by resolution rate)")
cols = ["resolve_rate_pct", "runs_resolved", "runs_failed_tests", "runs_failed_step_limit",
        "runs_failed_empty_patch", "runs_failed_time_limit", "total_usd", "cost_per_solve_usd", "wasted_spend_pct"]
L.append(by_model[cols].round(2).to_string())
L.append("\nFAILURE COMPOSITION PER MODEL (share of that model's failures)")
L.append(f_by_model[["fail_n", "wrong_patch_pct", "never_finished_pct"]].sort_values("wrong_patch_pct", ascending=False)
         .round(1).to_string())
L.append("\nTasks where at least one model hit the iteration cap: "
         f"{sl.task_id.nunique()} of {n_tasks}")
text = "\n".join(L)
print("\n" + text)
Path("failure_summary.txt").write_text(text, encoding="utf-8")

# --------------------------------------------------------------------------
# Dark-mode chart
# --------------------------------------------------------------------------
import matplotlib.pyplot as plt

BG, PANEL, GRID, TXT, MUTED = "#0b0f19", "#111827", "#1f2937", "#e5e7eb", "#8b95a7"
COL = {
    "resolved": "#34d399",
    "failed_tests": "#60a5fa",
    "failed_step_limit": "#fbbf24",
    "failed_empty_patch": "#f87171",
    "failed_time_limit": "#a78bfa",
}
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": TXT, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "text.parse_math": False})

fig = plt.figure(figsize=(15, 9.4), facecolor=BG)
gs = fig.add_gridspec(2, 1, height_ratios=[0.34, 1], hspace=0.38,
                      left=0.175, right=0.965, top=0.80, bottom=0.085)
ax_top = fig.add_subplot(gs[0])
ax = fig.add_subplot(gs[1])
for a_ in (ax_top, ax):
    a_.set_facecolor(PANEL)
    for s in a_.spines.values():
        s.set_color(GRID)

# ---- top: one stacked bar each for runs and spend ------------------------
rows_ = [("Share of runs", 100 * overall_runs / overall_runs.sum()),
         ("Share of spend", 100 * overall_spend / total_spend)]
for yi, (name, ser) in zip([1, 0], rows_):
    left = 0
    for k in ORDER:
        w = ser[k]
        ax_top.barh(yi, w, left=left, color=COL[k], height=0.58, edgecolor=BG, lw=1.5)
        if w >= 4:
            ax_top.text(left + w / 2, yi, f"{w:.0f}%", ha="center", va="center",
                        fontsize=11, fontweight="bold", color="#0b0f19")
        left += w
ax_top.set_yticks([1, 0])
ax_top.set_yticklabels([r[0] for r in rows_], fontsize=11)
ax_top.set_xlim(0, 100)
ax_top.set_xticks([])
ax_top.tick_params(axis="y", length=0)
ax_top.set_title(f"All {n_models} configs · {n_tasks} tasks · {len(d)} runs", color=MUTED,
                 fontsize=10, loc="left", pad=8)

# ---- bottom: per-model run outcomes -------------------------------------
order = by_model.index[::-1]  # best at top
y = np.arange(len(order))
left = np.zeros(len(order))
for k in ORDER:
    vals = np.array([runs.loc[m, k] for m in order], dtype=float)
    ax.barh(y, vals, left=left, color=COL[k], height=0.7, edgecolor=BG, lw=1.2, zorder=3)
    for yi, v, l in zip(y, vals, left):
        if v >= 4:
            ax.text(l + v / 2, yi, f"{int(v)}", ha="center", va="center", fontsize=8.5,
                    fontweight="bold", color="#0b0f19", zorder=4)
    left += vals
ax.set_yticks(y)
ax.set_yticklabels([f"{m}  ·  {by_model.loc[m, 'resolve_rate_pct']:.0f}%" for m in order], fontsize=9.5)
ax.set_xlim(0, runs.sum(axis=1).max())
ax.set_xlabel("Runs per model (45 tasks each)", labelpad=8, fontsize=10.5)
ax.tick_params(axis="y", length=0)
ax.grid(True, axis="x", color=GRID, lw=0.8)
ax.set_axisbelow(True)

# legend
handles = [plt.Rectangle((0, 0), 1, 1, color=COL[k]) for k in ORDER]
fig.legend(handles, [LABEL[k] for k in ORDER], loc="upper left", bbox_to_anchor=(0.175, 0.855),
           ncol=5, frameon=False, fontsize=9.5, labelcolor=TXT, handlelength=1.2, columnspacing=1.6)

wasted = 100 - overall.spend_pct["resolved"]
cap_spend = overall.spend_pct["failed_step_limit"]
fig.text(0.04, 0.945, "Where the runs and the money went", fontsize=22, fontweight="bold", color=TXT)
fig.text(0.04, 0.905,
         f"{wasted:.0f}% of spend went to runs that solved nothing  ·  "
         f"{cap_spend:.0f}% went to runs that hit the iteration cap",
         fontsize=11.5, color=COL["failed_step_limit"])
fig.text(0.04, 0.875,
         "SWE-bench Verified · tasks attempted by every config · one run each · "
         "cap = 100 iterations in the dataset's logged limit",
         fontsize=9.5, color=MUTED)
fig.text(0.965, 0.018, "Source: swebench-verified.jsonl · indicative, small sample",
         fontsize=8.5, color=MUTED, ha="right")

fig.savefig("failure_anatomy.png", dpi=220, facecolor=BG)
print("\nSaved: outcome_by_model.csv, spend_by_outcome.csv, failure_summary.txt, failure_anatomy.png")