'''
Generic Sweep script
(currently setup for no more than 3 dims)

20/10/2015
- B
'''
import numpy as np
from time import time, sleep
from parsers import copy_file
from ramp_mod import ramp
from DataStorer import DataStoreSP  # , DataStore2Vec, DataStore11Vec
#from covfunc import getCovMatrix
# Drivers
from dummydriver import instrument as dummy
from keithley2000 import instrument as key2000
from AnritzuSig import instrument as AnSigGen
from SRsim import instrument as sim900c
from Sim928 import instrument as sim928c
# from Yoko import instrument as yoko
from AfDigi import instrument as AfDig  # Digitizer driver
#from nirack import nit
import gc  # Garbage memory collection
# import IQcorr
# reload(IQcorr)
from IQcorr import Process as CorrProc  # Handle Correlation measurements

# PXI-Star Trigger control
# pstar = nit()
# pstar.send_many_triggers(10)

thisfile = __file__
filen_0 = 'S1_1017'
folder = 'data\\'

sim900 = sim900c('GPIB0::12::INSTR')
vm = key2000('GPIB0::29::INSTR')

# Digitizer setup
lags = 20
BW = 1e6
lsamples = 1e4
corrAvg = 1

D1 = AfDig(adressDigi='3036D1', adressLo='3011D1', LoPosAB=0, LoRef=0,
           name='D1 Lags (sec)', cfreq=4.1e9, inputlvl=-15,
           start=(-lags / BW), stop=(lags / BW),
           pt=(lags * 2 - 1), nSample=lsamples, sampFreq=BW)

D2 = AfDig(adressDigi='3036D2', adressLo='3010D2', LoPosAB=1, LoRef=2,
           name='D2 Lags (sec)', cfreq=4.1e9, inputlvl=-15,
           start=(-lags / BW), stop=(lags / BW), pt=(lags * 2 - 1),
           nSample=lsamples, sampFreq=BW)

# Sweep equipment setup
nothing = dummy('none', name='nothing', 
                start=0, stop=1, pt=1,
                sstep=20e-3, stime=0.0)

vBias = sim928c(sim900, name='V 1Mohm', sloti=2,
                start=-0.14, stop=0.14, pt=7,
                sstep=0.030, stime=0.020)

vMag = sim928c(sim900, name='Magnet V R=2.19KOhm', sloti=3,
               start=-0.7, stop=1.0, pt=1601,
               sstep=0.010, stime=0.020)

pflux = AnSigGen('GPIB0::17::INSTR', name='none',
                 start=0.0, stop=0.1, pt=1,
                 sstep=20e-3, stime=1e-3)

sgen = None
# CorrProc controls, coordinates D1 and D2 together (also does thes calcs.)
D12 = CorrProc(D1, D2, pflux, sgen, lags, BW, lsamples, corrAvg)


pflux.set_output(0)
# pflux.set_power_mode(1)  # Linear mode in mV
# pflux.set_power(pflux.start)  # if this would be a power sweep

dim_1 = vMag
dim_2 = vBias
dim_3 = nothing
dim_1.defval = 0.0
dim_2.defval = 0.0
dim_3.defval = 0.0
dim_1.UD = False


def sweep_dim_1(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)


def sweep_dim_2(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)


def sweep_dim_3(obj, value):
    pass

# This describes how data is saved
DS = DataStoreSP(folder, filen_0, dim_1, dim_2, dim_3, 'Vx1k')
D12.create_datastore_objs(folder, filen_0, dim_1, dim_2, dim_3)

DS.ask_overwrite()
copy_file(thisfile, filen_0, folder)


# describe how data is to be stored
def record_datapoint(kk, jj, ii, back):
    vdata = vm.get_val()
    if back is True:
        return DS.record_data2(vdata, kk, jj, ii)
 
    D12.init_trigger()  # Trigger and check D1 & D2
    DS.record_data(vdata, kk, jj, ii)
    D12.full_aqc(kk, jj, ii)  # Records and calc D1 & D2


def save_recorded():
    DS.save_data()  # save Volt data
    D12.data_save()  # save Digitizer data


# go to default value and activate output
sweep_dim_1(dim_1, dim_1.defval)
sweep_dim_2(dim_2, dim_2.defval)
sweep_dim_3(dim_3, dim_3.defval)
dim_1.output(1)
dim_2.output(1)

print 'Executing sweep'
texp = (2.0*dim_3.pt*dim_2.pt*dim_1.pt*(0.032+corrAvg*lsamples/BW)/60)
# print 'req time (min):'+str(2.0*dim_3.pt*dim_2.pt*dim_1.pt*0.032/60)
print 'req time (min):' + str(texp)

t0 = time()
try:
    for kk in range(dim_3.pt):
        sweep_dim_3(dim_3, dim_3.lin[kk])
        sweep_dim_2(dim_2, dim_2.start)

        for jj in range(dim_2.pt):
            sweep_dim_2(dim_2, dim_2.lin[jj])
            sweep_dim_1(dim_1, dim_1.start)

            sleep(0.2)
            print 'Up Trace'
            for ii in range(dim_1.pt):
                sweep_dim_1(dim_1, dim_1.lin[ii])
                record_datapoint(kk, jj, ii, False)

            if dim_1.UD is True:
                sweep_dim_1(dim_1, dim_1.stop)
                sleep(0.1)
                print 'Down Trace'
                for ii in range((dim_1.pt - 1), -1, -1):
                    sweep_dim_1(dim_1, dim_1.lin[ii])
                    record_datapoint(kk, jj, ii, True)

            save_recorded()
            t1 = time()
            t_rem = ((t1 - t0) / (jj + 1) * dim_2.pt * dim_3.pt - (t1 - t0))
            print 'req time (h):' + str(t_rem / 3600)
            gc.collect()
    print 'Measurement Finished'

finally:
    print 'Time used min:' + str((time() - t0) / 60)
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
