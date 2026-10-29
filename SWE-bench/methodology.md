# Methodology — Benchmark Teardown #2

## Question
How much do reported SWE-bench Verified results vary across agent scaffolds when the named model is Claude 3.5 Sonnet?

## Data sources
1. Published comparison table in the preprint PDF:
   https://www.preprints.org/frontend/manuscript/2ac614cb5a2d08573aea6cd8fd2f1675/download_pub
2. Official SWE-bench leaderboard:
   https://www.swebench.com/verified.html
3. Public leaderboard data repository:
   https://github.com/SWE-bench/swe-bench.github.io/blob/master/data/leaderboards.json

## Inclusion criteria
- Benchmark split identified as SWE-bench Verified.
- Model family named as Claude 3.5 Sonnet.
- A scaffold/harness is named in the source table.
- Scores are reported as percentages over 500 tasks.

## Values transcribed
- SWE-agent (20240620): 33.6% (168/500)
- SWE-agent + tools: 49.0% (245/500)
- Agentless: 50.8% (254/500)
- AutoCodeRover: 51.8% (259/500)
- OpenHands + CodeAct 2.1: 53.0% (265/500)
- PatchPilot: 53.6% (268/500)

## Calculation
Spread = highest reported resolution rate − lowest reported resolution rate
= 53.6% − 33.6% = 20.0 percentage points.

Equivalent resolved-task difference = 268 − 168 = 100 tasks out of 500.

## Important limitations
- These are published system-level results, not a controlled experiment. Model snapshot, prompts, tools, budgets, retries, and other settings may differ across submissions.
- The exact model snapshot is not uniformly specified for every row in the secondary comparison table. The chart labels the common model family, Claude 3.5 Sonnet, rather than asserting every row used an identical API snapshot.
- The 20-point range must not be described as a causal effect attributable solely to the scaffold.
- Do not mix SWE-bench Verified with SWE-bench Lite or Full results.
- A leaderboard score describes the complete evaluated configuration (model + scaffold + settings), not the base model in isolation.

## Recommended public wording
“Published Claude 3.5 Sonnet system results on SWE-bench Verified range from 33.6% to 53.6% across six scaffolds. That is a 20-percentage-point observed spread. Because the submissions are not a controlled, matched experiment, this demonstrates configuration sensitivity rather than isolating a causal scaffold effect.”

## Files
- `swebench_verified_data.csv`: row-level dataset and source notes
- `scaffold_comparison.csv`: chart-ready comparison
- `scaffold_gap_summary.csv`: summary statistics
- `chart.png`: horizontal bar chart
- `linkedin_post.txt`: draft post under 150 words
