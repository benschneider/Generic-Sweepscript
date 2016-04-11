'''
Generic Sweep script
(currently setup for no more than 3 dims)

20/10/2015
- B
'''
from time import time, sleep
from parsers import copy_file
from ramp_mod import ramp
from DataStorer import DataStoreSP
# Drivers
from dummydriver import instrument as dummy
from keithley2000 import instrument as key2000
from SRsim import instrument as sim900c
from Sim928 import instrument as sim928c
# from Yoko import instrument as yoko
# from AfDigi import instrument as AfDig  # Digitizer driver
from nirack import nit
import gc  # Garbage memory collection 

pstar = nit()

thisfile = __file__
filen_0 = 'S1_1015'
folder = 'data\\'

sim900 = sim900c('GPIB0::12::INSTR')
vm = key2000('GPIB0::29::INSTR')

# Digitizer setup
#lags = 20
#BW = 1e5
#lsamples= 1e6
#D1 = AfDig(adressDigi='3036D1', adressLo='3011D1', LoPosAB=0, LoRef=0, 
#           name='D1 Lags (sec)', cfreq = 4.1e9, inputlvl = -15, 
#           start=(-lags/BW), stop=(lags/BW), 
#           pt=(lags*2-1), nSample=lsamples, sampFreq=BW)
#
#D2 = AfDig(adressDigi='3036D2', adressLo='3010D2', LoPosAB=1, LoRef=2,
#           name='D2 Lags (sec)', cfreq = 4.8e9, inputlvl = -15,
#           start=(-lags/BW), stop=(lags/BW), pt=(lags*2-1),
#           nSample=lsamples, sampFreq=BW)


# Sweep equipment setup
vBias = sim928c(sim900, name='V 1Mohm', sloti=2,
                start=-6.5, stop=6.5, pt=1301,
                sstep=0.050, stime=0.010)

vMag = sim928c(sim900, name='Magnet V R=2.19KOhm', sloti=3,
               start=-0.2, stop=0.5, pt=701,
               sstep=0.010, stime=0.010)

PSG = dummy('GPIB0::11::INSTR', name='none',
            start=0.0, stop=1.0, pt=1,
            sstep=20e-3, stime=1e-3)

dim_1 = vBias
dim_1.UD = True
dim_1.defval = 0.0
dim_2 = vMag
dim_2.defval = 0.0
dim_3 = PSG
dim_3.defval = 0.0


def sweep_dim_1(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)


def sweep_dim_2(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)


def sweep_dim_3(obj, value):
    pass

DS = DataStoreSP(folder, filen_0, dim_1, dim_2, dim_3, 'Vx2k')
DS.ask_overwrite()
copy_file(thisfile, filen_0, folder)

# go to default value and activate output
sweep_dim_1(dim_1, dim_1.defval)
sweep_dim_2(dim_2, dim_2.defval)
sweep_dim_3(dim_3, dim_3.defval)
dim_1.output(1)
dim_2.output(1)

print 'Executing sweep'
print 'req time (min):'+str(2.0*dim_3.pt*dim_2.pt*dim_1.pt*0.032/60)
t0 = time()
try:
    for kk in range(dim_3.pt):
        sweep_dim_3(dim_3, dim_3.lin[kk])
        sweep_dim_2(dim_2, dim_2.start)
    
        for jj in range(dim_2.pt):
            sweep_dim_2(dim_2, dim_2.lin[jj])
            sweep_dim_1(dim_1, dim_1.start)
            sleep(0.2)
            if dim_1.UD is True:
                print 'Up Trace'
                for ii in range(dim_1.pt):
                    sweep_dim_1(dim_1, dim_1.lin[ii])
                    vdata = vm.get_val()
                    DS.record_data(vdata, kk, jj, ii)
    
                sweep_dim_1(dim_1, dim_1.stop)
                sleep(0.1)
                print 'Down Trace'
                for ii in range((dim_1.pt-1), -1, -1):
                    sweep_dim_1(dim_1, dim_1.lin[ii])
                    vdata = vm.get_val()
                    DS.record_data2(vdata, kk, jj, ii)
            else:
                for ii in range(dim_1.pt):
                    sweep_dim_1(dim_1, dim_1.lin[ii])
                    vdata = vm.get_val()
                    DS.record_data(vdata, kk, jj, ii)
    
            DS.save_data()
            t1 = time()
            remaining_time = ((t1-t0)/(jj+1)*dim_2.pt*dim_3.pt - (t1-t0))
            print 'req time (h):'+str(remaining_time/3600)
            gc.collect()
    print 'Measurement Finished'

except (KeyboardInterrupt):
    print '***** Keyboart Interupt *****'

finally:
    print 'Time used min:' + str((time()-t0)/60)
    print 'Sweep back to default'
    sweep_dim_1(dim_1, dim_1.defval)
    sleep(1)
    sweep_dim_2(dim_2, dim_2.defval)
    sleep(1)
    sweep_dim_3(dim_3, dim_3.defval)
    sleep(1)
    dim_1.output(0)
    sleep(1)
    dim_2.output(0)
    sim900._dconn()
    gc.collect()
    print 'done'
