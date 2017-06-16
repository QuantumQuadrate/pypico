import csv
import serial
ser = serial.Serial('/dev/tty.usbmodem1411', 115200, timeout = 1)

class ArduinoSerial():


    def START(self):
	try:
        	print ser.readline()
		return
  
	except serial.serialutil.SerialException:
		pass
		

    def READ(self, motor):
	try:
		w = open('EncoderPosition.csv', 'a')
		writer=csv.writer(w)
		
		#serial write to the arduino
		ser.write(chr(2))
		n = None
		if motor=="x":
			ser.write(chr(0))
			#Read the newest output from the Arduino
			n = ser.readline()
			if n:
				m = int(n,16)
               			if m > 0x7FFFFFFF:
                			m -= 0x100000000
				writer.writerow(['Position', m])
				return m
			else:
				return n
		elif motor=="y":
			ser.write(chr(1))
			#Read the newest output from the Arduino
			n = ser.readline()
			if n:
				m = int(n,16)
        			if m > 0x7FFFFFFF:
                			m -= 0x100000000
				return m
			else:
				return n
		else:
			#TODO: need a break here
			print "error, expecting x or y"
			return n
	except serial.serialutil.SerialException:
		#TODO: Stuff.
		pass

    def STATUS(self):
	try:
        	#get the serial number from the EEPROM of the arduino
		ser.write(chr(3))
		n = ser.readline()
		return n
	except serial.serialutil.SerialException:
		pass


