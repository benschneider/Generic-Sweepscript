'''
Python driver for:
Yokogawa 7651
Voltage / Current source

23/06/2015
- B
'''

#import numpy as np
import visa


class instrument2():
    '''
    yoko = instrument2('GPIB0::10::INSTR')
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

    def set_mode(self,option):
        '''
        1 -- Voltage mode,
        5 -- Current mode
        '''
        self.write('F' + str(option) + ' E')

    def set_vrange(self, range):
        '''range =
        2 10mV,
        3 100mV,
        4 1V,
        5 10V,
        6 30V
        '''
        self.write('R' + str(range) + ' E')

    def output(self, boolean):
        ''' output on O1, off O0'''
        self.w('O' + str(boolean) + ' E')

    def sweep_v(self, value, sweeptime):
        '''
        value, sweeptime
        '''
        self.w('M1 PI'+str(sweeptime)+' SW'+str(sweeptime)+' PRS S'+str(value)+' PRE RU2')
