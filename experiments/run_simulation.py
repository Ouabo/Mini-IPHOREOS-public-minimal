"""Independent calibration, locked evaluation, matched random streams. Desktop only."""
from pathlib import Path
import sys,json,csv,random,math,time,hashlib,argparse
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'baseline_v1'/'firmware'))
from cognitive.controller import CognitiveController
from cognitive.baselines import FairRuleBaseline
from belief_controller import Controller

POLICIES=('v1','v1_fair','adaptive','adaptive_no_information','ext1_no_information','ext1','ext1_memory','ext1_memory_fast','ext1_bias_ref')
SCENARIOS=('normal','slow','switch','recovery','dropout','bias')
# Diagnostic-only scenarios: not part of the original six-scenario success/
# false-verification comparison, so kept in a separate tuple rather than mixed
# into SCENARIOS (which many summaries and the comparison plot assume is the
# fairness-comparison set).
DIAGNOSTIC_SCENARIOS=('repeated','intermediate','bias_random','outlier')
P_OUTLIER=0.05  # 'outlier' scenario: per-step probability of a corrupted-but-
                 # present reading (distinct from 'dropout', a missing one).
# (contexts, informative, context_memory, fast_switch) for every
# CognitiveController-backed policy; v1 and v1_fair are built separately below
# since they are not CognitiveController. ext1_bias_ref additionally gets a
# pre-trial bias-reference check (see BIAS_REFERENCE_POLICIES, episode()).
_COGNITIVE_VARIANTS={'adaptive':(False,True,False,False),'adaptive_no_information':(False,False,False,False),
                     'ext1_no_information':(True,False,False,False),'ext1':(True,True,False,False),
                     'ext1_memory':(True,True,True,False),'ext1_memory_fast':(True,True,True,True),
                     'ext1_bias_ref':(True,True,False,False)}
BIAS_REFERENCE_POLICIES={'ext1_bias_ref'}
REF_DISTANCE=50.  # known reference distance for the bias check; well inside
                   # the 12-150 cm valid range, clear of the task's own 25 cm
                   # target and 55-130 cm start range.
N_REF=5  # reference readings taken once, before the main approach loop.

def make_controller(policy,cal,target=25.,band=4.):
    if policy=='v1':
        return Controller('mini','normal',dict(sensor_bias_cm=cal['sensor_bias'],measurement_var=cal['sensor_var'],
            speed_cm_s=cal['speed_normal'],coast_cm=cal['coast'],motion_var=cal['motion_var'],timeout_s=80.,max_moves=100))
    if policy=='v1_fair':
        return FairRuleBaseline(cal,target=target,band=band)
    contexts,informative,context_memory,fast_switch=_COGNITIVE_VARIANTS[policy]
    return CognitiveController(cal,contexts=contexts,informative=informative,context_memory=context_memory,fast_switch=fast_switch,target=target,band=band)

def calibrate(out):
    rng=np.random.default_rng(1701)
    errors=rng.normal(0,1.2,160)
    sensor_rows=[dict(true_cm=(20,30,50,80)[i//40],raw_cm=(20,30,50,80)[i//40]+float(e)) for i,e in enumerate(errors)]
    motion_rows=[]
    for label,v in [('normal',8.),('slow',3.)]:
        for _ in range(80):
            speed=max(.1,float(rng.normal(v,.5)))
            coast=float(rng.normal(.15,.025))
            motion_rows.append(dict(context=label,duration=.24,powered_distance=speed*.24,coast=coast))
    cal=dict(sensor_bias=float(errors.mean()),sensor_var=float(errors.var(ddof=1)),coast=float(np.mean([r['coast'] for r in motion_rows])),motion_var=.04)
    for label in ('normal','slow'):
        cal['speed_'+label]=float(np.mean([r['powered_distance']/r['duration'] for r in motion_rows if r['context']==label]))
    write_csv(out/'calibration_sensor.csv',sensor_rows);write_csv(out/'calibration_motion.csv',motion_rows)
    (out/'calibration.json').write_text(json.dumps(cal,indent=2))
    return cal

def write_csv(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)

SEGMENT_MOVES=8  # 'repeated' scenario: moves per normal/slow segment

def true_speed_and_context(scenario,nmove,factor):
    """True speed and the slow/normal label, generalised across scenarios.

    'repeated' alternates normal/slow every SEGMENT_MOVES moves, to test
    whether a context's memory is reused faster on its second+ visit.
    'intermediate' holds a constant speed between the two calibrated regimes,
    to check the filter degrades gracefully rather than forcing a false
    confident label.
    """
    if scenario=='repeated':
        slowed=(nmove//SEGMENT_MOVES)%2==1
        return (3. if slowed else 8.)*factor,slowed
    if scenario=='intermediate':
        return 5.5*factor,False
    slowed=scenario=='slow' or scenario=='switch' and nmove>=12 or scenario=='recovery' and nmove<12
    return (3. if slowed else 8.)*factor,slowed

def reconvergence_times(logs,tol=1.5,sustain=3):
    """Decisions from the start of each 'repeated'-scenario segment until the
    estimated speed is within tol of that segment's true speed for `sustain`
    consecutive decisions. None if it never (re)converges within the segment.
    This is the direct test of "faster reuse, not just accurate
    classification": compare decisions across visits to the same regime.
    """
    by_segment={}
    for entry in logs:
        by_segment.setdefault(entry['segment_index'],[]).append(entry)
    results=[]
    for seg_idx,entries in sorted(by_segment.items()):
        true_v=entries[0]['simulator_true_speed']
        streak=0;converge_at=None
        for i,e in enumerate(entries):
            est=e.get('estimated_speed')
            if est is not None and abs(est-true_v)<tol:
                streak+=1
                if streak>=sustain:converge_at=i-sustain+1;break
            else:streak=0
        results.append(dict(segment_index=seg_idx,true_speed=true_v,decisions=converge_at,segment_entries=len(entries)))
    return results

def episode(seed,scenario,policy,cal,trace=False,target=25.,band=4.,start_range=None,controller=None,deployment_factor=1.0):
    rng=random.Random(seed);sensor=random.Random(seed+100000);motor=random.Random(seed+200000)
    # 'repeated' needs enough distance that several normal/slow segments play
    # out before the task could finish; it is a tracking diagnostic, not part
    # of the six-scenario success/false-verification fairness comparison.
    # Capped below 150 cm: the controllers' own valid-reading range tops out
    # there, so anything higher is rejected as an invalid sensor reading.
    if start_range is not None:
        d=rng.uniform(*start_range)
    else:
        d=rng.uniform(100,130) if scenario=='repeated' else rng.uniform(55,80)
    # deployment_factor (default 1.0, a no-op): a persistent per-deployment speed
    # multiplier, distinct from the per-trial factor below -- see
    # experiments/run_transfer_validation.py, where it carries a true/false-start
    # speed bias that calibration's own pooled-mean estimate cannot see, shared
    # between one deployment's Task A training and its Task B evaluation.
    factor=rng.uniform(.9,1.1)*deployment_factor
    # An unknown deployment-time bias beyond what static calibration (cal
    # ['sensor_bias']) already captures: a fixed +5 cm for 'bias' (the original
    # scenario), a fresh per-trial draw for 'bias_random' (tests whether a
    # reference generalises beyond that one fixed offset), zero otherwise.
    if scenario=='bias':extra_bias=5.
    elif scenario=='bias_random':extra_bias=rng.uniform(-8.,8.)
    else:extra_bias=0.
    c=controller if controller is not None else make_controller(policy,cal,target=target,band=band)
    ref_decisions=0;ref_time=0.;bias_estimate=None
    if controller is None and policy in BIAS_REFERENCE_POLICIES:
        # Same physical sensor, same noise model, pointed at a known distance
        # instead of the wall -- not an oracle read of simulator truth.
        ref_readings=[REF_DISTANCE+extra_bias+sensor.gauss(0,1.2) for _ in range(N_REF)]
        bias_estimate,_=c.calibrate_bias(ref_readings,REF_DISTANCE)
        ref_decisions=N_REF;ref_time=N_REF*.15
    t=0.;nmove=0;contacts=0;logs=[];runtime=0;detected=None;false_alert=False
    for step in range(350):
        v,slowed=true_speed_and_context(scenario,nmove,factor)
        reading=d+extra_bias+sensor.gauss(0,1.2)
        if scenario=='outlier' and sensor.random()<P_OUTLIER:reading+=sensor.uniform(-20,20)
        if sensor.random() < (.12 if scenario=='dropout' else .02):reading=None
        start=time.perf_counter()
        if policy=='v1':
            action=c.observe(reading,t);dt=.12 if action=='MOVE' else 0.
            entry=dict(estimated_distance=c.mu,estimated_speed=cal['speed_normal'],distance_sd=math.sqrt(c.var) if c.mu is not None else None,intended_option=action,realised_event=c.reason)
        else:
            action,dt=c.step(reading,t);entry=dict(c.memory[-1])
            probs=entry['context_probabilities'];ps=probs.get('slow',0.)
            # Descriptive first threshold crossing, not guaranteed detection.
            if scenario=='switch' and nmove>=12 and ps>.8 and detected is None:detected=t
            if not slowed and ps>.8:false_alert=True
        runtime+=time.perf_counter()-start
        logs.append(dict(entry,simulator_true_distance=d,simulator_slow_context=slowed,simulator_true_speed=v,segment_index=nmove//SEGMENT_MOVES,moves_completed=nmove,simulator_time=t))
        if action in ('DONE','ABORT'):break
        if t>=80:action='ABORT';break
        if action=='MOVE':
            d-=max(0,v*dt+cal['coast']+motor.gauss(0,.08));contacts+=int(d<=0);nmove+=1
            if policy=='v1':c.record_move(dt)
            t+=dt+.20
        else:t+=.15
    else:action='ABORT'
    switch_times=[r['simulator_time'] for r in logs if r['moves_completed']>=12]
    delay=detected-switch_times[0] if detected is not None and switch_times else None
    row=dict(seed=seed,scenario=scenario,policy=policy,success=int(action=='DONE' and target-band<=d<=target+band),false_verified=int(action=='DONE' and not target-band<=d<=target+band),aborted=int(action!='DONE'),final_cm=d,absolute_error=abs(d-target),time_s=t,moves=nmove,readings=len(logs),contacts=contacts,compute_ms=runtime*1000,context_delay_s=delay,false_context_alert=int(false_alert),true_extra_bias=extra_bias,bias_estimate=bias_estimate,bias_estimate_error=abs(bias_estimate-extra_bias) if bias_estimate is not None else None,reference_decisions=ref_decisions,reference_time_s=ref_time)
    reconv=[dict(seed=seed,policy=policy,scenario=scenario,**r) for r in reconvergence_times(logs)] if scenario=='repeated' else None
    return row,logs,reconv

def build_parser():
    p=argparse.ArgumentParser()
    p.add_argument('--trials',type=int,default=100)
    p.add_argument('--seed-start',type=int,default=10000,help='First seed of the trial range (default: the development range used throughout this project). Use a disjoint value (e.g. 50000) for a genuinely held-out evaluation.')
    p.add_argument('--out-dir',type=str,default='results_ext1',help='Output directory, relative to the project root (default: results_ext1, the existing development results). Use a different directory for a held-out run so it never overwrites the development results.')
    return p

def main():
    p=build_parser()
    a=p.parse_args()
    if a.trials<2:p.error('Use at least two trials')
    seed0=a.seed_start
    out=ROOT/a.out_dir;out.mkdir(exist_ok=True);cal=calibrate(out)
    rows=[];reconv_rows=[]
    for scenario in SCENARIOS+DIAGNOSTIC_SCENARIOS:
        for policy in POLICIES:
            for seed in range(seed0,seed0+a.trials):
                row,logs,reconv=episode(seed,scenario,policy,cal);rows.append(row)
                if reconv:reconv_rows.extend(reconv)
                if seed==seed0:(out/f'trace_{scenario}_{policy}.json').write_text(json.dumps(logs,indent=2),encoding='utf-8')
        print(scenario,'complete',flush=True)
    write_csv(out/'trials.csv',rows)
    if reconv_rows:
        write_csv(out/'reconvergence.csv',reconv_rows)
        agg=[]
        for policy in POLICIES:
            for seg in sorted(set(r['segment_index'] for r in reconv_rows)):
                converged=[r['decisions'] for r in reconv_rows if r['policy']==policy and r['segment_index']==seg and r['decisions'] is not None]
                total=[r for r in reconv_rows if r['policy']==policy and r['segment_index']==seg]
                agg.append(dict(policy=policy,segment_index=seg,regime='slow' if seg%2 else 'normal',
                    n_total=len(total),n_converged=len(converged),
                    mean_decisions=float(np.mean(converged)) if converged else None))
        write_csv(out/'reconvergence_summary.csv',agg)
    summaries=[]
    for scenario in SCENARIOS:
        for policy in POLICIES:
            rr=[r for r in rows if r['scenario']==scenario and r['policy']==policy]
            z=dict(scenario=scenario,policy=policy,n=len(rr))
            for key in ('success','false_verified','aborted','absolute_error','time_s','moves','readings','compute_ms','false_context_alert'):
                z[key]=float(np.mean([r[key] for r in rr]))
            z['context_detected']=sum(r['context_delay_s'] is not None for r in rr)
            summaries.append(z)
    write_csv(out/'summary.csv',summaries)
    # Bias-reference evaluation: 'bias' (fixed +5 cm) and 'bias_random' (fresh
    # per-trial offset) for ext1 vs ext1_bias_ref, plus the reference's own
    # cost and estimation accuracy -- a direct cost/benefit report, not just a
    # pass/fail success-rate comparison.
    bias_rows=[r for r in rows if r['scenario'] in ('bias','bias_random') and r['policy'] in ('ext1','ext1_bias_ref')]
    if bias_rows:
        bias_summary=[]
        for scenario in ('bias','bias_random'):
            for policy in ('ext1','ext1_bias_ref'):
                rr=[r for r in bias_rows if r['scenario']==scenario and r['policy']==policy]
                if not rr:continue
                errs=[r['bias_estimate_error'] for r in rr if r['bias_estimate_error'] is not None]
                bias_summary.append(dict(scenario=scenario,policy=policy,n=len(rr),
                    success=float(np.mean([r['success'] for r in rr])),
                    false_verified=float(np.mean([r['false_verified'] for r in rr])),
                    mean_bias_estimate_error=float(np.mean(errs)) if errs else None,
                    mean_reference_decisions=float(np.mean([r['reference_decisions'] for r in rr])),
                    mean_reference_time_s=float(np.mean([r['reference_time_s'] for r in rr]))))
        write_csv(out/'bias_reference_summary.csv',bias_summary)
    # Outlier-robustness evaluation: a diagnostic scenario (not in SCENARIOS),
    # so it needs its own aggregation, same as reconvergence/bias-reference.
    outlier_rows=[r for r in rows if r['scenario']=='outlier']
    if outlier_rows:
        outlier_summary=[]
        for policy in POLICIES:
            rr=[r for r in outlier_rows if r['policy']==policy]
            if not rr:continue
            outlier_summary.append(dict(policy=policy,n=len(rr),
                success=float(np.mean([r['success'] for r in rr])),
                false_verified=float(np.mean([r['false_verified'] for r in rr])),
                aborted=float(np.mean([r['aborted'] for r in rr])),
                moves=float(np.mean([r['moves'] for r in rr]))))
        write_csv(out/'outlier_summary.csv',outlier_summary)
    contrasts=[];boot=np.random.default_rng(99)
    for scenario in SCENARIOS:
        for comparator in ('v1','v1_fair','adaptive','adaptive_no_information','ext1_no_information','ext1_memory','ext1_memory_fast','ext1_bias_ref'):
            aa=[r['success'] for r in rows if r['scenario']==scenario and r['policy']=='ext1']
            bb=[r['success'] for r in rows if r['scenario']==scenario and r['policy']==comparator]
            diff=np.array(aa)-np.array(bb);bs=diff[boot.integers(0,len(diff),(2000,len(diff)))].mean(axis=1)
            contrasts.append(dict(scenario=scenario,comparator=comparator,difference=float(diff.mean()),lo=float(np.quantile(bs,.025)),hi=float(np.quantile(bs,.975))))
    write_csv(out/'paired_success_differences.csv',contrasts)
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(15,4),layout='constrained')
    width=.8/len(POLICIES)
    for j,metric in enumerate(('success','false_verified')):
        for k,policy in enumerate(POLICIES):
            axes[j].bar(np.arange(len(SCENARIOS))+(k-(len(POLICIES)-1)/2)*width,[r[metric] for r in summaries if r['policy']==policy],width,label=policy)
        axes[j].set_xticks(range(len(SCENARIOS)),SCENARIOS,rotation=20);axes[j].set_ylim(0,1.05);axes[j].set_title(metric.replace('_',' '));axes[j].grid(axis='y',alpha=.2)
    axes[0].legend(fontsize=8);fig.suptitle('EXT1 — synthetic evaluation; no hardware evidence')
    fig.savefig(out/'comparison.png',dpi=160);plt.close(fig)
    manifest=dict(trials=len(rows),seeds=[seed0,seed0+a.trials-1],calibration_seed=1701,policies=POLICIES,scenarios=SCENARIOS,diagnostic_scenarios=DIAGNOSTIC_SCENARIOS,notes='Exploratory synthetic evaluation. Exploratory development: seeds reused after a numerical-test correction and comparator-design correction; not an independent confirmatory experiment. Paired percentile-bootstrap intervals are descriptive, unadjusted for multiplicity; all-identical outcomes can yield degenerate intervals. This does not prove zero uncertainty. Contexts are prescribed families, not discovered.',source_sha256={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [ROOT/'cognitive/model.py',ROOT/'cognitive/controller.py',ROOT/'cognitive/baselines.py',Path(__file__)]})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Saved',len(rows),'trials',flush=True)

if __name__=='__main__':main()
