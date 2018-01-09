import serial
import time

class ArduinoComm(object):

	def __init__(self, port, record=False, persist=True):
		self.record = record
		self.files = ['EncoderPositionX.dat', 'EncoderPositionY.dat']
		self.channels = 2
		self.baudrate = 115200
		self.port = port # 'COM10' or 'COM11'?
		self.timeout = 1
		self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)

		self.START()
		self.checkPorts()
		if not persist:
			self.RESET()

	def START(self):
		try:
			print "Arduino: {}".format(self.ser.readline())
			#TODO: Check for START in buffer
			return 0

		except serial.serialutil.SerialException:
			print "There was a serial/usb error"
			return 1

	def READ(self, motor):
		try:
			#serial write to the arduino
			#time.sleep(0.1)
			self.ser.write(chr(2)+chr(motor)) # read command. # no wait between two commands
			n = None
			if motor >= self.channels:
				#TODO: need a break here
				msg = "motor channel range `[0:{}]` exceeded. `{}` requested."
				print msg.format(self.channels-1, motor)
				raise KeyError

			#self.ser.write(chr(motor)) # read channel position
			#Read the newest output from the Arduino
			n = self.ser.readline() #TODO newline
			if n:
				# TODO: implement ASCII
				m = int(n,16)
				if m > 0x7FFFFFFF:
					m -= 0x100000000
				if self.record:
					with open(self.files[motor], 'w') as f:
						f.write(str(m))
				return m
			else:
				return n

		except serial.serialutil.SerialException:
			#TODO: Stuff.
			print "There was a serial/usb error"
			raise IOError

	def STATUS(self):
		try:
			#get the serial number from the EEPROM of the arduino
			self.ser.write(chr(3))
			n = self.ser.readline()
			print("port: {}, serno: {}".format(self.port, n))
			return n
		except serial.serialutil.SerialException:
			print "There was a serial/usb error"

	def RESET(self):
		try:
			self.ser.write(chr(4))
			n = self.ser.readline()
			return n
		except serial.serialutil.SerialException:
			print "There was a serial/usb error"


	def checkPorts(self):
		print "hello"
		#There are two ports, we assume COM10 and COM11 for now, and each are matched to an arduino
		#These arduinos have serial numbers 1 and 2, and these are matched to each port
		#a change in ports or a failure to match the serial numbers to the ports throws an error
		#try:
			# if self.port != 'COM4' and  self.port != 'COM11':
			# 	raise ValueError("Unexpected serial port")
			# serialn = self.STATUS()
			# if self.port == 'COM4' and int(serialn) != 1:
			# 	raise ValueError("Unexpected arduino serial number in port 1")
			# if self.port == 'COM11' and int(serialn) != 2:
			# 	raise ValueError("Unexpected arduino serial number in port 2")
		#except serial.serialutil.SerialException:
		#	print "There was a serial/usb error"
