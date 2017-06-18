import zmq
import sys
import argparse

motorLimit = 4

#===================================================

parser = argparse.ArgumentParser(description='Sends movement command to picomotor controller sever.')
parser.add_argument('-m','--motor', type=int, required=True,
                   help='specify the motor number on the controller')
parser.add_argument('-d','--deg', type=float, default=None,
                   help='specify the target position in degrees')
parser.add_argument('-s','--step', type=float, default=None,
                   help='specify the target position in steps')
parser.add_argument('-t','--test', default=False, action='store_true',
                  help='use localhost for testing')

args = parser.parse_args()

if (args.motor < motorLimit) and (args.motor >= 0):
    motor = int(args.motor)
    if (args.deg is not None) and (args.step is None):
        position = args.deg
        unit = 'DEG'
    elif (args.deg is None) and (args.step is not None):
        position = args.step
        unit = 'STEP'
    else:
        print "invlaid combination of commands"
        parser.print_help()
        sys.exit(0)
else:
    print("motor out of range: [0,%d]" % (motorLimit-1))
    parser.print_help()
    sys.exit(0)

#===================================================
def readPositions():
  print "STARTING READ POSITION CMD TEST"
  test_request = "READ:MOT"
  noError = True
  i=0
  while i<motorLimit:
    socket.send(test_request+str(i))
    message = socket.recv()
    if message[:len(errorStr)] == errorStr:
      noError = False
      print "Received error: [{}]".format( message )
    else:
      print "Received reply: [{}]".format( message )
    i+=1

def moveToAbs(m, pos, unit):
  print "STARTING ABSOLUTE MOVEMENT CMD TEST"
  test_request = "MOVE:ABS:MOT"
  movement = ' '+str(position)+unit
  print "Attempting ABS movement to:{}".format(movement)
  socket.send(test_request+str(motor)+movement)
  message = socket.recv()
  if message[:len(errorStr)] == errorStr:
    print "Received error: [{}]".format( message )
  else:
    print "Received reply: [{}]".format( message )

#===================================================

if args.test:
    print "running in test mode, connecting to localhost."
    ip="127.0.0.1"
else:
    ip="127.0.0.1"
port = 5000
errorStr = "Error : "

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://%s:%s" % (ip, port) )

readPositions()

print "args: [%d,%d,%s]" % (motor, position, unit)
moveToAbs(motor, position, unit)

readPositions()

socket.close()
