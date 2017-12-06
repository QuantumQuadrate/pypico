import socket
import time


class ArduinoComm(object):

    def __init__(self, IpAdress, record):
        self.record = record
        self.TCP_IP = IpAdress
        self.TCP_PORT = 1000
        self.BUFFER_SIZE = 1024
        self.files = ['EncoderPositionX.dat', 'EncoderPositionY.dat']
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection = self.s.connect((self.TCP_IP, self.TCP_PORT))
        self.s.settimeout(1)
        self.channels = 2
        
    #prints "start" and verifies communication with the arduino
    def START(self):
        time.sleep(0.1)
        n = None
        socketERR = 0
        while(n == None):
            try:
                self.s.send("5\n")
                n = self.s.recv(self.BUFFER_SIZE)
                if n != None:
                    print "Arduino: {}".format(n)
            except socket.timeout:
                socketERR = socketERR + 1
                time.sleep(0.1)
                if socketERR == 20:
                    print "socket timeout"
                    raise IOError
            except socket.error:
                print "Detected remote disconnect"
                time.sleep(1)
                self.s.close()
                self.reconnect()
                pass
            
    #asks for and returns the serial number of the arduino
    def STATUS(self):
        time.sleep(0.1)
        n = None
        socketERR = 0
        while(n == None):
            try:
                #get the serial number from the EEPROM of the arduino
                self.s.send("3\n")
                n = self.s.recv(self.BUFFER_SIZE)
                if n != None:
                    return n
            except socket.timeout:
                socketERR = socketERR + 1
                time.sleep(0.1)
                if socketERR == 20:
                    print "socket timeout"
                    raise IOError
            except socket.error:
                print "Detected remote disconnect"
                time.sleep(1)
                self.s.close()
                self.reconnect()
                pass

#reads the postion of the encoder from the arduino and returns it
    def READ(self, motor):
        time.sleep(0.1)
        n = None
        socketERR = 0
        while(n == None):
            try:
                if motor >= self.channels:
                    msg = "motor channel range `[0:{}]` exceeded. `{}` requested."
                    print msg.format(self.channels-1, motor)
                    raise KeyError
                #write to the arduino
                self.s.send("2\n") #send the read command
                self.s.send((str(motor)+"\n")) # read channel position
                #Read the newest output from the Arduino
                n = self.s.recv(self.BUFFER_SIZE) #TODO newline
                if n != None:
                    if self.record:
                        with open(self.files[motor], 'w') as f:
                            f.write(str(m))
                    return n
            except socket.timeout:
                socketERR = socketERR + 1
                time.sleep(0.1)
                if socketERR == 20:
                    print "socket timeout"
                    raise IOError
            except socket.error:
                print "Detected remote disconnect"
                time.sleep(1)
                self.s.close()
                self.reconnect()
                pass                    

    #resets the encoder postion to 0        
    def RESET(self):
        time.sleep(0.1)
        n = None
        socketERR = 0
        while(n == None):
            try:
                self.s.send("4\n")
                n = self.s.recv(self.BUFFER_SIZE)
                if n != None:
                    return n
            except socket.timeout:
                socketERR = socketERR + 1
                time.sleep(0.25)
                if socketERR == 20:
                    print "socket timeout"
                    raise IOError
            except socket.error:
                print "Detected remote disconnect"
                time.sleep(1)
                self.s.close()
                self.reconnect()
                pass

    #if the socket connection is broken (in case of a socket errror) re-opens the socket
    def reconnect(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection = self.s.connect((self.TCP_IP, self.TCP_PORT))
        self.s.settimeout(1)            
