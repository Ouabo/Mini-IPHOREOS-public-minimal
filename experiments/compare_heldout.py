"""Milestone 4: side-by-side development-seed vs held-out-seed replication
report. Reading only -- runs no simulation itself. Compares the specific
claims already published in Tutorial_EXT1_EN.pdf / Mathematical_Model_EXT1.pdf
against results_ext1_heldout/, produced by a seed range (default 50000+) never
used during development or threshold tuning (see docs/FROZEN_PARAMETERS.md).
"""
from pathlib import Path
import csv, sys

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / 'results_ext1'
HELD = ROOT / 'results_ext1_heldout'


def load_csv(path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as f:
        return list(csv.DictReader(f))


def row(rows, **keys):
    for r in rows:
        if all(r.get(k) == str(v) for k, v in keys.items()):
            return r
    return None


def f(x):
    return float(x) if x not in (None, '') else None


def main():
    if not HELD.exists():
        print(f'No held-out results at {HELD}. Run:\n'
              f'  python experiments/run_simulation.py --trials 100 --seed-start 50000 --out-dir results_ext1_heldout')
        sys.exit(1)

    dev_summary = load_csv(DEV / 'summary.csv')
    held_summary = load_csv(HELD / 'summary.csv')
    dev_reconv = load_csv(DEV / 'reconvergence_summary.csv')
    held_reconv = load_csv(HELD / 'reconvergence_summary.csv')
    dev_bias = load_csv(DEV / 'bias_reference_summary.csv')
    held_bias = load_csv(HELD / 'bias_reference_summary.csv')
    dev_outlier = load_csv(DEV / 'outlier_summary.csv')
    held_outlier = load_csv(HELD / 'outlier_summary.csv')

    print('=' * 78)
    print('MILESTONE 4 REPLICATION REPORT: development seeds vs held-out seeds')
    print('=' * 78)

    print('\n--- Claim 1 (Milestone 1): v1_fair roughly halves v1\'s move count, "normal" ---')
    for label, summ in (('dev', dev_summary), ('held-out', held_summary)):
        v1 = row(summ, scenario='normal', policy='v1')
        v1f = row(summ, scenario='normal', policy='v1_fair')
        if v1 and v1f:
            ratio = f(v1f['moves']) / f(v1['moves'])
            print(f'  {label:10s}: v1 moves={f(v1["moves"]):.1f}  v1_fair moves={f(v1f["moves"]):.1f}  ratio={ratio:.2f}')

    print('\n--- Claim 2 (Milestone 1): no-information policies stay reliable (no stalling-induced failures) ---')
    for policy in ('adaptive_no_information', 'ext1_no_information'):
        for label, summ in (('dev', dev_summary), ('held-out', held_summary)):
            r = row(summ, scenario='normal', policy=policy)
            if r:
                print(f'  {label:10s} {policy:26s}: success={f(r["success"]):.2f}  aborted={f(r["aborted"]):.2f}')

    print('\n--- Claim 3 (Milestone 2): memory+fast-recognition speeds up reconvergence from visit 2 onward ---')
    for seg, label_seg in ((1, '1st slow visit'), (3, '2nd slow visit'), (5, '3rd slow visit')):
        for label, rc in (('dev', dev_reconv), ('held-out', held_reconv)):
            cells = []
            for policy in ('ext1', 'ext1_memory', 'ext1_memory_fast'):
                r = row(rc, policy=policy, segment_index=seg)
                md = f(r['mean_decisions']) if r else None
                cells.append(f"{policy}={md:.2f}" if md is not None else f"{policy}=n/a")
            print(f'  {label:10s} {label_seg:16s}: ' + '  '.join(cells))
    dev_v2 = row(dev_reconv, policy='ext1_memory_fast', segment_index=3)
    held_v2 = row(held_reconv, policy='ext1_memory_fast', segment_index=3)
    dev_base = row(dev_reconv, policy='ext1', segment_index=3)
    held_base = row(held_reconv, policy='ext1', segment_index=3)
    if dev_v2 and held_v2 and dev_base and held_base:
        print(f'  verdict (ext1_memory_fast faster than ext1 on 2nd slow visit): '
              f'dev {f(dev_v2["mean_decisions"]):.2f} < {f(dev_base["mean_decisions"]):.2f}? '
              f'{f(dev_v2["mean_decisions"]) < f(dev_base["mean_decisions"])}   |   '
              f'held-out {f(held_v2["mean_decisions"]):.2f} < {f(held_base["mean_decisions"]):.2f}? '
              f'{f(held_v2["mean_decisions"]) < f(held_base["mean_decisions"])}')

    print('\n--- Claim 4 (Milestone 3): bias reference recovers success under bias and bias_random ---')
    for scenario in ('bias', 'bias_random'):
        for label, bs in (('dev', dev_bias), ('held-out', held_bias)):
            e = row(bs, scenario=scenario, policy='ext1')
            er = row(bs, scenario=scenario, policy='ext1_bias_ref')
            if e and er:
                print(f'  {label:10s} {scenario:12s}: ext1 success={f(e["success"]):.2f}  '
                      f'ext1_bias_ref success={f(er["success"]):.2f}  '
                      f'bias_est_err={f(er["mean_bias_estimate_error"]):.2f} cm')

    print('\n--- New (Milestone 4): outlier scenario -- descriptive, no prior claim ---')
    for policy in ('v1', 'v1_fair', 'adaptive', 'ext1_no_information', 'ext1', 'ext1_memory_fast', 'ext1_bias_ref'):
        for label, summ in (('dev', dev_outlier), ('held-out', held_outlier)):
            r = row(summ, policy=policy)
            if r:
                print(f'  {label:10s} {policy:22s}: success={f(r["success"]):.2f}  '
                      f'false_verified={f(r["false_verified"]):.2f}  aborted={f(r["aborted"]):.2f}')

    print('\n' + '=' * 78)
    print('Read each section above directly; this script reports numbers side by')
    print('side, it does not assert pass/fail. See the chat response for the')
    print('judgement call on whether each claim replicates.')


if __name__ == '__main__':
    main()
