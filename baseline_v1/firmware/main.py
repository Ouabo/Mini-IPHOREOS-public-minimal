"""Copy this and the four support files into the micro:bit Python Editor.
Default sensor mode never requests motor movement. B stops an active trial.
"""
from microbit import button_a,button_b,display,Image,sleep,running_time
import config as C
from hardware import Robot
from belief_controller import Controller

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
