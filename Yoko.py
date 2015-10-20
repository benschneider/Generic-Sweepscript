'''
Python driver for:
Yokogawa 7651
Voltage / Current source

23/06/2015
- B
'''

#import numpy as np
import visa
from time import sleep
import numpy as np
import sys
from ramp_mod import ramp

class instrument():
    '''
    yoko = instrument2('GPIB0::10::INSTR')
    w write
    r read
    a ask
    '''

    def __init__(self, adress, name = 'Yokogawa IV source', start = 0, stop = 0, pt = 1, sstep = 1e-3, stime = 1e-3):
        self._adress = adress
        self._visainstrument = visa.instrument(self._adress)
        self.v = 0
        self.name = name
        self.start = start
        self.stop = stop
        self.pt = pt
        self.lin = np.linspace(self.start,self.stop,self.pt)
        self.sstep = sstep
        self.stime = stime
        if self.pt > 1 :
            self.linstep = np.abs(self.lin[1]-self.lin[0])
        self.sweep_par = 'v'


    def w(self,write_cmd):
        self._visainstrument.write(write_cmd)

    def r(self):
        return self._visainstrument.read()

    def a(self,ask_cmd):
        return self._visainstrument.ask(ask_cmd)

    def set_mode(self,option):
        ''' option = 
        1 -- Voltage mode,
        5 -- Current mode
        '''
        self.w('F' + str(option) + ' E')

    def set_vrange(self, vrange):
        ''' vrange =
        2 -- 10mV,
        3 -- 100mV,
        4 -- 1V,
        5 -- 10V,
        6 -- 30V
        '''
        self.w('R' + str(vrange) + ' E')
        
        # catch error before it arrives at the Instrument
        if vrange == 2:
            if np.abs(self.start) > 12e-3:
                return sys.exit("Start value < -12mV. Abort")
            elif np.abs(self.stop) > 12e-3:
                return sys.exit("Stop value > 12mV. Abort")
            else:
                print ('Voltage range set to 10mV')
        elif vrange == 3:
            if np.abs(self.start) > 120e-3:
                return sys.exit("Start value < -120mV. Abort")
            elif np.abs(self.stop) > 120e-3:
                return sys.exit("Stop value > 120mV. Abort")
            else:
                print ('Voltage range set to 100mV')

    def output(self, boolean):
        ''' boolean =
        1 -- ON,
        0 -- OFF
        '''
        self.w('O' + str(boolean) + ' E')

    def sweep_v(self, value, sweeptime):
        '''
        value, sweeptime
        '''
        self.w('M1 PI'+str(sweeptime)+' SW'+str(sweeptime)+' PRS S'+str(value)+' PRE RU2')
        
    def set_v(self, value):
        self.w('S'+str(value)+' E')
        self.v = value
    
    def get_v(self):
        eval(self.a('H0 OD'))
        self.v = eval(self.a('H0 OD'))
        return self.v

    def set_v2(self, value):
        if self.linstep < self.sstep:
            self.set_v(value) #set value immideatly without check
        else:
            ramp(self, self.sweep_par, value, self.sstep, self.stime)
        
    def prepare_v(self, vrange=3):
        self.set_mode(1)
        self.set_vrange(vrange) 
        self.sweep_v(0.0,4)
        sleep(4.1)
        self.output(1)
        sleep(0.2)
