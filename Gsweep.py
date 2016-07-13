'''
Generic Sweep script
(currently setup for no more than 3 dims)

20/10/2015
- B
'''
#import numpy as np
from time import time, sleep
from parsers import copy_file
from ramp_mod import ramp
from DataStorer import DataStoreSP  # , DataStore2Vec, DataStore11Vec
# Drivers
from dummydriver import instrument as dummy
from keithley2000 import instrument as key2000
# from AnritzuSig import instrument as AnSigGen
from SRsim import instrument as sim900c
from Sim928 import instrument as sim928c
# from Yoko import instrument as yoko
# from AfDigi import instrument as AfDig  # Digitizer driver
import gc  # Garbage memory collection
# from IQcorr import Process as CorrProc  # Handle Correlation measurements
# import sys
# from RSZNB20 import instrument as ZNB20
import os


''' DC test sweep '''

thisfile = __file__
filen_0 = '1200'
folder = 'data_Jul12\\'
folder = folder + filen_0 + '\\'  # in one new folder
if not os.path.exists(folder):
    os.makedirs(folder)

sim900 = sim900c('GPIB0::12::INSTR')
vm = key2000('GPIB0::29::INSTR')

# Digitizer setup
lags = 30
BW = 1e6
lsamples = 1e4
corrAvg = 1
f1 = 4.8e9  # 4.799999e9
f2 = 4.1e9
#
#D1 = AfDig(adressDigi='3036D1', adressLo='3011D1', LoPosAB=0, LoRef=0,
#           name='D1', cfreq=f1, inputlvl=2,
#           start=(-lags / BW), stop=(lags / BW), pt=(lags * 2 - 1),
#           nSample=lsamples, sampFreq=BW)
#
#D2 = AfDig(adressDigi='3036D2', adressLo='3010D2', LoPosAB=1, LoRef=3,
#           name='D2', cfreq=f2, inputlvl=2,
#           start=(-lags / BW), stop=(lags / BW), pt=(lags * 2 - 1),
#           nSample=lsamples, sampFreq=BW)


def sweep_dim_1(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)


def sweep_dim_2(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)


def sweep_dim_3(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)

# Sweep equipment setup
#pFlux = AnSigGen('GPIB0::17::INSTR', name='FluxPump',
#                 start=0.03, stop=0.03, pt=1,
#                 sstep=10, stime=0)
#
#D12spacing = dummy(name='D1-f',
#                start=5.4e9, stop=3.5e9, pt=1,
#                sstep=4e9, stime=0.0)

vBias = sim928c(sim900, name='V 1Mohm', sloti=2,
                start=-5, stop=5, pt=201,
                sstep=0.060, stime=0.020)

vMag = sim928c(sim900, name='Magnet V R=22.19KOhm', sloti=3,
               start=-2.0, stop=2.0, pt=401,
               sstep=0.03, stime=0.020)

nothing = dummy(name='nothing',
                start=0, stop=1, pt=1,
                sstep=1.0, stime=0.0)


#pFlux.set_power_mode(1)  # Linear mode in mV
#pFlux.set_freq(f1+f2)
#pFlux.sweep_par='power'  # Power sweep
#D12spacing.D1 = D1  # assign objects (in reverse D1 f > D2 f)
#D12spacing.D2 = D2
#D12spacing.sweep_par = 'f12'
#D12spacing.cfreq = f1+f2
# sweep_dim_1(vBias, 0.002)

dim_1 = vBias
dim_1.UD = True
dim_1.defval = 0.0
dim_2 = vMag
dim_2.defval = 0.0
dim_3 = nothing
dim_3.defval = 0.0

#sgen = None
recordD12 = False  # all D1 D2 data storage
#D12 = CorrProc(D1, D2, pFlux, sgen, lags, BW, lsamples, corrAvg)
#D12.doHist2d = False  # Record Histograms (Larger -> Slower)
#D12.doCorrel = False
#D12.doRaw = False
#D12.doBG = False
#
#
# This describes how data is saved
DS = DataStoreSP(folder, filen_0, dim_1, dim_2, dim_3, 'Vx1k')
DS.ask_overwrite()
copy_file(thisfile, filen_0, folder)

# CorrProc controls, coordinates D1 and D2 together (also does thes calcs.)
if recordD12:
    D12.create_datastore_objs(folder, filen_0, dim_1, dim_2, dim_3)

# describe how data is to be stored
def record_data(kk, jj, ii, back):
    '''This function is called with each change in ii,jj,kk
        content: what to measure each time
    '''
    if recordD12:
        D12.init_trigger()  # Trigger and check D1 & D2
        #print 'send trigger from loop'
    vdata = vm.get_val()  # aquire voltage data point
    if back is True:
        return DS.record_data2(vdata, kk, jj, ii)
        # didnt implement backsweep with Digitizers yet

    DS.record_data(vdata, kk, jj, ii)
    if recordD12:
        D12.full_aqc(kk, jj, ii)  # Records and calc D1 & D2
        #if (lsamples/BW > 30):
        #    save_recorded()

def save_recorded():
    '''
    Which functions to call to save the recored data
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
dim_3.output(0)

print 'Executing sweep'
texp = (2.0*dim_3.pt*dim_2.pt*dim_1.pt*(0.032+corrAvg*lsamples/BW)/60.0)
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
                #txx = time()
                sweep_dim_1(dim_1, dim_1.lin[ii])
                record_data(kk, jj, ii, False)
                #print 'sweep+record ', time()-txx

            if dim_1.UD is True:
                sweep_dim_1(dim_1, dim_1.stop)
                sleep(0.1)
                print 'Down Trace'
                for ii2 in range((dim_1.pt - 1), -1, -1):
                    sweep_dim_1(dim_1, dim_1.lin[ii2])
                    record_data(kk, jj, ii2, True)

            save_recorded()
            runt = time()-t0  # time run so far
            avgtime = runt / ((kk+1)*(jj+1)*(ii+1))  # per point
            t_rem = avgtime*dim_3.pt*dim_2.pt*dim_1.pt - runt  # time left
            print 'req time (h):' + str(t_rem / 3600) + ' pt: ' + str(avgtime)
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
#    D1.performClose()
#    D2.performClose()
#    sweep_dim_1(vBias, 0.0)
    # pFlux.output(0)
    print 'done'