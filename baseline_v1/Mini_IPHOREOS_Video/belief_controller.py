"""Small dependency-free controller shared by desktop simulation and MicroPython.

All distances are cm, time is seconds, variance is cm^2. No hardware imports.
This is an uncertainty-aware state machine, not a derived full active-inference solver.
"""
from math import sqrt

def isfinite(value):
    return value == value and abs(value) != float('inf')

DEFAULTS = {
    'target_cm': 25.0, 'tolerance_cm': 4.0, 'minimum_cm': 12.0,
    'maximum_cm': 150.0, 'sensor_bias_cm': 0.0, 'measurement_var': 4.0,
    'variance_floor': 0.36, 'motion_var': 0.64, 'speed_cm_s': 8.0,
    'coast_cm': 0.15, 'extra_margin_cm': 0.5, 'pulse_s': 0.12,
    'max_samples': 16, 'max_invalid': 3, 'max_moves': 80,
    'timeout_s': 60.0, 'verify_count': 3,
}

class Controller:
    def __init__(self, policy='mini', context='normal', config=None):
        if policy not in ('raw','belief','mini') or context not in ('normal','careful'):
            raise ValueError('Unknown policy or context')
        self.cfg = dict(DEFAULTS)
        if config:
            for key,value in config.items():
                if key not in self.cfg: raise ValueError('Unknown config: '+key)
                self.cfg[key] = value
        c=self.cfg
        if not (0<c['minimum_cm']<c['target_cm']-c['tolerance_cm']<c['target_cm']+c['tolerance_cm']<c['maximum_cm']):
            raise ValueError('Invalid distance bounds')
        for key in ('measurement_var','variance_floor','motion_var','speed_cm_s','pulse_s','timeout_s'):
            if not isfinite(c[key]) or c[key]<=0: raise ValueError('Invalid '+key)
        if c['pulse_s']>.25 or c['coast_cm']<0 or c['extra_margin_cm']<0:
            raise ValueError('Invalid motion settings')
        self.policy=policy;self.context=context
        self.k=1.64 if context=='normal' else 2.33
        self.mu=None;self.var=c['measurement_var'];self.last_y=None
        self.invalid=0;self.rejected=0;self.samples=0;self.moves=0;self.verify=0
        self.terminal=None;self.reason='initial';self.started=None
        self.stop_latched=False;self.progress_anchor=None

    def result(self,action,reason):
        self.reason=reason
        if action in ('DONE','ABORT'): self.terminal=action
        return action

    def observe(self,raw_cm,now_s):
        if self.terminal: return self.terminal
        if self.started is None: self.started=now_s
        c=self.cfg
        if now_s-self.started>=c['timeout_s']: return self.result('ABORT','trial_timeout')
        self.samples+=1
        if raw_cm is None or not isfinite(raw_cm) or not c['minimum_cm']<=raw_cm<=c['maximum_cm']:
            self.invalid+=1;self.verify=0
            if raw_cm is not None and isfinite(raw_cm) and raw_cm<c['minimum_cm']:
                return self.result('ABORT','raw_clearance_limit')
            return self.result('ABORT' if self.invalid>=c['max_invalid'] or self.samples>c['max_samples'] else 'SAMPLE','invalid_sensor')
        y=raw_cm-c['sensor_bias_cm'];self.last_y=y
        if y<c['minimum_cm']: return self.result('ABORT','corrected_clearance_limit')
        if self.mu is not None and abs(y-self.mu)>max(8.0,4.0*sqrt(self.var+c['measurement_var'])):
            self.rejected+=1;self.verify=0
            return self.result('ABORT' if self.rejected>=3 or self.samples>c['max_samples'] else 'SAMPLE','inconsistent_observation')
        self.invalid=0;self.rejected=0
        if self.mu is None:
            self.mu=y;self.var=c['measurement_var']
        else:
            gain=self.var/(self.var+c['measurement_var'])
            self.mu+=gain*(y-self.mu)
            self.var=max(c['variance_floor'],(1.0-gain)*self.var)
        if self.progress_anchor is None: self.progress_anchor=self.mu
        sd=sqrt(self.var)
        if self.moves and self.moves%8==0 and self.samples==1:
            if self.progress_anchor-self.mu<1.0: return self.result('ABORT','no_measured_progress')
            self.progress_anchor=self.mu
        # All policies use the same measured-clearance and model consistency guards.
        if self.policy=='raw':
            if y<=c['target_cm']: self.stop_latched=True
            verify_ok=self.stop_latched and abs(y-c['target_cm'])<=c['tolerance_cm']
        elif self.policy=='belief':
            if self.mu<=c['target_cm']+0.5: self.stop_latched=True
            verify_ok=self.stop_latched and abs(self.mu-c['target_cm'])+1.64*sd<=c['tolerance_cm']
        else:
            verify_ok=abs(self.mu-c['target_cm'])+self.k*sd<=c['tolerance_cm']
        if verify_ok:
            self.verify+=1
            return self.result('DONE' if self.verify>=c['verify_count'] else 'SAMPLE','verify_target_band')
        self.verify=0
        if self.samples>=c['max_samples']: return self.result('ABORT','inconclusive_after_sampling')
        if self.stop_latched: return self.result('SAMPLE','stopped_pending_verification')
        if self.moves>=c['max_moves']: return self.result('ABORT','move_limit')
        step=c['speed_cm_s']*c['pulse_s']+c['coast_cm']
        if self.policy=='mini':
            lower=self.mu-self.k*sd-step-c['extra_margin_cm']
            if lower<c['target_cm']-c['tolerance_cm']:
                return self.result('SAMPLE','uncertain_next_step')
            if self.mu<=c['target_cm']:
                return self.result('SAMPLE','estimate_near_or_below_target')
        return self.result('MOVE','short_forward_pulse')

    def record_move(self,actual_seconds):
        if self.terminal or self.mu is None: raise ValueError('Movement without an active belief')
        if not 0<actual_seconds<=.30: raise ValueError('Invalid executed duration')
        self.mu-=self.cfg['speed_cm_s']*actual_seconds+self.cfg['coast_cm']
        self.var+=self.cfg['motion_var'];self.moves+=1;self.samples=0;self.verify=0

    def snapshot(self):
        return {'mu_cm':self.mu,'sd_cm':sqrt(self.var),'moves':self.moves,
                'stationary_samples':self.samples,'reason':self.reason,'terminal':self.terminal}
