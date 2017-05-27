import zmq
import time
import logging
import sys

from motorControl import MotorControl
from cmdparse import SCPIParser

import pypico_settings

port = 5000

# setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create a file handler for the logger
fh = logging.FileHandler('motorControl.log')
fh.setLevel(logging.DEBUG)
# create a console handler for the logger
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create format for log file
fformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
cformatter = logging.Formatter('%(levelname)s - %(message)s')
fh.setFormatter(fformatter)
ch.setFormatter(cformatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

test = False
if len(sys.argv) > 1:
    if sys.argv[1] == 'test':
        import fakeMotorControl
        test = True
        logger.info('Using test motor controller')
        mc = fakeMotorControl.MotorControl(pypico_settings, logger)

if not test:
    # setup motor controller
    mc = MotorControl(pypico_settings, logger)

p = SCPIParser(mc)

# setup zmq
context = zmq.Context()
socket = context.socket(zmq.REP)
addr = "tcp://*:{}".format(port)
socket.bind(addr)
logger.info('Server listening at: {}'.format(addr))

try:
    while True:
        #  Wait for next request from client
        message = socket.recv()
        logger.info("Received request: %s", message)
        #time.sleep(1)
        return_msg = p.parsecmd(message)
        logger.info("Returning msg: %s", return_msg)
        socket.send(return_msg)
except KeyboardInterrupt:
    pass

socket.close()
context.destroy()
