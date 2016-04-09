import zmq
import random

ip="169.254.5.101"
port = 5000

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://%s:%s" % (ip, port) )

errorStr = "Error : "
motor=0
position=100

# test read commands
print "STARTING READ POSITION CMD TEST"
test_request = "READ:MOT"
noError = True
i=0
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
print "STARTING ABSOLUTE MOVEMENT CMD TEST"
test_request = "MOVE:ABS:MOT"
movement = ' '+str(position)+'DEG'
print "Attempting ABS movement to:{}".format(movement)
socket.send(test_request+str(motor)+movement)
message = socket.recv()
if message[:len(errorStr)] == errorStr:
  print "Received error: [{}]".format( message )
else:
  print "Received reply: [{}]".format( message )
  
socket.send(test_request+str(motor))
message = socket.recv()
if message[:len(errorStr)] == errorStr:
  noError = False
  print "Received error: [{}]".format( message )
else:
  print "Received reply: [{}]".format( message )

socket.close()
