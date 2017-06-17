import logging
from np8742_tcp_comm import NP8742_TCP
import time

""" High-level motor controller class"""
class MotorControl():
    """ Class initialization """
    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = logger

        # TODO check status of arduino communication
        self.state = 'READY'
        # self.state = 'NOT READY' if failed

        # open connection to driver
        self.driver = NP8742_TCP(settings.host, settings.port, settings.timeout, settings.softStart, logger)

        self.errormsg = 'Command "{}" is not defined. \n select from [{}]'
        self.errormsg_numeric = 'Cound not parse numeric imput: "{}"'

        self.decoder_comm = ArduinoComm('COM10', record=True)
        self.decoder_comm.START()

	self.positions = [0]*settings.motor_count

    def close(self):
        self.driver.gentle_close()

    #===========================================================================
    #===================== HELPER COMMANDS =====================================
    #===========================================================================
    """ Read current position from encoderd log file.
        IOError on failure to read file """
    def getPosition(self, channel):
        try:
            pos = self.decoder_comm.READ(channel)
            self.positions[channel] = pos
        except:
            self.logger.exception("There was an issue with the arduino comm.")
            self.state = 'NOT READY'

        return pos

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
            self.waitForCmd(cmdID)
        """
    def waitForCmd(self, cmdID):
        last_cid = -1
        #print "block until cmd: {}".format(cmdID)
        while not self.driver.cmdFinishedQ(cmdID):
            cid = self.driver.currentCmdID()
            if cid != last_cid:
              self.logger.debug("current cmd: {}, waiting for: {}".format(cid,cmdID))
              last_cid = cid
            time.sleep(0.1) # not having print statement seems to break the loop for some reason

    """ Put code here to be called after a new motor position is achieved
        """
    def newPositionEvent(self, channel, position):
        pass

    #===========================================================================
    #===================== MOVEMENT COMMANDS ===================================
    #===========================================================================
    """ Move motor to the position in degrees relative to the current position"""
    def move_rel(self, channel, degrees):
        abs_deg = self.getPosition() + degrees
        return self.move_abs(channel, abs_deg)

    """ Move motor to the position in [units] relative to the current position.
        Returns IndexError if channel is out of range."""
    def move_rel_steps(self, channel, steps):
        # check channel range
        if channel < self.settings.motor_count:
            if self.state == 'READY':
		motor = channel + 1 # motors start at 1 on controller
                cmdID = self.driver.queueCommand("{}PR{}".format(motor,steps))[1]
                self.waitForCmd(cmdID)
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
        avg_steps = self.settings.steps_per_degree[channel]*(position - degrees)
        # we should arrive with positive stepping
        # turning the screw forward to minimize hysteresis
        if avg_steps < 0:
	    steps = int(round(avg_steps - self.settings.overshoot[channel]))
            status_msg = "Need to go negative. Current position {}DEG. Setpoint {}DEG. Steps to be taken: {}"
            self.logger.info(status_msg.format(position, degrees, steps))
	    try:
                ret = self.move_rel_steps(channel, steps)
	    except IndexError:
		print "motor is registered"

            if ret < 0: # if encoderd is not running dont allow motor movement
                return ret

        # now move forward
        msg = ''
        position = self.getPosition(channel)
        for i in range(self.settings.max_iterations):
            steps = zf*self.settings.steps_per_degree[channel]*( position - degrees )
            steps = int(round(steps))
            if( steps == 0 ):
                steps = 1
            status_msg = "Current position {}DEG. Setpoint {}DEG. Steps to be taken: {}"
            self.logger.debug(status_msg.format(position, degrees, steps))
            ret = self.move_rel_steps(channel, steps)
            if ret < 0:
                return ret
            position = self.getPosition(channel)
            if( degrees > position ):
                msg = "Current position {} deg. Setpoint exceeded by {} deg"
                break
            if( abs(degrees - position) <= 1/(2 * self.settings.steps_per_degree[channel]) ):
                msg = "New motor position is {} deg, error {} deg."
                break

        if( abs(position-degrees)<=self.settings.max_angle_errors[channel] ):
            if msg=='':
                msg = "Current position {} deg. Setpoint not achieved by {} deg after max iterations."
            self.logger.info(msg.format(position, position-degrees))
        else:
            self.logger.error(msg.format(position, position-degrees))

        self.newPositionEvent(channel, position)
        return 0
