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
# from AnritzuSig import instrument as AnSigGen
from SRsim import instrument as sim900c
from Sim928 import instrument as sim928c
from RSZNB20 import instrument as ZNB20
# from Yoko import instrument as yoko
import gc  # Garbage memory collection
import os

thisfile = __file__
filen_0 = '1171S21'
folder = 'data_May24\\'
folder = folder + filen_0 + '\\'  # in one new folder
if not os.path.exists(folder):
    os.makedirs(folder)


sim900 = sim900c('GPIB0::12::INSTR')
# sim900 = dummy('GPIB0::12::INSTR')
vm = key2000('GPIB0::29::INSTR')

VNA = ZNB20('TCPIP::129.16.115.137::INSTR', name='ZNB20',
                start=2.5e9, stop=8.5e9, pt=601,
                sstep=20e-3, stime=0.0, copy_setup=False)

# Sweep equipment setup
nothing = dummy(name='nothing', start=0, stop=1, pt=1, sstep=20e-3, stime=0.0)


vBias = sim928c(sim900, name='V 1Mohm', sloti=2,
                start=-5.0, stop=5.0, pt=101,
                sstep=0.060, stime=0.020)

vMag = sim928c(sim900, name='Magnet V R=22.19KOhm', sloti=3,
               start=-2.0, stop=5.0, pt=281,
               sstep=0.03, stime=0.020)

# pFlux = AnSigGen('GPIB0::17::INSTR', name='FluxPump',
#                  start=2.03, stop=0.03, pt=101,
#                  sstep=10, stime=0)

dim_1 = nothing
dim_1.defval = 0.0
dim_1.UD = False
dim_3 = vMag
dim_3.defval = 0.0
dim_2 = vBias
dim_2.defval = 0.0


def sweep_dim_1(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)


def sweep_dim_2(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)


def sweep_dim_3(obj, value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)


# This describes how data is saved
DS = DataStoreSP(folder, filen_0, dim_1, dim_2, dim_3, 'Vx1k')
DS.ask_overwrite()
copy_file(thisfile, filen_0, folder)
VNA.prepare_data_save(folder, filen_0, dim_1, dim_2, dim_3)


def record_data(kk, jj, ii, back):
    '''describe how data is to be stored
    This function is called with each change in ii,jj,kk
        content: what to measure each time
    '''
    VNA.init_sweep()
    vdata = vm.get_val()  # aquire voltage data point
    sleep(VNA.sweeptime)
    vnadata = VNA.get_data2()  # take VNA sweep
    if back is True:
        return DS.record_data2(vdata, kk, jj, ii)

    DS.record_data(vdata, kk, jj, ii)
    VNA.record_data(vnadata, kk, jj, ii)


def save_recorded():
    '''
    Which functions to call to save the recored data
    '''
    DS.save_data()  # save Volt data
    VNA.save_data()  # save VNA data

# go to default value and activate output
sweep_dim_1(dim_1, dim_1.defval)
sweep_dim_2(dim_2, dim_2.defval)
sweep_dim_3(dim_3, dim_3.defval)
dim_1.output(1)
dim_2.output(1)
dim_3.output(1)

print 'Executing sweep'
texp = (2.0 * dim_3.pt * dim_2.pt * dim_1.pt * (0.032) / 60.0)
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
                # print 'sweep+record ', time()-txx

            if dim_1.UD is True:
                sweep_dim_1(dim_1, dim_1.stop)
                sleep(0.1)
                print 'Down Trace'
                for ii2 in range((dim_1.pt - 1), -1, -1):
                    sweep_dim_1(dim_1, dim_1.lin[ii2])
                    record_data(kk, jj, ii2, True)

            runt = time() - t0  # time run so far
            avgtime = runt / ((kk + 1) * (jj + 1) * (ii + 1))  # per point
            t_rem = avgtime * dim_3.pt * dim_2.pt * dim_1.pt - runt  # time left
            print 'req time (h):' + str(t_rem / 3600) + ' pt: ' + str(avgtime)

        save_recorded()
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
    print 'done'
