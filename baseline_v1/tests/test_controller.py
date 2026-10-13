from pathlib import Path
import sys,math
import pytest
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'firmware'));sys.path.insert(0,str(R))
from belief_controller import Controller
from simulate import episode

@pytest.mark.parametrize('reading',[None,float('nan'),float('inf'),200.])
def test_invalid_never_moves(reading):
    c=Controller()
    assert c.observe(reading,0)=='SAMPLE'
    assert c.observe(reading,.15)=='SAMPLE'
    assert c.observe(reading,.30)=='ABORT'

def test_low_reading_stops_immediately():
    assert Controller().observe(5,0)=='ABORT'

def test_bayes_update_and_motion_prediction():
    c=Controller(config={'target_cm':50})
    c.observe(50,0);c.observe(52,.1)
    assert c.mu==51 and c.var==2
    c.record_move(.12)
    assert c.mu==pytest.approx(51-.96-.15) and c.var==pytest.approx(2.64)

def test_context_changes_same_belief_decision():
    a=Controller(context='normal');b=Controller(context='careful')
    assert a.observe(26,0)=='MOVE'
    assert b.observe(26,0)=='SAMPLE'

def test_verification_requires_multiple_samples():
    c=Controller()
    assert c.observe(25,0)=='SAMPLE'
    assert c.observe(25,.15)=='SAMPLE'
    assert c.observe(25,.3)=='DONE'
    assert c.observe(70,.45)=='DONE'

def test_inconsistent_sensor_aborts_without_chasing_outlier():
    c=Controller();c.observe(50,0)
    assert c.observe(100,.1)=='SAMPLE'
    assert c.observe(100,.2)=='SAMPLE'
    assert c.observe(100,.3)=='ABORT'

def test_uncertainty_floor_prevents_false_infinite_precision():
    c=Controller(config={'max_samples':1000,'verify_count':1000})
    for i in range(80): c.observe(25,i*.1)
    assert c.var>=.36

def test_expired_trial_and_move_limit():
    c=Controller();c.observe(60,0)
    assert c.observe(60,61)=='ABORT'
    c=Controller(config={'max_moves':1});c.observe(60,0);c.record_move(.12)
    assert c.observe(59,.5)=='ABORT'

def test_no_automatic_reverse_after_overshoot():
    c=Controller()
    actions=[c.observe(19,i*.15) for i in range(20)]
    assert 'MOVE' not in actions and actions[-1]=='ABORT'

def test_invalid_configuration():
    with pytest.raises(ValueError): Controller(config={'measurement_var':0})
    with pytest.raises(ValueError): Controller(config={'pulse_s':1})

def test_reproducibility_and_independent_success_definition():
    assert episode(12,'mini','normal')==episode(12,'mini','normal')
    for s in (False,True):
        r=episode(12,'mini','normal',s)
        assert r['independent_success']==int(r['terminal']=='DONE' and abs(r['final_cm']-25)<=4)
