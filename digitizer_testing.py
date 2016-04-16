# -*- coding: utf-8 -*-
"""
Created on Fri Apr 15 21:19:35 2016

@author: Morran or Lumi
"""

# code to test digitizer e.v.t. kill some sidebands

from AfDigi import instrument as AfDig  # Digitizer driver
from nirack import nit  # load PXI trigger
from time import sleep, time
import numpy as np
from matplotlib import pyplot as plt
from ctypes import c_int, c_long, c_float, c_double, c_ulong, POINTER, byref
from ctypes import WinDLL, c_char_p, Structure, c_void_p, c_short #, create_string_buffer
#
trigger = nit()

D = WinDLL('afDigitizerDll_32')
class afDigitizerBufferIQ_t(Structure):
    pass

afDigitizerBufferIQ_t._fields_ = [
        ('iBuffer', POINTER(c_float)),
        ('qBuffer', POINTER(c_float)),
        ('samples', c_ulong),
        ('userData', c_void_p)]

session=c_long()
print D.afDigitizerDll_CreateObject(byref(session))
ses=session.value
D.afDigitizerDll_BootInstrument(session, '3011D1', '3036D1', False)

pipe=c_long()
D.afDigitizerDll_Capture_PipeliningEnable_Get(ses, byref(pipe))
print  pipe.value


#status=c_long()
#D.afDigitizerDll_Trigger_SwTriggerMode_Set(ses, 1) #set software trigger mode to armed
#D.afDigitizerDll_Trigger_SwTriggerMode_Get(ses, byref(status))


pCount=c_ulong()   
pCap=c_long()
#D.afDigitizerDll_Capture_IQ_TriggerCount_Get(ses, byref(pCount))
 

D.afDigitizerDll_Capture_PipeliningEnable_Set(ses, 1)
D.afDigitizerDll_Trigger_Source_Set(ses, 8)  # set to PXI star trigger mode

#set center frequency
D.afDigitizerDll_RF_CentreFrequency_Set(ses, c_double(4.8e9))

#get center frequency
f = c_double()
D.afDigitizerDll_RF_CentreFrequency_Get(ses, byref(f))
print f

#get LO position (above-below)
state = c_int()
D.afDigitizerDll_RF_UserLOPosition_Get(ses, byref(state))

#set LO position
D.afDigitizerDll_RF_UserLOPosition_Get(ses, 1)

#set sampling rate
samprate = 250e6
D.afDigitizerDll_Modulation_SetGenericSamplingFreqRatio(ses, c_long(samprate) , c_long(1))



samplenum = 1e6
def getIF(samplenum):  
    samplenum = int(samplenum)
    D.afDigitizerDll_Capture_IF_TriggerArm(ses, c_int(samplenum)) 
    D.afDigitizerDll_Capture_IF_TriggerCount_Get(ses,byref(pCount))
    print 'Trigger received: '+ str(bool(pCount.value))
    trigger.send_software_trigger()  # send PXI star trigger
    sleep(0.1)
    D.afDigitizerDll_Capture_IF_TriggerCount_Get(ses,byref(pCount))
    print 'Trigger received: '+ str(bool(pCount.value))
    D.afDigitizerDll_Capture_IF_GetSampleCaptured(ses, samplenum, byref(pCap))
    print 'Capture ready: '+ str(bool(pCap.value))
    
    Buffertype = c_short*samplenum
    ifbuffer = Buffertype()
    D.afDigitizerDll_Capture_IF_CaptMem(ses, samplenum, byref(ifbuffer))
    data = np.array(ifbuffer)
    return data

def plotIF_fft():
    a = getIF(1e6)
    b = getfft(a)
    #b = getfft(D1.cIQ)
    #plt.close('all')
    plt.figure()
    plt.plot(np.abs(np.fft.fftshift(b)))
    #plt.figure(2)
    #np.fft.fftshift(D1.cfftsig)
    #plt.plot(np.abs(D1.cfftsig))


#lags = 20
#BW = 250e6
#lsamples = 2e6
#
## LO 187.5MHz above / below
#
#D1 = AfDig(adressDigi='3036D1', adressLo='3011D1', LoPosAB=1, LoRef=3,
#           name='D1 Lags (sec)', cfreq=4.8e9, inputlvl=0,
#           start=(-lags / BW), stop=(lags / BW), pt=(lags * 2 - 1), 
#           nSample=lsamples, sampFreq=BW)
#
#D2 = AfDig(adressDigi='3036D2', adressLo='3010D2', LoPosAB=1, LoRef=0,
#           name='D2 Lags (sec)', cfreq=4.8e9, inputlvl=0,
#           start=(-lags / BW), stop=(lags / BW), pt=(lags * 2 - 1),
#           nSample=lsamples, sampFreq=BW)
#
#def get_IQ1():
#    t0 = time()
#    D1.init_trigger_buff()
#    sleep(0.02)
#    trigger.send_software_trigger()
#    # D1.downl_data_buff()
#    D1.get_data_complete()
#    print time() - t0
#    
#def get_IQ2():
#    t0 = time()
#    D2.init_trigger_buff()  # D1 fills buffer once it receives a Trigger
#    sleep(0.02)
#    trigger.send_software_trigger()  # The Trigger signal (PXI star)
#    # D2.downl_data_buff()
#    D1.get_data_complete()
#    print time() - t0
#
def getfft(cdata):
    cfftsig = np.fft.fft(cdata)
    return cfftsig
#
#def plotfft():
#    get_IQ1()
#    a = getfft(D1.cIQ)
#    #b = getfft(D1.cIQ)
#    plt.close('all')
#    plt.figure(1)
#    plt.plot(np.abs(np.fft.fftshift(a)))
#    plt.figure(2)
#    #np.fft.fftshift(D1.cfftsig)
#    plt.plot(np.abs(D1.cfftsig))
#
##D1.digitizer.set_IFaliasFilter(0)  # Bypass aliasing filter
#
#def find_nearest(someArray, value):
#    ''' This function helps to find the index corresponding to a value
#    in an array.
#    Usage: indexZero = find_nearest(myarray, 0.0)
#    returns: abs(myarray-value).argmin()
#    '''
#    idx = abs(someArray - value).argmin()
#    return idx
