# Terminal-Bench 4.0 — Methodology

## Data source and retrieval date
- Primary benchmark: [Terminal-Bench 4.0 official site](https://www.tbench.ai/?version=4.0)
- Published leaderboard table used for the transcribed rows: [Snorkel AI Terminal-Bench 4.0 leaderboard](https://www.snorkel.ai/leaderboard/terminal-bench/)
- Retrieved: 2026-10-29
- The Snorkel table publishes model, effort, agent, resolution rate, release date, tokens, and cost. The official Terminal-Bench release notes describe v4.0 as a 66-task version with task fixes, resource calibration, and removal of saturated tasks: https://www.tbench.ai/news/terminal-bench-4-0

## What was included
- Transcribed all 23 entries shown in the published Snorkel AI leaderboard table.
- 22 entries had both a resolution rate and a cost and were included in `analysis.csv` and `chart.png`.
- `Muse Spark 1.3` had no displayed cost and is retained in `terminal_bench_data.csv` with a blank cost, but excluded from cost-based calculations and the chart.
- Model, agent, and effort are retained separately to avoid treating a model name alone as the full evaluation configuration.

## Cost interpretation and rounding
- The source displays total run cost in rounded `$k` units (e.g., `$4.7k`). Values were converted to approximate USD (e.g., `$4.7k` → `4700`) for arithmetic and plotting.
- Because the public display is rounded, cost-per-resolution-point values are approximate, especially for entries displayed as `$0.1k`.
- The published methodology states cost and tokens are totals for the full evaluation run across all 66 tasks, not per-task cost. These are therefore **run-total cost comparisons**, not production cost per resolved task or per successful individual attempt.
- This analysis uses the reported resolution rate as a percentage number. `cost_per_resolution_point = cost_USD / resolution_rate_percent`. Example: `$100 / 35.8 = $2.79 per percentage point`.

## Rankings
- `capability_rank`: descending resolution rate; ties share the same rank.
- `value_rank`: ascending cost per resolution point; ties share the same rank.
- "Best value" in this analysis means lowest reported total cost divided by reported resolution-rate percentage. It is a simple descriptive ratio, not a causal or universal purchasing recommendation.
- The chart's dashed frontier is drawn as a step line (the best reported result available at each budget; no interpolation between configurations). It is the Pareto frontier over reported cost and resolution rate: configurations for which no other plotted configuration has both lower/equal cost and higher/equal resolution rate with at least one strict improvement.

## Limitations
1. **Different configurations:** Model, agent harness, and effort setting vary. The unit of analysis is a model/agent/effort configuration, not model capability in isolation.
2. **Rounded costs:** Cost figures are displayed in rounded thousands of dollars. A `$0.1k` entry could be anywhere from about $50 to $150, so ratios and rankings among the cheapest entries (GLM-5.3-Flash and GPT-6 Luna, both tied at `$0.1k`) are not meaningful.
3. **Aggregate cost:** The published cost is for the evaluation run across 66 tasks; it is not per query, per solved task, or an estimate of production economics.
4. **Uncertainty:** Resolution rates are reported with confidence intervals on the source leaderboard, but this chart uses point estimates and does not encode uncertainty.
5. **Benchmark validity:** Epoch AI's review of Terminal-Bench 4.0.0 (reviewed 2026-09-04) identified publicly documented scoring defects in 30 of 66 tasks and classified the benchmark as flawed. See https://epoch.ai/benchmarks/terminal-bench-4/review. Results should be treated as indicative, not definitive.
6. **Leaderboard snapshots differ:** The official site is dynamic. The included table is a public leaderboard snapshot surfaced by Snorkel AI, retrieved 2026-10-29; it should not be silently mixed with other providers' independent Terminal-Bench evaluations.
7. **No new evaluations:** This project uses public leaderboard metrics only. No models were run.

## Reproduction
Requirements: Python 3, pandas, matplotlib, numpy.

From this directory:
```bash
python chart.py
```
`analysis.csv` is reproducible from `terminal_bench_data.csv` with the calculations above. `chart.py` regenerates the chart from `analysis.csv` and the raw leaderboard CSV. No API keys or model evaluation runs are required.
