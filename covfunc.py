# -*- coding: utf-8 -*-
"""
Created on Sun Nov 08 23:40:43 2015

@author: Ben
"""
import scipy.signal as signal
import numpy as np
import threading
from scipy.signal.signaltools import _next_regular
from numpy.fft import rfftn, irfftn
_rfft_lock = threading.Lock()


def get_g2(P1, P2, lags=20):
    ''' Returns the Top part of the G2 equation (<P1P2> - <P1><P2>)'''
    lags = int(lags)
    P1 = np.asarray(P1)
    P2 = np.asarray(P2)
    # G2 = np.zeros([lags*2-1])

    start = len(P1*2-1)-lags
    stop = len(P1*2-1)-1+lags

    # assume I1 Q1 have the same shape
    sP1 = np.array(P1.shape)
    complex_result = np.issubdtype(P1.dtype, np.complex)
    shape = sP1 - 1
    HPfilt = (int(sP1/(lags*4)))  # smallest features visible is lamda/4

    # Speed up FFT by padding to optimal size for FFTPACK
    fshape = [_next_regular(int(d)) for d in shape]
    fslice = tuple([slice(0, int(sz)) for sz in shape])
    # Pre-1.9 NumPy FFT routines are not threadsafe.  For older NumPys, make
    # sure we only call rfftn/irfftn from one thread at a time.
    if not complex_result and _rfft_lock.acquire(False):
        try:
            fftP1 = rfftn(P1, fshape)
            rfftP2 = rfftn(P2[::-1], fshape)
            G2 = irfftn((fftP1*rfftP2))[fslice].copy()[start:stop]/len(fftP1)
            return

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

    P12var = np.var(P1)*np.var(P2)
    return G2-P12var


def getCovMatrix(I1, Q1, I2, Q2, lags=20):
    '''
    This function was adaped from scipy.signal.fft.convolve.
    By Defining the number of lags one defines an interrest
    of region meaning any effect should happen on that oder of
    time scale; thus lower frequency effects cannot be displayed on
    that scale and can be discarded from the convolution.
    All input shapes need to be the same.
    requires an updated numpy version (1.9.0 +).
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
    # 10: <Squeezing> Magnitude
    # 11: <Squeezing> Phase
    '''

    lags = int(lags)
    I1 = np.asarray(I1)
    Q1 = np.asarray(Q1)
    I2 = np.asarray(I2)
    Q2 = np.asarray(Q2)
    CovMat = np.zeros([14, lags*2+1])

    start = len(I1) - lags - 1  # len(I1*2-1)-lags
    stop = len(I1) + lags  # len(I1*2-1)-1+lags

    # assume I1 Q1 have the same shape
    sI1 = np.array(I1.shape)
    sQ2 = np.array(Q2.shape)
    complex_result = (np.issubdtype(I1.dtype, np.complex) or
                      np.issubdtype(Q2.dtype, np.complex))
    shape = sI1 + sQ2 - 1
    # HPfilt = (int(sI1/(lags*4)))  # smallest features visible is lamda/4

    # Speed up FFT by padding to optimal size for FFTPACK
    fshape = [_next_regular(int(d)) for d in shape]
    fslice = tuple([slice(0, int(sz)) for sz in shape])
    # Pre-1.9 NumPy FFT routines are not threadsafe.  For older NumPys, make
    # sure we only call rfftn/irfftn from one thread at a time.
    if not complex_result and _rfft_lock.acquire(False):
        try:
            fftI1 = rfftn(I1, fshape)
            fftQ1 = rfftn(Q1, fshape)
            fftI2 = rfftn(I2, fshape)
            fftQ2 = rfftn(Q2, fshape)
            rfftI1 = rfftn(I1[::-1], fshape)
            rfftQ1 = rfftn(Q1[::-1], fshape)
            rfftI2 = rfftn(I2[::-1], fshape)
            rfftQ2 = rfftn(Q2[::-1], fshape)
            # filter frequencies outside the lags range (This is buggy atm)
            # fftI1 = np.concatenate((np.zeros(HPfilt), fftI1[HPfilt:]))
            # fftQ1 = np.concatenate((np.zeros(HPfilt), fftQ1[HPfilt:]))
            # fftI2 = np.concatenate((np.zeros(HPfilt), fftI2[HPfilt:]))
            # fftQ2 = np.concatenate((np.zeros(HPfilt), fftQ2[HPfilt:]))
            # filter frequencies outside the lags range
            # rfftI1 = np.concatenate((np.zeros(HPfilt), rfftI1[HPfilt:]))
            # rfftQ1 = np.concatenate((np.zeros(HPfilt), rfftQ1[HPfilt:]))
            # rfftI2 = np.concatenate((np.zeros(HPfilt), rfftI2[HPfilt:]))
            # rfftQ2 = np.concatenate((np.zeros(HPfilt), rfftQ2[HPfilt:]))
            # 0: <I1I1>
            CovMat[0, :] = (irfftn((fftI1*rfftI1))[fslice].copy()[start:stop] / len(fftI1))
            # 1: <Q1Q1>
            CovMat[1, :] = (irfftn((fftQ1*rfftQ1))[fslice].copy()[start:stop] / len(fftI1))
            # 2: <I2I2>
            CovMat[2, :] = (irfftn((fftI2*rfftI2))[fslice].copy()[start:stop] / len(fftI1))
            # 3: <Q2Q2>
            CovMat[3, :] = (irfftn((fftQ2*rfftQ2))[fslice].copy()[start:stop] / len(fftI1))
            # 4: <I1Q1>
            CovMat[4, :] = (irfftn((fftI1*rfftQ1))[fslice].copy()[start:stop] / len(fftI1))
            # 5: <I2Q2>
            CovMat[5, :] = (irfftn((fftI2*rfftQ2))[fslice].copy()[start:stop] / len(fftI1))
            # 6: <I1I2>
            CovMat[6, :] = (irfftn((fftI1*rfftI2))[fslice].copy()[start:stop] / len(fftI1))
            # 7: <Q1Q2>
            CovMat[7, :] = (irfftn((fftQ1*rfftQ2))[fslice].copy()[start:stop] / len(fftI1))
            # 8: <I1Q2>
            CovMat[8, :] = (irfftn((fftI1*rfftQ2))[fslice].copy()[start:stop] / len(fftI1))
            # 9: <Q1I2>
            CovMat[9, :] = (irfftn((fftQ1*rfftI2))[fslice].copy()[start:stop] / len(fftI1))
            # 10: <Squeezing> Magnitude
            CovMat[10, :] = (abs(1j*(CovMat[8, :]+CovMat[9, :]) + (CovMat[6, :] - CovMat[7, :])))
            # 11: <Squeezing> Angle
            CovMat[11, :] = np.angle(1j*(CovMat[8, :]+CovMat[9, :]) + (CovMat[6, :] - CovMat[7, :]))
            # 12: <Squeezing> Magnitude For Hyb Coupler
            CovMat[12, :] = (abs(1j*(CovMat[6, :]+CovMat[7, :]) + (CovMat[8, :] - CovMat[9, :])))
            # 12: Generic Absolute cross_correlation Power
            CovMat[13, :] =  abs(CovMat[6, :])+abs(CovMat[7, :]) + abs(CovMat[8, :]) + abs(CovMat[9, :])
            CovMat = f1pN(CovMat, lags, d=1)  # correct Trigger jitter
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
            print 'Not a complex result'
            pass  # ret = ret.real

    return CovMat


def f1pN(CovMat, lags0, d=1): 
    '''Simple Trigger correction function'''
    tArray = abs(CovMat[6, :])+abs(CovMat[7, :]) + abs(CovMat[8, :]) + abs(CovMat[9, :])
    squeezing_noise = np.sqrt(np.var(np.abs(tArray)))  # including the peak matters little
    if np.max(np.abs(tArray[lags0 - d:lags0 + d + 1])) < 3.0 * squeezing_noise:
        # logging.debug('SN ratio too low: Can not find trigger position')
        distance = 0
    else:
        distance = (np.argmax(tArray[lags0 - d:lags0 + d + 1]) - d) * - 1  # fround trigger jitter distance

    for i in range(6,14):
        CovMat[i, :] = np.roll(CovMat[i, :], distance)  # correct Trigger jitter

    return CovMat    


def covConv(a, b, lags=20):
    ''' returns fft convolution result
    assumes a, b to be same length 1-d numpy arrays
    '''
    result = signal.fftconvolve(a, b[::-1], mode='full')/(len(a)-1)
    start = len(a)-lags
    stop = len(a)-1+lags
    return result[start:stop]
