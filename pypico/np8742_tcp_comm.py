# ======================================================================
# Copyright 2015 by Matthew Ebert
#
#                         All Rights Reserved
#
# Permission to use, copy, modify, and distribute this software and
# its documentation for any purpose and without fee is hereby
# granted, provided that the above copyright notice appear in all
# copies and that both that copyright notice and this permission
# notice appear in supporting documentation, and that the name of 
# Matthew Ebert not be used in advertising or publicity pertaining to
# distribution of the software without specific, written prior
# permission.
#
# MATTHEW EBERT DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN
# NO EVENT SHALL MATTHEW EBERT BE LIABLE FOR ANY SPECIAL, INDIRECT OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
# OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
# ======================================================================

"""A class that implements low-level TCP/IP socket protocols for a Newport
8742 picomotor controller.

The commands sent to the 8742 controller form two classes:
1. an instruction (i.e. move, change velocity, etc.),
2. a query (i.e position, firmware version, etc.)
Queries end with a question mark ('?'), while instructions do not. Responses
are expected for queries but not for instructions.
Instructions appear to be blocking to other instructions, but queries can be
completed while an instruction is still executing.
The stop (ST) and abort (AB) commands, should have priority but I have not
confirmed this.

For example:
Move motor 1 1000 steps forward (1PR1000), position query on motor 1 (1TP?).
If motor 1 is still moving when the position query is recieved the
instantaneous position is returned. If the final position is desired then one
must query if the motor has finished moving (1MD?) until the response is '1'.
At this point the position query can be sent to obtain the final position.

This module is intended to provide a basic framework for implementing commands
sent to the device, waiting for expected responses and checking for motion to 
cease before sending the next command in the buffer.
"""

import asynchat, asyncore
import socket
import time
import threading
import logging
import re

class EmptyBuffer(Exception):
  """The command buffer is empty"""
  pass

class NP8742_TCP( asynchat.async_chat ):
  """This class handles TCP socket communications and is built on asynchat"""
  # ============================================================================
  def __init__(self, host, port=23, timeout=1, softStart=False, logger=None):
    """Initialize the class, open the socket"""
    asynchat.async_chat.__init__(self)

    self.STATES = [ "READY", "DISCONNECTED", "MV_WAIT", "ERROR", "EMPTY" ]
    self.state = self.STATES[1]

    self.logger = logger or logging.getLogger(__name__)

    self.__dict__['motorTypes'] = [0,0,0,0]
    self.__dict__['positions'] = [0,0,0,0]
    self.__dict__['velocities'] = [0,0,0,0]
    self.__dict__['accelerations'] = [0,0,0,0]

    
    self.ibuffer = [] # input buffer
    self.obuffer = '' # output buffer
    self.set_terminator('\r\n') # command and response termination protocol

    # store commands in a buffer that we only pop off after getting a response 
    # from the previous command
    self.cmdFIFO = asynchat.fifo()
    self.cmdCount = 0 # total commands sent to command buffer
    self.cmdID = -1 # ID number of last command sent to 8742
    # can be used to block the main thread until after a specfic command has been executed
    self.lastCmd = ''

    # connection info
    self.host = host # ip address
    self.port = port # port num (defaults to telnet port 23)
    self.timeout = timeout # time to wait for the listening thread after close

    self.connect(softStart)

  # ============================================================================
  def connect(self, softStart=False):
    """Create socket, connect, send status queries"""
    self.create_socket(socket.AF_INET, socket.SOCK_STREAM) # create tcp socket 
    try:
      # call parent connect method
      asynchat.async_chat.connect( self, (self.host, self.port) )
    except IOError:
      self.logger.error("Connection to %s:%s failed.",self.host,self.port)
      self.changeState("DISCONNECTED")
    else:
      self.logger.info("Connection to %s:%s succeeded.",self.host,self.port)
      self.changeState("READY")
      self.start(softStart)

  # ============================================================================
  def start(self, softStart):
    """Fill up buffer with start up commands, then start the listening loop."""
    self.queueCommand('ve?') # this one gets the telnet response too
    self.queueCommand('*idn?')
    if softStart:
      self.logger.info("Soft starting, no motor check will be performed.")
    else:
      self.logger.warning("Hard starting, motor check will be performed.")
      self.queueCommand('mc')

    # start pushing to the command buffer
    self.found_terminator()

    # asyncore.loop will block so it will need to be started in a new thread
    self.loop_thread = threading.Thread(
        target=asyncore.loop,
        name="Asyncore Loop",
        kwargs={'timeout':self.timeout} # ends loop after the socket is closed
    )
    self.logger.debug("Starting loop thread.")
    self.loop_thread.start()
    self.logger.debug("Loop thread started.")

    for i in range(3):
      self.queueCommand(str(i+1) + 'qm?')
      # wait until the motor type is updated
      while self.cmdFIFO.__len__() > 0:
        time.sleep(0.1)
      time.sleep(0.1) # allow time for thread to finish updating?
      # if the motor is connected record its settings
      print "motor types: ", self.__dict__["motorTypes"]
      if self.__dict__["motorTypes"][i] > 0:
        self.motorInit(i+1)

  # ============================================================================
  def gentle_close(self):
    """Close when command buffer is empty"""
    self.logger.info("Gentle close requested. Clearing command buffer.")
    self.logger.debug("Command buffer contains %d entries.",self.cmdFIFO.__len__())
    i=0
    while self.cmdFIFO.__len__() > 0:
      time.sleep(0.5)
      if self.state != "MV_WAIT":
        i += 1
      else:
        i += 0.1
      if i > 20:
        break
    self.handle_close()

  # ============================================================================
  def handle_close(self):
    """Close socket and wait for loop_thread to finish"""
    self.logger.info("Closing socket now.")
    self.close()
    self.logger.debug("Joining loop thread now.")
    self.loop_thread.join()

  # ============================================================================
  def collect_incoming_data(self, data):
    """Buffer data from the input stream.
    This method is necessary for the parent class.
    """
    self.ibuffer.append(data)

  # ============================================================================
  def found_terminator(self, ignoreResp=False):
    """Prepare the next command, either from the buffer or as a response to a
    previously sent command. 
    
    This method is called by the parent when it encounters the terminator
    sepcified by the set_terminator method in the incoming data stream.
    This method is necessary for the parent class.
    """
    ibufferStr = self.currentBufferString()
    self.logger.debug("terminator found, message: %s", repr(ibufferStr))
    if self.state == "MV_WAIT":
      self.logger.debug(
          "Response: %s\n",
          repr(self.currentBufferString())
      )
    else:
      self.logger.info(
          "Response: %s\n",
          repr(self.currentBufferString())
      )

    # normal operation, added ignore response since if the buffer was empty it
    # will attempt the reprocess the empty response
    if (self.state == "READY") and (not ignoreResp):
      # parse resonse from last command
      self.parseResponse( cmd=self.lastCmd, response=ibufferStr )

    # waiting for motion to stop
    elif self.state == "MV_WAIT":
      # hey are you done yet?
      nextCmd = self.lastMotorIndex + "md?" + self.get_terminator()
      time.sleep(0.1) # don't spam the port
      if (self.currentBufferString() == '1'):
        self.logger.info(
            "Motor %s: movement ceased. Continuing with command buffer.\n",
            self.lastMotorIndex
        )
        self.changeState("READY") # all done, ready for next command
      else:
        self.logger.debug(
            "Motor %s: waiting for movement to cease.",
            self.lastMotorIndex
        )

    # clear the input buffer
    self.ibuffer = []

    if self.state == "MV_WAIT":
      self.logger.debug("Sending next command(%d): %s",self.cmdID, repr(nextCmd))
    else:
      # get the next command from the buffer
      (valid, nextCmd) = self.cmdFIFO.pop()
      if not valid:
        self.logger.debug("Command buffer is now empty.")
        self.changeState("EMPTY")
        #raise EmptyBuffer
        return 0
      self.cmdID += 1
      self.lastCmd = nextCmd
      self.logger.info("Sending next command(%d): %s",self.cmdID,repr(nextCmd))

    self.push( nextCmd )

    # if the command does not expect a response, then send the next command
    if nextCmd[-1 - len(self.get_terminator()) ] != "?":
      # check if a move command was sent
      if self.moveCmdQ( nextCmd ):
        self.logger.debug("Definite movement command sent, waiting until movement completed")
        self.changeState("MV_WAIT") # all done, ready for next command
      else:
        self.logger.debug("No response expected, sending next command in buffer")
      # pretend we recieved a response
      self.found_terminator()
    else:
      self.logger.debug("Query sent, response expected")

  # ============================================================================
  def currentBufferString(self):
    """Return the character array in the input buffer as a string."""
    return "".join(self.ibuffer)

  # ============================================================================
  def currentCmdID(self):
    """Return the command ID last sent to controller."""
    return self.cmdID

  # ============================================================================
  def cmdFinishedQ(self, cmdID):
    """Return true if the command corresponding to cmdID has been completed, and
    the reponse (if necessary) processed.
    """
    if (self.cmdID > cmdID):
      self.logger.debug("command id has been passed")
      return True
    # TODO: fix condition for this 
    if ((self.cmdID == cmdID) and self.state in ["READY", "EMPTY"]):
      self.logger.debug("command id has been executed and the buffer is empty")
      return True
    return False

  # ============================================================================
  def currentBuffer(self):
    """Return the character array in the input buffer."""
    return self.ibuffer

  # ============================================================================
  def queueCommand(self, command):
    """Push command onto the command stack and append the specified terminator.
    Specify if command should block the main loop.
    Return a tuple (with the length of the command stack.
    """
    self.cmdCheckQ( command )
    self.cmdFIFO.push( command + self.get_terminator() )
    self.logger.debug(
        "added %d bytes to stack",
        len(command + self.get_terminator())
    )
    self.logger.debug(
        "command buffer is now %d entries long",
        self.cmdFIFO.__len__()
    )
    
    # command ID can be used to force the main thread to block until
    # this command is finished executing
    cmdID = self.cmdCount
    self.logger.debug("Added command(%d): %s",cmdID,repr(command))
    # total number fo commands entered into the buffer
    self.cmdCount += 1

    # if queue was empty then start it again
    if (self.state == "EMPTY") and (self.cmdFIFO.__len__() == 1):
      self.logger.debug("Buffer empty restarting transmission.")
      self.changeState("READY")
      # make sure to not try to process the empty response
      self.found_terminator(ignoreResp=True)
    
    return (self.cmdFIFO.__len__(), cmdID)
  
  # ============================================================================
  # dont include indefinite mv since it will never end,
  # motor check (MC) seems to require some short movement, so add it on
  def moveCmdQ( self, cmd ):
    """Check if cmd is a definite move command. Return boolean"""
    # need to rule out IP commands which are not movements
    if "IP" in cmd.upper():
      return False
    elif ( "P" in cmd.upper() ):
      index = cmd.upper().find('P') - 1
      self.lastMotorIndex = cmd[index]
    elif ( "MC" in cmd.upper() ):
      index = cmd.upper().find('MC') - 1
      self.logger.debug("Motor check command performed. Setting last motor to 1")
      self.lastMotorIndex = '1'
    else:
      return False

    self.logger.debug("last motor addressed: %s", self.lastMotorIndex)
    return True

  # ============================================================================
  def changeState(self, state="ERROR"):
    """Check that state is valid, then update field"""
    if state in self.STATES:
      self.state = state
      self.logger.debug("State changed to %s", self.state)
    else:
      self.logger.error("Attempted state change failed. Target state not recognized: %s", state)
      self.changeState()

  # ============================================================================
  def parseResponse(self, cmd, response):
    """Parse command and update information in __dict__"""
    CMD = cmd.upper()
    if '*IDN?' in CMD:
      self.__dict__['SerNo'] = response[-5:]
      self.logger.debug(
          "Serial number for host address - %s:%s is %s",
          self.host,
          self.port,
          self.__dict__['SerNo']
      )
      m = re.search('\sv([0-9.]+)\s',response)
      self.__dict__['FirmwareVer'] = m.group(1)
      self.logger.debug(
          "Serial number for host address - %s:%s is %s",
          self.host,
          self.port,
          self.__dict__['FirmwareVer']
      )
    elif 'AC?' in CMD:
      motor = int( CMD[ CMD.find('AC') -1 ] )
      self.__dict__['accelerations'][motor-1] = int(response)
    elif 'VA?' in CMD:
      motor = int( CMD[ CMD.find('VA') -1 ] )
      self.__dict__['velocities'][motor-1] = int(response)
    elif ('PA?' in CMD):
      motor = int( CMD[ CMD.find('PA') -1 ] )
      self.__dict__['positions'][motor-1] = int(response)
    elif ('PR?' in CMD):
      motor = int( CMD[ CMD.find('PR') -1 ] )
      self.__dict__['positions'][motor-1] = int(response)
    elif ('TP?' in CMD):
      motor = int( CMD[ CMD.find('TP') -1 ] )
      self.__dict__['positions'][motor-1] = int(response)
    elif ('QM?' in CMD):
      motor = int( CMD[ CMD.find('QM') -1 ] )
      self.__dict__['motorTypes'][motor-1] = int(response)

  # ============================================================================
  def motorInit(self, motor):
    """Queue commands to retrieve relevant parameters from motor"""
    m = str(motor)
    self.logger.info('Motor %s: type %s', m, self.__dict__["motorTypes"][motor-1])
    self.queueCommand(m+'ac?')
    self.queueCommand(m+'va?')
    self.queueCommand(m+'tp?')

  # ============================================================================
  def cmdCheckQ(self, cmd):
    return 0
    self.getMotor(cmd)
    msgstr = """Motor is not registered. If the status hasi changed, then you 
            may want to run a motor check (nnMC) command, followed by a motor
            type query (nnQM?). The motor types are listed as (0 means no
            motor):\n{0}\
            """.format(self.__dict__["motorTypes"])
    self.logger.error(msgstr)
    raise MotorReferenceError(msgstr)

# ==============================================================================
class MotorReferenceError(Exception): pass
  

# ==============================================================================
# ==============================================================================
# ==============================================================================
# testing module
# ==============================================================================
# ==============================================================================
# ==============================================================================

if __name__ == "__main__":
  host = '128.104.160.151'
  port = 23
  #TIMEOUT = 1

  # create a logger
  logger = logging.getLogger(__name__)
  logger.setLevel(logging.DEBUG)
  # create a file handler for the logger
  fh = logging.FileHandler('NP8742_test.log')
  fh.setLevel(logging.DEBUG)
  # create a console handler for the logger
  ch = logging.StreamHandler()
  ch.setLevel(logging.INFO)
  # create format for log file
  fformatter = logging.Formatter('%(asctime)s - %(name)s - %(threadName)s : %(thread)s - %(levelname)s - %(funcName)s - %(message)s')
  cformatter = logging.Formatter('%(name)s - %(threadName)s - %(levelname)s - %(message)s')
  fh.setFormatter(fformatter)
  ch.setFormatter(cformatter)
  # add the handlers to the logger
  logger.addHandler(fh)
  logger.addHandler(ch)

  try:
    np = NP8742_TCP(host,port,logger=logger)
  except Exception as e:
    print "There was a problem: %s" % e
  else:
    np.queueCommand('1tp?')
    np.queueCommand("1pr1000")
    np.queueCommand('1tp?')
    np.queueCommand("1pr-100")
    np.queueCommand('1tp?')

    np.gentle_close()

    np.connect(softStart=True)

    np.queueCommand('2tp?')
    np.queueCommand("2pr-1000")
    np.queueCommand('2tp?')
    np.queueCommand("2pr-100")
    np.queueCommand('2tp?')

    np.gentle_close()
