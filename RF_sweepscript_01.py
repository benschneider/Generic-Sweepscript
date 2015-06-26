'''
Generic Sweep script
(currently setup for no more than 3 dims)

22/06/2015
- B
'''

#for storing results
#execfile('ramp_mod.py')
#execfile('parsers.py') #old method to avoid the following:

#how to update functions of a module when loading from console ? ??? or tell Python to recompile its files :
import ramp_mod, parsers, RSZNB20, Yoko, testdriver
reload(RSZNB20)
reload(Yoko)
reload(parsers)
reload(ramp_mod)
reload(testdriver)
del ramp_mod, parsers, RSZNB20, Yoko, testdriver

import numpy as np
from time import time, sleep
from inspect import currentframe, getfile #
thisfile = getfile(currentframe())
from parsers import savemtx, ask_overwrite, copy_file, make_header
from ramp_mod import ramp
import sys

filen_0 = 'S1_143'
folder = 'data\\'

### DIM 1
from Yoko import instrument as i2
dim_1b = i2('GPIB0::10::INSTR') #'Yoko M' 
dim_1b.name = 'Yoko M'
dim_1b.start = -1 
dim_1b.stop = 1

from RSZNB20 import instrument as i1
dim_1 = i1('TCPIP::169.254.107.192::INSTR')
dim_1.name = dim_1b.name #'ZNB20 S21 - Time'
dim_1.start = dim_1b.start
dim_1.stop = dim_1b.stop
vdata = dim_1.get_data()
dim_1.pt = vdata.shape[0]    
dim_1.sweeptime = dim_1.get_sweeptime()
if dim_1.sweeptime < 5:
    sys.exit("Dim_1 Sweeptime is too short")

dim_1b.time = dim_1.sweeptime #second sweep while VNA records
dim_1b.set_mode(1) #V mode
dim_1b.set_vrange(4) #2  10mV, 3  100mV, 4  1V, 5  10V, 6  30V
dim_1b.sweep_v(0.0,4) #sweep to 0 V
sleep(4.2)
dim_1b.output(1) #turn Yoko ON
sleep(1)

def sweep_dim1(dim_1,dim_1b):
    '''
    1. sweep magnet to start position
    2. sweep magnet at the same time with the VNA
    3. return VNA data
    '''
    dim_1b.sweep_v(dim_1b.start, 4)
    sleep(4.2)
    dim_1.init_sweep()
    dim_1b.sweep_v(dim_1b.stop, dim_1b.time)        
    sleep(dim_1b.time+0.5)
    vdata = dim_1.get_data() # np.array(real+ i* imag)
    return vdata

from Yoko import instrument as i3
dim_2 = i3('GPIB0::13::INSTR') #'Yoko V' 
dim_2.name = 'Yoko V 14.8KOhm' 
dim_2.start = -12e-3
dim_2.stop = 12e-3
dim_2.pt = 121

dim_2.set_mode(1)
dim_2.set_vrange(3) 
dim_2.sweep_v(0.0,4)
sleep(4.2)
dim_2.output(1)
sleep(1)

from testdriver import instrument as i4 #just a dummy driver
dim_3 = i4('Nothing') #VNA POWER sweep
dim_3.name = 'RF-CW-FREQ' 
dim_3.start = 8.35e9
dim_3.stop = 8.55e9
dim_3.pt = 21
dim_3.set_freq_cw = dim_1.set_freq_cw

'''
#Other Equipment
execfile('keithley2000.py')
vm = instrument3('GPIB0::29::INSTR')
vm.optimise()
sleep(0.1)
vm.testspeed()
'''

#for the VNA I want 4 data files for Real, Imag, MAG, Phase
filen_1 = filen_0 + '_real'  + '.mtx'
filen_2 = filen_0 + '_imag'  + '.mtx'
filen_3 = filen_0 + '_mag'   + '.mtx'
filen_4 = filen_0 + '_phase' + '.mtx'
head_1 = make_header(dim_1, dim_2, dim_3, 'S21 _real')
head_2 = make_header(dim_1, dim_2, dim_3, 'S21 _imag')
head_3 = make_header(dim_1, dim_2, dim_3, 'S21 _mag')
head_4 = make_header(dim_1, dim_2, dim_3, 'S21 _phase')
matrix3d_1 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
matrix3d_2 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
matrix3d_3 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))
matrix3d_4 = np.zeros((dim_3.pt, dim_2.pt, dim_1.pt))


ask_overwrite(folder+filen_1)
copy_file(thisfile, filen_0, folder) #backup this script

dim_1.lin = np.linspace(dim_1.start,dim_1.stop,dim_1.pt)
dim_2.lin = np.linspace(dim_2.start,dim_2.stop,dim_2.pt)
dim_3.lin = np.linspace(dim_3.start,dim_3.stop,dim_3.pt)
#execute sweep
print 'req time (m):'+str(dim_3.pt*dim_2.pt*dim_1.sweeptime/60)
t0 = time()
try:
    for kk in range(dim_3.pt): 
        ''' Do Dim 3 '''
        dim_3val = dim_3.lin[kk] 
        dim_3.set_freq_cw(dim_3val)
    
        #sleep(5.2)
        '''Do Dim 2 prep'''
        dim_2.sweep_v(dim_2.start, 4)
        sleep(4.2)
        for jj in range(dim_2.pt):
            '''Do Dim 2 '''
            dim_2val = dim_2.lin[jj] 
            dim_2.sweep_v(dim_2val, 0.1)
            
            vdata = sweep_dim1(dim_1,dim_1b) #sweep dim1 & dim_1b
            if vdata == 'Error':
                vdata = sweep_dim1(dim_1,dim_1b)
            
            phase_data = np.angle(vdata)        
            matrix3d_1[kk,jj] = vdata.real
            matrix3d_2[kk,jj] = vdata.imag
            matrix3d_3[kk,jj] = np.absolute(vdata)
            matrix3d_4[kk,jj] = np.unwrap(phase_data)
            savemtx(folder + filen_1, matrix3d_1, header = head_1)
            savemtx(folder + filen_2, matrix3d_2, header = head_2)
            savemtx(folder + filen_3, matrix3d_3, header = head_3)
            savemtx(folder + filen_4, matrix3d_4, header = head_4)
            
            t1 = time()
            remaining_time = ((t1-t0)/(jj+1)*dim_2.pt*dim_3.pt - (t1-t0))
            print 'req time (h):'+str(remaining_time/3600)

finally:
    #Finish measurements
    print 'return Yokos to zero and switch off'
    dim_1b.sweep_v(0, 5)
    dim_2.sweep_v(0, 5)
    sleep(5.2)
    dim_1b.output(0) #turn Yoko Off
    dim_2.output(0)