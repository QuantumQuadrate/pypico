'''fakeMotorControl.py emulates the basic behavior of the motor controller for
testing.

TODO: change this to inherit from main motor controller
'''

import logging
import time
import numpy as np

""" High-level motor controller class"""
class MotorControl():
    """ Class initialization """
    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = logger
        self.state = 'READY'
        self.errormsg = 'Command "{}" is not defined. \n select from [{}]'
        self.errormsg_numeric = 'Cound not parse numeric imput: "{}"'
        self.positions =  [0]*settings.motor_count

    def close(self):
        self.logger.info("Close of fake controller requested.")

    #===========================================================================
    #===================== HELPER COMMANDS =====================================
    #===========================================================================
    """ Read current position from encoderd log file.
        IOError on failure to read file """
    def getPosition(self, channel):
        self.state = 'READY'
        # wait for some time for science
        time.sleep(0.1)
        return self.positions[channel] # its a number

    """ Converts numeric in [units] to degrees
        Raises KeyError if units are incorrect.
        Acceptable units: [DEG(default), STEP]"""
    def unit2degrees(self, channel, numeric, unit):
        s = unit.upper()
        s = s.strip()
        if unit == "DEG":
          return numeric
        elif unit == "STEP":
          return numeric * self.calibrations[channel]
        else:
          raise KeyError

    """ block execution until a certain command finishes execution.
        Typical use:
            cmdID = self.driver.queueCommand([command])[1]
            waitForCmd(cmdID)
        """
    def waitForCmd(self, cmdID):
        # just wait for some time
        time.sleep(2)

    """ Put code here to be called after a new motor position is achieved
        """
    def newPositionEvent(self, channel, position):
        pass

    #===========================================================================
    #===================== MOVEMENT COMMANDS ===================================
    #===========================================================================
    """ Move motor to the position in degrees relative to the current position
    """
    def move_rel(self, channel, degrees):
        abs_deg = self.getPosition(channel) + degrees
        return self.move_abs(channel, abs_deg)

    """ Move motor to the position in [units] relative to the current position.
        Returns IndexError if channel is out of range."""
    def move_rel_steps(self, channel, steps):
        # check channel range
        if channel < self.settings.motor_count:
            if self.state == 'READY':
                self.logger.info("Not sending command: {}PR{}".format(channel,steps))
                self.waitForCmd(1)
                # fake some movement with some error
                deg_target = steps/self.settings.steps_per_degree[channel]
                self.positions[channel] += deg_target*(1 + 0.1*np.random.randn(1)[0]) # 10% error
                self.logger.info("Changing position randomly to: {} DEG".format(self.positions[channel]))
                return 0
            else:
                return -1
        else:
            raise IndexError

    """ Move motor to the absolute position in degrees.
        Performs Zeno arrow approach to setpoint"""
    def move_abs(self, channel, degrees):
        # ratio of estimated steps to take when approaching setpoint
        # the larger the spread in steps the smaller the ratio should be
        # a small spread should approach 1.0
        # typical is 0.8-0.9
        zf = self.settings.zeno_factor[channel]
        # get approximate steps
        position = self.getPosition(channel)

        if( abs(position-degrees)<=self.settings.max_angle_errors[channel] ):
            self.logger.info('Already within acceptable angle error, not moving')
            return 0

        avg_steps = self.settings.steps_per_degree[channel]*(degrees - position)
        # we should arrive with positive stepping
        # turning the screw forward to minimize hysteresis
        if avg_steps < 0:
            ret = self.move_rel_steps(channel, avg_steps - self.settings.overshoot[channel])
            if ret < 0: # if encoderd is not running dont allow motor movement
                return ret

        position = self.getPosition(channel)
        msg = ''
        # now move forward
        for i in range(self.settings.max_iterations):
            steps = zf*self.settings.steps_per_degree[channel]*(degrees - position)
            steps = int(round(steps))
            if(steps == 0):
                steps = 1
            ret = self.move_rel_steps(channel, steps)
            if ret < 0:
                return ret
            position = self.getPosition(channel)
            if( degrees < position ):
                msg = "Current position {} deg. Setpoint exceeded by {} deg"
                break
            if( abs(degrees - position) <= 1/(2 * self.settings.steps_per_degree[channel] )):
                msg = "New motor position is {} deg, error {} deg."
                break

        if( abs(position-degrees)>=self.settings.max_angle_errors[channel] ):
            if not msg:
                msg = "Current position {} deg. Setpoint not achieved by {} deg after max iterations."
            self.logger.error(msg.format(position, position-degrees))
        else:
            self.logger.info(msg.format(position, position-degrees))

        self.newPositionEvent(channel, position)
        return 0
