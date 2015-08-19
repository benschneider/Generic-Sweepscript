import numpy as np
from time import sleep #,time

def ramp(instrument,parameter,value,step, wait):
    '''
    instrument -- actual variable where instrument is stored
    parameter -- (string) parameter to be ramped. Must have get and set.
    value -- final value
    step -- step size
    wait -- wait time per step
    '''
    v_start = getattr(instrument,'get_%s' % parameter)()
    
    if value > v_start:
        step = abs(step)
    else:
        step =- abs(step)

    if 2*abs(step) > abs(value - v_start):
        getattr(instrument,'set_%s' % parameter)(value)

    else:
        print str(instrument.name)+' '+str(np.arange(v_start,value,step))
        for v in np.arange(v_start,value,step):
            getattr(instrument,'set_%s' % parameter)(v)
            sleep(wait)
            
        getattr(instrument,'set_%s' % parameter)(value)