'''Python Wiimote interface for Linux, OSX, and Windows.'''

# Stated life as python_driver.py
# by Reto Spoerri
# rspoerri (@) nouser.org (http://www.nouser.org)
# A Python Wii-Driver, supporting the Nunchuck for OSX
# ---
# Brutally hacked and partially rewritten by Gary Bishop July 2009

# ---
# License:
# Free to use and modify (as long as the credits/license remain) in non-commercial products.
# Contact the author if planned to use/used in a commercial project.
# ---

logging = False

import os
import sys
import time
import atexit
import socket
import array

if sys.platform == 'darwin':
    # make lightblue look like the pybluez implementation
    import Foundation
    import lightblue

    def osx_discover_devices(duration=8, flush_cache=True, lookup_names=False):
        device_list = lightblue.finddevices(lookup_names, duration)
        if lookup_names:
            return [ (address,name) for address,name,device_class in device_list ]
        else:
            return device_list

    def osx_BluetoothSocket(protocol):
        return lightblue.socket(protocol)

    class bag(object):
        pass
    bluetooth = bag()
    bluetooth.discover_devices = osx_discover_devices
    bluetooth.BluetoothSocket = osx_BluetoothSocket
    bluetooth.L2CAP = lightblue.L2CAP

    def hackSocket(socket):
        return socket


elif sys.platform == 'win32':
    import bluetooth
    import threading
    import Queue
    class hackSocket(threading.Thread):
        '''Fake up a thread to read in the background for Windows'''
        def __init__(self, socket):
            self.socket = socket
            self.queue = Queue.Queue(1)
            self.timeout = 0.001
            threading.Thread.__init__(self)
            self.setDaemon(True)
            self.running = True
            self.start()

        def run(self):
            while self.running:
                try:
                    data = self.socket.recv(1024)
                except:
                    print 'except'
                else:
                    self.queue.put(data)

        def close(self):
            self.running = False
            self.join()
            self.socket.close()

        def recv(self, len):
            return self.queue.get(True, self.timeout)

        def settimeout(t):
            self.timeout = t

    
elif sys.platform == 'linux2':
    import bluetooth
    def hackSocket(socket):
        return socket

else:
    raise NotImplementedError, 'platform not supported'

SIGNAL_RUMBLE = 0x01
SIGNAL_LED   = (0x10, 0x20, 0x40, 0x80)

# Wiimote output commands
OutputReportNone            = 0x00
OutputReportLEDs            = 0x11
OutputReportType            = 0x12
OutputReportIR              = 0x13
OutputReportSpeaker         = 0x14
OutputReportStatus          = 0x15
OutputReportWriteMemory     = 0x16
OutputReportReadMemory      = 0x17
OutputReportSpeakerData     = 0x18
OutputReportSpeakerMute     = 0x19
OutputReportIR2             = 0x1a
# Wiimote registers
REGISTER_IR                     = 0x04b00030
REGISTER_IR_SENSITIVITY_1       = 0x04b00000
REGISTER_IR_SENSITIVITY_2       = 0x04b0001a
REGISTER_IR_MODE                = 0x04b00033
REGISTER_EXTENSION_INIT         = 0x04a40040
REGISTER_EXTENSION_TYPE         = 0x04a400fe
REGISTER_EXTENSION_CALIBRATION  = 0x04a40020
# Extension Types
ExtensionTypeNone              = 0x00
ExtensionTypeNunchuk           = 0xfe
ExtensionTypeClassicController = 0xfd
# IR modes
IrModeOff                      = 0x00
IrModeBasic                    = 0x01 # 10 bytes
IrModeExtended                 = 0x03 # 12 bytes
IrModeFull                     = 0x05 # 16 bytes * 2 (format unknown)

SIGNAL_IR_SENSITIVITY = {
             # [address, data, dataLength] 
    'lvl1' : [ [REGISTER_IR_SENSITIVITY_1, 0x0200007101006400fe, 9],
               [REGISTER_IR_SENSITIVITY_2, 0xfd05, 2] ], # lvl 1
    'lvl2' : [ [REGISTER_IR_SENSITIVITY_1, 0x0200007101009600b4, 9],
               [REGISTER_IR_SENSITIVITY_2, 0xb304, 2] ], # lvl 2
    'lvl3' : [ [REGISTER_IR_SENSITIVITY_1, 0x020000710100aa0064, 9],
               [REGISTER_IR_SENSITIVITY_2, 0x6303, 2] ], # lvl 3
    'lvl4' : [ [REGISTER_IR_SENSITIVITY_1, 0x020000710100c80036, 9],
               [REGISTER_IR_SENSITIVITY_2, 0x3503, 2] ], # lvl 4
    'lvl5' : [ [REGISTER_IR_SENSITIVITY_1, 0x020000710100720020, 9],
               [REGISTER_IR_SENSITIVITY_2, 0x1f03, 2] ], # lvl 5
    'max'  : [ [0x04b00006, 0x90, 1], [0x04b00008, 0x64, 1],
               [REGISTER_IR_SENSITIVITY_2, 0x6303, 2] ], # (max sensitivity)
}

SIGNAL_IR_SENSITIVITY_SORTED_LIST = sorted(SIGNAL_IR_SENSITIVITY.keys())

class WIIMOTESTATE:
    def __init__( self ):
        self.SEND_ACCEL = False
        self.SEND_IR = False
        self.SEND_CONTINUOUS = False
        self.SEND_EXTENSION = False
        self.TRANSMISSION_ENABLED = True
        self.BATTERY = 0
        self.LED = [0, 0, 0, 0]
        self.RUMBLE = False
        self.EXTENSIONTYPE = None
        self.ExtensionClass = None
        self.KEEP_HISTORY = False
        self.IR_SENSITIVITY = 'max'

        # Accel data
        self.AccelCalibration0 = [ 0.0, 0.0, 0.0 ]
        self.AccelCalibrationG = [ 0.0, 0.0, 0.0 ]
        self.AccelRaw = [ 0.0, 0.0, 0.0 ]
        self.Accel = [ 0.0, 0.0, 0.0 ]

        # IR data
        self.IrRaw = [ [0,0] for i in range(4) ]
        self.IrFound = [ 0 ] * 4
        self.IrSize = [ 0 ] * 4
        self.Ir = [ [0.0,0.0] for i in range(4) ]

        # Button data
        self.Button = {}
        for name in [ 'A', 'B', 'Up', 'Down', 'Left', 'Right', 'Home', '-', '+', '1', '2' ]:
            self.Button[name] = False
        self.ButtonState = 0

    def getLedSignal( self ):
        #  (52) 11 XX
        signal = 0
        for i in range(4):
            if self.LED[i]:
                signal += SIGNAL_LED[i]
        if self.RUMBLE:
            signal += SIGNAL_RUMBLE
        return signal

    def getSensitivitySignals( self ):
        #if self.IR_SENSITIVITY in SIGNAL_IR_SENSITIVITY.keys():
        return SIGNAL_IR_SENSITIVITY[self.IR_SENSITIVITY]
        #else:
        #  id = SIGNAL_IR_SENSITIVITY.keys()[self.IR_SENSITIVITY]
        #  return SIGNAL_IR_SENSITIVITY[id]

    def getRumbleSignal( self ):
        signal = 0
        if self.RUMBLE: signal += SIGNAL_RUMBLE
        return signal

    def getSendSignal( self ):
        # ba       0000001
        # bx       0000010
        # bai      0000011
        # bx       0000100
        # bax      0000101

        # (52) 12 00 XX
        signal = 0x30
        if self.SEND_ACCEL:
            signal += 0x01
        if self.SEND_IR:
            signal += 0x02
        if self.SEND_EXTENSION:
            signal += 0x04
        return signal

    def getTransmissionSignal( self ):
        # (52) 13 XX
        signal = 0
        if self.SEND_CONTINUOUS:
            signal += 0x04
        if self.RUMBLE:
            signal += 0x01
        return signal

    def getIrMode( self ):
        if logging:
            print "WIIMOTESTATE.getIrMode: IR %s, ACCEL %s, EXTENSION %s" % (
                ['OFF','ON'][self.SEND_IR], ['OFF','ON'][self.SEND_ACCEL],
                ['OFF','ON'][self.SEND_EXTENSION]),
        if self.SEND_IR:
            if self.SEND_ACCEL:
                if self.SEND_EXTENSION:
                    if logging: print "basic"
                    return IrModeBasic # must be this
                else:
                    if logging: print "extended"
                    return IrModeExtended # must be this
            else:
                if logging: print "extended"
                return IrModeExtended
        else:
            if logging: print "off"
            return IrModeOff

    def __repr__debug__( self ):
        txt = "B:%2d " % self.BATTERY
        txt += "LED: 1:%s 2:%s 3:%s 4:%s " % self.LED
        txt += "R: %s EXT:%s" %  (self.RUMBLE, str(self.EXTENSIONTYPE))
        if self.SEND_ACCEL:
            txt += "AccelCalib: X0: %3d Y0: %3d Z0: %3d  " % self.AccelCalibration0
            txt += "XG: %3d YG: %3d ZG: %3d " % self.AccelCalibrationG
            txt += "AccelRaw: %4d %4d %4d" % self.AccelRaw
        if self.SEND_IR:
            txt += "IR: "
            for i in range(4):
                txt += '%d: %d %4d %4d %2d ' % (i, self.IrFound[i],
                                                self.IrRaw[i][0], self.IrRaw[i][1],
                                                self.IrSize[i])
        txt  = "Button: " + str(self.Button)
        return txt

    def __repr__( self ):
        txt = "B:%2d " % self.BATTERY
        txt += "LED: 1:%s 2:%s 3:%s 4:%s " % self.LED
        txt += "R: %s EXT:%s " %  (self.RUMBLE, str(self.EXTENSIONTYPE))
        txt += 'Button:' + str(self.Button) + ' '
        if self.SEND_ACCEL:
            txt += "Accel: %2.2f %2.2f %2.2f " % self.Accel
        if self.SEND_IR:
            txt += "Ir: "
            for i in range(4):
                txt += '%d: %d %4d %4d %2d ' % (i, self.IrFound[i],
                                                self.IrRaw[i][0], self.IrRaw[i][1],
                                                self.IrSize[i])
        return txt

    def __str__( self ):
        return self.__repr__()

class WIIMOTEDUMMYEXTENSIONSTATE:
    def __repr__( self ):
        return "WIIMOTEDUMMYEXTENSIONSTATE"

    def __str__( self ):
        return self.__repr__()

class WIIMOTENUNCHUKEXTENSIONSTATE:

    def __init__(self):
        self.AccelCalibration0 = [ 0.0, 0.0, 0.0 ]
        self.AccelCalibrationG = [ 0.0, 0.0, 0.0 ]
        self.AccelRaw = [ 0.0, 0.0, 0.0 ]
        self.Accel = [ 0.0, 0.0, 0.0 ]
        self.Button = { 'C':False, 'Z':False }
        self.JoyMax = [0.0, 0.0]
        self.JoyMin = [0.0, 0.0]
        self.JoyMid = [0.0, 0.0]
        self.JoyRaw = [0.0, 0.0]
        self.Joy = [0.0, 0.0]

    def __repr__debug__( self ):
        txt = "NUNCHUK: "
        txt += "AccelCalib: X0: %3d Y0: %3d Z0: %3d " % self.AccelCalibration0
        txt += "XG: %3d YG: %3d ZG: %3d " % self.AccelCalibrationG
        txt += "AccelRaw: %4d %4d %4d " % self.AccelRaw
        txt += "Accel: %2.2f %2.2f %2.2f " % self.Accel
        txt += 'Joy: '
        for i in range(2):
            txt += 'Axis%d %2.2f %3d %3d %3d %3d ' % (i, self.Joy[i], self.JoyRaw[i],
                                                      self.JoyMin[i], self.JoyMid[i],
                                                      self.JoyMax[i])
        return txt

    def __repr__( self ):
        txt =  "NUNCHUK: X: %3d Y: %3d Z: %3d " % self.Accel
        txt += "X: %3d Y: %3d Button: %s" % (
          self.X, self.Y, str(self.Button)
        )
        return txt

    def __str__( self ):
        return self.__repr__debug__()


# --- some functions ---
def i2bs(val):
    lst = []
    while val:
        lst.append(val&0xff)
        val = val >> 8
    lst.reverse()
    return lst

def l2hex(l):
    # pretty output of a int list (to hex list)
    return [ hex(val) for val in l ]

def popMultiple( buffer, num ):
    return list(buffer.pop(0) for i in range(num))

def decryptBuffer( buffer ):
    return [ (i^0x17) + 0x17 for i in buffer ]

# --- the parsers ---
BUTTON = { '2':     0x0001,
           '1':     0x0002,
           'B':     0x0004,
           'A':     0x0008,
           '-':     0x0010,
           'Home':  0x0080,
           'Left':  0x0100,
           'Right': 0x0200,
           'Down':  0x0400,
           'Up':    0x0800,
           '+':     0x1000,
           }

def parseIr( buffer, wiiMoteState, size ):
    signal = popMultiple( buffer, size )
    if size == 12:
        for i in range(4):
            k = i*3
            wiiMoteState.IrRaw[i] = [ signal[k+0] + ((signal[k+2] & 0x30) >> 4 << 8),
                                      signal[k+1] +  (signal[k+2]         >> 6 << 8) ]
            wiiMoteState.IrSize[i] = signal[k+2] & 0x0f
            wiiMoteState.IrFound[i] = wiiMoteState.IrRaw[i][1] != 1023

    elif size == 10:
        for i in range(2):
            j = i*2
            k = i*5
            wiiMoteState.IrRaw[j] = [ signal[k+0] + ((signal[k+2] & 0x30) >> 4 << 8),
                                      signal[k+1] + ((signal[k+2] & 0xc0) >> 6 << 8) ]
            wiiMoteState.IrSize[j] = 5
            wiiMoteState.IrFound[j] = wiiMoteState.IrRaw[j][1] != 1023

            wiiMoteState.IrRaw[j+1] = [ signal[k+3] + ((signal[k+2] & 0x03)      << 8),
                                        signal[k+4] + ((signal[k+2] & 0x0c) >> 2 << 8) ]
            wiiMoteState.IrSize[j+1] = 5
            wiiMoteState.IrFound[j+1] = wiiMoteState.IrRaw[j+1][1] != 1023

    for i in range(4):
        wiiMoteState.Ir[i] = [ wiiMoteState.IrRaw[i][0] / 1024.0,
                               wiiMoteState.IrRaw[i][1] / 768.0 ]

    return buffer

def parseAccel( buffer, wiimoteState ):
    signal = popMultiple( buffer, 3 )

    # always call after ParseButtons which got the LSB's already

    for i in range(3):
        wiimoteState.AccelRaw[i] |= signal[i] << 2

        wiimoteState.Accel[i] = round(0.25 * (wiimoteState.AccelRaw[i] -
                                              wiimoteState.AccelCalibration0[i]*4) /
                                      (wiimoteState.AccelCalibrationG[i] -
                                       wiimoteState.AccelCalibration0[i]), 2)

    return buffer

def parseButtons( buffer, wiiMoteState ):
    keybuffer = popMultiple( buffer, 2 )

    state = (keybuffer[0]<<8) + keybuffer[1]

    for name,bit in BUTTON.iteritems():
        wiiMoteState.Button[name] = (state&bit) != 0

    wiiMoteState.ButtonState = state

    wiiMoteState.AccelRaw[0] = (keybuffer[0]>>5)&0x3 # bits 6:5 are bits 1:0 of X
    wiiMoteState.AccelRaw[1] = (keybuffer[1]>>4)&0x2 # bit 5 is bit 1 of Y
    wiiMoteState.AccelRaw[2] = (keybuffer[1]>>5)&0x2 # bit 6 is bit 1 of Z

    return buffer

def parseExtension( encryptedBuffer, extensionState ):
    if extensionState.__class__ == WIIMOTENUNCHUKEXTENSIONSTATE:
        buffer = decryptBuffer(encryptedBuffer)

        extensionState.RawX = buffer[0]
        extensionState.RawY = buffer[1]
        extensionState.Button['C'] = not((buffer[5] & 0x02) >> 1)
        extensionState.Button['Z'] = not(buffer[5] & 0x01)

        for i in range(3):
            extensionState.AccelRaw[i] = buffer[2+i]
            extensionState.Accel[i] = round((float(extensionState.AccelRaw[i]) -
                                             extensionState.AccelCalibration0[i]) /
                                            (extensionState.AccelCalibrationG[i] -
                                             extensionState.AccelCalibration0[i]), 2)

        for i in range(2):
            extensionState.Joy[i]  = ((extensionState.JoyRaw[i] - extensionState.JoyMid[i]) /
                                      float(extensionState.JoyMax[i] - extensionState.JoyMin[i]))

    return encryptedBuffer

def readReport( memoryReport ):
    error = memoryReport[0] & 0x0f
    if error == 8:
        if logging: print "W: readReport: error bit set (address don't exist)"
    elif error == 7:
        if logging: print "W: readReport: error bit set (write-only registers)"
    elif error == 0:
        pass
#    print "I: readReport: error bit not set"
    else:
        if logging: print "E: readReport: error bit is invalid", error
    size = ((memoryReport[0] & 0xf0) >> 4)
#  print "I: readReport: package size", size
    packageOffset = memoryReport[1] << 8 + memoryReport[2]
    if size == 1:
        header = popMultiple( memoryReport, 2 )
    else:
        header = popMultiple( memoryReport, 3 )
    data = popMultiple( memoryReport, size )
    return data

INPUTREPORT_DATA =  { "InputReportStatus"                     : [ 0x20,  8 ]
                    , "InputReportReadData"                   : [ 0x21, 23 ]
                    , "InputReportUnknown1"                   : [ 0x22,  6 ]
                    , "InputReportButtons"                    : [ 0x30,  4 ]
                    , "InputReportButtonsAccel"               : [ 0x31,  7 ]
                    , "InputReportButtonsExtension8"          : [ 0x32, 12 ]
                    , "InputReportButtonsAccelIR12"           : [ 0x33, 19 ]
                    , "InputReportButtonsExtension19"         : [ 0x34, 23 ]
                    , "InputReportButtonsAccelExtension16"    : [ 0x35, 23 ]
                    , "InputReportButtonsIR10Extension9"      : [ 0x36, 23 ]
                    , "InputReportButtonsAccelIR10Extension6" : [ 0x37, 23 ]
                    , "InputReportButtonsAccelIR"             : [ 0x38, 23 ]
                    , "InputReportExtension21"                : [ 0x3d, 23 ]
                    , "InputReportInterleaved1"               : [ 0x3e, 23 ]
                    , "InputReportInterleaved2"               : [ 0x3f, 23 ] }

INREPORT_V2L = dict(); INREPORT_N2V = dict(); INREPORT_V2N = dict()
for n, [v, l] in INPUTREPORT_DATA.items():
    INREPORT_V2L[v] = l
    INREPORT_N2V[n] = v
    INREPORT_V2N[v] = n

def findWiimotes(duration):
    return [ addr for addr, name in bluetooth.discover_devices(duration, False, True)
             if name == 'Nintendo RVL-CNT-01' ]

class wiimoteLibClass(object):
    def __init__( self, id ):
        # storage containers for received data
        self.wiiMoteState = WIIMOTESTATE()
        self.extensionState = WIIMOTEDUMMYEXTENSIONSTATE()

        self.data = list()
        self.connected = False
        self.packageCount = 0

        self.connectToUid( id )

    def run(self):
        '''handle reading in the background so we do not miss packets'''
        while self.connected:
            try:
                data = self.isocket.recv(1024)
            except Exception, e:
                print 'recv', e
            else:
                self.read_queue.put(data)
                

    def connect(self, bd_addr):
        '''attempt to connect to the bluetooth device at bd_addr'''
        self.bd_addr = bd_addr
        
        # create the sockets
        try:
            self.isocket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
            self.osocket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        except:
            raise NotImplementedError, 'Bluetooth protocol L2CAP not supported'

        #time.sleep(0.1)

        # connect the input
        try:
            self.isocket.connect((self.bd_addr,19))
        except:
            self.isocket.close()
            self.osocket.close()
            raise socket.error, 'Cannot connect to %s input socket' % self.bd_addr

        self.isocket = hackSocket(self.isocket) # for Windows

        #time.sleep(0.1)

        try:
            self.isocket.settimeout(0.001)
        except:
            pass

        # connect the output
        try:
            self.osocket.connect((self.bd_addr,17))
        except:
            self.isocket.close()
            self.osocket.close()
            raise socket.error, 'Cannot connect to %s output socket' % self.bd_addr

        try:
            self.osocket.settimeout(10.0)
        except:
            pass
        
        self.connected = True

        # setup magic cleanup
        atexit.register(self.atExit)

        
        return True

    def atExit(self):
        try:
            self.isocket.close()
            self.osocket.close()
        except:
            pass

    def connectToUid( self, uid ):
        self.connect( uid )

        # set leds disabled (must be done just after connecting, else they blink forever)
        state = self.SetLEDs( 0, 0, 0, 0 )
        if state is False:
            raise RuntimeError, "send data test failed"

        # accept initializing package (this must be done, if a extension is already plugged in)
        for i in xrange(10):
            self.step()

        self.readCalibration()

        # set default settings (ir/accel/continuous disabled)
        self.updateIrMode()

        for i in xrange(10):
            self.step()

        else:
            state = True

    def readData( self ):
        try:
            data = self.isocket.recv(1024)
        except Exception, e:
            pass
        else:
            if data is None or len(data) == 0: # read error?
                self.SetRumble(0) # probe to see
            else:
                # convert to a list of integers
                self.data.extend(array.array('B', data).tolist())

    def sendData(self, data):
        # convert from a list of integers
        str_data = array.array('B', data).tostring()
        try:
            self.osocket.send(str_data)
        except Exception, e:
            print 'sendData', e
            self.connected = False
            self.atExit()

    def step( self ):
        self.readData()
        return self.parseData()

    def parseData( self ):
        while len(self.data)>=2:
            retVal = self.parseDataStep()
            if retVal is not None:
                return retVal
            if retVal == -1:
                return None
        return None

    def parseDataStep( self ):
        if len(self.data)>=2:
            pkgType = self.data[1]
            # check package
            try:
                if pkgType in INREPORT_V2L and len(self.data) >= INREPORT_V2L[pkgType]:
                    package = popMultiple( self.data, INREPORT_V2L[pkgType])
                else:
                    #print "W: wiimoteLibClass.parseData: invalid or unknown package", hex(pkgType), len(self.data), INREPORT_V2L.get(pkgType, None)#, self.data
                    return -1
            except:
                print "E: wiimoteLibClass.parseData: invalid data"
                #print "E: - ", self.data
                #print "E: - ", l2hex(self.data)
                raise

            self.packageCount += 1

            tmp = popMultiple( package, 2)
            if   pkgType == INREPORT_N2V['InputReportStatus']:
                package = parseButtons( package, self.wiiMoteState )
                #print "W: wiimoteLibClass.parseData: InputReportStatus, pkg", l2hex(package)

                # get the real LED values in case the values from SetLEDs() somehow becomes out of sync, which really shouldn't be possible
                for i in range(4):
                    self.wiiMoteState.LED[i] = (package[1] & SIGNAL_LED[i]) != 0
                self.wiiMoteState.BATTERY = package[3]
                extensionPluggedIn        = (package[1] & 0x02) != 0
                speakerEnabled            = (package[1] & 0x04) != 0
                continuousOutputMode      = (package[1] & 0x08) != 0
                self.initializeExtension()
            elif pkgType == INREPORT_N2V['InputReportReadData']:
                package = parseButtons( package, self.wiiMoteState )
                return package
            elif pkgType == INREPORT_N2V['InputReportButtons']:
                package = parseButtons( package, self.wiiMoteState )
            elif pkgType == INREPORT_N2V['InputReportButtonsAccel']:
                package = parseButtons( package, self.wiiMoteState )
                package = parseAccel( package, self.wiiMoteState )
            elif pkgType == INREPORT_N2V['InputReportButtonsExtension8']:
                package = parseButtons( package, self.wiiMoteState )
                package = parseExtension( package, self.extensionState )
            elif pkgType == INREPORT_N2V['InputReportButtonsAccelIR12']:
                package = parseButtons( package, self.wiiMoteState )
                package = parseAccel( package, self.wiiMoteState )
                package = parseIr( package, self.wiiMoteState, 12 )
            elif pkgType == INREPORT_N2V['InputReportButtonsExtension19']:
                package = parseButtons( package, self.wiiMoteState )
                package = parseExtension( package, self.extensionState )
            elif pkgType == INREPORT_N2V['InputReportButtonsAccelExtension16']:
                package = parseButtons( package, self.wiiMoteState )
                package = parseAccel( package, self.wiiMoteState )
                package = parseExtension( package, self.extensionState )
            elif pkgType == INREPORT_N2V['InputReportButtonsIR10Extension9']:
                package = parseButtons( package, self.wiiMoteState )
                package = parseIr( package, self.wiiMoteState, 10 )
                package = parseExtension( package, self.extensionState )
            elif pkgType == INREPORT_N2V['InputReportButtonsAccelIR10Extension6']:
                package = parseButtons( package, self.wiiMoteState )
                package = parseAccel( package, self.wiiMoteState )
                package = parseIr( package, self.wiiMoteState, 10 )
                package = parseExtension( package, self.extensionState )
            elif pkgType == INREPORT_N2V['InputReportButtonsAccelIR']:
                package = parseButtons( package, self.wiiMoteState )
                package = parseAccel( package, self.wiiMoteState )
                package = parseIr( package, self.wiiMoteState )
            elif pkgType == INREPORT_N2V['InputReportExtension21']:
                package = parseExtension( package, self.extensionState )
            elif pkgType == INREPORT_N2V['InputReportInterleaved1']:
                pass
            elif pkgType == INREPORT_N2V['InputReportInterleaved2']:
                pass
            elif pkgType == INREPORT_N2V['InputReportUnknown1']:
                pass
            else:
                print "W: wiimoteLib2: unknown package type:", hex(pkgType), l2hex(package)
        else:
            return -1

    def initializeExtension( self ):
        # initialize the extension
        self.sendData( i2bs(0x521604A400400100000000000000000000000000000000) )

        extension = self._read_from_mem(REGISTER_EXTENSION_TYPE, 2)
        if extension[0] == ExtensionTypeNunchuk:
            print "I: wiimoteLibClass.initializeExtension: found nunchuk extension controller"
            self.extensionState = WIIMOTENUNCHUKEXTENSIONSTATE()
            self.wiiMoteState.SEND_EXTENSION = True
        elif extension[0] == ExtensionTypeClassicController:
            print "I: wiimoteLibClass.initializeExtension: found classic extension controller (not handled)"
            self.extensionState = WIIMOTEDUMMYEXTENSIONSTATE()
            self.wiiMoteState.SEND_EXTENSION = True
        elif extension[0] == 0xff:
            print "I: wiimoteLibClass.initializeExtension: partially inserted"
            self.extensionState = WIIMOTEDUMMYEXTENSIONSTATE()
            self.wiiMoteState.SEND_EXTENSION = False
        else:
            print "I: wiimoteLibClass.initializeExtension: unknown or none inserted %s" % hex(extension[0])
            self.extensionState = WIIMOTEDUMMYEXTENSIONSTATE()
            self.wiiMoteState.SEND_EXTENSION = False

        extensionCalibration = decryptBuffer(self._read_from_mem(REGISTER_EXTENSION_CALIBRATION, 16))

        if self.extensionState.__class__ == WIIMOTENUNCHUKEXTENSIONSTATE:
            for i in range(3):
                self.extensionState.AccelCalibration0[i] = float(extensionCalibration[i])
                self.extensionState.AccelCalibrationG[i] = float(extensionCalibration[4+i])
            for i in range(2):
                self.extensionState.JoyMax[i] = float(extensionCalibration[8+i])
                self.extensionState.JoyMin[i] = float(extensionCalibration[9+i])
                self.extensionState.JoyMid[i] = float(extensionCalibration[10+i])

        self.updateIrMode()
        self.sendData([0x52]+i2bs(0x1200)+[self.wiiMoteState.getSendSignal()])

    def SetLEDs(self, *leds):
        for i in range(len(leds)):
            self.wiiMoteState.LED[i] = leds[i]
        return self.updateRumbleLED()

    def SetRumble(self,on):
        self.wiiMoteState.RUMBLE = on
        self.updateRumbleLED()

    def updateRumbleLED( self ):
        ledSignal = self.wiiMoteState.getLedSignal()
        return self.sendData((0x52,OutputReportLEDs,ledSignal))

    def setContinuous( self, continous = True ):
        print "I: p3f.src.wiimote.set_continuous"
        self.wiiMoteState.SEND_CONTINUOUS = continous
        #self.sendData([0x52]+i2bs(0x12)+[self.wiiMoteState.getTransmissionSignal(), self.wiiMoteState.getSendSignal()])
        #time.sleep(0.1)
        self.updateMode()

    def setAccel( self, state ):
        print "I: p3f.src.wiimote.setAccel: state %s" % (['off','on'][state])
        self.wiiMoteState.SEND_ACCEL = state
        self.updateMode()

    def activate_accel(self):
        print "I: p3f.src.wiimote.activate_accel: is depricated, use setAccel instead"
        self.setAccel( True )

    def setIr( self, state, sensitivity='max' ):
        print "I: p3f.src.wiimote.setIr: state %s sensitivity %s" % (['off','on'][state], str(sensitivity))
        if state:
            print "I: - activating accel as well, cause ir alone doesnt work"
            self.setAccel( True )
        self.wiiMoteState.SEND_IR = state
        if sensitivity not in SIGNAL_IR_SENSITIVITY:
            print "wiimoteLib2.wiimoteLibClass.setIr: INVALID SENSITIVITY", sensitivity, "must be one of", SIGNAL_IR_SENSITIVITY.keys()
            raise Exception
        self.wiiMoteState.IR_SENSITIVITY = sensitivity # 0 some state, 1 maximum sensitivity
        self.updateIrMode()

    def activate_IR(self, maxsensitivity = False ):
        print "I: p3f.src.wiimote.activate_IR:  is depricated, use setIr instead"
        if maxsensitivity:  # sensitivity must be one of SIGNAL_IR_SENSITIVITY
            sensitivity = 'max'
        else:
            sensitivity = 'lvl3'
        self.setIr( True, sensitivity )

    def updateIrMode( self ):
        self.updateMode()
        time.sleep(0.1)
        self.sendData([0x52]+i2bs(0x1304))
        time.sleep(0.1)
        self.sendData([0x52]+i2bs(0x1a04))
        time.sleep(0.1)
        self._write_to_mem(REGISTER_IR,0x08)                               # 0x04b00030
        time.sleep(0.1)

        # sensitivity
        for addr, signal, signalLength in self.wiiMoteState.getSensitivitySignals():
            self._write_to_mem(addr, signal, signalLength)
            time.sleep(0.1)

        time.sleep(0.1)
        self._write_to_mem(REGISTER_IR_MODE, self.wiiMoteState.getIrMode()) # 0x04b00033

        time.sleep(0.1)
        self.updateMode()

    def updateMode( self ):
        time.sleep(0.1)
        self.sendData([0x52]+i2bs(0x12)+[self.wiiMoteState.getTransmissionSignal(), self.wiiMoteState.getSendSignal()])

    def _get_battery_status(self):
        data = self.requestData( (0x52,0x15,0x00), 7 )
        #print len(data), data
        battery_level = (100*data[7])/206
        self.wiiMoteState.BATTERY = battery_level

        if False: # check if requestdata works correctly
            self.sendData((0x52,0x15,0x00))
            self.running2 = True
            while self.running2:
                try:
                    x= map(ord,self.isocket.recv(32))
                except lightblue.BluetoothError:
                    continue
                except socket.timeout:
                    continue
                self.state = ""
                for each in x[:17]:
                    if len(x) >= 7:
                        self.running2 = False
                        battery_level = (100*x[7])/206
            if self.wiiMoteState.BATTERY != battery_level:
                print "E: _get_battery_status: is wrong", self.wiiMoteState.BATTERY, battery_level
                raise
            else:
                print "I: _get_battery_status: is correct", self.wiiMoteState.BATTERY, battery_level
                raise

    def readCalibration( self ):
        # equivalent to wiimote.ReadCalibration
        parseData = self._read_from_mem( 0x0016, 7 )

        if len(parseData) == 6:
            for i in range(3):
                self.wiiMoteState.AccelCalibration0[i] = float(parseData[i])
                self.wiiMoteState.AccelCalibrationG[i] = float(parseData[3+i])
        else:
            print "E: wiimoteLibClass.readCalibration: invalid data", parseData

    def _write_to_mem(self, address, value, val_len=None):
#    print "I: wiimoteLibClass._write_to_mem: ", hex(address), ":", hex(value)
        val = i2bs(value)
        if val_len is None:
            # calculate value length if not defined
            val_len=len(val)
        val += [0]*(16-val_len)
        msg = [0x52,OutputReportWriteMemory] + i2bs(address) + [val_len] + val
        self.sendData(msg)

    def _read_from_mem( self, address, size ):
        ''' starts another read loop, and exits if a memory read response happens
        '''
        # equivalent to wiimote.ReadData
        adr = i2bs(address)
        adr_len = len(adr)
        adr = [0]*(4-adr_len) + adr
        siz = i2bs(size)
        siz_len = len(siz)
        siz = [0]*(2-siz_len) + siz
        sendData = [0x52, OutputReportReadMemory] + adr + siz
        self.sendData( sendData )

        running = True
        timer = time.time()
        x = 0
        while running:
            if (time.time()-timer < 1.0):
                returnData = self.step()
                if returnData is not None:
                    if len(returnData) >= size:
                        parseData = readReport( returnData )
                        return parseData
            else:
                print "E: wiimoteLibClass._read_from_mem: timeout", address, size
                return list()

    def hasNunchuck(self):
        return self.extensionState.__class__ == WIIMOTENUNCHUKEXTENSIONSTATE

    def getPressedButtons(self):
        buttons = set([ name for name,value in self.wiiMoteState.Button.iteritems() if value ])
        if self.hasNunchuck():
            buttons |= set([ name for name,value in self.extensionState.Button.items()
                             if value ])
        return buttons

        
        

def testApp():
    addresses = findWiimotes(4)
    print 'addresses = ', addresses
    if addresses:
        wiimote = wiimoteLibClass(addresses[0])
    else:
        print 'no wiimotes found'
        sys.exit(1)
        
    print "wiimote connection succeeded"

    debug = pygameDebug( wiimote )

    if True:
        #wiimote.setIr( True, 'max' )
        wiimote.setAccel(True)
        wiimote.setContinuous( True )

    if False:
        print "set rumble"
        wiimote.wiiMoteState.RUMBLE = True
        wiimote.SetLEDs( 1,0,0,0 )
        time.sleep( 0.1 )

    debug.run()

class pygameDebug:
    def __init__( self, wiimote ):
        self.wiimote = wiimote
        if not hasPygame:
            print "pygameDebug requires pygame"
            raise
        pygame.init()
        size = width, height = 256, 256
        self.screen = pygame.display.set_mode(size)
        #self.font = pygame.font.Font('freesansbold.ttf', 17)

        # calculate fps
        self.t = time.time()
        self.c = 0
        self.lastPackageCount = 0

        # rendering stuff
        self.colors = {
          'wii': [ (255,0,0), (0,255,0), (0,0,255) ],
          'nunchuck': [ (255,255,0), (255,0,255), (0,255,255) ],
        }
        self.lines = {}
        self.lines['wii'] = [ [0]*256 for i in range(3) ]
        self.lines['nunchuck'] = [ [0]*256 for i in range(3) ]

        self.activeButtons = list()

    def run( self ):
        pygame.time.set_timer(pygame.USEREVENT, 50)
        while self.wiimote.connected:
            evt = pygame.event.poll()
            if evt.type == pygame.QUIT:
                pygame.time.set_timer(pygame.USEREVENT, 0)
                break
            elif evt.type == pygame.USEREVENT:
                self.draw()
            self.step()
            self.calcFps()

    def draw(self):
            # output wiiMoteState
        self.screen.fill((0,0,0))

        # show key state
        if False:
            text = self.font.render( self.wiimote.wiiMoteState.__repr__(), True, (255, 255, 255), (159, 182, 205))
            textRect = text.get_rect()
            textRect.centerx = self.screen.get_rect().centerx
            textRect.centery = self.screen.get_rect().centery
            self.screen.blit(text, textRect)
        # show ir data
        if False:
            for x,y,r,c in points:
                pygame.draw.circle(self.screen, c, (int(x/4),int(y/4)), r, 0)

        for k,v in self.lines.items():
            prev = 128
            for i in range(3):
                for j in xrange(256):
                    p = int(v[i][j]*32+128)
                    pygame.draw.line(self.screen, self.colors[k][i], (j-1,prev),(j,p), 1 )
                    prev = p

        pygame.display.flip()
        if True:
            if True:
                t = int(time.time())
                l1 = t & 0x01
                l2 = t & 0x02
                l3 = t & 0x04
                l4 = t & 0x08
            else:
                l1, l2, l3, l4 = 0,0,0,0
            self.wiimote.SetLEDs( l1, l2, l3, l4 )


    def calcFps( self ):
        self.c += 1
        if time.time() - self.t > 1.0:
            dt = time.time() - self.t
            print "fps", self.c/dt
            self.t = time.time()
            self.c = 0
            print "packages received", self.wiimote.packageCount - self.lastPackageCount
            self.lastPackageCount = self.wiimote.packageCount

    def step( self ):

        CONSOLE_OUTPUT = False

        self.wiimote.step()

        if self.wiimote.wiiMoteState.Button['A']:
            print self.wiimote.wiiMoteState

        # edit sensitivity
        if True:
            currentSetting = self.wiimote.wiiMoteState.IR_SENSITIVITY
            currentSettingNumber = SIGNAL_IR_SENSITIVITY_SORTED_LIST.index( currentSetting )
            maxLen = len(SIGNAL_IR_SENSITIVITY_SORTED_LIST)
            #print "EDIT SENSITIVITY", currentSetting, currentSettingNumber, maxLen
            # increase sensitivity
            if self.wiimote.wiiMoteState.Button['+']:
                if '+' not in self.activeButtons:
                # do it here
                    self.wiimote.setIr( True, SIGNAL_IR_SENSITIVITY_SORTED_LIST[ min(maxLen-1, max(currentSettingNumber+1, 0) ) ] )
                    self.activeButtons.append( "+" )
            else:
                if "+" in self.activeButtons:
                    self.activeButtons.remove( "+" )

            # decrease sensitivity
            if self.wiimote.wiiMoteState.Button['-']:
                if '-' not in self.activeButtons:
                    # do it here
                    self.wiimote.setIr( True, SIGNAL_IR_SENSITIVITY_SORTED_LIST[ min(maxLen-1, max(currentSettingNumber-1, 0) ) ] )
                    self.activeButtons.append( "-" )
            else:
                if "-" in self.activeButtons:
                    self.activeButtons.remove( "-" )

        if True:
            l1, l2, l3, l4 = 0,0,0,0

            if False:
                print self.wiimote.wiiMoteState

            wiimote = self.wiimote

            points = list()
            for i in range(4):
                if wiimote.wiiMoteState.IrFound[i]:
                    points.append( wiimote.wiiMoteState.IrRaw[i] +
                                   [ wiimote.wiiMoteState.IrSize[i], (255,0,0) ])

            for i in range(3):
                self.lines['wii'][i].append(wiimote.wiiMoteState.Accel[i])
                self.lines['wii'][i].pop(0)

            if CONSOLE_OUTPUT:
                print "wiimote.wiiMoteState", wiimote.wiiMoteState

            if wiimote.extensionState.__class__ == WIIMOTENUNCHUKEXTENSIONSTATE:
                for i in range(3):
                    self.lines['nunchuck'][i].append(wiimote.extensionState.Accel[i])
                    self.lines['nunchuck'][i].pop(0)

                if CONSOLE_OUTPUT:
                    print "wiimote.extensionState", wiimote.extensionState


if __name__ == "__main__":
    usePygame = True
    if usePygame:
        hasPygame = False
        try:
            pass
            import pygame
            hasPygame = True
        except:
            print "testing app requires pygame (for visual debug ouput)"
            usePygame = False

    if usePygame:
        testApp(  )
    else:
        #wiimote = wiimoteLibClass( '00:1C:BE:36:24:AD' )
        wiimote = wiimoteLibClass( '00:19:1D:CE:29:1A' )
        print >>sys.stderr, 'wiimote connect succeeded'
        wiimote.setAccel(True)
        wiimote.setContinuous( True )

        N = 4000
        wstart = time.time()
        pstart = time.clock()
        for i in xrange(N):
            wiimote.step()

        pend = time.clock()
        wend = time.time()

        ptime = pend - pstart
        wtime = wend - wstart

        print '%d steps, %.1f wall time, %.1f processor time, %.1f%% load, %.2g per step' % (
            N, wtime, ptime, 100*ptime/wtime, ptime/N)
