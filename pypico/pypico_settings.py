import imp # for loading config file in another directory
import os.path
import util

host = '169.254.5.20'
port = 23 # telnet port (do not change)

motor_count = 2 # number of motors
max_iterations = 20 # attempts to hit setpoint
timeout = 1 # asynchat timeout
softStart = False # softStart will not check the type of motor attached to the controller
# checking the type of motor will move it a little bit. If that is not acceptable then set to True

# motor calibrations: 2016/03/19
steps_per_degree = [44.5,36.6]
# set to about 2 std devs
zeno_factor = [0.7,0.7]
# steps to overshoot setpoint when moving backwards
overshoot = [1000,1000]

# max angle errors (degrees) without throwing an error
# for us 1 degree ~ 11 deg/um -> 0.1 deg / 11 deg/um = 10 nm 
max_angle_errors = [0.1,0.1]

## ENCODERD file locations
encoderd_settings_path = '/home/pi/encoderd/'
encoderd_settings_file = 'encoderd_settings'
print encoderd_settings_file

f, filename, desc = imp.find_module(encoderd_settings_file, [encoderd_settings_path])
encoderd_settings = imp.load_module(encoderd_settings_file, f, filename, desc)
encoderd_refresh_rate = encoderd_settings.REFRESH_RATE

encoderd_log_path = '/home/pi/.encoderd/'
encoderd_pidfile = os.path.join(encoderd_log_path,'encoderd.pid')

# motor angle log files
motor_angle_files = [ 'Angle_780X.log', 'Angle_780Y.log' ]
motor_angle_files = [ os.path.join(encoderd_log_path, f) for f in motor_angle_files ]

try:
  pf = file(encoderd_pidfile,'r')
  encoderd_pid = int(pf.read().strip())
  pf.close()
except IOError:
  encoderd_pid = None

if encoderd_pid:
  encoderd_running = util.pid_exists(encoderd_pid)
else:
  encoderd_running = False
