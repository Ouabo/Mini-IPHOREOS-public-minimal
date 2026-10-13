# Frozen parameters for the held-out evaluation (Milestone 4)

Every tunable constant in EXT1's cognitive architecture, as of this freeze, with its
file location. None of these change for the held-out run (`results_ext1_heldout/`);
if the held-out evaluation suggests any of them should change, that is a finding to
report, not something to act on inside this same milestone.

## Receding-horizon planner (`cognitive/controller.py`, `CognitiveController._plan`)

| Constant | Value | Role |
|---|---|---|
| Duration menu | `{0., .12, .24}` s | Candidate pulse durations, both horizon steps |
| Planning horizon `H` | 2 decisions | `_plan` enumerates `durations x durations` |
| Cost weight | 0.08 | Per-step cost, `cost1`/`cost2` |
| Information weight | 0.8 | First-step information term only |
| Overshoot margin | `2.33*sigma + 0.5` cm | Safety exclusion, both horizon steps |
| No-progress threshold | 1 cm | Net two-step displacement needed to trigger the penalty |
| No-progress penalty | 1.0 | Added to the all-SAMPLE (0,0) pair's score only |

Set during Milestone 1 (fair baselines + short-horizon planner); not re-tuned since.

## Context library and fast recognition (`cognitive/model.py`, `Belief`)

| Constant | Value | Role |
|---|---|---|
| `LIB_CONFIDENCE_GATE` | 0.7 | Minimum posterior weight to update the library |
| `LIB_VAR_INIT` | 4.0 | Initial/"untouched" library variance; also the maturity threshold for a jump |
| `LIB_VAR_FLOOR` | 0.05 | Minimum library variance after updates |
| `CUSUM_SLACK` | 0.2 | Per-step damping in the change-point accumulator |
| `CUSUM_THRESHOLD` | 0.5 | Accumulated-evidence threshold that triggers a jump |
| `JUMP_WEIGHT` | 0.85 | Posterior weight assigned to the recognised context on a jump |
| `JUMP_VAR_FLOOR` | 0.05 | Minimum post-jump speed variance |

`CUSUM_SLACK`/`CUSUM_THRESHOLD` were explicitly selected by grid search over
`(slack, threshold) in {(0,0.2), (0.1,0.3), (0.2,0.5), (0.3,1.0)}` on 50-100
development seeds (10000-10099) of the `repeated` and `normal` scenarios -- see
`Mathematical_Model_EXT1.pdf`, Section 12.3. This is exactly the kind of
development-set-only selection this milestone's held-out run is meant to check.

## Bias reference (`experiments/run_simulation.py`)

| Constant | Value | Role |
|---|---|---|
| `REF_DISTANCE` | 50.0 cm | Known reference distance for the pre-trial bias check |
| `N_REF` | 5 | Reference readings taken once, before the main approach loop |

Chosen for physical plausibility (well inside the valid sensing range, clear of the
task's own distances) and a reasonable resulting standard error
(`sqrt(1.44/5) ~= 0.54` cm against the 5-8 cm biases tested), not grid-searched.

## Task B / cross-task transfer validation (`experiments/run_transfer_validation.py`)

Frozen before the transfer-validation run, same discipline as above -- these are
declared ahead of time, not picked after seeing results.

| Constant | Value | Role |
|---|---|---|
| `TARGET_B` | 85.0 cm | Task B's nominal target distance (Task A's is 25.0 cm, unchanged) |
| `BAND_B` | 4.0 cm | Task B's verification band half-width (same half-width as Task A) |
| `START_RANGE_B` | (115, 145) cm | Task B's starting-distance range |
| Checkpoint maturity gate | `weight > Belief.LIB_CONFIDENCE_GATE` (0.7) for both contexts | Condition for a "training checkpoint" to count as mature enough to seed transfer from |

`TARGET_B`/`START_RANGE_B` are chosen to be clearly separated from both Task A's target
(25 cm) and the shared `REF_DISTANCE` (50 cm, unchanged -- the same sensor calibration
and bias-reference distance apply to both tasks), matching the existing design
rationale for `REF_DISTANCE` above. Task B intentionally reuses Task A's sensor/motor
physics and context structure unchanged (same `normal`/`slow` speeds, same per-trial
`factor` noise) -- only the goal (target/band/start) differs. This isolates the
goal-transfer question cleanly; transfer under a genuinely different sensor/surface
characteristic is out of scope for this pass (see `run_transfer_validation.py`'s
docstring).

**Superseding note.** The first transfer-validation pass (one checkpoint shared across
all 100 Task-B seeds) found no measurable difference between cold-start, zero-update
and adapt-with-updates: the checkpoint converged to within noise of the untrained
calibration prior, so there was no information gap for the library to close
(`Mathematical_Model_EXT1.tex`, Section 10). The constants below give Task A something
to teach that calibration cannot already supply, and are frozen before the re-run,
same discipline as above:

| Constant | Value | Role |
|---|---|---|
| `DEPLOYMENT_FACTOR_RANGE` | Uniform(0.6, 0.85) | Persistent per-deployment speed multiplier, outside calibration's own sampling noise (SE of the pooled 80-pulse mean ~0.056) and outside the existing per-trial `Uniform(0.9,1.1)` factor |
| `DEPLOYMENT_SEED_OFFSET` | 400000 | `deployment_factor = random.Random(seed+DEPLOYMENT_SEED_OFFSET).uniform(*DEPLOYMENT_FACTOR_RANGE)`, deterministic per Task-B seed |
| `TRAIN_SEED_BLOCK` | 100 | Per-deployment Task-A training seeds: `30000 + seed_index*100 + episode_index`, disjoint across the 100 deployments |

Each of the 100 standard Task-B seeds is now its own "deployment": its
`deployment_factor` is shared between the checkpoint trained on Task A and its own
Task-B evaluation under all three conditions, including cold-start -- cold-start faces
the same real, uncorrected bias, it just never learned it from Task A first.

## What is explicitly NOT in this freeze

The simulator's own generative constants (sensor noise sd 1.2 cm, motion noise sd
0.08 cm, dropout rate 12%, the new outlier rate/magnitude) are part of the evaluation
protocol, not the controller, and are unchanged between development and held-out runs
by construction (same `experiments/run_simulation.py`, different seeds only).
