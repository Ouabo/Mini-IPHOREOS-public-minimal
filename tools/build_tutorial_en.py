"""Build the English EXT1 tutorial from the recorded simulation summary."""
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((ROOT/'results_ext1/summary.csv').open(encoding='utf-8')))
reconv_rows=list(csv.DictReader((ROOT/'results_ext1/reconvergence_summary.csv').open(encoding='utf-8')))

POLICY_LABELS=[('v1','V1'),('v1_fair','V1 (fair action set)'),('adaptive','Adaptive'),
    ('adaptive_no_information','Adaptive, no information'),('ext1_no_information','EXT1 without information'),('ext1','EXT1'),
    ('ext1_memory','EXT1 + context memory'),('ext1_memory_fast','EXT1 + memory + fast recognition')]

def reconv_row(policy,segment_index):
    return next(r for r in reconv_rows if r['policy']==policy and int(r['segment_index'])==segment_index)

def reconv_table():
    result='<table><tr><th>Visit to the regime</th><th>EXT1 (no memory)</th><th>+ context memory only</th><th>+ memory and fast recognition</th></tr>'
    labels=['1st (normal)','1st (slow)','2nd (normal)','2nd (slow)','3rd (normal)','3rd (slow)','4th (normal)']
    for seg,label in enumerate(labels):
        result+='<tr><td>'+label+'</td>'
        for policy in ('ext1','ext1_memory','ext1_memory_fast'):
            r=reconv_row(policy,seg)
            md=r['mean_decisions']
            cell=f"{float(md):.1f} decisions (n={r['n_converged']}/{r['n_total']})" if md else f"did not converge (0/{r['n_total']})"
            result+=f'<td>{cell}</td>'
        result+='</tr>'
    return result+'</table>'

def result_table():
    result='<table><tr><th>Scenario</th>'+''.join(f'<th>{label}</th>' for _,label in POLICY_LABELS)+'</tr>'
    for scenario in ('normal','slow','switch','recovery','dropout','bias'):
        result+='<tr><td>'+scenario+'</td>'
        for policy,_ in POLICY_LABELS:
            row=next(r for r in rows if r['scenario']==scenario and r['policy']==policy)
            result+=f"<td>{100*float(row['success']):.0f}%</td>"
        result+='</tr>'
    return result+'</table>'

def percentage(scenario,policy,metric):
    row=next(r for r in rows if r['scenario']==scenario and r['policy']==policy)
    return f"{100*float(row[metric]):.0f}%"

sections=[('1. EXT1: what changes', '''
<p class="lead">A minimal cognitive architecture for estimating, interpreting and acting in a wall-approach experiment.</p>
<div class="notice">EXT1 VERSION — a desktop Python prototype evaluated in simulation. Neither physical deployment nor autonomous discovery of new concepts is claimed.</div>
<p>Mini_IPHOREOS V1 estimates distance and applies fixed rules. EXT1 jointly estimates distance and effective speed, maintains probabilities over two movement contexts, and selects an action using an objective that combines progress, cost and information.</p>
<table><tr><th>Preserved V1</th><th>EXT1 extension</th></tr><tr><td>Scalar distance estimate</td><td>Distance, speed and joint uncertainty</td></tr><tr><td>Normal/careful: manual setting</td><td>Normal/slow: inferred environmental hypotheses</td></tr><tr><td>Movement rules</td><td>Comparison of candidate actions</td></tr><tr><td>Current state</td><td>Belief and event log</td></tr></table>
<p>The target distance is 25 cm, with an acceptable band of 21–29 cm. Ground truth belongs to the simulator; the controller receives only noisy measurements, time and calibration parameters.</p>
<h2>Keeping the versions separate</h2><p><code>baseline_v1/</code> contains the reference copy. Its files and the original project's files were checked against SHA-256 hashes. The extension uses <code>cognitive/</code>, <code>experiments/</code> and <code>results_ext1/</code>. This guide is the entry point for EXT1; the V1 tutorial remains in its own folder. The earlier French EXT1 guide is retained separately.</p>
<h2>Companion materials</h2><p>Full equation derivations, including the material new in this release, are in <a href="Mathematical_Model_EXT1.pdf">Mathematical_Model_EXT1.pdf</a>. Two silent, captioned walkthroughs are in <code>Mini_IPHOREOS_EXT1_Video/</code>: <a href="Mini_IPHOREOS_EXT1_Video/EXT1_Explanation_EN.mp4">EXT1_Explanation_EN.mp4</a> (fair baselines and the two-step planner) and <a href="Mini_IPHOREOS_EXT1_Video/EXT1_Memory_Explanation_EN.mp4">EXT1_Memory_Explanation_EN.mp4</a> (the context-memory negative result, diagnosis and fix — Section 7).</p>
'''),('2. Concepts, events and contexts', '''
<div class="flow">Observation → distance/speed belief → predictive relations → selected option → next observation → realised event</div>
<h2>Operational concepts</h2><p>The log explicitly records two relations: “the target is compatible with my belief” and “this pulse should produce this displacement”. Their forms are defined by the designer; calibration estimates speeds and the online loop updates beliefs. The system does not discover a conceptual vocabulary.</p>
<h2>Intended option and realised event</h2><p><code>intended_option</code> is MOVE, SAMPLE, DONE or ABORT. <code>realised_event</code> describes an initial reading, an observation after movement, a stationary reading, an unexpected outcome, an unusable reading or target verification. Here, “movement observed” means that an observation follows a movement command; it does not establish displacement through an independent measurement.</p>
<h2>Inferred context</h2><p>The normal and slow families are predefined, with calibrated speeds near 8 and 3 cm/s. The filter updates their probabilities without receiving the simulator's true context. No selected family is certain: evidence of a change must accumulate in the observations.</p>
<p>V1's careful setting is a control preference, not a hypothesis about the floor. EXT1 distinguishes these meanings. Low speed can have several physical causes: the model infers slower dynamics without necessarily diagnosing a slippery surface.</p>
<h2>Memory</h2><p>The log connects observations, beliefs, options and outcomes. It supports analysis; cross-episode skill memory, learning through replay and long-horizon event composition are not yet implemented.</p>
'''),('3. Model and estimation', '''
<p>The state is <b>x = (d, v)</b>, comprising distance and speed. The discrete context is normal or slow. A Gaussian distribution is maintained for each context and combined using probability weights.</p>
<div class="equation">d′ = d − v Δt − c + noise<br>v′ = ρv + (1 − ρ)m<sub>context</sub> + noise<br>y = d + b + measurement noise</div>
<p>Here c is mean coasting distance and b is calibrated sensor bias. The contextual models use ρ = 0.80. At each movement, a transition matrix with diagonal entries 0.96 allows context changes. Updates combine moment mixing, linear prediction and Kalman correction; normalised likelihoods update context weights. Repeated stationary readings do not artificially trigger context transitions.</p>
<p>Synthetic calibration is separate: seed 1701, 160 readings at four distances, and 80 pulses per speed family. Labels are available during supervised calibration but never supplied to the controller during evaluation. The script estimates bias, sensor variance, speeds and coasting distance. The movement variance of 0.04 cm² and other hyperparameters remain prototype choices, not results of hardware calibration.</p>
<div class="notice">Identifiability: with a single sensor y = d + b + noise, unknown absolute distance and unknown constant bias can remain confounded. EXT1 does not claim to learn that bias without an additional reference.</div>
<p>Joint covariance lets movements followed by measurements inform speed. Tests check covariance positivity, normalised probabilities, and the fact that repeated stationary readings alone do not reveal an unknown speed.</p>
'''),('4. Decisions and control limits', '''
<p>After each valid reading, the candidate pulse durations are 0 s (stay and measure), 0.12 s and 0.24 s. A duration is excluded if its predicted lower distance bound, including uncertainty and an additional 0.5 cm margin, falls below 21 cm.</p>
<h2>A two-step planner, not a one-step one</h2>
<p>The controller now enumerates <i>pairs</i> of durations (dt&#8321;, dt&#8322;) — nine combinations from the three-value menu — rolls the belief forward through both steps using the same transition used for real updates (without touching the real belief), and scores the pair as a whole. Only the first duration of the best-scoring pair is executed; the controller re-plans from the next real observation, in the usual receding-horizon style.</p>
<div class="equation">Score(dt&#8321;,dt&#8322;) = [(predicted distance after both steps − 25)² + predicted variance after both steps] / 400<br>+ 0.08 × (cost of dt&#8321;) + 0.08 × (cost of dt&#8322;) − 0.8 × expected information from dt&#8321;<br>+ 1.0, added only to the "measure, measure" pair, and only when some safe pair would have moved the robot more than 1 cm</div>
<p>That last term is the explicit no-progress cost: a pure "measure twice" plan is no longer allowed to look optimal purely because moving briefly raises predicted variance, whenever a safe alternative would actually make progress. A single-step planner could previously keep choosing to wait indefinitely, particularly with the information term switched off, because it could not see that movement now is what makes a later verification possible. Looking two steps ahead, plus this penalty, removes that specific failure mode; it is a heuristic fix for an identified failure, not a proof that stalling is impossible in every situation.</p>
<p>Information is still a Gaussian proxy: half the logarithm of the ratio of speed variance before and after a hypothetical next measurement. It is neither exact mutual information about context nor a complete expected-free-energy implementation.</p>
<p>Three consecutive readings satisfying |estimated distance − 25| + 1.64 standard deviations ≤ 4 lead to DONE. They are correlated and do not constitute three independent validations. Three consecutive invalid or inconsistent readings lead to ABORT. The experiment also imposes limits of 80 s, 100 movements and 350 decisions.</p>
<p>Risk control depends on the model. Bias can invalidate its margins. No physical safety certificate is provided.</p>
<h2>A fair rule-based comparator</h2>
<p>V1's original controller only ever offers a fixed 0.12 s pulse, so it could never show what a wider action menu is worth on its own. The <code>v1_fair</code> comparator keeps V1's rule-based philosophy — the same verification thresholds, the same invalid-reading and progress-abort handling, no joint speed estimation — but, like EXT1, chooses from the same three-value duration menu, taking the longest duration that still clears the overshoot safety margin. V1's single-pulse rule is the special case of this rule when only 0.12 s is offered.</p>
<p>Full derivations for both the planner and the fair comparator, with a worked numerical example, are in <a href="Mathematical_Model_EXT1.pdf">Mathematical_Model_EXT1.pdf</a>.</p>
'''),('5. Run and explore the project', '''
<p>Open PowerShell in <code>Mini_IPHOREOS_EXT1</code>. NumPy, Matplotlib and pytest are already installed in the current environment. For a fresh installation:</p>
<pre>python -m pip install -r requirements.txt
python -B -m pytest -q -p no:cacheprovider tests
python -B experiments/run_simulation.py --trials 100</pre>
<p>The final command writes 6,400 episodes to <code>results_ext1/</code>: six fairness-comparison scenarios plus two diagnostic-only scenarios (<code>repeated</code>, <code>intermediate</code>; see Section 7), eight policies and 100 seeds per combination. It replaces earlier EXT1 results, never V1 results. Computation times depend on the machine.</p>
<table><tr><th>File</th><th>Purpose</th></tr><tr><td>calibration*.csv / json</td><td>Synthetic data and estimated parameters</td></tr><tr><td>trials.csv</td><td>One row per episode, including failures</td></tr><tr><td>summary.csv</td><td>Aggregated results (six fairness scenarios)</td></tr><tr><td>reconvergence.csv / _summary.csv</td><td>Per-segment speed-reconvergence timing from the <code>repeated</code> scenario (Section 7)</td></tr><tr><td>paired_success_differences.csv</td><td>Exploratory paired contrasts</td></tr><tr><td>trace_*.json</td><td>Event log and simulator truth for seed 10000</td></tr><tr><td>comparison.png</td><td>Success and false-verification rates</td></tr><tr><td>manifest.json</td><td>Seeds, limitations and source hashes</td></tr></table>
<p>When reading a trace, distinguish <code>simulator_*</code> fields from information available to the controller. These evaluation fields are appended after the decision.</p>
<pre>python tools/build_tutorial.py</pre><p>This rebuilds the English HTML and PDF tutorial after a new simulation. It requires Playwright, PyMuPDF and Microsoft Edge. EXT1 depends on NumPy: do not copy these files directly to the micro:bit.</p>
'''),('6. Results and interpretation', '''
<p>Success means DONE with true distance between 21 and 29 cm. Observed percentages from the recorded simulation summary:</p>'''+result_table()+'''
<img src="results_ext1/comparison.png" alt="Comparison of success and false-verification rates">
<p><b>Fair-baseline check:</b> <code>v1_fair</code> gives V1's rule-based logic the same duration menu as EXT1. In the normal scenario it completes in about half as many moves as the original V1, confirming that V1's extra moves were partly an artefact of its narrower action set, not purely a less adaptive decision rule. But a wider menu is not free: in the slow and switch scenarios <code>v1_fair</code> does noticeably <i>worse</i> than the original single-pulse V1 ('''+percentage('slow','v1_fair','success')+''' and '''+percentage('switch','v1_fair','success')+''' success, against '''+percentage('slow','v1','success')+''' and '''+percentage('switch','v1','success')+''' for V1). V1's rule assumes a fixed, uncalibrated-for-this-regime speed; committing to a longer 0.24 s pulse on that wrong assumption overshoots by more than a short 0.12 s pulse would. A wider action menu only pays off when paired with a dynamics estimate that can tell it is safe to use. The remaining gap, if any, between <code>v1_fair</code> and EXT1 is the part attributable to joint estimation, context and information-seeking specifically.</p>
<p><b>Context versus plain adaptation:</b> the adaptive filter without discrete contexts, using the same information term, achieves '''+percentage('slow','adaptive','success')+''' under slow dynamics and '''+percentage('switch','adaptive','success')+''' after a slowdown — similar to EXT1. These single-switch scenarios still do not establish a distinct advantage of the contextual layer over plain adaptive estimation. Section 7 reports the experiment that actually isolates that question — repeated, not single, regime visits — and the (initially negative, then positive after diagnosis) result.</p>
<p><b>An unresolved pattern under sensor bias:</b> with unknown bias, the two information-seeking variants do markedly worse than their no-information counterparts: EXT1 reaches '''+percentage('bias','ext1','success')+''' success ('''+percentage('bias','ext1','false_verified')+''' false verification) versus '''+percentage('bias','ext1_no_information','success')+''' ('''+percentage('bias','ext1_no_information','false_verified')+''') without information-seeking; similarly '''+percentage('bias','adaptive','success')+''' versus '''+percentage('bias','adaptive_no_information','success')+''' for the context-free pair. V1 scores '''+percentage('bias','v1','success')+'''. This is a striking pattern from the same development seeds, not a frozen confirmatory result — information-seeking moves may be reinforcing confidence in a biased position faster, but that explanation has not been separately tested.</p>
'''),('7. Context memory: a negative result, a diagnosis, and a fix', '''
<p class="lead">This section is the most scientifically interesting part of this release: a clean hypothesis, a genuine failure to confirm it, a diagnosis found by tracing individual decisions rather than guessing, and a targeted fix that then worked. All four stages are reported, not just the ending.</p>
<h2>The hypothesis</h2>
<p>Once a regime (normal or slow) has been experienced, recognising it again later should let the controller adapt faster than estimating its dynamics from scratch a second time — faster <i>reuse</i>, not merely accurate classification. Testing this needed a scenario no prior release had: <code>repeated</code> alternates normal/slow every 8 moves within a single long episode, so the same regime is revisited several times and reconvergence speed can be measured visit by visit.</p>
<h2>Attempt 1: a persistent library (negative result)</h2>
<p>Each context already carries a mean-reversion target in its dynamics (the <code>ρ</code> equation in Section 3), but that target was a <i>fixed</i> calibration constant, and the state it pulls toward is continuously blended across contexts by the context-mixing step — so nothing about a context\'s speed actually persisted once belief shifted away from it. <code>ext1_memory</code> adds a separate, persistent per-context record (mean and variance) updated only when that context is confidently active, used as the mean-reversion target in place of the fixed constant.</p>
<p>Measured on <code>repeated</code>, this did not help — if anything, reconvergence was slightly slower and less reliable than without it. A follow-up fix for a hypothesised cause (the library\'s own uncertainty shrinking until it could no longer be corrected) made no measurable difference either, across a five-point parameter sweep.</p>
<h2>The diagnosis</h2>
<p>Tracing individual decisions (not aggregate statistics) showed why: reconvergence time is dominated by how long the <i>context weight</i> takes to swing back above the confidence gate after a switch — governed by the shared context-transition matrix and the per-reading observation likelihood — not by how accurate the underlying speed estimate is once that weight has already arrived. The library only ever changed the latter. Isolating just the part the library does influence (speed accuracy <i>after</i> a context is already confidently classified) still showed no consistent benefit. The bottleneck was recognition speed, not estimation precision.</p>
<h2>Attempt 2: recognise, then reuse directly</h2>
<p>EXT1 + memory + fast recognition (<code>ext1_memory_fast</code>) adds a change-point detector that accumulates evidence a challenger context explains recent readings better than the one currently believed active:</p>
<div class="equation">S<sub>k</sub> ← max(0, S<sub>k</sub> + advantage<sub>k</sub> − slack)</div>
<p>using the <i>pure</i> observation log-likelihood (no prior weighting), so a single noisy reading cannot trigger anything — only a sustained run of evidence can. When S<sub>k</sub> crosses a threshold, and only if that context\'s library entry has actually been learned before, the controller performs a discrete reset: jump the context weight up, and seed its speed estimate directly from the remembered value, bypassing the slow continuous weight-mixing entirely. This is the literal reuse step.</p>
<h2>The result</h2>
<p>Decisions needed to reconverge on each visit to a regime, averaged over 100 trials:</p>'''+reconv_table()+'''
<p>The first visit to each regime is identical across all three (nothing to reuse yet — exactly as it should be). From the second visit onward, memory plus fast recognition is consistently faster <i>and</i> more trials converge at all, with the gap widening on later visits. On scenarios with no repeat visit within an episode (<code>switch</code>, <code>recovery</code>, <code>normal</code>), all three are byte-identical: no cost, no new false alarms, because there is nothing yet to recognise. The detection threshold was chosen by a grid search on development data, trading detection speed against false-jump rate; the trade-off curve actually tried is documented alongside the chosen constants in the source.</p>
<p>Full derivations for the library, the change-point statistic and the reuse step, plus the diagnostic trace that located the bottleneck, are in <a href="Mathematical_Model_EXT1.pdf">Mathematical_Model_EXT1.pdf</a>. A captioned walkthrough of this whole story is in <a href="Mini_IPHOREOS_EXT1_Video/EXT1_Memory_Explanation_EN.mp4">EXT1_Memory_Explanation_EN.mp4</a>.</p>
'''),('8. Scientific scope and next validation', '''
<p><b>Addressed so far:</b> four of the six items in this project\'s improvement plan are now implemented. V1\'s fixed 0.12 s pulse versus the cognitive family\'s 0.12/0.24 s menu was a genuine confound; the <code>v1_fair</code> baseline and the completed (context x information) 2x2 factorial now hold the action menu, observation model and interaction budget fixed across every controller used for causal comparisons (Section 4). The planner no longer evaluates a single step in isolation (Section 4\'s two-step horizon and no-progress cost). Context now has a persistent, reusable memory, and regime changes are recognised from accumulated evidence rather than single readings (Section 7). All four are mechanical and architectural fixes, not yet validated on a held-out evaluation set — see below.</p>
<p>Context beliefs have memory in a second sense worth distinguishing from Section 7\'s library: in the recovery scenario, a high slow-context probability can persist after normal speed resumes. The <code>false_context_alert</code> column includes this transient lag, not just spontaneous false alarms. Zeros for policies without contexts do not represent detection performance. Per-trial change-detection delays are available in <code>trials.csv</code>.</p>
<p>Paired bootstrap intervals are descriptive and unadjusted for multiplicity. Identical outcomes can produce a degenerate interval: 100 successes do not prove that the success probability equals one. Seeds were reused after a numerical-test correction and a comparator correction. This is exploratory development, not independent confirmatory validation.</p>
<h2>Next steps</h2><ol><li>Address sensor bias with an explicit, costed reference observation, propagating its uncertainty into the stopping decision — not with more filtering alone.</li><li>Freeze the design on development scenarios, then evaluate on unused seeds and conditions: previously unseen intermediate speeds (the <code>intermediate</code> scenario is a first step), bias with and without a reference, missing/outlier readings, and identical action sets across controllers.</li><li>Calibrate the real robot, adapt the software to its hardware and run independent supervised trials.</li></ol>
<p>For assembly, wiring and physical calibration, consult the V1 tutorial in <code>baseline_v1/</code>. This document does not change V1 motor programs. The present EXT1 release demonstrates software operation only.</p>
''')]
css='''@page{size:A4;margin:17mm}body{font:11pt Arial;color:#172a40;margin:0}section{break-after:page}section:last-child{break-after:auto}h1{font-size:23pt;color:#126b70;margin:10px 0 20px}h2{font-size:14pt;margin-top:24px}p,li{line-height:1.45}table{border-collapse:collapse;width:100%;font-size:10pt;margin:15px 0}td,th{padding:9px;border:1px solid #c8d7df;text-align:left}th{background:#e3f0f2}.notice{padding:14px;background:#fff0d0;border-left:4px solid #dd9b24;margin:18px 0}.flow,.equation{padding:18px;background:#e6f3f1;line-height:1.7}pre{white-space:pre-wrap;background:#edf1f5;padding:14px;font-size:10pt}code{font-size:9.5pt;overflow-wrap:anywhere}img{width:100%}.tag{font-size:9pt;color:#597485;letter-spacing:1px}.lead{font-size:15pt}@media screen{body{max-width:820px;margin:30px auto;padding:20px}section{margin-bottom:65px}}'''
document='<!doctype html><html lang="en"><meta charset="utf-8"><title>Mini_IPHOREOS_EXT1 — Tutorial</title><style>'+css+'</style><body>'+''.join('<section><div class="tag">MINI_IPHOREOS_EXT1 • COGNITIVE ARCHITECTURE • SIMULATION</div><h1>'+title+'</h1>'+body+'</section>' for title,body in sections)+'</body></html>'
(ROOT/'Tutorial_EXT1_EN.html').write_text(document,encoding='utf-8')
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,channel='msedge');page=browser.new_page()
    page.goto((ROOT/'Tutorial_EXT1_EN.html').as_uri());page.emulate_media(media='print')
    page.wait_for_function('Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)')
    page.pdf(path=str(ROOT/'Tutorial_EXT1_EN.pdf'),format='A4',print_background=True,prefer_css_page_size=True)
    browser.close()
import fitz
doc=fitz.open(ROOT/'Tutorial_EXT1_EN.pdf')
report={'language':'English','pages':len(doc),'words':sum(len(p.get_text().split()) for p in doc),'outside':[]}
for i,p in enumerate(doc):
    for b in p.get_text('blocks'):
        if b[0]<0 or b[1]<0 or b[2]>p.rect.width+1 or b[3]>p.rect.height+1:report['outside'].append(i+1)
doc[0].get_pixmap().save(ROOT/'docs/tutorial_preview_EN.png')
(ROOT/'docs/tutorial_verification_EN.json').write_text(json.dumps(report,indent=2))
assert not report['outside'],report
print(report)
