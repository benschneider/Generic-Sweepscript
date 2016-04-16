from ctypes import c_float, POINTER, pointer, c_long
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
                 start=4.43e9, stop=0, pt=1, nSample=1e6, sampFreq=1e5,
                 buffmode=True):
        self.capture_ref = None
        self.buffmode = buffmode
        self.bandwidth = sampFreq
        self.removeDCoff = 0
        self.LoPos = LoPosAB          # Lo Above (1) or Below (0)
        self.freq = cfreq
        self.nSamples = int(nSample)   # Samples taken/trigger
        self.inputLvl = inputlvl
        self.Overload = 0
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
        if self.buffmode:
            self.setup_buffer()

    def performOpen(self):
        try:
            # self.digitizer.create_object()
            self.digitizer.boot_instrument(self.adressLo, self.adressDigi)
            print 'Digitizer ', self.name, ' started'
        except PXIDigitizer_wrapper.Error as e:
            print "Digitizer start failed"
            self.digitizer.close_instrument()
            self.digitizer.destroy_object()
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
            self.digitizer.close_instrument()
            self.digitizer.destroy_object()
            del self.digitizer
            self.close_memfiles()

    def set_settings(self):
        '''
        right now its easies to simply set the settings here
        '''
        self.digitizer.rf_remove_dc_offset_set(bool(self.removeDCoff))
        self.digitizer.modulation_generic_sampling_frequency_set(self.bandwidth)
        # self.digitizer.trigger_IQ_bandwidth_set(self.bandwidth, iOption)
        self.digitizer.rf_rf_input_level_set(self.inputLvl)
        self.digitizer.rf_userLOPosition_set(self.LoPos)
        self.digitizer.modulation_mode_set(5)  # Set to Generic
        self.digitizer.rf_centre_frequency_set(self.freq)
        self.digitizer.lo_reference_set(self.LoRef)
        self.digitizer.trigger_source_set(self.trig_source)
        self.digitizer.set_piplining(1)  # activate Pipelining (download data while it keeps measuring)

    def prep_data(self):
        '''Creates a range of empty variables which are used store data in'''
        self.vAvgIQ = None
        self.vAvgPow = None
        self.cRawIQ = None
        self.AvgMag = None
        self.AvgPhase = None
        self.vAvgMag = None
        self.vAvgPh = None
        self.create_memfiles()

    def create_memfiles(self):
        '''This creates on DISK Temp files to store large data chunks '''
        if self.nSamples > 1e5:
            self.cIQ = np.memmap(self.name[:2]+'.cIQ.mem', dtype='complex64', mode='w+', shape=self.nSamples)
            self.scaledI = np.memmap(self.name[:2]+'.I.mem', dtype=np.float32, mode='w+', shape=self.nSamples)
            self.scaledQ = np.memmap(self.name[:2]+'.Q.mem', dtype=np.float32, mode='w+', shape=self.nSamples)
            self.cfftsig = np.memmap(self.name[:2]+'.FFT.mem', dtype='complex64', mode='w+', shape=self.nSamples)
            self.i_buffer = np.memmap(self.name[:2]+'.IB.mem', dtype=c_float, mode='w+', shape=self.nSamples)
            self.q_buffer = np.memmap(self.name[:2]+'.QB.mem', dtype=c_float, mode='w+', shape=self.nSamples)

        else:
            self.i_buffer = np.zeros(self.nSamples, dtype=c_float)
            self.q_buffer = np.zeros(self.nSamples, dtype=c_float)
            self.cIQ = np.zeros(self.nSamples, dtype='complex64')
            self.scaledI = np.zeros(self.nSamples, dtype=np.float32)
            self.scaledQ = np.zeros(self.nSamples, dtype=np.float32)
            self.cfftsig = np.zeros(self.nSamples, dtype='complex64')

    def close_memfiles(self):
        del self.cIQ, self.scaledI, self.scaledQ, self.cfftsig
        if self.buffmode:
            del self.i_buffer, self.q_buffer

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
        '''grabs the biggest chunks of data '''
        self.checkADCOverload()
        (self.scaledI[:], self.scaledQ[:]) = self.digitizer.capture_iq_capt_mem(self.nSamples)

    def setup_buffer(self):
        '''
        The following is for setting the digitizer up in a buffering mode
        '''
        self.checkADCOverload()
        self.capture_ref = PXIDigitizer_wrapper.afDigitizerCaptureIQ_t()
        self.timeout = int(1000*self.nSamples/self.bandwidth+10000)
        i_ctypes = self.i_buffer.ctypes.data_as(POINTER(c_float))
        q_ctypes = self.q_buffer.ctypes.data_as(POINTER(c_float))
        self.buffer_ref = PXIDigitizer_wrapper.afDigitizerBufferIQ_t(
            i_ctypes, q_ctypes, self.nSamples)
        self.buffer_ref_pointer = pointer(self.buffer_ref)
        # print 'buffer setup'

    def init_trigger_IF(self):
        return self.digitizer.TriggerArmIF(self.nSamples)

    def init_trigger_buff(self):
        ''' Initiate the Digitizer capturing into the buffer,
        once a trigger signal is received  '''
        self.digitizer.capture_iq_issue_buffer(
            buffer_ref=self.buffer_ref, capture_ref=self.capture_ref, timeout=self.timeout)

    def downl_data_check(func):
        '''This is a property used when downloading data from the buffer.
        it excecutes the func until download beginns
        '''
        def new_func(*args, **kwargs):
            s = args[0]
            while True:
                try:
                    func(*args, **kwargs)
                except Exception, e:
                    if str(e) == 'Reclaim timeout':
                        # print 'Reclaim timeout'
                        sleep(0.05)
                        continue
                    elif str(e) == 'ADC overflow occurred in reclaimed buffer':
                        print e.message
                        s.ACDoverflow += 1
                        if s.ACDoverflow > 2:
                            raise e
                        break
                    else:
                        raise e
                s.ACDoverflow = 0
                break
        return new_func

    @downl_data_check
    def downl_data_buff(self):
        a = self.digitizer.capture_iq_reclaim_buffer(
            capture_ref=self.capture_ref, buffer_ref_pointer=self.buffer_ref_pointer)
        if a == 0:
            '''for successfull download of buffer store IQ as complex array'''
            self.scaledI[:] = self.i_buffer
            self.scaledQ[:] = self.q_buffer

    def get_data_complete(self):
        ''' Downloads Data, Lvl Correction and processes the data
        stored as self.scaledI ...'''
        self.downl_data_buff()
        self.levelcorr = self.digitizer.rf_level_correction_get()
        self.process_data()

    def killsideband(self, onlyfft=False):
        '''
        Generates complex FFT of the data and kills the side-band.
        cleared FFT data is stored in self.cfftsig
        '''
        self.cfftsig[:] = np.fft.fft(self.cIQ)
        self.cfftsig[:] = np.fft.fftshift(self.cfftsig)  # temporarily used for bug hunting
        smid = int(len(self.cfftsig)/2) + 1
        if self.LoPos is 0:
            self.cfftsig[smid:-1] = 0.0
        else:
            self.cfftsig[0:smid] = 0.0
        if onlyfft:
            return
        # self.cIQ[:] = np.fft.ifft(np.fft.ifftshift(self.cfftsig))
        self.scaledI[:] = np.imag(self.cIQ)
        self.scaledQ[:] = np.real(self.cIQ)

    def process_data(self):
        ''' Sample the signal, calc I+j*Q theta
         and store it in the driver object
         of each trigger there are x samples... which can be averaged...
        '''
        self.scaledI[:] = np.array((np.array(self.scaledI[:])*np.power(10.0, self.levelcorr/20.0)/np.sqrt(1000)))
        self.scaledQ[:] = np.array((np.array(self.scaledQ[:])*np.power(10.0, self.levelcorr/20.0)/np.sqrt(1000)))
        self.cIQ[:] = 1j * self.scaledQ + self.scaledI
        # self.killsideband()  # Not yet working using hardware filters for now

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
        self.AvgMag = np.mean(np.absolute(self.cIQ))
        self.AvgPhase = np.mean(np.angle(self.cIQ))

    def set_bandwidth(self, val):
        self.digitizer.trigger_IQ_bandwidth_set(val)

    def set_sampRate(self, val):
        self.digitizer.modulation_generic_sampling_frequency_set(val)

    def checkADCOverload(self):
        if self.digitizer.check_ADCOverload():
            self.Overload = self.Overload + 1
            print 'Overload number:', self.Overload
            sleep(0.2)
            if self.Overload > 1:
                self.digitizer.rf_rf_input_level_set(30)
                raise Exception('ADC overloaded 2x in a row')
        else:
            self.Overload = 0
