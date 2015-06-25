'''
Python driver for:
Rohde & Schwartz
ZNB20
Vector Network Analyzer
100kHz - 20Ghz


22/06/2015
- B
'''

import numpy as np
from struct import unpack #, pack
from time import sleep
import visa

class instrument():
    #name = 'ZNB20'
    #start = -30e-3 
    #stop = 30e-3
    #pt = 1001 # number of points
    #power = -30 #rf power
    '''
    vna = instrument1('TCPIP::169.254.107.192::INSTR')
    w write
    r read
    a ask
    '''

    def __init__(self, adress):
        self._adress = adress
        self._visainstrument = visa.instrument(self._adress)
        self.name = 'ZNB20'
        
    def w(self,write_cmd):
        self._visainstrument.write(write_cmd)

    def r(self):
        return self._visainstrument.read()

    def a(self,ask_cmd):
        return self._visainstrument.ask(ask_cmd)

    def init_sweep(self):
        self.w(':INIT:IMM;*OPC')

    def abort(self):
        self.w(':ABOR;:INIT:CONT OFF') #abort current sweep
        self.w(':SENS:AVER:CLE') #clear prev averages
        self.w(':SENS:SWE:COUN 1') #set counts to 1

   
    def set_power(self,power):
        self.w(':SOUR:POW '+str(power))
    
    def get_power(self):
        return self.a(':SOUR:POW?')

    def get_data(self):
        try:
            sData = self.a(':FORM REAL,32;CALC:DATA? SDATA') #grab data from VNA
        except:
            print 'Waiting for VNA'
            sleep (10) #poss. asked to early for data (for now just sleep 10 sec)
            sData = self.a(':FORM REAL,32;CALC:DATA? SDATA') #try once more after 5 seconds
        i0 = sData.find('#')
        nDig = int(sData[i0+1])
        nByte = int(sData[i0+2:i0+2+nDig])
        nData = nByte/4
        nPts = nData/2
        data32 = sData[(i0+2+nDig):(i0+2+nDig+nByte)]
        #if len(data32) == nByte unpack should work
        try:
            vData = unpack('!'+str(nData)+'f', data32)
            vData = np.array(vData)
            mC = vData.reshape((nPts,2)) # data is in I0,Q0,I1,Q1,I2,Q2,.. format, convert to complex
            vComplex = mC[:,0] + 1j*mC[:,1]
        except:
            print 'problem with unpack likely bad data from VNA'
            print self.get_error()
            self.w('*CLS') #CLear Status
            return 'Error'            
        return vComplex 
            
    def get_error(self):
        return self.a('SYST:ERR:ALL?')
