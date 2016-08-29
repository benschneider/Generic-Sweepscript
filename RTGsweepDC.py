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
from SRsim import instrument as sim900c
from Sim928 import instrument as sim928c
# from Yoko import instrument as yoko
#from AfDigi import instrument as AfDig  # Digitizer driver
import gc  # Garbage memory collection
#from IQcorr import Process as CorrProc  # Handle Correlation measurements
import sys
import os

thisfile = __file__
filen_0 = '2005_RTDC'
folder = 'data_Jul28\\'
if not os.path.exists(folder):
    os.makedirs(folder)


sim900 = sim900c('GPIB0::12::INSTR')
vm = key2000('GPIB0::29::INSTR')


f1 = 4.8e9
f2 = 4.1e9



# Sweep equipment setup
nothing = dummy('none', name='nothing',
                start=0, stop=1, pt=1,
                sstep=20e-3, stime=0.0)

vBias = sim928c(sim900, name='V 1Mohm', sloti=4,
                start=(-6 +0.002), stop=6.002, pt=301,
                sstep=0.060, stime=0.020)

#vMag = dummy(sim900, name='Magnet V R=22.19KOhm', sloti=3,
#               start=-0.0, stop=0.0, pt=351,
#               sstep=0.03, stime=0.020)

pFlux = dummy('GPIB0::8::INSTR', name='FluxPump',
                 start=0.00, stop=0.00, pt=1,
                 sstep=10, stime=0)
#-30 dB at output

sgen = None

#pFlux.set_power_mode(1)  # Linear mode in mV
## f1+f2
#pFlux.set_freq(f1+f2)
#pFlux.sweep_par='power'  # Power sweep

dim_3 = nothing
dim_3.defval = 0.03 #pFlux
dim_2 = nothing
dim_2.defval = 0.0
dim_1 = vBias
dim_1.defval = 0.0
dim_1.UD = False
recordD12 = False  # all D1 D2 data storage
#D12 = CorrProc(D1, D2, pFlux, sgen, lags, BW, lsamples, corrAvg)
#D12.doHist2d = True  # Record Histograms (Larger -> Slower)
#D12.doRaw = False
#D12.doBG = False

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

# CorrProc controls, coordinates D1 and D2 together (also does thes calcs.)
#if recordD12:
#    D12.create_datastore_objs(folder, filen_0, dim_1, dim_2, dim_3)

# describe how data is to be stored
def record_data(kk, jj, ii, back):
    '''This function is called with each change in ii,jj,kk
        content: what to measure each time
    '''
#    if recordD12:
#        D12.init_trigger()  # Trigger and check D1 & D2
#        #print 'send trigger from loop'
    vdata = vm.get_val()  # aquire voltage data point
    if back is True:
        return DS.record_data2(vdata, kk, jj, ii)
        # didnt implement backsweep with Digitizers yet

    DS.record_data(vdata, kk, jj, ii)
#    if recordD12:
#        D12.full_aqc(kk, jj, ii)  # Records and calc D1 & D2
#        #if (lsamples/BW > 30):
#        #    save_recorded()

def save_recorded():
    '''
    Which functions to call to save the recored data
    '''
    DS.save_data()  # save Volt data
#    if recordD12:
#        D12.data_save()  # save Digitizer data

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
dim_3.output(0)

print 'Executing sweep'
texp = (2.0*dim_3.pt*dim_2.pt*dim_1.pt*(0.032)/60.0)
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
    #sleep(1)
    #dim_1.output(0)
    #sleep(1)
    #dim_2.output(0)
    sleep(1)
    dim_3.output(0)
    sim900._dconn()
    gc.collect()
    # D1.downl_data_buff()
    # D2.downl_data_buff()
    # D1.performClose()
    # D2.performClose()
    print 'done'
