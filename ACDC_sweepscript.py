'''
Generic Sweep script
(currently setup for no more than 3 dims)

22/06/2015
- B
'''

#how to update functions of a module when loading from console ? ??? or tell Python to recompile its files :
import ramp_mod, parsers, RSZNB20, Yoko, dummydriver
reload(RSZNB20)
reload(Yoko)
reload(parsers)
reload(ramp_mod)
reload(dummydriver)
del ramp_mod, parsers, RSZNB20, Yoko, dummydriver

import numpy as np
from time import time, sleep
from inspect import currentframe, getfile #
thisfile = getfile(currentframe())
from parsers import savemtx, ask_overwrite, copy_file, make_header
from ramp_mod import ramp

filen_0 = 'S1_148'
folder = 'data\\'

### MEASURING SHAPIRO-STEPS ###

#Drivers
from RSZNB20 import instrument as znb20
from keithley2000 import instrument as key2000
from Yoko import instrument as yoko
from dummydriver import instrument as ddriver
#Data aquisition instruments
vna = znb20('TCPIP::169.254.107.192::INSTR')
vm = key2000('GPIB0::29::INSTR')

#Sweep instruments
dim_1 = yoko('GPIB0::13::INSTR',
           name = 'Yoko V R=14.8KOhm',
           start = -100e-3, 
           stop = 100e-3, 
           pt = 2001 ) #'Yoko V' 
dim_1.prepare_v(vrange = 3)  # vrange =2 -- 10mV, 3 -- 100mV, 4 -- 1V, 5 -- 10V, 6 -- 30V
def sweep_dim_1(dim_1,value):
     ramp(dim_1, 'v', value, 0.0001, 0.001)

dim_2 = yoko('GPIB0::10::INSTR',
            name = 'Magnet V R=2.19KOhm',
            start = -0.5, 
            stop = 0.5, 
            pt = 201) #'Yoko M' 
dim_2.prepare_v(vrange = 4)
def sweep_dim_2(dim_2,value):
     ramp(dim_2, 'v', value, 0.01, 0.01)


dim_3 = ddriver(name = 'RF-Power',
                start = -30,
                stop = -30,
                pt = 1) #VNA POWER sweep
#dim_3.set_power = vna.set_power
def sweep_dim_3(dim_3,value):
     pass
          
vm.prepare_data_save(folder, filen_0, dim_1, dim_2, dim_3)
vm.ask_overwrite()

copy_file(thisfile, filen_0, folder) #backup this script
print 'Executing sweep'
print 'req time (h):'+str(dim_3.pt*dim_2.pt*dim_1.pt*0.03/3600)
t0 = time()
try:
    #1Vsource 2Magnet 3Nothing
    for kk in range(dim_3.pt): 
        sweep_dim_3(dim_3,dim_3.lin[kk])

        sweep_dim_2(dim_2,dim_2.start)
        for jj in range(dim_2.pt):
            sweep_dim_2(dim_2,dim_2.lin[jj])
            
            sweep_dim_1(dim_1,dim_1.start)
            for ii in range(dim_1.pt):
                if dim_1.pt > 300:
                    dim_1.set_v(dim_1.lin[ii]) #sets value imediately (Dangerous!)
                else:
                    sweep_dim_1(dim_1,dim_1.lin[ii]) #slower but safer sweep
                vdata = vm.get_val()
                vm.record_data(vdata,kk,jj,ii)
                        
            vm.save_data()            
            t1 = time()
            remaining_time = ((t1-t0)/(jj+1)*dim_2.pt*dim_3.pt - (t1-t0))
            print 'req time (h):'+str(remaining_time/3600)

finally:
    print 'Finish measurements'
    print 'Time used :' +str(time()-t0)
    print 'Yokos -> zero and switch off'
    dim_1.sweep_v(0, 5)
    dim_3.sweep_v(0, 5)
    sleep(5.2)
    dim_1.output(0) #Yoko Off
    dim_3.output(0)
    