from ctypes import c_float, POINTER, pointer
from time import sleep
import numpy as np
import PXIDigitizer_wrapper
reload(PXIDigitizer_wrapper)

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

    def __init__(self, adressDigi='3036D1', adressLo='3011D1',
                 LoPosAB=1, LoRef=0, name='D', cfreq=4.57e9, inputlvl=30,
                 start=4.43e9, stop=0, pt=1, nSample=50e3, sampFreq=10e6):
        self.sampFreq = sampFreq        # Hz
        self.bandwidth = 0.1e6
        self.removeDCoff = 1
        self.LoPos = LoPosAB          # Lo Above (1) or Below (0)
        self.freq = cfreq
        self.nSamples = int(nSample)   # Samples taken/trigger
        self.inputLvl = inputlvl
        self.Overload = 4           # to test the overload code
        self.LoRef = LoRef          # 0=ocxo, 1=int 2=extDaisy, 3=extTerminated
        self.trig_source = 8        # 8=Star, 32=SW, 35=internal
        self.adressLo = adressLo
        self.adressDigi = adressDigi
        self.name = name
        self.start = start
        self.stop = stop
        self.pt = pt
        self.lin = np.linspace(self.start, self.stop, self.pt)
        self.digitizer = PXIDigitizer_wrapper.afDigitizer_BS()
        self.prep_data()
        self.performOpen()
        self.set_settings()
        self.setup_buffer()
        
    def performOpen(self):
        try:
            # self.digitizer.create_object()
            self.digitizer.boot_instrument(self.adressLo, self.adressDigi)
            print 'Digitizer ', self.name, ' started'
        except PXIDigitizer_wrapper.Error as e:
            print "Digitizer start failed"
            raise Exception(e)

    def performClose(self, bError=False):
        ''' assume digitizer exists'''
        try:
            self.digitizer.rf_rf_input_level_set(30)
            self.digitizer.close_instrument(bCheckError=not bError)
        except PXIDigitizer_wrapper.Error as e:
            if not bError:
                raise Exception(e)
        finally:
            self.digitizer.destroy_object()
            del self.digitizer

    def set_settings(self):
        '''
        right now its easies to simply set the settings here
        '''
        self.digitizer.rf_remove_dc_offset_set(bool(self.removeDCoff))
        self.digitizer.modulation_generic_sampling_frequency_set(self.sampFreq)
        # self.digitizer.trigger_IQ_bandwidth_set(self.bandwidth, iOption)
        self.digitizer.rf_rf_input_level_set(self.inputLvl)
        self.digitizer.rf_userLOPosition_set(self.LoPos)
        self.digitizer.modulation_mode_set(5)  # Set to Generic
        self.digitizer.rf_centre_frequency_set(self.freq)
        self.digitizer.lo_reference_set(self.LoRef)
        self.digitizer.trigger_source_set(self.trig_source)

    def prep_data(self):
        self.vAvgIQ = None
        self.vAvgPow = None
        self.cRawIQ = None
        self.AvgMag = None
        self.AvgPhase = None
        self.vAvgMag = None
        self.vAvgPh = None
        self.scaledI = None
        self.scaledQ = None

    def set_freq(self, freq):
        self.digitizer.rf_centre_frequency_set(freq)

    def get_freq(self):
        return self.digitizer.rf_centre_frequency_get()

    def set_inputLevel(self, value):
        self.digitizer.rf_rf_input_level_set(value)

    def get_Levelcorr(self):
        self.levelcorr = self.digitizer.rf_level_correction_get()
        return self.levelcorr

    def set_LoAboveBelow(self, val):
        ''' below(0), above(1) '''
        self.digitizer.rf_userLOPosition_set(val)

    def init_trigger(self):
        self.digitizer.trigger_arm_set(self.nSamples * 2)

    def wait_capture_complete(self):
        while self.digitizer.data_capture_complete_get() is False:
            sleep(10e-3)
        pass

    def downl_data(self):
        '''grabs the biggest chunks of data and does
        not update the Level correction value'''
        # self.wait_capture_complete()
        self.scaledI = np.zeros(self.nSamples)
        self.scaledQ = np.zeros(self.nSamples)
        self.checkADCOverload()
        (self.scaledI, self.scaledQ) = self.digitizer.capture_iq_capt_mem(self.nSamples)

    def setup_buffer(self):
        '''
        The following is for setting the digitizer up in a buffering mode
        '''
        self.checkADCOverload()
        self.capture_ref = PXIDigitizer_wrapper.afDigitizerCaptureIQ_t()
        self.i_buffer = np.zeros(self.nSamples, dtype=c_float)
        self.q_buffer = np.zeros(self.nSamples, dtype=c_float)
        self.timeout = 10000
        i_ctypes = self.i_buffer.ctypes.data_as(POINTER(c_float))
        q_ctypes = self.q_buffer.ctypes.data_as(POINTER(c_float))
        self.buffer_ref = PXIDigitizer_wrapper.afDigitizerBufferIQ_t(
            i_ctypes, q_ctypes, self.nSamples)
        self.buffer_ref_pointer = pointer(self.buffer_ref)
        print 'buffer setup'

    def init_trigger_buff(self):
        ''' Initiate the Digitizer capturing into the buffer '''
        self.digitizer.capture_iq_issue_buffer(buffer_ref=self.buffer_ref, 
                                               capture_ref=self.capture_ref,
                                               timeout=self.timeout)

    def downl_data_buff(self):
        self.digitizer.capture_iq_reclaim_buffer(
        capture_ref=self.capture_ref, buffer_ref_pointer=self.buffer_ref_pointer)
        if self.buffer_ref_pointer:
            total_samples = self.buffer_ref.samples
        else:
            print "NO BUFFER!"
            total_samples = 0
        self.scaledI = self.i_buffer[:total_samples].astype(np.float32)
        self.scaledQ = self.q_buffer[:total_samples].astype(np.float32)

    def get_newdata(self):
        ''' This one Triggers, waits till capture is complete
            Downloads Data, Downloads Lvl Correction and processes the data
            such that it can be grabed with the other functions '''
        self.init_trigger()
        self.downl_data()
        self.levelcorr = self.digitizer.rf_level_correction_get()
        self.process_data()

    def killsideband(self):
        '''
        Generates complex FFT of the data and kills the side-band.
        cleared FFT data is stored in self.cfftsig
        '''
        self.cfftsig = np.fft.fft(1j*self.scaledI + self.scaledQ)
        smid = int(len(self.cfftsig)/2) + 1
        if self.LoPos is 1:
            self.cfftsig[smid:-1] = 0.0
        else:
            self.cfftsig[0:smid] = 0.0

    def process_data(self):
        ''' Sample the signal, calc I+j*Q theta
         and store it in the driver object
         of each trigger there are x samples... which can be averaged...
        '''
        self.scaledI = np.array((np.array(self.scaledI)*np.power(10.0, self.levelcorr/20.0)/np.sqrt(1000)))
        self.scaledQ = np.array((np.array(self.scaledQ)*np.power(10.0, self.levelcorr/20.0)/np.sqrt(1000)))

        vI = np.zeros(1)
        vQ = np.zeros(1)
        vI2 = np.zeros(1)
        vQ2 = np.zeros(1)

        # Avg I/Q and scale data to Volt / sqrt(1Ohm)
        vI = np.mean(self.scaledI, axis=0)
        vQ = np.mean(self.scaledQ, axis=0)
        vI2 = np.mean(self.scaledI**2, axis=0)
        vQ2 = np.mean(self.scaledQ**2, axis=0)

        self.vAvgIQ = vI + 1j * vQ
        self.vAvgPow = (vI2 + vQ2)
        self.vAvgMag = np.absolute(self.vAvgIQ)
        self.vAvgPh = np.angle(self.vAvgIQ)

        # Average Magnitudes and Phases
        cRawIQ = 1j * self.scaledQ + self.scaledI
        self.AvgMag = np.mean(np.absolute(cRawIQ))
        self.AvgPhase = np.mean(np.angle(cRawIQ))

    def set_bandwidth(self, val):
        self.digitizer.trigger_IQ_bandwidth_set(val)

    def set_sampRate(self, val):
        self.digitizer.modulation_generic_sampling_frequency_set(val)

    def checkADCOverload(self):
        if self.digitizer.check_ADCOverload():
            self.Overload = self.Overload + 1
            print 'Overload number:', self.Overload
            sleep(0.2)
            if self.Overload > 2:
                self.digitizer.rf_rf_input_level_set(30)
                raise Exception('ADC overloaded 2x in a row')
        else:
            self.Overload = 0
