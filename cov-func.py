# -*- coding: utf-8 -*-
"""
Created on Sun Nov 08 23:40:43 2015

@author: Ben
"""
import scipy.signal as signal

def covConv(a,b):
    ''' returns fft convolution result 
    assumes a, b to be same length 1-d numpy arrays
    '''
    return signal.fftconvolve(a, b[::-1], mode='full')/(len(a)-1)
