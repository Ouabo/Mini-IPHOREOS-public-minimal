"""O3 preliminary evidence: does the context library learned on Task A
transfer to Task B, a different goal on the same physics?

Each of the project's standard 100 development seeds (10000-10099) is treated
as its own "deployment": a persistent, per-deployment speed multiplier
(deployment_factor, frozen range in docs/FROZEN_PARAMETERS.md) shifts the true
speed in both that deployment's Task A training and its Task B evaluation, but
is invisible to the static calibration step (a precise pooled-mean estimate
over 80 pulses) -- calibration cannot see it, so a cold-start belief starts
from a provably wrong prior. Three conditions, each run on Task B (target=85cm,
band=4cm, start=(115,145)cm -- frozen) under that deployment's own bias:

  - cold_start: a fresh ext1_memory_fast controller, empty library, faces the
    deployment's real bias with no prior exposure to it.
  - zero_update_transfer: library seeded from that deployment's Task-A-trained
    checkpoint (see build_checkpoint below), memory_frozen=True -- read but
    never rewritten, i.e. transfer without adaptation.
  - adapt_with_updates: same seeded starting point, memory_frozen=False --
    transfer with adaptation left on.

A first pass (one checkpoint shared across all 100 seeds, no persistent bias)
found no measurable difference between the three conditions: the checkpoint
converged to within noise of the untrained calibration prior, so there was
nothing for the library to transfer that cold-start didn't already have for
free (Mathematical_Model_EXT1.tex, Section 10). This version's deployment_factor
exists specifically to give the library something calibration cannot already
supply.

Task B intentionally reuses Task A's sensor/motor model and context structure
unchanged (same normal/slow speeds, same per-trial noise, same context
transition structure) -- only the goal and the persistent deployment bias
differ. Transfer under a genuinely different sensor/surface characteristic
remains out of scope for this pass.

Scope limit, reported honestly either way: if zero-update transfer still does
not beat cold start, that is the finding, not something to tune away.
"""
import random
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cognitive.controller import CognitiveController
from cognitive.model import Belief
from experiments.run_simulation import calibrate, episode, write_csv

DEPLOYMENT_FACTOR_RANGE = (0.6, 0.85)  # persistent per-deployment speed
# multiplier: outside calibration's own sampling noise (SE of the pooled
# 80-pulse mean ~0.056) and outside the existing per-trial Uniform(0.9,1.1)
# factor, so it cannot be mistaken for ordinary trial-to-trial variation.
DEPLOYMENT_SEED_OFFSET = 400000  # deterministic per Task-B seed, disjoint
# from the sensor/motor-stream offsets (+100000/+200000) episode() itself uses.
TRAIN_SEED_BLOCK = 100  # per-deployment Task-A training seeds:
# TASK_A_TRAIN_SEED_START + seed_index*TRAIN_SEED_BLOCK + episode_index;
# must exceed TASK_A_TRAIN_MAX_EPISODES so no two deployments' blocks collide.
TASK_A_TRAIN_SEED_START = 30000  # disjoint from the dev range (10000+) and
                                   # the held-out range (50000+) used elsewhere.
TASK_A_TRAIN_MAX_EPISODES = 20

TASK_B_SEED_START = 10000  # same development seed range used throughout this
                             # project (run_simulation.py's own --seed-start default).
TASK_B_TRIALS = 100
TASK_B_SCENARIOS = ('normal', 'switch')  # 'normal' exercises only the learned
# normal-context speed; 'switch' additionally exercises the slow-context entry
# and the fast CUSUM recognition built in Milestone 2 -- both library entries
# get a chance to show (or fail to show) transfer.

TARGET_B = 85.
BAND_B = 4.
START_RANGE_B = (115., 145.)


def deployment_factor_for(seed):
    return random.Random(seed + DEPLOYMENT_SEED_OFFSET).uniform(*DEPLOYMENT_FACTOR_RANGE)


def _reset_position_state(belief, cal):
    """Episode-boundary reset: a new episode starts at an unrelated physical
    distance, so the position/speed filter (states/covs/weights) and the
    CUSUM accumulator must restart fresh -- but lib_mean/lib_var (the
    persistent library) are deliberately left untouched, since carrying those
    forward across episodes is the entire point of checkpoint-building.
    """
    fresh = Belief(cal, contexts=belief.contexts)
    belief.states = fresh.states.copy()
    belief.covs = fresh.covs.copy()
    belief.weights = fresh.weights.copy()
    belief.initialised = False
    belief.last_innovation = 0.
    belief.cusum = np.zeros(len(belief.means))


def build_checkpoint(cal, seed_index, deployment_factor):
    """Train ext1_memory_fast on Task A's 'repeated' scenario (target=25,
    band=4 -- Task A's own frozen parameters, unchanged), under this
    deployment's own persistent speed bias, across successive independent
    episodes, carrying only the library forward between them (via
    _reset_position_state), until both contexts' library entries are
    confidently updated: lib_var < Belief.LIB_VAR_INIT, the same maturity
    condition already frozen for _jump_to's own gate.
    """
    c = CognitiveController(cal, contexts=True, informative=True, context_memory=True, fast_switch=True)
    episodes_used = 0
    base = TASK_A_TRAIN_SEED_START + seed_index * TRAIN_SEED_BLOCK
    for i in range(TASK_A_TRAIN_MAX_EPISODES):
        seed = base + i
        c.terminal = None
        c.verify = 0
        c.moves = 0
        c.invalid = 0
        c.last_action = 'START'
        c.memory = []
        _reset_position_state(c.belief, cal)
        episode(seed, 'repeated', 'ext1_memory_fast', cal, controller=c, deployment_factor=deployment_factor)
        episodes_used = i + 1
        if np.all(c.belief.lib_var < Belief.LIB_VAR_INIT):
            break
    matured = bool(np.all(c.belief.lib_var < Belief.LIB_VAR_INIT))
    checkpoint = dict(lib_mean=c.belief.lib_mean.copy(), lib_var=c.belief.lib_var.copy())
    return checkpoint, matured, episodes_used


def make_task_b_controller(cal, seed_library=None, frozen=False):
    c = CognitiveController(cal, contexts=True, informative=True, context_memory=True, fast_switch=True,
                             target=TARGET_B, band=BAND_B, memory_frozen=frozen)
    if seed_library is not None:
        c.belief.lib_mean = seed_library['lib_mean'].copy()
        c.belief.lib_var = seed_library['lib_var'].copy()
    return c


def decisions_to_target(logs):
    """First decision (1-indexed) at which the belief's own target-band
    membership test (the same test CognitiveController.step uses for
    'verify_target') is satisfied -- a single-crossing competence measure,
    not the DONE-after-3-consecutive-verifications success criterion.
    """
    for i, entry in enumerate(logs):
        if entry.get('concept_target'):
            return i + 1
    return None


def post_switch_reconvergence(logs, tol=1.5, sustain=3):
    """Decisions from the Task B 'switch' scenario's regime change (the same
    moves_completed>=12 threshold true_speed_and_context uses) until the
    estimated speed is within tol of the new true speed for `sustain`
    consecutive decisions -- exactly run_simulation.py's reconvergence_times
    definition, applied to Task B's one switch point. decisions_to_target is
    dominated by the 30-60cm of travel still needed to reach the target band
    (Section~sec:transfer's diagnosis), which swamps any few-decision
    recognition-speed advantage; this isolates the one quantity Milestone 2
    actually showed the context library speeds up -- regime recognition, not
    estimation precision -- now measured across tasks instead of within one.
    """
    post = [e for e in logs if e['moves_completed'] >= 12]
    if not post:
        return None
    true_v = post[0]['simulator_true_speed']
    streak = 0
    for i, e in enumerate(post):
        est = e.get('estimated_speed')
        if est is not None and abs(est - true_v) < tol:
            streak += 1
            if streak >= sustain:
                return i - sustain + 1
        else:
            streak = 0
    return None


def run_deployment(seed_index, seed, cal):
    """One deployment: build its checkpoint under its own persistent speed
    bias, then run all three conditions on its Task B evaluation under that
    same bias and seed. Cold-start faces the identical real bias; it just
    never learned it from Task A first.
    """
    deployment_factor = deployment_factor_for(seed)
    checkpoint, matured, episodes_used = build_checkpoint(cal, seed_index, deployment_factor)
    if not matured:
        return [], deployment_factor, matured, episodes_used
    rows = []
    conditions = (('cold_start', None, False),
                  ('zero_update_transfer', checkpoint, True),
                  ('adapt_with_updates', checkpoint, False))
    for scenario in TASK_B_SCENARIOS:
        for name, seed_library, frozen in conditions:
            controller = make_task_b_controller(cal, seed_library=seed_library, frozen=frozen)
            row, logs, _ = episode(seed, scenario, 'ext1_memory_fast', cal,
                                    target=TARGET_B, band=BAND_B, start_range=START_RANGE_B,
                                    controller=controller, deployment_factor=deployment_factor)
            rows.append(dict(condition=name, scenario=scenario, seed=seed,
                              deployment_factor=deployment_factor,
                              success=row['success'], moves=row['moves'],
                              decisions_to_target=decisions_to_target(logs),
                              switch_reconvergence=post_switch_reconvergence(logs) if scenario == 'switch' else None))
    return rows, deployment_factor, matured, episodes_used


def summarize(rows):
    summary = []
    conditions = sorted(set(r['condition'] for r in rows),
                         key=lambda c: ['cold_start', 'zero_update_transfer', 'adapt_with_updates'].index(c))
    for condition in conditions:
        for scenario in TASK_B_SCENARIOS:
            rr = [r for r in rows if r['condition'] == condition and r['scenario'] == scenario]
            reached = [r['decisions_to_target'] for r in rr if r['decisions_to_target'] is not None]
            reconverged = [r['switch_reconvergence'] for r in rr if r['switch_reconvergence'] is not None]
            summary.append(dict(condition=condition, scenario=scenario, n=len(rr),
                                 success_rate=float(np.mean([r['success'] for r in rr])),
                                 mean_moves=float(np.mean([r['moves'] for r in rr])),
                                 reached_target_rate=len(reached) / len(rr) if rr else None,
                                 mean_decisions_to_target=float(np.mean(reached)) if reached else None,
                                 reconverged_rate=len(reconverged) / len(rr) if scenario == 'switch' and rr else None,
                                 mean_switch_reconvergence=float(np.mean(reconverged)) if reconverged else None))
    return summary


def main():
    out = ROOT / 'results_transfer'
    out.mkdir(exist_ok=True)
    cal = calibrate(out)

    rows = []
    immature = 0
    for seed_index, seed in enumerate(range(TASK_B_SEED_START, TASK_B_SEED_START + TASK_B_TRIALS)):
        deployment_rows, deployment_factor, matured, episodes_used = run_deployment(seed_index, seed, cal)
        if not matured:
            immature += 1
            continue
        rows += deployment_rows
    print(f'{TASK_B_TRIALS - immature}/{TASK_B_TRIALS} deployments matured and were evaluated '
          f'(deployment_factor in {DEPLOYMENT_FACTOR_RANGE})')
    if immature:
        print(f'WARNING: {immature} deployment(s) did not mature within the training budget and were skipped entirely.')

    write_csv(out / 'transfer_trials.csv', rows)
    summary = summarize(rows)
    write_csv(out / 'transfer_summary.csv', summary)

    print()
    header = f"{'condition':<22}{'scenario':<10}{'n':>5}{'success':>9}{'moves':>8}{'reach%':>8}{'dec->tgt':>10}{'switch_reconv':>14}"
    print(header)
    for z in summary:
        dec = f"{z['mean_decisions_to_target']:.2f}" if z['mean_decisions_to_target'] is not None else 'n/a'
        reach = f"{z['reached_target_rate']*100:.1f}%" if z['reached_target_rate'] is not None else 'n/a'
        reconv = f"{z['mean_switch_reconvergence']:.2f}" if z['mean_switch_reconvergence'] is not None else 'n/a'
        print(f"{z['condition']:<22}{z['scenario']:<10}{z['n']:>5}{z['success_rate']:>9.2f}{z['mean_moves']:>8.1f}{reach:>8}{dec:>10}{reconv:>14}")


if __name__ == '__main__':
    main()
