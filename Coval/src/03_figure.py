import pandas as pd, numpy as np, json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
tts=pd.read_csv('output/tts_front.csv',index_col=0); stt=pd.read_csv('output/stt_front_ttft.csv',index_col=0)
disc=pd.read_csv('output/stt_disc.csv',index_col=0); mm=json.load(open('output/mm.json'))['mm']
print('TTS p50==0:',(tts.wer_p50==0).sum(),'/',len(tts),' STT max>=100:',(stt.wer_max>=100).sum(),'/',len(stt))
plt.rcParams.update({'font.size':7,'axes.spines.top':False,'axes.spines.right':False,'font.family':'DejaVu Sans'})
fig,ax=plt.subplots(2,2,figsize=(7.6,6.0),dpi=220)
cm=plt.cm.viridis
def short(i): return i.split('/')[-1].replace('-preview-us-east','').replace('assemblyai-','')
def frontier(a,t,lab,xlim=None,logx=False,xl=''):
    for i,r in t.iterrows():
        c=cm(0.15+0.75*r.p_front) if r.p_front>0.05 else '#b9b9b9'
        a.errorbar(r.lat,r.wer,xerr=[[r.lat-r.lat_lo],[r.lat_hi-r.lat]],yerr=[[r.wer-r.wer_lo],[r.wer_hi-r.wer]],
                   fmt='o',ms=3.2,color=c,ecolor=c,elinewidth=.5,alpha=.9 if r.p_front>.05 else .55,capsize=0)
    f=t[t.on_front].sort_values('lat'); a.step(f.lat,f.wer,where='post',color='#222',lw=.9,ls='--',zorder=0)
    for i,r in t.iterrows():
        if i in lab:
            dx,dy=lab[i]; a.annotate(f"{short(i)} ({r.p_front:.2f})",(r.lat,r.wer),xytext=(dx,dy),textcoords='offset points',fontsize=5.6,
                arrowprops=dict(arrowstyle='-',lw=.3,color='#666'))
    if logx:
        a.set_xscale('log'); a.xaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f'{int(v):,}'))
        a.xaxis.set_minor_formatter(plt.NullFormatter()); a.set_xticks([40,100,300,1000,3000] if xl.startswith('TTFA') else [600,1000,2000,5000])
    a.set_ylim(0,None); a.set_xlabel(xl); a.set_ylabel('WER, mean % (95% CI, prompt-clustered)')
frontier(ax[0,0],tts,{'fluxions/vui':(4,16),'gradium/gradium-tts-beta-202609':(-4,48),'inworld/inworld-tts-2-flash':(20,78),'nari/qwen3-tts-fast':(-30,92),'murf/falcon-2':(34,112),'elevenlabs/eleven_v4_turbo':(-6,72),'cartesia/sonic-3.6':(10,96)},logx=True,xl='TTFA p50, ms (log; 95% CI)')
ax[0,0].set_title('A  TTS frontier, 30d  (label = P on frontier)',loc='left',fontsize=7.4,fontweight='bold')
frontier(ax[0,1],stt,{'saidwire/saidwire-en-2026-10-30':(6,22),'baseten/qwen3-asr-1.7b':(-62,-24),'assemblyai/universal-3.6-pro':(30,-26),'deepgram/nova-3':(-30,22),'baseten/whisper-large-v3':(14,46),'nari/qwen3-asr-fast':(10,40),'openai/gpt-realtime-whisper':(6,26)},logx=True,xl='TTFT p50, ms (log; 95% CI)')
ax[0,1].set_title('B  STT frontier, 30d',loc='left',fontsize=7.4,fontweight='bold')
sm=plt.cm.ScalarMappable(cmap=cm,norm=plt.Normalize(0,1)); 
cax=fig.add_axes([0.93,0.60,0.012,0.30]); cb=fig.colorbar(sm,cax=cax); cb.set_label('P(on frontier)',fontsize=6); cb.ax.tick_params(labelsize=5.5)
# C slope chart TTFS rank -> TTFT rank
a=ax[1,0]; hi=['soniox/stt-rt-v6','nari/qwen3-asr-fast','reson8/realtime-global','elevenlabs/scribe_v2_realtime','baseten/whisper-large-v3','deepgram/nova-2','deepgram/nova-3']
for i,r in disc.iterrows():
    on=i in hi; col=('#c0392b' if r['shift']<0 else '#1f77b4') if on else '#d0d0d0'
    a.plot([0,1],[r.rk_ttfs,r.rk_ttft],color=col,lw=1.1 if on else .5,zorder=2 if on else 1)
    if on:
        a.text(-.04,r.rk_ttfs,short(i),ha='right',va='center',fontsize=5.6,color=col)
        a.text(1.04,r.rk_ttft,short(i),ha='left',va='center',fontsize=5.6,color=col)
a.set_xlim(-.75,1.75); a.invert_yaxis(); a.set_xticks([0,1]); a.set_xticklabels(['rank by TTFS\n(repo headline)','rank by TTFT']); a.set_yticks([]); a.spines['left'].set_visible(False)
a.set_title('C  STT: TTFS vs TTFT ranks (ρ = 0.63)',loc='left',fontsize=7.4,fontweight='bold')
# D variance decomposition
a=ax[1,1]; names=['TTS TTFA','STT TTFS','STT TTFT','TTS WER','STT WER']; keys=['TTS TTFA (log p50)','STT TTFS (log p50)','STT TTFT (log p50)','TTS WER (avg)','STT WER (avg)']
icc=[mm[k]['icc'] for k in keys]; sb=[mm[k]['sd_between'] for k in keys]; sr=[mm[k]['sd_resid'] for k in keys]
y=np.arange(len(names)); a.barh(y,[v*100 for v in icc],color='#4c78a8',height=.55)
for j,(v,b,r) in enumerate(zip(icc,sb,sr)): a.text(v*100+1,j,f"ICC {v:.2f}   SDmodel {b:.2f} | SDwindow {r:.2f}",va='center',fontsize=5.8)
a.set_yticks(y); a.set_yticklabels(names); a.invert_yaxis(); a.set_xlim(0,175); a.set_xticks([0,50,100]); a.set_xlabel('% of variance between models (rest = 24h/7d/30d drift)')
a.set_title('D  Mixed model: y ~ window + (1 | model)',loc='left',fontsize=7.4,fontweight='bold')
fig.subplots_adjust(left=.07,right=.91,top=.95,bottom=.09,hspace=.38,wspace=.28); fig.savefig('output/fig.png'); print('fig ok')
