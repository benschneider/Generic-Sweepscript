'''
Python driver for:
SRS
Voltage / Current source

23/06/2015
- B
'''

# from time import time, sleep
# import sys
# from ramp_mod import ramp

import visa
import numpy as np
rm = visa.ResourceManager()

class instrument():
    '''
    srssim = instrument('GPIB0::12::INSTR')
    w write
    r read
    a ask
    '''


    def __init__(self, adress='GPIB0::12::INSTR', name='SIM 900', port=2,
                 start = 0, stop = 0, pt = 1,
                 sstep = 1e-3, stime = 1e-3):
        '''
        Establish connection, create shorthand for read,r, write,w and ask, a
        store sweep parameters here
        '''
        self.port = 2
        self._visainstrument = rm.open_resource(adress)
        self.a = self._visainstrument.ask
        self.r = self._visainstrument.read
        self.w = self._visainstrument.write
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
        self.sweep_par = 'v'
    
    def _get_key(self, port):
        return str(port)+'xY'+str(port)+'z'
    
    def conn(self, port):
        self._port = port
        key = self._get_key(port)
        return self.w("CONN "+str(port)+", '"+ key +"'")
        
    def dconn(self):
        key = self._get_key(self._port)
        return self.w(key)

    def get_volt(self):
        return float(self.a('VOLT?'))
        
    def set_volt(self, value):
        self.w('VOLT '+str(value))
        
    def get_idn(self):
        print self.a('*IDN?')

    def rest(self):
        return self.w('*RST')
        
    def set_output(self, boolval=False):
        '''
        Set output on/off True/False
        '''
        if boolval:
            return self.w('OPON')
        else:
            return self.w('OPOF')
            
    def get_batts(self):
        ''' returns the battery state'''
        return self.a('BATS?')
        
    def set_cbatt(self):
        ''' switches the Battery '''
        return self.w('BCOR')