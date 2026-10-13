# Mini-IPHOREOS: from mathematics to a working toy robot

Start with [the illustrated PDF tutorial](Tutorial_A_to_Z.pdf), or open [index.html](index.html) for the offline simulation replay and browser guide. The 24-page tutorial contains the complete purchasing, assembly, calibration, programming and experiment sequence.

For the full derivation and exact implemented rules, read [the mathematical companion](Mathematical_Model.pdf), with [editable LaTeX source](Mathematical_Model.tex). It includes worked calculations, parameter estimation, probability interpretations, implementation limits and direct tutorial chapter links. Run `python tools/check_math_model.py` to check its numerical examples against the actual controller.

The robot approaches a cardboard wall and attempts to stop with its ultrasonic sensor face 25 cm away (acceptable band 21–29 cm). It estimates distance and uncertainty, selects a short movement or another measurement, and verifies the result. This is a reduced demonstration of IPHOREOS; it is a rule-based belief controller, not a complete active-inference implementation.

## What to do first

1. Read chapters 01–04 before buying. Planned budget: **€107.28**, including delivery allowance and reserve; core listed hardware: **€63.28**. See [shopping_list.csv](shopping_list.csv) and [financial plan](FINANCIAL_PLAN.md).
2. Buy the Kitronik :MOVE Motor **5683**, a **micro:bit V2 Go bundle**, and matched AA batteries. Confirm checkout prices and included parts.
3. Assemble following the manufacturer instructions and the tutorial. Start with the sensor-only program, then test supported wheels, then calibrate short floor movements.
4. Follow the guide to edit calibration and enable the appropriate bundled program. All supplied motor programs are disabled by default. Never run the vendor demonstration as your beginner test.
5. Start with a clear floor area and broad cardboard target. Use the physical power switch to stop; button B provides a software stop. Compare physical ruler measurements with the robot's reported result.

## Included files

| Folder / file | Purpose |
|---|---|
| `flash/01_sensor_only.py` through `07_mini_careful.py` | Seven single-file programs for the official micro:bit Python editor |
| `firmware/` | Shared mathematical controller, hardware adapter, configuration and pinned vendor driver |
| `simulate.py`, `results/` | Reproducible synthetic experiments, summaries and traces |
| `tools/calibrate.py` | Summarise your sensor and motion measurements |
| `data/` | Blank templates for your physical measurements |
| `assets/` | Ten editable diagrams, two simulation plots and a labelled concept rendering |
| `docs/VALIDATION_REPORT.md` | Computer validation and outstanding physical checks |

## Run the computer project

From this directory in PowerShell, with Python installed:

```powershell
python -m pip install numpy matplotlib pytest
python -m pytest -q
python simulate.py
```

These commands run on your computer, not the micro:bit. To program the robot, follow the tutorial using https://python.microbit.org/ and one file from `flash/`. A `.py` file is not a precompiled `.hex`; use the editor's transfer/download workflow.

Optional rebuild commands:

```powershell
python tools/bundle_firmware.py
python tools/make_assets.py
python tools/build_guide.py
```

Rebuilding firmware replaces the generated `flash/` files; save your calibration edits first. Rebuilding the PDF additionally needs Playwright, PyMuPDF and an available Microsoft Edge installation; use `python tools/render_and_verify.py`. Optional serial recording needs `pyserial`; see the tutorial before connecting a moving robot by USB.

## Evidence and limits

Computer tests pass and 3,600 synthetic trials are supplied. **The physical robot has not been assembled, flashed or tested for this package.** Sensor mapping and API use were checked against vendor sources, but actual timing, board revision, memory, motor polarity, distance bias and travel must be checked on your unit. Unknown sensor bias can cause false verification even with a narrow estimated uncertainty. Synthetic outcomes are not physical success rates.

PicoGK is optional for a later custom enclosure or bracket. It is not needed to construct this kit, execute the controller, or translate software decisions into motor power. The guide explains that interface explicitly.

Original code: MIT, see `LICENSE`. Third-party driver: its retained MIT notice and `docs/VENDOR_LICENSE`. Concept-art provenance is in `assets/IMAGE_PROVENANCE.md`.
