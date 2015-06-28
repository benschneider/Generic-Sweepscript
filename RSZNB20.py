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
from parsers import savemtx, make_header, ask_overwrite

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

    def __init__(self, adress,name = 'ZNB20',start = 0, stop = 0, pt = 1):
        self._adress = adress
        self._visainstrument = visa.instrument(self._adress)
        self.name = name
        self._tempdata = self.get_data()
        self.pt = self._tempdata.shape[0]   
        self.sweeptime = self.get_sweeptime()+0.1
        self.start = start
        self.stop = stop
        self.lin = np.linspace(self.start,self.stop,self.pt)
        
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
    def get_error(self):
        return self.a('SYST:ERR:ALL?')
    def get_sweeptime(self):
        return eval(self.a('SWE:TIME?'))
    def get_freq(self):
        return eval(self.a('FREQ?'))
    def set_freq_cw(self,value):
        self.w('FREQ:CW '+str(value))

    def get_data(self):
        ''' involves some error handling
        if an error occures it returns 'Error'
        '''
        try:
            sData = self.a(':FORM REAL,32;CALC:DATA? SDATA') #grab data from VNA
        except:
            print 'Waiting for VNA'
            sleep (3) #poss. asked to early for data (for now just sleep 10 sec)
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
        
    def get_data2(self):
        vnadata = self.get_data() # np.array(real+ i* imag)
        if vnadata == 'Error':
            sleep(0.03)
            vnadata = self.get_data2()
            print 'retake VNA Data'
        return vnadata

    def prepare_data_save(self, folder, filen_0, dim_1, dim_2, dim_3):
        self._folder = folder
        self._filen_1 = filen_0 + '_real'  + '.mtx'
        self._filen_2 = filen_0 + '_imag'  + '.mtx'
        self._filen_3 = filen_0 + '_mag'   + '.mtx'
        self._filen_4 = filen_0 + '_phase' + '.mtx'
        self._head_1 = make_header(dim_1, dim_2, dim_3, 'S21 _real')
        self._head_2 = make_header(dim_1, dim_2, dim_3, 'S21 _imag')
        self._head_3 = make_header(dim_1, dim_2, dim_3, 'S21 _mag')
        self._head_4 = make_header(dim_1, dim_2, dim_3, 'S21 _phase')
        self._matrix3d_1 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_2 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_3 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
        self._matrix3d_4 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
                
    def record_data(self,vnadata,kk,jj,ii=1):
        self._phase_data = np.angle(vnadata)        
        if vnadata.shape[0] == 1:
            self._matrix3d_1[kk,jj,ii] = vnadata.real
            self._matrix3d_2[kk,jj,ii] = vnadata.imag
            self._matrix3d_3[kk,jj,ii] = np.absolute(vnadata)
            self._matrix3d_4[kk,jj,ii] = self._phase_data
        else:
            self._matrix3d_1[kk,jj] = vnadata.real
            self._matrix3d_2[kk,jj] = vnadata.imag
            self._matrix3d_3[kk,jj] = np.absolute(vnadata)
            self._matrix3d_4[kk,jj] = np.unwrap(self._phase_data)
        
    def save_data(self):
        savemtx(self._folder + self._filen_1, self._matrix3d_1, header = self._head_1)
        savemtx(self._folder + self._filen_2, self._matrix3d_2, header = self._head_2)
        savemtx(self._folder + self._filen_3, self._matrix3d_3, header = self._head_3)
        savemtx(self._folder + self._filen_4, self._matrix3d_4, header = self._head_4)
                
    def ask_overwrite(self):
        ask_overwrite(self._folder+self._filen_1)
