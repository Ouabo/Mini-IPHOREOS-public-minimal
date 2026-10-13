# Mini_IPHOREOS explanatory video

**Video:** [Mini_IPHOREOS_Explanation_EN.mp4](Mini_IPHOREOS_Explanation_EN.mp4)

Duration: 2 minutes 30 seconds. Resolution: 1280 × 720 at 12 frames per second. English on-screen explanations; no voice-over or audio.

## What the video shows

- 00:00–00:12: task and definitions of concept, event and context.
- 00:12–00:49: nominal approach, belief updating and decision explanations.
- 00:49–01:31: manually selected normal versus careful contexts.
- 01:31–02:13: an unknown +5 cm sensor bias, compared with a supplied correction.
- 02:13–02:30: implemented capabilities and future research.

The robot aims to stop 25 cm from the wall; the acceptable band is 21–29 cm. Gold shows simulator ground truth. Green shows the controller's estimate and its uncertainty band. The controller never receives the true distance.

## Evidence and interpretation

The English video reads exactly the same CSV traces as the French version. These were generated with an unchanged copy of the project controller and simulation rules matching `simulate.py`. Seed 7 was fixed for the illustrative trials.

The careful context is selected manually. Proximity categories are explanatory annotations, not learned concepts. Events show measurements and controller decisions, not learned event schemas. Bands show the estimate ± k standard deviations; they do not guarantee statistical coverage.

Side-by-side trials are mapped onto a common video duration, so playback is not a comparison of execution time. Positions update at measurement instants; motor pulses are not continuously animated.

The +5 cm correction is supplied exactly to illustrate calibration; it is not estimated in this experiment. In this particular uncorrected trial the robot finishes at approximately 21.33 cm, still inside the target band. It does not falsely verify completion. The nominal and corrected trials finish at approximately 25.91 cm. A single illustrative trial per condition does not replace the project's 3,600-episode benchmark.

No physical robot data or hardware validation is presented. Mini_IPHOREOS is a rule-based, uncertainty-aware controller, not the full proposed active-inference architecture.

## Files and reproducibility

`trace_normal.csv`, `trace_prudent.csv`, `trace_biais.csv` and `trace_corrige.csv` are shared with the French version. `manifest_EN.json` records provenance, settings and outcomes. `preview_EN_20s.png`, `preview_EN_70s.png` and `preview_EN_124s.png` provide still previews.

To rebuild in the original workspace, run `python make_mini_iphoreos_video_en.py`. The script requires Pillow, imageio-ffmpeg, the existing trace files and the original controller path specified in the script. Its local dependency directory is `.video_dependencies`. The French video and README are preserved.
