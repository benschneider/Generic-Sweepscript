'''
Generic Sweep script
(currently setup for no more than 3 dims)

20/10/2015
- B
'''
# import numpy as np
from time import time, sleep
from parsers import copy_file
from ramp_mod import ramp
from DataStorer import DataStoreSP  # , DataStore2Vec, DataStore11Vec
# Drivers
from dummydriver import instrument as dummy
from keithley2000 import instrument as key2000
from AnritzuSig import instrument as AnSigGen
from SRsim import instrument as sim900c
from Sim928 import instrument as sim928c
# from Yoko import instrument as yoko
from AfDigi import instrument as AfDig  # Digitizer driver
import gc  # Garbage memory collection
from IQcorr import Process as CorrProc  # Handle Correlation measurements
import sys
import os
# import logging


thisfile = __file__
filen_0 = '3010'
folder = 'data_Dec04\\'
if not os.path.exists(folder):
    os.makedirs(folder)

sim900 = sim900c('GPIB0::12::INSTR')
vm = key2000('GPIB0::29::INSTR')

# Digitizer setup
lags = 200
BW = 1e5
lsamples = 1e6
corrAvg = 1
f1 = 4.45e9
f2 = 4.45e9
fd = f1+f2

D1 = AfDig(adressDigi='PXI7::13::INSTR', adressLo='PXI7::14::INSTR', LoPosAB=1, LoRef=3,
           name='D1 Lags (sec)', cfreq=f1, inputlvl=-10,
           start=(-lags / BW), stop=(lags / BW), pt=(lags * 2 + 1),
           nSample=lsamples, sampFreq=BW)

D2 = AfDig(adressDigi='PXI8::14::INSTR', adressLo='PXI8::15::INSTR', LoPosAB=0, LoRef=0,
           name='D2 Lags (sec)', cfreq=f2, inputlvl=-10,
           start=(-lags / BW), stop=(lags / BW), pt=(lags * 2 + 1),
           nSample=lsamples, sampFreq=BW)

dummyD1D2 = dummy('none', name='nothing', start=4.4e9, stop=4.5e9, pt=1, sstep=6e9, stime=0.0)

vBias = sim928c(sim900, name='V 1Mohm', sloti=4,
                start=-20.0, stop=20.0, pt=101,
                sstep=0.200, stime=0.020)

vMag = sim928c(sim900, name='Magnet V R=22.19KOhm', sloti=3,
               start=-2.50, stop=-2.50, pt=1,
               sstep=0.03, stime=0.020)

pFlux = AnSigGen('GPIB0::17::INSTR', name='FluxPump',
                 start=0.03, stop=0.03, pt=1,
                 sstep=30e-3, stime=1e-3)

nothing = dummy('none', name='nothing',
                start=0, stop=1, pt=1,
                sstep=20e-3, stime=0.0)

dummyD1D2.setup_digitizers(D1, D2)
dummyD1D2.sweep_par = 'f11'

sgen = None

pFlux.set_power_mode(1)  # Linear mode in mV
pFlux.set_freq(fd)
pFlux.sweep_par = 'power'  # Power sweep
pFlux.output(0)  # Power OFF (0)/ On (1)
# -20 dB at output

dim_1 = vBias
dim_1.defval = 0.0
dim_3 = vMag
dim_3.defval = 0.0
dim_2 = nothing
dim_2.defval = 0.0
dim_1.UD = False
recordD12 = True  # activates /deactivates all D1 D2 data storage
D12 = CorrProc(D1, D2, pFlux, sgen, lags, BW, lsamples, corrAvg)
D12.doHist2d = False
D12.doBG = False
D12.doRaw = False
D12.doCorrel = True


def sweep_dim_1(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)


def sweep_dim_2(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)


def sweep_dim_3(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)


DS = DataStoreSP(folder, filen_0, dim_1, dim_2, dim_3, 'Vx1k')
DS.ask_overwrite()
copy_file(thisfile, filen_0, folder)

if recordD12:
    D12.create_datastore_objs(folder, filen_0, dim_1, dim_2, dim_3)
    # CorrProc controls, coordinates D1 and D2 together (also does thes calcs.)


def record_data(kk, jj, ii, back):
    '''This function is called with each change in ii,jj,kk
        content: what to measure each time
    '''
    if recordD12:
        D12.init_trigger()  # Trigger and check D1 & D2
    vdata = vm.get_val()  # acquire voltage data point
    if back is True:
        return DS.record_data2(vdata, kk, jj, ii)

    DS.record_data(vdata, kk, jj, ii)
    if recordD12:
        D12.full_aqc(kk, jj, ii)  # Records and calc D1 & D2
        if (lsamples/BW > 30):
            # save data at each point if it takes longer than 1min per point
            save_recorded()


def save_recorded():
    '''
    Which functions to call to save the recorded data
    '''
    DS.save_data()  # save Volt data
    if recordD12:
        D12.data_save()  # save Digitizer data


# go to default value and activate output
sweep_dim_1(dim_1, dim_1.defval)
sweep_dim_2(dim_2, dim_2.defval)
sweep_dim_3(dim_3, dim_3.defval)
dim_1.output(1)
dim_2.output(1)
dim_3.output(1)

print 'Executing sweep'
texp = (2.0*dim_3.pt*dim_2.pt*dim_1.pt*(0.032+corrAvg*lsamples/BW)/60.0)
print 'req time (min):' + str(texp)

t0 = time()
try:
    for kk in range(dim_3.pt):
        sweep_dim_3(dim_3, dim_3.lin[kk])

        for jj in range(dim_2.pt):
            sweep_dim_2(dim_2, dim_2.lin[jj])
            # sweep_dim_1(dim_1, dim_1.start)

            sleep(0.2)
            print 'Up Trace'
            for ii in range(dim_1.pt):
                sweep_dim_1(dim_1, dim_1.lin[ii])
                record_data(kk, jj, ii, False)

            if dim_1.UD is True:
                sweep_dim_1(dim_1, dim_1.stop)
                sleep(0.1)
                print 'Down Trace'
                for ii in range((dim_1.pt - 1), -1, -1):
                    sweep_dim_1(dim_1, dim_1.lin[ii])
                    record_data(kk, jj, ii, True)

            sweep_dim_1(dim_1, dim_1.start)

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
    sleep(1)
    dim_3.output(0)
    sim900._dconn()
    gc.collect()
    D1.performClose()
    D2.performClose()
    print 'done'
