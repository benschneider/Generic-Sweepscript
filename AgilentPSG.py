'''
Python driver for:
Agilent Technologies
E8257D
PSG Analog Signal Generator
250kHz - 20Ghz

17/07/2015
- B
'''

import visa
import numpy as np
#from struct import unpack #, pack
#from time import sleep
#from parsers import savemtx, make_header, ask_overwrite

class instrument():
    '''
    PSG = instrument('GPIB0::11::INSTR')
    w write
    r read
    a ask
    '''
    
    def __init__(self, adress,name = 'PSG',start = 0, stop = 0, pt = 1, sstep = 1e-3, stime = 1e-3):
        self._adress = adress
        self._visainstrument = visa.instrument(self._adress)
        self.name = name
        self.start = start
        self.stop = stop
        self.pt = pt
        self.lin = np.linspace(self.start,self.stop,self.pt)
        self.powUnit = self.a(':UNIT:POW?')
        self.ALC = self.a(':POW:ALC?')
        #self.output = self.get_power()
        #self.phaseOffset = self.get_phaseOffset()
        self.sstep = sstep
        self.stime = stime


    def w(self,write_cmd):
        self._visainstrument.write(write_cmd)

    def r(self):
        return self._visainstrument.read()

    def a(self,ask_cmd):
        return self._visainstrument.ask(ask_cmd)

    def get_freq(self):
        return eval(self.a('FREQ?'))

    def set_freq(self, freq):
        return self.w(':SOUR:FREQ '+str(freq))

    def set_powUnit(self, value = 'DBM'):
        ''' value DBM or V'''
        self.w(':UNIT:POW '+ str(value))
        self.powUnit = value

    def set_power(self, power):
        self.w(':SOUR:POW:IMM:AMPL '+ str(power) + str(self.powUnit))
        self.pow = power

    def get_power(self): 
        return eval(self.a(':SOUR:POW:IMM:AMPL?'))
             
    def set_ALC(self,boolval = 1):
        ''' ALC : Automatic levelling control'''
        self.w(':POW:ALC '+str(boolval))
        self.ALC = boolval

    def set_output(self,boolval = 0):
        self.w(':OUTP ' +str(boolval))
        self.output = boolval

    def set_phaseOffset(self,phaseOffs = 0):
        phaseOffs = np.deg2rad(phaseOffs)
        self.w(':SOUR:PHAS:ADJ ' +str(phaseOffs))
        self.phaseOffset = phaseOffs
    def get_phaseOffset(self,phaseOffs = 0):
        return eval(self.a(':SOUR:PHAS:ADJ?'))