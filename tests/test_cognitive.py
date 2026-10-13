import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cognitive.model import Belief
from cognitive.controller import CognitiveController
from cognitive.baselines import FairRuleBaseline

CAL=dict(sensor_bias=0.,sensor_var=1.44,speed_normal=8.,speed_slow=3.,coast=.15,motion_var=.04)

def _run_episode(controller,true_distance,max_steps=400):
    d=true_distance;t=0.;action='SAMPLE'
    for _ in range(max_steps):
        action,dt=controller.step(d,t)
        if action in ('DONE','ABORT'):break
        if action=='MOVE':d-=CAL['speed_normal']*dt+CAL['coast'];t+=dt+.20
        else:t+=.15
    return action,d,t

def test_context_inference_and_covariance():
    b=Belief(CAL);d=70.;b.observe(d)
    for _ in range(45):
        b.predict(.24);d-=3*.24+.15;b.observe(d)
        assert abs(sum(b.weights)-1)<1e-10
        assert all(np.linalg.eigvalsh(p).min()>-1e-10 for p in b.covs)
    assert b.weights[1]>.8
    assert abs(b.moments()[0][1]-3)<1

def test_stationary_sampling_does_not_identify_speed():
    b=Belief(CAL);b.observe(50)
    for _ in range(10):b.observe(50)
    assert np.allclose(b.weights,[.8,.2])

def test_unknown_constant_bias_not_magically_removed():
    a=Belief(CAL);b=Belief(CAL)
    for i in range(15):
        if i:a.predict(.12);b.predict(.12)
        a.observe(60-i*1.11);b.observe(65-i*1.11)
    assert abs((b.moments()[0][0]-a.moments()[0][0])-5)<1e-7

def test_invalid_readings_abort_and_latch():
    c=CognitiveController(CAL)
    assert c.step(None,0)[0]=='SAMPLE'
    assert c.step(None,.15)[0]=='SAMPLE'
    assert c.step(None,.3)[0]=='ABORT'
    assert c.step(70,.45)[0]=='ABORT'

def test_target_verifies_without_movement():
    c=CognitiveController(CAL)
    actions=[c.step(25,i*.15)[0] for i in range(3)]
    assert actions==['SAMPLE','SAMPLE','DONE']
    assert c.moves==0

def test_realised_and_intended_are_separate():
    c=CognitiveController(CAL);a,dt=c.step(70,0)
    assert a=='MOVE' and 0<dt<=.24
    assert c.memory[-1]['realised_event']=='initial_reading'
    assert c.memory[-1]['intended_option']=='MOVE'

def test_predicted_does_not_mutate_belief():
    b=Belief(CAL);b.observe(70.)
    states_before=b.states.copy();covs_before=b.covs.copy();weights_before=b.weights.copy()
    b.predicted(.24)
    assert np.array_equal(b.states,states_before)
    assert np.array_equal(b.covs,covs_before)
    assert np.array_equal(b.weights,weights_before)

def test_no_information_planner_makes_progress_instead_of_stalling():
    # Regression guard for the short-horizon planner + no-progress cost: with
    # informative=False, a one-step planner could get stuck preferring
    # repeated SAMPLE forever. The receding-horizon planner must still move.
    c=CognitiveController(CAL,contexts=True,informative=False)
    action,d,t=_run_episode(c,70.)
    assert c.moves>=3
    assert d<60.

def test_adaptive_no_information_runs_end_to_end():
    # Completes the (contexts, informative) 2x2 factorial used to attribute
    # EXT1's behaviour to context inference vs. information-seeking.
    c=CognitiveController(CAL,contexts=False,informative=False)
    action,d,t=_run_episode(c,70.)
    assert action in ('DONE','ABORT')
    assert t<=80+1e-6
    assert c.moves<=100

def test_fair_rule_baseline_runs_end_to_end():
    c=FairRuleBaseline(CAL)
    action,d,t=_run_episode(c,70.)
    assert action in ('DONE','ABORT')
    assert t<=80+1e-6
    assert c.moves<=100
    assert c.memory[-1]['context_probabilities']=={}

def test_fair_rule_baseline_can_use_the_longer_pulse():
    c=FairRuleBaseline(CAL)
    action,dt=c.step(70.,0.)
    assert action=='MOVE' and dt==.24

def test_context_library_persists_while_inactive():
    # Regression guard for the bug this milestone fixes: without a persistent
    # library, a context's learned speed is corrupted by cross-context mixing
    # within a handful of steps once it stops being observed (confirmed before
    # this fix: 2.0 -> 2.886 after 1 step, -> 4.09 by step 10). The library
    # must not move at all while there is no evidence for that context.
    b=Belief(CAL,memory=True)
    b.lib_mean[1]=2.0
    for _ in range(20):b.predict(.24)
    assert b.lib_mean[1]==2.0

def test_context_library_updates_only_when_confident():
    # Ambiguous evidence (weights below the confidence gate) must never move
    # the library, however informative the per-component state looks.
    b=Belief(CAL,memory=True)
    b.weights=np.array([.5,.5])
    b.states[:,1]=[2.0,2.0]
    before=b.lib_mean.copy()
    b._update_library()
    assert np.array_equal(b.lib_mean,before)

def test_context_library_updates_when_confidently_active():
    b=Belief(CAL,memory=True)
    b.weights=np.array([.1,.9])
    b.states[1,1]=2.0
    before=b.lib_mean[1]
    b2_var_before=b.lib_var[1]
    b._update_library()
    assert b.lib_mean[1]!=before
    assert abs(b.lib_mean[1]-2.0)<abs(before-2.0)
    assert b.lib_var[1]<b2_var_before

def test_cusum_ignores_small_isolated_evidence():
    # A single modest advantage for the challenger, below slack+threshold,
    # must not accumulate into a jump, and a subsequent negative step for the
    # same candidate must not leave a residual that later causes one either.
    b=Belief(CAL,memory=True,fast_switch=True)
    b.weights=np.array([.8,.2])
    b.lib_mean[1]=2.5;b.lib_var[1]=0.5  # mature library: a jump would be allowed
    b._update_cusum(np.array([0.,0.3]))
    assert b.weights[1]!=Belief.JUMP_WEIGHT
    b._update_cusum(np.array([0.,-5.]))  # strongly against the challenger now
    assert b.cusum[1]==0.
    assert b.weights[1]!=Belief.JUMP_WEIGHT

def test_cusum_jumps_on_sustained_evidence_with_mature_library():
    b=Belief(CAL,memory=True,fast_switch=True)
    b.weights=np.array([.8,.2])
    b.lib_mean[1]=2.5;b.lib_var[1]=0.5  # mature: library has been learned before
    for _ in range(6):
        if b.weights[1]==Belief.JUMP_WEIGHT:break
        b._update_cusum(np.array([0.,0.3]))
    assert b.weights[1]==Belief.JUMP_WEIGHT
    assert b.states[1,1]==2.5  # reused the library value directly
    assert np.all(b.cusum==0.)  # accumulators reset after acting

def test_cusum_never_jumps_into_an_immature_library():
    b=Belief(CAL,memory=True,fast_switch=True)
    b.weights=np.array([.8,.2])
    # lib_var left at its default LIB_VAR_INIT: never confidently learned before.
    assert b.lib_var[1]==Belief.LIB_VAR_INIT
    for _ in range(10):
        b._update_cusum(np.array([0.,0.3]))
    assert b.weights[1]!=Belief.JUMP_WEIGHT

def test_fast_switch_defaults_off():
    b=Belief(CAL,memory=True)
    assert b.fast_switch is False
    c=CognitiveController(CAL)
    assert c.belief.fast_switch is False

def test_reconvergence_instrumentation_is_well_formed():
    # Sanity check for the segment-reconvergence bookkeeping used to evaluate
    # the "faster reuse" claim empirically (results_ext1/reconvergence.csv);
    # does not assert which policy is faster -- that is an empirical question
    # for the full simulation, reported in results_ext1/reconvergence_summary.csv,
    # not something to bake into a unit-test assertion.
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
    from run_simulation import reconvergence_times
    logs=[dict(segment_index=0,simulator_true_speed=8.,estimated_speed=v) for v in [2.,8.1,7.9,8.0]]
    logs+=[dict(segment_index=1,simulator_true_speed=3.,estimated_speed=v) for v in [8.,3.1,2.9,3.0]]
    results=reconvergence_times(logs,tol=1.5,sustain=3)
    assert results[0]['decisions']==1
    assert results[1]['decisions']==1

def test_bias_reference_defaults_do_not_change_belief():
    # Non-regression: before set_bias_reference is ever called, extra_bias_mean
    # /extra_bias_var must be exactly zero, so observe()/information() are
    # numerically identical to the pre-bias-reference implementation.
    a=Belief(CAL);b=Belief(CAL)
    assert a.extra_bias_mean==0. and a.extra_bias_var==0.
    for d in (70.,68.,64.,60.):
        a.observe(d);b.observe(d)
    assert np.array_equal(a.states,b.states) and np.array_equal(a.covs,b.covs)
    assert a.information(.24)==b.information(.24)

def test_calibrate_bias_recovers_a_known_offset():
    c=CognitiveController(CAL)
    true_offset=5.0
    readings=[50.+true_offset+e for e in (-0.6,0.3,-0.1,0.5,-0.1)]  # mean offset 0.0 cm of noise
    mean,var=c.calibrate_bias(readings,ref_distance=50.)
    assert abs(mean-true_offset)<0.5
    assert abs(var-CAL['sensor_var']/5)<1e-9
    assert c.belief.extra_bias_mean==mean and c.belief.extra_bias_var==var
    # More readings should not increase the estimated variance.
    _,var10=c.calibrate_bias(readings*2,ref_distance=50.)
    assert var10<var

def test_bias_reference_uncertainty_widens_the_belief():
    # The propagation this milestone is about: a reference's own imprecision
    # must inflate P, not just shift the point estimate.
    a=Belief(CAL);b=Belief(CAL)
    b.set_bias_reference(0.,2.0)
    a.observe(70.);b.observe(70.)
    a.observe(68.);b.observe(68.)
    assert b.moments()[1][0,0]>a.moments()[1][0,0]

def test_outlier_reading_is_rejected_by_the_innovation_gate():
    # The 'outlier' scenario (experiments/run_simulation.py) corrupts an
    # otherwise-present reading by up to +-20 cm; this must be large enough
    # that Belief's existing innovation gate (not a new mechanism) catches it,
    # confirming the scenario actually exercises robustness rather than
    # silently passing corrupted data straight into the filter.
    b=Belief(CAL);b.observe(70.)
    for _ in range(5):b.predict(.24);b.observe(68.)
    accepted=b.observe(68.+20.)  # a worst-case +20 cm outlier draw
    assert accepted is False

def test_cli_defaults_match_the_development_configuration():
    # Non-regression for the held-out-evaluation CLI: an invocation with
    # neither flag must reproduce today's development configuration exactly,
    # so every number already published in the tutorial/math companion stays
    # reproducible with the plain `python experiments/run_simulation.py` command.
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
    from run_simulation import build_parser
    a=build_parser().parse_args([])
    assert a.seed_start==10000
    assert a.out_dir=='results_ext1'
    assert a.trials==100

def test_target_band_defaults_match_task_a():
    # Non-regression for the O3 transfer-validation parametrisation: with no
    # target/band given, both controllers must reproduce Task A's original
    # hardcoded boundary (verify at 25+-4, overshoot-abort below 21) exactly.
    c=CognitiveController(CAL)
    assert c.target==25. and c.band==4.
    f=FairRuleBaseline(CAL)
    assert f.target==25. and f.band==4.

def test_nondefault_target_band_shifts_the_verify_boundary():
    # Task B's target (85, band 4): verification must trigger near 85, not 25,
    # and the overshoot-abort floor must move to target-band (81), not 21.
    c=CognitiveController(CAL,target=85.,band=4.)
    action,d,t=_run_episode(c,115.)
    assert action=='DONE'
    assert 81.<=d<=89.

def test_memory_frozen_seed_is_read_but_never_rewritten():
    # Core mechanism behind "zero-update transfer" (run_transfer_validation.py):
    # a library seeded directly (no CUSUM jump needed to build it) must still
    # be read as the _advance reversion target and the _jump_to target, but
    # memory_frozen=True must stop _update_library from ever changing it.
    b=Belief(CAL,memory=True,fast_switch=True,memory_frozen=True)
    b.lib_mean[:]=[9.0,2.0];b.lib_var[:]=[0.3,0.3]  # seeded "prior experience"
    b.weights=np.array([.1,.9]);b.states[1,1]=2.0
    before=b.lib_mean.copy()
    b._update_library()
    assert np.array_equal(b.lib_mean,before)  # frozen: no write despite confident weight
    # still read continuously as the mean-reversion target in _advance:
    states,covs,weights=b._advance(.24,b.states,b.covs,b.weights)
    assert abs(states[1,1]-2.0)<abs(b.states[1,1]-9.0)  # pulled toward lib_mean[1]=2.0, not calibration's 8/3
    # still read as the jump target:
    b.cusum[1]=Belief.CUSUM_THRESHOLD+0.1
    b.weights=np.array([.8,.2])
    b._update_cusum(np.array([0.,1.0]))
    assert b.states[1,1]==2.0

def test_deployment_factor_default_is_a_no_op():
    # Non-regression for run_transfer_validation.py's persistent per-deployment
    # speed bias: the default (1.0) must reproduce an episode byte-identical
    # to calling episode() without the argument at all.
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
    from run_simulation import episode
    cal=dict(CAL)
    row_a,_,_=episode(10000,'normal','ext1',cal)
    row_b,_,_=episode(10000,'normal','ext1',cal,deployment_factor=1.0)
    for key in row_a:
        if key=='compute_ms':continue
        assert row_a[key]==row_b[key]

def test_deployment_factor_scales_the_simulated_true_speed():
    # Confirms deployment_factor actually reaches the simulated physics (not
    # just the signature): with the same seed, the same rng stream draws the
    # same per-trial factor, so true speed at every step must scale by
    # exactly the ratio of the two deployment_factor values.
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
    from run_simulation import episode
    cal=dict(CAL)
    _,logs_base,_=episode(10000,'normal','ext1',cal,deployment_factor=1.0)
    _,logs_scaled,_=episode(10000,'normal','ext1',cal,deployment_factor=0.7)
    for a,b in zip(logs_base,logs_scaled):
        assert abs(b['simulator_true_speed']-0.7*a['simulator_true_speed'])<1e-9

def test_post_switch_reconvergence_measures_decisions_from_the_switch_point():
    # run_transfer_validation.py's sharper transfer metric: decisions_to_target
    # is dominated by raw travel distance and swamps any few-decision
    # recognition-speed advantage, so this isolates convergence of the speed
    # estimate alone, counted from the scenario's one switch point (the same
    # moves_completed>=12 threshold true_speed_and_context uses).
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
    from run_transfer_validation import post_switch_reconvergence
    def make_logs(speeds_after_switch):
        logs=[dict(moves_completed=i,simulator_true_speed=8.,estimated_speed=8.) for i in range(12)]
        logs+=[dict(moves_completed=12+i,simulator_true_speed=3.,estimated_speed=s) for i,s in enumerate(speeds_after_switch)]
        return logs
    fast=make_logs([3.1,3.0,2.9]+[3.0]*5)
    slow=make_logs([7.0,6.0,5.0,4.0,3.1,3.0,2.9]+[3.0]*5)
    never=make_logs([7.0]*10)
    assert post_switch_reconvergence(fast)==0
    assert post_switch_reconvergence(slow)==3
    assert post_switch_reconvergence(fast)<post_switch_reconvergence(slow)
    assert post_switch_reconvergence(never) is None
