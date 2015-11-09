'''
Generic Sweep script
(currently setup for no more than 3 dims)

20/10/2015
- B
'''
from time import time, sleep
from parsers import copy_file
from ramp_mod import ramp
from DataStorer import DataStoreSP, DataStore2Vec, DataStore10Vec
from covfunc import getCovMatrix
thisfile = __file__

filen_0 = 'S1_910'
folder = 'data\\'

# Driver
from AgilentPSG import instrument as aPSG
from dummydriver import instrument as dummy
from keithley2000 import instrument as key2000
from Yoko import instrument as yoko
from AfDigi import instrument as AfDig

vm = key2000('GPIB0::29::INSTR')


lagsamples = 50e3
BW = 10e6
D1 = AfDig(adressDigi='3036D1', 
           adressLo='3011D1', 
           LoPosAB=1, 
           LoRef=0, 
           name='D1 Lags (sec)',
           cfreq = 4.57e9,
           start=(-lagsamples/BW), 
           stop=(lagsamples/BW), 
           pt=(lagsamples*2-1),
           nSample=lagsamples,
           sampFreq=BW)

D2 = AfDig(adressDigi='3036D2', 
           adressLo='3010D2', 
           LoPosAB=0, 
           LoRef=2, 
           name='D2 Lags (sec)',
           cfreq = 4.43e9,
           start=(-lagsamples/BW), 
           stop=(lagsamples/BW), 
           pt=(lagsamples*2-1),
           nSample=lagsamples,
           sampFreq=BW)

iBias = yoko('GPIB0::13::INSTR',
           name = 'Yoko V R=(998.83+14.24)KOhm',
           start = -2e-3,
           stop = -2e-3,
           pt = 1,
           sstep = 0.1, # def max voltage steps it can take
           stime = 0.1)
iBias.prepare_v(vrange = 5)  # vrange =2 -- 10mV, 3 -- 100mV, 4 -- 1V, 5 -- 10V, 6 -- 30V
iBias.UD = False
iBias.sweep_v(iBias.start, 1)  # sweep Ibias to its position

vMag = yoko('GPIB0::10::INSTR',
            name = 'Magnet V R=2.19KOhm',
            start = 0,
            stop = 0,
            pt = 1,
            sstep = 10e-3,
            stime = 1e-6)
vMag.prepare_v(vrange = 4)

PSG = aPSG('GPIB0::11::INSTR',
           name = 'RF - Power (V)',
           start = 250e-3,
           stop = 0,
           pt = 251,
           sstep = 20e-3,
           stime = 1e-3)
           
PSG.set_powUnit('V')
PSG.set_freq(9e9)  # 1GHz gives 2 uV steps
PSG.set_output(0)

iBias.sweep_par = 'v'
vMag.sweep_par = 'v'


nothing = dummy('GPIB0::11::INSTR',
           name = 'nothing',
           start = 250e-3,
           stop = 0,
           pt = 1,
           sstep = 20e-3,
           stime = 1e-3)


#dim_1= iBias
dim_1 = PSG
dim_1.UD = False
def sweep_dim_1(obj,value):
    #ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)
    #obj.sweep_v(value, 5)
    #sleep(5.1)
    PSG.set_power(value)

dim_2 = vMag
def sweep_dim_2(obj,value):
    ramp(obj, obj.sweep_par, value, obj.sstep, obj.stime)

dim_3 = nothing
def sweep_dim_3(obj,value):
    pass

DSP = DataStoreSP(folder, filen_0, dim_1, dim_2, dim_3, 'Voltage (V) x1000')
DSP.ask_overwrite()
DS2vD1 = DataStore2Vec(folder, filen_0, dim_1, dim_2, dim_2, 'D1vAvg')
DS2mD1 = DataStore2Vec(folder, filen_0, dim_1, dim_2, dim_2, 'D1mAvg')
DS2vD2 = DataStore2Vec(folder, filen_0, dim_1, dim_2, dim_2, 'D2vAvg')
DS2mD2 = DataStore2Vec(folder, filen_0, dim_1, dim_2, dim_2, 'D2mAvg')
DS10 = DataStore10Vec(folder, filen_0, dim_1, dim_2, D1, 'CovMat')
DS10.ask_overwrite()

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
                    dim_1.set_v2(dim_1.lin[ii])
                    vdata = vm.get_val()
                    DSP.record_data(vdata,kk,jj,ii)
                    
                    I1, Q1 = D1.get_rawIQ()
                    I2, Q2 = D2.get_rawIQ()

                    t0conv = time()
                    covMat = getCovMatrix(I1, Q1, I2, Q2)
                    DS10.record_data(covMat,kk,jj,ii)
                    print time()-t0conv

                    D1M, D1Ph = D1.get_AvgMagPhs()
                    DS2mD1.record_data(D1M, D1Ph, kk, jj, ii)
                    
                    D2M, D2Ph = D2.get_AvgMagPhs()
                    DS2mD2.record_data(D2M, D2Ph ,kk,  jj,ii)
                    
                    D1vM, D1vPh = D1.get_vAvgMagPhs()
                    DS2vD1.record_data(D1vM, D1vPh ,kk, jj, ii)
                    
                    D2vM, D2vPh = D2.get_vAvgMagPhs()
                    DS2vD2.record_data(D2vM, D2vPh ,kk ,jj ,ii)

                    D1Levelcorr = D1.get_Levelcorr()
                    D2Levelcorr = D2.get_Levelcorr()

            DSP.save_data()
            DS10.save_data()
            DS2vD1.save_data()
            DS2vD2.save_data()
            DS2mD1.save_data()
            DS2mD2.save_data()
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
    iBias.output(0)
    vMag.output(0)
    print  'done'
