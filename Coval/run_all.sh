#!/usr/bin/env bash
set -e
python3 src/01_flatten.py
python3 src/02_analysis.py
python3 src/03_figure.py
python3 src/04_pdf.py
echo "Done: output/Dsouza_Coval_Voice_Benchmarks_Scoped_Analysis.pdf"
