# -*- coding: utf-8 -*-
'''
Python driver for:
SRS Sim928 Voltage source
26/03/2016
- B

This is an instrument inside an SRS SIM900 rack
This is essentially a subclass specifically to the instrument type

The SRS rack class stores the information which instrumen it is 
currently connected to.
'''

import visa
from time import time, sleep
import numpy as np
#rm = visa.ResourceManager()

class instrument():
    '''
    srssim = instrument('GPIB0::12::INSTR')
    w write
    r read
    a ask
    '''

    def __init__(self, sim900obj, name='sim928', sloti=2, 
                 start=0, stop=0, pt=1, sstep=1e-3, stime=1e-3):
        '''
        Establish connection, create shorthand for read,r, write,w and ask, a
        store sweep parameters here
        '''
        self.name = name
        self.time = time()
        self.sloti = sloti  # instrument port / slot number
        self.sim900 = sim900obj  # this is the sim900 rack
        self.a = self.sim900.a
        self.w = self.sim900.w
        self.start = start
        self.stop = stop
        self.pt = pt
        self.lin = np.linspace(self.start,self.stop,self.pt)
        self.sstep = sstep
        self.stime = stime
        if self.pt > 1 :
            self.linstep = np.abs(self.lin[1]-self.lin[0])
        self._voltage = 0.0
        self.sweep_par = 'volt'  # xx, ramper will use get_xx and set_xx 
        self.w('PSTA ON')  # status register pulse only (instead of latch)

    def get_volt(self, update=False):
        ''' check if connection flag is True
            if it isn't it creates a connection to the selected port
            then it returns the Voltage 
            it only updates from device if connection was not established
            or if the update is True
        '''
        change = self.sim900.set_conn(self.sloti)
        if update or change is True:
            sleep(0.1)
            try:
                value = self.a('VOLT?')
                try:
                    self._voltage = eval(value)
                except ValueError, e:
                    sleep(1)
                    print e + '---' + value
                    self.get_volt(True)
                
            except visa.VisaIOError:
                print 'failed'
                self.sim900.reconnect(self.sloti)
                sleep(1)
                #self._voltage = float(self.a('VOLT?'))
                self.get_volt(True)
            return self._voltage
        else:
            return self._voltage
                    
    def set_volt(self, value):
        ''' check if connection flag is True
            if it isn't it creates a connection to the selected port
            then it sets the Voltage
            time() is used to ensure enough time for the instrument
        '''
        #if (time()-self.time) < 0.03:
        #    sleep(0.02)
        change = self.sim900.set_conn(self.sloti)
        if change is True:
            sleep(0.3)
        self.w('VOLT '+str(value))
        #self.time = time()
        self._voltage = value
        
    def get_batts(self):
        ''' returns the battery state'''
        self.sim900.set_conn(self.sloti)
        return self.a('BATS?')
        
    def set_cbatt(self):
        ''' switches the Battery '''
        self.sim900.set_conn(self.sloti)
        return self.w('BCOR')        
        
    def output(self, val=0):
        '''
        Set output on/off True/False
        '''
        self.sim900.set_conn(self.sloti)
        if val is 1:
            a = self.w('OPON')
            sleep(0.02)
            return a
        else:
            a = self.w('OPOF')
            sleep(0.02)
            return a