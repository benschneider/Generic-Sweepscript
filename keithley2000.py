'''
23/6/2015
-B

Keithley 2000 driver
'''


import visa


class instrument3():
    '''
    vm2000 = instrument3('GPIB0::29::INSTR')
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


    def optimise(self):
        '''prepare keithley for fast measurements ~< 50ms pp
        i.e. turn all non-essentials off
        '''
        self.w('*RST')                    #reset keithley
        self.w(':VOLT:DC:NPLC 20')        #set nplc to 20ms (50Hz) 'If you can't beat noise go with it!'
        self.w(':DISP:ENAB 0')                               #turn display off
        self.w('SENSe:FUNCtion "VOLTage:DC"') #'obvious'
        self.w(':FORM:ELEM READ')             #just getting the values nothing else.. :)
        self.w('INITiate:CONTinuous OFF;:ABORt')      #self.set_trigger_continuous(False)
        self.w('SYSTem:AZERo:STATe OFF')               #Turn autozero off for speed (will result in voltage offsets over time!!)
        self.w('SENSe:VOLTage:DC:AVERage:STATe OFF')  #Turn off filter for speed
        self.w('SENSe:VOLTage:DC:RANGe 1')          #give it a fixed range to max speed
        self.w('TRIG:DEL:AUTO OFF')                   #set triger delay to manual
        self.w('TRIG:DEL 0')                          #TRIGger:DELay to 0 sec
        self.w('TRIGger:COUNt 1')

    def read(self):
        return eval(self.a('READ?'))