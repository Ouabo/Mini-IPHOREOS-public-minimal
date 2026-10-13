"""Check the companion's worked examples against the shipped controller."""
from pathlib import Path
import sys
import json
import math

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'firmware'))
from belief_controller import Controller

def close(actual, expected):
    assert math.isclose(actual, expected, rel_tol=1e-8, abs_tol=1e-8), (actual, expected)

report = {}
c = Controller()
assert c.observe(50, 0) == 'MOVE'
c.record_move(.12)
close(c.mu, 48.89)
close(c.var, 4.64)
prior = {'mu': c.mu, 'variance': c.var}
assert c.observe(49, .32) == 'MOVE'
close(c.mu, 48.94907407407407)
close(c.var, 2.148148148148148)
report['prediction_update'] = {'prior': prior, 'posterior': c.snapshot()}

for context, expected, lower in [('normal', 'MOVE', 21.11), ('careful', 'SAMPLE', 19.73)]:
    c = Controller(context=context)
    assert c.observe(26, 0) == expected
    calculated = c.mu - c.k * math.sqrt(c.var) - 1.11 - .5
    close(calculated, lower)
    report[context] = {'action': expected, 'predicted_lower_cm': calculated}

for context, expected in [('normal', ['SAMPLE', 'SAMPLE', 'DONE']),
                          ('careful', ['SAMPLE', 'SAMPLE', 'SAMPLE', 'DONE'])]:
    c = Controller(context=context)
    actions = [c.observe(25, i * .15) for i in range(len(expected))]
    assert actions == expected
    report[context + '_verification'] = actions

report['gaussian_interpretation'] = {}
for k in (1.64, 2.33):
    central = math.erf(k / math.sqrt(2))
    report['gaussian_interpretation'][str(k)] = {
        'central_probability': central,
        'one_sided_tail': (1-central)/2,
        'maximum_mean_error_at_floor_cm': 4-k*.6,
    }

# A controlled counterexample: unknown bias defeats repeated verification.
c = Controller()
actions = [c.observe(25, i*.15) for i in range(3)]
assert actions[-1] == 'DONE' and abs(20-25) > 4
report['bias_counterexample'] = {'synthetic_true_cm': 20, 'raw_cm': 25, 'terminal': actions[-1]}
report['hardware_tested'] = False
output = ROOT / 'results/math_model_checks.json'
output.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('Mathematical examples match the controller; report:', output)
