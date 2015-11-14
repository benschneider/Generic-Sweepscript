# -*- coding: utf-8 -*-
"""
Created on Sun Nov 08 23:40:43 2015

@author: Ben
"""
import scipy.signal as signal
import numpy as np
from scipy.fftpack import (fft, ifft, ifftshift, fft2, ifft2, fftn,
                           ifftn, fftfreq)
from numpy.fft import rfftn, irfftn
# from threading import Thread
# import thread
def newConv(I1, Q1, I2, Q2, lags=20):
    ''' By Defining the number of lags one defines an interrest 
    of region meaning any effect should happen on that oder of
    time scale; thus lower frequency effects cannot be displayed on
    that scale and can be discarded from the convolution.    '''
    
    
    I1 = asarray(I1)
    Q1 = asarray(Q1)

    if in1.ndim == in2.ndim == 0:  # scalar inputs
        return in1 * in2
    elif not in1.ndim == in2.ndim:
        raise ValueError("in1 and in2 should have the same dimensionality")
    elif in1.size == 0 or in2.size == 0:  # empty arrays
        return array([])

    s1 = array(in1.shape)
    s2 = array(in2.shape)
    complex_result = (np.issubdtype(in1.dtype, np.complex) or
                      np.issubdtype(in2.dtype, np.complex))
    shape = s1 + s2 - 1

    # Speed up FFT by padding to optimal size for FFTPACK
    fshape = [_next_regular(int(d)) for d in shape]
    fslice = tuple([slice(0, int(sz)) for sz in shape])
    # Pre-1.9 NumPy FFT routines are not threadsafe.  For older NumPys, make
    # sure we only call rfftn/irfftn from one thread at a time.
    if not complex_result and (_rfft_mt_safe or _rfft_lock.acquire(False)):
        try:
            ret = irfftn(rfftn(in1, fshape) *
                         rfftn(in2, fshape), fshape)[fslice].copy()
        finally:
            if not _rfft_mt_safe:
                _rfft_lock.release()
    else:
        # If we're here, it's either because we need a complex result, or we
        # failed to acquire _rfft_lock (meaning rfftn isn't threadsafe and
        # is already in use by another thread).  In either case, use the
        # (threadsafe but slower) SciPy complex-FFT routines instead.
        ret = ifftn(fftn(in1, fshape) * fftn(in2, fshape))[fslice].copy()
        if not complex_result:
            ret = ret.real

    return ret


def covConv(a,b, lags=20):
    ''' returns fft convolution result 
    assumes a, b to be same length 1-d numpy arrays
    '''
    result = signal.fftconvolve(a, b[::-1], mode='full')/(len(a)-1)
    start = len(a)-lags
    stop = len(a)-1+lags
    return result[start:stop]  
    
def getCovMatrix(I1, Q1, I2, Q2, lags=20, extended = True):
    ''' # Matrix index as follows:
    # 0: <I1I1>
    # 1: <Q1Q1>
    # 2: <I2I2>
    # 3: <Q2Q2>
    # 4: <I1Q1>
    # 5: <I2Q2>
    # 6: <I1I2>
    # 7: <Q1Q2>
    # 8: <I1Q2>
    # 9: <Q1I2> '''
    CovMat = np.zeros([11,lags*2-1])
    if extended is True :
        # these should simply show a single peak 
        # with a height of its covariance
        # CovMat[0,:] = thread.start_new_thread( covConv, (I1, I1, lags) )
        # thread.start_new_thread( print_time, ("Thread-2", 4, ) )
        CovMat[0,:] = covConv(I1, I1, lags)                 
        CovMat[1,:] = covConv(Q1, Q1, lags)
        CovMat[2,:] = covConv(I2, I2, lags)
        CovMat[3,:] = covConv(Q2, Q2, lags) 
        
    # and these one go to zero for non singlemode squeezed states
    CovMat[4,:] = covConv(I1, Q1, lags)
    CovMat[5,:] = covConv(I2, Q2, lags)
    # these ones are relevant for 2 mode squeezing  
    CovMat[6,:]= covConv(I1, I2, lags)
    CovMat[7,:]= covConv(Q1, Q2, lags)
    CovMat[8,:]= covConv(I1, Q2, lags)
    CovMat[9,:]= covConv(Q1, I2, lags)
    CovMat[10,:] = abs(1j*(CovMat[8,:]+CovMat[9,:]) + (CovMat[6,:] - CovMat[7,:]))
    return CovMat
    