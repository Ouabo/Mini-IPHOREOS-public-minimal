# Mini_IPHOREOS_EXT1 — cognitive extension

Start with the [English PDF tutorial](Tutorial_EXT1_EN.pdf) or [HTML tutorial](Tutorial_EXT1_EN.html). English is the default language for new project outputs; French versions are preserved separately.

## Status

EXT1 is implemented as a desktop Python prototype and evaluated in 2,400 synthetic episodes across six scenarios and four policies. It is not physically validated or ready for direct deployment on a micro:bit. The original project and the 111-file `baseline_v1/` reference were verified unchanged against `baseline_manifest.json`.

The architecture jointly estimates distance and speed, infers probabilities for predefined normal/slow contexts, logs intended actions and realised events, and selects actions using progress, cost and an information proxy. Concept families are predefined; motion parameters are calibrated. The event log is not a learned skill memory. This is not a complete active-inference implementation.

## Run EXT1

Open PowerShell in this directory:

```powershell
python -m pip install -r requirements.txt
python -B -m pytest -q -p no:cacheprovider tests
python -B experiments/run_simulation.py --trials 100
python tools/build_tutorial.py
```

The simulation replaces files in `results_ext1/`; it does not overwrite V1 results. Tutorial generation requires Microsoft Edge, Playwright and PyMuPDF. The default builder produces `Tutorial_EXT1_EN.html` and `Tutorial_EXT1_EN.pdf`. Use `python tools/build_tutorial_fr.py` only when a French rebuild is wanted.

## Findings and limits

In the supplied exploratory run, EXT1 succeeds in 100% of slow-regime episodes and 97% after a slowdown. The adaptive filter without discrete contexts reaches the same success rates, so an advantage specific to the context layer is not established. Under an unknown +5 cm sensor bias, EXT1 produces 14% false verifications versus 1% for V1 in this protocol. These are not the historical V1 benchmark figures.

V1 uses fixed 0.12 s pulses, whereas adaptive policies can also use 0.24 s pulses. This limits attribution of improvements over V1. Development seeds were reused after corrections, so results are exploratory, not independent confirmation. See the tutorial for the paired-bootstrap limitations and the no-information ablation's tendency to stall.

## Directory layout

- `baseline_v1/`: preserved original code, tutorial and results.
- `cognitive/`: context filter, event log and action selection.
- `experiments/`: synthetic calibration and comparisons.
- `tests/`: six EXT1 tests; the baseline has its own 18 tests.
- `results_ext1/`: current traces, trial data, summaries, plots and provenance.
- `tools/`: English and French tutorial builders.
- `docs/`: tutorial checks and historical development notes.
- `development_run_*/`: archived development runs, not final results.

To check the copied reference separately:

```powershell
cd baseline_v1
python -B -m pytest -q -p no:cacheprovider
```

Do not modify `baseline_v1/` or the original project while developing EXT1. Existing French documentation remains available in `README_FR.md` and `Tutorial_EXT1_FR.*`.
