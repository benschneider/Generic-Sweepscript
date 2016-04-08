'''
Generic Sweep script
(currently setup for no more than 3 dims)

22/06/2015
- B
'''
from time import time, sleep
from parsers import copy_file
from ramp_mod import ramp
from inspect import currentframe, getfile
thisfile = getfile(currentframe())

filen_0 = 'S1_160'
folder = 'data\\'

### Sc vs. Mag field ###

#Drivers
#from RSZNB20 import instrument as znb20
from keithley2000 import instrument as key2000
from Yoko import instrument as yoko
from dummydriver import instrument as dummy
#Data aquisition instruments
#vna = znb20('TCPIP::169.254.107.192::INSTR')
vm = key2000('GPIB0::29::INSTR')

#Sweep instruments
iBias = yoko('GPIB0::13::INSTR',
           name = 'Yoko V R=14.8KOhm',
           start =-90e-3, 
           stop = 90e-3, 
           pt = 1801 ) #'Yoko V' 
iBias.prepare_v(vrange = 3)  # vrange =2 -- 10mV, 3 -- 100mV, 4 -- 1V, 5 -- 10V, 6 -- 30V

vMag = yoko('GPIB0::10::INSTR',
            name = 'Magnet V R=2.19KOhm',
            start = -0.5, 
            stop = 0.5, 
            pt = 401) #'Yoko M' 
vMag.prepare_v(vrange = 4)

dim_3 = dummy(name = 'Nothing',
                start = 0,
                stop = 0,
                pt = 1)

dim_1= iBias
dim_2= vMag
def sweep_dim_1(dim_1,value):
     ramp(dim_1, 'v', value, 0.001, 0.0001)
def sweep_dim_2(dim_3,value):
     ramp(dim_3, 'v', value, 0.01, 0.01)
def sweep_dim_3(dim_2,value):
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
                if dim_1.pt > 180:
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
    dim_2.sweep_v(0, 5)
    sleep(5.2)
    dim_1.output(0) #Yoko Off
    dim_2.output(0)
    