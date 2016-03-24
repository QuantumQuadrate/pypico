import zmq
import time
import logging

import motorControl
#from cmdparse import parsecmd

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

# setup motor controller
mc = MotorControl(pypico_settings, logger)

# setup zmq
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:%s" % port)


while True:
    #  Wait for next request from client
    message = socket.recv()
    print "Received request: ", message
    time.sleep(1)
    return_msg = parsecmd(message)
    print(return_msg)
    socket.send(return_msg)
