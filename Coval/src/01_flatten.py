"""Flatten coval-benchmarks.json into one row per (task, window, model, metric)."""
import json, pandas as pd
d = json.load(open('data/coval-benchmarks.json'))
rows = []
for task, tv in d['benchmarks'].items():
    for w, wv in tv['windows'].items():
        for m in wv['models']:
            for met, s in m['metrics'].items():
                rows.append(dict(task=task, window=w, provider=m['provider'], model=m['model'], metric=met,
                                 **{k: s.get(k) for k in ('avg','p50','p90','p95','p99','min','max','samples')}))
df = pd.DataFrame(rows); df['id'] = df.provider + '/' + df.model
df.to_csv('output/flat.csv', index=False); print(len(df), 'rows')
