"""Two-mode interacting Gaussian filter for distance and effective velocity.

Concept families and context labels are supplied; motion parameters are calibrated.
No ground truth or environment labels enter the online filter.
"""
import math
import numpy as np


class Belief:
    LIB_CONFIDENCE_GATE = 0.7
    LIB_VAR_INIT = 4.0
    LIB_VAR_FLOOR = 0.05
    # CUSUM accumulated-evidence change detector (fast_switch=True only): a
    # sustained run of evidence favouring a challenger context, not a single
    # noisy reading, is required before recognising a regime change.
    # Selected on development data (grid search over the 'repeated' and
    # 'normal' scenarios, 50/100 seeds): this point gives a ~33% reduction in
    # reconvergence time on repeat context visits (4.30 -> 2.9 decisions) with
    # a near-zero false-jump rate (1/100 trials) on the no-switch scenario.
    # Lower thresholds (e.g. slack=0, threshold=0.2) give a larger effect
    # (4.3 -> ~2.1) but a materially higher false-jump rate (several per 100);
    # higher ones (slack=0.3, threshold=1.0) eliminate false jumps but also
    # most of the benefit. This is the chosen trade-off point, not the only
    # one considered.
    CUSUM_SLACK = 0.2
    CUSUM_THRESHOLD = 0.5
    JUMP_WEIGHT = 0.85
    JUMP_VAR_FLOOR = 0.05

    def __init__(self, calibration, contexts=True, memory=False, fast_switch=False, memory_frozen=False):
        self.cal = calibration
        self.contexts = contexts
        self.memory = memory
        self.fast_switch = fast_switch
        # Cross-task transfer validation only (experiments/run_transfer_validation.py):
        # when True, lib_mean/lib_var are still READ (as the _advance reversion
        # target and the _jump_to target), but never WRITTEN by _update_library --
        # a seeded library stays exactly as seeded, testing "transfer without
        # updates" as distinct from "transfer with adaptation" (memory_frozen=False
        # with a seeded library). Default False: zero behaviour change for every
        # existing policy.
        self.memory_frozen = memory_frozen
        self.names = ['normal', 'slow'] if contexts else ['adaptive']
        self.means = np.array([calibration['speed_normal'], calibration['speed_slow']] if contexts else [calibration['speed_normal']])
        self.weights = np.array([.8, .2] if contexts else [1.])
        self.states = np.column_stack([np.zeros(len(self.means)), self.means])
        self.covs = np.array([np.diag([calibration['sensor_var'], 4.]) for _ in self.means])
        self.initialised = False
        self.last_innovation = 0.
        # Persistent per-context memory: unlike self.means (the fixed calibration
        # prior) or self.states (continuously mixed across contexts by _advance),
        # lib_mean/lib_var are never touched by the mixing step, so a context's
        # learned speed survives untouched while that context is inactive. Only
        # used when memory=True; harmless and unread otherwise.
        self.lib_mean = self.means.copy()
        self.lib_var = np.full(len(self.means), self.LIB_VAR_INIT)
        self.cusum = np.zeros(len(self.means))
        # Explicit bias reference (set_bias_reference, called once before the
        # main loop if requested): defaults to zero mean/variance, so every
        # existing call site is numerically unaffected unless opted in.
        self.extra_bias_mean = 0.
        self.extra_bias_var = 0.

    def set_bias_reference(self, mean, var):
        """Fold in a bias estimate from an independent, known-distance
        reference observation (computed by the caller from its own readings,
        not derived from simulator truth). `var` is added to every
        observation's effective variance from now on, so the reference's own
        imprecision is propagated into P and therefore the verification
        margin, not just the point correction `mean`.
        """
        self.extra_bias_mean = mean
        self.extra_bias_var = var

    def _obs_var(self):
        return self.cal['sensor_var'] + self.extra_bias_var

    def moments(self):
        return self.moments_of(self.states,self.covs,self.weights)

    @staticmethod
    def moments_of(states,covs,weights):
        mean = weights @ states
        cov = sum(w*(p+np.outer(m-mean,m-mean)) for w,m,p in zip(weights,states,covs))
        return mean,cov

    def predict(self, duration):
        if duration == 0:
            return
        states,covs,weights=self._advance(duration,self.states,self.covs,self.weights)
        self.states,self.covs,self.weights=states,covs,weights

    def predicted(self, duration):
        """Pure lookahead: same transition as predict(), without mutating self.

        Used by the planner to score hypothetical action sequences before
        committing to one. Returns (states, covs, weights); chain calls to
        _advance with these to look further ahead, and moments_of(...) to
        read off a hypothetical (mean, cov).
        """
        if duration == 0:
            return self.states.copy(),self.covs.copy(),self.weights.copy()
        return self._advance(duration,self.states,self.covs,self.weights)

    def _advance(self, duration, states, covs, weights):
        # Context transitions occur at motor actions, not at repeated static reads.
        n=len(self.means)
        transition=np.array([[.96,.04],[.04,.96]]) if n==2 else np.ones((1,1))
        prior=weights@transition
        old_m=states.copy();old_p=covs.copy()
        new_states=states.copy();new_covs=covs.copy()
        for j in range(n):
            w=weights*transition[:,j]/prior[j]
            m=w@old_m
            p=sum(wi*(pi+np.outer(mi-m,mi-m)) for wi,mi,pi in zip(w,old_m,old_p))
            rho=.80 if self.contexts else 1.
            # d' = d-v*dt-coast; v' mean-reverts weakly to calibrated mode.
            f=np.array([[1.,-duration],[0.,rho]])
            reversion_target=self.lib_mean[j] if self.memory else self.means[j]
            new_states[j]=f@m+np.array([-self.cal['coast'],(1-rho)*reversion_target])
            new_covs[j]=f@p@f.T+np.diag([self.cal['motion_var'],.30 if self.contexts else .65])
        return new_states,new_covs,prior

    def observe(self, reading):
        y=reading-self.cal['sensor_bias']-self.extra_bias_mean
        if not self.initialised:
            self.states[:,0]=y;self.initialised=True
            return True
        obs_var=self._obs_var()
        mean,cov=self.moments()
        self.last_innovation=(y-mean[0])/math.sqrt(cov[0,0]+obs_var)
        if abs(self.last_innovation)>5:
            return False
        logs=[];raw_loglik=[]
        for j in range(len(self.means)):
            p=self.covs[j]; innovation=y-self.states[j,0]
            variance=p[0,0]+obs_var;gain=p[:,0]/variance
            ll=-.5*(math.log(2*math.pi*variance)+innovation**2/variance)
            raw_loglik.append(ll)
            logs.append(math.log(max(self.weights[j],1e-15))+ll)
            self.states[j]+=gain*innovation
            # Joseph form protects covariance numerically.
            a=np.eye(2)-np.outer(gain,[1.,0.])
            self.covs[j]=a@p@a.T+np.outer(gain,gain)*obs_var
        logs=np.array(logs); self.weights=np.exp(logs-logs.max());self.weights/=sum(self.weights)
        if self.fast_switch:
            self._update_cusum(np.array(raw_loglik))
        if self.memory and not self.memory_frozen:
            self._update_library()
        return True

    def _update_cusum(self,raw_loglik):
        """Accumulate persistent (not single-reading) evidence that a
        challenger context explains recent observations better than the one
        currently believed dominant, using the pure observation log-likelihood
        (no prior term) so this is a genuine change-point statistic rather than
        a restatement of the existing posterior weights.
        """
        dominant=int(np.argmax(self.weights))
        candidates=[k for k in range(len(self.means)) if k!=dominant]
        if not candidates:
            return
        advantages=raw_loglik-raw_loglik[dominant]
        best=max(candidates,key=lambda k:advantages[k])
        for k in candidates:
            self.cusum[k]=max(0.,self.cusum[k]+advantages[k]-self.CUSUM_SLACK) if k==best else 0.
        self.cusum[dominant]=0.
        if self.cusum[best]>self.CUSUM_THRESHOLD and self.lib_var[best]<self.LIB_VAR_INIT:
            self._jump_to(best)

    def _jump_to(self,k):
        """Discrete regime recognition: once accumulated evidence crosses the
        threshold and context k has a library entry mature enough to trust
        (has been confidently observed before), reset directly into it rather
        than waiting for the slow continuous weight-mixing in _advance to
        arrive at the same place on its own. This is the actual "reuse" step.
        """
        n=len(self.means)
        self.weights=np.full(n,(1.-self.JUMP_WEIGHT)/max(n-1,1))
        self.weights[k]=self.JUMP_WEIGHT
        self.states[k,1]=self.lib_mean[k]
        self.covs[k][1,1]=max(self.lib_var[k],self.JUMP_VAR_FLOOR)
        self.cusum[:]=0.

    def _update_library(self):
        """Controlled update: only fold a context's current speed estimate into
        its persistent library entry when that context is confidently active
        (posterior weight above LIB_CONFIDENCE_GATE), so ambiguous evidence never
        contaminates the memory. The Kalman-gain update is self-limiting (large
        steps while lib_var is large, shrinking as the library converges) and
        bounded below by LIB_VAR_FLOOR against false overconfidence.
        """
        for j in range(len(self.means)):
            if self.weights[j] <= self.LIB_CONFIDENCE_GATE:
                continue
            v_j, p_vv = self.states[j, 1], self.covs[j][1, 1]
            gain = self.lib_var[j] / (self.lib_var[j] + p_vv)
            self.lib_mean[j] += gain * (v_j - self.lib_mean[j])
            self.lib_var[j] = max(self.LIB_VAR_FLOOR, (1 - gain) * self.lib_var[j])

    def information(self,duration):
        """Gaussian proxy: expected information about speed from the next reading.

        This is not full expected free energy or context mutual information.
        """
        _,p=self.moments();f=np.array([[1.,-duration],[0.,1.]])
        pp=f@p@f.T
        if duration:pp+=np.diag([self.cal['motion_var'],.30])
        posterior=max(1e-9,pp[1,1]-pp[1,0]**2/(pp[0,0]+self._obs_var()))
        return max(0.,.5*math.log(max(pp[1,1],1e-9)/posterior))
