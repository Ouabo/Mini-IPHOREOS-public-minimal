"""Reproducible one-dimensional toy experiment. No physical robot is required."""
from pathlib import Path
import sys,csv,json,random,hashlib,platform
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'firmware'))
from belief_controller import Controller
OUT=R/'results';OUT.mkdir(exist_ok=True)
AS=R/'assets';AS.mkdir(exist_ok=True)
POLICIES=['raw','belief','mini']

def episode(seed,policy,context,stress=False,trace=False):
    # Streams separate motion from sensing. Same seed shares starting conditions;
    # differing action sequences necessarily generate different observation paths.
    init=random.Random(seed);sensor=random.Random(seed+100000);motion=random.Random(seed+200000)
    d=init.uniform(45,85);speed=init.uniform(6.8,9.2);bias=5.0 if stress else init.uniform(-.6,.6)
    c=Controller(policy,context);time=0.;samples=0;contacts=0;log=[]
    for index in range(600):
        u=sensor.random();noise=sensor.gauss(0,1.6)
        raw=None if u<.02 else d+bias+noise+(12.0 if .02<=u<.03 else 0.)
        action=c.observe(raw,time);samples+=1
        log.append({'time_s':time,'true_cm':d,'raw_cm':raw,'mu_cm':c.mu,'sd_cm':c.snapshot()['sd_cm'],'action':action,'reason':c.reason})
        if action in ('DONE','ABORT'): break
        if action=='MOVE':
            d-=max(0,speed*.12+.15+motion.gauss(0,.20))
            if d<=0: contacts+=1
            c.record_move(.12);time+=.32
        else: time+=.15
    else: action='ABORT';c.reason='simulation_cap'
    row={'seed':seed,'policy':policy,'context':context,'scenario':'bias_stress' if stress else 'nominal',
         'terminal':action,'reason':c.reason,'final_cm':d,'absolute_error_cm':abs(d-25),
         'independent_success':int(action=='DONE' and abs(d-25)<=4),
         'false_verified':int(action=='DONE' and abs(d-25)>4),'wall_contacts':contacts,
         'time_s':time,'samples':samples,'moves':c.moves}
    return (row,log) if trace else row

def write_csv(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    rows=[episode(seed,p,c,s) for s in (False,True) for c in ('normal','careful') for p in POLICIES for seed in range(300)]
    write_csv(OUT/'simulation_trials.csv',rows)
    summary=[]
    for s in ('nominal','bias_stress'):
        for context in ('normal','careful'):
            for policy in POLICIES:
                rr=[r for r in rows if r['scenario']==s and r['context']==context and r['policy']==policy]
                row={'scenario':s,'context':context,'policy':policy,'n':len(rr)}
                for key in ('independent_success','false_verified','absolute_error_cm','time_s','samples','moves','wall_contacts'):
                    row[key]=sum(r[key] for r in rr)/len(rr)
                row['aborted']=sum(r['terminal']=='ABORT' for r in rr)/len(rr)
                summary.append(row)
    write_csv(OUT/'simulation_summary.csv',summary)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(2,2,figsize=(10,6.5),layout='constrained')
    for a,key,title in zip(ax.flat,['independent_success','time_s','false_verified','aborted'],['Verified AND within target band','Mean trial time (s)','False verification rate','Aborted / inconclusive rate']):
        for j,s in enumerate(['nominal','bias_stress']):
            vals=[next(r[key] for r in summary if r['scenario']==s and r['policy']==p and r['context']=='normal') for p in POLICIES]
            a.bar(np.arange(3)+(j-.5)*.34,vals,.34,color=['#0D8080','#C97200'][j],label=['Nominal','+5 cm bias stress'][j])
        a.set_xticks(range(3),['Raw','Belief','Mini']);a.set_title(title);a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
    ax[0,0].legend(frameon=False,fontsize=8)
    fig.suptitle('Synthetic software benchmark • 300 trials per group • no hardware results')
    for ext in ['png','pdf']:fig.savefig(AS/f'benchmark.{ext}',dpi=180)
    plt.close(fig)
    r,trace=episode(7,'mini','normal',trace=True);write_csv(OUT/'example_trace.csv',trace)
    fig,ax=plt.subplots(figsize=(10,4),layout='constrained')
    t=np.array([x['time_s'] for x in trace]);mu=np.array([x['mu_cm'] if x['mu_cm'] is not None else np.nan for x in trace]);sd=np.array([x['sd_cm'] for x in trace])
    ax.plot(t,[x['true_cm'] for x in trace],color='#0F1E2E',label='Simulator truth')
    ax.plot(t,mu,color='#0D8080',label='Distance belief')
    ax.fill_between(t,mu-1.96*sd,mu+1.96*sd,color='#17C4B0',alpha=.22,label='Nominal model interval')
    ax.scatter(t,[np.nan if x['raw_cm'] is None else x['raw_cm'] for x in trace],s=8,color='#C97200',alpha=.6,label='Noisy observations')
    ax.axhspan(21,29,color='#0D8080',alpha=.10);ax.axhline(25,ls='--',color='#0F1E2E')
    ax.set(xlabel='Simulated elapsed time (s)',ylabel='Sensor-to-wall distance (cm)',title='One preselected synthetic trial • seed 7 • '+r['terminal'])
    ax.legend(frameon=False,ncol=2,fontsize=8)
    for ext in ['png','pdf']:fig.savefig(AS/f'belief_trace.{ext}',dpi=180)
    plt.close(fig)
    manifest={'python':platform.python_version(),'numpy':np.__version__,'seeds':[0,299],'trials':len(rows),
              'source_sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),R/'firmware/belief_controller.py']},
              'warning':'Synthetic feasibility only; no empirical fit or hardware validation. Bias stress intentionally challenges the observation model.'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
