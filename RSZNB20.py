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
from struct import unpack, pack
import visa

class instrument1():
    '''
    vna = instrument1('TCPIP::169.254.107.192::INSTR')
    w write
    r read
    a ask
    '''

    def __init__(self, adress):
        self._adress = adress
        self._visainstrument = visa.instrument(self._adress)

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

    def get_data(self):
        sData = self.a(':FORM REAL,32;CALC:DATA? SDATA') #grab data from VNA
        i0 = sData.find('#')
        nDig = int(sData[i0+1])
        nByte = int(sData[i0+2:i0+2+nDig])
        nData = nByte/4
        nPts = nData/2
        data32 = sData[(i0+2+nDig):(i0+2+nDig+nByte)]
        vData = unpack('!'+str(nData)+'f', data32)
        vData = np.array(vData)
        # data is in I0,Q0,I1,Q1,I2,Q2,.. format, convert to complex
        mC = vData.reshape((nPts,2))
        vComplex = mC[:,0] + 1j*mC[:,1]
        return vComplex
