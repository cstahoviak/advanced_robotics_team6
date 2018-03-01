import serial
import time
import maestro

def mini_Protocol(usb):
    for i in range(0, 255):
        usb.write(chr(0xFF)+chr(0x00)+chr(i))
        print i
        usb.write(chr(0x90)+chr(0x00))
        print ord(usb.read())
        print ord(usb.read())
        print
        time.sleep(0.01)
    for i in range(254, -1, -1):
        usb.write(chr(0xFF)+chr(0x00)+chr(i))
        print i
        usb.write(chr(0x90)+chr(0x00))
        print ord(usb.read())
        print ord(usb.read())
        print
        time.sleep(0.01)


def compact_Protocol(usb):
    for i in range(4095,7906):
        low = int("{0:b}".format(i)[-7:], base=2)
        high = int("{0:b}".format(i)[0:-7], base=2)
        usb.write(chr(0x84)+chr(0x00)+chr(low)+chr(high))
        print i
        usb.write(chr(0x90)+chr(0x00))
        print ord(usb.read())
        print ord(usb.read())
        print
        time.sleep(0.0001)
    for i in range(7905, 4094, -1):
        low = int("{0:b}".format(i)[-7:], base=2)
        high = int("{0:b}".format(i)[0:-7], base=2)
        usb.write(chr(0x84)+chr(0x00)+chr(low)+chr(high))
        print i
        usb.write(chr(0x90)+chr(0x00))
        print ord(usb.read())
        print ord(usb.read())
        print
        time.sleep(0.0001)

if __name__ == '__main__':
    usb = serial.Serial('/dev/ttyACM0')

    mini_Protocol(usb)      # Simple, less precise protocol
    compact_Protocol(usb)   # Complex, more precise protocol

    usb.write(chr(0xA1))
    usb.write(chr(0xA2))
    usb.close()
