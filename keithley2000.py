'''
23/6/2015
-B

Keithley 2000 driver
'''


import visa
from time import time, sleep
from parsers import savemtx, make_header, ask_overwrite
import numpy as np

class instrument():
    '''
    vm2000 = instrument('GPIB0::29::INSTR')
    w write
    r read
    a ask
    '''

    def __init__(self, adress, name= 'Keithley 2000 Voltmeter'):
        self.name = name
        self._adress = adress
        self._visainstrument = visa.instrument(self._adress)
        self.optimise()
        sleep(0.3)
        self.testspeed()
        self.testspeed()

    def w(self,write_cmd):
        self._visainstrument.write(write_cmd)

    def r(self):
        return self._visainstrument.read()

    def a(self,ask_cmd):
        return self._visainstrument.ask(ask_cmd)


    def optimise(self):
        '''prepare keithley for fast measurements ~< 50ms pp
        i.e. turn all non-essentials off
        '''
        self.w('*RST')                    #reset keithley
        self.w(':VOLT:DC:NPLC 340')        #set nplc to 20ms (50Hz) 'If you can't beat the noise go with it!'
        self.w(':DISP:ENAB 0')                               #turn display off
        self.w('SENSe:FUNCtion "VOLTage:DC"') #'obvious'
        self.w(':FORM:ELEM READ')             #just getting the values nothing else.. :)
        self.w('INITiate:CONTinuous OFF;:ABORt')      #self.set_trigger_continuous(False)
        self.w('SYSTem:AZERo:STATe OFF')               #Turn autozero off for speed (will result in voltage offsets over time!!)
        self.w('SENSe:VOLTage:DC:AVERage:STATe OFF')  #Turn off filter for speed
        self.w('SENSe:VOLTage:DC:RANGe 10')          #give it a fixed range to max speed
        self.w('TRIG:DEL:AUTO OFF')                   #set triger delay to manual
        self.w('TRIG:DEL 0')                          #TRIGger:DELay to 0 sec
        self.w('TRIGger:COUNt 1')

    def get_val(self):
        return eval(self.a('READ?'))
    
    def testspeed(self):
        t00 = time()
        self.get_val()
        t01 = time()
        print 'less than 32ms is good, '+str(t01-t00) +'s'

#Data storage stuff
    def prepare_data_save(self, folder, filen_0, dim_1, dim_2, dim_3, colour_name):
        self._folder = folder
        self._filen_1 = filen_0 + '.mtx'
        self._head_1 = make_header(dim_1, dim_2, dim_3, colour_name)
        self._matrix3d_1 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
                
    def record_data(self,vdata,kk,jj,ii=1):
        self._matrix3d_1[kk,jj,ii] = vdata
        
    def save_data(self):
        savemtx(self._folder + self._filen_1, self._matrix3d_1, header = self._head_1)
                
    def ask_overwrite(self):
        ask_overwrite(self._folder+self._filen_1)
