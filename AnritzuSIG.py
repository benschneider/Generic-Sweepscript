# -*- coding: utf-8 -*-
"""
Created on Tue Apr 12 20:13:10 2016

@author: Ben

MG3692C Signal Generator 
Driver
"""


import visa
import numpy as np
rm = visa.ResourceManager()
#from struct import unpack #, pack
#from time import sleep
#from parsers import savemtx, make_header, ask_overwrite

class instrument():
    '''
    SIG = instrument('GPIB0::17::INSTR')
    w write
    r read
    a ask
    '''
    
    def __init__(self, adress='GPIB0::17::INSTR', name='SIG', 
                 start=0, stop=0, pt=1, sstep=1e-3, stime=1e-3):
        self._adress = adress
        self._visainstrument = rm.open_resource(adress)
        self.r = self._visainstrument.read
        self.a = self._visainstrument.ask
        self.w = self._visainstrument.write
        self.name = name
        self.start = start
        self.stop = stop
        self.pt = pt
        self.lin = np.linspace(self.start,self.stop,self.pt)
        self.sstep = sstep
        self.stime = stime
        self.output = self.get_power()
        self.phaseOffset = self.get_phaseOffset()

    def get_freq(self):
        '''Return in Hz'''
        # return eval(self.a('OM1')*1e3)
        return eval(self.a('OF1'))*1e3

    def set_freq(self, freq):
        '''Set in Hz'''
        return self.w('F1 '+str(freq)+' Hz')

    def set_pulse(self, bstate):
        '''0 off, 1 on'''
        if bool(bstate) is True:
            return self.w('IP')
            
        return self.w('P0')

    def set_pulse_period(self, period):
        ''' in mu sec'''
        return self.w('PER '+str(period)+' US')
        
    def get_pulse_period(self):
        return self.a('OPR')

    def set_pulse_width(self, period):
        ''' in mu sec'''
        return self.w('W1 '+str(period)+' US')

    def get_pulse_width(self):
        return self.a('OW1')

    def set_pulse_delay(self, period):
        ''' in mu sec'''
        return self.w('D1 '+str(period)+' US')

    def get_pulse_delay(self, period):
        return self.a('OD1')

    def set_power(self, power):
        self.pow = power
        return self.w('L1 '+str(power)+' DMCLOCF1')

    def get_power(self):
        return eval(self.a('OL1'))

    def set_power_mode(self, state):
        ''' 1 LIN (mV), 0 LOG (dBm)'''
        if bool(state) is False:
            print 'Power in dBm'
            return self.w('LOG')
        
        print 'Power in mV'
        return self.w('LIN')

    def set_ALC(self, bstate):
        ''' ON - OFF 1, 0 '''
        self.ALC = bstate
        return self.w('SL'+str(bstate))
             
    def set_PCS(self, boolval=1):
        ''' Use power correction (req table)'''
        self.w(':CORR:STAT '+str(boolval))
        self.PCS = boolval

    def set_output(self, boolval=0):
        self.output = boolval
        return self.w('RF '+str(boolval))

    def get_output(self):
        ''' command not found yet '''
        return self.output

    def set_phaseOffset(self, phaseOffs):
        '''Phase Offset in Degrees'''
        self.phaseOffset = phaseOffs
        return self.w('PS1 PSO '+str(phaseOffs)+' DG') 
        
    def get_phaseOffset(self):
        return self.a('OPO')