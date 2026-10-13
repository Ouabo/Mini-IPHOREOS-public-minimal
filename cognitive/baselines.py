"""Rule-based distance controller with the same action menu, observation
model and interaction budget as CognitiveController.

Used to separate "better decision architecture" from "wider action set"
when comparing against the legacy v1 controller (baseline_v1/, preserved
unmodified per AGENTS.md), which can only choose a fixed 0.12s pulse and
has no access to a 0.24s pulse. FairRuleBaseline mirrors v1's 'mini' rule
logic (same verify/abort thresholds, same inconsistency/invalid-reading
handling, same timeout/move-limit budget) but picks among the same
duration menu (0., .12, .24) as CognitiveController, using the longest
pulse that stays clear of the overshoot safety margin.

This deliberately does NOT jointly estimate speed: it stays a pure
distance-belief rule controller, matching v1's philosophy. Adaptive speed
estimation without the cognitive context/information layer is a separate
question, covered by the 'adaptive_no_information' policy.
"""
import math

DURATIONS = (.24, .12)  # longest-first; 0. (SAMPLE) is always the fallback


class FairRuleBaseline:
    def __init__(self, calibration, target=25., band=4.):
        self.cal = calibration
        self.target = target
        self.band = band
        self.mu = None
        self.var = calibration['sensor_var']
        self.invalid = 0
        self.verify = 0
        self.moves = 0
        self.samples = 0
        self.terminal = None
        self.last_action = 'START'
        self.memory = []
        self.progress_anchor = None

    def step(self, reading, time):
        if self.terminal:
            return self.terminal, 0.
        valid = reading is not None and math.isfinite(reading) and 12 <= reading <= 150
        if valid and self.mu is not None:
            y = reading - self.cal['sensor_bias']
            if abs(y - self.mu) > max(8.0, 4.0 * math.sqrt(self.var + self.cal['sensor_var'])):
                valid = False
        if not valid:
            self.invalid += 1
            self.verify = 0
            return self._record('ABORT' if self.invalid >= 3 else 'SAMPLE', 0., reading, time,
                                 'invalid_or_inconsistent_reading')
        self.invalid = 0
        y = reading - self.cal['sensor_bias']
        if self.mu is None:
            self.mu = y
            self.var = self.cal['sensor_var']
        else:
            gain = self.var / (self.var + self.cal['sensor_var'])
            self.mu += gain * (y - self.mu)
            self.var = max(.36, (1. - gain) * self.var)
        if self.progress_anchor is None:
            self.progress_anchor = self.mu
        self.samples += 1
        if time >= 80 or self.moves >= 100:
            return self._record('ABORT', 0., reading, time, 'budget_exhausted')
        sd = math.sqrt(self.var)
        in_target = abs(self.mu - self.target) + 1.64 * sd <= self.band
        self.verify = self.verify + 1 if in_target else 0
        if self.verify:
            return self._record('DONE' if self.verify >= 3 else 'SAMPLE', 0., reading, time, 'verify_target')
        if self.mu < self.target - self.band:
            return self._record('ABORT', 0., reading, time, 'estimated_overshoot')
        if self.moves and self.moves % 8 == 0 and self.samples == 1:
            if self.progress_anchor - self.mu < 1.0:
                return self._record('ABORT', 0., reading, time, 'no_measured_progress')
            self.progress_anchor = self.mu
        dt = self._choose_duration(sd)
        return self._record('MOVE' if dt else 'SAMPLE', dt, reading, time, 'rule_based')

    def _choose_duration(self, sd):
        # Longest pulse that still clears the overshoot safety margin (the
        # same style of lower-bound check v1's 'mini' policy applies to its
        # one fixed pulse), so the baseline genuinely benefits from the
        # wider menu instead of defaulting back to the shortest option.
        for dt in DURATIONS:
            step = self.cal['speed_normal'] * dt + self.cal['coast']
            lower = self.mu - 1.64 * sd - step - .5
            if lower >= self.target - self.band:
                return dt
        return 0.

    def _record(self, action, dt, reading, time, reason):
        self.memory.append(dict(time=time, reading=reading, estimated_distance=self.mu,
                                 distance_sd=math.sqrt(self.var), context_probabilities={},
                                 intended_option=action, pulse_seconds=dt, reason=reason,
                                 realised_event=reason))
        self.last_action = action
        if action in ('DONE', 'ABORT'):
            self.terminal = action
        if action == 'MOVE':
            self.mu -= self.cal['speed_normal'] * dt + self.cal['coast']
            self.var += self.cal['motion_var']
            self.moves += 1
            self.verify = 0
            self.samples = 0
        return action, dt
