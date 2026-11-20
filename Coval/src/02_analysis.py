import numpy as np, pandas as pd, json, warnings
import statsmodels.formula.api as smf
from scipy.stats import spearmanr
warnings.filterwarnings('ignore')
rng=np.random.default_rng(7)
df=pd.read_csv('output/flat.csv')
res={}

# ---------- A. mixed models: log(p50 latency) ~ window + (1|model) ----------
def mm(task,metric,col='p50',log=True,minn=50):
    x=df[(df.task==task)&(df.metric==metric)&(df.samples>=minn)].dropna(subset=[col]).copy()
    x=x[x.avg<20] if metric=='WER' else x
    x=x[x.id.map(x.id.value_counts())==3]   # models present in all 3 windows
    x=x[x[col]>0] if log else x
    x['y']=np.log(x[col]) if log else x[col]
    m=smf.mixedlm('y ~ C(window)',x,groups=x['id']).fit(reml=True)
    vb=float(m.cov_re.iloc[0,0]); vr=float(m.scale)
    return dict(n_models=x.id.nunique(),var_between=vb,var_resid=vr,icc=vb/(vb+vr),
                sd_between=vb**.5,sd_resid=vr**.5,
                win={k:float(v) for k,v in m.fe_params.items() if 'window' in k})
res['mm']={
 'TTS TTFA (log p50)':mm('TTS','TTFA'),
 'STT TTFS (log p50)':mm('STT','TTFS'),
 'STT TTFT (log p50)':mm('STT','TTFT'),
 'TTS WER (avg)':mm('TTS','WER','avg',log=False),
 'STT WER (avg)':mm('STT','WER','avg',log=False)}
for k,v in res['mm'].items(): print(k,{a:(round(b,4) if isinstance(b,float) else b) for a,b in v.items()})

# ---------- B. quantile-knot bootstrap ----------
def knots(r):
    q=[0,.5,.9,.95,.99,1]; v=[r['min'],r['p50'],r['p90'],r['p95'],r['p99'],r['max']]
    pts=[(a,b) for a,b in zip(q,v) if b==b and b is not None]
    # enforce monotone
    qs=[p[0] for p in pts]; vs=np.maximum.accumulate([p[1] for p in pts])
    return np.array(qs),vs
def draws(r,n,B,calib=None):
    qs,vs=knots(r); u=rng.random((B,n)); x=np.interp(u,qs,vs)
    if calib is not None:
        m=np.interp(rng.random(200000),qs,vs).mean()
        if m>0: x=x*(calib/m)
    return x
def boot(r,stat,n,B=2000,calib=None):
    x=draws(r,n,B,calib)
    return np.median(x,axis=1) if stat=='median' else x.mean(axis=1)

def table(task,lat,win='30d',n_lat=None,n_wer=None,minn=300):
    L=df[(df.task==task)&(df.metric==lat)&(df.window==win)].set_index('id')
    W=df[(df.task==task)&(df.metric=='WER')&(df.window==win)].set_index('id')
    ids=[i for i in L.index if i in W.index and L.loc[i,'samples']>=minn and W.loc[i,'samples']>=minn
         and not (W.loc[i,'avg']>20)]
    out=[]; draws_lat={}; draws_w={}
    for i in ids:
        l=L.loc[i]; w=W.loc[i]
        bl=boot(l,'median',int(min(l.samples,n_lat or l.samples)))
        bw=boot(w,'mean',n_wer,calib=w.avg)
        draws_lat[i]=bl; draws_w[i]=bw
        out.append(dict(id=i,lat=l.p50,lat_lo=np.percentile(bl,2.5),lat_hi=np.percentile(bl,97.5),
                        wer=w.avg,wer_lo=np.percentile(bw,2.5),wer_hi=np.percentile(bw,97.5),
                        wer_p50=w.p50,wer_p90=w.p90,wer_max=w['max'],n=int(l.samples)))
    t=pd.DataFrame(out).set_index('id')
    # frontier membership probability
    B=2000; M=np.stack([draws_lat[i] for i in ids],1); Wm=np.stack([draws_w[i] for i in ids],1)
    mem=np.zeros(len(ids))
    for b in range(B):
        a=M[b]; c=Wm[b]
        for j in range(len(ids)):
            dom=((a<=a[j])&(c<=c[j])&((a<a[j])|(c<c[j]))).any()
            mem[j]+= (not dom)
    t['p_front']=mem/B
    # point frontier
    pf=[]
    for i in t.index:
        r=t.loc[i]; pf.append(not ((t.lat<=r.lat)&(t.wer<=r.wer)&((t.lat<r.lat)|(t.wer<r.wer))).any())
    t['on_front']=pf
    return t,draws_lat,draws_w
tts,tl,tw=table('TTS','TTFA',n_wer=30)       # 30 prompts => prompt-clustered n_eff
stt,sl,sw=table('STT','TTFT',n_wer=50)       # 50-utt subset (per docs) => n_eff
stt2,_,_=table('STT','TTFS',n_wer=50)
tts.to_csv('output/tts_front.csv'); stt.to_csv('output/stt_front_ttft.csv'); stt2.to_csv('output/stt_front_ttfs.csv')
pd.set_option('display.width',200)
print(tts.sort_values('lat').round(2)[['lat','lat_lo','lat_hi','wer','wer_lo','wer_hi','wer_p50','wer_p90','wer_max','p_front','on_front']].to_string())
print(stt.sort_values('lat').round(2)[['lat','lat_lo','lat_hi','wer','wer_lo','wer_hi','wer_p90','wer_max','p_front','on_front']].to_string())

# ---------- C. pairwise: "challenger vs flagship" ----------
def pair(task,a,b,tl,tw):
    pl=(tl[a]<tl[b]).mean(); pw=(tw[a]<tw[b]).mean()
    return dict(a=a,b=b,P_a_faster=round(pl,3),P_a_lower_WER=round(pw,3),dWER=round(float(np.mean(tw[a]-tw[b])),3),
                dWER_ci=[round(float(np.percentile(tw[a]-tw[b],2.5)),2),round(float(np.percentile(tw[a]-tw[b],97.5)),2)])
pairs=[('nari/qwen3-tts-fast','elevenlabs/eleven_v4_turbo'),('nari/qwen3-tts-fast','cartesia/sonic-3.6'),
       ('baseten/qwen3-tts-1.7b','google/chirp-3-hd'),('fluxions/vui','elevenlabs/eleven_v4_turbo'),('deepdub/dd-etts-3.3','elevenlabs/eleven_v4_turbo')]
for a,b in pairs:
    if a in tl and b in tl: print(pair('TTS',a,b,tl,tw))
spairs=[('nari/qwen3-asr-fast','assemblyai/universal-3.6-pro'),('baseten/whisper-large-v3','openai/gpt-realtime-whisper'),
        ('baseten/qwen3-asr-1.7b','google/chirp_3'),('deepgram/nova-3','assemblyai/universal-3.6-pro')]
for a,b in spairs:
    if a in sl and b in sl: print(pair('STT',a,b,sl,sw))

# ---------- D. metric discordance TTFS vs TTFT (STT) ----------
a=df[(df.task=='STT')&(df.window=='30d')&(df.metric=='TTFS')].set_index('id').p50
b=df[(df.task=='STT')&(df.window=='30d')&(df.metric=='TTFT')].set_index('id').p50
j=pd.concat([a.rename('ttfs'),b.rename('ttft')],axis=1).dropna()
j=j[df[(df.task=='STT')&(df.window=='30d')&(df.metric=='TTFT')].set_index('id').loc[j.index,'samples']>=300]
rho=spearmanr(j.ttfs,j.ttft); print('Spearman TTFS vs TTFT',rho, len(j))
j['rk_ttfs']=j.ttfs.rank(); j['rk_ttft']=j.ttft.rank(); j['shift']=j.rk_ttfs-j.rk_ttft
print(j.sort_values('shift').round(0).to_string()); j.to_csv('output/stt_disc.csv')

# ---------- E. tail share of WER mass ----------
def tail_share(r):
    qs,vs=knots(r); x=np.interp(rng.random(400000),qs,vs); x=x*(r.avg/x.mean()) if x.mean()>0 else x
    s=np.sort(x); return s[int(.9*len(s)):].sum()/s.sum(), (x==0).mean()
rows=[]
for t,lat in(('TTS','TTFA'),('STT','TTFT')):
    W=df[(df.task==t)&(df.metric=='WER')&(df.window=='30d')&(df.samples>=300)]
    for _,r in W.iterrows():
        if r.avg<20 and r.avg>0:
            ts,z=tail_share(r); rows.append(dict(task=t,id=r.id,tail10_share=ts,zero_share=z,avg=r.avg,p50=r.p50,p90=r.p90,mx=r['max']))
T=pd.DataFrame(rows); T.to_csv('output/tail.csv')
print(T.groupby('task')[['tail10_share','zero_share','avg','p90','mx']].median().round(2))
json.dump(res,open('output/mm.json','w'),default=float)
