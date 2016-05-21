# -*- coding: utf-8 -*-
"""
Created on Fri May 20 18:12:38 2016

@author: Morran or Lumi
"""

from parsers import storehdf5
import numpy as np

# Sim data
I1 = np.random.rand(int(1e6))  
Q1 = np.random.rand(int(1e6))  
I2 = np.random.rand(int(1e6))  
Q2 = np.random.rand(int(1e6))  
ArrD1D2 = np.zeros([1, 4, 1e6])
ArrD1D2[0,0] = I1
ArrD1D2[0,1] = Q1
ArrD1D2[0,2] = I2
ArrD1D2[0,3] = Q2

# Exa cordinates
ii = 12
jj = 20
kk = 1
coord = np.zeros([1, 3])
coord[0, 0] = ii
coord[0, 1] = jj
coord[0, 2] = kk

f1 = storehdf5('test.hdf5')
f1.open_f(mode='r')
#shapeD1D2 = (0, 4, 1e6)
#shapeCord = (0, 3)
#f1.create_dset2(shapeD1D2, label='D12raw', esize=(ii*jj*kk))
#f1.create_dset2(shapeCord, label='ijk', esize=(ii*jj*kk))

ca = f1.h5.root.D12raw
ca2 = f1.h5.root.ijk

#ca.append(ArrD1D2)
#ca2.append(coord)
#ca.flush()
#ca2.flush()

# f1.close()