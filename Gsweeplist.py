# -*- coding: utf-8 -*-
"""
Created on Wed May 04 17:34:26 2016

@author: Ben
"""
from parsers import copy_file_interminal
import os

'''
8x8 Cov Matrix
- Shotnoise
- I1 I1  upper left quad
- I2 I2 lower right quad
- I1 I2 Cov Mat with Gain 1
- I2 I1 Cov Mat with Gain 2
- Shotnoise
'''

'''
No RT narrow bandpass filter involved
'''
filen_0 = '1208_SN11_up'
folder = 'data_Jul17\\'
copy_file_interminal('GsweepSN11_1.py', filen_0, folder)
execfile('GsweepSN11_1.py')

filen_0 = '1208_SN11_down'
folder = 'data_Jul17\\'
copy_file_interminal('GsweepSN11_2.py', filen_0, folder)
execfile('GsweepSN11_2.py')

#folder = 'data_Jul15\\'
#filen_0 = '1206_SN22_0'
#copy_file_interminal('GsweepSN22.py', filen_0, folder)
#execfile('GsweepSN22.py')
#
#folder = 'data_Jul15\\'
#filen_0 = '1206'
#copy_file_interminal('GsweepCov2.py', filen_0, folder)
#execfile('GsweepCov2.py')
#
#folder = 'data_Jul15\\'
#filen_0 = '1206_SN11_1'
#copy_file_interminal('GsweepSN11.py', filen_0, folder)
#execfile('GsweepSN11.py')
#
#folder = 'data_Jul15\\'
#filen_0 = '1206_SN22_1'
#copy_file_interminal('GsweepSN22.py', filen_0, folder)
#execfile('GsweepSN22.py')

# execfile('Gsweeplist2.py')  # Possibility to add more measurements here