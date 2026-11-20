# Coval voice benchmarks: scoped TTS/STT analysis

This project re-analyzes the aggregate statistics published by Coval's TTS/STT
benchmark. It asks how stable model rankings are under uncertainty, how STT
latency conclusions change with the metric, and how much mean WER depends on
extreme observations.

The analysis uses only published aggregate quantiles and sample counts. It does
not run providers, use per-item outputs, inspect transcripts, or make cost
comparisons.

The included input is `data/coval-benchmarks.json`, synced 2026-11-19 from
[openbenchmarks-labs/tts-stt-benchmarks-by-coval](https://github.com/openbenchmarks-labs/tts-stt-benchmarks-by-coval).

## Deliverable

[Open the one-page analysis PDF](output/Dsouza_Coval_Voice_Benchmarks_Scoped_Analysis.pdf).
The figure and intermediate tables are generated in `output/`.

## Reproduce

Requirements: Python 3.10+ and the packages in `requirements.txt`. From this
directory, create an environment and install dependencies:

```bash
python -m venv .venv
```

On macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
bash run_all.sh
```

On Windows PowerShell, install and run each pipeline stage in order:

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python src\01_flatten.py
.\.venv\Scripts\python src\02_analysis.py
.\.venv\Scripts\python src\03_figure.py
.\.venv\Scripts\python src\04_pdf.py
```

The scripts expect to be run from this directory. They read the included
`data/coval-benchmarks.json` snapshot and write tables, a figure, and the PDF
under `output/`. `fetch_data.sh` replaces the included snapshot with the latest
upstream file; doing so changes the results. Keep the included snapshot when
reproducing the published PDF.

## Pipeline

1. `src/01_flatten.py` converts the nested JSON snapshot into one row per task,
   window, model, and metric.
2. `src/02_analysis.py` fits mixed models, bootstraps reconstructed distributions,
   estimates frontier membership, compares selected model pairs, and calculates
   rank discordance and WER-tail summaries.
3. `src/03_figure.py` creates the four-panel analysis figure.
4. `src/04_pdf.py` lays out the one-page report.

## Method and limitations

The bootstrap reconstructs distributions by piecewise-linear interpolation
through published min, p50, p90, p95, p99, and max values. WER is calibrated to
the published mean. Effective sample sizes of 30 TTS prompts and 50 STT
utterances are used for WER uncertainty; confidence intervals are approximate
and may be optimistic. A per-task model cannot be fit because item-level results
are not public.

The exact inclusion rules, assumptions, and interpretation notes are summarized
in the report and in the upstream benchmark's `docs/methodology.md`. The input
snapshot is from
[openbenchmarks-labs/tts-stt-benchmarks-by-coval](https://github.com/openbenchmarks-labs/tts-stt-benchmarks-by-coval);
data rights and licensing remain with the original publishers.
