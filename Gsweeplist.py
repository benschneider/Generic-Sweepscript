# -*- coding: utf-8 -*-
"""
Created on Wed May 04 17:34:26 2016

@author: Ben
"""
from parsers import copy_file_interminal
# import os

'''
No RT narrow bandpass filter involved
'''
# filen_0 = '3040_SN1'
# folder = 'data_Dec09\\'
# scriptfile = 'GsweepSN11_f.py'
# copy_file_interminal(scriptfile, filen_0, folder)
# execfile(scriptfile)

filen_0 = '3041_par'
folder = 'data_Dec09\\'
scriptfile = 'GsweepSN11_Parabola.py'
copy_file_interminal(scriptfile, filen_0, folder)
execfile(scriptfile)

filen_0 = '3042_SN2'
folder = 'data_Dec09\\'
scriptfile = 'GsweepSN11_f2.py'
copy_file_interminal(scriptfile, filen_0, folder)
execfile(scriptfile)

execfile('Gsweeplist2.py')  # Possibility to add more measurements here