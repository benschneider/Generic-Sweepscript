'''
Generic Sweep script
(currently setup for no more than 3 dims)

20/10/2015
- B
'''
from time import time, sleep
from parsers import copy_file
from ramp_mod import ramp
from DataStorer import DataStoreSP  # , DataStore2Vec, DataStore11Vec
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

thisfile = __file__
filen_0 = '1214_Par'
folder = 'data_Jul19\\'
folder = folder + filen_0 + '\\'  # in one new folder
if not os.path.exists(folder):
    os.makedirs(folder)

sim900 = sim900c('GPIB0::12::INSTR')
vm = key2000('GPIB0::29::INSTR')

# Digitizer setup
lags = 30
BW = 1e6
lsamples = 1e6
corrAvg = 1
f1 = 4.8e9  # 4.799999e9
f2 = 4.8e9

# BPF implemented to kill noise sideband,
# FFT filtering not yet working, possibly BW not large enough
# D1 4670MHZ Edge (4.8GHz) LO above
# D2 4330MHz Edge (4.1GHz) LO below
D1 = AfDig(adressDigi='3036D1', adressLo='3011D1', LoPosAB=1, LoRef=0,
           name='D1 Lags (sec)', cfreq=f1, inputlvl=-20,
           start=(-lags / BW), stop=(lags / BW), pt=(lags * 2 - 1),
           nSample=lsamples, sampFreq=BW)

D2 = AfDig(adressDigi='3036D2', adressLo='3010D2', LoPosAB=0, LoRef=3,
           name='D2 Lags (sec)', cfreq=f2, inputlvl=-15,
           start=(-lags / BW), stop=(lags / BW), pt=(lags * 2 - 1),
           nSample=lsamples, sampFreq=BW)

# Sweep equipment setup
Dfreq = dummy('DigiFreq', name='Frequency',
                start=4e9, stop=6.0e9, pt=201,
                sstep=10e9, stime=0.0)

vBias = sim928c(sim900, name='V 1Mohm', sloti=4, 
                start=0.0, stop=0.0, pt=1, 
                sstep=0.060, stime=0.020)

vMag = sim928c(sim900, name='Magnet V R=22.19KOhm', sloti=3,
               start=-1.1, stop=-1.1, pt=1,
               sstep=0.03, stime=0.020)

pFlux = AnSigGen('GPIB0::8::INSTR', name='FluxPump',
                 start=0.1, stop=0.00, pt=51,
                 sstep=30e-3, stime=1e-3)
# -30 dB at output

sgen = None

pFlux.set_power_mode(1)  # Linear mode in mV
# f1+f2
pFlux.set_freq(8.9e9)
pFlux.sweep_par='power'  # Power sweep
pFlux.output(1)
Dfreq.sweep_par='f11'
Dfreq.D1 = D1
Dfreq.D2 = D2

dim_1 = Dfreq
dim_1.defval = 4.8e9
dim_2 = pFlux
dim_2.defval = 0.0
dim_3 = vMag
dim_3.defval = -1.1
dim_1.UD = False
recordD12 = True  # activates /deactivates all D1 D2 data storage
D12 = CorrProc(D1, D2, pFlux, sgen, lags, BW, lsamples, corrAvg)
D12.doHist2d = False
D12.doBG = False
D12.doRaw = True
D12.doCorrel = True

def sweep_dim_1(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)


def sweep_dim_2(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)


def sweep_dim_3(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)


sweep_dim_1(vBias, 0.0)
vBias.output(1)

# This describes how data is saved
DS = DataStoreSP(folder, filen_0, dim_1, dim_2, dim_3, 'Vx1k')
DS.ask_overwrite()
copy_file(thisfile, filen_0, folder)

if recordD12:
    # CorrProc controls, coordinates D1 and D2 together (also does thes calcs.)
    D12.create_datastore_objs(folder, filen_0, dim_1, dim_2, dim_3)


# describe how data is to be stored
def record_data(kk, jj, ii, back):
    '''This function is called with each change in ii,jj,kk
        content: what to measure each time
    '''
    if recordD12:
        D12.init_trigger()  # Trigger and check D1 & D2
        # print 'send trigger from loop'
    vdata = vm.get_val()  # aquire voltage data point
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
    Which functions to call to save the recored data
    '''
    DS.save_data()  # save Volt data
    if recordD12:
        D12.data_save()  # save Digitizer data

def progresbar(kk, jj, ii):
    ''' shows the progress (only from cmd line) '''
    sys.stdout.write('\r')
    pgsk = 100.0*(kk/dim_3.pt)
    pgsj = 100.0*(jj/dim_2.pt)
    pgsi = 100.0*(ii/dim_1.pt)
    sys.stdout.write('kk ' + str(pgsk) + ' jj ' + str(pgsj) + ' ii ' + str(pgsi))
    sys.stdout.flush()


# go to default value and activate output
sweep_dim_1(dim_1, dim_1.defval)
sweep_dim_2(dim_2, dim_2.defval)
sweep_dim_3(dim_3, dim_3.defval)
dim_1.output(1)
dim_2.output(1)
dim_3.output(1)

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
                sweep_dim_1(dim_1, dim_1.lin[ii])
                record_data(kk, jj, ii, False)

            if dim_1.UD is True:
                sweep_dim_1(dim_1, dim_1.stop)
                sleep(0.1)
                print 'Down Trace'
                for ii in range((dim_1.pt - 1), -1, -1):
                    # progresbar(kk, jj, ii)
                    sweep_dim_1(dim_1, dim_1.lin[ii])
                    record_data(kk, jj, ii, True)

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
    pFlux.output(0)
    gc.collect()
    vBias.output(0)
    # D1.downl_data_buff()
    # D2.downl_data_buff()
    D1.performClose()
    D2.performClose()
    print 'done'