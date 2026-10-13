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
