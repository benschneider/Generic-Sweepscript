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

from time import sleep
import visa
rm = visa.ResourceManager()

class instrument():
    '''
    srssim = instrument('GPIB0::12::INSTR')
    w write
    r read
    a ask
    '''


    def __init__(self, adress='GPIB0::12::INSTR', name='SIM 900'):
        '''
        Establish connection, create shorthand for read,r, write,w and ask, a
        store sweep parameters here
        '''
        self.slot = 2  # this keeps track which slot it is connected to
        self._visainstrument = rm.open_resource(adress)
        self.a = self._visainstrument.ask
        self.r = self._visainstrument.read
        self.w = self._visainstrument.write
        self.name = name
        self.connection = False
        self.default_reset()        
        
    def default_reset(self):
        '''This resets the voltage sources (on slot 2,3,4) '''
        self.refresh()
        self.clearslot(2)
        self.clearslot(3)
        self.clearslot(4)

    def _get_key(self, slot):
        '''Creates a simple escape string for the connection'''
        self.key = 'xY'+str(slot)+'zZ'
    
    def _conn(self, slot):
        self.slot = slot
        self._get_key(slot)
        self.connection = True
        # print 'connect ', self.key
        return self.w("CONN "+str(slot)+", '"+ self.key +"'")
        
    def _dconn(self):
        self.connection = False
        # print 'disconnect ', self.key
        return self.w(self.key)

    def set_conn(self, slot):
        ''' Activate connection to specified slot, 
        returns: True if the connection was changed, (False if not)'''
       
        if self.connection is True:
            if self.slot == slot:
                return False
            else:
                self._dconn()
                sleep(0.5)
                
        self._conn(slot)
        sleep(0.5)
        self.connection = True
        return True
 
    def get_idn(self):
        print self.a('*IDN?')

    def reset(self):
        return self.w('*RST')
        
    def done(self):
        return self.a('DONE?')
        
    def refresh(self):
        ''' RESET the sim and all instruments get them ready '''
        self.w('FLOQ')
        self.w('SRST')
        self.w('*RST')
        self.w('*CLS')

    def clearslot(self, slot):
        self.w('FLSI ' + str(slot))
        self.w('FLSO ' + str(slot))
        self.w('FLSH ' + str(slot))
        
        