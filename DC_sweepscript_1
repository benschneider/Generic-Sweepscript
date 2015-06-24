'''
Generic Sweep script
(currently setup for no more than 3 dims)

22/06/2015
- B
'''

#import visa
import numpy as np
from time import sleep
from time import time

#for storing results
execfile('parsers.py')
execfile('ramp_mod.py')

#Overwrites without asking!!
filen_1 = 'S1_133_voltage.mtx'

#first sweep dim:
dim_1start = -35e-3 #yokoV
dim_1stop = 35e-3
dim_1pt = 70001

dim_2start = 0.3 #yokoM
dim_2stop = 0.3
dim_2pt = 1

dim_3start = 0 # nothing
dim_3stop = 1
dim_3pt = 1

head1 = ['Units', 'V_measured x1k',
        'Yoko_Vsource', str(dim_1start), str(dim_1stop),
        'Yoko_Magnet', str(dim_2stop), str(dim_2start),
        'Nothing', str(dim_3start), str(dim_3stop),]

#driver
#execfile('RSZNB20.py')
#vna = instrument1('TCPIP::169.254.107.192::INSTR')
execfile('Yoko.py')
yokoM = instrument2('GPIB0::10::INSTR')
yokoV = instrument2('GPIB0::13::INSTR')
execfile('keithley2000.py')
vm = instrument3('GPIB0::29::INSTR')

#setup 
vm.optimise()
sleep(0.1)
vm.testspeed()

yokoM.set_mode(1) #V mode
yokoV.set_mode(1)
yokoM.set_vrange(4) #2  10mV, 3  100mV, 4  1V, 5  10V, 6  30V
yokoV.set_vrange(3) 

yokoM.sweep_v(0.0,4) #sweep to 0 V
yokoV.sweep_v(0.0,4)
sleep(4.2)

#yokoV.output(0) #turn Yoko off (for now)
#yokoM.output(0)

#Prepare for sweep
matrix3d = np.zeros((dim_3pt, dim_2pt, dim_1pt))
dim_1lin = np.linspace(dim_1start,dim_1stop,dim_1pt)
dim_2lin = np.linspace(dim_2start,dim_2stop,dim_2pt)
dim_3lin = np.linspace(dim_3start,dim_3stop,dim_3pt)
yokoV.output(1) #turn Yoko ON
yokoM.output(1)
sleep(1)

#execute sweep
print 'req est time (min):'+str(dim_3pt*dim_2pt*dim_1pt*0.03/60)
t0 = time()
for kk in range(dim_3pt):
    dim_3val = dim_3lin[kk] 
    #here sweep dim 3    
    yokoM.sweep_v(dim_2start, 5)
    sleep(5.2)
    for jj in range(dim_2pt):
        dim_2val = dim_2lin[jj]
        yokoM.sweep_v(dim_2val, 0.1)
        #prepare sweep 
        yokoV.sweep_v(dim_1start, 6)
        sleep(6.2)
        for ii in range(dim_1pt):
            dim_3val = dim_1lin[ii]
            #t0 = time()
            if dim_1pt > 600:
                yokoV.set_v(dim_3val) #sets value imediately (Dangerous!)
            else:
                ramp(yokoV, 'v', dim_3val, 0.002, 0.01) #slower but safer sweep
            #t1 = time()
            #print t1-t0
            vmdata = vm.get_val() #takes 30ms
            matrix3d[kk,jj,ii] = vmdata

        #store data into a file
        savemtx(filen_1, matrix3d, header = head1)
        t1 = time()
        remaining_time = ((t1-t0)/(jj+1)*dim_2pt - (t1-t0))
        print 'req est time (h):'+str(remaining_time/3600)

#Finish measurements
#return Yoko to zero and switch off
yokoM.sweep_v(0, 3)
yokoV.sweep_v(0, 3)
sleep(3.1)
yokoV.output(0) #turn Yoko Off
yokoM.output(0)
