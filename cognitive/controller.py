"""Belief -> grounded relations -> intended option -> realised-event memory."""
import math
from .model import Belief


class CognitiveController:
    def __init__(self, calibration, contexts=True, informative=True, context_memory=False, fast_switch=False, target=25., band=4., memory_frozen=False):
        self.belief=Belief(calibration,contexts,memory=context_memory,fast_switch=fast_switch,memory_frozen=memory_frozen)
        self.informative=informative
        self.target=target;self.band=band
        self.memory=[];self.verify=0;self.moves=0;self.invalid=0
        self.last_action='START';self.terminal=None

    def calibrate_bias(self,ref_readings,ref_distance):
        """Fold in a one-time, known-distance reference check (ref_readings:
        raw sensor readings of a target at ref_distance, already corrected for
        neither sensor_bias nor this extra bias). Estimates any deployment-
        time bias beyond the static calibration, with its own standard error,
        and propagates both into the belief via Belief.set_bias_reference --
        see cognitive/model.py. Call once, before the main step() loop.
        """
        cal=self.belief.cal
        mean=sum(ref_readings)/len(ref_readings)-cal['sensor_bias']-ref_distance
        var=cal['sensor_var']/len(ref_readings)
        self.belief.set_bias_reference(mean,var)
        return mean,var

    def step(self,reading,time):
        if self.terminal:return self.terminal,0.
        valid=reading is not None and math.isfinite(reading) and 12<=reading<=150
        if valid:valid=self.belief.observe(reading)
        if not valid:
            self.invalid+=1;self.verify=0
            return self._record('ABORT' if self.invalid>=3 else 'SAMPLE',0.,reading,time,'invalid_or_inconsistent_reading')
        self.invalid=0
        mean,p=self.belief.moments();d=mean[0];sd=math.sqrt(p[0,0])
        if time>=80 or self.moves>=100:
            return self._record('ABORT',0.,reading,time,'budget_exhausted')
        in_target=abs(d-self.target)+1.64*sd<=self.band
        self.verify=self.verify+1 if in_target else 0
        if self.verify:
            return self._record('DONE' if self.verify>=3 else 'SAMPLE',0.,reading,time,'verify_target')
        if d<self.target-self.band:
            return self._record('ABORT',0.,reading,time,'estimated_overshoot')
        dt,info=self._plan(d)
        return self._record('MOVE' if dt else 'SAMPLE',dt,reading,time,'goal_and_information' if self.informative else 'goal_only',info)

    def _plan(self,d):
        """Receding-horizon (2-step) lookahead over candidate pulse durations.

        Enumerates both this step's and the next step's duration, scores the
        pair by rolling the belief forward with Belief.predicted/_advance
        (without mutating it), and executes only the first duration of the
        best-scoring pair. A one-step planner can get stuck preferring
        repeated SAMPLE forever, particularly with information-seeking
        disabled, because it cannot see that a move now is what makes a
        later verification possible; the explicit no-progress penalty below
        targets exactly that failure mode.
        """
        b=self.belief;durations=(0.,.12,.24);sequences=[];floor=self.target-self.band
        for dt1 in durations:
            states1,covs1,weights1=b.predicted(dt1)
            mean1,cov1=b.moments_of(states1,covs1,weights1)
            if dt1 and (mean1[0]-2.33*math.sqrt(max(cov1[0,0],0))-.5<floor):continue
            info=b.information(dt1) if self.informative else 0.
            cost1=.08*(dt1+.20 if dt1 else .15)
            for dt2 in durations:
                states2,covs2,weights2=(states1,covs1,weights1) if dt2==0. else b._advance(dt2,states1,covs1,weights1)
                mean2,cov2=b.moments_of(states2,covs2,weights2)
                if dt2 and (mean2[0]-2.33*math.sqrt(max(cov2[0,0],0))-.5<floor):continue
                cost2=.08*(dt2+.20 if dt2 else .15)
                goal=((mean2[0]-self.target)**2+cov2[0,0])/400
                sequences.append(dict(dt1=dt1,dt2=dt2,info=info,
                    score=goal+cost1+cost2-.8*info,displacement=d-mean2[0]))
        if not sequences:
            return 0.,0.
        if any(s['displacement']>1. for s in sequences):
            for s in sequences:
                if s['dt1']==0. and s['dt2']==0.:s['score']+=1.0
        best=min(sequences,key=lambda s:s['score'])
        return best['dt1'],best['info']

    def _record(self,action,dt,reading,time,reason,info=0.):
        b=self.belief
        mean,p=b.moments()
        event='initial_reading' if self.last_action=='START' else ('movement_observed' if self.last_action=='MOVE' else 'stationary_reading')
        if abs(b.last_innovation)>2:event='unexpected_outcome'
        if reason=='verify_target':event='target_verification'
        if reason=='invalid_or_inconsistent_reading':event='unusable_reading'
        self.memory.append(dict(time=time,reading=reading,estimated_distance=float(mean[0]),estimated_speed=float(mean[1]),distance_sd=math.sqrt(p[0,0]),context_probabilities=dict(zip(b.names,map(float,b.weights))),concept_target=bool(abs(mean[0]-self.target)+1.64*math.sqrt(p[0,0])<=self.band),concept_expected_displacement=float(max(0,mean[1])*dt+(b.cal['coast'] if dt else 0)),realised_event=event,intended_option=action,pulse_seconds=dt,reason=reason,speed_information_proxy=info))
        self.last_action=action
        if action in ('DONE','ABORT'):self.terminal=action
        if action=='MOVE':self.moves+=1;self.verify=0;b.predict(dt)
        return action,dt
