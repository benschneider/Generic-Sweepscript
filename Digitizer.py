from time import sleep
import numpy as np
import sys
import PXIDigitizer_wrapper

# Digitizer.boot_instrument('PXI7::15::INSTR', 'PXI6::10::INSTR')
# Digitizer.boot_instrument('3011D1', '3036D1')


class instrument():

    '''Upon start, creates connection to Digitizer and Local oscillator
        this driver only contains some rudimentary functions to run
        the PXI-Aeroflex 3036 Digitizer.
        To speed things up one function is used to record data which is
        then stored in the object.
        From this various aspects are then calculated as needed and
        retriggered/recoreded again when actually needed instead of every time
        again...
    '''

    def __init__(self, adressDigi='3036D1', adressLo='3011D1', name='D',
                 start=0, stop=0, pt=1, sstep=20e-3, stime=1e-3):
        self.sampFreq = 10e6        # in Hz
        self.bandwidth = 10e6
        self.avgPerTrig = 1
        self.removeDCoff = 1
        self.LoPos = 1              # Lo Above (1) or Below (0)
        self.freq = 5e9
        self.nSamples = 50e3        # Samples taken/trigger
        self.Overload = 3           # to test the overload code
        self.LoRef = 0              # 0=ocxo, 1=int 2=extDaisy, 3=extTerminated
        self.trig_source = 8        # 8=Star, 32=SW, 35=internal
        self.adressLo = adressLo
        self.adressDigi = adressDigi
        self.name = name
        self.start = start
        self.stop = stop
        self.pt = pt
        self.lin = np.linspace(self.start, self.stop, self.pt)
        self.digitizer = PXIDigitizer_wrapper.afDigitizer_BS()
        try:
            self.digitizer.create_object()
            self.digitizer.boot_instrument(adressLo, adressDigi)
            self.prep_data()
            self.set_settings()
            print self.digitizer.ref_is_locked()  # print Lo locked confirmation
        except PXIDigitizer_wrapper.Error as e:
            self.raiseOnError(e)

    def raiseOnError(self, e):
            print str(e), sys.exc_info()[0]
            raise

    def performClose(self, bError=False):
        ''' assume digitizer exists'''
        try:
            self.digitizer.rf_rf_input_level_set(30)
            self.digitizer.close_instrument(bCheckError=not bError)
        except PXIDigitizer_wrapper.Error as e:
            if not bError:
                self.raiseOnError(e)
        finally:
            try:
                self.digitizer.destroy_object()
                del self.digitizer
            except:
                pass

    def set_settings(self):
        '''
        #right now its easies to simply set the settings here
        '''
        self.digitizer.rf_remove_dc_offset_set(bool(self.removeDCoff))
        self.digitizer.modulation_generic_sampling_frequency_set(self.sampFreq)
        # self.digitizer.trigger_IQ_bandwidth_set(self.bandwidth, iOption)
        self.digitizer.rf_rf_input_level_set(-10)
        self.digitizer.rf_userLOPosition_set(self.LoPos)
        self.digitizer.modulation_mode_set(5)  # Set to Generic
        self.digitizer.rf_centre_frequency_set(self.freq)
        self.digitizer.lo_reference_set(self.LoRef)
        self.digitizer.trigger_source_set(self.trig_source)

    def prep_data(self):
        self.vectorI = None
        self.vectorQ = None
        self.cAvgSignal = None
        self.cAvgSignal2 = None
        self.cTrace = None
        self.vPTrace = None
        self.vPowerMeanUnAvg = None
        self.MeanMag = None
        self.MeanPhas = None
        self.vMeanUnAvg = None
        self.cRaw = None
        self.dPower = None

    def set_freq(self, freq):
        self.digitizer.rf_centre_frequency_set(freq)

    def set_inputLevel(self, value):
        self.digitizer.rf_rf_input_level_set(value)

    def get_Levelcorr(self):
        return self.digitizer.rf_level_correction_get()

    def set_LoAboveBelow(self, val):
        '''
        #0 is below 1 is above
        '''
        self.digitizer.rf_userLOPosition_set(val)

    def getIQTrace(self):
        """Return I and Q signal in time as a complex vector,
        resample the signal if needed, and then clear cTrace to indicate
        capture has been taken."""
        if self.cTrace is None:
            self.sampleAndAverage()
        vTrace = self.cTrace
        self.cTrace = None
        return vTrace

    def sampleAndAverage(self):
        '''# Sample the signal, calc I+j*Q theta
        # and store it in the driver object
        # of each triger there are x samples... which can be averaged...
        '''
        TriggerSourceValue = self.digitizer.trigger_source_get()
        dLevelCorrection = self.digitizer.rf_level_correction_get()
        self.digitizer.trigger_arm_set(self.nSamples*2)
        self.checkADCOverload()
        vI = np.zeros(self.nSamples)
        vQ = np.zeros(self.nSamples)
        vI2 = np.zeros(self.nSamples)
        vQ2 = np.zeros(self.nSamples)
        vIMean = np.zeros(1)
        vQMean = np.zeros(1)

        # TriggersourceValue 32 = SW trigger
        if TriggerSourceValue is not 32:
            self.digitizer.trigger_arm_set(self.nSamples*2)
            self.checkADCOverload()
            # wait for external trigger signal
            while self.digitizer.data_capture_complete_get() is False:
                self.thread().msleep(1)
                self.checkADCOverload()
                (lI, lQ) = self.digitizer.capture_iq_capt_mem(self.nSamples)
        else:
                self.checkADCOverload()
                (lI, lQ) = self.digitizer.capture_iq_capt_mem(self.nSamples)

        # scale data to Volt / sqrt(1Ohm)
        scaledI = (np.array(lI)
                   * np.power(10.0, dLevelCorrection/20.0)
                   / np.sqrt(1000))
        scaledQ = (np.array(lQ)
                   * np.power(10.0, dLevelCorrection/20.0)
                   / np.sqrt(1000))
        crep = scaledI + 1j*scaledQ

        # We add the aquired data to the vI and vQ arrays
        vI = vI + np.mean(scaledI, axis=0)
        vQ = vQ + np.mean(scaledQ, axis=0)
        vI2 = vI2 + np.mean(scaledI**2, axis=0)
        vQ2 = vQ2 + np.mean(scaledQ**2, axis=0)

        # Result data being stored
        self.vPowerMean = (np.mean(scaledI**2, axis=1)
                           + np.mean(scaledQ**2, axis=1))
        self.vIMean = np.mean(scaledI, axis=1)
        self.vQMean = np.mean(scaledQ, axis=1)
        self.MeanMag = np.mean(np.absolute(crep), axis=1)
        self.MeanPhase = np.mean(np.angle(crep), axis=1)

        self.vMeanUnAvg = vIMean+1j*vQMean
        self.cTrace = vI+1j*vQ
        self.vPTrace = (vI2+vQ2)
        self.cAvgSignal = np.average(vI)+1j*np.average(vQ)
        self.cAvgSignal2 = np.rect(self.MeanMag, self.MeanPhas)
        self.dPower = np.average(vI2)+np.average(vQ2)

    def get_Vcorr(self):
        pass

    def set_bandwidth(self, val):
        pass

    def get_bandwidth(self):
        return 0

    def set_sampRate(self, val):
        self.digitizer.modulation_generic_sampling_frequency_set(val)

    def checkADCOverload(self):
        if self.digitizer.check_ADCOverload():
            self.Overload = self.Overload + 1
            sleep(0.2)
            if self.Overload > 3:
                self.digitizer.rf_rf_input_level_set(30)
                print 'ADC overloaded 3x in a row', sys.exc_info()[0]
                raise
        else:
            self.Overload = 0
