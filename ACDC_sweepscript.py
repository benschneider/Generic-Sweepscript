'''
Generic Sweep script
(currently setup for no more than 3 dims)

22/06/2015
- B
'''
from time import time, sleep
from parsers import copy_file
from ramp_mod import ramp
# from inspect import currentframe, getfile
# thisfile = getfile(currentframe())
thisfile = __file__

filen_0 = 'S1_618' # 0.203120,  466.836
folder = 'data\\'

# Drivers
# from RSZNB20 import instrument as znb20
from dummydriver import instrument as dummy
# from AgilentPSG import instrument as APSG
from keithley2000 import instrument as key2000
from Yoko import instrument as yoko

# vna = znb20('TCPIP::169.254.107.192::INSTR')
vm = key2000('GPIB0::29::INSTR')

iBias = yoko('GPIB0::13::INSTR',
           name = 'Yoko V R=(998.83+14.24)KOhm',
           start = 6,
           stop = -6, 
           pt = 601,
           sstep = 0.1, #def max voltage steps it can take
           stime = 0.1) 
iBias.prepare_v(vrange = 5)  # vrange =2 -- 10mV, 3 -- 100mV, 4 -- 1V, 5 -- 10V, 6 -- 30V

vMag = yoko('GPIB0::10::INSTR',
            name = 'Magnet V R=2.19KOhm',
            start = -280e-3,
            stop = 360e-3, 
            pt = 321,
            sstep = 5e-3,
            stime = 1e-6) #'Yoko M' 
vMag.prepare_v(vrange = 4)

# PSG = APSG('GPIB0::11::INSTR',
PSG = dummy('GPIB0::11::INSTR',
           name = 'RF - Power (V)',
           start = 0,
           stop = 0,
           pt = 1,
           sstep = 20e-3,
           stime = 1e-3) 

# PSG.set_powUnit('V')
# PSG.set_freq(11.7e9)  # 1GHz gives 2 uV steps
# PSG.set_output(1)

#define what is to be swept i.e. get_v(..) /set_v(..) would be 'v'
iBias.sweep_par = 'v' 
vMag.sweep_par = 'v'
# PSG.sweep_par = 'power'

dim_1= iBias
def sweep_dim_1(obj,value):
    #obj.set_v2(value)
    obj.sweep_v(value, 5)
    sleep(5.1)
    #sleep(1.1)
    #ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)

dim_2= vMag
def sweep_dim_2(obj,value):
    # obj.set_v2(value)
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)

dim_3= PSG
def sweep_dim_3(obj,value):
    pass
    # obj.set_power(value)
    # ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)

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
        sweep_dim_2(dim_2,dim_2.start)
        for jj in range(dim_2.pt):
            sweep_dim_2(dim_2,dim_2.lin[jj])            
            
            sweep_dim_1(dim_1,dim_1.start)
            for ii in range(dim_1.pt):
                dim_1.set_v2(dim_1.lin[ii])
                #sweep_dim_1(dim_1,dim_1.lin[ii])
                vdata = vm.get_val()
                vm.record_data(vdata,kk,jj,ii)
                       
            vm.save_data()            
            t1 = time()
            remaining_time = ((t1-t0)/(jj+1)*dim_2.pt*dim_3.pt - (t1-t0))
            print 'req time (h):'+str(remaining_time/3600)
    print 'Measurement Finished'

except (KeyboardInterrupt):
    print '***** Keyboart Interupt *****'
    
finally:
    print 'Time used min:' +str((time()-t0)/60)
    print 'Yokos -> zero and switch off'
    iBias.sweep_v(0, 5)
    vMag.sweep_v(0, 5)
    sleep(5.2)
    iBias.output(0) #Yoko Off
    vMag.output(0)
    # PSG.set_output(0)
    print  'done'
