"""Hardware adapter: Kitronik :MOVE Motor + micro:bit V2 only.
Ultrasonic P13/P14 follows Kitronik's MakeCode source. Range timing uses
MicroPython machine.time_pulse_us; empirical calibration is required.
"""
from microbit import pin13,pin14,button_b,sleep,running_time
from machine import time_pulse_us
from utime import sleep_us,ticks_ms,ticks_diff
from KitronikMOVEMotor import MOVEMotor

class Robot:
    def __init__(self):
        self.driver=MOVEMotor()
        self.stop()
        pin13.write_digital(0)
        pin14.set_pull(pin14.NO_PULL)

    def stop(self):
        # Attempt both channels even if one channel reports an error.
        try: self.driver.motorOff('l')
        finally: self.driver.motorOff('r')

    def distance(self):
        pin13.write_digital(0);sleep_us(5)
        pin13.write_digital(1);sleep_us(10);pin13.write_digital(0)
        duration=time_pulse_us(pin14,1,12000)
        if duration<=0: return None
        cm=duration/58.0
        return cm if 2.0<=cm<=150.0 else None

    def pulse(self,left,right,milliseconds):
        if button_b.is_pressed(): raise RuntimeError('USER_STOP')
        if not (0<=left<=80 and 0<=right<=80 and 0<milliseconds<=250):
            raise ValueError('Pulse outside training limits')
        start=ticks_ms()
        try:
            self.driver.motorOn('l','f',left)
            self.driver.motorOn('r','f',right)
            while ticks_diff(ticks_ms(),start)<milliseconds:
                if button_b.is_pressed(): raise RuntimeError('USER_STOP')
                sleep(5)
        finally:
            self.stop()
        return ticks_diff(ticks_ms(),start)/1000.0

    def colour(self,r,g,b):
        self.driver.setLEDs((r,g,b));self.driver.showLEDs()
