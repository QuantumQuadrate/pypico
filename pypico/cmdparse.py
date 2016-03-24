errormsg = 'Command "{}" is not defined. \n select from [{}]'
errormsg_numeric = 'Cound not parse numeric imput: "{}"'

def Error(string):
  return ("Error : " + string)

# Might format return string in later versions
def return_string(string):
  return string

# splits a string with number and unit into float and string tuple
def parse_numeric(arg):
  # search for first non-numeric charater (after whitespace)
  s = arg.strip()
  i=0
  for c in s:
    if c.isalpha():
      break
    i+=1
  return (float(s[:i]),s[i:])

# splits off current command level, then follows command switch to next level
def nextCMD( current_cmd, cmd_switch, args ):
  try:
    (cmd,rest) = args.split(':',1) # split off only the first cmd
  except ValueError:  # error on no delimiter found
    # check if there is a numerical value (space deliminated)
    splt = args.split(' ',1)
    cmd = splt[0]
    rest = ''
    if len(splt) == 2:
      rest = splt[1]
    
  # if the command is invalid, return a list of valid commands
  if cmd not in cmd_switch:
    cmds = []
    for key in cmd_switch:
        cmds.append(':'.join([current_cmd,str(key)]))
    return Error(errormsg.format(cmd, ','.join(cmds)))

  # if the command is valid, continue to the next level
  return cmd_switch[cmd](rest)

################################################################################
### START
################################################################################
# starting lcoation for all commands
def parsecmd(args):
  #Function switch to map commands to functions
  cmd_switch = {
    #'SENSE': sense,
    #'SEND' : send,
    #'TRIG' : trig,
    #'FETCH': fetch,
    'READ' : read,
    #'MEAS' : meas,
    'MOVE' : move,
  }
  #Check if command exists
  return nextCMD('', cmd_switch, args)

################################################################################
### START - READ
################################################################################
#Switch for all read commands
def read(args):
  cmd_switch = {
    'MOT0' : read_mot_0,
    'MOT1' : read_mot_1,
    'MOT2' : read_mot_2,
    'MOT3' : read_mot_3,
  }
  #Check if command exists
  return nextCMD('READ', cmd_switch, args)

def read_mot_0(args):
  return read_mot(0,args)

def read_mot_1(args):
  return read_mot(1,args)

def read_mot_2(args):
  return read_mot(2,args)

def read_mot_3(args):
  return read_mot(3,args)

#Wrapper around motor driver library####################
def read_mot(chan, args):
  #degrees = motor_driver.read_mot(chan)
  degrees = [273,12.23,-34,4000.23][chan]
  return return_string(str(degrees))

################################################################################
### START - MOVE
################################################################################
#Swtich for all move commands
def move(args):
  cmd_switch = {
    'REL': rel_move,
    'ABS': abs_move,
  }
  return nextCMD('MOVE', cmd_switch, args)

################################################################################
### START - MOVE - RELATIVE MOVE
################################################################################
# move relative to current position
def rel_move(args):
  cmd_switch = {
    'MOT0' : rel_mv_0,
    'MOT1' : rel_mv_1,
    'MOT2' : rel_mv_2,
    'MOT3' : rel_mv_3,
  }
  return nextCMD('REL', cmd_switch, args)

def rel_mv_0(args):
  return rel_mv(0,args)

def rel_mv_1(args):
  return rel_mv(1,args)

def rel_mv_2(args):
  return rel_mv(2,args)

def rel_mv_3(args):
  return rel_mv(3,args)

#Wrapper around motor driver library####################
def rel_mv(chan, args):
  # parse movement numbers
  try:
    (number, unit) = parse_numeric(args)
  except ValueError:
    return Error(errormsg_numeric.format(args))
    
  degrees = [273,12.23,-34,4000.23][chan]
  #act_degrees = motor_driver.rel_move(chan,number,unit)
  return return_string(' '.join([str(number),unit]))

################################################################################
### START - MOVE - ABSOLUTE MOVE
################################################################################
# move relative to current position
def abs_move(args):
  cmd_switch = {
    'MOT0' : abs_mv_0,
    'MOT1' : abs_mv_1,
    'MOT2' : abs_mv_2,
    'MOT3' : abs_mv_3,
  }
  return nextCMD('ABS', cmd_switch, args)

def abs_mv_0(args):
  return abs_mv(0,args)

def abs_mv_1(args):
  return abs_mv(1,args)

def abs_mv_2(args):
  return abs_mv(2,args)

def abs_mv_3(args):
  return abs_mv(3,args)

#Wrapper around motor driver library####################
def abs_mv(chan, args):
  # parse movement numbers
  try:
    (number, unit) = parse_numeric(args)
  except ValueError:
    return Error(errormsg_numeric.format(args))
    
  degrees = [273,12.23,-34,4000.23][chan]
  #act_degrees = motor_driver.abs_move(chan,number,unit)
  return return_string(' '.join([str(number),unit]))
