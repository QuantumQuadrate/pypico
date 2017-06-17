import serial

class ArduinoComm(object):

	def __init__(self, port, record=False):
		self.record = record
		self.files = ['EncoderPositionX.dat', 'EncoderPositionY.dat']
		self.channels = 2
		self.baudrate = 115200
		self.port = port # 'COM10'
		self.timeout = 1
		ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)

	def START(self):
		try:
			print ser.readline()
			#TODO: Check for START in buffer
			return 0

		except serial.serialutil.SerialException:
			print "There was a serial/usb error"
			return 1

	def READ(self, motor):
		try:
			#serial write to the arduino
			ser.write(chr(2)) # read command
			n = None
			if motor >= self.channels:
				#TODO: need a break here
				msg = "motor channel range `[0:{}]` exceeded. `{}` requested."
				print msg.format(self.channels-1, motor)
				raise KeyError

			ser.write(chr(channel)) # read channel position
			#Read the newest output from the Arduino
			n = ser.readline() #TODO newline
			if n:
				# TODO: implement ASCII
				m = int(n,16)
				if m > 0x7FFFFFFF:
					m -= 0x100000000
				if self.record:
					with open(self.files[channel], 'w') as f:
						f.write(str(m))
				return m
			else:
				return n

		except serial.serialutil.SerialException:
			#TODO: Stuff.
			print "There was a serial/usb error"

	def STATUS(self):
		try:
			#get the serial number from the EEPROM of the arduino
			ser.write(chr(3))
			n = ser.readline()
			return n
		except serial.serialutil.SerialException:
			print "There was a serial/usb error"
