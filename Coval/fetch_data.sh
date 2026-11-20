#!/usr/bin/env bash
# Refresh the data snapshot from the public repository (results will change as the benchmark updates).
curl -sL -o data/coval-benchmarks.json https://raw.githubusercontent.com/openbenchmarks-labs/tts-stt-benchmarks-by-coval/main/coval-benchmarks.json
