'''
Python driver for:
SRS sim 900 rack

26/03/2016
- B

SRS SIM900 rack
The SRS rack class stores the information which instrumen it is 
currently connected to.

It handles changes to the selected port one wants to talk to.
With this one communicates only to one instrument at a time.
'''

from time import sleep, time
import visa
rm = visa.ResourceManager()

class instrument():
    '''
    srssim = instrument('GPIB0::12::INSTR')
    w write
    r read
    a ask
    '''


    def __init__(self, adress='GPIB0::12::INSTR', name='SIM 900', commspeed = 0.020):
        '''
        Establish connection, create shorthand for read,r, write,w and ask, a
        store sweep parameters here
        '''
        self.slot = 2  # this keeps track which slot it is connected to
        self.adress = adress
        self._visainstrument = rm.open_resource(adress)
        self._visainstrument.read_termination = '\n'
        self._visainstrument.write_termination = '\n'
        self._visainstrument.write_raw("BRDT 'TERM LF'")
        self._ses = self._visainstrument.session
        self._t0 = time()*1.0
        self._commspeed = commspeed
        self.r = self._visainstrument.read
        self.name = name
        self.connection = False
        self.default_reset()        

    def a(self, string):
        '''Ensure no to overload the rack with commands'''
        if abs(time()*1.0-self._t0) < self._commspeed:
            sleep(0.015)
        a = self._visainstrument.ask(string)
        self._t0 = time()
        return a

    def w(self, string):
        if abs(time()*1.0-self._t0) < self._commspeed:
            sleep(0.015)
        self._t0 = time()
        return self._visainstrument.write(string)
        
    def default_reset(self):
        '''This resets the voltage sources (on slot 2,3,4) '''
        self.refresh()
        self.clearslot(2)
        self.clearslot(3)
        self.clearslot(4)

    def _get_key(self, slot):
        '''Creates a simple escape string for the connection'''
        # self.key = 'Ycy'+str(slot)+'zaZ'
        self.key = 'xyZZy'
        return self.key
    
    def _conn(self, slot):
        self.slot = slot
        self._get_key(slot)
        self.connection = True
        # self.w("CONN "+str(slot)+", '"+ self.key +"'")
        return self.w("CONN "+str(slot)+", '"+ self.key +"'")
        
        
    def _dconn(self):
        self.connection = False
        #a = self.w(self._get_key(self.slot))
        a = self._visainstrument.write_raw(self.key)        
        return a

    def set_conn(self, slot):
        ''' Activate connection to specified slot, 
        returns: True if the connection was changed, (False if not)'''
       
        if self.connection is True:
            if self.slot == slot:
                return False
            else:
                self._dconn()
                sleep(0.3)
                
        self._conn(slot)
        sleep(0.3)
        self.connection = True
        return True

    def reconnect(self, slot):
        self._visainstrument.clear()
        self._visainstrument = rm.open_resource(self.adress)
        self._visainstrument.write_termination='\n'
        print 'reconnecting'
        self.get_idn()
        self.refresh()
        self.clearslot(slot)
        sleep(0.3)
        self._conn(slot)
        sleep(2)
        self.get_idn()       
        self.slot = slot
 
    def get_idn(self):
        print self.a('*IDN?')

    def reset(self):
        return self.w('*RST')
        
    def done(self):
        return self.a('DONE?')
        
    def refresh(self):
        ''' RESET the sim and all instruments get them ready '''
        self.w('FLOQ')
        t1 = time()
        self.w('SRST')
        self.w('*RST')
        print time()-t1
        self.w('*CLS')

    def clearslot(self, slot):
        self.w('FLSI ' + str(slot))
        self.w('FLSO ' + str(slot))
        self.w('FLSH ' + str(slot))
        
        