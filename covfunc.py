# -*- coding: utf-8 -*-
"""
Created on Sun Nov 08 23:40:43 2015

@author: Ben
"""
import scipy.signal as signal
import numpy as np
import threading
from scipy.signal.signaltools import _next_regular
# from scipy.fftpack import (fft, ifft, ifftshift, fft2, ifft2, fftn,
#                            ifftn, fftfreq)
from numpy.fft import rfftn, irfftn
_rfft_lock = threading.Lock()
# import thread


def getCovMatrix2(I1, Q1, I2, Q2, lags=20):
    ''' By Defining the number of lags one defines an interrest
    of region meaning any effect should happen on that oder of
    time scale; thus lower frequency effects cannot be displayed on
    that scale and can be discarded from the convolution.
    All input shapes need to be the same.
    requires an updated numpy version (1.9.0 +).
    '''

    lags = int(lags)
    I1 = np.asarray(I1)
    Q1 = np.asarray(Q1)
    I2 = np.asarray(I2)
    Q2 = np.asarray(Q2)
    CovMat = np.zeros([11, lags*2-1])

    start = len(I1*2-1)-lags
    stop = len(I1*2-1)-1+lags

    # assume I1 Q1 have the same shape
    sI1 = np.array(I1.shape)
    sQ2 = np.array(Q2.shape)
    complex_result = (np.issubdtype(I1.dtype, np.complex) or
                      np.issubdtype(Q2.dtype, np.complex))
    shape = sI1 + sQ2 - 1
    HPfilt = (int(shape/lags))

    # Speed up FFT by padding to optimal size for FFTPACK
    fshape = [_next_regular(int(d)) for d in shape]
    fslice = tuple([slice(0, int(sz)) for sz in shape])
    # Pre-1.9 NumPy FFT routines are not threadsafe.  For older NumPys, make
    # sure we only call rfftn/irfftn from one thread at a time.
    if not complex_result and _rfft_lock.acquire(False):
        try:
            fftI1 = rfftn(I1, fshape)
            fftQ1 = rfftn(Q1, fshape)
            fftI2 = rfftn(I1, fshape)
            fftQ2 = rfftn(Q2, fshape)

            rfftI1 = rfftn(I1[::-1], fshape)
            rfftQ1 = rfftn(Q1[::-1], fshape)
            rfftI2 = rfftn(I1[::-1], fshape)
            rfftQ2 = rfftn(Q2[::-1], fshape)

            # filter frequencies outside the lags range
            fftI1 = np.concatenate((np.zeros(HPfilt), fftI1[HPfilt:]))
            fftQ1 = np.concatenate((np.zeros(HPfilt), fftQ1[HPfilt:]))
            fftI2 = np.concatenate((np.zeros(HPfilt), fftI2[HPfilt:]))
            fftQ2 = np.concatenate((np.zeros(HPfilt), fftQ2[HPfilt:]))

            # filter frequencies outside the lags range
            rfftI1 = np.concatenate((np.zeros(HPfilt), rfftI1[HPfilt:]))
            rfftQ1 = np.concatenate((np.zeros(HPfilt), rfftQ1[HPfilt:]))
            rfftI2 = np.concatenate((np.zeros(HPfilt), rfftI2[HPfilt:]))
            rfftQ2 = np.concatenate((np.zeros(HPfilt), rfftQ2[HPfilt:]))

            # ret = irfftn(rfftn(in1, fshape) *
            #             rfftn(in2, fshape), fshape)[fslice].copy()

            CovMat[0, :] = irfftn((fftI1*rfftI1))[fslice].copy()[start:stop]
            CovMat[1, :] = irfftn((fftQ1*rfftQ1))[fslice].copy()[start:stop]
            CovMat[2, :] = irfftn((fftI2*rfftI2))[fslice].copy()[start:stop]
            CovMat[3, :] = irfftn((fftQ2*rfftQ2))[fslice].copy()[start:stop]

            CovMat[4, :] = irfftn((fftI1*rfftQ1))[fslice].copy()[start:stop]
            CovMat[5, :] = irfftn((fftI2*rfftQ2))[fslice].copy()[start:stop]

            CovMat[6, :] = irfftn((fftI1*rfftI2))[fslice].copy()[start:stop]
            CovMat[7, :] = irfftn((fftQ1*rfftQ2))[fslice].copy()[start:stop]
            CovMat[8, :] = irfftn((fftI1*rfftQ2))[fslice].copy()[start:stop]
            CovMat[9, :] = irfftn((fftQ1*rfftI2))[fslice].copy()[start:stop]

            CovMat[10, :] = (abs(1j*(CovMat[8, :]+CovMat[9, :])
                                 + (CovMat[6, :] - CovMat[7, :])))
            return CovMat

        finally:
            _rfft_lock.release()

    else:
        # If we're here, it's either because we need a complex result, or we
        # failed to acquire _rfft_lock (meaning rfftn isn't threadsafe and
        # is already in use by another thread).  In either case, use the
        # (threadsafe but slower) SciPy complex-FFT routines instead.
        # ret = ifftn(fftn(in1, fshape) * fftn(in2, fshape))[fslice].copy()
        print 'Abort, reason:complex input or Multithreaded FFT not available'

        if not complex_result:
            pass  # ret = ret.real

    return CovMat


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
    # 9: <Q1I2>
    # 10: <Squeezing> '''

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

