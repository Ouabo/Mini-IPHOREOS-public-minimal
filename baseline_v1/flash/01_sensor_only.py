# Mini-IPHOREOS: 01_sensor_only
# Generated from firmware/. All motor enables remain False until you edit them.
class C:
    """Edit only after the tutorial's stationary and supported-wheel checks."""
    MODE = 'sensor'  # sensor, motor_test, pulse_calibration, or run
    MOTORS_ENABLED = False
    CALIBRATION_CONFIRMED = False
    POLICY = 'mini'  # raw, belief, mini
    CONTEXT = 'normal'  # normal or careful (selected before a trial)
    PWM_LEFT = 45     # vendor scale 0..255, NOT cm/s; provisional
    PWM_RIGHT = 45
    MAX_PWM = 80      # training cap, not a hardware safety certification
    PULSE_MS = 120
    SETTLE_MS = 200   # must exceed observed coast time before sensing
    SAMPLE_INTERVAL_MS = 150
    TRIGGER_PIN = 13
    ECHO_PIN = 14
    SENSOR_MAX_CM = 150
    CALIBRATION = {
        'sensor_bias_cm': 0.0, 'measurement_var': 4.0,
        'variance_floor': 0.36, 'speed_cm_s': 8.0,
        'coast_cm': 0.15, 'motion_var': 0.64,
        'extra_margin_cm': 0.5,
    }

# microbit-module: KitronikMOVEMotor@1.1.0
# Copyright (c) Kitronik Ltd 2022. 
#
# The MIT License (MIT)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from microbit import i2c, pin3, pin8, pin12, pin15, pin16, display, sleep
from neopixel import NeoPixel

# A module to simplify the driving o the motors on Kitronik :MOVE Motor buggy with micro:bit
#Some useful constants
CHIP_ADDR = 0x62 # CHIP_ADDR is the standard chip address for the PCA9632, datasheet refers to LED control but chip is used for PWM to motor driver
MODE_1_REG_ADDR = 0x00
MODE_2_REG_ADDR = 0x01
MOTOR_OUT_ADDR = 0x08 #MOTOR output register address
MODE_1_REG_VALUE = 0x00 #setup to normal mode and not to respond to sub address
MODE_2_REG_VALUE = 0x04  #Setup to make changes on ACK, outputs set to open-drain
MOTOR_OUT_VALUE = 0xAA  #Outputs set to be controled PWM registers

#Register offsets for the motors
LEFT_MOTOR = 0x04
RIGHT_MOTOR = 0x02

# Servo Constants
SERVO_MIN_PULSE = 500 #microsec
SERVO_MAX_PULSE = 2500 #microsec
SERVO_DEGREE_RANGE = 180
SERVO_DEG_TO_uS = (SERVO_MAX_PULSE - SERVO_MIN_PULSE) / SERVO_DEGREE_RANGE
SERVO_PWM_PERIOD = 20 #ms

LEDS_NUMBER = 4

class MOVEMotor:

    #An initialisation function to setup the PCA chip correctly
    #Note that if the :MOVE motor is off the microPython will likely throw OS error 19 - which menas it cant talk to the I2C chip
    def __init__(self):
        self.moveMotorVersion = 0
        display.clear()
        display.off()
        pin3.write_digital(1)
        sleep(100)
        if pin12.read_digital() == 1:
            pin3.write_digital(0)
            sleep(100)
            if pin12.read_digital() == 0:
                self.moveMotorVersion = 20
        
        display.on()
        buffer = bytearray(2)

        if self.moveMotorVersion == 0:
            try:
                buffer[0] = MODE_1_REG_ADDR
                buffer[1] = MODE_1_REG_VALUE
                i2c.write(CHIP_ADDR,buffer,False)
                readBuffer = i2c.read(CHIP_ADDR,1,False)
                if readBuffer[0] == MODE_1_REG_VALUE:
                    self.moveMotorVersion = 10
            except OSError:
                self.moveMotorVersion = 31
                self.ws2811 = NeoPixel(pin12, 2)
        
        if self.moveMotorVersion != 31:
            try:
                buffer[0] = MODE_1_REG_ADDR
                buffer[1] = MODE_1_REG_VALUE
                i2c.write(CHIP_ADDR,buffer,False)
                buffer[0] = MODE_2_REG_ADDR
                buffer[1] = MODE_2_REG_VALUE
                i2c.write(CHIP_ADDR,buffer,False)
                buffer[0] = MOTOR_OUT_ADDR
                buffer[1] = MOTOR_OUT_VALUE
                i2c.write(CHIP_ADDR,buffer,False)
            except OSError:
                raise OSError("Check the Micro:bit is turned on!")
        
        # now setup PWM on the servo pin
        pin15.set_analog_period(SERVO_PWM_PERIOD)
        pin16.set_analog_period(SERVO_PWM_PERIOD)

        # Setup LEDs
        self.leds = NeoPixel(pin8, LEDS_NUMBER)

    # Function to set the requested motor running in chosen direction at a set speed.
    # motor = l for left and motor = r for right
    # direction = f for forward and direction = r for reverse
    # speed between 0 and 255
    def motorOn(self, motor, direction, speed):
        speed = int(speed)
        if speed > 255:
            speed = 255
        elif speed < 0:
            speed = 0
        
        if self.moveMotorVersion != 31:
            # V1 to V2 :MOVE Motor
            motorForward = bytearray([0, 0])
            motorBackward = bytearray([0, 0])
            if motor == "l":
                # Left motor
                motorForward[0] = LEFT_MOTOR
                motorBackward[0] = LEFT_MOTOR + 1
            elif motor == "r":
                # Right motor
                motorForward[0] = RIGHT_MOTOR + 1
                motorBackward[0] = RIGHT_MOTOR
            if direction == "f":
                # Going forwards
                motorForward[1] = speed
            elif direction == "r":
                # Going backwards
                motorBackward[1] = speed
            i2c.write(CHIP_ADDR, motorForward, False)
            i2c.write(CHIP_ADDR, motorBackward, False)
        
        else:
            # V3 :MOVE Motor
            motorBuf = bytearray([0, 0, 0])
            motorJump = bytearray([0, 0, 0])
            wsIndex = 0
            if motor == "l":
                # Left motor
                wsIndex = 1
                if direction == "f":
                    # Going forwards
                    motorBuf[0] = speed
                    motorJump[0] = 255
                elif direction == "r":
                    # Going backwards
                    motorBuf[1] = speed
                    motorJump[1] = 255
            elif motor == "r":
                # Right motor
                wsIndex = 0
                if direction == "f":
                    # Going forwards
                    motorBuf[1] = speed
                    motorJump[1] = 255
                elif direction == "r":
                    # Going backwards
                    motorBuf[0] = speed
                    motorJump[0] = 255
            self.ws2811[wsIndex] = (motorJump[0], motorJump[1], motorJump[2])
            self.ws2811.show()
            sleep(1) # 1 ms
            self.ws2811[wsIndex] = (motorBuf[0], motorBuf[1], motorBuf[2])
            self.ws2811.show()

    # A function that stop a given motor
    # motor = l for left and motor = r for right
    def motorOff(self, motor):
        if self.moveMotorVersion != 31:
            # V1 to V2 :MOVE Motor
            stopBuffer = bytearray([0, 0])
            if motor == "l":
                # Left motor
                stopBuffer[0] = LEFT_MOTOR
                i2c.write(CHIP_ADDR, stopBuffer, False)
                stopBuffer[0] = LEFT_MOTOR + 1
                i2c.write(CHIP_ADDR, stopBuffer, False)
            elif motor == "r":
                # Right motor
                stopBuffer[0] = RIGHT_MOTOR
                i2c.write(CHIP_ADDR, stopBuffer, False)
                stopBuffer[0] = RIGHT_MOTOR + 1
                i2c.write(CHIP_ADDR, stopBuffer, False)
        
        else:
            # V3 :MOVE Motor
            if motor == "l":
                # Left motor
                self.ws2811[1] = (0, 0, 255)
            elif motor == "r":
                # Right motor
                self.ws2811[0] = (0, 0, 255)
            self.ws2811.show()
    
    # Servo Control
    # servo is expected to be 1 or 2, as per the silk on the buggy.
    # Servos are on Pins 15 and 16. We write an analog to them.
    # goToPosition converts degrees to microseconds and calls gotoPeriod, 
    def goToPosition(self, servo, degrees):
        period = SERVO_MIN_PULSE + (SERVO_DEG_TO_uS * degrees)
        self.goToPeriod(servo, period)
        
    def goToPeriod(self, servo, period):
        if servo < 1:
            servo = 1
        elif servo > 2:
            servo = 2
        if period < SERVO_MIN_PULSE:
            period = SERVO_MIN_PULSE
        elif period > SERVO_MAX_PULSE:
            period = SERVO_MAX_PULSE
        duty = round(period * 1024 * 50 // 1000000) #1024-steps in analog, 50Hz frequency, // to convert to uS
        if servo == 1:
            pin15.write_analog(duty)
        elif  servo == 2:
            pin16.write_analog(duty)
    
    # LED Control
    def setLED(self, led, colour):
        if led < 0:
            led = 0
        elif led > LEDS_NUMBER - 1:
            led = LEDS_NUMBER - 1
        self.leds[led] = colour
    
    def setLEDs(self, colour):
        for i in range(LEDS_NUMBER):
            self.setLED(i, colour)
    
    def showLEDs(self):
        self.leds.show()

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

"""Hardware adapter: Kitronik :MOVE Motor + micro:bit V2 only.
Ultrasonic P13/P14 follows Kitronik's MakeCode source. Range timing uses
MicroPython machine.time_pulse_us; empirical calibration is required.
"""
from microbit import pin13,pin14,button_b,sleep,running_time
from machine import time_pulse_us
from utime import sleep_us,ticks_ms,ticks_diff


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

"""Copy this and the four support files into the micro:bit Python Editor.
Default sensor mode never requests motor movement. B stops an active trial.
"""
from microbit import button_a,button_b,display,Image,sleep,running_time




def emit(trial,action,raw,controller=None):
    s=controller.snapshot() if controller else {}
    print('LOG,%s,%d,%s,%s,%s,%s,%s,%s' % (
        trial,running_time(),action,str(raw),str(s.get('mu_cm','')),
        str(s.get('sd_cm','')),str(s.get('moves','')),s.get('reason','')))

def wait_start(robot):
    robot.stop();display.show('A')
    while button_a.is_pressed(): sleep(20)
    while not button_a.is_pressed():
        if button_b.is_pressed(): robot.stop()
        sleep(20)
    while button_a.is_pressed(): sleep(20)
    if button_b.is_pressed(): raise RuntimeError('USER_STOP')

def main():
    robot=None
    try:
        if C.TRIGGER_PIN!=13 or C.ECHO_PIN!=14: raise ValueError('Unsupported sensor pin mapping')
        robot=Robot();robot.colour(0,0,12)
        print('LOG_HEADER,trial_id,time_ms,action,raw_cm,mu_cm,sd_cm,moves,reason')
        print('INFO,driver_board_version',robot.driver.moveMotorVersion)
        if C.MODE=='sensor':
            display.show('S')
            while not button_b.is_pressed():
                emit('stationary','SENSOR',robot.distance());sleep(C.SAMPLE_INTERVAL_MS)
            return
        if not C.MOTORS_ENABLED: raise ValueError('Set MOTORS_ENABLED only after supported-wheel preparation')
        if C.PWM_LEFT>C.MAX_PWM or C.PWM_RIGHT>C.MAX_PWM: raise ValueError('PWM exceeds training cap')
        if C.MODE in ('motor_test','pulse_calibration'):
            wait_start(robot)
            seconds=robot.pulse(C.PWM_LEFT,C.PWM_RIGHT,C.PULSE_MS)
            print('INFO,executed_pulse_seconds',seconds)
            sleep(C.SETTLE_MS);display.show(Image.SQUARE);return
        if C.MODE!='run': raise ValueError('Unknown MODE')
        if not C.CALIBRATION_CONFIRMED: raise ValueError('Finish sensor, speed and coast calibration first')
        cfg=dict(C.CALIBRATION);cfg['pulse_s']=C.PULSE_MS/1000.0
        controller=Controller(C.POLICY,C.CONTEXT,cfg)
        wait_start(robot);trial=str(running_time());started=running_time()
        while True:
            if button_b.is_pressed(): raise RuntimeError('USER_STOP')
            raw=robot.distance()
            action=controller.observe(raw,(running_time()-started)/1000.0)
            emit(trial,action,raw,controller)
            if action=='MOVE':
                robot.colour(0,12,0);display.show(Image.ARROW_N)
                elapsed=robot.pulse(C.PWM_LEFT,C.PWM_RIGHT,C.PULSE_MS)
                controller.record_move(elapsed);sleep(C.SETTLE_MS)
            elif action=='SAMPLE':
                robot.stop();robot.colour(12,6,0);display.show('?');sleep(C.SAMPLE_INTERVAL_MS)
            else:
                robot.stop();display.show(Image.HAPPY if action=='DONE' else Image.NO)
                robot.colour(0,12,0) if action=='DONE' else robot.colour(12,0,0)
                break
    except Exception as error:
        print('ERROR',str(error));display.show(Image.NO)
    finally:
        if robot is not None: robot.stop()

main()
