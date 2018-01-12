import serial
from serial.tools.list_ports import comports as list_ports
from serial.serialutil import SerialException
from time import sleep
import threading
from Document import *

def listDevices():
    ret=[]
    for p in list_ports():
        ret.append(p.device)
    return ret

class Device:
    def __init__(self, port):
        self.progress=0.0
        self.pause=False
        self.stop=False
        self.running=False
        try:
            self.ser = serial.Serial(port, baudrate=115200)
            self.connected = True
        except serial.serialutil.SerialException:
            self.connected = False

    def startPlot(self, g, callback):
        t=threading.Thread( target = self.plot, args = (g, callback, ) )
        t.start()

    def plot(self, g, callback):
        self.progress=0.0
        self.pause=False
        self.stop=False
        self.running=True
        num=0
        self.ser.flushInput()
        for i in range(0,len(g)):
            if self.stop:
                self.command(gCodeMove(160,0,100, 1000))
                self.running=False
                callback()
                return
            if self.pause:
                cmd='G0'+g[max(i-1,0)][2:]
                self.command(cmd)
                while self.pause and not self.stop:
                    sleep(0.5)
            out = self.command(g[i])
            if(out[3:6]=='E22'):
                print('Position is unreachable:\n'+g[i].decode())
                print('Aborting...')
                out = self.command(gCodeMove(160,0,100, 1000))
                self.running=False
                callback()
                return
            num=num+1
            self.progress = float(num)/float(len(g))*100.0
        self.running=False
        self.stop=True
        callback()

    def isConnected(self):
        return self.connected

    def disconnect(self):
        self.ser.close()
        self.connected = False

    def engage(self):
        return self.command('M17')

    def disengage(self):
        return self.command('M2019')

    def getDeviceName(self):
        out = self.command('P2201')
        return out[3:]

    def getHWVersion(self):
        out = self.command('P2202')
        return out[3:]

    def getSWVersion(self):
        out = self.command('P2203')
        return out[3:]

    def getAPIVersion(self):
        out = self.command('P2204')
        return out[3:]

    def getMode(self):
        out = self.command('P2400')
        return int(out.decode()[4:5])

    def setMode(self, mode=1):
        if mode>=0 and mode<=3:
            self.command('M2400 S%d'%mode)
        else:
            print('Invalid mode '+str(mode))

    def command(self, cmd):
        self.ser.flushInput()
        self.ser.write((cmd+'\n').encode())
        return self.ser.readline().decode().strip()

    def setServo(self, val):
        if val>=0 and val<=180:
            return self.command('G2202 N3 V%0.2f'%val)


