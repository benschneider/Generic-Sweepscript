# -*- coding: utf-8 -*-
"""
Created on Fri Nov 06 13:43:48 2015

@author: Ben

simulation of
correlation calculations and averages
with data which includes noise.

"""

import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt
from time import time

lags = 25
points = int(1e4)
triggers = 100

NoiseRatio1 = np.float64(10)
NoiseRatio2 = np.float64(10)

k = np.float64(triggers)
autocorr2 = np.float64(0.0)

t0 = time()
# sig0 = np.float64(np.random.randn(lags))
# sig1 = np.float64(np.tile(sig0, points/lags))
sig1 = np.float64(np.random.randn(points))
sig0 = sig1

for i in range(triggers):
    # print i, time() - t0
    a = np.float64(np.random.randn(points))
    b = np.float64(np.random.randn(points))
    a = np.float64((a + sig1/NoiseRatio1))
    b = np.float64((b + sig1/NoiseRatio2))
    # b = a/np.float64(100.0) + b (this simulates some data on top of noise)
    # a = sig1  # as test
    # b = sig1  # as test
    # t1 = time()
    # covab = np.cov(a,b)

    t2 = time()
    autocorr = signal.fftconvolve(a, b[::-1], mode='full')/(len(a)-1)
    autocorraa = signal.fftconvolve(a, a[::-1], mode='full')/(len(a)-1)
    autocorrbb = signal.fftconvolve(b, b[::-1], mode='full')/(len(b)-1)

    # autocorr2 = signal.correlate(a, b, mode='full')  #  Very slow
    # autocorr2 = np.convolve(a,b[::-1])  #  Slow
    t3 = time()
    # autocorr = autocorr/abs(autocorr).max()
    autocorr2 += np.float64(autocorr/k)
    t4 = time()
    # print t1-t0
    # print t2-t1
    # print t3-t2
    # print t4-t0

print (time() - t0)/k

# plt.plot(np.arange(-len(a)+1,len(a)), autocorr2)
result = autocorr2[(len(autocorr2)+1)/2-lags:(len(autocorr2)+1)/2+lags-1]
# plt.plot(np.arange(-lags+1,lags),
# autocorr2[segments*lags-lags:segments*lags+lags-1])
plt.plot(np.arange(-lags+1, lags), result)
print result.max()

# res2 = signal.convolve(sig0, sig0[::-1],
# mode='full')/(len(sig0)-1) # this simply takes way too long!!
# plt.plot(np.arange(-lags+1,lags), res2)

# result2 = signal.fftconvolve(sig0, sig0[::-1], mode='full')/(len(sig0)-1)
# res2 = result2[(len(result2)+1)/2-lags:(len(result2)+1)/2+lags-1]
# plt.plot(np.arange(-lags+1,lags), res2)
