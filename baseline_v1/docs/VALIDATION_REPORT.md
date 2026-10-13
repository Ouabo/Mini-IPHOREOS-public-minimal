# Validation report — 10 September 2026

## Completed on a computer

- 18 automated tests cover the mathematical controller, invalid observations, uncertainty behaviour, termination, deterministic simulation and mocked hardware timing/stop interfaces.
- Seven bundled Python programs compile syntactically on desktop Python. This does not establish micro:bit runtime compatibility or available memory.
- 3,600 synthetic episodes compare raw, belief and Mini controllers under two contexts and two sensor scenarios. Trial data and source hashes are in `results/`.
- The 24-page PDF was rendered and checked for text outside page boundaries. Browser replay controls and image loading were checked. Machine-readable layout results are in `review/verification.json`.
- Vendor driver files are pinned to commit `b551ddefa1099afec1a4901d2b19bb4aa9228c15`, with hashes and retained licensing in `docs/`.

## Mathematical companion

`Mathematical_Model.pdf` derives and documents the implemented model. Its constructed prediction/update, context-decision, repeated-verification and unknown-bias examples were checked against the shared controller by `tools/check_math_model.py`; numeric output is in `results/math_model_checks.json`. Gaussian interval probabilities are also calculated there.

The companion PDF passed checks for text outside page boundaries and unresolved LaTeX references. Relative file links and tutorial chapter anchors were checked by `tools/verify_math_document.py`, with results in `review/math_verification.json`. Tutorial chapter 13 and the project homepage link back to the companion. These documentation checks do not add physical validation.

Nominal Mini/normal simulation success was 99.33% in 300 trials. With an unknown +5 cm sensor bias, false verification was 27.33%. These figures concern the specified synthetic model only. The careful context did not universally improve outcomes under bias. See the tutorial and full summary CSV for all baselines and tradeoffs.

## Required on the actual robot

1. Confirm kit revision, micro:bit V2, connections, power and successful editor upload.
2. Validate ultrasound readings at measured distances and fit bias/noise; check a held-out distance.
3. With wheels supported, verify forward polarity, short pulse operation, button B and physical power-off.
4. On the intended floor, measure travel and coast at the selected PWM and pulse duration. Update configuration explicitly.
5. Run supervised trials from the prescribed starting area. Measure final distance independently with a ruler and record aborts, contacts and false verification.
6. Compare policies using repeated trials and report all outcomes, including failures.

No physical trials have been performed for this package. Blank recording sheets are intentionally blank. The concept image is illustrative and does not establish hardware dimensions or construction details.
