import zmq
import time
from cmdparse import *

port = 5000

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
