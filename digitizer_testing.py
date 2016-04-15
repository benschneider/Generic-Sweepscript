# -*- coding: utf-8 -*-
"""
Created on Fri Apr 15 21:19:35 2016

@author: Morran or Lumi
"""

# code to test digitizer data 
# Goal is to kill the noise sideband.

from AfDigi import instrument as AfDig  # Digitizer driver
# from IQcorr import Process as CorrProc  # Handle Correlation measurements
from nirack import nit  # load PXI trigger
from time import sleep
import numpy as np

lags = 20
BW = 10e6
lsamples = 30e6
corrAvg = 1

# LO 187MHz above / below

D1 = AfDig(adressDigi='3036D1', adressLo='3011D1', LoPosAB=1, LoRef=3,
           name='D1 Lags (sec)', cfreq=4.8e9, inputlvl=0,
           start=(-lags / BW), stop=(lags / BW), pt=(lags * 2 - 1), 
           nSample=lsamples, sampFreq=BW)

D2 = AfDig(adressDigi='3036D2', adressLo='3010D2', LoPosAB=1, LoRef=0,
           name='D2 Lags (sec)', cfreq=4.8e9, inputlvl=0,
           start=(-lags / BW), stop=(lags / BW), pt=(lags * 2 - 1),
           nSample=lsamples, sampFreq=BW)

trigger = nit()

def get_IQ1():
    D1.init_trigger_buff()
    sleep(0.02)
    trigger.send_software_trigger()
    D1.downl_data_buff2()
    
def get_IQ2():
    D2.init_trigger_buff()
    sleep(0.02)
    trigger.send_software_trigger()
    D2.downl_data_buff2()

def getfft():
    '''
    Generates complex FFT of the data and kills the side-band.
    cleared FFT data is stored in self.cfftsig
    '''
    cfftsig = np.fft.fft(1j*D1.scaledI + D1.scaledQ)
    #smid = int(len(cfftsig)/2) + 1
    #if self.LoPos is 1:
    #    self.cfftsig[smid:-1] = 0.0
    #else:
    #    self.cfftsig[0:smid] = 0.0
    return cfftsig
