# -*- coding: utf-8 -*-
"""
Created on Wed May 04 17:34:26 2016

@author: Ben
"""
from parsers import copy_file_interminal
folder = 'data_May12\\'

filen_0 = '1152SN0_'
copy_file_interminal('GsweepSN1.py', filen_0, folder)
execfile('GsweepSN1.py')
filen_0 = '1152_'
copy_file_interminal('Gsweep.py', filen_0, folder)
execfile('Gsweep.py')
filen_0 = '1152SN1_'
copy_file_interminal('GsweepSN1.py', filen_0, folder)
execfile('GsweepSN1.py')

execfile('Gsweeplist2.py')  # Possibility to add more measurements here