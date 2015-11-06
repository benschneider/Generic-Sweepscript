'''
Generic Sweep script
(currently setup for no more than 3 dims)

22/06/2015
- B
'''
from time import time, sleep
from parsers import copy_file
from ramp_mod import ramp
#from inspect import currentframe, getfile
#thisfile = getfile(currentframe())
thisfile = __file__

filen_0 = 'S1_457_BW' # 0.203120,  466.836
folder = 'data\\'

### Ib vs. Mag field (Up / Down sweeps) ###
## TEST IV CURVE AT 11.32mK ! ##
## GROUND LOOP TESTS inc VNA and Hempt ##

#Drivers
#from RSZNB20 import instrument as znb20
#from dummydriver import instrument as dummy
from AgilentPSG import instrument as APSG
from keithley2000 import instrument as key2000
from Yoko import instrument as yoko

#vna = znb20('TCPIP::169.254.107.192::INSTR')
vm = key2000('GPIB0::29::INSTR')

iBias = yoko('GPIB0::13::INSTR',
           name = 'Yoko V R=14.24KOhm',
           start = -30e-3,
           stop = 30e-3, 
           pt = 1201,
           sstep = 5e-3, #def step and step/wait-time in sec for ramping
           stime = 1e-3) 
iBias.prepare_v(vrange = 4)  # vrange =2 -- 10mV, 3 -- 100mV, 4 -- 1V, 5 -- 10V, 6 -- 30V

vMag = yoko('GPIB0::10::INSTR',
            name = 'Magnet V R=2.19KOhm',
            start = 31e-3,
            stop = 31e-3, 
            pt = 1,
            sstep = 20e-3,
            stime = 1e-3) #'Yoko M' 
vMag.prepare_v(vrange = 4)

PSG = APSG('GPIB0::11::INSTR',
           name = 'RF - Power (V)',
           start = 300e-3,
           stop = 0,
           pt = 301,
           sstep = 20e-3,
           stime = 1e-3) 

PSG.set_powUnit('V')
PSG.set_freq(10.23e9)  # 1GHz gives 2 uV steps
PSG.set_output(1)

#define what is to be swept i.e. get_v(..) /set_v(..) would be 'v'
iBias.sweep_par = 'v' 
vMag.sweep_par = 'v'
#PSG.sweep_par = 'power'

dim_1= iBias
def sweep_dim_1(obj,value):
    obj.sweep_v(value, 2)
    sleep(2.1)
    #ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)

dim_3= vMag
def sweep_dim_3(obj,value):
    #pass
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)

dim_2= PSG
def sweep_dim_2(obj,value):
    obj.set_power(value)
    return obj.get_power
    #ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)

d2range = dim_2.lin 
# Keithley data recording
vm.prepare_data_save(folder, filen_0, dim_1, dim_2, dim_3, 'Voltage (V) x1000')
vm.ask_overwrite()
copy_file(thisfile, filen_0, folder) #backup this script
print 'Executing sweep'
print 'req time (min):'+str(dim_3.pt*dim_2.pt*dim_1.pt*0.032/60)
t0 = time()
try:
    for kk in range(dim_3.pt): 
        sweep_dim_3(dim_3,dim_3.lin[kk])
        d2val = sweep_dim_2(dim_2,dim_2.start)
        for jj in range(dim_2.pt):
            d2range[jj] = sweep_dim_2(dim_2,dim_2.lin[jj])            
            
            sweep_dim_1(dim_1,dim_1.start)
            #up sweep
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
    print 'Measurement Finished'

finally:
    print 'Time used :' +str(time()-t0)
    print 'Yokos -> zero and switch off'
    iBias.sweep_v(0, 5)
    vMag.sweep_v(0, 5)
    sleep(5.2)
    iBias.output(0) #Yoko Off
    vMag.output(0)