'''
Python driver for:
Yokogawa 7651
Voltage / Current source

23/06/2015
- B
'''

# import numpy as np
import visa
from time import sleep
import numpy as np
import sys
from ramp_mod import ramp
rm = visa.ResourceManager()

class instrument():
    '''
    yoko = instrument('GPIB0::10::INSTR')
    yoko = instrument('RS232...')
    yoko._visainstrument.set_baud(...)

    w write
    r read
    a ask
    '''


    def __init__(self, adress, name='Yokogawa IV source',
                 start = 0, stop = 0, pt = 1,
                 sstep = 1e-3, stime = 1e-3):
        self._adress = adress
        # self._visainstrument = visa.instrument(self._adress) # 1.5
        self._visainstrument = rm.open_resource(self._adress) # new visa
        self.iv = 0
        self.name = name
        self.start = start
        self.stop = stop
        self.pt = pt
        self.lin = np.linspace(self.start,self.stop,self.pt)
        self.sstep = sstep
        self.stime = stime
        if self.pt > 1 :
            self.linstep = np.abs(self.lin[1]-self.lin[0])
        self.sweep_par = 'iv'  # xx, ramper will use get_xx and set_xx

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

    def set_ivrange(self, vrange):
        ''' vrange =
        2 -- 10mV,
        3 -- 100mV,
        4 -- 1V,
        5 -- 10V,
        6 -- 30V
        In current mode =
        4 -- 1mA,
        5 -- 10mA,
        6 -- 100mA
        '''
        self.w('R' + str(vrange) + ' E')

        # catch error before it arrives at the Instrument
        if vrange == 2:
            if np.abs(self.start) > 12e-3:
                return sys.exit("Start value < -12mV. Abort")
            elif np.abs(self.stop) > 12e-3:
                return sys.exit("Stop value > 12mV. Abort")
            else:
                print ('range set to 10mV')
        elif vrange == 3:
            if np.abs(self.start) > 120e-3:
                return sys.exit("Start value < -120mV. Abort")
            elif np.abs(self.stop) > 120e-3:
                return sys.exit("Stop value > 120mV. Abort")
            else:
                print ('range set to 100mV')

    def output(self, val):
        ''' boolean =
        1 -- ON,
        0 -- OFF
        '''
        self.w('O' + str(val) + ' E')

    def sweep_iv(self, value, sweeptime):
        '''
        value, sweeptime
        '''
        self.w('M1 PI'+str(sweeptime)
               +' SW'+str(sweeptime)
               +' PRS S'+str(value)
               +' PRE RU2')

    def set_iv(self, value):
        self.w('S'+str(value)+' E')
        self.iv = value

    def get_iv(self):
        eval(self.a('H0 OD'))
        self.iv = eval(self.a('H0 OD'))
        return self.iv

    def set_iv2(self, value):
        if self.linstep < self.sstep:
            self.set_iv(value)  # set value immideatly without check
        else:
            ramp(self, self.sweep_par, value, self.sstep, self.stime)

    def prepare_v(self, vrange=3):
        self.set_mode(1)
        self.set_ivrange(vrange)
        self.sweep_iv(0.0, 3)
        sleep(3.1)
        self.output(1)
        sleep(0.2)

    def prepare_i(self, vrange=4):
        self.set_mode(5)
        self.set_ivrange(vrange)
        self.sweep_iv(0.0, 3)
        sleep(3.1)
        self.output(1)
        sleep(0.2)
