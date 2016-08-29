# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 17:44:16 2016

@author: Morran or Lumi
"""

#import numpy as np
from time import time, sleep
from parsers import copy_file
from SRsim import instrument as sim900c
from Sim928 import instrument as sim928c

sim900 = sim900c('GPIB0::12::INSTR')

D1 = sim928c(sim900, name='V 1Mohm', sloti=2,
                start=(-6 +0.002), stop=6.002, pt=301,
                sstep=0.060, stime=0.020)

D2 = sim928c(sim900, name='V 1Mohm', sloti=3,
                start=(-6 +0.002), stop=6.002, pt=301,
                sstep=0.060, stime=0.020)
                
                
#print D1.a('*IDN?')
#sleep(5)
#D1.set_volt(1)
#print D1.a('BIDN? PNUM')
#print D1.a('BIDN? SERIAL')
#print D1.a('BIDN? MAXCY')
#print D1.a('BIDN? CYCLES')
#print D1.a('BIDN? PDATE')