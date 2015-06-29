import numpy as np
import time as timemod
from time import sleep

def ramp(instrument,parameter,value,step,time):
    '''
    instrument -- actual variable where instrument is stored
    parameter -- (string) parameter to be ramped. Must have get and set.
    value -- final value
    step -- stepsize
    time -- timestep
    '''
    v_start = getattr(instrument,'get_%s' % parameter)()
    #v_start = str(instrument)+'.get_'+str(parameter)
    
    if value > v_start:
        step = abs(step)
    else:
        step =- abs(step)

    if 2*abs(step) > abs(value - v_start):
        getattr(instrument,'set_%s' % parameter)(value)

    else:
        for v in np.arange(v_start,value,step):
            getattr(instrument,'set_%s' % parameter)(v)
            sleep(time)

        getattr(instrument,'set_%s' % parameter)(value)
