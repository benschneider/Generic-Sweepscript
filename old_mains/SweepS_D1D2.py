'''
Generic Sweep script
(currently setup for no more than 3 dims)

20/10/2015
- B
'''
from time import time, sleep
from parsers import copy_file
from ramp_mod import ramp
from DataStorer import DataStoreSP, DataStore2Vec, DataStore11Vec
from covfunc import getCovMatrix
import numpy as np

thisfile = __file__

filen_0 = 'S1_959_G27mV_P80mOnOff'
folder = 'data\\'

# Driver
from AgilentPSG import instrument as aPSG
from dummydriver import instrument as dummy
from keithley2000 import instrument as key2000
from Yoko import instrument as yoko
from AfDigi import instrument as AfDig

vm = key2000('GPIB0::29::INSTR')

lsamples = 1e6
lags = 25  # in points
BW = 1e5
corrAvg = 10

D1 = AfDig(adressDigi='3036D1',
           adressLo='3011D1',
           LoPosAB=0,
           LoRef=0,
           name='D1 Lags (sec)',
           cfreq = 4.1e9,
           inputlvl = -15,
           start=(-lags/BW),
           stop=(lags/BW),
           pt=(lags*2-1),
           nSample=lsamples,
           sampFreq=BW)

D2 = AfDig(adressDigi='3036D2',
           adressLo='3010D2',
           LoPosAB=1,
           LoRef=2,
           name='D2 Lags (sec)',
           cfreq = 4.8e9,
           inputlvl = -15,
           start=(-lags/BW),
           stop=(lags/BW),
           pt=(lags*2-1),
           nSample=lsamples,
           sampFreq=BW)

iBias = yoko('GPIB0::13::INSTR',
           name = 'Yoko V R=(998.83+14.24)KOhm',
           start = -1-2e-3,
           stop = 1-2e-3,
           pt = 5,
           sstep = 0.1, # def max voltage steps it can take
           stime = 0.05)
iBias.prepare_v(vrange = 6)  # vrange =2 -- 10mV, 3 -- 100mV, 4 -- 1V, 5 -- 10V, 6 -- 30V
iBias.UD = False
#iBias.sweep_v(-6, 6)
iBias.sweep_v(iBias.start, 10)  # sweep Ibias to its position

vMag = yoko('GPIB0::10::INSTR',
            name = 'Magnet V R=2.19KOhm',
            start = 27e-3,  # -300e-3,
            stop = 27e-3,  # 300e-3,
            pt = 1,
            sstep = 10e-3,
            stime = 1e-6)
vMag.prepare_v(vrange = 4)
vMag.sweep_v(vMag.start, 2)
sleep (7)

PSG = aPSG('GPIB0::11::INSTR',
           name = 'RF - Power (V)',
           start = 60.0e-3,  # 406e-3+40e-9,
           stop = 60.0e-3,  # 230e-3,
           pt = 2,
           sstep = 20e-3,
           stime = 1e-3)

PSG.set_powUnit('V')
# PSG.set_freq(12.9e9)  # 1GHz gives 2uV steps
# PSG.set_freq(12.2e9)
PSG.set_freq(8.9e9)
PSG.set_output(1)
PSG.set_power(PSG.start)

iBias.sweep_par = 'v'
vMag.sweep_par = 'v'


nothing = dummy('GPIB0::11::INSTR',
           name = 'nothing',
           start = 0,
           stop = 0,
           pt = 1,
           sstep = 20e-3,
           stime = 1e-3)

# dim_2 = vMag

dim_1 = PSG
dim_2= iBias
dim_3 = nothing
dim_1.UD = False

def sweep_dim_1(obj,index):
    # value = obj.lin[int(index)]
    if index == 0 :  # check for even number
        PSG.set_output(1)
    elif index == 1:
        PSG.set_output(0)
    else:
        PSG.set_output(0)
    # PSG.set_power(value)
    # ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)
    # PSG.set_output(1)
    pass


def sweep_dim_2(obj,index):
    value = obj.lin[int(index)]
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)
    # obj.sweep_v(value, 5)
    # sleep(5.1)
    # PSG.set_power(value)

def sweep_dim_3(obj,index):
    # value = obj.lin[int(index)]
    pass

DSP = DataStoreSP(folder, filen_0, dim_1, dim_2, dim_3, label='V', cname='Voltage x1k')
DS11 = DataStore11Vec(folder, filen_0, dim_1, dim_2, D1, 'CovMat')
DSP.ask_overwrite()

DSP_PD1 = DataStoreSP(folder, filen_0, dim_1, dim_2, dim_3, label='D1Pow', cname='Watts')
DSP_LD1 = DataStoreSP(folder, filen_0, dim_1, dim_2, dim_3, label='D1LevCorr', cname='LvLCorr')
DS2vD1 = DataStore2Vec(folder, filen_0, dim_1, dim_2, dim_3, 'D1vAvg')
DS2mD1 = DataStore2Vec(folder, filen_0, dim_1, dim_2, dim_3, 'D1mAvg')

DSP_PD2 = DataStoreSP(folder, filen_0, dim_1, dim_2, dim_3, label='D2Pow', cname='Watts')
DSP_LD2 = DataStoreSP(folder, filen_0, dim_1, dim_2, dim_3, label='D2LevCorr', cname='LvLCorr')
DS2vD2 = DataStore2Vec(folder, filen_0, dim_1, dim_2, dim_3, 'D2vAvg')
DS2mD2 = DataStore2Vec(folder, filen_0, dim_1, dim_2, dim_3, 'D2mAvg')


copy_file(thisfile, filen_0, folder) #backup this script
print 'Executing sweep'
# print 'Est. req time (min):'+str(corrAvg*lsamples/BW*dim_3.pt*dim_2.pt*dim_1.pt*0.032/60)  # this involves only DC measurements
print '2nd Est. req time (h):' +str(corrAvg*lsamples/BW*1.1*dim_3.pt*dim_2.pt*dim_1.pt/3600)  # Involving both DC, AC and Correlations..
t0 = time()
try:
    for kk in range(dim_3.pt):
        sweep_dim_3(dim_3, kk)
        sweep_dim_2(dim_2, 0)
        for jj in range(dim_2.pt):
            sweep_dim_2(dim_2, jj)
            sweep_dim_1(dim_1, 0)
            D1.get_newdata()   # run one test and update lvl correction
            D2.get_newdata()   # run one test and update lvl correction

            if dim_1.UD is True:
                print 'Up Trace'
                for ii in range(dim_1.pt):
                    dim_1.set_v2(dim_1.lin[ii])
                    vdata = vm.get_val()
                    DSP.record_data(vdata,kk,jj,ii)

                sweep_dim_1(dim_1,dim_1.stop)
                print 'Down Trace'
                for ii in range((dim_1.pt-1),-1,-1):
                    dim_1.set_v2(dim_1.lin[ii])
                    vdata = vm.get_val()
                    DSP.record_data2(vdata,kk,jj,ii)
            else:
                for ii in range(dim_1.pt):
                    # dim_1.set_v2(dim_1.lin[ii])
                    sweep_dim_1(dim_1, ii)
                    # D1.get_newdata()  # run one test and update lvl correction
                    # D2.get_newdata()  # run one test and update lvl correction

                    vdata = np.float(0.0)
                    D1Ma = np.float(0.0)
                    D1Pha =  np.float(0.0)
                    D1vMa = np.float(0.0)
                    D1vPha =  np.float(0.0)

                    D2vMa = np.float(0.0)
                    D2vPha =  np.float(0.0)
                    D2Ma = np.float(0.0)
                    D2Pha =  np.float(0.0)

                    covAvgMat = np.zeros([11,lags*2-1])
                    D1aPow = np.float(0.0)
                    D2aPow = np.float(0.0)
                    D1.init_trigger()
                    D2.init_trigger()

                    t0conv = time()
                    for cz in range(int(corrAvg)):
                        # Digitizers take data now @ same/sim time

                        D1.wait_capture_complete()
                        D2.wait_capture_complete()

                        D1.downl_data()
                        D2.downl_data()

                        if (cz+1) < corrAvg:
                            D1.init_trigger()
                            D2.init_trigger()

                        D1.process_data()
                        D2.process_data()

                        # Digitizer 1 Values
                        D1M, D1Ph = D1.get_AvgMagPhs()
                        D1Ma = D1Ma + D1M
                        D1Pha = D1Pha + D1Ph

                        D1vM, D1vPh = D1.get_vAvgMagPhs()
                        D1vMa = D1vMa + D1vM
                        D1vPha = D1vPha + D1vPh

                        D1aPow = D1aPow + D1.get_AvgPower()
                        D2aPow = D2aPow + D2.get_AvgPower()

                        # Digitizer 2 Values
                        D2M, D2Ph = D2.get_AvgMagPhs()
                        D2Ma = D2Ma + D1M
                        D2Pha = D2Pha + D2Ph

                        D2vM, D2vPh = D2.get_vAvgMagPhs()
                        D2vMa = D2vMa + D2vM
                        D2vPha = D2vPha + D2vPh
                        vdata = vdata + vm.get_val()

                        I1 = D1.scaledI
                        Q1 = D1.scaledQ
                        I2 = D2.scaledI
                        Q2 = D2.scaledQ
                        covAvgMat = covAvgMat +  getCovMatrix(I1, Q1, I2, Q2, lags)

                        # D1Lvl = D1Lvl + D1.levelcorr
                        # D2Lvl = D2Lvl + D2.levelcorr

                    # print cz, time()-t0conv

                    # Recording data in Memory
                    DS11.record_data(covAvgMat/np.float(corrAvg),kk,jj,ii)
                    DSP.record_data(vdata/np.float(corrAvg),kk,jj,ii)

                    DSP_LD1.record_data(D1.levelcorr,kk, jj, ii)
                    DS2mD1.record_data(D1Ma/np.float(corrAvg), D1Pha/np.float(corrAvg), kk, jj, ii)
                    DS2vD1.record_data(D1vMa/np.float(corrAvg), D1vPha/np.float(corrAvg) ,kk, jj, ii)
                    DSP_PD1.record_data((D1aPow/np.float(corrAvg)) ,kk, jj, ii)

                    DSP_LD2.record_data(D2.levelcorr, kk, jj, ii)
                    DS2mD2.record_data(D2Ma/np.float(corrAvg), D2Pha/np.float(corrAvg), kk, jj, ii)
                    DS2vD2.record_data(D2vMa/np.float(corrAvg), D2vPha/np.float(corrAvg), kk, jj, ii)
                    DSP_PD2.record_data((D2aPow/np.float(corrAvg)) ,kk, jj, ii)

                    DSP.save_data()
                    DS11.save_data()
                    DSP_PD1.save_data()
                    DSP_PD2.save_data()



            # Free up some Memomy
            covAvgMat = None
            covMat = None
            I1 = None
            I2 = None
            Q1 = None
            Q2 = None

            DSP.save_data()
            DS11.save_data()

            DS2vD1.save_data()
            DS2mD1.save_data()
            DSP_PD1.save_data()
            DSP_LD2.save_data()
            DSP_LD1.save_data()

            DS2vD2.save_data()
            DS2mD2.save_data()
            DSP_PD2.save_data()

            t1 = time()
            remaining_time = ((t1-t0)/(jj+1)*dim_2.pt*dim_3.pt - (t1-t0))
            print 'req time (h):'+str(remaining_time/3600)

    print 'Measurement Finished'
    # D1.performClose()
    # D2.performClose()

except (KeyboardInterrupt):
    print '***** Keyboart Interupt *****'

finally:
    print 'Time used min:' +str((time()-t0)/60)
    print 'Yokos -> zero and switch off'
    iBias.sweep_v(0, 5)
    vMag.sweep_v(0, 5)
    sleep(5.2)
    iBias.output(0)
    vMag.output(0)
    PSG.set_output(0)
    D1.performClose()
    D2.performClose()
    print  'done'
