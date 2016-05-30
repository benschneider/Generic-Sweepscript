# -*- coding: utf-8 -*-
"""
Created on Wed May 04 17:34:26 2016

@author: Ben
"""
from parsers import copy_file_interminal
import os

filen_0 = '1177_18GLPSN0'
folder = 'data_May29\\'
if not os.path.exists(folder):
    os.makedirs(folder)
    
copy_file_interminal('GsweepSN1.py', filen_0, folder)
execfile('GsweepSN1.py')

filen_0 = '1177_18GLP'
copy_file_interminal('Gsweep.py', filen_0, folder)
execfile('Gsweep.py')

filen_0 = '1177_18GLPSN1'
copy_file_interminal('GsweepSN1.py', filen_0, folder)
execfile('GsweepSN1.py')

execfile('Gsweeplist2.py')  # Possibility to add more measurements here