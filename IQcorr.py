'''
This file containts the procedures for cross correlations using 2 Aeroflex 
Digitizers, a signal source and 

31/03/2016
- B
'''

class Proc1():

    def __init__(self, D1, D2, pgen, sgen, pstar):
        '''
        D1, D2, pgen, pstar
        D1,2: Digitizer 1,2 object
        pgen: Flux Pump (Anritzu pulsed mode)
        sgen: Signal Generator
        pstar: Trigger source (PXI-Star)
        '''
        # Make some object references
        self.D1 = D1
        self.D2 = D2
        self.D1w = D1.Digitizer
        self.D2w = D2.Digitizer
        self.sgen = sgen
        self.pgen = pgen
        self.pstar = pstar
        
    def setup_D1D2(self):
        '''
        Trigger on PXI-Star
        Enable pipelining
        '''
        self.D1w.trigger_source_set(8)
        self.D2w.trigger_source_set(8)
        self.D1w.set_piplining(1)
        self.D2w.set_piplining(1)

    
    def get_data(self, samples):
        ''' 
        2. Arm Trigger
        - Send PXI trigger
        3. TriggerDetected_Get - Check if trigger arrived
        4. CaptMem
        
        '''
        self.D1w.trigger_arm_set(samples)
        self.D2w.trigger_arm_set(samples)
        self.D1w.trigger_detected_get()
        
    
    def get_cov_matrix(self):
        pass
    
    def get_g2(self):
        pass
