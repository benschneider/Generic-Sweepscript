# -*- coding: utf-8 -*-
"""
Created on Wed May 04 17:34:26 2016

@author: Ben
"""
from parsers import copy_file_interminal
folder = 'data_May12\\'

#execfile('GsweepSN1.py')  # 1096_SN shotnoise calibration
#copy_file('GsweepSN1.py', filen_0, folder)
#execfile('Gsweep1.py')  # 1097
#copy_file('Gsweep1.py', filen_0, folder)
#execfile('GsweepSN2.py')  # 1098_SN
#copy_file('GsweepSN2.py', filen_0, folder)
#execfile('Gsweep2.py')  # 1099
#copy_file('Gsweep2.py', filen_0, folder)
#execfile('GsweepSN3.py')  # 1100_SN
#copy_file('GsweepSN3.py', filen_0, folder)
#execfile('Gsweep3.py')  # 1101
#copy_file('Gsweep3.py', filen_0, folder)
#execfile('GsweepSN4.py')  # 1102_SN
#copy_file('GsweepSN4.py', filen_0, folder)

filen_0 = '1130_SN0'
copy_file_interminal('GsweepSN1.py', filen_0, folder)
# copy_file('GsweepSN5.py', filen_0, folder)
execfile('GsweepSN1.py')
filen_0 = '1130'
copy_file_interminal('Gsweep.py', filen_0, folder)
execfile('Gsweep.py')
filen_0 = '1130_SN1'
copy_file_interminal('GsweepSN1.py', filen_0, folder)
execfile('GsweepSN1.py')
