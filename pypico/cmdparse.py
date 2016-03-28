
class SCPIParser():
  def __init__(self, motor_driver):
    self.errormsg = 'Command "{}" is not defined. \nSelect from [{}]'
    self.errormsg_numeric = 'Cound not parse numeric imput: "{}"'
    self.errormsg_oor = 'Motor {} is not registered in pypico_settings file.'
    self.errormsg_units = 'Unit {} is not recognized. \nSelect from [{}].'
    self.motor_driver = motor_driver
  
  def Error(self, string):
    return ("Error : " + string)
  
  # Might format return string in later versions
  def return_string(self, string):
    return string
  
  # splits a string with number and unit into float and string tuple
  def parse_numeric(self, arg):
    # search for first non-numeric charater (after whitespace)
    s = arg.strip()
    i=0
    for c in s:
      if c.isalpha():
        break
      i+=1
    return (float(s[:i]),s[i:])
  
  # splits off current command level, then follows command switch to next level
  def nextCMD(self, current_cmd, cmd_switch, args ):
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
      return self.Error(self.errormsg.format(cmd, ','.join(cmds)))
  
    # if the command is valid, continue to the next level
    return cmd_switch[cmd](rest)
  
  ################################################################################
  ### START
  ################################################################################
  # starting lcoation for all commands
  def parsecmd(self, args):
    #Function switch to map commands to functions
    cmd_switch = {
      #'SENSE': sense,
      #'SEND' : send,
      #'TRIG' : trig,
      #'FETCH': fetch,
      'READ' : self.read,
      #'MEAS' : meas,
      'MOVE' : self.move,
    }
    #Check if command exists
    return self.nextCMD('', cmd_switch, args)
  
  ################################################################################
  ### START - READ
  ################################################################################
  #Switch for all read commands
  def read(self, args):
    cmd_switch = {
      'MOT0' : self.read_mot_0,
      'MOT1' : self.read_mot_1,
      'MOT2' : self.read_mot_2,
      'MOT3' : self.read_mot_3,
    }
    #Check if command exists
    return self.nextCMD('READ', cmd_switch, args)
  
  def read_mot_0(self, args):
    return self.read_mot(0,args)
  
  def read_mot_1(self, args):
    return self.read_mot(1,args)
  
  def read_mot_2(self, args):
    return self.read_mot(2,args)
  
  def read_mot_3(self, args):
    return self.read_mot(3,args)
  
  #Wrapper around motor driver library####################
  def read_mot(self, chan, args):
    try:
      degrees = self.motor_driver.getPosition(chan)
    except IndexError:
      return self.Error(self.errormsg_oor.format(chan))
    return self.return_string(str(degrees))
  
  ################################################################################
  ### START - MOVE
  ################################################################################
  #Swtich for all move commands
  def move(self, args):
    cmd_switch = {
      'REL': self.rel_move,
      'ABS': self.abs_move,
    }
    return self.nextCMD('MOVE', cmd_switch, args)
  
  ################################################################################
  ### START - MOVE - RELATIVE MOVE
  ################################################################################
  # move relative to current position
  def rel_move(self,args):
    cmd_switch = {
      'MOT0' : self.rel_mv_0,
      'MOT1' : self.rel_mv_1,
      'MOT2' : self.rel_mv_2,
      'MOT3' : self.rel_mv_3,
    }
    return self.nextCMD('REL', cmd_switch, args)
  
  def rel_mv_0(self,args):
    return self.rel_mv(0,args)
  
  def rel_mv_1(self,args):
    return self.rel_mv(1,args)
  
  def rel_mv_2(self,args):
    return self.rel_mv(2,args)
  
  def rel_mv_3(self,args):
    return self.rel_mv(3,args)
  
  #Wrapper around motor driver library####################
  def rel_mv(self, chan, args):
    # parse movement numbers
    try:
      (number, unit) = self.parse_numeric(args)
    except ValueError:
      return self.Error(self.errormsg_numeric.format(args))
      
    try:
        if unit.upper() == "STEP":
            self.motor_driver.move_rel_steps(chan,number)
        elif (unit.upper() == "DEG") or (unit == ''):
            self.motor_driver.move_rel(chan,number)
        else:
            raise ValueError
    except IndexError:
        return self.Error(self.errormsg_oor.format(chan))
    except ValueError:
        return self.Error(self.errormsg_units.format(unit.UPPER(), "DEG,STEP"))
        

    return self.return_string(' '.join([str(number),unit]))
  
  ################################################################################
  ### START - MOVE - ABSOLUTE MOVE
  ################################################################################
  # move relative to current position
  def abs_move(self, args):
    cmd_switch = {
      'MOT0' : self.abs_mv_0,
      'MOT1' : self.abs_mv_1,
      'MOT2' : self.abs_mv_2,
      'MOT3' : self.abs_mv_3,
    }
    return self.nextCMD('ABS', cmd_switch, args)
  
  def abs_mv_0(self, args):
    return self.abs_mv(0,args)
  
  def abs_mv_1(self, args):
    return self.abs_mv(1,args)
  
  def abs_mv_2(self, args):
    return self.abs_mv(2,args)
  
  def abs_mv_3(self, args):
    return self.abs_mv(3,args)
  
  #Wrapper around motor driver library####################
  def abs_mv(self, chan, args):
    # parse movement numbers
    try:
      (number, unit) = self.parse_numeric(args)
    except ValueError:
      return self.Error(self.errormsg_numeric.format(args))
      
    try:
        if (unit.upper() == "DEG") or (unit == ''):
            self.motor_driver.move_abs(chan,number)
        else:
            raise ValueError
    except IndexError:
        return self.Error(self.errormsg_oor.format(chan))
    except ValueError:
        return self.Error(self.errormsg_units.format(unit.UPPER(), "DEG"))
        
    return self.return_string(' '.join([str(number),unit]))
