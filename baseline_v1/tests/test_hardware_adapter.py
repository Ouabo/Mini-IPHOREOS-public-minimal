"""Desktop mocks check adapter semantics, not electrical compatibility."""
import sys,types,importlib
import pytest

def load(monkeypatch,pulse=-1,button=False):
    calls=[]
    class Pin:
        NO_PULL=0
        def write_digital(self,x): calls.append(('pin',x))
        def set_pull(self,x): pass
    class Driver:
        def motorOff(self,m): calls.append(('off',m))
        def motorOn(self,*a): calls.append(('on',)+a)
    mb=types.ModuleType('microbit');mb.pin13=Pin();mb.pin14=Pin();mb.button_b=types.SimpleNamespace(is_pressed=lambda:button);mb.sleep=lambda x:None;mb.running_time=lambda:0
    machine=types.ModuleType('machine');machine.time_pulse_us=lambda *x:pulse
    utime=types.ModuleType('utime');utime.sleep_us=lambda x:None;utime.ticks_ms=lambda:0;utime.ticks_diff=lambda a,b:a-b
    vendor=types.ModuleType('KitronikMOVEMotor');vendor.MOVEMotor=Driver
    for name,module in [('microbit',mb),('machine',machine),('utime',utime),('KitronikMOVEMotor',vendor)]:monkeypatch.setitem(sys.modules,name,module)
    sys.modules.pop('hardware',None);h=importlib.import_module('hardware')
    return h.Robot(),calls

def test_timeout_is_missing_not_free_space(monkeypatch):
    r,c=load(monkeypatch);assert r.distance() is None;assert ('off','l') in c and ('off','r') in c
def test_echo_conversion(monkeypatch):
    r,c=load(monkeypatch,pulse=1450);assert r.distance()==25
def test_stop_button_blocks_motor_start(monkeypatch):
    r,c=load(monkeypatch,button=True)
    with pytest.raises(RuntimeError): r.pulse(45,45,120)
    assert not any(x[0]=='on' for x in c)
def test_pulse_limits(monkeypatch):
    r,c=load(monkeypatch)
    with pytest.raises(ValueError): r.pulse(200,200,1000)
    assert not any(x[0]=='on' for x in c)
