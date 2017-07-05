host = '192.168.1.122'
port = 23 # telnet port (do not change)

motor_count = 4 # number of motors
max_iterations = 20 # attempts to hit setpoint
timeout = 1 # asynchat timeout
softStart = False # softStart will not check the type of motor attached to the controller
# checking the type of motor will move it a little bit. If that is not acceptable then set to True

# 780 motor calibrations: 2016/03/19
# 480 motor calibrations: 2017/06/17
steps_per_degree = [-44.5, -36.6, -36.5, -45.8]
# set to about 2 std devs
zeno_factor = [0.7, 0.7, 0.7, 0.7]
# steps to overshoot setpoint when moving backwards
overshoot = [1000, 1000, 1000, 1000]

# max angle errors (degrees) without throwing an error
# for us 1 degree ~ 11 deg/um -> 0.1 deg / 11 deg/um = 10 nm
max_angle_errors = [0.1, 0.1, 0.1, 0.1]

#serial ports
port = ['COM10', 'COM11']

# list of attached encoders
encoders=[
    dict(
        name="780X",                # device nickname
        calibration=360/(2048*4.0), # degrees/step, HEDR-55L2-BH07
    ),
    dict(
        name="780Y",                # device nickname
        calibration=360/(2048*4.0), # degrees/step, HEDR-55L2-BH07
    ),
    dict(
        name="480X",                # device nickname
        calibration=360/(2048*4.0), # degrees/step, HEDR-55L2-BH07
    ),
    dict(
        name="480Y",                # device nickname
        calibration=360/(2048*4.0), # degrees/step, HEDR-55L2-BH07
    ),
]
