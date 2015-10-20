import numpy as np
from time import sleep #, time

def ramp(instrument,parameter,value,step, wait):
    '''
    instrument -- actual variable where instrument is stored
    parameter -- (string) parameter to be ramped. Must have get and set.
    value -- final value
    step -- step size
    wait -- wait time per step
    '''
    get_v = getattr(instrument,'get_%s' % parameter)
    set_v = getattr(instrument,'set_%s' % parameter)
    
    v_start = get_v()
    
    if value > v_start:
        step = abs(step)
    else:
        step =- abs(step)

    if 2*abs(step) > abs(value - v_start):
        set_v(value)

    else:
        print str(instrument.name)+' '+str(np.arange(v_start,value,step))
        for v in np.arange(v_start,value,step):
            # tt00 = time()
            set_v(v)
            if wait > 0.0:
                sleep(wait)
            # print time() - tt00
            
        set_v(value)