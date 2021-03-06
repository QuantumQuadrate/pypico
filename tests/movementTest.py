import zmq
import random

port = 5000

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:%s" % port)

errorStr = "Error : "

# test read commands
print "STARTING READ POSITION CMD TEST"
test_request = "READ:MOT"
i=0
noError = True
while noError:
  socket.send(test_request+str(i))
  message = socket.recv()
  if message[:len(errorStr)] == errorStr:
    noError = False
    print "Received error: [{}]".format( message )
  else:
    print "Received reply: [{}]".format( message )
  i+=1

# test write commands
print "STARTING RELATIVE MOVEMENT CMD TEST"
test_request = "MOVE:REL:MOT"
i=0
noError = True
while noError:
  movement = ' '+str(1000)+'STEP'
  print "Attempting REL movement to:{}".format(movement)
  socket.send(test_request+str(i)+movement)
  message = socket.recv()
  if message[:len(errorStr)] == errorStr:
    noError = False
    print "Received error: [{}]".format( message )
  else:
    print "Received reply: [{}]".format( message )
  i+=1

# test write commands
print "STARTING ABSOLUTE MOVEMENT CMD TEST"
test_request = "MOVE:ABS:MOT"
i=0
noError = True
while noError:
  movement = ' '+str(0)+'DEG'
  print "Attempting ABS movement to:{}".format(movement)
  socket.send(test_request+str(i)+movement)
  message = socket.recv()
  if message[:len(errorStr)] == errorStr:
    noError = False
    print "Received error: [{}]".format( message )
  else:
    print "Received reply: [{}]".format( message )
  i+=1
